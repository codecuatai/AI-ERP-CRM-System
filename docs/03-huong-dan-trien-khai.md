# Hướng dẫn triển khai MVP

## Môi trường

- Python 3.11 hoặc 3.12
- Windows PowerShell
- API key Gemini tùy chọn; ứng dụng có phân tích cục bộ để demo offline

## Cài đặt và chạy

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py makemigrations crm
python manage.py migrate
python manage.py seed_crm_data
python manage.py createsuperuser
python manage.py runserver
```

Wagtail Admin: `http://127.0.0.1:8000/admin/`  
CRM Dashboard: `http://127.0.0.1:8000/crm/`

## Cấu hình Gemini (tùy chọn)

Điền `GEMINI_API_KEY` trong `.env` rồi khởi động lại server. Để trống key thì nút phân tích dùng quy tắc cục bộ. Nếu Gemini lỗi hoặc trả kết quả không hợp lệ, ứng dụng cũng chuyển sang phân tích cục bộ.

## Nhập dữ liệu

Lệnh `python manage.py seed_crm_data` tạo khách hàng và tương tác giả lập để demo; lệnh này không tạo tài khoản đăng nhập. Trong Wagtail Admin → Snippets, bạn cũng có thể tự tạo Customer và Interaction. Mở CRM Dashboard, vào trang chi tiết và bấm nút phân tích. Kết quả mới được lưu thành AIAnalysis và cập nhật phân khúc/điểm của Customer.

## Luồng trình bày

`Wagtail Admin → Customer + Interaction → AI service → Gemini hoặc quy tắc cục bộ → AIAnalysis → CRM Dashboard`

Khi demo, dùng dữ liệu giả lập; không nhập thông tin cá nhân thật vào API AI.
