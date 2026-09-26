import json

from django.conf import settings

from crm.models import Customer


def _rule_based_analysis(customer, interactions):
    interaction_count = len(interactions)
    content = " ".join(item.content.lower() for item in interactions)
    if customer.total_spent >= 20_000_000:
        segment, score = Customer.Segment.VIP, 90
        reason = "Tổng chi tiêu ở mức cao."
        recommendation = "Duy trì chăm sóc cá nhân hóa và giới thiệu chương trình khách hàng thân thiết."
    elif any(word in content for word in ("giá", "báo giá", "tư vấn", "triển khai", "demo")):
        segment, score = Customer.Segment.POTENTIAL, 75
        reason = "Lịch sử tương tác cho thấy khách đang tìm hiểu sản phẩm hoặc dịch vụ."
        recommendation = "Nhân viên kinh doanh nên liên hệ tư vấn nhu cầu và gửi thông tin phù hợp."
    elif interaction_count == 0 and customer.total_spent == 0:
        segment, score = Customer.Segment.UNCLASSIFIED, 25
        reason = "Chưa có lịch sử mua hàng hoặc tương tác để đánh giá."
        recommendation = "Bổ sung lịch sử trao đổi hoặc liên hệ để tìm hiểu nhu cầu khách hàng."
    else:
        segment, score = Customer.Segment.POTENTIAL, 55
        reason = f"Có {interaction_count} tương tác; cần thêm dữ liệu để phân loại chắc chắn hơn."
        recommendation = "Tiếp tục ghi nhận tương tác và theo dõi nhu cầu trước khi đề xuất bán hàng."
    return {"segment": segment, "score": score, "summary": reason, "recommendation": recommendation}


def analyze_customer(customer):
    """Use Gemini when configured; validate its result and fall back to local rules."""
    interactions = list(customer.interactions.all()[:20])
    fallback = _rule_based_analysis(customer, interactions)
    if not settings.GEMINI_API_KEY:
        return {**fallback, "provider": "rules"}

    history = "\n".join(f"- {item.kind}: {item.subject}. {item.content[:500]}" for item in interactions)
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
        from google import genai

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        data = json.loads(response.text)
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
