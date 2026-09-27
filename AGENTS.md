# Hướng dẫn cho AI agent

## 1. Bối cảnh dự án

Đây là đồ án **“Xây dựng hệ thống CRM thông minh tích hợp AI hỗ trợ quản lý và chăm sóc khách hàng cho doanh nghiệp cung cấp giải pháp chuyển đổi số”**.

Doanh nghiệp trong bối cảnh này tư vấn, bán và triển khai các giải pháp như phần mềm quản lý kho, POS, CRM, hạ tầng máy chủ, sao lưu dữ liệu và tích hợp hệ thống cho khách hàng B2B.

Mục tiêu của hệ thống là giúp nhân viên kinh doanh:

- Tập trung thông tin khách hàng và lịch sử trao đổi.
- Xác định khách hàng cần ưu tiên.
- Dùng Gemini hoặc rules fallback để phân khúc, chấm điểm và đề xuất chăm sóc.
- Biến đề xuất của AI thành hành động có thể theo dõi.

Không mở rộng dự án thành ERP đầy đủ. Không tự thêm kế toán, kho, nhân sự, thanh toán hoặc quản lý triển khai nếu nhiệm vụ không yêu cầu.

## 2. Công nghệ và cấu trúc

- Python 3.11 hoặc 3.12.
- Django được cài thông qua Wagtail `>=7.0,<9.0`.
- Wagtail Snippets để quản trị dữ liệu.
- SQLite cho môi trường development.
- Django Templates + Tailwind CSS 3.4.19 cho frontend.
- Google Gemini qua `google-genai`; rules fallback bắt buộc vẫn phải hoạt động khi thiếu API key.

Các file quan trọng:

| File/thư mục | Vai trò |
|---|---|
| `crm/models.py` | `Customer`, `Interaction`, `LeadRequest`, `LeadFollowUp`, `LeadFollowUpResponse`, `AIAnalysis` |
| `crm/forms.py` | Form yêu cầu tư vấn, soạn email follow-up, phản hồi và consent |
| `crm/views.py` | Form công khai/follow-up, gửi email, Dashboard, hồ sơ và endpoint phân tích |
| `crm/services/ai_service.py` | Gemini và `_rule_based_analysis()` |
| `crm/templates/crm/` | Form công khai, Dashboard, hồ sơ và layout |
| `crm/migrations/` | Migration database phải được commit |
| `crm/test_*.py`, `crm/tests.py` | Test AI, view và form lead |
| `crm/management/commands/seed_crm_data.py` | Dữ liệu demo |
| `config/settings/dev.py` | SQLite, `.env`, Gemini, môi trường local |
| `PUBLIC_SITE_URL`, `EMAIL_*` | Domain link phản hồi và cấu hình SMTP; local mặc định in email ra terminal |
| `tailwind/` | Nguồn Tailwind và lệnh build CSS |
| `.github/workflows/ci.yml` | CI cho backend và frontend |
| `README.md` | Tài liệu người dùng và mô tả dự án |

## 3. Quy tắc làm việc

1. Đọc `README.md`, các model/view/service liên quan và tài liệu roadmap trước khi sửa code.
2. Giữ đúng bối cảnh khách hàng B2B của doanh nghiệp chuyển đổi số.
3. Ưu tiên thay đổi nhỏ, dễ kiểm tra; không viết lại kiến trúc hiện tại.
4. Mọi thay đổi database phải cập nhật model và tạo migration phù hợp.
5. Không xóa dữ liệu, file hoặc tính năng hiện có nếu nhiệm vụ không yêu cầu.
6. Không đưa API key, mật khẩu hoặc dữ liệu khách hàng thật vào source code.
7. Không để AI tự gửi email/tin nhắn hoặc tự thay đổi dữ liệu quan trọng nếu chưa có bước xác nhận của người dùng.
8. Khi Gemini không khả dụng, tính năng liên quan phải có thông báo rõ ràng hoặc fallback an toàn.
9. Giao diện phải dùng tiếng Việt và tương thích mobile.
10. Sau khi hoàn thành, cập nhật README nếu có thay đổi luồng sử dụng.

## 4. Cách chạy và kiểm tra

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py makemigrations crm
python manage.py migrate
python manage.py seed_crm_data
python manage.py createsuperuser
python manage.py runserver
```

### Kiểm tra bắt buộc sau khi sửa

```powershell
python manage.py check
python manage.py test
```

Nếu môi trường chưa có Django, cài dependencies trước bằng `pip install -r requirements.txt`. Khi thay đổi model, chạy `python manage.py makemigrations crm`, kiểm tra migration, rồi commit file trong `crm/migrations/`. CI dùng `python manage.py makemigrations --check --dry-run` để phát hiện model thay đổi nhưng chưa tạo migration.

Khi sửa giao diện:

```powershell
cd tailwind
npm install
npm run css:build
```

## 5. Nhiệm vụ ưu tiên tiếp theo

### Xây dựng “Việc cần chăm sóc khách hàng”

Biến đề xuất từ AI thành một việc có thể giao và theo dõi.

#### Phạm vi chức năng

- Tạo việc từ trang hồ sơ khách hàng.
- Cho phép nhập nội dung việc cần làm.
- Việc thuộc về đúng một khách hàng.
- Có loại việc: liên hệ lại, gọi điện, gửi báo giá, hẹn gặp hoặc khác.
- Có người phụ trách; nếu hệ thống chưa có cơ chế phân công riêng, dùng user đăng nhập hiện tại.
- Có ngày đến hạn.
- Có mức ưu tiên: thấp, vừa, cao.
- Có trạng thái: `Cần làm`, `Đang làm`, `Hoàn tất`.
- Có thể chỉnh sửa và đánh dấu hoàn tất.
- Dashboard hiển thị ít nhất: việc hôm nay, việc quá hạn và việc sắp tới.
- Từ đề xuất AI có thể mở form tạo việc với nội dung gợi ý được điền sẵn; người dùng phải xác nhận trước khi lưu.

#### Gợi ý mô hình dữ liệu

Tạo model mới, ví dụ `CareTask`, gồm tối thiểu:

- `customer`: ForeignKey đến `Customer`.
- `title` hoặc `content`: nội dung việc.
- `kind`: loại việc.
- `assignee`: ForeignKey đến user, cho phép xử lý theo quy tắc của dự án hiện tại.
- `due_at`: hạn hoàn thành.
- `priority`: thấp/vừa/cao.
- `status`: cần làm/đang làm/hoàn tất.
- `created_at`, `updated_at`, và thời điểm hoàn tất nếu cần.

Model phải được đăng ký trong Wagtail Snippets để có thể quản trị thủ công.

#### Tiêu chí hoàn thành

- Nhân viên tạo được việc từ một khách hàng cụ thể.
- Việc hiển thị đúng trong hồ sơ khách hàng.
- Có thể sửa trạng thái và đánh dấu hoàn tất.
- Dashboard phân biệt đúng việc hôm nay, quá hạn và sắp tới.
- Không tạo việc nếu người dùng chưa xác nhận form.
- Migration chạy thành công.
- Có dữ liệu mẫu để trình diễn ít nhất việc quá hạn và việc sắp tới.
- Rules fallback vẫn chạy nếu không có `GEMINI_API_KEY`.
- README mô tả được luồng sử dụng mới.

#### Không làm trong nhiệm vụ này

- Không tự động gửi email, SMS, Zalo hoặc thông báo bên ngoài.
- Không xây dựng Celery, cron hoặc xử lý nền.
- Không thêm module kế toán, kho, nhân sự hay thanh toán.
- Không thay đổi tên model CRM hiện có nếu không cần thiết.

## 6. Bàn giao kết quả

Khi hoàn thành một nhiệm vụ, agent phải báo cáo:

1. Các file đã thay đổi.
2. Chức năng đã triển khai.
3. Migration hoặc dữ liệu seed đã cập nhật.
4. Các lệnh kiểm tra đã chạy và kết quả.
5. Vấn đề còn lại hoặc quyết định cần người dùng xác nhận.

## 7. Quy trình Git của nhóm

Chỉ sử dụng một nhánh chính:

```text
main  ←  feature branch / bugfix branch
```

- `main` là nhánh ổn định và là nhánh duy nhất để tích hợp.
- Không commit trực tiếp vào `main`.
- Mỗi nhiệm vụ tạo một nhánh riêng, ví dụ `feature/care-tasks` hoặc `fix/ai-fallback`.
- Mở Pull Request từ nhánh nhiệm vụ vào `main`.
- Chỉ merge sau khi CI chạy thành công và có người xem lại thay đổi.
- Ưu tiên **Squash and merge** để lịch sử `main` gọn.
- Sau khi merge, xóa nhánh nhiệm vụ.

CI chỉ cần chạy khi có Pull Request vào `main` và khi có commit mới trên `main`. Các kiểm tra bắt buộc gồm Django check, migration check, test tự động và build frontend.
