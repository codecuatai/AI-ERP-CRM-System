import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Kịch bản tư vấn kiến thức giải pháp chuyển đổi số DigiFlow
DIGIFLOW_KNOWLEDGE_BASE = {
    "pricing": (
        "Về chi phí triển khai: DigiFlow áp dụng mô hình module hóa linh hoạt theo quy mô thực tế "
        "của doanh nghiệp (không ép buộc mua trọn gói cồng kềnh).\n\n"
        "• Gói khởi điểm (Kho & Bán hàng hoặc POS): chỉ từ vài triệu đồng/tháng tùy số lượng điểm bán và người dùng.\n"
        "• Gói CRM & Chăm sóc khách hàng thông minh: tính theo số lượng tài khoản kinh doanh và nhu cầu phân tích AI.\n"
        "• Triển khai máy chủ riêng & Cloud: chi phí hạ tầng tối ưu trên Docker & PostgreSQL.\n\n"
        "Anh/chị có thể để lại thông tin ở tab 'Điền form' để kỹ sư DigiFlow gửi bảng dự toán chi phí chi tiết theo quy mô của bên mình!"
    ),
    "timeline": (
        "Về thời gian triển khai: Nhờ kiến trúc Docker hóa và các module đã được chuẩn hóa, "
        "thời gian triển khai thông thường tại DigiFlow chỉ mất từ **2 đến 4 tuần** (nhanh gấp 3 lần so với ERP truyền thống):\n\n"
        "1. Tuần 1: Khảo sát quy trình và thống nhất bài toán thực tế.\n"
        "2. Tuần 2: Cấu hình hệ thống, chuẩn hóa và nhập dữ liệu ban đầu.\n"
        "3. Tuần 3: Đào tạo 1:1 cho đội ngũ nhân viên và chạy thử nghiệm (UAT).\n"
        "4. Tuần 4: Chính thức golive và đồng hành hỗ trợ vận hành 24/7."
    ),
    "inventory": (
        "Về giải pháp Quản lý kho & Bán hàng:\n\n"
        "• Quản lý tồn kho đa điểm, đa chi nhánh theo thời gian thực.\n"
        "• Tự động cảnh báo khi tồn kho chạm ngưỡng an toàn, hạn chế thất thoát hàng hóa.\n"
        "• Quản lý quy trình xuất - nhập - chuyển kho và kiểm kê định kỳ bằng mã vạch/QR.\n"
        "• Kết nối đồng bộ dữ liệu tức thời với hệ thống POS bán hàng và bộ phận kinh doanh."
    ),
    "pos": (
        "Về giải pháp POS & Bán hàng đa kênh:\n\n"
        "• Giao diện tính tiền tốc độ cao, hỗ trợ thao tác cảm ứng trên máy POS, tablet hoặc máy tính.\n"
        "• Tích hợp thanh toán QR Code động, máy quẹt thẻ ngân hàng và máy in hóa đơn điện tử chuẩn thuế.\n"
        "• Mọi giao dịch bán hàng tại quầy lập tức trừ tồn kho trung tâm và đồng bộ doanh thu vào báo cáo."
    ),
    "crm": (
        "Về giải pháp DigiFlow AI CRM:\n\n"
        "• Tập trung 100% dữ liệu khách hàng và lịch sử trao đổi tại một nơi duy nhất.\n"
        "• Trợ lý AI hỗ trợ phân loại phân khúc (VIP, Tiềm năng, Rủi ro) và chấm điểm ưu tiên chăm sóc.\n"
        "• Quản lý hàng đợi công việc (Care Tasks), tự động nhắc việc quá hạn cho nhân viên kinh doanh.\n"
        "• Hỗ trợ soạn thảo email/tin nhắn nháp thông minh, nhân viên luôn là người kiểm duyệt cuối cùng (Human-in-the-loop)."
    ),
    "security": (
        "Về bảo mật & Hạ tầng dữ liệu:\n\n"
        "• DigiFlow triển khai hệ thống độc lập trên Docker và cơ sở dữ liệu PostgreSQL máy chủ riêng biệt.\n"
        "• Dữ liệu được mã hóa và sao lưu (backup) tự động định kỳ đa vùng bảo mật 256-bit.\n"
        "• Cam kết tuân thủ nghiêm ngặt quy định về bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP."
    ),
    "integration": (
        "Về tích hợp hệ thống (System Integration):\n\n"
        "• DigiFlow cung cấp API mở chuẩn RESTful để kết nối mượt mà giữa CRM, Kho, POS, phần mềm kế toán và các sàn thương mại điện tử.\n"
        "• Đội ngũ kỹ sư sẽ khảo sát hệ thống hiện tại của bên mình để tư vấn phương án tích hợp không gây gián đoạn vận hành."
    ),
    "default": (
        "Chào anh/chị! Em là Trợ lý AI Chuyên viên Tư vấn Chuyển đổi số của DigiFlow.\n\n"
        "DigiFlow chuyên cung cấp các giải pháp công nghệ B2B thực chiến gồm:\n"
        "1. **Quản lý kho & Bán hàng** (đồng bộ đa kho, chống thất thoát)\n"
        "2. **POS Bán hàng đa kênh** (thanh toán QR, in hóa đơn điện tử)\n"
        "3. **AI CRM & Chăm sóc khách hàng** (tập trung dữ liệu, phân loại AI, nhắc việc)\n"
        "4. **Hạ tầng Cloud & Sao lưu dữ liệu** (máy chủ riêng bảo mật, sao lưu định kỳ)\n\n"
        "Anh/chị đang quan tâm đến giải pháp nào hoặc muốn tìm hiểu về chi phí/thời gian triển khai cho quy mô bên mình ạ?"
    ),
}


def _detect_solution_intent(text: str) -> str:
    """Xác định giải pháp khách hàng quan tâm dựa trên từ khóa câu hỏi."""
    lower = text.lower()
    if any(k in lower for k in ("crm", "khách hàng", "chăm sóc", "sales", "tiềm năng", "lead")):
        return "CRM"
    if any(k in lower for k in ("kho", "tồn kho", "nhập xuất", "kiểm kê", "hàng hóa")):
        return "ERP"
    if any(k in lower for k in ("pos", "thu ngân", "tính tiền", "bán lẻ", "quầy", "hóa đơn")):
        return "POS"
    if any(k in lower for k in ("máy chủ", "server", "cloud", "sao lưu", "backup", "bảo mật", "hạ tầng")):
        return "INFRASTRUCTURE"
    if any(k in lower for k in ("tích hợp", "api", "kết nối", "đồng bộ hệ thống")):
        return "INTEGRATION"
    if any(k in lower for k in ("ai", "trí tuệ nhân tạo", "tự động hóa", "automation")):
        return "AI"
    return "OTHER"


def _rule_based_chat_reply(message: str) -> dict:
    """Trả lời thông minh dựa trên knowledge base chuyên gia khi không dùng Gemini."""
    lower = message.lower()
    suggested_solution = _detect_solution_intent(message)

    if any(k in lower for k in ("giá", "chi phí", "bao nhiêu tiền", "báo giá", "bảng giá", "kinh phí", "ngân sách")):
        reply = DIGIFLOW_KNOWLEDGE_BASE["pricing"]
    elif any(k in lower for k in ("thời gian", "bao lâu", "tiến độ", "mất mấy ngày", "khi nào xong", "lộ trình")):
        reply = DIGIFLOW_KNOWLEDGE_BASE["timeline"]
    elif any(k in lower for k in ("kho", "tồn kho", "kiểm kê", "thất thoát", "xuất nhập")):
        reply = DIGIFLOW_KNOWLEDGE_BASE["inventory"]
    elif any(k in lower for k in ("pos", "thu ngân", "máy in", "hóa đơn", "quầy", "thanh toán qr")):
        reply = DIGIFLOW_KNOWLEDGE_BASE["pos"]
    elif any(k in lower for k in ("crm", "chăm sóc khách", "khách hàng", "lead", "sales", "email nháp")):
        reply = DIGIFLOW_KNOWLEDGE_BASE["crm"]
    elif any(k in lower for k in ("bảo mật", "sao lưu", "backup", "máy chủ", "server", "cloud", "nghị định 13")):
        reply = DIGIFLOW_KNOWLEDGE_BASE["security"]
    elif any(k in lower for k in ("tích hợp", "api", "kết nối", "phần mềm kế toán", "sàn")):
        reply = DIGIFLOW_KNOWLEDGE_BASE["integration"]
    else:
        reply = DIGIFLOW_KNOWLEDGE_BASE["default"]

    return {
        "reply": reply,
        "suggested_solution": suggested_solution,
        "provider": "rules",
    }


def _call_gemini_chat(message: str, history: list[dict] = None) -> str:
    """Gọi Gemini API để trả lời tự nhiên theo ngữ cảnh."""
    from google import genai

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    system_instruction = (
        "Bạn là Trợ lý AI Chuyên viên Tư vấn Chuyển đổi số của DigiFlow - doanh nghiệp chuyên cung cấp giải pháp B2B "
        "gồm: Quản lý kho & Bán hàng, POS & Bán hàng đa kênh, CRM & Chăm sóc khách hàng thông minh, Hạ tầng Cloud & Sao lưu dữ liệu, Tích hợp hệ thống.\n\n"
        "Nguyên tắc tư vấn:\n"
        "1. Trả lời bằng tiếng Việt thân thiện, chuyên nghiệp, súc tích (khoảng 2-4 đoạn ngắn).\n"
        "2. Đi thẳng vào giải pháp và lợi ích thực tế cho doanh nghiệp, không nói lý thuyết sáo rỗng.\n"
        "3. Nhấn mạnh ưu thế: Triển khai nhanh 2-4 tuần, chi phí module hóa linh hoạt, dữ liệu máy chủ riêng bảo mật theo Nghị định 13.\n"
        "4. Nếu khách hỏi về chi phí: Giải thích chi phí tính theo quy mô/module (khoảng vài triệu/tháng) và khuyến khích để lại thông tin để kỹ sư DigiFlow gửi bảng tính chi tiết.\n"
        "5. Không bịa đặt dịch vụ ngoài phạm vi (như tài chính kế toán chuyên sâu, xuất nhập khẩu quốc tế).\n"
        "6. Kết thúc câu trả lời một cách tự nhiên, gợi ý khách bấm chuyển sang tab 'Điền form' để nhận bản đề xuất giải pháp 1:1."
    )

    contents = []
    if history:
        for item in history[-6:]:  # Lấy tối đa 6 lượt trao đổi gần nhất
            role = "user" if item.get("role") == "user" else "model"
            text = str(item.get("content", ""))[:1000]
            if text:
                contents.append(f"{role.upper()}: {text}")
    
    contents.append(f"USER: {message}")
    prompt = f"{system_instruction}\n\nLỊCH SỬ TRAO ĐỔI:\n" + "\n".join(contents) + "\n\nMODEL:"

    primary_model = getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    models_to_try = [primary_model]
    for fallback_model in ("gemini-flash-lite-latest", "gemini-2.5-flash-lite"):
        if fallback_model not in models_to_try:
            models_to_try.append(fallback_model)

    last_err = None
    for m in models_to_try:
        try:
            response = client.models.generate_content(
                model=m,
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            last_err = e
            logger.info("Thử gọi model %s thất bại (%s), tiếp tục thử model dự phòng...", m, e)

    if last_err:
        raise last_err
    raise ValueError("Không nhận được phản hồi từ Gemini")


def answer_customer_question(message: str, history: list[dict] = None) -> dict:
    """
    Điểm vào chính: Nhận câu hỏi của khách hàng, trả lời qua Gemini nếu có cấu hình,
    hoặc fallback mượt mà qua knowledge base rules.
    """
    clean_message = (message or "").strip()
    if not clean_message:
        return {
            "reply": "Dạ em có thể hỗ trợ giải đáp thông tin gì về giải pháp chuyển đổi số cho anh/chị ạ?",
            "suggested_solution": "OTHER",
            "provider": "rules",
        }

    suggested_solution = _detect_solution_intent(clean_message)

    api_key = getattr(settings, "GEMINI_API_KEY", "").strip()
    if not api_key:
        return _rule_based_chat_reply(clean_message)

    import concurrent.futures
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(_call_gemini_chat, clean_message, history=history)
        reply_text = future.result(timeout=7.0)
        executor.shutdown(wait=False)
        if not reply_text:
            raise ValueError("Phản hồi Gemini rỗng")
        return {
            "reply": reply_text,
            "suggested_solution": suggested_solution,
            "provider": "gemini",
        }
    except Exception as exc:
        executor.shutdown(wait=False)
        logger.warning("Không thể gọi Gemini Chat API (%s), chuyển sang rules fallback tức thì.", exc)
        return _rule_based_chat_reply(clean_message)
