import hashlib
import csv
import logging
import secrets
from datetime import timedelta
from smtplib import SMTPException
from urllib.parse import urljoin, urlsplit

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Case, IntegerField, Max, Q, Sum, When
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from .forms import CareTaskForm, EmailDraftForm, LeadFollowUpComposeForm, LeadFollowUpResponseForm, PublicLeadRequestForm
from .models import AIAnalysis, CareTask, Customer, Interaction, LeadFollowUp, LeadFollowUpResponse, LeadRequest
from .services.ai_service import analyze_customer as run_customer_analysis
from .services.email_draft_service import create_email_draft

logger = logging.getLogger(__name__)


@login_required
@permission_required("crm.access_crm", raise_exception=True)
def dashboard(request):
    active_customers = Customer.objects.filter(is_active=True)
    today = timezone.localdate()
    open_tasks = CareTask.objects.exclude(status=CareTask.Status.DONE).select_related(
        "customer", "assignee"
    ).annotate(priority_order=Case(
        When(priority=CareTask.Priority.HIGH, then=0),
        When(priority=CareTask.Priority.MEDIUM, then=1),
        default=2,
        output_field=IntegerField(),
    ))
    context = {
        "customer_count": active_customers.count(),
        "unclassified_count": active_customers.filter(ai_segment=Customer.Segment.UNCLASSIFIED).count(),
        "vip_count": active_customers.filter(ai_segment=Customer.Segment.VIP).count(),
        "total_spent": active_customers.aggregate(total=Sum("total_spent"))["total"] or 0,
        "new_lead_count": LeadRequest.objects.filter(status=LeadRequest.Status.NEW).count(),
        "recent_lead_requests": LeadRequest.objects.select_related("customer")[:5],
        "unclassified_customers": active_customers.filter(
            ai_segment=Customer.Segment.UNCLASSIFIED
        ).order_by("-created_at")[:5],
        "today_tasks": open_tasks.filter(due_at=today).order_by("priority_order", "due_at")[:5],
        "overdue_tasks": open_tasks.filter(due_at__lt=today).order_by("due_at", "priority_order")[:5],
        "upcoming_tasks": open_tasks.filter(due_at__gt=today).order_by("due_at")[:5],
        "overdue_task_count": open_tasks.filter(due_at__lt=today).count(),
        "today_task_count": open_tasks.filter(due_at=today).count(),
    }
    return render(request, "crm/dashboard.html", context)


@login_required
@permission_required("crm.access_crm", raise_exception=True)
def customer_list(request):
    query = request.GET.get("q", "").strip()
    selected_segment = request.GET.get("segment", "").strip()
    customers = Customer.objects.filter(is_active=True)
    if query:
        customers = customers.filter(
            Q(full_name__icontains=query)
            | Q(email__icontains=query)
            | Q(company__icontains=query)
        )
    if selected_segment:
        customers = customers.filter(ai_segment=selected_segment)

    page = Paginator(customers.order_by("full_name"), 15).get_page(request.GET.get("page"))
    return render(request, "crm/customer_list.html", {
        "page": page,
        "customers": page.object_list,
        "query": query,
        "selected_segment": selected_segment,
        "segment_choices": Customer.Segment.choices,
    })


@login_required
@permission_required("crm.access_crm", raise_exception=True)
def priority_customer_list(request):
    """Transparent rules-based queue; ranking never changes customer data."""
    today = timezone.localdate()
    stale_before = timezone.now() - timedelta(days=30)
    selected_filter = request.GET.get("filter", "")
    customers = Customer.objects.filter(is_active=True).annotate(
        last_interaction=Max("interactions__occurred_at"),
    ).prefetch_related("care_tasks")
    queue = []
    for customer in customers:
        open_tasks = [task for task in customer.care_tasks.all() if task.status != CareTask.Status.DONE]
        overdue = any(task.due_at < today for task in open_tasks)
        stale = customer.last_interaction is None or customer.last_interaction < stale_before
        score = customer.ai_score
        reasons = []
        if customer.ai_segment == Customer.Segment.CHURN_RISK:
            score += 40
            reasons.append("Có nguy cơ rời bỏ")
        elif customer.ai_segment == Customer.Segment.VIP:
            score += 30
            reasons.append("Khách hàng VIP")
        if overdue:
            score += 35
            reasons.append("Có việc chăm sóc quá hạn")
        if stale:
            score += 20
            reasons.append("Chưa có tương tác trong 30 ngày")
        if customer.ai_score >= 70:
            reasons.append(f"Điểm tiềm năng {customer.ai_score}/100")
        if selected_filter == "churn" and customer.ai_segment != Customer.Segment.CHURN_RISK:
            continue
        if selected_filter == "vip" and customer.ai_segment != Customer.Segment.VIP:
            continue
        if selected_filter == "stale" and not stale:
            continue
        if selected_filter == "overdue" and not overdue:
            continue
        queue.append({"customer": customer, "priority_score": score, "reasons": reasons or ["Theo dõi định kỳ"]})
    queue.sort(key=lambda item: (-item["priority_score"], item["customer"].full_name.casefold()))
    page = Paginator(queue, 20).get_page(request.GET.get("page"))
    return render(request, "crm/priority_customer_list.html", {
        "page": page, "queue": page.object_list, "selected_filter": selected_filter,
    })


@login_required
@permission_required("crm.access_crm", raise_exception=True)
def customer_email_draft(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    initial = {"goal": "check_in", "tone": "formal", "length": "vừa"}
    if request.method == "POST":
        form = EmailDraftForm(request.POST)
        action = request.POST.get("action")
        if form.is_valid() and action == "generate":
            result = create_email_draft(
                customer, form.cleaned_data["goal"], form.cleaned_data["tone"], form.cleaned_data["length"]
            )
            form = EmailDraftForm(initial={
                "goal": form.cleaned_data["goal"],
                "tone": form.cleaned_data["tone"],
                "length": form.cleaned_data["length"],
                "draft": result["draft"],
            })
            messages.info(request, "Đây là bản nháp để bạn xem và chỉnh sửa; hệ thống chưa gửi email.")
            return render(request, "crm/email_draft.html", {
                "customer": customer, "form": form, "provider": result["provider"],
            })
        if form.is_valid() and action == "record_sent":
            draft = form.cleaned_data["draft"].strip()
            if not draft:
                form.add_error("draft", "Hãy tạo hoặc nhập nội dung email trước khi xác nhận.")
            else:
                Interaction.objects.create(
                    customer=customer, kind=Interaction.Kind.EMAIL,
                    subject=f"Email chăm sóc: {form.cleaned_data['goal']}",
                    content=draft,
                )
                messages.success(request, "Đã ghi nhận email bạn xác nhận đã gửi. CRM không gửi email tự động.")
                return redirect("crm:customer_detail", pk=customer.pk)
    else:
        form = EmailDraftForm(initial=initial)
    return render(request, "crm/email_draft.html", {"customer": customer, "form": form})


def _customer_queryset_for_export(request):
    customers = Customer.objects.all()
    query = request.GET.get("q", "").strip()
    segment = request.GET.get("segment", "").strip()
    if query:
        customers = customers.filter(Q(full_name__icontains=query) | Q(email__icontains=query) | Q(company__icontains=query))
    if segment:
        customers = customers.filter(ai_segment=segment)
    if request.GET.get("active") == "1":
        customers = customers.filter(is_active=True)
    return customers.order_by("full_name")


@login_required
@permission_required("crm.export_crm_data", raise_exception=True)
def export_customers_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="crm-customers.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["Họ tên", "Email", "Điện thoại", "Công ty", "Nguồn", "Phân khúc", "Điểm AI", "Đang hoạt động", "Tổng chi tiêu (VNĐ)"])

    def safe_cell(value):
        text = str(value or "")
        return f"'{text}" if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text

    for customer in _customer_queryset_for_export(request).iterator():
        writer.writerow([
            safe_cell(customer.full_name), safe_cell(customer.email), safe_cell(customer.phone),
            safe_cell(customer.company), safe_cell(customer.source),
            safe_cell(customer.get_ai_segment_display()), safe_cell(customer.ai_score),
            "Có" if customer.is_active else "Không", safe_cell(customer.total_spent),
        ])
    return response


@login_required
@permission_required("crm.access_crm", raise_exception=True)
def crm_report(request):
    today = timezone.localdate()
    start_date = today - timedelta(days=30)
    context = {
        "customer_total": Customer.objects.count(),
        "new_customers": Customer.objects.filter(created_at__date__gte=start_date).count(),
        "segments": [
            {"label": label, "count": Customer.objects.filter(ai_segment=value).count()}
            for value, label in Customer.Segment.choices
        ],
        "lead_statuses": [
            {"label": label, "count": LeadRequest.objects.filter(status=value).count()}
            for value, label in LeadRequest.Status.choices
        ],
        "task_statuses": [
            {"label": label, "count": CareTask.objects.filter(status=value).count()}
            for value, label in CareTask.Status.choices
        ],
        "overdue_tasks": CareTask.objects.filter(status__in=[CareTask.Status.TODO, CareTask.Status.IN_PROGRESS], due_at__lt=today).count(),
        "period_start": start_date,
    }
    return render(request, "crm/report.html", context)


@login_required
@permission_required("crm.access_crm", raise_exception=True)
def lead_request_list(request):
    query = request.GET.get("q", "").strip()
    selected_status = request.GET.get("status", "").strip()
    requests = LeadRequest.objects.select_related("customer").prefetch_related("follow_ups__response")
    if query:
        requests = requests.filter(
            Q(customer__full_name__icontains=query)
            | Q(customer__email__icontains=query)
            | Q(customer__company__icontains=query)
            | Q(request_text__icontains=query)
        )
    if selected_status:
        requests = requests.filter(status=selected_status)

    page = Paginator(requests, 15).get_page(request.GET.get("page"))
    return render(request, "crm/lead_request_list.html", {
        "page": page,
        "lead_requests": page.object_list,
        "query": query,
        "selected_status": selected_status,
        "status_choices": LeadRequest.Status.choices,
    })


@login_required
@permission_required("crm.access_crm", raise_exception=True)
def care_task_list(request):
    query = request.GET.get("q", "").strip()
    selected_status = request.GET.get("status", "").strip()
    tasks = CareTask.objects.select_related("customer", "assignee").annotate(
        priority_order=Case(
            When(priority=CareTask.Priority.HIGH, then=0),
            When(priority=CareTask.Priority.MEDIUM, then=1),
            default=2,
            output_field=IntegerField(),
        ),
        status_order=Case(
            When(status=CareTask.Status.TODO, then=0),
            When(status=CareTask.Status.IN_PROGRESS, then=1),
            default=2,
            output_field=IntegerField(),
        ),
    ).order_by("status_order", "due_at", "priority_order", "-created_at")
    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
            | Q(customer__full_name__icontains=query) | Q(customer__company__icontains=query)
        )
    if selected_status:
        tasks = tasks.filter(status=selected_status)
    page = Paginator(tasks, 20).get_page(request.GET.get("page"))
    return render(request, "crm/care_task_list.html", {
        "page": page,
        "tasks": page.object_list,
        "query": query,
        "selected_status": selected_status,
        "status_choices": CareTask.Status.choices,
        "today": timezone.localdate(),
    })


@login_required
@permission_required("crm.manage_care_tasks", raise_exception=True)
@require_http_methods(["GET", "POST"])
def care_task_form(request, pk=None, customer_pk=None):
    task = get_object_or_404(CareTask, pk=pk) if pk is not None else CareTask()
    customer = get_object_or_404(Customer, pk=customer_pk) if customer_pk is not None else None
    if request.method == "POST":
        form = CareTaskForm(request.POST, instance=task, customer=customer)
        if form.is_valid():
            saved_task = form.save(commit=False)
            if saved_task.assignee_id is None:
                saved_task.assignee = request.user
            if saved_task.status == CareTask.Status.DONE:
                saved_task.completed_at = saved_task.completed_at or timezone.now()
            else:
                saved_task.completed_at = None
            saved_task.save()
            messages.success(request, "Đã lưu việc chăm sóc khách hàng.")
            if customer_pk is not None:
                return redirect("crm:customer_detail", pk=customer_pk)
            return redirect("crm:care_tasks")
    else:
        initial = {} if task.pk else {"due_at": timezone.localdate()}
        if customer is not None and request.GET.get("suggestion") == "1":
            analysis = customer.ai_analyses.first()
            if analysis:
                suggestion = analysis.recommendation.strip()
                initial["title"] = suggestion[:177].rsplit(" ", 1)[0] + "…" if len(suggestion) > 180 else suggestion
                initial["description"] = suggestion
        form = CareTaskForm(instance=task, customer=customer, initial=initial)
    return render(request, "crm/care_task_form.html", {
        "form": form,
        "task": task,
        "customer": customer or (task.customer if task.pk else None),
        "is_edit": task.pk is not None,
    })


@login_required
@permission_required("crm.manage_crm_leads", raise_exception=True)
@require_POST
def update_lead_request_status(request, pk):
    lead_request = get_object_or_404(LeadRequest, pk=pk)
    status = request.POST.get("status", "")
    valid_statuses = {value for value, _label in LeadRequest.Status.choices}
    if status not in valid_statuses:
        messages.error(request, "Trạng thái yêu cầu không hợp lệ.")
    else:
        lead_request.status = status
        lead_request.save(update_fields=["status"])
        messages.success(request, "Đã cập nhật trạng thái yêu cầu tư vấn.")
    return redirect("crm:lead_requests")


@login_required
@permission_required("crm.access_crm", raise_exception=True)
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    has_public_requests = customer.lead_requests.exists()
    has_ai_consent = (
        customer.lead_requests.filter(ai_processing_consent=True).exists()
        or LeadFollowUpResponse.objects.filter(
            follow_up__lead_request__customer=customer,
            ai_processing_consent=True,
        ).exists()
    )
    context = {
        "customer": customer,
        "interactions": customer.interactions.all(),
        "care_tasks": customer.care_tasks.select_related("assignee").annotate(
            status_order=Case(
                When(status=CareTask.Status.TODO, then=0),
                When(status=CareTask.Status.IN_PROGRESS, then=1),
                default=2,
                output_field=IntegerField(),
            )
        ).order_by("status_order", "due_at")[:10],
        "has_public_requests": has_public_requests,
        "latest_analysis": customer.ai_analyses.first(),
        "analysis_history": customer.ai_analyses.all()[1:5],
        "can_run_ai_analysis": request.user.has_perm("crm.analyze_customer") and (not has_public_requests or has_ai_consent),
    }
    return render(request, "crm/customer_detail.html", context)


@login_required
@permission_required(("crm.access_crm", "crm.analyze_customer"), raise_exception=True)
@require_POST
def analyze_customer_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    public_requests = customer.lead_requests.all()
    if public_requests.exists():
        permitted_requests = list(public_requests.filter(ai_processing_consent=True))
        permitted_follow_up_responses = list(
            LeadFollowUpResponse.objects.filter(
                follow_up__lead_request__customer=customer,
                ai_processing_consent=True,
            ).select_related("follow_up__lead_request")
        )
        if not permitted_requests and not permitted_follow_up_responses:
            messages.error(request, "Khách hàng chưa đồng ý phân tích AI cho nội dung nào.")
            return redirect("crm:customer_detail", pk=customer.pk)
        result = run_customer_analysis(
            customer,
            permitted_requests=permitted_requests,
            permitted_follow_up_responses=permitted_follow_up_responses,
        )
    else:
        result = run_customer_analysis(customer)
    analysis = AIAnalysis.objects.create(customer=customer, **result)
    customer.ai_segment = analysis.segment
    customer.ai_score = analysis.score
    customer.save(update_fields=["ai_segment", "ai_score", "updated_at"])
    if analysis.provider == "gemini":
        messages.success(request, "Đã phân tích khách hàng bằng Gemini.")
    else:
        messages.info(request, "Đã phân tích bằng quy tắc cục bộ. Cấu hình GEMINI_API_KEY để gọi Gemini.")
    return redirect("crm:customer_detail", pk=customer.pk)


@require_http_methods(["GET", "POST"])
def public_lead_request(request):
    form = PublicLeadRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        save_public_lead_request(form.cleaned_data)
        return redirect("crm:lead_request_success")

    return render(request, "crm/lead_request.html", {
        "form": form,
        "brand_name": settings.PUBLIC_BRAND_NAME,
        "contact_email": settings.PUBLIC_CONTACT_EMAIL,
    })


@require_http_methods(["GET"])
def public_lead_request_success(request):
    return render(request, "crm/lead_request_success.html", {
        "brand_name": settings.PUBLIC_BRAND_NAME,
        "contact_email": settings.PUBLIC_CONTACT_EMAIL,
    })


@require_http_methods(["GET", "POST"])
def landing_page(request):
    from wagtail.models import Site
    from .models import LandingPage

    site = Site.find_for_request(request)
    if site:
        homepage = site.root_page.specific
        if isinstance(homepage, LandingPage) and homepage.live:
            return homepage.serve(request)
    form = PublicLeadRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        save_public_lead_request(form.cleaned_data)
        return redirect("crm:lead_request_success")

    return render(request, "crm/landing_page.html", {
        "form": form,
        "brand_name": settings.PUBLIC_BRAND_NAME,
        "contact_email": settings.PUBLIC_CONTACT_EMAIL,
    })


def save_public_lead_request(data):
    with transaction.atomic():
        customer = Customer.objects.filter(email__iexact=data["email"]).first()
        if customer is None:
            customer = Customer.objects.create(
                full_name=data["full_name"],
                email=data["email"],
                phone=data["phone"],
                company=data["company"],
                source="Website",
            )

        LeadRequest.objects.create(
            customer=customer,
            solution_interest=data["solution_interest"],
            request_text=data["request_text"],
            ai_processing_consent=data["ai_processing_consent"],
            ai_processing_consent_at=timezone.now() if data["ai_processing_consent"] else None,
        )
        Interaction.objects.create(
            customer=customer,
            kind=Interaction.Kind.OTHER,
            subject="Yêu cầu tư vấn từ website",
            content=data["request_text"],
        )


@staff_member_required
@permission_required("crm.manage_crm_leads", raise_exception=True)
@require_http_methods(["GET", "POST"])
def lead_follow_up(request, pk):
    lead_request = get_object_or_404(
        LeadRequest.objects.select_related("customer").prefetch_related("follow_ups__response"),
        pk=pk,
    )
    form = LeadFollowUpComposeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        token = secrets.token_urlsafe(32)
        follow_up = LeadFollowUp.objects.create(
            lead_request=lead_request,
            question_text=form.cleaned_data["question_text"],
            token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
            created_by=request.user,
            expires_at=timezone.now() + timedelta(days=settings.LEAD_FOLLOW_UP_LINK_TTL_DAYS),
        )

        try:
            site_url = settings.PUBLIC_SITE_URL.rstrip("/") + "/"
            parsed_site_url = urlsplit(site_url)
            local_http_allowed = settings.DEBUG and parsed_site_url.hostname in {"localhost", "127.0.0.1"}
            if parsed_site_url.scheme != "https" and not (parsed_site_url.scheme == "http" and local_http_allowed):
                raise ValueError("PUBLIC_SITE_URL phải dùng HTTPS ngoài môi trường phát triển local.")
            if not parsed_site_url.netloc or parsed_site_url.username or parsed_site_url.password:
                raise ValueError("PUBLIC_SITE_URL chưa được cấu hình hợp lệ.")

            reply_path = reverse("crm:lead_follow_up_reply", kwargs={"token": token})
            reply_url = urljoin(site_url, reply_path)
            context = {
                "brand_name": settings.PUBLIC_BRAND_NAME,
                "customer_name": lead_request.customer.full_name,
                "question_text": follow_up.question_text,
                "reply_url": reply_url,
                "expires_at": follow_up.expires_at,
            }
            email = EmailMultiAlternatives(
                subject=f"{settings.PUBLIC_BRAND_NAME}: bổ sung thông tin tư vấn",
                body=render_to_string("crm/emails/lead_follow_up.txt", context),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[lead_request.customer.email],
            )
            email.attach_alternative(render_to_string("crm/emails/lead_follow_up.html", context), "text/html")
            if email.send(fail_silently=False) != 1:
                raise SMTPException("Email backend không xác nhận gửi thành công.")
        except Exception:
            logger.exception("Không gửi được email bổ sung cho lead_request_id=%s", lead_request.pk)
            follow_up.status = LeadFollowUp.Status.FAILED
            follow_up.token_hash = ""
            follow_up.save(update_fields=["status", "token_hash"])
            messages.error(request, "Chưa gửi được email. Kiểm tra cấu hình email và địa chỉ website rồi thử lại.")
        else:
            LeadFollowUp.objects.filter(
                lead_request=lead_request,
                status=LeadFollowUp.Status.SENT,
            ).exclude(pk=follow_up.pk).update(
                status=LeadFollowUp.Status.REVOKED,
                token_hash="",
            )
            follow_up.status = LeadFollowUp.Status.SENT
            follow_up.sent_at = timezone.now()
            follow_up.save(update_fields=["status", "sent_at"])
            if lead_request.status == LeadRequest.Status.NEW:
                lead_request.status = LeadRequest.Status.CONTACTED
                lead_request.save(update_fields=["status"])
            Interaction.objects.create(
                customer=lead_request.customer,
                kind=Interaction.Kind.EMAIL,
                subject="Đã gửi email hỏi thêm thông tin",
                content=follow_up.question_text,
            )
            messages.success(request, f"Đã gửi email đến {lead_request.customer.email}.")

        return redirect("crm:lead_follow_up", pk=lead_request.pk)

    return render(request, "crm/lead_follow_up_compose.html", {
        "lead_request": lead_request,
        "form": form,
        "follow_ups": lead_request.follow_ups.all(),
        "brand_name": settings.PUBLIC_BRAND_NAME,
        "follow_up_ttl_days": settings.LEAD_FOLLOW_UP_LINK_TTL_DAYS,
    })


@staff_member_required
@permission_required("crm.manage_crm_leads", raise_exception=True)
@require_POST
def revoke_lead_follow_up(request, pk, follow_up_id):
    follow_up = get_object_or_404(LeadFollowUp, pk=follow_up_id, lead_request_id=pk)
    if follow_up.status == LeadFollowUp.Status.SENT:
        follow_up.status = LeadFollowUp.Status.REVOKED
        follow_up.token_hash = ""
        follow_up.save(update_fields=["status", "token_hash"])
        messages.success(request, "Đã thu hồi link trả lời của khách hàng.")
    else:
        messages.info(request, "Link này không còn ở trạng thái có thể thu hồi.")
    return redirect("crm:lead_follow_up", pk=pk)


def _find_follow_up_by_token(token):
    if len(token) != 43 or any(char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-" for char in token):
        return None
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return (
        LeadFollowUp.objects.select_related("lead_request__customer")
        .filter(token_hash=token_hash)
        .first()
    )


def _render_follow_up_public_page(request, context, status=200):
    response = render(request, "crm/lead_follow_up_public.html", context, status=status)
    response["Referrer-Policy"] = "no-referrer"
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


@never_cache
@require_http_methods(["GET", "POST"])
def lead_follow_up_reply(request, token):
    follow_up = _find_follow_up_by_token(token)
    if follow_up is None:
        return _render_follow_up_public_page(request, {
            "state": "invalid",
            "brand_name": settings.PUBLIC_BRAND_NAME,
        }, status=404)

    if follow_up.status == LeadFollowUp.Status.ANSWERED:
        return _render_follow_up_public_page(request, {
            "state": "answered",
            "brand_name": settings.PUBLIC_BRAND_NAME,
        })

    if follow_up.status != LeadFollowUp.Status.SENT:
        return _render_follow_up_public_page(request, {
            "state": "unavailable",
            "brand_name": settings.PUBLIC_BRAND_NAME,
        }, status=410)

    if follow_up.expires_at <= timezone.now():
        follow_up.status = LeadFollowUp.Status.EXPIRED
        follow_up.save(update_fields=["status"])
        return _render_follow_up_public_page(request, {
            "state": "expired",
            "brand_name": settings.PUBLIC_BRAND_NAME,
        }, status=410)

    form = LeadFollowUpResponseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            locked_follow_up = LeadFollowUp.objects.select_for_update().get(pk=follow_up.pk)
            if locked_follow_up.status != LeadFollowUp.Status.SENT or locked_follow_up.expires_at <= timezone.now():
                return _render_follow_up_public_page(request, {
                    "state": "unavailable",
                    "brand_name": settings.PUBLIC_BRAND_NAME,
                }, status=410)

            submitted_at = timezone.now()
            response = LeadFollowUpResponse.objects.create(
                follow_up=locked_follow_up,
                current_challenge=form.cleaned_data["current_challenge"],
                desired_outcome=form.cleaned_data["desired_outcome"],
                implementation_timing=form.cleaned_data["implementation_timing"],
                preferred_contact_time=form.cleaned_data["preferred_contact_time"],
                ai_processing_consent=form.cleaned_data["ai_processing_consent"],
                ai_processing_consent_at=(
                    submitted_at if form.cleaned_data["ai_processing_consent"] else None
                ),
                ai_processing_consent_version="followup-v1",
            )
            locked_follow_up.status = LeadFollowUp.Status.ANSWERED
            locked_follow_up.responded_at = submitted_at
            locked_follow_up.save(update_fields=["status", "responded_at"])
            Interaction.objects.create(
                customer=locked_follow_up.lead_request.customer,
                kind=Interaction.Kind.OTHER,
                subject="Khách hàng phản hồi form bổ sung",
                content=(
                    f"Khó khăn hiện tại: {response.current_challenge}\n"
                    f"Kết quả mong muốn: {response.desired_outcome or 'Chưa cung cấp'}\n"
                    f"Thời điểm dự kiến: {response.get_implementation_timing_display() or 'Chưa xác định'}\n"
                    f"Thời gian tiện liên hệ: {response.preferred_contact_time or 'Chưa cung cấp'}"
                ),
            )
        return redirect("crm:lead_follow_up_reply", token=token)

    return _render_follow_up_public_page(request, {
        "state": "form",
        "form": form,
        "follow_up": follow_up,
        "brand_name": settings.PUBLIC_BRAND_NAME,
    })


@require_http_methods(["GET"])
def privacy_notice(request):
    return render(request, "crm/privacy_notice.html", {
        "brand_name": settings.PUBLIC_BRAND_NAME,
        "data_controller_name": settings.PUBLIC_DATA_CONTROLLER_NAME,
        "privacy_email": settings.PUBLIC_PRIVACY_EMAIL,
        "data_retention_notice": settings.PUBLIC_DATA_RETENTION_NOTICE,
    })
