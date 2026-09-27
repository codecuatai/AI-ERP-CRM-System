import hashlib
import logging
import secrets
from datetime import timedelta
from smtplib import SMTPException
from urllib.parse import urljoin, urlsplit

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from .forms import LeadFollowUpComposeForm, LeadFollowUpResponseForm, PublicLeadRequestForm
from .models import AIAnalysis, Customer, Interaction, LeadFollowUp, LeadFollowUpResponse, LeadRequest
from .services.ai_service import analyze_customer as run_customer_analysis

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    active_customers = Customer.objects.filter(is_active=True)
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
    }
    return render(request, "crm/dashboard.html", context)


@login_required
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
        "has_public_requests": has_public_requests,
        "latest_analysis": customer.ai_analyses.first(),
        "analysis_history": customer.ai_analyses.all()[1:5],
        "can_run_ai_analysis": not has_public_requests or has_ai_consent,
    }
    return render(request, "crm/customer_detail.html", context)


@login_required
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
