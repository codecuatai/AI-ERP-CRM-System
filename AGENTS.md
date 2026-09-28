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
| `crm/models.py` | Các model CRM và Wagtail `LandingPage` |
| `crm/forms.py` | Form yêu cầu tư vấn, follow-up, consent, việc chăm sóc và email draft |
| `crm/views.py` | Frontend CRM, hàng đợi ưu tiên, báo cáo/CSV, phân tích và follow-up |
| `crm/services/` | Phân tích Gemini/rules và dịch vụ soạn email nháp có consent |
| `crm/wagtail_hooks.py` | Cấu hình SnippetViewSet tìm kiếm/lọc/xem chi tiết |
| `crm/templates/crm/` | Các trang CRM, CMS landing page, báo cáo và thao tác email |
| `crm/migrations/` | Migration database phải được commit |
| `crm/test_*.py`, `crm/tests.py` | Test AI, view và form lead |
| `crm/test_browser_e2e.py` | E2E trình duyệt Chromium trên test database cô lập |
| `requirements-e2e.txt` | Phụ thuộc tùy chọn để chạy browser E2E |
| `crm/management/commands/seed_crm_data.py` | Dữ liệu demo |
| `setup_cms_homepage`, `setup_crm_groups` | Khởi tạo trang chủ CMS và nhóm quyền CRM |
| `config/settings/dev.py` | SQLite, `.env`, Gemini, môi trường local; tự sinh secret nếu thiếu |
| `config/settings/prod.py` | Profile deploy: yêu cầu secret/host/origin/HTTPS/email hợp lệ và bật secure cookies/HSTS |
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
python manage.py migrate
python manage.py setup_cms_homepage
python manage.py setup_crm_groups
python manage.py seed_crm_data
python manage.py createsuperuser
python manage.py runserver
```

### Kiểm tra bắt buộc sau khi sửa

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Nếu môi trường chưa có Django, cài dependencies trước bằng `pip install -r requirements.txt`. Khi thay đổi model, chạy `python manage.py makemigrations crm`, kiểm tra migration, rồi commit file trong `crm/migrations/`. CI dùng `python manage.py makemigrations --check --dry-run` để phát hiện model thay đổi nhưng chưa tạo migration.

Khi sửa giao diện:

```powershell
cd tailwind
npm install
npm run css:build
```

Kiểm thử E2E trình duyệt dùng Chromium và database test cô lập:

```powershell
python -m pip install -r requirements-e2e.txt
playwright install chromium
$env:RUN_BROWSER_E2E = "1"
python manage.py test crm.test_browser_e2e --verbosity=2
Remove-Item Env:RUN_BROWSER_E2E
```

Không chạy test browser có ghi dữ liệu lên database development; class `StaticLiveServerTestCase` tự tạo/xóa test database. CI chạy browser E2E riêng trên Python 3.12.

## 5. Các tính năng đã có và hướng phát triển

- `CareTask`, hàng đợi ưu tiên, email draft có người duyệt, CMS landing page, SnippetViewSet, CSV và báo cáo cơ bản đã có.
- Chạy `setup_crm_groups` sau migrate; chỉ tài khoản được gán nhóm và có quyền mới truy cập màn hình CRM. Follow-up email cần người dùng staff và quyền quản lý lead.
- AI không tự gửi email/tin nhắn; draft chỉ được lưu thành tương tác khi nhân viên chủ động xác nhận đã gửi bên ngoài.
- Trước khi nhận dữ liệu thật từ internet, cần triển khai giới hạn request cho form công khai tại reverse proxy/CDN/WAF; profile production hiện vẫn dùng SQLite, cần database/backup bền vững phù hợp tải thực tế.
- Hướng phát triển kế tiếp được theo dõi trong `docs/lo-trinh-tinh-nang.md`; cập nhật tài liệu đó khi trạng thái roadmap thay đổi.
- Giữ phạm vi CRM, không thêm kế toán, kho, nhân sự, thanh toán hoặc xử lý nền nếu nhiệm vụ không yêu cầu.

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

CI chạy khi có Pull Request vào `main` và khi có commit mới trên `main`. Các kiểm tra gồm Django check, migration check, test tự động, build frontend, pip-audit và npm audit.
