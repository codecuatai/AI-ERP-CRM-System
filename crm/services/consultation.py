"""Shared validation and conservative intent detection for Vietnamese B2B advice."""

import re
import unicodedata


def normalize_text(text):
    return unicodedata.normalize("NFC", str(text or "")).casefold()


def contains_phrase(text, phrase):
    return bool(re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", normalize_text(text)))


def clean_chat_history(history, limit=12):
    if not isinstance(history, list):
        return []
    return [
        {"role": item["role"], "content": item["content"].strip()[:1000]}
        for item in history[-limit:]
        if isinstance(item, dict)
        and item.get("role") in ("user", "assistant")
        and isinstance(item.get("content"), str)
        and item["content"].strip()
    ]


def detect_solution_intent(text):
    # Specific integration/infrastructure requests take precedence over incidental
    # mentions of customers, CRM or inventory in a description of a connector.
    groups = (
        ("INTEGRATION", ("tích hợp", "kết nối hệ thống", "đồng bộ hệ thống")),
        ("INFRASTRUCTURE", ("máy chủ", "server", "cloud", "sao lưu", "backup", "bảo mật", "hạ tầng")),
        ("ERP", ("pos", "thu ngân", "tính tiền", "quầy", "mã vạch", "kho", "kiểm kê", "bán lẻ")),
        ("CRM", ("crm",)),
        ("AI", ("ai", "trí tuệ nhân tạo", "tự động hóa", "automation", "chatbot")),
        ("CRM", ("khách hàng", "chăm sóc", "sales", "tiềm năng", "lead")),
        ("INTEGRATION", ("api",)),
    )
    for solution, phrases in groups:
        if any(contains_phrase(text, phrase) for phrase in phrases):
            return solution
    return "OTHER"


def contextual_solution(message, history=None):
    solution = detect_solution_intent(message)
    if solution == "OTHER":
        for item in reversed(clean_chat_history(history)):
            if item["role"] == "user":
                solution = detect_solution_intent(item["content"])
                if solution != "OTHER":
                    break
    return solution
