#!/bin/sh
set -e

# Chờ kết nối PostgreSQL sẵn sàng nếu sử dụng PostgreSQL
python - <<'EOF'
import os
import sys
import time
import socket
from urllib.parse import urlsplit

db_url = os.environ.get("DJANGO_DATABASE_URL", "").strip()
if db_url and any(db_url.startswith(p) for p in ("postgres://", "postgresql://")):
    parsed = urlsplit(db_url)
    host = parsed.hostname or "crm-db"
    port = parsed.port or 5432
    print(f"==> Đang kiểm tra kết nối cơ sở dữ liệu PostgreSQL tại {host}:{port}...", flush=True)
    for attempt in range(1, 46):
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"==> Kết nối PostgreSQL thành công ({host}:{port})!", flush=True)
                sys.exit(0)
        except OSError:
            time.sleep(1)
    print(f"==> LỖI: Hết thời gian chờ kết nối PostgreSQL ({host}:{port})", file=sys.stderr, flush=True)
    sys.exit(1)
EOF

# Kiểm tra nếu lệnh được gọi là khởi động web server (runserver hoặc tương đương)
is_runserver=0
for arg in "$@"; do
    if [ "$arg" = "runserver" ]; then
        is_runserver=1
        break
    fi
done

if [ "$is_runserver" -eq 1 ]; then
    echo "==> Đang thực hiện migrate database..."
    python manage.py migrate --noinput

    echo "==> Đang thiết lập trang chủ CMS Wagtail..."
    python manage.py setup_cms_homepage || true

    echo "==> Đang thiết lập nhóm quyền CRM..."
    python manage.py setup_crm_groups || true

    # Khởi tạo dữ liệu mẫu nếu có cờ DJANGO_SEED_DATA
    if [ "${DJANGO_SEED_DATA}" = "true" ] || [ "${DJANGO_SEED_DATA}" = "1" ]; then
        echo "==> Đang khởi tạo dữ liệu mẫu CRM..."
        python manage.py seed_crm_data || true
    fi

    echo "==> Đang thiết lập analytics views cho Apache Superset..."
    python manage.py setup_superset_analytics || true

    # Tự động tạo superuser nếu có biến môi trường
    if [ -n "${DJANGO_SUPERUSER_USERNAME}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD}" ]; then
        python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@digiflow.test')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'==> Đã tạo tài khoản quản trị (superuser): {username}')
else:
    print(f'==> Tài khoản {username} đã tồn tại.')
" || true
    fi
fi

exec "$@"
