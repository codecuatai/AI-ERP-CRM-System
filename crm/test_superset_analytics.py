from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import SimpleTestCase


class SupersetAnalyticsCommandTests(SimpleTestCase):
    def test_analytics_views_require_postgresql(self):
        with patch.object(connection, "vendor", "sqlite"):
            with self.assertRaisesMessage(CommandError, "Superset analytics views require PostgreSQL"):
                call_command("setup_superset_analytics")

    def test_verification_requires_postgresql(self):
        with patch.object(connection, "vendor", "sqlite"):
            with self.assertRaisesMessage(CommandError, "Superset analytics verification requires PostgreSQL"):
                call_command("verify_superset_analytics")
