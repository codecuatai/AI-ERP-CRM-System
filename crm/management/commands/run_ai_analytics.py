"""Django management command to execute the AI Analytics pipeline and populate the analytics data mart."""

import sys
from django.core.management.base import BaseCommand
from crm.analytics.pipeline import AnalyticsPipeline

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class Command(BaseCommand):
    help = "Thực thi toàn bộ bộ mô hình AI phân tích dữ liệu CRM và nạp kết quả vào schema analytics cho Apache Superset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--evaluate",
            action="store_true",
            help="Hiển thị bảng đánh giá độ chính xác và hiệu năng của các mô hình AI.",
        )

    def handle(self, *args, **options):
        self.stdout.write("==> Đang khởi động AI Analytics Pipeline cho hệ thống CRM...")

        pipeline = AnalyticsPipeline()
        summary = pipeline.run_all()

        self.stdout.write(self.style.SUCCESS(
            f"✔ Hoàn tất xử lý AI Analytics Pipeline:\n"
            f"  - Leads chấm điểm & dự báo xác suất Win: {summary['leads_analyzed']}\n"
            f"  - Tương tác phân tích cảm xúc & rủi ro Churn: {summary['sentiments_analyzed']}\n"
            f"  - Khách hàng phân nhóm RFM theo tâm tham chiếu: {summary['customers_segmented']}\n"
            f"  - Chuỗi thời gian dự báo doanh thu: {summary['forecast_months']} tháng tới\n"
            f"  - Bất thường vận hành/giao dịch phát hiện: {summary['anomalies_detected']}"
        ))

        if options.get("evaluate"):
            from django.core.management import call_command
            call_command("evaluate_ai_quality", stdout=self.stdout)
