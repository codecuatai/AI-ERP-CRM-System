from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import AIAnalysis, Customer
from .services.ai_service import analyze_customer as run_customer_analysis


@login_required
def dashboard(request):
    customers = Customer.objects.filter(is_active=True)
    context = {
        "customers": customers,
        "customer_count": customers.count(),
        "unclassified_count": customers.filter(ai_segment=Customer.Segment.UNCLASSIFIED).count(),
        "vip_count": customers.filter(ai_segment=Customer.Segment.VIP).count(),
        "recent_analyses": AIAnalysis.objects.select_related("customer")[:5],
    }
    return render(request, "crm/dashboard.html", context)


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    context = {
        "customer": customer,
        "interactions": customer.interactions.all(),
        "analyses": customer.ai_analyses.all()[:5],
    }
    return render(request, "crm/customer_detail.html", context)


@login_required
@require_POST
def analyze_customer_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    result = run_customer_analysis(customer)
    analysis = AIAnalysis.objects.create(customer=customer, **result)
    customer.ai_segment = analysis.segment
    customer.ai_score = analysis.score
    customer.save(update_fields=["ai_segment", "ai_score", "updated_at"])
    if analysis.provider == "gemini":
        messages.success(request, "Đã phân tích khách hàng bằng Gemini.")
    else:
        messages.info(request, "Đã phân tích bằng dữ liệu mẫu (quy tắc cục bộ). Cấu hình GEMINI_API_KEY để gọi Gemini.")
    return redirect("crm:customer_detail", pk=customer.pk)

