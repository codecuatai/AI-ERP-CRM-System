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
        reason = (
            "Khách hàng thuộc phân khúc VIP với tổng mức chi tiêu lũy kế lớn (trên 20 triệu đồng) trong hệ thống giải pháp chuyển đổi số. "
            "Doanh nghiệp có tính cam kết cao, quy trình vận hành gắn kết tốt với các giải pháp của DigiFlow. "
            "Tiềm năng mở rộng (Cross-sell/Up-sell) sang các phân hệ bổ trợ như hạ tầng Cloud bảo mật cao, tích hợp ERP toàn diện hoặc tự động hóa AI là rất lớn. "
            "Rủi ro rời bỏ thấp nhưng cần duy trì chất lượng hỗ trợ dịch vụ kỹ thuật và kênh kết nối trực tiếp với cấp quản lý."
        )
        recommendation = (
            "Checklist 1: Khảo sát định kỳ & Đánh giá hiệu suất hệ thống đang vận hành\n"
            "Hành động cụ thể: Liên hệ trực tiếp Ban Giám đốc hoặc Trưởng bộ phận phụ trách để khảo sát độ hài lòng và ghi nhận phản hồi vận hành thực tế.\n"
            "Mục tiêu: Củng cố mức độ tin cậy và đảm bảo hệ thống vận hành trơn tru 100%.\n"
            "Thời hạn khuyến nghị: Trong vòng 3 ngày làm việc.\n\n"
            "Checklist 2: Tư vấn nâng cấp phân hệ & Tối ưu luồng dữ liệu tự động\n"
            "Hành động cụ thể: Soạn hồ sơ đề xuất tích hợp liên thông các phân hệ bổ trợ (POS - CRM - Quản lý Kho) nhằm loại bỏ thao tác nhập liệu thủ công.\n"
            "Mục tiêu: Nâng cao năng suất nghiệp vụ và gia tăng giá trị vòng đời hợp đồng.\n"
            "Thời hạn khuyến nghị: Trong vòng 7 ngày.\n\n"
            "Checklist 3: Gia hạn hợp đồng dịch vụ & Cam kết dịch vụ đối tác chiến lược SLA VIP\n"
            "Hành động cụ thể: Gửi dự thảo phụ lục cam kết dịch vụ hỗ trợ ưu tiên 24/7 (SLA VIP) kèm chính sách ưu đãi cho hợp đồng năm tiếp theo.\n"
            "Mục tiêu: Đạt thỏa thuận gia hạn dài hạn trước khi kỳ hợp đồng hiện tại đáo hạn.\n"
            "Thời hạn khuyến nghị: Trong tháng này."
        )
    elif any(word in content for word in ("giá", "báo giá", "tư vấn", "triển khai", "demo", "erp", "pos", "crm", "cloud")):
        segment, score = Customer.Segment.POTENTIAL, 75
        reason = (
            "Khách hàng thuộc phân khúc Tiềm năng cao, thể hiện sự quan tâm trực tiếp và rõ nét đến các giải pháp chuyển đổi số "
            "(như phần mềm quản lý kho ERP, POS bán hàng, CRM chăm sóc khách hàng hoặc hạ tầng Cloud) thông qua các yêu cầu tư vấn và tương tác gần đây. "
            "Doanh nghiệp đang chủ động tìm kiếm công cụ để giải quyết các điểm nghẽn quản lý. "
            "Xác suất chuyển đổi thành hợp đồng chính thức rất cao nếu nhân viên kinh doanh tiếp cận đúng thời điểm với kịch bản giải pháp bám sát thực tế."
        )
        recommendation = (
            "Checklist 1: Cuộc gọi khảo sát nhu cầu chuyên sâu (Scoping Call)\n"
            "Hành động cụ thể: Nhân viên kinh doanh liên hệ người liên hệ chính để xác định rõ quy mô nhân sự, hệ thống hiện tại và ngân sách dự kiến.\n"
            "Mục tiêu: Nắm bắt chính xác bài toán nghiệp vụ cốt lõi và các điểm nghẽn vận hành của khách hàng.\n"
            "Thời hạn khuyến nghị: Trong vòng 24 giờ kể từ khi tiếp nhận.\n\n"
            "Checklist 2: Thiết lập kịch bản Demo giải pháp thực tế theo bài toán của khách\n"
            "Hành động cụ thể: Chuẩn bị dữ liệu mẫu và kịch bản demo giải pháp (ERP/POS/CRM) bám sát mô hình kinh doanh của doanh nghiệp trước buổi gặp.\n"
            "Mục tiêu: Giúp khách hàng trực tiếp trải nghiệm cách giải pháp tháo gỡ điểm nghẽn thực tế.\n"
            "Thời hạn khuyến nghị: Trong vòng 3 ngày làm việc.\n\n"
            "Checklist 3: Soạn thảo báo giá sơ bộ & Bảng phân tích hiệu quả ROI\n"
            "Hành động cụ thể: Gửi email tóm tắt các tính năng chính kèm bảng phân tích hiệu quả thu hồi vốn (ROI) và lộ trình triển khai chi tiết.\n"
            "Mục tiêu: Cung cấp đầy đủ căn cứ thuyết phục để khách hàng trình duyệt kế hoạch nội bộ.\n"
            "Thời hạn khuyến nghị: Trong vòng 5 ngày làm việc."
        )
    elif interaction_count == 0 and (not include_spending or customer.total_spent == 0):
        segment, score = Customer.Segment.UNCLASSIFIED, 25
        reason = (
            "Hồ sơ khách hàng mới khởi tạo hoặc được tạo nội bộ, chưa có đủ dữ liệu lịch sử trao đổi và giao dịch chi tiêu để đánh giá chính xác. "
            "Cần thực hiện các bước tiếp cận ban đầu để chuẩn hóa thông tin doanh nghiệp, xác định người đại diện có thẩm quyền và nhận diện bài toán chuyển đổi số cần ưu tiên."
        )
        recommendation = (
            "Checklist 1: Thu thập và chuẩn hóa thông tin cơ bản của doanh nghiệp\n"
            "Hành động cụ thể: Tìm kiếm thông tin mã số thuế, website, lĩnh vực hoạt động và cập nhật đầy đủ vào hồ sơ khách hàng trên CRM.\n"
            "Mục tiêu: Xây dựng bức tranh toàn cảnh về quy mô và đặc thù kinh doanh của khách hàng.\n"
            "Thời hạn khuyến nghị: Trong vòng 24 giờ.\n\n"
            "Checklist 2: Gửi email giới thiệu giải pháp & Lời mời trao đổi sơ bộ\n"
            "Hành động cụ thể: Soạn email giới thiệu ngắn gọn các giải pháp thế mạnh của DigiFlow (ERP, POS, CRM, Cloud) và mời một cuộc trao đổi ngắn.\n"
            "Mục tiêu: Khơi gợi sự quan tâm và kết nối trực tiếp với người phụ trách chuyển đổi số.\n"
            "Thời hạn khuyến nghị: Trong vòng 2 ngày làm việc.\n\n"
            "Checklist 3: Đặt lịch follow-up và lưu trữ tương tác đầu tiên\n"
            "Hành động cụ thể: Tạo việc nhắc nhở liên hệ lại sau 3 ngày và ghi nhận đầy đủ phản hồi đầu tiên vào hệ thống để AI tiếp tục phân tích.\n"
            "Mục tiêu: Kích hoạt dòng tương tác và chuyển trạng thái khách hàng sang phễu tiềm năng.\n"
            "Thời hạn khuyến nghị: Trong vòng 5 ngày."
        )
    else:
        segment, score = Customer.Segment.POTENTIAL, 55
        reason = (
            f"Hồ sơ đã ghi nhận {interaction_count} tương tác trao đổi. Khách hàng đang trong quá trình cân nhắc phương án hoặc theo dõi giải pháp. "
            "Cần duy trì kết nối đều đặn, bổ sung thêm thông tin về hiện trạng hạ tầng và lộ trình triển khai để phân loại chính xác mức độ ưu tiên."
        )
        recommendation = (
            "Checklist 1: Liên hệ cập nhật tiến độ và ghi nhận phản hồi mới nhất\n"
            "Hành động cụ thể: Gọi điện hoặc gửi email hỏi thăm tiến độ đánh giá giải pháp của khách hàng sau các buổi trao đổi trước.\n"
            "Mục tiêu: Nắm bắt vướng mắc hoặc băn khoăn hiện tại của doanh nghiệp để kịp thời hỗ trợ.\n"
            "Thời hạn khuyến nghị: Trong vòng 48 giờ.\n\n"
            "Checklist 2: Cung cấp tài liệu Case Study doanh nghiệp tương đồng\n"
            "Hành động cụ thể: Gửi bản tin tóm tắt kết quả triển khai thành công giải pháp số tại một doanh nghiệp có quy mô và lĩnh vực tương tự.\n"
            "Mục tiêu: Gia tăng mức độ tin cậy và giải tỏa tâm lý e ngại rủi ro triển khai.\n"
            "Thời hạn khuyến nghị: Trong vòng 3 ngày.\n\n"
            "Checklist 3: Lập kế hoạch nhắc hẹn chăm sóc tiếp theo trên CRM\n"
            "Hành động cụ thể: Thiết lập việc chăm sóc định kỳ với hạn xử lý rõ ràng để không bỏ lỡ cơ hội chuyển đổi khi khách hàng sẵn sàng triển khai.\n"
            "Mục tiêu: Duy trì sự hiện diện chuyên nghiệp và chủ động của DigiFlow.\n"
            "Thời hạn khuyến nghị: Cuối tuần này."
        )
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
        remaining_slots = max(0, 20 - len(interactions))
        if remaining_slots > 0 and getattr(customer, "pk", None):
            ai_chats = customer.interactions.filter(subject__icontains="Trợ lý AI")[:remaining_slots]
            for chat in ai_chats:
                interactions.append(
                    SimpleNamespace(
                        kind="Hội thoại Trợ lý AI",
                        subject="Lịch sử trao đổi cùng AI",
                        content=chat.content[:2000],
                    )
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
    checklist_instructions = """
QUY ĐỊNH BẮT BUỘC:
1. 'segment': Phải là 1 trong 5 giá trị: VIP, POTENTIAL, HIBERNATING, CHURN_RISK, UNCLASSIFIED.
2. 'score': Số nguyên từ 0 đến 100 biểu thị điểm số tiềm năng.
3. 'summary': Phân tích CHI TIẾT, ĐÀO SÂU (2-3 đoạn văn phân tích rõ ràng):
   - Đánh giá hiện trạng bài toán nghiệp vụ và nhu cầu chuyển đổi số thực tế.
   - Tiềm năng giá trị khách hàng và cơ hội mở rộng giải pháp (Cross-sell/Up-sell).
   - Đánh giá rủi ro cạnh tranh hoặc rủi ro vận hành cần lưu ý.
4. 'recommendation': TUYỆT ĐỐI KHÔNG DÙNG DẤU GẠCH ĐẦU DÒNG THÔNG THƯỜNG (- hoặc •).
   BẮT BUỘC tổ chức thành từng CHECKLIST HÀNH ĐỘNG CỤ THỂ, ĐÁNH SỐ THỨ TỰ (Checklist 1, Checklist 2, Checklist 3,...).
   Mỗi checklist phải có định dạng rõ ràng:
   Checklist 1: [Tiêu đề hành động ngắn gọn]
   Hành động cụ thể: [Mô tả chi tiết việc nhân viên kinh doanh cần làm]
   Mục tiêu: [Kết quả mong đợi đạt được]
   Thời hạn khuyến nghị: [Ví dụ: Trong 24h / Trong 3 ngày / Trong tuần này]

   Checklist 2: [Tiêu đề hành động ngắn gọn]
   Hành động cụ thể: ...
   Mục tiêu: ...
   Thời hạn khuyến nghị: ...

   Checklist 3: [Tiêu đề hành động ngắn gọn]
   Hành động cụ thể: ...
   Mục tiêu: ...
   Thời hạn khuyến nghị: ...
"""

    if restricted_to_consented_requests:
        prompt = f"""Bạn là trợ lý phân tích CRM chuyển đổi số B2B. Chỉ dùng các nội dung nhu cầu đã được khách đồng ý cho phân tích.
Không suy đoán danh tính cá nhân. Chỉ trả về JSON hợp lệ với 4 trường: segment, score, summary, recommendation.
{checklist_instructions}

Giải pháp quan tâm và nội dung nhu cầu:
{history or 'Chưa có'}"""
    else:
        prompt = f"""Bạn là trợ lý phân tích CRM chuyển đổi số B2B. Dựa vào dữ liệu khách hàng dưới đây, phân loại và lập kế hoạch chăm sóc.
Chỉ trả về JSON hợp lệ với 4 trường: segment, score, summary, recommendation.
{checklist_instructions}

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
