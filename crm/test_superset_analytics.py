from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase


class SupersetAnalyticsCommandTests(SimpleTestCase):
    def test_analytics_views_require_postgresql(self):
        with self.assertRaisesMessage(CommandError, "Superset analytics views require PostgreSQL"):
            call_command("setup_superset_analytics")
