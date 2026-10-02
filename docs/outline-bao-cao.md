# Dàn ý báo cáo — CRM thông minh cho doanh nghiệp chuyển đổi số

**Đề tài:** Xây dựng hệ thống CRM thông minh tích hợp AI hỗ trợ quản lý và chăm sóc khách hàng cho doanh nghiệp cung cấp giải pháp chuyển đổi số  
**Môn:** Hệ thống Kinh doanh Thông minh — Day 6  
**Ràng buộc:** Tối đa 1 lần nộp

> Tài liệu này là dàn ý để hoàn thiện báo cáo và chụp ảnh minh chứng. Không ghi kết quả kiểm thử trực tiếp trên máy hay kết quả gọi Gemini online nếu chưa thực sự chạy và xác nhận.

## 1. Mở đầu

- **Bối cảnh:** Doanh nghiệp cung cấp giải pháp chuyển đổi số tư vấn khách hàng B2B về CRM, quản lý kho/POS, hạ tầng máy chủ, sao lưu và tích hợp hệ thống. Thông tin rời rạc khiến nhân viên khó biết ai cần ưu tiên và bước chăm sóc tiếp theo là gì.
- **Mục tiêu:** tập trung hồ sơ và tương tác; thu nhận nhu cầu; hỗ trợ phân loại/chấm điểm khách hàng bằng Gemini hoặc rules fallback; chuyển đề xuất được nhân viên duyệt thành việc chăm sóc theo dõi được.
- **Phạm vi:** CRM cốt lõi trên Wagtail/Django, không phải ERP đầy đủ; không có kế toán, kho, nhân sự hay thanh toán.

## 2. Cơ sở lý thuyết

1. So sánh ERP và CRM; lý do chọn bài toán CRM cho doanh nghiệp chuyển đổi số.
2. Django xử lý nghiệp vụ và Wagtail quản trị Pages, Snippets, quyền người dùng.
3. Google Gemini SDK (`google-genai`) với structured JSON response; rules fallback đảm bảo luồng demo không phụ thuộc API.
4. Consent theo mục đích, giới hạn dữ liệu gửi AI và nguyên tắc người dùng duyệt trước hành động.

## 3. Phân tích và thiết kế hệ thống

### 3.1 Mô hình dữ liệu chính

- `Customer`: doanh nghiệp/đầu mối liên hệ, nguồn, ghi chú, tổng chi tiêu, trạng thái và kết quả phân tích mới nhất.
- `LeadRequest`: nhóm giải pháp, nội dung nhu cầu, trạng thái và consent tiếp nhận/AI được lưu riêng.
- `Interaction`: lịch sử trao đổi gắn với một khách hàng.
- `LeadFollowUp` và `LeadFollowUpResponse`: link bổ sung thông tin có hạn dùng/dùng một lần/thu hồi; phản hồi cùng consent AI riêng.
- `AIAnalysis`: lịch sử từng lần phân tích, phân khúc, điểm, nhận định, khuyến nghị và provider.
- `CareTask`: việc chăm sóc gắn với khách hàng, người phụ trách, hạn, ưu tiên và trạng thái.
- `LandingPage`: trang chủ biên tập được bằng Wagtail.

### 3.2 Luồng nghiệp vụ

```text
Khách gửi form công khai
  → Customer + LeadRequest + Interaction
  → Nhân viên xem/cập nhật lead trong CRM hoặc Wagtail
  → (tùy chọn) gửi link hỏi thêm có thời hạn
  → phản hồi được lưu; chỉ dùng cho AI nếu có consent riêng
  → nhân viên chủ động chạy phân tích Gemini / rules fallback
  → AIAnalysis + kết quả trên hồ sơ
  → nhân viên xem xét, xác nhận và tạo CareTask
  → theo dõi việc quá hạn / hôm nay / sắp tới trên dashboard
```

### 3.3 Giao diện và quyền

- Trang công khai `/`: landing page Wagtail, nhóm giải pháp, form tư vấn và trang quyền riêng tư.
- Khu vực nhân viên `/crm/`: dashboard, danh bạ, hồ sơ, hàng đợi ưu tiên, hộp thư lead, việc chăm sóc, báo cáo và CSV.
- Wagtail Admin `/admin/`: Pages và Snippets; quyền CRM được gom theo nhóm Nhân viên/Quản lý, endpoint nghiệp vụ kiểm tra quyền tương ứng.
- Frontend dùng Django Templates và Tailwind CSS; giao diện responsive.

## 4. Triển khai

1. Python 3.11/3.12, `requirements.txt`, `.env.example`; SQLite mặc định cho local.
2. `crm/models.py`, migration được commit; tạo homepage mẫu bằng `setup_cms_homepage`, nhóm quyền bằng `setup_crm_groups`, dữ liệu demo bằng `seed_crm_data`.
3. `crm/services/ai_service.py`: Gemini có kiểm tra kết quả và fallback rules.
4. `crm/services/email_draft_service.py`: soạn nháp; người dùng tự duyệt, không tự gửi.
5. Profile production ở `config/settings/prod.py`: yêu cầu secret mạnh, host rõ ràng, HTTPS URL, secure cookies/HSTS; người triển khai còn phải cấu hình SMTP, HTTPS, database bền vững và backup.
6. `.github/workflows/ci.yml`: matrix Python 3.11/3.12, migration check, Django check, test và Tailwind build.

## 5. Kiểm thử và đánh giá

Chạy tại thư mục có `manage.py`:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Các test tự động trong `crm/tests.py`, `crm/test_*.py` bao phủ form/consent, luồng lead/follow-up, quyền truy cập, việc chăm sóc, xuất dữ liệu và AI fallback. Số lượng test có thể thay đổi theo code; lấy kết quả mới từ lần chạy ngay trước khi nộp, không giữ số cũ trong báo cáo.

| Kịch bản | Cách xác nhận | Bằng chứng cần chuẩn bị |
|---|---|---|
| Wagtail/CMS | Đăng nhập, sửa trang chủ, quản lý Snippets | Ảnh Pages và Snippets |
| Lead công khai | Gửi form, thử consent bắt buộc/tùy chọn, email lặp, honeypot | Lead và hồ sơ tương ứng |
| CRM nội bộ | Tìm/lọc khách, cập nhật lead, xem hồ sơ và timeline | Dashboard, danh bạ, hồ sơ |
| Follow-up | Gửi email console, trả lời, thử dùng lại/thu hồi/hết hạn link | Email terminal và trạng thái phản hồi |
| AI fallback | Để trống `GEMINI_API_KEY`, phân tích khách đủ điều kiện | Provider `rules` và bản ghi `AIAnalysis` |
| AI online | Chỉ chạy khi có API key được cấp và cho phép | Kết quả thực tế; không đưa key vào ảnh/báo cáo |
| Việc chăm sóc | Tạo, sửa/hoàn tất; kiểm tra hạn trên dashboard | Việc liên kết khách hàng và dashboard |
| Production settings | Cấu hình env staging an toàn, chạy `check --deploy` | Output kiểm tra và cấu hình đã che secret |

Ghi lại kết quả thực tế: ngày chạy, phiên bản Python, lệnh, số test thành công/thất bại, kết quả CI và vấn đề còn lại. Chưa gọi Gemini online nếu không có key; không dùng thông tin khách hàng thật trong demo.

## 6. Kết luận và hướng phát triển

- Đánh giá luồng CRM từ tiếp nhận nhu cầu đến phân tích, người duyệt và việc theo dõi.
- Nêu rõ giới hạn: SQLite vẫn là mặc định local; fallback là heuristics minh họa; chưa có tác vụ nền hoặc nhập CSV. Luồng PostgreSQL/Superset đã có cấu hình Docker riêng cho demo analytics.
- Hướng phát triển: nhập CSV có preview/validation, lọc báo cáo theo thời gian, PostgreSQL và backup/monitoring trước khi triển khai thực tế.

## Phụ lục

- Các lệnh setup và chạy app: xem [README](../README.md#bắt-đầu-nhanh).
- Tính năng đã có/còn thiếu: xem [roadmap](lo-trinh-tinh-nang.md).
- Không ghi mật khẩu/tài khoản demo, API key, token follow-up hay dữ liệu cá nhân thật vào báo cáo công khai.
