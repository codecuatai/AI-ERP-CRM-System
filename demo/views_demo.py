"""
views_demo.py — Views + URLs mẫu cho Frontend Dashboard.
Copy vào crm/views.py và thêm vào urls.py của dự án Wagtail.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Customer, Order, SupportTicket

try:
    from .ai_services import classify_customer_smart, suggest_email_gemini
    import os
    HAS_AI = True
except ImportError:
    HAS_AI = False


# --- 1. Dashboard chính: /crm/ ---
def crm_dashboard(request):
    customers = Customer.objects.all().order_by('-total_revenue')
    segment = request.GET.get('segment', '')
    q = request.GET.get('q', '')
    if segment:
        customers = customers.filter(ai_segment=segment)
    if q:
        customers = customers.filter(name__icontains=q)

    context = {
        'customers': customers,
        'total_customers': Customer.objects.count(),
        'vip_count': Customer.objects.filter(ai_segment='VIP').count(),
        'potential_count': Customer.objects.filter(ai_segment='POTENTIAL').count(),
        'hibernating_count': Customer.objects.filter(ai_segment='HIBERNATING').count(),
        'churn_count': Customer.objects.filter(ai_segment='CHURN_RISK').count(),
        'recent_orders': Order.objects.all().order_by('-created_at')[:10],
        'open_tickets': SupportTicket.objects.filter(status='OPEN').count(),
        'q': q, 'segment': segment,
    }
    return render(request, 'crm/dashboard.html', context)


# --- 2. Nút "Phân loại bằng AI" cho 1 khách hàng ---
@require_POST
def classify_one(request, pk):
    c = get_object_or_404(Customer, pk=pk)
    days = (timezone.now() - c.last_order_at).days if c.last_order_at else 999
    tickets = c.tickets.count()

    if HAS_AI and (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        result = classify_customer_smart(c.name, float(c.total_revenue), c.order_count, days, tickets)
        code_map = {'VIP': 'VIP', 'Tiềm năng': 'POTENTIAL', 'Ngủ đông': 'HIBERNATING', 'Rời bỏ': 'CHURN_RISK'}
        c.ai_segment = code_map.get(result.get('segment'), 'POTENTIAL')
        c.ai_score = result.get('score', 0)
        c.ai_summary = f"[{result.get('source')}] {result.get('reason')}"
    else:  # fallback rule-based offline
        if float(c.total_revenue) >= 20_000_000 and days <= 30:
            c.ai_segment, c.ai_score = 'VIP', 95
        elif c.order_count >= 3 and days <= 60:
            c.ai_segment, c.ai_score = 'POTENTIAL', 75
        elif days > 180:
            c.ai_segment, c.ai_score = 'CHURN_RISK', 20
        elif days > 90:
            c.ai_segment, c.ai_score = 'HIBERNATING', 40
        else:
            c.ai_segment, c.ai_score = 'POTENTIAL', 60
        c.ai_summary = f"[rule-based] R={days} ngày, F={c.order_count}, M={c.total_revenue:,.0f}đ."
    c.ai_updated_at = timezone.now()
    c.save()
    messages.success(request, f"Đã phân loại {c.name} → {c.get_ai_segment_display()}")
    return redirect('crm_dashboard')


# --- 3. API gợi ý email (gọi bằng fetch từ dashboard) ---
def suggest_email_api(request, pk):
    c = get_object_or_404(Customer, pk=pk)
    seg = c.get_ai_segment_display()
    if HAS_AI and os.getenv("GEMINI_API_KEY"):
        try:
            data = suggest_email_gemini(c.name, seg, float(c.total_revenue))
            c.ai_email_suggestion = data["email"]
            c.save()
            return JsonResponse({"ok": True, "email": data["email"], "source": "gemini"})
        except Exception as e:
            return JsonResponse({"ok": False, "error": str(e)}, status=500)
    # fallback mẫu theo segment (demo offline vẫn đẹp)
    templates = {
        'VIP': f"Tiêu đề: Tri ân {c.name} — ưu đãi VIP 20%\n\nKính chào {c.name},\nCảm ơn quý khách đã đồng hành với tổng chi tiêu {c.total_revenue:,.0f}đ. Tặng quý khách voucher VIP 20% + giao hàng ưu tiên trong tháng này.\n\nTrân trọng,\nĐội ngũ CSKH",
        'Tiềm năng': f"Tiêu đề: {c.name} ơi, combo dành riêng cho bạn\n\nChào {c.name},\nThấy bạn mua khá thường xuyên, shop gợi ý combo tiết kiệm 15% cho lần mua tiếp theo. Đặt trong 7 ngày để giữ ưu đãi nhé!",
        'Ngủ đông': f"Tiêu đề: Nhớ bạn, {c.name} — quay lại nhận quà 100k\n\nChào {c.name},\nLâu rồi shop chưa thấy bạn. Tặng bạn voucher 100k + freeship để chào đón quay lại. Mã: WELCOMEBACK.",
        'Nguy cơ rời bỏ': f"Tiêu đề: Xin lỗi và mong {c.name} cho shop một cơ hội\n\nChào {c.name},\nShop rất tiếc về trải nghiệm chưa tốt. Tặng bạn voucher xin lỗi 200k + hỗ trợ 1-1. Mong bạn phản hồi để shop khắc phục.",
    }
    key = seg if seg in templates else 'Tiềm năng'
    if 'VIP' in seg:
        key = 'VIP'
    elif 'rời' in seg.lower():
        key = 'Nguy cơ rời bỏ'
    elif 'ngủ' in seg.lower():
        key = 'Ngủ đông'
    email = templates.get(key, templates['Tiềm năng'])
    c.ai_email_suggestion = email
    c.save()
    return JsonResponse({"ok": True, "email": email, "source": "rule-based"})


# --- urls.py (thêm vào crm/urls.py) ---
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.crm_dashboard, name='crm_dashboard'),
    path('classify/<int:pk>/', views.classify_one, name='crm_classify_one'),
    path('api/suggest-email/<int:pk>/', views.suggest_email_api, name='crm_suggest_email'),
]
# + include('crm.urls') vào urls.py chính với prefix 'crm/'
"""
