from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .forms import PublicLeadRequestForm
from .models import AIAnalysis, Customer, Interaction, LeadRequest
from .services.ai_service import analyze_customer as run_customer_analysis


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
    requests = LeadRequest.objects.select_related("customer")
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
    has_ai_consent = customer.lead_requests.filter(ai_processing_consent=True).exists()
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
        if not permitted_requests:
            messages.error(request, "Khách hàng chưa đồng ý phân tích AI. Chỉ chạy phân tích sau khi có yêu cầu đã bật đồng ý AI.")
            return redirect("crm:customer_detail", pk=customer.pk)
        result = run_customer_analysis(customer, permitted_requests=permitted_requests)
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


@require_http_methods(["GET"])
def privacy_notice(request):
    return render(request, "crm/privacy_notice.html", {
        "brand_name": settings.PUBLIC_BRAND_NAME,
        "data_controller_name": settings.PUBLIC_DATA_CONTROLLER_NAME,
        "privacy_email": settings.PUBLIC_PRIVACY_EMAIL,
        "data_retention_notice": settings.PUBLIC_DATA_RETENTION_NOTICE,
    })
