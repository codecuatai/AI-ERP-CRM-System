from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from .models import AIAnalysis, CareTask, Customer, Interaction, LeadRequest, SalesRecord


class SeedCRMDataCommandTests(TestCase):
    def test_seed_adds_a_varied_fictional_dataset_and_is_idempotent(self):
        call_command("seed_crm_data", stdout=StringIO())

        self.assertEqual(Customer.objects.count(), 30)
        self.assertEqual(Interaction.objects.count(), 58)
        self.assertEqual(LeadRequest.objects.count(), 24)
        self.assertEqual(AIAnalysis.objects.count(), 20)
        self.assertEqual(CareTask.objects.count(), 19)
        self.assertEqual(SalesRecord.objects.count(), 12)
        self.assertTrue(SalesRecord.objects.filter(status=SalesRecord.Status.VOID).exists())
        self.assertTrue(SalesRecord.objects.filter(status=SalesRecord.Status.WON).exists())
        self.assertTrue(Customer.objects.filter(email__endswith="@digiflow.test").exists())
        self.assertTrue(LeadRequest.objects.filter(ai_processing_consent=True).exists())
        self.assertTrue(LeadRequest.objects.filter(ai_processing_consent=False).exists())
        self.assertTrue(CareTask.objects.filter(status=CareTask.Status.DONE).exists())
        self.assertTrue(CareTask.objects.filter(status=CareTask.Status.IN_PROGRESS).exists())

        call_command("seed_crm_data", stdout=StringIO())

        self.assertEqual(Customer.objects.count(), 30)
        self.assertEqual(Interaction.objects.count(), 58)
        self.assertEqual(LeadRequest.objects.count(), 24)
        self.assertEqual(AIAnalysis.objects.count(), 20)
        self.assertEqual(CareTask.objects.count(), 19)
        self.assertEqual(SalesRecord.objects.count(), 12)

    def test_seed_does_not_overwrite_existing_customer_fields(self):
        customer = Customer.objects.create(
            full_name="Tên do người dùng chỉnh sửa",
            email="contact@alpha-tech.vn",
            company="Công ty đã tùy chỉnh",
            notes="Ghi chú cần được giữ nguyên.",
        )

        call_command("seed_crm_data", stdout=StringIO())

        customer.refresh_from_db()
        self.assertEqual(customer.full_name, "Tên do người dùng chỉnh sửa")
        self.assertEqual(customer.company, "Công ty đã tùy chỉnh")
        self.assertEqual(customer.notes, "Ghi chú cần được giữ nguyên.")
