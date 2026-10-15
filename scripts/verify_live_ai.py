"""Call configured Gemini only with explicitly fictional consultation content."""

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django
django.setup()

from crm.models import Customer
from crm.services.ai_chat_service import answer_customer_question
from crm.services.email_draft_service import create_email_draft

history = []
exchanges = []
for message in ("Doanh nghiệp minh họa có 3 kho và 2 quầy POS, muốn kiểm kê bằng mã vạch.",
                "Chi phí bao nhiêu và thời gian triển khai bao lâu?"):
    result = answer_customer_question(message, history)
    exchanges.append({"message": message, **result})
    history.extend([{"role":"user", "content":message}, {"role":"assistant", "content":result["reply"]}])
customer = Customer.objects.get(email="scenario.crm-sales@consultation.test")
draft = create_email_draft(customer, "meeting", "formal", "vừa")
report = {"provenance":"Hội thoại minh họa và hồ sơ scenario.crm-sales; không có dữ liệu khách hàng thật. Không gửi email.",
          "chat": exchanges, "email_draft": draft,
          "note":"Kiểm tra tích hợp thực tế và rà soát thủ công nội dung; không phải thước đo độ chính xác tổng quát."}
path = ROOT / "docs" / "validation" / "live-ai-conversation.json"
path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
