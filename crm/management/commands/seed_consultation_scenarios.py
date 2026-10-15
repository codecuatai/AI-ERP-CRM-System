"""Add explicitly fictional B2B consultation cases without overwriting existing data."""

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.test.utils import override_settings
from django.utils import timezone

from crm.models import AIAnalysis, Customer, Interaction, LeadRequest
from crm.services.ai_service import analyze_customer


class Command(BaseCommand):
    help = "Thêm 8 tình huống tư vấn B2B minh họa; tùy chọn phân tích các hồ sơ này."

    def add_arguments(self, parser):
        parser.add_argument("--analyze", action="store_true")
        parser.add_argument("--rules-only", action="store_true")
        parser.add_argument("--reanalyze", action="store_true")
        parser.add_argument("--case", action="append", dest="case_ids")

    def handle(self, *args, **options):
        fixture = json.loads((Path(__file__).resolve().parents[2] / "data" / "consultation_scenarios.json").read_text(encoding="utf-8"))
        for case in fixture["cases"]:
            if options["case_ids"] and case["id"] not in options["case_ids"]:
                continue
            customer, created = Customer.objects.get_or_create(
                email=f"scenario.{case['id']}@consultation.test",
                defaults={"full_name": case["name"], "company": case["company"],
                          "source": "Tình huống tư vấn minh họa", "notes": fixture["provenance"]},
            )
            if not customer.source == "Tình huống tư vấn minh họa":
                self.stdout.write(f"Bỏ qua hồ sơ đã được người dùng quản lý: {customer.pk}")
                continue
            lead, new_lead = LeadRequest.objects.get_or_create(
                customer=customer, request_text=case["request"],
                defaults={"solution_interest": case["solution"], "ai_processing_consent": case["consent"],
                          "ai_processing_consent_at": timezone.now() if case["consent"] else None},
            )
            if new_lead:
                Interaction.objects.create(
                    customer=customer, subject="Yêu cầu tư vấn minh họa B2B", content=case["request"],
                    ai_processing_consent=case["consent"],
                )
                if case["chat"]:
                    Interaction.objects.create(
                        customer=customer, subject="Lịch sử trao đổi cùng Trợ lý AI",
                        content="\n".join(("Khách hàng" if x["role"] == "user" else "DigiFlow AI") + ": " + x["content"] for x in case["chat"]),
                        ai_processing_consent=case["consent"],
                    )
            result = None
            if options["analyze"] and case["consent"] and (options["reanalyze"] or not customer.ai_analyses.exists()):
                if options["rules_only"]:
                    with override_settings(GEMINI_API_KEY=""):
                        result = analyze_customer(customer, permitted_requests=[lead])
                else:
                    result = analyze_customer(customer, permitted_requests=[lead])
                analysis = AIAnalysis.objects.create(customer=customer, **result)
                customer.ai_segment, customer.ai_score = analysis.segment, analysis.score
                customer.save(update_fields=["ai_segment", "ai_score", "updated_at"])
            self.stdout.write(json.dumps({"case": case["id"], "customer_id": customer.pk,
                "created": created, "consent": case["consent"],
                "expected": case["expected_segment"], "actual": customer.ai_segment,
                "provider": result["provider"] if result else "không chạy lại"}, ensure_ascii=False))
        self.stdout.write("Đây là dữ liệu minh họa; không đại diện khách hàng thật. Không gửi email.")
