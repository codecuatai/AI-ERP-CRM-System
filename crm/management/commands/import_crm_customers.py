"""Import real CRM customer records from a CSV file."""

import csv
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import transaction

from crm.models import Customer


REQUIRED_COLUMNS = {"full_name", "email"}
OPTIONAL_COLUMNS = {"phone", "company", "source", "notes", "total_spent", "is_active"}
ALLOWED_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS


class Command(BaseCommand):
    help = "Nhập hồ sơ khách hàng từ CSV (UTF-8); không tự tạo dữ liệu mẫu."

    def add_arguments(self, parser):
        parser.add_argument("csv_file", help="Đường dẫn file CSV khách hàng.")
        parser.add_argument(
            "--update",
            action="store_true",
            help="Cập nhật hồ sơ có email trùng; mặc định bỏ qua để tránh ghi đè.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Kiểm tra và báo số dòng có thể nhập nhưng không ghi database.",
        )

    def handle(self, *args, **options):
        path = options["csv_file"]
        try:
            with open(path, "r", encoding="utf-8-sig", newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                headers = {header.strip() for header in (reader.fieldnames or []) if header}
                missing = REQUIRED_COLUMNS - headers
                unknown = headers - ALLOWED_COLUMNS
                if missing:
                    raise CommandError(f"Thiếu cột bắt buộc: {', '.join(sorted(missing))}")
                if unknown:
                    raise CommandError(f"Cột không được hỗ trợ: {', '.join(sorted(unknown))}")
                rows = self._validate_rows(reader, headers)
        except OSError as exc:
            raise CommandError(f"Không đọc được file CSV: {exc}") from exc
        except UnicodeError as exc:
            raise CommandError("File phải dùng mã hóa UTF-8 hoặc UTF-8 có BOM.") from exc

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS(f"CSV hợp lệ: {len(rows)} hồ sơ sẵn sàng nhập (dry-run)."))
            return

        created = updated = skipped = 0
        with transaction.atomic():
            for email, values in rows:
                customer = Customer.objects.filter(email__iexact=email).first()
                if customer:
                    if options["update"]:
                        for field, value in values.items():
                            setattr(customer, field, value)
                        customer.save(update_fields=[*values.keys(), "updated_at"])
                        updated += 1
                    else:
                        skipped += 1
                    continue
                Customer.objects.create(**values)
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Hoàn tất: tạo {created}, cập nhật {updated}, bỏ qua email trùng {skipped}."
        ))

    def _validate_rows(self, reader, headers):
        rows = []
        seen_emails = set()
        for row_number, raw in enumerate(reader, start=2):
            row = {(key or "").strip(): (value or "").strip() for key, value in raw.items()}
            email = row.get("email", "").lower()
            name = row.get("full_name", "")
            errors = []
            if not email:
                errors.append("thiếu email")
            if not name:
                errors.append("thiếu họ tên")
            elif len(name) > 160:
                errors.append("họ tên vượt quá 160 ký tự")
            if email in seen_emails:
                errors.append("email bị lặp trong file")
            if email:
                try:
                    validate_email(email)
                except ValidationError:
                    errors.append("email không hợp lệ")
                if len(email) > 254:
                    errors.append("email vượt quá 254 ký tự")
            seen_emails.add(email)

            values = {key: row[key] for key in headers & OPTIONAL_COLUMNS if key in row}
            values.update(full_name=name, email=email)
            for field, limit in (("phone", 30), ("company", 160), ("source", 100)):
                if field in values and len(values[field]) > limit:
                    errors.append(f"{field} vượt quá {limit} ký tự")
            if "total_spent" in values:
                try:
                    amount = Decimal(values["total_spent"] or "0")
                    if not amount.is_finite() or amount < 0 or amount > Decimal("99999999999999"):
                        raise InvalidOperation
                    values["total_spent"] = amount.quantize(Decimal("1"))
                except (InvalidOperation, ValueError):
                    errors.append("total_spent phải là số tiền không âm")
            if "is_active" in values:
                boolean = values["is_active"].lower()
                if boolean not in {"true", "false", "1", "0", "yes", "no", "co", "khong"}:
                    errors.append("is_active dùng true/false, 1/0, yes/no hoặc co/khong")
                else:
                    values["is_active"] = boolean in {"true", "1", "yes", "co"}
            if errors:
                raise CommandError(f"Dòng {row_number}: {', '.join(errors)}")
            rows.append((email, values))
        return rows
