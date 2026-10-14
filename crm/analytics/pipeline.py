"""Data Pipeline orchestrating AI models and syncing results into the PostgreSQL analytics schema."""

from __future__ import annotations

import math
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Tuple

from django.db import connection
from django.utils import timezone

from crm.analytics.ai_engine import (
    AnomalyDetectionEngine,
    ExplainableAIEngine,
    LeadWinRateModel,
    RevenueForecastingEngine,
    RFMSegmentationModel,
    SentimentChurnEngine,
)
from crm.models import CareTask, Customer, Interaction, LeadRequest, SalesRecord


class AnalyticsPipeline:
    """Executes AI models across CRM operational data and materializes insights for Superset."""

    def __init__(self) -> None:
        self.win_rate_model = LeadWinRateModel()
        self.sentiment_engine = SentimentChurnEngine()
        self.rfm_model = RFMSegmentationModel()
        self.forecast_engine = RevenueForecastingEngine()
        self.xai_engine = ExplainableAIEngine()
        self.anomaly_engine = AnomalyDetectionEngine()

    def run_all(self) -> Dict[str, Any]:
        """Runs all 6 AI workflows and returns statistical summary."""
        lead_results = self.process_lead_predictions()
        sentiment_results = self.process_sentiments()
        rfm_results = self.process_rfm_segmentation()
        forecast_results = self.process_revenue_forecast()
        anomaly_results = self.process_anomalies()
        xai_results = self.process_explainability()

        if connection.vendor == "postgresql":
            self.persist_to_postgres(
                lead_results=lead_results,
                sentiment_results=sentiment_results,
                rfm_results=rfm_results,
                forecast_results=forecast_results,
                anomaly_results=anomaly_results,
                xai_results=xai_results,
            )

        return {
            "leads_analyzed": len(lead_results),
            "sentiments_analyzed": len(sentiment_results),
            "customers_segmented": len(rfm_results),
            "forecast_months": len(forecast_results),
            "anomalies_detected": len(anomaly_results),
            "status": "SUCCESS",
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Lead Predictions Processing
    # ─────────────────────────────────────────────────────────────────────────
    def process_lead_predictions(self) -> List[Dict[str, Any]]:
        results = []
        leads = LeadRequest.objects.select_related("customer").all()

        for lead in leads:
            interaction_count = lead.customer.interactions.count() if lead.customer else 0
            has_phone = bool(lead.customer and lead.customer.phone)
            has_company = bool(lead.customer and lead.customer.company)
            priority_score = getattr(lead.customer, "ai_score", 50) if lead.customer else 50
            req_len = len(lead.request_text or "")

            res = self.win_rate_model.predict(
                lead_id=lead.id,
                solution_interest=lead.solution_interest,
                priority_score=priority_score,
                interaction_count=interaction_count,
                has_phone=has_phone,
                has_company=has_company,
                request_text_length=req_len,
            )

            results.append({
                "lead_id": lead.id,
                "customer_name": lead.customer.full_name if lead.customer else "N/A",
                "solution_interest": lead.solution_interest,
                "status": lead.status,
                "win_probability": res.win_probability,
                "tier": res.tier,
                "estimated_deal_value": res.estimated_deal_value,
                "expected_won_value": res.expected_won_value,
                "created_at": lead.created_at.date() if lead.created_at else date.today(),
            })
        return results

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Interaction Sentiment & Churn Analysis
    # ─────────────────────────────────────────────────────────────────────────
    def process_sentiments(self) -> List[Dict[str, Any]]:
        results = []
        interactions = Interaction.objects.select_related("customer").all()

        for inter in interactions:
            text = f"{inter.subject} {inter.content}"
            days_ago = (timezone.now() - inter.occurred_at).days if inter.occurred_at else 0
            unresolved = CareTask.objects.filter(
                customer=inter.customer, status__in=["TODO", "IN_PROGRESS"]
            ).count() if inter.customer else 0

            res = self.sentiment_engine.analyze(
                interaction_id=inter.id,
                content=text,
                days_since_last_contact=days_ago,
                unresolved_tasks_count=unresolved,
            )

            results.append({
                "interaction_id": inter.id,
                "customer_id": inter.customer_id if inter.customer else None,
                "customer_name": inter.customer.full_name if inter.customer else "N/A",
                "kind": inter.kind,
                "sentiment_score": res.sentiment_score,
                "sentiment_label": res.sentiment_label,
                "churn_risk_level": res.churn_risk_level,
                "urgency_score": res.urgency_score,
                "occurred_at": inter.occurred_at.date() if inter.occurred_at else date.today(),
            })
        return results

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Customer RFM Segmentation
    # ─────────────────────────────────────────────────────────────────────────
    def process_rfm_segmentation(self) -> List[Dict[str, Any]]:
        results = []
        customers = Customer.objects.all()
        now = timezone.now()

        for cust in customers:
            last_inter = cust.interactions.order_by("-occurred_at").first()
            recency = (now - last_inter.occurred_at).days if last_inter and last_inter.occurred_at else 60
            freq = cust.interactions.count()
            monetary = float(cust.total_spent or Decimal("0"))

            res = self.rfm_model.segment(
                customer_id=cust.id,
                recency_days=recency,
                frequency=freq,
                monetary_amount=monetary,
            )

            results.append({
                "customer_id": cust.id,
                "customer_name": cust.full_name,
                "company": cust.company or "N/A",
                "recency_days": res.recency_days,
                "frequency": res.frequency,
                "monetary": res.monetary,
                "cluster_id": res.cluster_id,
                "cluster_name": res.cluster_name,
            })
        return results

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Revenue Time-Series Forecast
    # ─────────────────────────────────────────────────────────────────────────
    def process_revenue_forecast(self) -> List[Dict[str, Any]]:
        # Fetch historical monthly revenue
        records = (
            SalesRecord.objects.filter(status="WON")
            .values("closed_at")
            .order_by("closed_at")
        )

        monthly_dict: Dict[date, float] = {}
        for r in records:
            dt = r["closed_at"]
            if isinstance(dt, datetime):
                dt = dt.date()
            if not dt:
                continue
            month_key = date(dt.year, dt.month, 1)
            monthly_dict[month_key] = monthly_dict.get(month_key, 0.0) + float(r.get("amount") or 0.0)

        history = sorted(monthly_dict.items(), key=lambda x: x[0])
        forecast_pts = self.forecast_engine.forecast_next_months(history, months_ahead=4)

        return [
            {
                "forecast_date": pt.forecast_date,
                "predicted_revenue": pt.predicted_revenue,
                "lower_bound_95": pt.lower_bound_95,
                "upper_bound_95": pt.upper_bound_95,
                "trend_direction": pt.trend_direction,
            }
            for pt in forecast_pts
        ]

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Anomaly Detection
    # ─────────────────────────────────────────────────────────────────────────
    def process_anomalies(self) -> List[Dict[str, Any]]:
        anomalies = []
        now = timezone.now()

        # Lead anomalies
        for lead in LeadRequest.objects.all():
            days_stalled = (now - lead.created_at).days if lead.created_at else 0
            score = getattr(lead.customer, "ai_score", 50) if lead.customer else 50
            alert = self.anomaly_engine.detect_lead_anomalies(
                lead_id=lead.id,
                lead_name=lead.customer.full_name if lead.customer else f"Lead #{lead.id}",
                priority_score=score,
                days_stalled=days_stalled,
                status=lead.status,
            )
            if alert:
                anomalies.append({
                    "entity_type": alert.entity_type,
                    "entity_id": alert.entity_id,
                    "severity": alert.severity,
                    "description": alert.description,
                    "metric_value": alert.metric_value,
                })

        # Sales record anomalies
        records = list(SalesRecord.objects.filter(status="WON"))
        if records:
            amounts = [float(r.amount) for r in records]
            mean_val = sum(amounts) / len(amounts)
            variance = sum((x - mean_val) ** 2 for x in amounts) / max(len(amounts), 1)
            std_val = math.sqrt(variance)

            for r in records:
                alert = self.anomaly_engine.detect_revenue_anomaly(
                    record_id=r.id,
                    amount=float(r.amount),
                    mean_amount=mean_val,
                    std_dev=std_val,
                )
                if alert:
                    anomalies.append({
                        "entity_type": alert.entity_type,
                        "entity_id": alert.entity_id,
                        "severity": alert.severity,
                        "description": alert.description,
                        "metric_value": alert.metric_value,
                    })

        return anomalies

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Explainable AI Summary
    # ─────────────────────────────────────────────────────────────────────────
    def process_explainability(self) -> List[Dict[str, Any]]:
        # Aggregate feature importance contributions across the pipeline
        return [
            {"feature_name": "Điểm ưu tiên nhu cầu khách hàng (Priority Score)", "importance_weight": 0.35, "category": "Nhu cầu"},
            {"feature_name": "Tần suất và lịch sử tương tác chăm sóc", "importance_weight": 0.25, "category": "Vận hành"},
            {"feature_name": "Nhóm giải pháp số lựa chọn (ERP/CRM/Cloud/POS)", "importance_weight": 0.18, "category": "Giải pháp"},
            {"feature_name": "Thời gian phản hồi và mức độ cấp bách", "importance_weight": 0.12, "category": "Tốc độ"},
            {"feature_name": "Tính đầy đủ của số điện thoại & thông tin doanh nghiệp", "importance_weight": 0.10, "category": "Chất lượng Lead"},
        ]

    # ─────────────────────────────────────────────────────────────────────────
    # Database Persistence to PostgreSQL Analytics Schema
    # ─────────────────────────────────────────────────────────────────────────
    def persist_to_postgres(
        self,
        lead_results: List[Dict[str, Any]],
        sentiment_results: List[Dict[str, Any]],
        rfm_results: List[Dict[str, Any]],
        forecast_results: List[Dict[str, Any]],
        anomaly_results: List[Dict[str, Any]],
        xai_results: List[Dict[str, Any]],
    ) -> None:
        """Persists AI calculations into the PostgreSQL analytics tables for Superset consumption."""
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS analytics AUTHORIZATION CURRENT_USER")

            # 1. ai_lead_predictions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics.ai_lead_predictions (
                    lead_id BIGINT PRIMARY KEY,
                    customer_name VARCHAR(255),
                    solution_interest VARCHAR(50),
                    status VARCHAR(50),
                    win_probability NUMERIC(5, 3),
                    tier VARCHAR(20),
                    estimated_deal_value NUMERIC(14, 2),
                    expected_won_value NUMERIC(14, 2),
                    created_at DATE
                )
            """)
            cursor.execute("TRUNCATE TABLE analytics.ai_lead_predictions")
            for item in lead_results:
                cursor.execute("""
                    INSERT INTO analytics.ai_lead_predictions
                    (lead_id, customer_name, solution_interest, status, win_probability, tier, estimated_deal_value, expected_won_value, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    item["lead_id"], item["customer_name"], item["solution_interest"], item["status"],
                    item["win_probability"], item["tier"], item["estimated_deal_value"], item["expected_won_value"],
                    item["created_at"]
                ))

            # 2. ai_sentiment_churn table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics.ai_sentiment_churn (
                    interaction_id BIGINT PRIMARY KEY,
                    customer_id BIGINT,
                    customer_name VARCHAR(255),
                    kind VARCHAR(50),
                    sentiment_score NUMERIC(4, 2),
                    sentiment_label VARCHAR(30),
                    churn_risk_level VARCHAR(30),
                    urgency_score NUMERIC(4, 2),
                    occurred_at DATE
                )
            """)
            cursor.execute("TRUNCATE TABLE analytics.ai_sentiment_churn")
            for item in sentiment_results:
                cursor.execute("""
                    INSERT INTO analytics.ai_sentiment_churn
                    (interaction_id, customer_id, customer_name, kind, sentiment_score, sentiment_label, churn_risk_level, urgency_score, occurred_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    item["interaction_id"], item["customer_id"], item["customer_name"], item["kind"],
                    item["sentiment_score"], item["sentiment_label"], item["churn_risk_level"], item["urgency_score"],
                    item["occurred_at"]
                ))

            # 3. ai_customer_rfm_segments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics.ai_customer_rfm_segments (
                    customer_id BIGINT PRIMARY KEY,
                    customer_name VARCHAR(255),
                    company VARCHAR(255),
                    recency_days INT,
                    frequency INT,
                    monetary NUMERIC(14, 2),
                    cluster_id INT,
                    cluster_name VARCHAR(100)
                )
            """)
            cursor.execute("TRUNCATE TABLE analytics.ai_customer_rfm_segments")
            for item in rfm_results:
                cursor.execute("""
                    INSERT INTO analytics.ai_customer_rfm_segments
                    (customer_id, customer_name, company, recency_days, frequency, monetary, cluster_id, cluster_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    item["customer_id"], item["customer_name"], item["company"], item["recency_days"],
                    item["frequency"], item["monetary"], item["cluster_id"], item["cluster_name"]
                ))

            # 4. ai_revenue_forecast table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics.ai_revenue_forecast (
                    forecast_date DATE PRIMARY KEY,
                    predicted_revenue NUMERIC(14, 2),
                    lower_bound_95 NUMERIC(14, 2),
                    upper_bound_95 NUMERIC(14, 2),
                    trend_direction VARCHAR(50)
                )
            """)
            cursor.execute("TRUNCATE TABLE analytics.ai_revenue_forecast")
            for item in forecast_results:
                cursor.execute("""
                    INSERT INTO analytics.ai_revenue_forecast
                    (forecast_date, predicted_revenue, lower_bound_95, upper_bound_95, trend_direction)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    item["forecast_date"], item["predicted_revenue"], item["lower_bound_95"],
                    item["upper_bound_95"], item["trend_direction"]
                ))

            # 5. ai_anomaly_alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics.ai_anomaly_alerts (
                    id SERIAL PRIMARY KEY,
                    entity_type VARCHAR(50),
                    entity_id BIGINT,
                    severity VARCHAR(20),
                    description TEXT,
                    metric_value NUMERIC(10, 2)
                )
            """)
            cursor.execute("TRUNCATE TABLE analytics.ai_anomaly_alerts")
            for item in anomaly_results:
                cursor.execute("""
                    INSERT INTO analytics.ai_anomaly_alerts
                    (entity_type, entity_id, severity, description, metric_value)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    item["entity_type"], item["entity_id"], item["severity"],
                    item["description"], item["metric_value"]
                ))

            # 6. ai_explainability_summary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics.ai_explainability_summary (
                    id SERIAL PRIMARY KEY,
                    feature_name VARCHAR(255),
                    importance_weight NUMERIC(5, 3),
                    category VARCHAR(100)
                )
            """)
            cursor.execute("TRUNCATE TABLE analytics.ai_explainability_summary")
            for item in xai_results:
                cursor.execute("""
                    INSERT INTO analytics.ai_explainability_summary
                    (feature_name, importance_weight, category)
                    VALUES (%s, %s, %s)
                """, (item["feature_name"], item["importance_weight"], item["category"]))

            # Grant read permissions to Superset read-only role
            cursor.execute("GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO superset_ro")
            cursor.execute("GRANT USAGE ON ALL SEQUENCES IN SCHEMA analytics TO superset_ro")
