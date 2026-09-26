"""
ai_services_demo.py — Service AI: rule-based + OpenAI + Gemini.
Chạy độc lập KHÔNG cần Django (để demo offline), copy vào crm/ai_services.py khi dựng Wagtail thật.
"""

import json
import os
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# 1. PHÂN LOẠI RULE-BASED (luôn chạy được, không cần API key → demo an toàn)
# ---------------------------------------------------------------------------

def classify_rule_based(revenue, order_count, days_since_last_order, ticket_count=0):
    """
    Logic RFM đơn giản:
    - VIP: doanh thu >= 20tr và mua gần đây (<=30 ngày)
    - Tiềm năng: mua thường xuyên (>=3 đơn) và gần đây (<=60 ngày)
    - Rời bỏ: có ticket phàn nàn + lâu không mua, hoặc >180 ngày
    - Ngủ đông: 90-180 ngày không mua
    """
    if ticket_count >= 3 and days_since_last_order > 60:
        return {"segment": "Rời bỏ", "code": "CHURN_RISK", "score": 25,
                "reason": f"{ticket_count} ticket phàn nàn + {days_since_last_order} ngày không mua."}
    if revenue >= 20_000_000 and days_since_last_order <= 30:
        return {"segment": "VIP", "code": "VIP", "score": 95,
                "reason": f"Chi tiêu {revenue:,.0f}đ, mua cách đây {days_since_last_order} ngày."}
    if order_count >= 3 and days_since_last_order <= 60:
        return {"segment": "Tiềm năng", "code": "POTENTIAL", "score": 75,
                "reason": f"{order_count} đơn, mua cách đây {days_since_last_order} ngày — nên upsell."}
    if days_since_last_order > 180:
        return {"segment": "Rời bỏ", "code": "CHURN_RISK", "score": 20,
                "reason": f"{days_since_last_order} ngày không mua — cần win-back."}
    if days_since_last_order > 90:
        return {"segment": "Ngủ đông", "code": "HIBERNATING", "score": 40,
                "reason": f"{days_since_last_order} ngày không mua — gửi ưu đãi kích hoạt."}
    return {"segment": "Tiềm năng", "code": "POTENTIAL", "score": 60,
            "reason": "Khách mới, cần nuôi dưỡng thêm."}


# ---------------------------------------------------------------------------
# 2. GỌI GEMINI (miễn phí) — dùng khi có GEMINI_API_KEY
# ---------------------------------------------------------------------------
CLASSIFY_PROMPT = """Bạn là chuyên gia CRM. Phân loại khách hàng sau thành 1 trong 4 nhóm:
VIP, Tiềm năng, Ngủ đông, Rời bỏ.
Dữ liệu: tên {name}, tổng chi tiêu {revenue} VND, {orders} đơn,
lần mua cuối {recency} ngày trước, {tickets} ticket hỗ trợ.
Trả về JSON duy nhất: {{"segment": "...", "score": 0-100, "reason": "..."}}"""

EMAIL_PROMPT = """Viết email chăm sóc khách hàng tiếng Việt, lịch sự,
cho {name} thuộc nhóm {segment}. Tổng chi tiêu {revenue} VND.
Gồm: tiêu đề, lời chào, 1 ưu đãi phù hợp, lời kêu gọi. Dưới 150 từ."""

REPORT_PROMPT = """Bạn là trợ lý kinh doanh. Dựa vào dữ liệu tuần:
- Tổng doanh thu: {revenue} VND, {orders} đơn, {new_customers} KH mới
- Top 3 KH: {top3}
Viết báo cáo tuần 5-7 dòng: điểm nổi bật, cảnh báo rời bỏ, gợi ý hành động tuần tới."""


def classify_with_gemini(name, revenue, orders, recency, tickets=0, api_key=None, model="gemini-1.5-flash"):
    """Gọi Google Gemini. Cần: pip install google-generativeai"""
    import google.generativeai as genai
    genai.configure(api_key=api_key or os.getenv("GEMINI_API_KEY"))
    m = genai.GenerativeModel(model)
    prompt = CLASSIFY_PROMPT.format(name=name, revenue=f"{revenue:,.0f}",
                                    orders=orders, recency=recency, tickets=tickets)
    resp = m.generate_content(prompt)
    text = resp.text.strip().replace("```json", "").replace("```", "").strip()
    data = json.loads(text)
    data["source"] = "gemini"
    return data


def suggest_email_gemini(name, segment, revenue, api_key=None, model="gemini-1.5-flash"):
    import google.generativeai as genai
    genai.configure(api_key=api_key or os.getenv("GEMINI_API_KEY"))
    m = genai.GenerativeModel(model)
    prompt = EMAIL_PROMPT.format(name=name, segment=segment, revenue=f"{revenue:,.0f}")
    return {"email": m.generate_content(prompt).text.strip(), "source": "gemini"}


# ---------------------------------------------------------------------------
# 3. GỌI OPENAI — dùng khi có OPENAI_API_KEY
# ---------------------------------------------------------------------------
def classify_with_openai(name, revenue, orders, recency, tickets=0, api_key=None, model="gpt-4o-mini"):
    """Cần: pip install openai"""
    from openai import OpenAI
    client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    prompt = CLASSIFY_PROMPT.format(name=name, revenue=f"{revenue:,.0f}",
                                    orders=orders, recency=recency, tickets=tickets)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    data = json.loads(resp.choices[0].message.content)
    data["source"] = "openai"
    return data


# ---------------------------------------------------------------------------
# 4. HÀM TỔNG: tự chọn Gemini → OpenAI → rule-based (không bao giờ crash demo)
# ---------------------------------------------------------------------------
def classify_customer_smart(name, revenue, orders, recency, tickets=0):
    if os.getenv("GEMINI_API_KEY"):
        try:
            return classify_with_gemini(name, revenue, orders, recency, tickets)
        except Exception as e:
            print(f"[AI] Gemini lỗi ({e}), thử OpenAI...")
    if os.getenv("OPENAI_API_KEY"):
        try:
            return classify_with_openai(name, revenue, orders, recency, tickets)
        except Exception as e:
            print(f"[AI] OpenAI lỗi ({e}), dùng rule-based...")
    r = classify_rule_based(revenue, orders, recency, tickets)
    r["source"] = "rule-based"
    return r


# ---------------------------------------------------------------------------
# 5. DEMO CHẠY TRỰC TIẾP: python ai_services_demo.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== DEMO AI ERP/CRM (offline, không cần API key) ===\n")
    samples = [
        ("Nguyễn Văn An", 45_000_000, 12, 5, 0),
        ("Trần Thị Bích", 8_500_000, 4, 20, 1),
        ("Lê Hoàng Cường", 3_200_000, 1, 120, 0),
        ("Phạm Minh Đức", 15_000_000, 6, 200, 4),
    ]
    for name, rev, orders, rec, tick in samples:
        r = classify_customer_smart(name, rev, orders, rec, tick)
        print(f"• {name}: {r['segment']} (điểm {r['score']}, nguồn: {r.get('source')})")
        print(f"  Lý do: {r['reason']}\n")
