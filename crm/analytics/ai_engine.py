"""Core AI Engine for CRM Analytics and Predictive Modeling.

Provides 6 specialized AI models designed for B2B Digital Transformation CRM:
1. LeadWinRateModel: Lead Scoring & Win-rate probability classifier.
2. SentimentChurnEngine: Vietnamese B2B NLP sentiment & churn risk detection.
3. RFMSegmentationModel: RFM profile assignment to fixed reference centroids.
4. RevenueForecastingEngine: Validated baseline selection with exploratory error bands.
5. ExplainableAIEngine: Formula contributions and a heuristic decision explanation.
6. AnomalyDetectionEngine: Operational and transaction anomaly detection.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from crm.services.consultation import normalize_text


@dataclass
class LeadPredictionResult:
    lead_id: int
    win_probability: float
    tier: str  # HOT, WARM, COLD
    estimated_deal_value: float
    expected_won_value: float
    key_drivers: List[str]


@dataclass
class SentimentResult:
    interaction_id: int
    sentiment_score: float  # -1.0 to 1.0
    sentiment_label: str    # POSITIVE, NEUTRAL, NEGATIVE
    churn_risk_level: str   # LOW, MEDIUM, HIGH
    urgency_score: float    # 0.0 to 1.0


@dataclass
class RFMSegmentResult:
    customer_id: int
    recency_days: int
    frequency: int
    monetary: float
    cluster_id: int
    cluster_name: str


@dataclass
class ForecastPoint:
    forecast_date: date
    predicted_revenue: float
    lower_bound_95: float
    upper_bound_95: float
    trend_direction: str
    model_name: str = "NAIVE"


@dataclass
class AnomalyAlert:
    entity_type: str  # LEAD, TASK, TRANSACTION
    entity_id: int
    severity: str     # HIGH, MEDIUM, LOW
    description: str
    metric_value: float


# ─────────────────────────────────────────────────────────────────────────────
# 1. LEAD SCORING & WIN-RATE CLASSIFIER
# ─────────────────────────────────────────────────────────────────────────────

class LeadWinRateModel:
    """Untrained sigmoid prioritization score; not a calibrated conversion probability."""

    SOLUTION_BASE_RATES: Dict[str, float] = {
        "CRM": 0.58,
        "ERP": 0.52,
        "POS": 0.65,
        "INFRASTRUCTURE": 0.48,
        "INTEGRATION": 0.45,
        "AI": 0.40,
        "OTHER": 0.35,
    }

    @staticmethod
    def _sigmoid(z: float) -> float:
        return 1.0 / (1.0 + math.exp(-max(min(z, 15.0), -15.0)))

    def feature_contributions(
        self,
        priority_score: int,
        interaction_count: int,
        has_phone: bool,
        has_company: bool,
        request_text_length: int,
        solution_interest: str,
        response_time_hours: Optional[float] = None,
    ) -> Dict[str, float]:
        speed = (1.0 if response_time_hours <= 4 else (0.5 if response_time_hours <= 24 else 0.2)) if response_time_hours is not None else 0.0
        return {
            "Điểm nhu cầu": 2.2 * min(max(priority_score, 0), 100) / 100.0,
            "Tần suất tương tác": 1.8 * min(max(interaction_count, 0) / 5.0, 1.0),
            "Thông tin liên hệ đầy đủ": 1.2 * (0.5 * bool(has_phone) + 0.5 * bool(has_company)),
            "Mức chi tiết nhu cầu": 0.8 * min(max(request_text_length, 0) / 150.0, 1.0),
            "Tốc độ gửi form hỏi thêm đã ghi nhận": 0.9 * speed,
            "Nhóm giải pháp": (self.SOLUTION_BASE_RATES.get(solution_interest, 0.40) - 0.5) * 2,
        }

    def predict(
        self,
        lead_id: int,
        solution_interest: str,
        priority_score: int,
        interaction_count: int,
        has_phone: bool,
        has_company: bool,
        request_text_length: int,
        response_time_hours: Optional[float] = None,
        customer_segment: str = "",
    ) -> LeadPredictionResult:
        norm_priority = min(max(priority_score, 0), 100) / 100.0

        # Feature normalization
        contact_quality = (0.5 if has_phone else 0.0) + (0.5 if has_company else 0.0)
        speed_factor = (1.0 if response_time_hours <= 4.0 else (0.5 if response_time_hours <= 24.0 else 0.2)) if response_time_hours is not None else 0.0

        # Linear combination logit
        z = sum(self.feature_contributions(
            priority_score, interaction_count, has_phone, has_company,
            request_text_length, solution_interest, response_time_hours,
        ).values()) - 2.8

        win_prob = round(self._sigmoid(z), 3)
        if customer_segment in {"HIBERNATING", "CHURN_RISK"}:
            win_prob = min(win_prob, 0.25)
        elif customer_segment == "UNCLASSIFIED":
            win_prob = min(win_prob, 0.39)

        if win_prob >= 0.70:
            tier = "HOT"
        elif win_prob >= 0.40:
            tier = "WARM"
        else:
            tier = "COLD"

        # Estimate deal value based on solution
        deal_values = {
            "CRM": 45_000_000.0,
            "ERP": 120_000_000.0,
            "POS": 35_000_000.0,
            "INFRASTRUCTURE": 85_000_000.0,
            "INTEGRATION": 60_000_000.0,
            "AI": 50_000_000.0,
            "OTHER": 25_000_000.0,
        }
        estimated_val = deal_values.get(solution_interest, 30_000_000.0)
        expected_won = round(estimated_val * win_prob, 2)

        key_drivers = []
        if norm_priority >= 0.7:
            key_drivers.append(f"Điểm ưu tiên nhu cầu cao ({priority_score}/100)")
        if interaction_count >= 2:
            key_drivers.append(f"Đã có lịch sử trao đổi ({interaction_count} lần)")
        if contact_quality >= 0.9:
            key_drivers.append("Hồ sơ doanh nghiệp & số liên hệ đầy đủ")
        if speed_factor >= 0.9:
            key_drivers.append("Đã ghi nhận gửi form hỏi thêm sớm (<4h)")
        if not key_drivers:
            key_drivers.append("Cần thêm thông tin khảo sát để xác minh nhu cầu")

        return LeadPredictionResult(
            lead_id=lead_id,
            win_probability=win_prob,
            tier=tier,
            estimated_deal_value=estimated_val,
            expected_won_value=expected_won,
            key_drivers=key_drivers,
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2. VIETNAMESE B2B SENTIMENT & CHURN RISK ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class SentimentChurnEngine:
    """Analyzes customer interactions for sentiment polarities and churn vulnerability."""

    POSITIVE_LEXICON = {
        "hài lòng": 1.5, "đồng ý": 1.4, "tốt": 1.0, "xuất sắc": 1.8, "nhanh": 1.0,
        "tiện lợi": 1.2, "ổn định": 1.1, "rất thích": 1.5, "chốt hợp đồng": 1.6, "ký hợp đồng": 1.5,
        "hiệu quả": 1.3, "chuyên nghiệp": 1.4, "cảm ơn": 0.8, "phù hợp": 1.1,
        "thành công": 1.3, "đúng hạn": 1.0, "nhiệt tình": 1.1,
    }

    NEGATIVE_LEXICON = {
        "lỗi": -1.5, "chậm": -1.3, "đắt": -1.1, "chưa rõ": -0.8, "phức tạp": -1.2,
        "hoãn": -1.4, "khó dùng": -1.3, "kém": -1.5, "thất vọng": -1.8, "không hài lòng": -1.9,
        "sự cố": -1.4, "hủy": -1.8, "mất dữ liệu": -2.0, "treo": -1.2, "bức xúc": -1.8,
        "không liên hệ": -1.1, "chờ lâu": -1.2,
    }

    URGENCY_KEYWORDS = {"gấp": 0.8, "khẩn": 0.9, "ngay": 0.6, "sớm": 0.5, "sự cố": 0.8}

    def analyze(
        self,
        interaction_id: int,
        content: str,
        days_since_last_contact: int = 0,
        unresolved_tasks_count: int = 0,
    ) -> SentimentResult:
        text_lower = normalize_text(content)
        pos_score = 0.0
        neg_score = 0.0

        lexicon = {**self.POSITIVE_LEXICON, **self.NEGATIVE_LEXICON,
                   "đã khắc phục lỗi": 1.2, "đã xử lý sự cố": 1.2}
        phrases = "|".join(re.escape(word) for word in sorted(lexicon, key=len, reverse=True))
        pattern = re.compile(
            r"(?<!\w)(?P<neg>(?:không|chưa|chẳng|chả)(?:\s+\w+){0,2}\s+)?"
            r"(?P<phrase>" + phrases + r")(?!\w)"
        )
        for match in pattern.finditer(text_lower):
            weight = lexicon[match.group("phrase")]
            if match.group("neg"):
                weight = -weight
            # Rhetorical denial: "hài lòng gì mà...", "tốt đâu". Match a
            # grammatical construction rather than memorizing a full example.
            if weight > 0 and re.match(r"\s+(?:gì\s+mà|đâu\b)", text_lower[match.end():]):
                weight = -weight
            if weight > 0:
                pos_score += weight
            else:
                neg_score += abs(weight)

        total_weights = pos_score + neg_score
        if total_weights > 0:
            raw_score = (pos_score - neg_score) / (pos_score + neg_score)
        else:
            raw_score = 0.0

        sentiment_score = round(max(min(raw_score, 1.0), -1.0), 2)

        if sentiment_score >= 0.25:
            sentiment_label = "POSITIVE"
        elif sentiment_score <= -0.25:
            sentiment_label = "NEGATIVE"
        else:
            sentiment_label = "NEUTRAL"

        # Calculate urgency
        urgency = 0.1
        for kw, score in self.URGENCY_KEYWORDS.items():
            if kw in text_lower:
                urgency = max(urgency, score)

        # Churn risk determination
        churn_points = 0
        if sentiment_label == "NEGATIVE":
            churn_points += 4 if any(phrase in text_lower for phrase in ("hủy hợp đồng", "mất dữ liệu", "không gia hạn")) else 3
        elif sentiment_label == "NEUTRAL":
            churn_points += 1

        if days_since_last_contact > 30:
            churn_points += 2
        elif days_since_last_contact > 14:
            churn_points += 1

        if unresolved_tasks_count >= 2:
            churn_points += 2

        if churn_points >= 4:
            churn_risk_level = "HIGH"
        elif churn_points >= 2:
            churn_risk_level = "MEDIUM"
        else:
            churn_risk_level = "LOW"

        return SentimentResult(
            interaction_id=interaction_id,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            churn_risk_level=churn_risk_level,
            urgency_score=round(urgency, 2),
        )


# ─────────────────────────────────────────────────────────────────────────────
# 3. RFM CUSTOMER SEGMENTATION (FIXED REFERENCE PROFILES)
# ─────────────────────────────────────────────────────────────────────────────

class RFMSegmentationModel:
    """Assign RFM profiles to fixed reference centroids; no K-Means training."""

    CLUSTER_NAMES = {
        0: "Khách hàng Chiến lược (VIP)",
        1: "Khách hàng Tiềm năng cao",
        2: "Khách hàng Đang duy trì",
        3: "Khách hàng Nguy cơ đóng băng",
    }

    # Reference centroids [RecencyNorm (lower is better), FrequencyNorm (higher is better), MonetaryNorm (higher is better)]
    CENTROIDS = [
        [0.15, 0.85, 0.90],  # VIP: Recency low, F high, M high
        [0.25, 0.60, 0.50],  # High Potential: Recency low, F med, M med
        [0.55, 0.35, 0.30],  # Retaining: Recency med, F low-med, M low-med
        [0.85, 0.15, 0.15],  # At-Risk / Dormant: Recency high, F low, M low
    ]

    def segment(
        self,
        customer_id: int,
        recency_days: int,
        frequency: int,
        monetary_amount: float,
        max_recency: int = 180,
        max_frequency: int = 20,
        max_monetary: float = 300_000_000.0,
    ) -> RFMSegmentResult:
        # Min-Max Normalization
        r_norm = min(max(recency_days, 0) / max(max_recency, 1), 1.0)
        f_norm = min(max(frequency, 0) / max(max_frequency, 1), 1.0)
        m_norm = min(max(monetary_amount, 0) / max(max_monetary, 1.0), 1.0)

        point = [r_norm, f_norm, m_norm]

        best_cluster = 0
        min_dist = float("inf")

        for c_id, centroid in enumerate(self.CENTROIDS):
            # Euclidean distance
            dist = math.sqrt(
                (point[0] - centroid[0]) ** 2
                + (point[1] - centroid[1]) ** 2
                + (point[2] - centroid[2]) ** 2
            )
            if dist < min_dist:
                min_dist = dist
                best_cluster = c_id

        return RFMSegmentResult(
            customer_id=customer_id,
            recency_days=recency_days,
            frequency=frequency,
            monetary=monetary_amount,
            cluster_id=best_cluster,
            cluster_name=self.CLUSTER_NAMES[best_cluster],
        )


# ─────────────────────────────────────────────────────────────────────────────
# 4. TIME-SERIES REVENUE FORECASTING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class RevenueForecastingEngine:
    """Choose a simple forecast using past-only rolling validation, defaulting to baseline.

    Legacy *_95 field names remain for dashboard compatibility. Their values are
    exploratory error bands, not calibrated 95% prediction intervals.
    """

    MODEL_LABELS = {"NAIVE": "Baseline tháng cuối", "LINEAR": "Xu hướng tuyến tính", "MEAN_3": "Trung bình 3 tháng"}

    @staticmethod
    def predict_value(values, model, step=1):
        if model == "NAIVE":
            return max(values[-1], 0.0)
        if model == "MEAN_3":
            return max(sum(values[-3:]) / len(values[-3:]), 0.0)
        n = len(values)
        mean_x, mean_y = (n - 1) / 2, sum(values) / n
        den = sum((i - mean_x) ** 2 for i in range(n)) or 1.0
        slope = sum((i - mean_x) * (y - mean_y) for i, y in enumerate(values)) / den
        return max(mean_y + slope * (n - 1 + step - mean_x), 0.0)

    def select_model(self, values):
        origins = list(range(max(3, len(values) - 6), len(values)))
        errors = {model: [abs(values[i] - self.predict_value(values[:i], model)) for i in origins]
                  for model in self.MODEL_LABELS}
        mae = {model: sum(items) / len(items) if items else None for model, items in errors.items()}
        selected = "NAIVE"
        # Conservative operating policy: need 18 observed months, at least five
        # folds, and improvement both overall and in the latest two folds.
        # The threshold is a guardrail, not a statistical accuracy guarantee.
        if len(values) >= 18 and len(origins) >= 5 and mae["NAIVE"] > 0:
            candidate = min(mae, key=mae.get)
            if (mae[candidate] < 0.9 * mae["NAIVE"]
                    and sum(errors[candidate][-2:]) < sum(errors["NAIVE"][-2:])):
                selected = candidate
        return {"model": selected, "validation_folds": len(origins), "mae": mae,
                "errors": errors[selected] or [abs(b - a) for a, b in zip(values, values[1:])]}

    def forecast_next_months(
        self,
        historical_monthly_revenues: List[Tuple[date, float]],
        months_ahead: int = 4,
    ) -> List[ForecastPoint]:
        if len(historical_monthly_revenues) < 3 or months_ahead <= 0:
            return []

        ys = [float(val) for _, val in historical_monthly_revenues]
        selection = self.select_model(ys)
        model = selection["model"]
        errors = sorted(selection["errors"])
        error_band = errors[math.ceil(0.95 * len(errors)) - 1] if errors else 0.0
        last_date = historical_monthly_revenues[-1][0]
        results: List[ForecastPoint] = []
        next_value = self.predict_value(ys, model)
        trend_dir = "TĂNG" if next_value > ys[-1] else ("GIẢM" if next_value < ys[-1] else "ỔN ĐỊNH")

        for step in range(1, months_ahead + 1):
            predicted = self.predict_value(ys, model, step)
            margin = error_band * math.sqrt(step)

            # Next month date calculation
            month_calc = last_date.month + step
            year_calc = last_date.year + ((month_calc - 1) // 12)
            month_final = ((month_calc - 1) % 12) + 1
            f_date = date(year_calc, month_final, 1)

            results.append(
                ForecastPoint(
                    forecast_date=f_date,
                    predicted_revenue=round(predicted, 2),
                    lower_bound_95=round(max(predicted - margin, 0.0), 2),
                    upper_bound_95=round(predicted + margin, 2),
                    trend_direction=f"{self.MODEL_LABELS[model]} · {trend_dir}",
                    model_name=model,
                )
            )

        return results


# ─────────────────────────────────────────────────────────────────────────────
# 5. EXPLAINABLE AI (XAI) ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class ExplainableAIEngine:
    """Relative contributions of four observed scoring features; not Shapley attribution."""

    @staticmethod
    def explain_lead_scoring(
        priority_score: int,
        interaction_count: int,
        solution_interest: str,
        has_verified_contact: bool,
    ) -> List[Dict[str, Any]]:
        values = LeadWinRateModel().feature_contributions(
            priority_score, interaction_count, has_verified_contact, has_verified_contact,
            0, solution_interest,
        )
        selected = ["Điểm nhu cầu", "Tần suất tương tác", "Nhóm giải pháp", "Thông tin liên hệ đầy đủ"]
        total = sum(abs(values[key]) for key in selected) or 1
        return [{"feature": key, "impact_percentage": round(values[key] / total * 100, 1),
                 "description": "Đóng góp trong bốn đặc trưng quan sát của công thức; không phải xác suất hoặc SHAP.",
                 "direction": "POSITIVE" if values[key] > 0 else ("NEGATIVE" if values[key] < 0 else "NEUTRAL")}
                for key in selected]



# ─────────────────────────────────────────────────────────────────────────────
# 6. ANOMALY DETECTION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class AnomalyDetectionEngine:
    """Scans operations and transactions for outliers and operational bottlenecks."""

    @staticmethod
    def detect_lead_anomalies(
        lead_id: int,
        lead_name: str,
        priority_score: int,
        days_stalled: int,
        status: str,
    ) -> Optional[AnomalyAlert]:
        # High-value lead neglected
        if priority_score >= 80 and days_stalled >= 5 and status not in ("COMPLETED", "WON", "LOST"):
            return AnomalyAlert(
                entity_type="LEAD",
                entity_id=lead_id,
                severity="HIGH",
                description=f"Khách hàng tiềm năng cao '{lead_name}' (Điểm: {priority_score}) bị dừng phản hồi {days_stalled} ngày!",
                metric_value=float(days_stalled),
            )
        return None

    @staticmethod
    def detect_revenue_anomaly(
        record_id: int,
        amount: float,
        mean_amount: float,
        std_dev: float,
    ) -> Optional[AnomalyAlert]:
        if std_dev > 0:
            z_score = abs(amount - mean_amount) / std_dev
            if z_score >= 2.5:
                return AnomalyAlert(
                    entity_type="TRANSACTION",
                    entity_id=record_id,
                    severity="MEDIUM",
                    description=f"Giao dịch trị giá {amount:,.0f} VNĐ lệch nhiều (Z={z_score:.2f}) so với các giao dịch đang có.",
                    metric_value=round(z_score, 2),
                )
        return None
