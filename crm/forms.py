from django import forms
from django.conf import settings

from .models import LeadFollowUpResponse, LeadRequest


class PublicLeadRequestForm(forms.Form):
    full_name = forms.CharField(
        label="Họ và tên",
        max_length=160,
        widget=forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Ví dụ: Nguyễn Minh Anh"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "ban@example.com"}),
    )
    phone = forms.CharField(
        label="Số điện thoại (không bắt buộc)",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "tel", "placeholder": "Không bắt buộc"}),
    )
    company = forms.CharField(
        label="Công ty (không bắt buộc)",
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "organization", "placeholder": "Không bắt buộc"}),
    )
    solution_interest = forms.ChoiceField(
        label="Giải pháp bạn quan tâm",
        choices=(("", "Chọn nhóm giải pháp"), *LeadRequest.SolutionInterest.choices),
        widget=forms.Select(),
    )
    request_text = forms.CharField(
        label="Bạn đang cần hỗ trợ điều gì?",
        max_length=2000,
        widget=forms.Textarea(attrs={
            "rows": 5,
            "placeholder": "Ví dụ: Đội ngũ đang quản lý khách hàng bằng bảng tính và muốn tìm hiểu CRM cho 10 nhân viên…",
        }),
    )
    consent = forms.BooleanField(
        label="",
        error_messages={"required": "Vui lòng xác nhận đồng ý trước khi gửi yêu cầu."},
    )
    ai_processing_consent = forms.BooleanField(required=False, label="")
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in {"consent", "ai_processing_consent", "website"}:
                field.widget.attrs["class"] = "form-input"
        self.fields["consent"].label = (
            f"Tôi đồng ý để {settings.PUBLIC_DATA_CONTROLLER_NAME} sử dụng thông tin đã cung cấp "
            "để tiếp nhận, lưu hồ sơ và phản hồi yêu cầu tư vấn của tôi."
        )
        self.fields["ai_processing_consent"].label = (
            "Tôi đồng ý (không bắt buộc) cho phép phân tích nội dung nhu cầu và giải pháp quan tâm bằng AI "
            "để tạo gợi ý nội bộ. Nếu dùng Google Gemini, nội dung này có thể được gửi đến Google; "
            "tên, email và số điện thoại được lược bỏ. Vui lòng đọc Thông báo quyền riêng tư trước khi chọn."
        )
        self.fields["website"].widget.attrs["class"] = "form-honeypot"

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_website(self):
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError("Không thể gửi yêu cầu này.")
        return value


class LeadFollowUpComposeForm(forms.Form):
    question_text = forms.CharField(
        label="Nội dung email",
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 5, "class": "form-input"}),
        initial=(
            "Để chuẩn bị tư vấn sát với nhu cầu của anh/chị, vui lòng bổ sung một vài thông tin "
            "trong biểu mẫu bảo mật bên dưới. Anh/chị chỉ cần chia sẻ những nội dung phù hợp."
        ),
    )


class LeadFollowUpResponseForm(forms.Form):
    current_challenge = forms.CharField(
        label="Khó khăn hoặc quy trình hiện tại",
        max_length=2000,
        widget=forms.Textarea(attrs={
            "rows": 4,
            "class": "form-input",
            "placeholder": "Bạn đang gặp khó khăn gì trong công việc hiện tại?",
        }),
    )
    desired_outcome = forms.CharField(
        label="Bạn mong muốn đạt được kết quả gì?",
        max_length=2000,
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 3,
            "class": "form-input",
            "placeholder": "Không bắt buộc",
        }),
    )
    implementation_timing = forms.ChoiceField(
        label="Thời điểm dự kiến triển khai",
        required=False,
        choices=(("", "Chưa xác định"), *LeadFollowUpResponse.ImplementationTiming.choices),
        widget=forms.Select(attrs={"class": "form-input"}),
    )
    preferred_contact_time = forms.CharField(
        label="Thời gian tiện liên hệ",
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "Ví dụ: 9:00–11:00 các ngày trong tuần",
        }),
    )
    ai_processing_consent = forms.BooleanField(required=False, label="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ai_processing_consent"].label = (
            "Tôi đồng ý (không bắt buộc) cho phép phân tích AI phần trả lời này để tạo gợi ý nội bộ. "
            "Nếu dùng Google Gemini, nội dung có thể được gửi tới Google. Không nhập dữ liệu nhạy cảm "
            "hoặc bí mật kinh doanh."
        )
