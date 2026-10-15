import json
from pathlib import Path

from django.core.management.base import BaseCommand

from crm.analytics.evaluation import evaluate_quality


class Command(BaseCommand):
    help = "Đo kết quả trên tình huống B2B minh họa và backtest doanh thu; không in metric ghi cứng."

    def add_arguments(self, parser):
        parser.add_argument("--provider", choices=("rules", "gemini", "stored"), default="rules")
        parser.add_argument("--output", type=Path)

    def handle(self, *args, **options):
        report = evaluate_quality(options["provider"])
        rendered = json.dumps(report, ensure_ascii=False, indent=2)
        if options["output"]:
            options["output"].parent.mkdir(parents=True, exist_ok=True)
            options["output"].write_text(rendered, encoding="utf-8")
        self.stdout.write(rendered)
