"""Create privacy-limited PostgreSQL views for Apache Superset."""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection


ANALYTICS_VIEWS = {
    "customer_monthly": """
        SELECT date_trunc('month', created_at)::date AS month,
               ai_segment AS segment,
               count(*)::bigint AS customer_count,
               coalesce(sum(total_spent), 0)::numeric AS recorded_customer_spend
        FROM crm_customer
        GROUP BY 1, 2
    """,
    "lead_pipeline": """
        SELECT date_trunc('month', created_at)::date AS month,
               status,
               solution_interest,
               count(*)::bigint AS lead_count
        FROM crm_leadrequest
        GROUP BY 1, 2, 3
    """,
    "care_task_summary": """
        SELECT date_trunc('month', created_at)::date AS month,
               kind,
               priority,
               status,
               count(*)::bigint AS task_count,
               count(*) FILTER (
                   WHERE status != 'DONE' AND due_at < current_date
               )::bigint AS overdue_count
        FROM crm_caretask
        GROUP BY 1, 2, 3, 4
    """,
    "revenue_transactions": """
        SELECT closed_at,
               amount,
               status,
               CASE WHEN status = 'WON' THEN amount ELSE 0 END AS won_revenue
        FROM crm_salesrecord
    """,
}


class Command(BaseCommand):
    help = "Tạo các view tổng hợp, không chứa thông tin liên hệ, cho Superset đọc."

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError(
                "Superset analytics views require PostgreSQL. Set DJANGO_DATABASE_URL and retry."
            )

        try:
            with connection.cursor() as cursor:
                cursor.execute("CREATE SCHEMA IF NOT EXISTS analytics AUTHORIZATION CURRENT_USER")
                for name, select_sql in ANALYTICS_VIEWS.items():
                    cursor.execute(f"CREATE OR REPLACE VIEW analytics.{name} AS {select_sql}")
                    cursor.execute(f"GRANT SELECT ON analytics.{name} TO superset_ro")
                cursor.execute("GRANT USAGE ON SCHEMA analytics TO superset_ro")
                cursor.execute(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA analytics "
                    "GRANT SELECT ON TABLES TO superset_ro"
                )
        except Exception as exc:
            raise CommandError(
                "Không thể tạo view analytics hoặc cấp quyền cho superset_ro. "
                "Hãy kiểm tra role được tạo bởi Docker Compose Superset và quyền database."
            ) from exc

        self.stdout.write(self.style.SUCCESS(
            "Created 4 views in schema analytics and granted Superset read-only access."
        ))
