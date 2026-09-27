import json
from types import SimpleNamespace

from django.conf import settings

from crm.models import Customer


class AIConsentRequired(Exception):
    """Raised when a public lead has no recorded consent for AI analysis."""


def _rule_based_analysis(customer, interactions, include_spending=True):
    interaction_count = len(interactions)
    content = " ".join(item.content.lower() for item in interactions)
    if include_spending and customer.total_spent >= 20_000_000:
        segment, score = Customer.Segment.VIP, 90
        reason = "Tổng chi tiêu ở mức cao."
        recommendation = "Duy trì chăm sóc cá nhân hóa và giới thiệu chương trình khách hàng thân thiết."
    elif any(word in content for word in ("giá", "báo giá", "tư vấn", "triển khai", "demo")):
        segment, score = Customer.Segment.POTENTIAL, 75
        reason = "Lịch sử tương tác cho thấy khách đang tìm hiểu sản phẩm hoặc dịch vụ."
        recommendation = "Nhân viên kinh doanh nên liên hệ tư vấn nhu cầu và gửi thông tin phù hợp."
    elif interaction_count == 0 and (not include_spending or customer.total_spent == 0):
        segment, score = Customer.Segment.UNCLASSIFIED, 25
        reason = "Chưa có lịch sử mua hàng hoặc tương tác để đánh giá."
        recommendation = "Bổ sung lịch sử trao đổi hoặc liên hệ để tìm hiểu nhu cầu khách hàng."
    else:
        segment, score = Customer.Segment.POTENTIAL, 55
        reason = f"Có {interaction_count} tương tác; cần thêm dữ liệu để phân loại chắc chắn hơn."
        recommendation = "Tiếp tục ghi nhận tương tác và theo dõi nhu cầu trước khi đề xuất bán hàng."
    return {"segment": segment, "score": score, "summary": reason, "recommendation": recommendation}


def _request_gemini(prompt):
    from google import genai

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    return response.text


def analyze_customer(customer, permitted_requests=None, permitted_follow_up_responses=None):
    """Use Gemini when configured; validate its result and fall back to local rules."""
    if permitted_requests is None and permitted_follow_up_responses is None and customer.lead_requests.exists():
        raise AIConsentRequired("Public lead requests require explicit AI consent before analysis.")
    restricted_to_consented_requests = permitted_requests is not None or permitted_follow_up_responses is not None
    if restricted_to_consented_requests:
        permitted_requests = [
            request for request in (permitted_requests or []) if request.ai_processing_consent
        ]
        permitted_follow_up_responses = [
            response
            for response in (permitted_follow_up_responses or [])
            if response.ai_processing_consent
        ]
        if not permitted_requests and not permitted_follow_up_responses:
            raise AIConsentRequired("At least one item with AI consent is required.")
        interactions = [
            SimpleNamespace(
                kind="Yêu cầu tư vấn",
                subject=request.get_solution_interest_display(),
                content=request.request_text[:2000],
            )
            for request in permitted_requests[:20]
        ]
        remaining_slots = max(0, 20 - len(interactions))
        interactions.extend(
            SimpleNamespace(
                kind="Phản hồi bổ sung",
                subject="Thông tin khách hàng bổ sung",
                content=(
                    f"Khó khăn hiện tại: {response.current_challenge[:1500]}\n"
                    f"Kết quả mong muốn: {response.desired_outcome[:1000] or 'Chưa cung cấp'}\n"
                    f"Thời điểm dự kiến: {response.get_implementation_timing_display() or 'Chưa xác định'}"
                ),
            )
            for response in permitted_follow_up_responses[:remaining_slots]
        )
    else:
        interactions = list(customer.interactions.all()[:20])
    fallback = _rule_based_analysis(
        customer,
        interactions,
        include_spending=not restricted_to_consented_requests,
    )
    if not settings.GEMINI_API_KEY:
        return {**fallback, "provider": "rules"}

    history = "\n".join(f"- {item.kind}: {item.subject}. {item.content[:500]}" for item in interactions)
    if restricted_to_consented_requests:
        prompt = f"""Bạn là trợ lý phân tích CRM. Chỉ dùng các nội dung nhu cầu đã được khách đồng ý cho phân tích.
Không suy đoán danh tính cá nhân. Chỉ trả về JSON hợp lệ với các trường segment, score, summary, recommendation.
segment phải là một trong: VIP, POTENTIAL, HIBERNATING, CHURN_RISK, UNCLASSIFIED.
score là số nguyên từ 0 đến 100. summary và recommendation viết bằng tiếng Việt, ngắn gọn.

Giải pháp quan tâm và nội dung nhu cầu:
{history or 'Chưa có'}"""
    else:
        prompt = f"""Bạn là trợ lý phân tích CRM. Dựa vào dữ liệu dưới đây, phân loại khách hàng.
Chỉ trả về JSON hợp lệ với các trường segment, score, summary, recommendation.
segment phải là một trong: VIP, POTENTIAL, HIBERNATING, CHURN_RISK, UNCLASSIFIED.
score là số nguyên từ 0 đến 100. summary và recommendation viết bằng tiếng Việt, ngắn gọn.

Khách hàng: {customer.full_name}
Công ty: {customer.company or 'Chưa cung cấp'}
Tổng chi tiêu: {customer.total_spent} VND
Ghi chú: {customer.notes or 'Không có'}
Lịch sử tương tác:
{history or 'Chưa có'}"""
    try:
        response_text = _request_gemini(prompt)
        if not response_text:
            raise ValueError("Gemini trả về nội dung trống")
        data = json.loads(response_text)
        segment = data.get("segment")
        allowed = {choice for choice, _label in Customer.Segment.choices}
        if segment not in allowed:
            raise ValueError("Gemini trả về phân khúc không hợp lệ")
        score = max(0, min(100, int(data.get("score", fallback["score"]))))
        return {
            "segment": segment,
            "score": score,
            "summary": str(data.get("summary", fallback["summary"]))[:4000],
            "recommendation": str(data.get("recommendation", fallback["recommendation"]))[:4000],
            "provider": "gemini",
        }
    except Exception:
        return {**fallback, "provider": "rules"}
