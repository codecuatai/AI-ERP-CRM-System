from django.db import models
from django.utils import timezone
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class Customer(models.Model):
    class Segment(models.TextChoices):
        UNCLASSIFIED = "UNCLASSIFIED", "Chưa phân loại"
        VIP = "VIP", "VIP"
        POTENTIAL = "POTENTIAL", "Tiềm năng"
        HIBERNATING = "HIBERNATING", "Ngủ đông"
        CHURN_RISK = "CHURN_RISK", "Nguy cơ rời bỏ"

    full_name = models.CharField("Họ và tên", max_length=160)
    email = models.EmailField("Email", unique=True)
    phone = models.CharField("Số điện thoại", max_length=30, blank=True)
    company = models.CharField("Công ty", max_length=160, blank=True)
    source = models.CharField("Nguồn khách hàng", max_length=100, blank=True)
    notes = models.TextField("Ghi chú", blank=True)
    total_spent = models.DecimalField("Tổng chi tiêu (VNĐ)", max_digits=14, decimal_places=0, default=0)
    is_active = models.BooleanField("Đang hoạt động", default=True)
    ai_segment = models.CharField("Phân khúc AI", max_length=20, choices=Segment.choices, default=Segment.UNCLASSIFIED)
    ai_score = models.PositiveSmallIntegerField("Điểm tiềm năng (0–100)", default=0)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("Cập nhật lần cuối", auto_now=True)

    panels = [
        MultiFieldPanel([
            FieldPanel("full_name"), FieldPanel("email"), FieldPanel("phone"),
            FieldPanel("company"), FieldPanel("source"), FieldPanel("notes"),
            FieldPanel("total_spent"), FieldPanel("is_active"),
        ], heading="Thông tin khách hàng"),
        MultiFieldPanel([
            FieldPanel("ai_segment", read_only=True), FieldPanel("ai_score", read_only=True),
        ], heading="Kết quả phân tích AI"),
    ]

    class Meta:
        ordering = ["full_name"]
        verbose_name = "Khách hàng"
        verbose_name_plural = "Khách hàng"

    def __str__(self):
        return f"{self.full_name} ({self.email})"


@register_snippet
class Interaction(models.Model):
    class Kind(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        PHONE = "PHONE", "Điện thoại"
        MEETING = "MEETING", "Gặp mặt"
        OTHER = "OTHER", "Khác"

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="interactions", verbose_name="Khách hàng")
    kind = models.CharField("Hình thức", max_length=10, choices=Kind.choices, default=Kind.OTHER)
    subject = models.CharField("Chủ đề", max_length=200)
    content = models.TextField("Nội dung trao đổi")
    occurred_at = models.DateTimeField("Thời điểm", auto_now_add=True)

    panels = [FieldPanel("customer"), FieldPanel("kind"), FieldPanel("subject"), FieldPanel("content")]

    class Meta:
        ordering = ["-occurred_at"]
        verbose_name = "Lịch sử tương tác"
        verbose_name_plural = "Lịch sử tương tác"

    def __str__(self):
        return f"{self.customer.full_name} — {self.subject}"


@register_snippet
class AIAnalysis(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="ai_analyses", verbose_name="Khách hàng")
    segment = models.CharField("Phân khúc", max_length=20, choices=Customer.Segment.choices)
    score = models.PositiveSmallIntegerField("Điểm tiềm năng", default=0)
    summary = models.TextField("Nhận định")
    recommendation = models.TextField("Đề xuất hành động")
    provider = models.CharField("Nguồn phân tích", max_length=30, default="rules")
    created_at = models.DateTimeField("Thời điểm phân tích", auto_now_add=True)

    panels = [
        FieldPanel("customer"), FieldPanel("segment", read_only=True),
        FieldPanel("score", read_only=True), FieldPanel("summary", read_only=True),
        FieldPanel("recommendation", read_only=True), FieldPanel("provider", read_only=True),
    ]

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Kết quả phân tích AI"
        verbose_name_plural = "Kết quả phân tích AI"

    def __str__(self):
        return f"{self.customer.full_name} — {self.get_segment_display()} ({self.created_at:%Y-%m-%d})"


@register_snippet
class LeadRequest(models.Model):
    class SolutionInterest(models.TextChoices):
        CRM = "CRM", "CRM & chăm sóc khách hàng"
        ERP = "ERP", "Quản lý kho & bán hàng"
        INFRASTRUCTURE = "INFRASTRUCTURE", "Máy chủ & sao lưu dữ liệu"
        INTEGRATION = "INTEGRATION", "Tích hợp hệ thống"
        AI = "AI", "AI & tự động hóa"
        OTHER = "OTHER", "Nhu cầu khác / chưa xác định"

    class Status(models.TextChoices):
        NEW = "NEW", "Mới gửi"
        CONTACTED = "CONTACTED", "Đã liên hệ"
        COMPLETED = "COMPLETED", "Đã xử lý"

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="lead_requests",
        verbose_name="Khách hàng",
    )
    solution_interest = models.CharField(
        "Giải pháp quan tâm",
        max_length=20,
        choices=SolutionInterest.choices,
        default=SolutionInterest.OTHER,
    )
    request_text = models.TextField("Nhu cầu khách hàng")
    status = models.CharField("Trạng thái", max_length=12, choices=Status.choices, default=Status.NEW)
    consent_at = models.DateTimeField("Thời điểm đồng ý", default=timezone.now, editable=False)
    consent_version = models.CharField("Phiên bản nội dung đồng ý", max_length=20, default="v2", editable=False)
    ai_processing_consent = models.BooleanField("Đồng ý phân tích AI", default=False)
    ai_processing_consent_at = models.DateTimeField("Thời điểm đồng ý phân tích AI", null=True, blank=True, editable=False)
    ai_processing_consent_version = models.CharField("Phiên bản đồng ý phân tích AI", max_length=20, default="v1", editable=False)
    created_at = models.DateTimeField("Thời điểm gửi", auto_now_add=True)

    panels = [
        FieldPanel("customer"),
        FieldPanel("solution_interest"),
        FieldPanel("request_text", read_only=True),
        FieldPanel("status"),
        FieldPanel("consent_at", read_only=True),
        FieldPanel("consent_version", read_only=True),
        FieldPanel("ai_processing_consent", read_only=True),
        FieldPanel("ai_processing_consent_at", read_only=True),
        FieldPanel("ai_processing_consent_version", read_only=True),
        FieldPanel("created_at", read_only=True),
    ]

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Yêu cầu tư vấn"
        verbose_name_plural = "Yêu cầu tư vấn"

    def __str__(self):
        return f"{self.customer.full_name} — {self.get_status_display()} ({self.created_at:%Y-%m-%d})"
