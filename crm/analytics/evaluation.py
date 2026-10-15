"""Reproducible sanity checks; these small authored cases are not a production benchmark."""

import json
from collections import Counter
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from django.utils import timezone

from crm.analytics.ai_engine import RevenueForecastingEngine, SentimentChurnEngine
from crm.analytics.pipeline import AnalyticsPipeline
from crm.services.ai_service import _rule_based_analysis, analyze_customer
from crm.services.consultation import contextual_solution


def evaluate_quality(provider="rules"):
    dataset = json.loads((Path(__file__).resolve().parents[1] / "data" / "consultation_scenarios.json").read_text(encoding="utf-8"))
    engine = SentimentChurnEngine()
    sentiment = [{"text": text, "expected": label, "actual": engine.analyze(i, text).sentiment_label}
                 for i, (text, label) in enumerate(dataset["sentiment_cases"])]
    matrix = Counter((x["expected"], x["actual"]) for x in sentiment)
    f1s = []
    for label in ("POSITIVE", "NEUTRAL", "NEGATIVE"):
        tp = matrix[label, label]
        fp = sum(v for (expected, actual), v in matrix.items() if actual == label and expected != label)
        fn = sum(v for (expected, actual), v in matrix.items() if expected == label and actual != label)
        f1s.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0)
    segments, intents = [], []
    for case in dataset["cases"]:
        intents.append({"case": case["id"], "expected": case["solution"],
                        "actual": contextual_solution(case["request"], case["chat"])})
        if not case["consent"]:
            continue
        interactions = [SimpleNamespace(kind="Yêu cầu tư vấn", subject="Tình huống minh họa", content=case["request"])]
        customer = SimpleNamespace(pk=None, full_name="Hồ sơ minh họa", company="Minh họa", total_spent=Decimal("0"), notes="",
            lead_requests=SimpleNamespace(exists=lambda: False),
            interactions=SimpleNamespace(exclude=lambda **kwargs: interactions))
        if provider == "stored":
            from crm.models import AIAnalysis
            saved = AIAnalysis.objects.filter(customer__email=f"scenario.{case['id']}@consultation.test").first()
            result = ({"segment": saved.segment, "score": saved.score, "provider": saved.provider,
                       "summary": saved.summary, "recommendation": saved.recommendation} if saved else
                      {"segment": None, "score": None, "provider": "not_run", "summary": "Chưa có kết quả lưu", "recommendation": ""})
        elif provider == "gemini":
            result = analyze_customer(customer)
        else:
            result = {**_rule_based_analysis(customer, interactions), "provider": "rules"}
        segments.append({"case": case["id"], "expected": case["expected_segment"],
                         "actual": result["segment"], "score": result["score"],
                         "provider": result["provider"], "summary": result["summary"],
                         "recommendation": result["recommendation"]})
    history = AnalyticsPipeline().revenue_history()
    backtest = []
    forecast = RevenueForecastingEngine()
    for i in range(max(3, len(history) - 4), len(history)):
        point = forecast.forecast_next_months(history[:i], months_ahead=1)[0]
        actual = history[i][1]
        backtest.append({"month": str(history[i][0]), "actual": actual,
                         "prediction": point.predicted_revenue, "model": point.model_name,
                         "linear_prediction": forecast.predict_value([v for _, v in history[:i]], "LINEAR"),
                         "naive_previous_month": history[i - 1][1]})
    n = len(backtest)
    return {
        "evaluated_at": timezone.now().isoformat(),
        "dataset_version": dataset["version"], "provenance": dataset["provenance"],
        "limitations": "Tập tình huống nhỏ do nhóm biên soạn, có dùng để sửa rules; không suy rộng độ chính xác ra khách hàng thật. Điểm lead chưa hiệu chuẩn xác suất. Chưa có nhãn WON/LOST để đo ROC-AUC.",
        "sentiment": {"sample_size": len(sentiment),
            "accuracy": sum(x["expected"] == x["actual"] for x in sentiment) / len(sentiment),
            "macro_f1": sum(f1s) / len(f1s), "cases": sentiment},
        "solution_intent": {"sample_size": len(intents), "correct": sum(x["expected"] == x["actual"] for x in intents), "cases": intents},
        "customer_segments": {"sample_size": len(segments), "correct": sum(x["expected"] == x["actual"] for x in segments),
                              "requested_provider": provider, "cases": segments},
        "revenue_backtest": {"sample_size": n, "unit": "VND",
            "mae": sum(abs(x["actual"] - x["prediction"]) for x in backtest) / n if n else None,
            "naive_mae": sum(abs(x["actual"] - x["naive_previous_month"]) for x in backtest) / n if n else None,
            "linear_mae": sum(abs(x["actual"] - x["linear_prediction"]) for x in backtest) / n if n else None,
            "selected_model": forecast.select_model([v for _, v in history])["model"] if len(history) >= 3 else None,
            "cases": backtest, "note": "Rolling origin tối đa 4 tháng, chọn mô hình chỉ từ tiền tố quá khứ. Chính sách thận trọng: ít hơn 18 tháng dùng baseline; mô hình khác cần ít nhất 5 fold nội bộ, cải thiện MAE 10% và tốt hơn ở 2 fold gần nhất. Đây là ngưỡng vận hành, không bảo đảm vượt baseline trong tương lai. Dữ liệu có thể là demo."},
    }
