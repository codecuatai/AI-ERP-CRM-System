"""
models_demo.py — File mẫu định nghĩa các Wagtail Models và Snippets cho hệ thống AI ERP/CRM.
Có thể copy trực tiếp vào app crm/models.py của dự án Wagtail.
"""

from django.db import models
from django.utils import timezone
from wagtail.models import Page
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.views.snippets import SnippetViewSet


# ============================================================================
# 1. MODEL CUSTOMER (Khách hàng CRM) - Đăng ký dạng Snippet trong Wagtail
# ============================================================================
@register_snippet
class Customer(models.Model):
    SEGMENT_CHOICES = [
        ('UNCLASSIFIED', 'Chưa phân loại'),
        ('VIP', 'Khách hàng VIP (Doanh thu cao, gắn bó)'),
        ('POTENTIAL', 'Khách hàng tiềm năng (Tần suất mua tốt)'),
        ('HIBERNATING', 'Khách hàng ngủ đông (Lâu không mua)'),
        ('CHURN_RISK', 'Nguy cơ rời bỏ (Có phàn nàn / bỏ rơi)'),
    ]

    # Thông tin cơ bản
    code = models.CharField(max_length=20, unique=True, verbose_name="Mã khách hàng")
    name = models.CharField(max_length=150, verbose_name="Tên khách hàng")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Số điện thoại")
    company = models.CharField(max_length=200, blank=True, verbose_name="Công ty / Doanh nghiệp")
    address = models.CharField(max_length=255, blank=True, verbose_name="Địa chỉ")

    # Chỉ số ERP/CRM (Recency - Frequency - Monetary)
    total_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Tổng chi tiêu (VNĐ)")
    order_count = models.PositiveIntegerField(default=0, verbose_name="Số lượng đơn hàng")
    last_order_at = models.DateTimeField(null=True, blank=True, verbose_name="Lần mua gần nhất")

    # Kết quả do AI phân tích
    ai_segment = models.CharField(
        max_length=20,
        choices=SEGMENT_CHOICES,
        default='UNCLASSIFIED',
        verbose_name="Phân khúc AI"
    )
    ai_score = models.FloatField(default=0.0, verbose_name="Điểm gắn bó AI (0-100)")
    ai_summary = models.TextField(blank=True, verbose_name="Đánh giá từ AI")
    ai_email_suggestion = models.TextField(blank=True, verbose_name="Gợi ý phản hồi / Email CSKH")
    ai_updated_at = models.DateTimeField(null=True, blank=True, verbose_name="Thời điểm AI phân tích")

    # Thời gian tạo / cập nhật
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Cấu hình Panels hiển thị trong Wagtail Admin
    panels = [
        MultiFieldPanel([
            FieldPanel('code'),
            FieldPanel('name'),
            FieldPanel('email'),
            FieldPanel('phone'),
            FieldPanel('company'),
            FieldPanel('address'),
        ], heading="Thông tin cơ bản"),

        MultiFieldPanel([
            FieldPanel('total_revenue'),
            FieldPanel('order_count'),
            FieldPanel('last_order_at'),
        ], heading="Dữ liệu kinh doanh (RFM)"),

        MultiFieldPanel([
            FieldPanel('ai_segment'),
            FieldPanel('ai_score'),
            FieldPanel('ai_summary'),
            FieldPanel('ai_email_suggestion'),
            FieldPanel('ai_updated_at', read_only=True),
        ], heading="Trí tuệ nhân tạo (AI Analysis)"),
    ]

    class Meta:
        verbose_name = "Khách hàng"
        verbose_name_plural = "Danh sách Khách hàng"
        ordering = ['-total_revenue']

    def __str__(self):
        return f"[{self.code}] {self.name} - {self.get_ai_segment_display()}"


# ============================================================================
# 2. MODEL ORDER (Đơn hàng ERP)
# ============================================================================
@register_snippet
class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Chờ xử lý'),
        ('CONFIRMED', 'Đã xác nhận'),
        ('SHIPPED', 'Đang giao hàng'),
        ('COMPLETED', 'Hoàn thành'),
        ('CANCELLED', 'Đã hủy'),
    ]

    order_code = models.CharField(max_length=30, unique=True, verbose_name="Mã đơn hàng")
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Khách hàng"
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Tổng tiền (VNĐ)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Trạng thái")
    notes = models.TextField(blank=True, verbose_name="Ghi chú đơn")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Ngày đặt")

    panels = [
        FieldPanel('order_code'),
        FieldPanel('customer'),
        FieldPanel('total_amount'),
        FieldPanel('status'),
        FieldPanel('notes'),
        FieldPanel('created_at'),
    ]

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Quản lý Đơn hàng"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_code} - {self.customer.name} ({self.total_amount:,.0f} VNĐ)"


# ============================================================================
# 3. MODEL SUPPORT TICKET (Chăm sóc khách hàng CRM)
# ============================================================================
@register_snippet
class SupportTicket(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Thấp'),
        ('MEDIUM', 'Trung bình'),
        ('HIGH', 'Cao / Khẩn cấp'),
    ]
    STATUS_CHOICES = [
        ('OPEN', 'Mới tiếp nhận'),
        ('IN_PROGRESS', 'Đang xử lý'),
        ('RESOLVED', 'Đã giải quyết'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="tickets")
    subject = models.CharField(max_length=255, verbose_name="Tiêu đề yêu cầu")
    content = models.TextField(verbose_name="Nội dung phản ánh")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    ai_suggested_reply = models.TextField(blank=True, verbose_name="Gợi ý câu trả lời từ AI")
    created_at = models.DateTimeField(auto_now_add=True)

    panels = [
        FieldPanel('customer'),
        FieldPanel('subject'),
        FieldPanel('content'),
        FieldPanel('priority'),
        FieldPanel('status'),
        FieldPanel('ai_suggested_reply'),
    ]

    class Meta:
        verbose_name = "Yêu cầu hỗ trợ"
        verbose_name_plural = "Yêu cầu hỗ trợ (Tickets)"


# ============================================================================
# 4. WAGTAIL VIEWSET TÙY CHỈNH CHO ADMIN
# ============================================================================
class CustomerViewSet(SnippetViewSet):
    model = Customer
    icon = "user"
    menu_label = "CRM Khách hàng"
    menu_order = 200
    add_to_admin_menu = True
    list_display = ("code", "name", "total_revenue", "order_count", "ai_segment", "ai_score")
    list_filter = ("ai_segment", "company")
    search_fields = ("code", "name", "email", "phone")


# ============================================================================
# 5. WAGTAIL PAGE (Frontend Dashboard cho người dùng)
# ============================================================================
class CrmDashboardPage(Page):
    """
    Trang hiển thị Frontend Dashboard trong Wagtail
    """
    intro = models.CharField(max_length=250, default="Bảng điều khiển kinh doanh thông minh tích hợp AI")

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context['customers'] = Customer.objects.all().order_by('-total_revenue')
        context['total_customers'] = Customer.objects.count()
        context['vip_count'] = Customer.objects.filter(ai_segment='VIP').count()
        context['churn_count'] = Customer.objects.filter(ai_segment='CHURN_RISK').count()
        context['recent_orders'] = Order.objects.all().order_by('-created_at')[:10]
        return context

    class Meta:
        verbose_name = "Trang Dashboard CRM"
