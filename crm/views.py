import hashlib
import csv
import json
import logging
import secrets
from datetime import timedelta
from smtplib import SMTPException
from urllib.parse import urljoin, urlsplit

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Case, IntegerField, Max, Q, Sum, When
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import CareTaskForm, EmailDraftForm, LeadFollowUpComposeForm, LeadFollowUpResponseForm, PublicLeadRequestForm
from .models import AIAnalysis, CareTask, Customer, Interaction, LeadFollowUp, LeadFollowUpResponse, LeadRequest
from .services.ai_chat_service import answer_customer_question
from .services.consultation import clean_chat_history
from .services.ai_service import analyze_customer as run_customer_analysis
from .services.email_draft_service import create_email_draft

logger = logging.getLogger(__name__)


def _get_report_analytics_context(today):
    """Query PostgreSQL analytics schema or return graceful intelligent fallback."""
    from django.db import connection

    data = {
        "has_ai_datamart": False,
        "total_expected_revenue": 0,
        "hot_leads_count": 0,
        "lead_tiers": [],
        "solutions": [],
        "forecast": [],
        "sentiment": [],
        "churn_risk": [],
        "rfm_clusters": [],
        "xai": [],
        "anomalies": [],
    }
    try:
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'analytics' AND table_name = 'ai_lead_predictions'"
                )
                row = cursor.fetchone()
                if row and row[0] > 0:
                    data["has_ai_datamart"] = True

                    cursor.execute("""
                        SELECT tier, count(*), coalesce(sum(expected_won_value), 0)::numeric
                        FROM analytics.ai_lead_predictions
                        GROUP BY tier ORDER BY tier
                    """)
                    data["lead_tiers"] = [
                        {"tier": r[0], "count": r[1], "revenue": float(r[2])}
                        for r in cursor.fetchall()
                    ]
                    data["total_expected_revenue"] = sum(item["revenue"] for item in data["lead_tiers"])
                    data["hot_leads_count"] = sum(item["count"] for item in data["lead_tiers"] if item["tier"] == "HOT")

                    cursor.execute("""
                        SELECT solution_interest, coalesce(sum(estimated_deal_value), 0)::numeric,
                               coalesce(sum(expected_won_value), 0)::numeric, count(*)
                        FROM analytics.ai_lead_predictions
                        GROUP BY solution_interest ORDER BY 2 DESC
                    """)
                    data["solutions"] = [
                        {"solution": r[0], "deal_value": float(r[1]), "expected_won": float(r[2]), "count": r[3]}
                        for r in cursor.fetchall()
                    ]

                    cursor.execute("""
                        SELECT forecast_date, predicted_revenue, lower_bound_95, upper_bound_95, trend_direction
                        FROM analytics.ai_revenue_forecast ORDER BY forecast_date
                    """)
                    data["forecast"] = [
                        {"date": str(r[0]), "predicted": float(r[1]), "lower": float(r[2]), "upper": float(r[3]), "trend": r[4]}
                        for r in cursor.fetchall()
                    ]

                    cursor.execute("""
                        SELECT sentiment_label, count(*)
                        FROM analytics.ai_sentiment_churn GROUP BY sentiment_label
                    """)
                    data["sentiment"] = [{"label": r[0], "count": r[1]} for r in cursor.fetchall()]

                    cursor.execute("""
                        SELECT churn_risk_level, count(*)
                        FROM analytics.ai_sentiment_churn GROUP BY churn_risk_level
                    """)
                    data["churn_risk"] = [{"level": r[0], "count": r[1]} for r in cursor.fetchall()]

                    cursor.execute("""
                        SELECT cluster_name, count(*)
                        FROM analytics.ai_customer_rfm_segments GROUP BY cluster_name
                    """)
                    data["rfm_clusters"] = [{"cluster": r[0], "count": r[1]} for r in cursor.fetchall()]

                    cursor.execute("""
                        SELECT feature_name, importance_weight, category
                        FROM analytics.ai_explainability_summary ORDER BY importance_weight DESC
                    """)
                    data["xai"] = [{"feature": r[0], "weight": float(r[1]), "category": r[2]} for r in cursor.fetchall()]

                    cursor.execute("""
                        SELECT entity_type, severity, description
                        FROM analytics.ai_anomaly_alerts ORDER BY id LIMIT 5
                    """)
                    data["anomalies"] = [{"entity_type": r[0], "severity": r[1], "description": r[2]} for r in cursor.fetchall()]
                    cursor.execute("SELECT severity, count(*) FROM analytics.ai_anomaly_alerts GROUP BY severity")
                    data["anomaly_summary"] = [{"severity": r[0], "count": r[1]} for r in cursor.fetchall()]
    except Exception as exc:
        data["has_ai_datamart"] = False
        logger.debug("Analytics datamart query failed/skipped: %s", exc)

    if not data["has_ai_datamart"]:
        from collections import Counter
        from crm.analytics.pipeline import AnalyticsPipeline
        pipe = AnalyticsPipeline()
        leads = pipe.process_lead_predictions()
        tiers, solutions = {}, {}
        for lead in leads:
            tier = tiers.setdefault(lead["tier"], {"tier": lead["tier"], "count": 0, "revenue": 0})
            tier["count"] += 1
            tier["revenue"] += lead["expected_won_value"]
            sol = solutions.setdefault(lead["solution_interest"], {"solution": lead["solution_interest"], "count": 0, "deal_value": 0, "expected_won": 0})
            sol["count"] += 1
            sol["deal_value"] += lead["estimated_deal_value"]
            sol["expected_won"] += lead["expected_won_value"]
        data["lead_tiers"] = list(tiers.values())
        data["solutions"] = list(solutions.values())
        data["hot_leads_count"] = tiers.get("HOT", {}).get("count", 0)
        data["total_expected_revenue"] = sum(x["revenue"] for x in tiers.values())
        data["forecast"] = [{"date": str(x["forecast_date"]), "predicted": x["predicted_revenue"],
                             "lower": x["lower_bound_95"], "upper": x["upper_bound_95"], "trend": x["trend_direction"]}
                            for x in pipe.process_revenue_forecast()]
        sentiments = pipe.process_sentiments()
        data["sentiment"] = [{"label": key, "count": count} for key, count in Counter(x["sentiment_label"] for x in sentiments).items()]
        data["churn_risk"] = [{"level": key, "count": count} for key, count in Counter(x["churn_risk_level"] for x in sentiments).items()]
        data["rfm_clusters"] = [{"cluster": key, "count": count} for key, count in Counter(x["cluster_name"] for x in pipe.process_rfm_segmentation()).items()]
        data["xai"] = [{"feature": x["feature_name"], "weight": x["importance_weight"]} for x in pipe.process_explainability()]
        alerts = pipe.process_anomalies()
        data["anomalies"] = alerts[:5]
        data["anomaly_summary"] = [{"severity": key, "count": count} for key, count in Counter(item["severity"] for item in alerts).items()]
    data["data_source"] = "postgresql_datamart" if data["has_ai_datamart"] else "crm_live_rules"

    data["chart_json"] = json.dumps(data)
    return data


@login_required
@permission_required("crm.access_crm", raise_exception=True)
def dashboard(request):
    active_customers = Customer.objects.filter(is_active=True)
    today = timezone.localdate()
    lead_total_count = LeadRequest.objects.count()
    customer_count = active_customers.count()
    open_tasks = CareTask.objects.exclude(status=CareTask.Status.DONE).select_related(
        "customer", "assignee"
    ).annotate(priority_order=Case(
        When(priority=CareTask.Priority.HIGH, then=0),
        When(priority=CareTask.Priority.MEDIUM, then=1),
        default=2,
        output_field=IntegerField(),
    ))

    analytics_data = _get_report_analytics_context(today)

    hot_leads = LeadRequest.objects.filter(status=LeadRequest.Status.NEW).select_related("customer")
    if active_customers.filter(ai_score__gt=0).exists():
        hot_leads = hot_leads.order_by("-customer__ai_score")[:4]
    else:
        hot_leads = hot_leads.order_by("-created_at")[:4]

    churn_risk_customers = active_customers.filter(ai_segment=Customer.Segment.CHURN_RISK).order_by("-created_at")[:4]

    total_tasks_count = CareTask.objects.count()
    done_tasks_count = CareTask.objects.filter(status=CareTask.Status.DONE).count()
    task_completion_rate = round((done_tasks_count / total_tasks_count) * 100) if total_tasks_count > 0 else 100

    lead_status_counts = {
        value: LeadRequest.objects.filter(status=value).count()
        for value, _ in LeadRequest.Status.choices
    }

    context = {
        "customer_count": customer_count,
        "show_first_run_guide": customer_count == 0 and lead_total_count == 0,
        "unclassified_count": active_customers.filter(ai_segment=Customer.Segment.UNCLASSIFIED).count(),
        "vip_count": active_customers.filter(ai_segment=Customer.Segment.VIP).count(),
        "total_spent": active_customers.aggregate(total=Sum("total_spent"))["total"] or 0,
        "new_lead_count": LeadRequest.objects.filter(status=LeadRequest.Status.NEW).count(),
        "recent_lead_requests": LeadRequest.objects.select_related("customer")[:5],
        "unclassified_customers": active_customers.filter(
            ai_segment=Customer.Segment.UNCLASSIFIED
        ).order_by("-created_at")[:5],
        "today_tasks": open_tasks.filter(due_at=today).order_by("priority_order", "due_at")[:5],
        "overdue_tasks": open_tasks.filter(due_at__lt=today).order_by("due_at", "priority_order")[:5],
        "upcoming_tasks": open_tasks.filter(due_at__gt=today).order_by("due_at")[:5],
        "overdue_task_count": open_tasks.filter(due_at__lt=today).count(),
        "today_task_count": open_tasks.filter(due_at=today).count(),
        "open_task_count": open_tasks.count(),
        # Enhanced business KPIs & AI insights
        "total_expected_revenue": analytics_data.get("total_expected_revenue", 0),
        "hot_leads_count": analytics_data.get("hot_leads_count", 0),
        "hot_leads": hot_leads,
        "churn_risk_count": active_customers.filter(ai_segment=Customer.Segment.CHURN_RISK).count(),
        "churn_risk_customers": churn_risk_customers,
        "task_completion_rate": task_completion_rate,
        "lead_status_counts": lead_status_counts,
    }
    return render(request, "crm/dashboard.html", context)


@login_required
@permission_required("crm.access_crm", raise_exception=True)
def customer_list(request):
    query = request.GET.get("q", "").strip()
    selected_segment = request.GET.get("segment", "").strip()
    all_active_customers = Customer.objects.filter(is_active=True)

    # Precompute metrics and counts for quick filter pills
    total_active_count = all_active_customers.count()
    segment_counts = {"all": total_active_count}
    for val, _ in Customer.Segment.choices:
        segment_counts[val] = all_active_customers.filter(ai_segment=val).count()

    customers = all_active_customers
    if query:
        customers = customers.filter(
            Q(full_name__icontains=query)
            | Q(email__icontains=query)
            | Q(company__icontains=query)
            | Q(phone__icontains=query)
        )
    if selected_segment:
        customers = customers.filter(ai_segment=selected_segment)

    page = Paginator(customers.order_by("full_name"), 15).get_page(request.GET.get("page"))
    return render(request, "crm/customer_list.html", {
        "page": page,
        "customers": page.object_list,
        "query": query,
        "selected_segment": selected_segment,
        "segment_choices": Customer.Segment.choices,
        "segment_counts": segment_counts,
        "total_active_count": total_active_count,
        "vip_count": segment_counts.get(Customer.Segment.VIP, 0),
        "potential_count": segment_counts.get(Customer.Segment.POTENTIAL, 0),
        "churn_risk_count": segment_counts.get(Customer.Segment.CHURN_RISK, 0),
        "unclassified_count": segment_counts.get(Customer.Segment.UNCLASSIFIED, 0),
    })


@login_required
@permission_required("crm.access_crm", raise_exception=True)
def priority_customer_list(request):
    """Transparent rules-based queue; ranking never changes customer data."""
    today = timezone.localdate()
    stale_before = timezone.now() - timedelta(days=30)
    selected_filter = request.GET.get("filter", "").strip()
    customers = Customer.objects.filter(is_active=True).annotate(
        last_interaction=Max("interactions__occurred_at"),
    ).prefetch_related("care_tasks")

    filter_counts = {
        "all": 0,
        "churn": 0,
        "vip": 0,
        "stale": 0,
        "overdue": 0,
        "urgent": 0,
    }

    all_items = []
    for customer in customers:
        open_tasks = [task for task in customer.care_tasks.all() if task.status != CareTask.Status.DONE]
        overdue = any(task.due_at < today for task in open_tasks)
        stale = customer.last_interaction is None or customer.last_interaction < stale_before
        score = customer.ai_score
        reasons = []

        is_churn = customer.ai_segment == Customer.Segment.CHURN_RISK
        is_vip = customer.ai_segment == Customer.Segment.VIP

        if is_churn:
            score += 40
            reasons.append("Có nguy cơ rời bỏ")
        elif is_vip:
            score += 30
            reasons.append("Khách hàng VIP")
        if overdue:
            score += 35
            reasons.append("Có việc chăm sóc quá hạn")
        if stale:
            score += 20
            reasons.append("Chưa có tương tác trong 30 ngày")
        if customer.ai_score >= 70:
            reasons.append(f"Điểm tiềm năng {customer.ai_score}/100")

        is_urgent = score >= 80

        # Update counts
        filter_counts["all"] += 1
        if is_churn:
            filter_counts["churn"] += 1
        if is_vip:
            filter_counts["vip"] += 1
        if stale:
            filter_counts["stale"] += 1
        if overdue:
            filter_counts["overdue"] += 1
        if is_urgent:
            filter_counts["urgent"] += 1

        all_items.append({
            "customer": customer,
            "priority_score": score,
            "reasons": reasons or ["Theo dõi định kỳ"],
            "is_churn": is_churn,
            "is_vip": is_vip,
            "stale": stale,
            "overdue": overdue,
            "is_urgent": is_urgent,
        })

    # Filter queue based on selected_filter
    queue = []
    for item in all_items:
        if selected_filter == "churn" and not item["is_churn"]:
            continue
        if selected_filter == "vip" and not item["is_vip"]:
            continue
        if selected_filter == "stale" and not item["stale"]:
            continue
        if selected_filter == "overdue" and not item["overdue"]:
            continue
        if selected_filter == "urgent" and not item["is_urgent"]:
            continue
        queue.append(item)

    queue.sort(key=lambda item: (-item["priority_score"], item["customer"].full_name.casefold()))
    page = Paginator(queue, 20).get_page(request.GET.get("page"))
    return render(request, "crm/priority_customer_list.html", {
        "page": page,
        "queue": page.object_list,
        "selected_filter": selected_filter,
        "filter_counts": filter_counts,
        "total_queue_count": filter_counts["all"],
        "urgent_count": filter_counts["urgent"],
        "overdue_count": filter_counts["overdue"],
        "churn_count": filter_counts["churn"],
        "vip_count": filter_counts["vip"],
    })


@login_required
@permission_required("crm.access_crm", raise_exception=True)
def customer_email_draft(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    initial = {"goal": "check_in", "tone": "formal", "length": "vừa"}
    if request.method == "POST":
        form = EmailDraftForm(request.POST)
        action = request.POST.get("action")
        if form.is_valid() and action == "generate":
            result = create_email_draft(
                customer, form.cleaned_data["goal"], form.cleaned_data["tone"], form.cleaned_data["length"]
            )
            form = EmailDraftForm(initial={
                "goal": form.cleaned_data["goal"],
                "tone": form.cleaned_data["tone"],
                "length": form.cleaned_data["length"],
                "draft": result["draft"],
            })
            messages.info(request, "Đây là bản nháp để bạn xem và chỉnh sửa; hệ thống chưa gửi email.")
            return render(request, "crm/email_draft.html", {
                "customer": customer, "form": form, "provider": result["provider"],
            })
        if form.is_valid() and action == "record_sent":
            draft = form.cleaned_data["draft"].strip()
            if not draft:
                form.add_error("draft", "Hãy tạo hoặc nhập nội dung email trước khi xác nhận.")
            else:
                Interaction.objects.create(
                    customer=customer, kind=Interaction.Kind.EMAIL,
                    subject=f"Email chăm sóc: {form.cleaned_data['goal']}",
                    content=draft,
                )
                messages.success(request, "Đã ghi nhận email bạn xác nhận đã gửi. CRM không gửi email tự động.")
                return redirect("crm:customer_detail", pk=customer.pk)
    else:
        form = EmailDraftForm(initial=initial)
    return render(request, "crm/email_draft.html", {"customer": customer, "form": form})


def _customer_queryset_for_export(request):
    customers = Customer.objects.all()
    query = request.GET.get("q", "").strip()
    segment = request.GET.get("segment", "").strip()
    if query:
        customers = customers.filter(Q(full_name__icontains=query) | Q(email__icontains=query) | Q(company__icontains=query))
    if segment:
        customers = customers.filter(ai_segment=segment)
    if request.GET.get("active") == "1":
        customers = customers.filter(is_active=True)
    return customers.order_by("full_name")


@login_required
@permission_required("crm.export_crm_data", raise_exception=True)
def export_customers_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="crm-customers.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["Họ tên", "Email", "Điện thoại", "Công ty", "Nguồn", "Phân khúc", "Điểm AI", "Đang hoạt động", "Tổng chi tiêu (VNĐ)"])

    def safe_cell(value):
        text = str(value or "")
        return f"'{text}" if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text

    for customer in _customer_queryset_for_export(request).iterator():
        writer.writerow([
            safe_cell(customer.full_name), safe_cell(customer.email), safe_cell(customer.phone),
            safe_cell(customer.company), safe_cell(customer.source),
            safe_cell(customer.get_ai_segment_display()), safe_cell(customer.ai_score),
            "Có" if customer.is_active else "Không", safe_cell(customer.total_spent),
        ])
    return response


@login_required
@permission_required("crm.access_crm", raise_exception=True)
def crm_report(request):
    today = timezone.localdate()
    start_date = today - timedelta(days=30)
    analytics_data = _get_report_analytics_context(today)
    from .services.report_insights import report_insights
    from .services.superset_embed import LIVE_CHARTS
    insights = report_insights(analytics_data)

    context = {
        "customer_total": Customer.objects.count(),
        "new_customers": Customer.objects.filter(created_at__date__gte=start_date).count(),
        "segments": [
            {"label": label, "count": Customer.objects.filter(ai_segment=value).count()}
            for value, label in Customer.Segment.choices
        ],
        "lead_statuses": [
            {"label": label, "count": LeadRequest.objects.filter(status=value).count()}
            for value, label in LeadRequest.Status.choices
        ],
        "task_statuses": [
            {"label": label, "count": CareTask.objects.filter(status=value).count()}
            for value, label in CareTask.Status.choices
        ],
        "overdue_tasks": CareTask.objects.filter(status__in=[CareTask.Status.TODO, CareTask.Status.IN_PROGRESS], due_at__lt=today).count(),
        "period_start": start_date,
        # Enhanced Data Mart & Superset Analytics
        "analytics": analytics_data,
        "chart_json": analytics_data.get("chart_json", "{}"),
        "chart_data": {key: value for key, value in analytics_data.items() if key != "chart_json"},
        "can_sync_analytics": request.user.has_perm("crm.analyze_customer"),
        "total_expected_revenue": analytics_data.get("total_expected_revenue", 0),
        "hot_leads_count": analytics_data.get("hot_leads_count", 0),
        "report_insights": insights,
        "live_charts": [{**chart, "insight": insight["text"]} for chart, insight in zip(LIVE_CHARTS, insights)],
    }
    return render(request, "crm/report.html", context)


@login_required
@permission_required("crm.access_crm", raise_exception=True)
@never_cache
@require_GET
def superset_guest_session(request):
    from .context_processors import crm_links
    from .services.superset_embed import guest_session

    try:
        result = guest_session(request.user)
    except Exception as exc:
        # Do not return upstream errors: they may contain server/configuration details.
        logger.warning("Superset embedding unavailable (%s)", type(exc).__name__)
        return JsonResponse({"error": "Chưa kết nối được dashboard Superset. Bạn vẫn có thể xem biểu đồ CRM và phần nhận xét."}, status=503)
    return JsonResponse({**result, "domain": crm_links(request)["superset_url"]})


@login_required
@permission_required(("crm.access_crm", "crm.analyze_customer"), raise_exception=True)
@require_POST
def sync_ai_analytics_pipeline(request):
    """Trigger background AI analytics recalculation and return to report."""
    try:
        from crm.analytics.pipeline import AnalyticsPipeline
        pipe = AnalyticsPipeline()
        summary = pipe.run_all()
        messages.success(request, f"Đã cập nhật phân tích: {summary['leads_analyzed']} yêu cầu, "
                         f"{summary['sentiments_analyzed']} trao đổi và {summary['forecast_months']} tháng dự báo.")
    except Exception as exc:
        logger.exception("Error syncing AI analytics pipeline: %s", exc)
        messages.warning(request, f"Không thể đồng bộ pipeline: {exc}")
    return redirect("crm:report")



@login_required
@permission_required("crm.access_crm", raise_exception=True)
def lead_request_list(request):
    query = request.GET.get("q", "").strip()
    selected_status = request.GET.get("status", "").strip()
    all_requests = LeadRequest.objects.all()

    # Precompute metrics and status counts for quick filter pills
    total_leads_count = all_requests.count()
    status_counts = {"all": total_leads_count}
    for val, _ in LeadRequest.Status.choices:
        status_counts[val] = all_requests.filter(status=val).count()

    requests = LeadRequest.objects.select_related("customer").prefetch_related("follow_ups__response")
    if query:
        requests = requests.filter(
            Q(customer__full_name__icontains=query)
            | Q(customer__email__icontains=query)
            | Q(customer__company__icontains=query)
            | Q(customer__phone__icontains=query)
            | Q(request_text__icontains=query)
        )
    if selected_status:
        requests = requests.filter(status=selected_status)

    page = Paginator(requests, 15).get_page(request.GET.get("page"))
    return render(request, "crm/lead_request_list.html", {
        "page": page,
        "lead_requests": page.object_list,
        "query": query,
        "selected_status": selected_status,
        "status_choices": LeadRequest.Status.choices,
        "status_counts": status_counts,
        "total_leads_count": total_leads_count,
        "new_leads_count": status_counts.get(LeadRequest.Status.NEW, 0),
        "contacted_count": status_counts.get(LeadRequest.Status.CONTACTED, 0),
        "completed_count": status_counts.get(LeadRequest.Status.COMPLETED, 0),
    })


@login_required
@permission_required("crm.access_crm", raise_exception=True)
def care_task_list(request):
    today = timezone.localdate()
    query = request.GET.get("q", "").strip()
    selected_status = request.GET.get("status", "").strip()
    selected_filter = request.GET.get("filter", "").strip()

    all_tasks = CareTask.objects.all()
    open_tasks = all_tasks.exclude(status=CareTask.Status.DONE)
    task_counts = {
        "all": all_tasks.count(),
        "todo": all_tasks.filter(status=CareTask.Status.TODO).count(),
        "in_progress": all_tasks.filter(status=CareTask.Status.IN_PROGRESS).count(),
        "done": all_tasks.filter(status=CareTask.Status.DONE).count(),
        "overdue": open_tasks.filter(due_at__lt=today).count(),
        "today": open_tasks.filter(due_at=today).count(),
    }

    tasks = CareTask.objects.select_related("customer", "assignee").annotate(
        priority_order=Case(
            When(priority=CareTask.Priority.HIGH, then=0),
            When(priority=CareTask.Priority.MEDIUM, then=1),
            default=2,
            output_field=IntegerField(),
        ),
        status_order=Case(
            When(status=CareTask.Status.TODO, then=0),
            When(status=CareTask.Status.IN_PROGRESS, then=1),
            default=2,
            output_field=IntegerField(),
        ),
    ).order_by("status_order", "due_at", "priority_order", "-created_at")

    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
            | Q(customer__full_name__icontains=query) | Q(customer__company__icontains=query)
            | Q(customer__phone__icontains=query)
        )
    if selected_status:
        tasks = tasks.filter(status=selected_status)

    if selected_filter == "overdue":
        tasks = tasks.filter(due_at__lt=today).exclude(status=CareTask.Status.DONE)
    elif selected_filter == "today":
        tasks = tasks.filter(due_at=today).exclude(status=CareTask.Status.DONE)

    page = Paginator(tasks, 20).get_page(request.GET.get("page"))
    return render(request, "crm/care_task_list.html", {
        "page": page,
        "tasks": page.object_list,
        "query": query,
        "selected_status": selected_status,
        "selected_filter": selected_filter,
        "status_choices": CareTask.Status.choices,
        "task_counts": task_counts,
        "today": today,
    })


@login_required
@permission_required("crm.manage_care_tasks", raise_exception=True)
@require_http_methods(["GET", "POST"])
def care_task_form(request, pk=None, customer_pk=None):
    task = get_object_or_404(CareTask, pk=pk) if pk is not None else CareTask()
    customer = get_object_or_404(Customer, pk=customer_pk) if customer_pk is not None else None
    if request.method == "POST":
        form = CareTaskForm(request.POST, instance=task, customer=customer)
        if form.is_valid():
            saved_task = form.save(commit=False)
            if saved_task.assignee_id is None:
                saved_task.assignee = request.user
            if saved_task.status == CareTask.Status.DONE:
                saved_task.completed_at = saved_task.completed_at or timezone.now()
            else:
                saved_task.completed_at = None
            saved_task.save()
            messages.success(request, "Đã lưu việc chăm sóc khách hàng.")
            if customer_pk is not None:
                return redirect("crm:customer_detail", pk=customer_pk)
            return redirect("crm:care_tasks")
    else:
        initial = {} if task.pk else {"due_at": timezone.localdate()}
        if customer is not None:
            if request.GET.get("title"):
                initial["title"] = request.GET.get("title").strip()[:180]
                if request.GET.get("desc"):
                    initial["description"] = request.GET.get("desc").strip()
            elif request.GET.get("suggestion") == "1":
                analysis = customer.ai_analyses.first()
                if analysis:
                    suggestion = analysis.recommendation.strip()
                    initial["title"] = suggestion[:177].rsplit(" ", 1)[0] + "…" if len(suggestion) > 180 else suggestion
                    initial["description"] = suggestion
        form = CareTaskForm(instance=task, customer=customer, initial=initial)
    return render(request, "crm/care_task_form.html", {
        "form": form,
        "task": task,
        "customer": customer or (task.customer if task.pk else None),
        "is_edit": task.pk is not None,
    })


@login_required
@permission_required("crm.manage_crm_leads", raise_exception=True)
@require_POST
def update_lead_request_status(request, pk):
    lead_request = get_object_or_404(LeadRequest, pk=pk)
    status = request.POST.get("status", "")
    valid_statuses = {value for value, _label in LeadRequest.Status.choices}
    if status not in valid_statuses:
        messages.error(request, "Trạng thái yêu cầu không hợp lệ.")
    else:
        lead_request.status = status
        lead_request.save(update_fields=["status"])
        messages.success(request, "Đã cập nhật trạng thái yêu cầu tư vấn.")
    return redirect("crm:lead_requests")


@login_required
@permission_required("crm.access_crm", raise_exception=True)
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    has_public_requests = customer.lead_requests.exists()
    has_ai_consent = (
        customer.lead_requests.filter(ai_processing_consent=True).exists()
        or LeadFollowUpResponse.objects.filter(
            follow_up__lead_request__customer=customer,
            ai_processing_consent=True,
        ).exists()
    )
    context = {
        "customer": customer,
        "today": timezone.localdate(),
        "can_analyze_permission": request.user.has_perm("crm.analyze_customer"),
        "interactions": customer.interactions.all(),
        "care_tasks": customer.care_tasks.select_related("assignee").annotate(
            status_order=Case(
                When(status=CareTask.Status.TODO, then=0),
                When(status=CareTask.Status.IN_PROGRESS, then=1),
                default=2,
                output_field=IntegerField(),
            )
        ).order_by("status_order", "due_at")[:10],
        "has_public_requests": has_public_requests,
        "latest_analysis": customer.ai_analyses.first(),
        "analysis_history": customer.ai_analyses.all()[1:5],
        "can_run_ai_analysis": request.user.has_perm("crm.analyze_customer") and (not has_public_requests or has_ai_consent),
    }
    return render(request, "crm/customer_detail.html", context)


@login_required
@permission_required(("crm.access_crm", "crm.analyze_customer"), raise_exception=True)
@require_POST
def analyze_customer_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    public_requests = customer.lead_requests.all()
    if public_requests.exists():
        permitted_requests = list(public_requests.filter(ai_processing_consent=True))
        permitted_follow_up_responses = list(
            LeadFollowUpResponse.objects.filter(
                follow_up__lead_request__customer=customer,
                ai_processing_consent=True,
            ).select_related("follow_up__lead_request")
        )
        if not permitted_requests and not permitted_follow_up_responses:
            messages.error(request, "Khách hàng chưa đồng ý phân tích AI cho nội dung nào.")
            return redirect("crm:customer_detail", pk=customer.pk)
        result = run_customer_analysis(
            customer,
            permitted_requests=permitted_requests,
            permitted_follow_up_responses=permitted_follow_up_responses,
        )
    else:
        result = run_customer_analysis(customer)
    analysis = AIAnalysis.objects.create(customer=customer, **result)
    customer.ai_segment = analysis.segment
    customer.ai_score = analysis.score
    customer.save(update_fields=["ai_segment", "ai_score", "updated_at"])
    if analysis.provider == "gemini":
        messages.success(request, "Đã phân tích khách hàng bằng Gemini.")
    else:
        messages.info(request, "Đã phân tích bằng quy tắc cục bộ. Cấu hình GEMINI_API_KEY để gọi Gemini.")
    return redirect("crm:customer_detail", pk=customer.pk)


@require_http_methods(["GET", "POST"])
def public_lead_request(request):
    form = PublicLeadRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        save_public_lead_request(form.cleaned_data)
        return redirect("crm:lead_request_success")

    return render(request, "crm/lead_request.html", {
        "form": form,
        "brand_name": settings.PUBLIC_BRAND_NAME,
        "contact_email": settings.PUBLIC_CONTACT_EMAIL,
        "contact_email_is_demo": _is_demo_email(settings.PUBLIC_CONTACT_EMAIL),
    })


@require_http_methods(["GET"])
def public_lead_request_success(request):
    return render(request, "crm/lead_request_success.html", {
        "brand_name": settings.PUBLIC_BRAND_NAME,
        "contact_email": settings.PUBLIC_CONTACT_EMAIL,
        "contact_email_is_demo": _is_demo_email(settings.PUBLIC_CONTACT_EMAIL),
    })


@require_http_methods(["GET", "POST"])
def landing_page(request):
    from wagtail.models import Site
    from .models import LandingPage

    site = Site.find_for_request(request)
    if site:
        homepage = site.root_page.specific
        if isinstance(homepage, LandingPage) and homepage.live:
            return homepage.serve(request)
    form = PublicLeadRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        save_public_lead_request(form.cleaned_data)
        return redirect("crm:lead_request_success")

    return render(request, "crm/landing_page.html", {
        "form": form,
        "brand_name": settings.PUBLIC_BRAND_NAME,
        "contact_email": settings.PUBLIC_CONTACT_EMAIL,
        "contact_email_is_demo": _is_demo_email(settings.PUBLIC_CONTACT_EMAIL),
    })


def save_public_lead_request(data):
    with transaction.atomic():
        customer = Customer.objects.filter(email__iexact=data["email"]).first()
        if customer is None:
            try:
                # The nested atomic block creates a savepoint, so a concurrent
                # submission can lose the unique-email race without breaking
                # the outer transaction that records the lead.
                with transaction.atomic():
                    customer = Customer.objects.create(
                        full_name=data["full_name"],
                        email=data["email"],
                        phone=data["phone"],
                        company=data["company"],
                        source="Website",
                    )
            except IntegrityError:
                customer = Customer.objects.filter(email__iexact=data["email"]).first()
                if customer is None:
                    raise

        LeadRequest.objects.create(
            customer=customer,
            solution_interest=data["solution_interest"],
            request_text=data["request_text"],
            ai_processing_consent=data["ai_processing_consent"],
            ai_processing_consent_at=timezone.now() if data["ai_processing_consent"] else None,
        )
        Interaction.objects.create(
            customer=customer,
            kind=Interaction.Kind.OTHER,
            subject="Yêu cầu tư vấn từ website",
            content=data["request_text"],
            ai_processing_consent=data["ai_processing_consent"],
        )

        chat_history_raw = str(data.get("chat_history", "")).strip()
        if chat_history_raw:
            try:
                import json as _json
                history_list = clean_chat_history(_json.loads(chat_history_raw))
                lines = []
                for item in history_list:
                    role_name = "Khách hàng" if item.get("role") == "user" else "DigiFlow AI"
                    lines.append(f"{role_name}: {item.get('content', '')}")
                formatted_chat = "\n".join(lines)
            except Exception:
                formatted_chat = ""

            if formatted_chat.strip():
                Interaction.objects.create(
                    customer=customer,
                    kind=Interaction.Kind.OTHER,
                    subject="Lịch sử trao đổi cùng Trợ lý AI",
                    content=formatted_chat[:4000],
                    ai_processing_consent=data["ai_processing_consent"],
                )


@require_POST
def ai_chat_consultant(request):
    """
    Endpoint công khai cho phép khách hàng hỏi đáp trực tiếp cùng AI tư vấn giải pháp chuyển đổi số.
    """
    import json as _json

    try:
        payload = _json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Dữ liệu JSON không hợp lệ"}, status=400)

    if not isinstance(payload, dict) or not isinstance(payload.get("message"), str):
        return JsonResponse({"error": "Tin nhắn phải là chuỗi trong một đối tượng JSON."}, status=400)
    message = payload["message"].strip()
    history = clean_chat_history(payload.get("history", []))

    if not message:
        return JsonResponse({"error": "Nội dung tin nhắn không được để trống"}, status=400)

    if len(message) > 1000:
        return JsonResponse({"error": "Tin nhắn tối đa 1000 ký tự"}, status=400)

    result = answer_customer_question(message, history=history)
    return JsonResponse(result)


@staff_member_required
@permission_required("crm.manage_crm_leads", raise_exception=True)
@require_http_methods(["GET", "POST"])
def lead_follow_up(request, pk):
    lead_request = get_object_or_404(
        LeadRequest.objects.select_related("customer").prefetch_related("follow_ups__response"),
        pk=pk,
    )
    form = LeadFollowUpComposeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        token = secrets.token_urlsafe(32)
        follow_up = LeadFollowUp.objects.create(
            lead_request=lead_request,
            question_text=form.cleaned_data["question_text"],
            token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
            created_by=request.user,
            expires_at=timezone.now() + timedelta(days=settings.LEAD_FOLLOW_UP_LINK_TTL_DAYS),
        )

        try:
            site_url = settings.PUBLIC_SITE_URL.rstrip("/") + "/"
            parsed_site_url = urlsplit(site_url)
            local_http_allowed = settings.DEBUG and parsed_site_url.hostname in {"localhost", "127.0.0.1"}
            if parsed_site_url.scheme != "https" and not (parsed_site_url.scheme == "http" and local_http_allowed):
                raise ValueError("PUBLIC_SITE_URL phải dùng HTTPS ngoài môi trường phát triển local.")
            if not parsed_site_url.netloc or parsed_site_url.username or parsed_site_url.password:
                raise ValueError("PUBLIC_SITE_URL chưa được cấu hình hợp lệ.")

            reply_path = reverse("crm:lead_follow_up_reply", kwargs={"token": token})
            reply_url = urljoin(site_url, reply_path)
            context = {
                "brand_name": settings.PUBLIC_BRAND_NAME,
                "customer_name": lead_request.customer.full_name,
                "question_text": follow_up.question_text,
                "reply_url": reply_url,
                "expires_at": follow_up.expires_at,
            }
            email = EmailMultiAlternatives(
                subject=f"{settings.PUBLIC_BRAND_NAME}: bổ sung thông tin tư vấn",
                body=render_to_string("crm/emails/lead_follow_up.txt", context),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[lead_request.customer.email],
            )
            email.attach_alternative(render_to_string("crm/emails/lead_follow_up.html", context), "text/html")
            if email.send(fail_silently=False) != 1:
                raise SMTPException("Email backend không xác nhận gửi thành công.")
        except Exception:
            logger.exception("Không gửi được email bổ sung cho lead_request_id=%s", lead_request.pk)
            follow_up.status = LeadFollowUp.Status.FAILED
            follow_up.token_hash = ""
            follow_up.save(update_fields=["status", "token_hash"])
            messages.error(request, "Chưa gửi được email. Kiểm tra cấu hình email và địa chỉ website rồi thử lại.")
        else:
            LeadFollowUp.objects.filter(
                lead_request=lead_request,
                status=LeadFollowUp.Status.SENT,
            ).exclude(pk=follow_up.pk).update(
                status=LeadFollowUp.Status.REVOKED,
                token_hash="",
            )
            follow_up.status = LeadFollowUp.Status.SENT
            follow_up.sent_at = timezone.now()
            follow_up.save(update_fields=["status", "sent_at"])
            if lead_request.status == LeadRequest.Status.NEW:
                lead_request.status = LeadRequest.Status.CONTACTED
                lead_request.save(update_fields=["status"])
            Interaction.objects.create(
                customer=lead_request.customer,
                kind=Interaction.Kind.EMAIL,
                subject="Đã gửi email hỏi thêm thông tin",
                content=follow_up.question_text,
            )
            messages.success(request, f"Đã gửi email đến {lead_request.customer.email}.")

        return redirect("crm:lead_follow_up", pk=lead_request.pk)

    return render(request, "crm/lead_follow_up_compose.html", {
        "lead_request": lead_request,
        "form": form,
        "follow_ups": lead_request.follow_ups.all(),
        "brand_name": settings.PUBLIC_BRAND_NAME,
        "follow_up_ttl_days": settings.LEAD_FOLLOW_UP_LINK_TTL_DAYS,
    })


@staff_member_required
@permission_required("crm.manage_crm_leads", raise_exception=True)
@require_POST
def revoke_lead_follow_up(request, pk, follow_up_id):
    follow_up = get_object_or_404(LeadFollowUp, pk=follow_up_id, lead_request_id=pk)
    if follow_up.status == LeadFollowUp.Status.SENT:
        follow_up.status = LeadFollowUp.Status.REVOKED
        follow_up.token_hash = ""
        follow_up.save(update_fields=["status", "token_hash"])
        messages.success(request, "Đã thu hồi link trả lời của khách hàng.")
    else:
        messages.info(request, "Link này không còn ở trạng thái có thể thu hồi.")
    return redirect("crm:lead_follow_up", pk=pk)


def _find_follow_up_by_token(token):
    if len(token) != 43 or any(char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-" for char in token):
        return None
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return (
        LeadFollowUp.objects.select_related("lead_request__customer")
        .filter(token_hash=token_hash)
        .first()
    )


def _render_follow_up_public_page(request, context, status=200):
    response = render(request, "crm/lead_follow_up_public.html", context, status=status)
    # Keep the origin available for browser form POST / CSRF checks while
    # withholding the token-bearing path from Referer headers.
    response["Referrer-Policy"] = "strict-origin"
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


@never_cache
@require_http_methods(["GET", "POST"])
def lead_follow_up_reply(request, token):
    follow_up = _find_follow_up_by_token(token)
    if follow_up is None:
        return _render_follow_up_public_page(request, {
            "state": "invalid",
            "brand_name": settings.PUBLIC_BRAND_NAME,
        }, status=404)

    if follow_up.status == LeadFollowUp.Status.ANSWERED:
        return _render_follow_up_public_page(request, {
            "state": "answered",
            "brand_name": settings.PUBLIC_BRAND_NAME,
        })

    if follow_up.status != LeadFollowUp.Status.SENT:
        return _render_follow_up_public_page(request, {
            "state": "unavailable",
            "brand_name": settings.PUBLIC_BRAND_NAME,
        }, status=410)

    if follow_up.expires_at <= timezone.now():
        follow_up.status = LeadFollowUp.Status.EXPIRED
        follow_up.save(update_fields=["status"])
        return _render_follow_up_public_page(request, {
            "state": "expired",
            "brand_name": settings.PUBLIC_BRAND_NAME,
        }, status=410)

    form = LeadFollowUpResponseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            locked_follow_up = LeadFollowUp.objects.select_for_update().get(pk=follow_up.pk)
            if locked_follow_up.status != LeadFollowUp.Status.SENT or locked_follow_up.expires_at <= timezone.now():
                return _render_follow_up_public_page(request, {
                    "state": "unavailable",
                    "brand_name": settings.PUBLIC_BRAND_NAME,
                }, status=410)

            submitted_at = timezone.now()
            response = LeadFollowUpResponse.objects.create(
                follow_up=locked_follow_up,
                current_challenge=form.cleaned_data["current_challenge"],
                desired_outcome=form.cleaned_data["desired_outcome"],
                implementation_timing=form.cleaned_data["implementation_timing"],
                preferred_contact_time=form.cleaned_data["preferred_contact_time"],
                ai_processing_consent=form.cleaned_data["ai_processing_consent"],
                ai_processing_consent_at=(
                    submitted_at if form.cleaned_data["ai_processing_consent"] else None
                ),
                ai_processing_consent_version="followup-v1",
            )
            locked_follow_up.status = LeadFollowUp.Status.ANSWERED
            locked_follow_up.responded_at = submitted_at
            locked_follow_up.save(update_fields=["status", "responded_at"])
            Interaction.objects.create(
                customer=locked_follow_up.lead_request.customer,
                kind=Interaction.Kind.OTHER,
                subject="Khách hàng phản hồi form bổ sung",
                ai_processing_consent=response.ai_processing_consent,
                content=(
                    f"Khó khăn hiện tại: {response.current_challenge}\n"
                    f"Kết quả mong muốn: {response.desired_outcome or 'Chưa cung cấp'}\n"
                    f"Thời điểm dự kiến: {response.get_implementation_timing_display() or 'Chưa xác định'}\n"
                    f"Thời gian tiện liên hệ: {response.preferred_contact_time or 'Chưa cung cấp'}"
                ),
            )
        return redirect("crm:lead_follow_up_reply", token=token)

    return _render_follow_up_public_page(request, {
        "state": "form",
        "form": form,
        "follow_up": follow_up,
        "brand_name": settings.PUBLIC_BRAND_NAME,
    })


@require_http_methods(["GET"])
def privacy_notice(request):
    privacy_email = settings.PUBLIC_PRIVACY_EMAIL
    return render(request, "crm/privacy_notice.html", {
        "brand_name": settings.PUBLIC_BRAND_NAME,
        "data_controller_name": settings.PUBLIC_DATA_CONTROLLER_NAME,
        "privacy_email": privacy_email,
        "privacy_email_is_demo": _is_demo_email(privacy_email),
        "data_retention_notice": settings.PUBLIC_DATA_RETENTION_NOTICE,
    })


def _is_demo_email(email):
    """Identify reserved example domains so they are never presented as real contacts."""
    domain = email.rpartition("@")[2].lower().rstrip(".")
    return domain == "test" or domain.endswith((".test", ".example", ".invalid"))
