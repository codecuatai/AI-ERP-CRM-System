"""Verify that Superset analytics views match the CRM source tables."""

from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Đối chiếu các view analytics với dữ liệu CRM nguồn trước khi mở dashboard Superset."

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError(
                "Superset analytics verification requires PostgreSQL. "
                "Set DJANGO_DATABASE_URL and retry."
            )

        checks = {
            "customers": (
                "SELECT count(*)::bigint, coalesce(sum(total_spent), 0)::numeric FROM crm_customer",
                "SELECT coalesce(sum(customer_count), 0)::bigint, "
                "coalesce(sum(recorded_customer_spend), 0)::numeric "
                "FROM analytics.customer_monthly",
            ),
            "leads": (
                "SELECT count(*)::bigint FROM crm_leadrequest",
                "SELECT coalesce(sum(lead_count), 0)::bigint FROM analytics.lead_pipeline",
            ),
            "care tasks": (
                "SELECT count(*)::bigint FROM crm_caretask",
                "SELECT coalesce(sum(task_count), 0)::bigint FROM analytics.care_task_summary",
            ),
            "revenue": (
                "SELECT coalesce(sum(amount), 0)::numeric FROM crm_salesrecord WHERE status = 'WON'",
                "SELECT coalesce(sum(won_revenue), 0)::numeric FROM analytics.revenue_transactions",
            ),
        }

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT table_name FROM information_schema.views "
                    "WHERE table_schema = 'analytics'"
                )
                views = {row[0] for row in cursor.fetchall()}
                expected_views = {
                    "customer_monthly",
                    "lead_pipeline",
                    "care_task_summary",
                    "revenue_transactions",
                }
                missing = expected_views - views
                if missing:
                    raise CommandError(
                        "Thiếu view analytics: " + ", ".join(sorted(missing))
                    )

                for label, (source_sql, view_sql) in checks.items():
                    cursor.execute(source_sql)
                    source = cursor.fetchone()
                    cursor.execute(view_sql)
                    view = cursor.fetchone()
                    if tuple(Decimal(str(value or 0)) for value in source) != tuple(
                        Decimal(str(value or 0)) for value in view
                    ):
                        raise CommandError(
                            f"Đối chiếu {label} không khớp: nguồn={source}, view={view}"
                        )
                    self.stdout.write(self.style.SUCCESS(f"PASS {label}: {source}"))
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(
                "Không thể đọc view analytics. Hãy chạy setup_superset_analytics trước."
            ) from exc

        self.stdout.write(self.style.SUCCESS("Analytics views match CRM source data."))
