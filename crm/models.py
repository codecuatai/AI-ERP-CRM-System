from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.utils import timezone
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail import blocks
from wagtail.fields import StreamField
from wagtail.models import Page

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager


class Customer(models.Model):
    if TYPE_CHECKING:
        interactions: RelatedManager["Interaction"]
        ai_analyses: RelatedManager["AIAnalysis"]
        lead_requests: RelatedManager["LeadRequest"]

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
        permissions = [
            ("access_crm", "Can access the CRM workspace"),
            ("analyze_customer", "Can run customer AI analysis"),
            ("manage_crm_leads", "Can manage CRM leads and follow-ups"),
            ("manage_care_tasks", "Can manage customer care tasks"),
            ("export_crm_data", "Can export CRM data"),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.email})"


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


class AIAnalysis(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="ai_analyses", verbose_name="Khách hàng")
    segment = models.CharField("Phân khúc", max_length=20, choices=Customer.Segment.choices)
    score = models.PositiveSmallIntegerField("Điểm tiềm năng", default=0)
    summary = models.TextField("Nhận định")
    recommendation = models.TextField("Đề xuất hành động")
    provider = models.CharField("Nguồn phân tích", max_length=30, default="rules")
    created_at = models.DateTimeField("Thời điểm phân tích", auto_now_add=True)

    if TYPE_CHECKING:
        def get_segment_display(self) -> str: ...

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


class LeadRequest(models.Model):
    if TYPE_CHECKING:
        follow_ups: RelatedManager["LeadFollowUp"]

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

    if TYPE_CHECKING:
        def get_solution_interest_display(self) -> str: ...

        def get_status_display(self) -> str: ...

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


class LeadFollowUp(models.Model):
    if TYPE_CHECKING:
        def get_status_display(self) -> str: ...

    class Status(models.TextChoices):
        PENDING = "PENDING", "Đang chuẩn bị"
        SENT = "SENT", "Đã gửi"
        FAILED = "FAILED", "Gửi thất bại"
        ANSWERED = "ANSWERED", "Đã phản hồi"
        EXPIRED = "EXPIRED", "Hết hạn"
        REVOKED = "REVOKED", "Đã thu hồi"

    lead_request = models.ForeignKey(
        LeadRequest,
        on_delete=models.CASCADE,
        related_name="follow_ups",
        verbose_name="Yêu cầu tư vấn",
    )
    question_text = models.TextField("Nội dung email hỏi thêm", max_length=2000)
    token_hash = models.CharField("Mã truy cập đã mã hóa", max_length=64, blank=True, editable=False)
    status = models.CharField("Trạng thái", max_length=12, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_follow_ups",
        verbose_name="Nhân viên gửi",
    )
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)
    sent_at = models.DateTimeField("Ngày gửi", null=True, blank=True)
    expires_at = models.DateTimeField("Link hết hạn lúc")
    responded_at = models.DateTimeField("Ngày khách phản hồi", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Yêu cầu bổ sung thông tin"
        verbose_name_plural = "Yêu cầu bổ sung thông tin"

    def __str__(self):
        return f"Bổ sung thông tin — {self.lead_request.customer.full_name} ({self.created_at:%Y-%m-%d})"


class LeadFollowUpResponse(models.Model):
    if TYPE_CHECKING:
        def get_implementation_timing_display(self) -> str: ...

    class ImplementationTiming(models.TextChoices):
        EXPLORING = "EXPLORING", "Đang tìm hiểu"
        WITHIN_MONTH = "WITHIN_MONTH", "Trong vòng 1 tháng"
        ONE_TO_THREE_MONTHS = "ONE_TO_THREE_MONTHS", "Trong 1–3 tháng"
        LATER = "LATER", "Sau 3 tháng"

    follow_up = models.OneToOneField(
        LeadFollowUp,
        on_delete=models.CASCADE,
        related_name="response",
        verbose_name="Yêu cầu bổ sung",
    )
    current_challenge = models.TextField("Khó khăn hiện tại", max_length=2000)
    desired_outcome = models.TextField("Kết quả mong muốn", max_length=2000, blank=True)
    implementation_timing = models.CharField(
        "Thời điểm dự kiến",
        max_length=24,
        choices=ImplementationTiming.choices,
        blank=True,
    )
    preferred_contact_time = models.CharField("Thời gian tiện liên hệ", max_length=120, blank=True)
    ai_processing_consent = models.BooleanField("Đồng ý phân tích AI", default=False)
    ai_processing_consent_at = models.DateTimeField("Thời điểm đồng ý AI", null=True, blank=True, editable=False)
    ai_processing_consent_version = models.CharField(
        "Phiên bản đồng ý AI",
        max_length=20,
        default="followup-v1",
        editable=False,
    )
    submitted_at = models.DateTimeField("Thời điểm gửi phản hồi", auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Phản hồi bổ sung của khách hàng"
        verbose_name_plural = "Phản hồi bổ sung của khách hàng"

    def __str__(self):
        return f"Phản hồi — {self.follow_up.lead_request.customer.full_name} ({self.submitted_at:%Y-%m-%d})"


class CareTask(models.Model):
    class Kind(models.TextChoices):
        FOLLOW_UP = "FOLLOW_UP", "Liên hệ lại"
        CALL = "CALL", "Gọi điện"
        QUOTE = "QUOTE", "Gửi báo giá"
        MEETING = "MEETING", "Hẹn gặp"
        OTHER = "OTHER", "Khác"

    class Priority(models.TextChoices):
        LOW = "LOW", "Thấp"
        MEDIUM = "MEDIUM", "Vừa"
        HIGH = "HIGH", "Cao"

    class Status(models.TextChoices):
        TODO = "TODO", "Cần làm"
        IN_PROGRESS = "IN_PROGRESS", "Đang làm"
        DONE = "DONE", "Hoàn tất"

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="care_tasks", verbose_name="Khách hàng"
    )
    title = models.CharField("Việc cần làm", max_length=180)
    description = models.TextField("Ghi chú", blank=True)
    kind = models.CharField("Loại việc", max_length=12, choices=Kind.choices, default=Kind.FOLLOW_UP)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="crm_care_tasks", verbose_name="Người phụ trách",
    )
    due_at = models.DateField("Ngày đến hạn")
    priority = models.CharField("Mức ưu tiên", max_length=8, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField("Trạng thái", max_length=12, choices=Status.choices, default=Status.TODO)
    completed_at = models.DateTimeField("Thời điểm hoàn tất", null=True, blank=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("Cập nhật lần cuối", auto_now=True)

    panels = [
        FieldPanel("customer"), FieldPanel("title"), FieldPanel("description"),
        FieldPanel("kind"), FieldPanel("assignee"), FieldPanel("due_at"),
        FieldPanel("priority"), FieldPanel("status"),
    ]

    class Meta:
        ordering = ["status", "due_at", "-priority", "-created_at"]
        verbose_name = "Việc chăm sóc khách hàng"
        verbose_name_plural = "Việc chăm sóc khách hàng"

    def __str__(self):
        return f"{self.title} — {self.customer.full_name}"


class SalesRecord(models.Model):
    """A minimal closed-sale record for CRM revenue reporting, not accounting."""

    class Status(models.TextChoices):
        WON = "WON", "Đã chốt"
        VOID = "VOID", "Đã hủy"

    reference = models.CharField("Mã giao dịch", max_length=40, unique=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="sales_records",
        verbose_name="Khách hàng",
    )
    amount = models.DecimalField("Giá trị giao dịch (VNĐ)", max_digits=14, decimal_places=0)
    closed_at = models.DateField("Ngày chốt")
    status = models.CharField("Trạng thái", max_length=8, choices=Status.choices, default=Status.WON)
    created_at = models.DateTimeField("Ngày tạo bản ghi", auto_now_add=True)

    panels = [
        FieldPanel("reference"), FieldPanel("customer"), FieldPanel("amount"),
        FieldPanel("closed_at"), FieldPanel("status"),
    ]

    class Meta:
        ordering = ["-closed_at", "reference"]
        verbose_name = "Giao dịch doanh thu"
        verbose_name_plural = "Giao dịch doanh thu"

    def __str__(self):
        return f"{self.reference} — {self.amount:,.0f} VNĐ"


class LandingPage(Page):
    """Editable public homepage for the digital-transformation CRM demo."""

    hero_title = models.CharField("Tiêu đề chính", max_length=180, default="Công nghệ nên giúp công việc")
    hero_emphasis = models.CharField("Cụm từ nhấn mạnh", max_length=100, default="trôi chảy hơn.")
    hero_text = models.TextField(
        "Mô tả chính",
        default="Kết nối quy trình bán hàng, quản lý vận hành và dữ liệu trên những giải pháp phù hợp với cách doanh nghiệp bạn đang làm việc.",
    )
    solutions_heading = models.CharField("Tiêu đề khu vực giải pháp", max_length=180, default="Những mảnh ghép cho một vận hành gọn hơn.")
    solutions_intro = models.TextField(
        "Giới thiệu giải pháp",
        default="Không phải doanh nghiệp nào cũng cần cùng một bộ công cụ. Hãy bắt đầu từ điểm nghẽn đang làm đội ngũ mất thời gian nhất.",
    )
    solutions = StreamField(
        [
            ("solution", blocks.StructBlock([
                ("icon", blocks.CharBlock(max_length=8, required=False)),
                ("category", blocks.CharBlock(max_length=60)),
                ("title", blocks.CharBlock(max_length=100)),
                ("description", blocks.TextBlock()),
                ("link_label", blocks.CharBlock(max_length=60, default="Trao đổi về giải pháp")),
            ], icon="list-ul")),
        ], blank=True, use_json_field=True, verbose_name="Các giải pháp",
    )
    approach_heading = models.CharField("Tiêu đề cách làm", max_length=180, default="Bắt đầu từ bài toán. Không bắt đầu từ phần mềm.")
    approach_intro = models.TextField(
        "Giới thiệu cách làm",
        default="Một giải pháp có ích phải phù hợp với con người và quy trình sử dụng nó.",
    )
    approach_steps = StreamField(
        [
            ("step", blocks.StructBlock([
                ("title", blocks.CharBlock(max_length=100)),
                ("description", blocks.TextBlock()),
            ], icon="list-ol")),
        ], blank=True, use_json_field=True, verbose_name="Các bước triển khai",
    )
    contact_heading = models.CharField("Tiêu đề liên hệ", max_length=160, default="Chia sẻ điều bạn muốn cải thiện.")
    contact_intro = models.TextField(
        "Giới thiệu liên hệ",
        default="Chọn nhóm giải pháp và chia sẻ nhu cầu. Đội ngũ sẽ xem xét yêu cầu, sau đó liên hệ để trao đổi bước tiếp theo.",
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel([FieldPanel("hero_title"), FieldPanel("hero_emphasis"), FieldPanel("hero_text")], heading="Hero"),
        MultiFieldPanel([FieldPanel("solutions_heading"), FieldPanel("solutions_intro"), FieldPanel("solutions")], heading="Giải pháp"),
        MultiFieldPanel([FieldPanel("approach_heading"), FieldPanel("approach_intro"), FieldPanel("approach_steps")], heading="Cách làm"),
        MultiFieldPanel([FieldPanel("contact_heading"), FieldPanel("contact_intro")], heading="Liên hệ"),
    ]

    parent_page_types = ["wagtailcore.Page"]
    subpage_types = []

    class Meta:
        verbose_name = "Trang chủ doanh nghiệp"

    def get_context(self, request, *args, **kwargs):
        from django.conf import settings as django_settings
        from .forms import PublicLeadRequestForm

        context = super().get_context(request, *args, **kwargs)
        context.update({
            "form": PublicLeadRequestForm(request.POST or None),
            "brand_name": django_settings.PUBLIC_BRAND_NAME,
            "contact_email": django_settings.PUBLIC_CONTACT_EMAIL,
            "contact_email_is_demo": django_settings.PUBLIC_CONTACT_EMAIL.lower().endswith(
                (".test", ".example", ".invalid")
            ),
        })
        return context

    def serve(self, request, *args, **kwargs):
        if request.method == "POST":
            from django.shortcuts import redirect
            from .forms import PublicLeadRequestForm
            from .views import save_public_lead_request

            form = PublicLeadRequestForm(request.POST)
            if form.is_valid():
                save_public_lead_request(form.cleaned_data)
                return redirect("crm:lead_request_success")
        return super().serve(request, *args, **kwargs)
