# AI CRM với Wagtail

MVP cho đề tài **xây dựng hệ thống AI CRM quản lý và phân tích khách hàng sử dụng Wagtail CMS và Google Gemini**.

Ứng dụng tập trung vào một luồng có thể trình diễn trọn vẹn: nhân viên quản lý khách hàng và lịch sử trao đổi trong Wagtail Admin → yêu cầu AI phân tích → lưu kết quả → xem nhận định và đề xuất trên dashboard.

## Chức năng

- Quản lý Customer, Interaction và lịch sử AIAnalysis trong Wagtail Admin (Snippets).
- Dashboard và trang chi tiết khách hàng, yêu cầu đăng nhập bằng tài khoản Wagtail.
- Phân tích phân khúc, điểm tiềm năng, nhận định và đề xuất hành động.
- Gọi Gemini khi có `GEMINI_API_KEY`; nếu chưa có hoặc API lỗi, dùng quy tắc cục bộ để ứng dụng vẫn demo được.
- Lưu từng lần phân tích để xem lại kết quả.

## Cấu trúc

```text
ai_erp/                 Cấu hình Django/Wagtail, URL và entrypoints
crm/                    Model, giao diện, view và AI service
templates/crm/          Dashboard và trang chi tiết
docs/                   Kế hoạch, thiết kế và hướng dẫn báo cáo
demo/                   Bản demo HTML ban đầu được giữ lại để tham khảo
```

## Chạy trên Windows

Yêu cầu Python 3.11 hoặc 3.12.

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

Mở [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) để quản trị dữ liệu và [http://127.0.0.1:8000/crm/](http://127.0.0.1:8000/crm/) để xem CRM. Trang `/` chuyển tới dashboard. Tài khoản superuser dùng chung cho cả hai.

## Bật Gemini

Mở `.env`, thêm API key lấy từ [Google AI Studio](https://aistudio.google.com/apikey), rồi khởi động lại server:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

Không đưa `.env` hoặc dữ liệu khách hàng thật lên Git. Nếu không có key, nút phân tích vẫn hoạt động bằng quy tắc cục bộ.

## Luồng demo

1. Đăng nhập Wagtail Admin, vào Snippets và xem dữ liệu mẫu (hoặc tạo khách hàng mới).
2. Mở CRM Dashboard và chọn khách hàng có lịch sử tương tác.
3. Bấm **Phân tích bằng AI**.
4. Xem phân khúc, điểm, nhận định, đề xuất và nguồn phân tích đã lưu.

Xem kế hoạch và nội dung báo cáo trong `docs/`. Phạm vi MVP không bao gồm đơn hàng, kho hay kế toán để ưu tiên hoàn thiện luồng CRM/AI.
