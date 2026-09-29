import csv
from pathlib import Path
import tempfile
from io import StringIO

from django.core.management import call_command, CommandError
from django.test import TestCase

from .models import Customer


class ImportCRMCustomersCommandTests(TestCase):
    def run_import(self, rows, *args, headers=None):
        headers = headers or ["full_name", "email", "company", "total_spent", "is_active"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "customers.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)
            output = StringIO()
            call_command("import_crm_customers", str(path), *args, stdout=output)
            return output.getvalue()

    def test_dry_run_validates_without_writing(self):
        output = self.run_import([
            {"full_name": "Nguyễn Văn A", "email": "A@congty.vn", "company": "ABC", "total_spent": "0", "is_active": "true"},
        ], "--dry-run")

        self.assertIn("1 hồ sơ sẵn sàng nhập", output)
        self.assertFalse(Customer.objects.exists())

    def test_import_creates_customers_and_duplicate_email_is_skipped(self):
        self.run_import([
            {"full_name": "Nguyễn Văn A", "email": "A@congty.vn", "company": "ABC", "total_spent": "1200000", "is_active": "true"},
        ])
        output = self.run_import([
            {"full_name": "Tên khác", "email": "a@congty.vn", "company": "Khác", "total_spent": "0", "is_active": "false"},
        ])

        self.assertEqual(Customer.objects.count(), 1)
        customer = Customer.objects.get()
        self.assertEqual(customer.full_name, "Nguyễn Văn A")
        self.assertEqual(customer.total_spent, 1200000)
        self.assertIn("bỏ qua email trùng 1", output)

    def test_update_changes_only_fields_present_in_csv(self):
        Customer.objects.create(full_name="Tên cũ", email="a@congty.vn", company="Công ty cũ", phone="0900")

        self.run_import(
            [{"full_name": "Tên mới", "email": "A@congty.vn", "company": "Công ty mới"}],
            "--update",
            headers=["full_name", "email", "company"],
        )

        customer = Customer.objects.get()
        self.assertEqual(customer.full_name, "Tên mới")
        self.assertEqual(customer.company, "Công ty mới")
        self.assertEqual(customer.phone, "0900")

    def test_invalid_later_row_rejects_the_whole_import_before_writing(self):
        with self.assertRaises(CommandError):
            self.run_import([
                {"full_name": "Hợp lệ", "email": "ok@congty.vn", "company": "ABC", "total_spent": "0", "is_active": "true"},
                {"full_name": "Thiếu email", "email": "", "company": "ABC", "total_spent": "0", "is_active": "true"},
            ])

        self.assertFalse(Customer.objects.exists())
