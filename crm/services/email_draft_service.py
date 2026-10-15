from django.conf import settings
import re

from crm.models import Customer, LeadFollowUpResponse


GOALS = {
    "thanks": "cảm ơn khách hàng đã trao đổi",
    "check_in": "hỏi thăm tiến độ và nhu cầu hiện tại",
    "meeting": "đề xuất sắp xếp một buổi trao đổi hoặc demo",
    "quote": "trao đổi về báo giá và phạm vi giải pháp",
    "reconnect": "kết nối lại một cách lịch sự sau một thời gian chưa liên hệ",
}


def _fallback_draft(goal, tone, customer, length="vừa", context_parts=()):
    first_name = customer.full_name.strip() or "Anh/Chị"
    openings = {
        "formal": f"Kính gửi {first_name},",
        "friendly": f"Chào {first_name},",
    }
    bodies = {
        "thanks": "Cảm ơn anh/chị đã dành thời gian trao đổi với chúng tôi. Chúng tôi rất trân trọng cơ hội tìm hiểu nhu cầu của doanh nghiệp.",
        "check_in": "Tôi xin phép hỏi thăm tình hình và nhu cầu hiện tại của doanh nghiệp. Nếu có điểm nào cần làm rõ, chúng tôi sẵn sàng cùng anh/chị trao đổi.",
        "meeting": "Nếu phù hợp, chúng tôi mong muốn sắp xếp một buổi trao đổi ngắn để tìm hiểu quy trình và giới thiệu hướng giải pháp phù hợp.",
        "quote": "Chúng tôi sẵn sàng trao đổi thêm về phạm vi và báo giá để bảo đảm đề xuất phù hợp với nhu cầu thực tế của doanh nghiệp.",
        "reconnect": "Đã một thời gian kể từ lần trao đổi trước, tôi xin phép kết nối lại để hỏi thăm kế hoạch và xem chúng tôi có thể hỗ trợ gì thêm không.",
    }
    signoff = "Trân trọng," if tone == "formal" else "Thân mến,"
    context = ""
    if context_parts and length != "ngắn":
        context = "\n\nNgữ cảnh đã ghi nhận: " + " ".join(context_parts)[:350]
    if length == "chi tiết":
        context += ("\n\nĐể chuẩn bị đề xuất phù hợp, anh/chị có thể xác nhận quy mô sử dụng, "
                    "điểm vướng ưu tiên và thời điểm mong muốn? Phạm vi, chi phí và tiến độ sẽ được "
                    "nhân viên xác nhận sau khảo sát; nội dung này chưa phải báo giá hay cam kết dịch vụ.")
    closing = "" if length == "ngắn" else "\n\nAnh/chị có thể phản hồi email này nếu muốn trao đổi thêm."
    return f"{openings.get(tone, openings['formal'])}\n\n{bodies[goal]}{context}{closing}\n\n{signoff}\nĐội ngũ tư vấn"


def create_email_draft(customer, goal, tone="formal", length="standard"):
    """Generate a human-reviewed draft; only consented public details may reach Gemini."""
    consented_requests = list(customer.lead_requests.filter(ai_processing_consent=True)[:5])
    consented_answers = list(LeadFollowUpResponse.objects.filter(
        follow_up__lead_request__customer=customer,
        ai_processing_consent=True,
    ).select_related("follow_up__lead_request")[:5])
    context_parts = [
        f"Nhóm giải pháp quan tâm: {item.get_solution_interest_display()}. "
        f"Nhu cầu khách đã đồng ý phân tích: {item.request_text[:800]}"
        for item in consented_requests
    ]
    context_parts.extend(f"Nhu cầu đã đồng ý phân tích: {item.current_challenge[:800]}" for item in consented_answers)
    fallback = _fallback_draft(goal, tone, customer, length, context_parts)
    if not settings.GEMINI_API_KEY or (customer.lead_requests.exists() and not consented_requests and not consented_answers):
        return {"draft": fallback, "provider": "rules"}
    context_text = "\n".join(context_parts) or "Không có thông tin khách hàng được phép dùng làm ngữ cảnh."
    prompt = (
        "Soạn email chăm sóc khách hàng B2B bằng tiếng Việt, chỉ trả nội dung email. "
        "Không bịa dữ kiện, không hứa hẹn điều chưa xác nhận, không đưa thông tin cá nhân vào email. "
        "Chưa có bảng giá hoặc danh mục gói được xác nhận. Không nói rằng có gói phù hợp ngân sách, "
        "đáp ứng đủ ngân sách hay chắc chắn triển khai đúng hạn; chỉ đề xuất khảo sát để xác nhận. "
        f"Mục tiêu: {GOALS[goal]}. Giọng văn: {tone}. Độ dài: {length}.\n"
        "Chỉ dùng thông tin bên dưới nếu có; đây là nội dung đã có consent AI.\n"
        f"{context_text}"
    )
    try:
        from google import genai

        client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options={"timeout": 15000})
        draft_response = client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt)
        draft = draft_response.text
        if not draft or len(draft.strip()) < 20:
            raise ValueError("Gemini trả về bản nháp rỗng hoặc quá ngắn")
        if re.search(r"(?:chúng tôi|digiflow)\s+(?:cam kết|đảm bảo|bảo đảm|có các gói|có gói)", draft, re.I):
            raise ValueError("Bản nháp có cam kết thương mại chưa được xác nhận")
        return {"draft": draft.strip()[:5000], "provider": "gemini"}
    except Exception:
        return {"draft": fallback, "provider": "rules"}
