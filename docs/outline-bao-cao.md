# Dàn ý báo cáo nộp — CRM thông minh cho doanh nghiệp chuyển đổi số

**Đề tài:** Xây dựng hệ thống CRM thông minh tích hợp AI hỗ trợ quản lý và chăm sóc khách hàng cho doanh nghiệp cung cấp giải pháp chuyển đổi số  
**Môn:** Hệ thống Kinh doanh Thông minh — Day 6  
**Ràng buộc:** Tối đa 1 lần nộp  

---

## 1. Mở đầu
- **Bối cảnh:** Doanh nghiệp cung cấp giải pháp chuyển đổi số thường phải tư vấn, demo, triển khai và chăm sóc nhiều khách hàng B2B cùng lúc. Nếu dữ liệu khách hàng và lịch sử trao đổi nằm rời rạc, nhân viên khó xác định khách hàng nào cần ưu tiên và nên thực hiện bước chăm sóc nào tiếp theo.
- **Mục tiêu:**
  1. Xây dựng hệ thống CRM trên nền tảng Wagtail CMS để quản lý khách hàng doanh nghiệp và lịch sử tư vấn/triển khai giải pháp.
  2. Tích hợp AI (Google Gemini) để phân khúc khách hàng, chấm điểm tiềm năng và đề xuất hành động chăm sóc.
  3. Xây dựng Frontend Dashboard để nhân viên kinh doanh theo dõi khách hàng và kết quả AI.
  4. Có cơ chế fallback bằng quy tắc cục bộ khi thiếu API key hoặc dịch vụ AI gặp sự cố.
- **Phạm vi:** Trọng tâm vào luồng CRM của doanh nghiệp chuyển đổi số: Quản trị khách hàng và tương tác → Đánh giá nhu cầu/tiềm năng → Đề xuất chăm sóc. Dự án không triển khai kế toán, tồn kho, nhân sự hoặc toàn bộ ERP.

---

## 2. Cơ sở lý thuyết
- **2.1 ERP vs CRM:** So sánh tổng quan, lý do lựa chọn phân hệ CRM làm trọng tâm trong bài toán quản lý khách hàng của doanh nghiệp chuyển đổi số.
- **2.2 Wagtail CMS & Django:**
  - Vì sao chọn Wagtail: Giao diện quản trị hiện đại, tính năng Snippets (`@register_snippet`) cho phép quản lý thực thể phi cấu trúc trang linh hoạt.
  - Tổ chức Panel: `FieldPanel`, `MultiFieldPanel` giúp cấu trúc form nhập liệu trực quan.
- **2.3 Mô hình AI và cơ chế tích hợp:**
  - Google Gemini API (`google-genai>=1.0.0`), model `gemini-3.5-flash-lite`.
  - Structured Output với `response_mime_type="application/json"`.
  - Cơ chế Fallback quy tắc cục bộ (`_rule_based_analysis`) đảm bảo ứng dụng không crash khi API gặp sự cố.

---

## 3. Phân tích và Thiết kế hệ thống
- **3.1 Kiến trúc dữ liệu (Data Architecture):**
  - `Customer`: Thông tin định danh, doanh thu lũy kế (`total_spent`), kết quả AI cache (`ai_segment`, `ai_score`); được tạo từ form website hoặc Wagtail Admin.
  - `Interaction`: Lịch sử tương tác (Email, Điện thoại, Gặp mặt, Khác) theo quan hệ 1—n với Customer.
  - `LeadRequest`: Nhóm giải pháp, nội dung nhu cầu, trạng thái; consent tiếp nhận và consent AI tùy chọn được lưu tách biệt cùng dấu thời gian/phiên bản.
  - `AIAnalysis`: Bản ghi lịch sử mỗi lần AI phân tích (Audit log gồm phân khúc, điểm, nhận định, đề xuất, nguồn provider).
- **3.2 Luồng xử lý dữ liệu (Data Flow):**
  - `Khách gửi form → Customer + LeadRequest + Interaction lưu DB → Nhân viên xem trong Wagtail → Nếu có consent AI thì bấm phân tích → AI Service (Gemini/Rules) → AIAnalysis & cập nhật Customer → Dashboard`.
- **3.3 Thiết kế giao diện (UI/UX):**
  - Landing page công khai tại `/` giới thiệu doanh nghiệp/giải pháp và form thu thập yêu cầu; khu vực nhân viên tách riêng tại `/crm/`.
  - Trang Dashboard dùng Django Templates và Tailwind CSS: thống kê, tìm kiếm/lọc, bảng khách hàng và điểm tiềm năng.
  - Trang chi tiết: hồ sơ, timeline trao đổi, nút phân tích AI, kết quả và lịch sử phân tích.
  - Form tư vấn công khai: có lựa chọn giải pháp, thu nhu cầu; consent nhận/phản hồi bắt buộc và consent AI tùy chọn, không gộp mục đích. Có trang thông báo quyền riêng tư mẫu.

---

## 4. Triển khai hệ thống (Kèm ảnh chụp màn hình minh họa)
- **4.1 Khởi tạo dự án & Môi trường:**
  - Cấu hình `config/settings/base.py`, `config/settings/dev.py`, quản lý secret qua `.env`.
  - Thư viện: `wagtail>=7.0`, `google-genai>=1.0.0`, `python-dotenv>=1.0.0`.
- **4.2 Xây dựng Models & Snippets:**
  - Trích xuất code `Customer`, `Interaction`, `LeadRequest`, `AIAnalysis` trong `crm/models.py`.
- **4.3 Tích hợp AI Service & Fallback:**
  - Trích xuất hàm `analyze_customer` và `_rule_based_analysis` trong `crm/services/ai_service.py`.
  - Kỹ thuật prompt engineering định dạng JSON cho bài toán phân tích CRM.
- **4.4 Giao diện người dùng:**
  - Templates `crm/templates/crm/landing_page.html`, `crm/templates/crm/lead_request.html`, `crm/templates/crm/dashboard.html` và `crm/templates/crm/customer_detail.html`.
- **4.5 Tự động hóa Seed dữ liệu:**
  - Lệnh `python manage.py seed_crm_data` nạp dữ liệu giả lập; tạo tài khoản riêng bằng `python manage.py createsuperuser`.
- **4.6 Kiểm thử và CI:**
  - Test Django nằm trong `crm/tests.py`, `crm/test_ai_service.py` và `crm/test_views.py`.
  - GitHub Actions tại `.github/workflows/ci.yml` chạy trên Pull Request hoặc push vào `main`, kiểm tra Python 3.11/3.12, migration, Django check, test backend và build Tailwind.

---

## 5. Kiểm thử và Đánh giá

| Kịch bản kiểm thử | Thao tác thực hiện | Kết quả mong đợi | Kết quả thực tế |
|---|---|---|---|
| **KT1: Quản trị Wagtail** | Đăng nhập Admin, tạo mới Customer và 2 Interaction | Bản ghi hiển thị đầy đủ trong Snippets | Django check và migration đã đạt; cần chụp ảnh thao tác Admin trước khi nộp |
| **KT2: Phân tích AI (Online)** | Cấu hình `GEMINI_API_KEY`, bấm "Phân tích bằng AI" | Trả về phân khúc, điểm, đề xuất với provider `gemini` | Chưa chạy vì môi trường kiểm thử chưa cấu hình API key |
| **KT3: Fallback (Offline)** | Bỏ trống `GEMINI_API_KEY`, bấm phân tích | Hệ thống dùng rule-based, thông báo rõ ràng, không crash | Đã đạt trong test tự động; provider `rules` |
| **KT4: Lưu vết lịch sử** | Phân tích nhiều lần cho 1 khách hàng | `AIAnalysis` lưu từng lần, Customer cập nhật giá trị mới nhất | Luồng code đã có; cần kiểm tra thủ công hoặc bổ sung test riêng |
| **KT5: Form tư vấn công khai** | Gửi form, bỏ consent bắt buộc, bật/tắt consent AI, email trùng, honeypot | Consent AI lưu riêng; không đồng ý vẫn tiếp nhận lead nhưng chặn AI; từ chối consent nhận thiếu/bot; không tạo Customer trùng | Kiểm tra bằng test tự động |
| **KT6: Giới hạn dữ liệu AI** | Chỉ đồng ý một lead trong nhiều yêu cầu và chạy phân tích | Prompt Gemini chỉ có nội dung/nhóm giải pháp đã đồng ý; không có định danh hoặc yêu cầu chưa đồng ý | Đã đạt trong test tự động |

Lần kiểm tra sau khi hoàn thiện form: **23 test đạt**, `python manage.py check` đạt, `makemigrations --check --dry-run` không phát hiện migration thiếu và Tailwind build thành công. Gemini online chưa được xác nhận vì chưa dùng API key thật.

---

## 6. Kết luận và Hướng phát triển
- **Kết quả cần xác nhận:** Bổ sung ảnh giao diện và một lần chạy Gemini online nếu có API key trước khi nộp.
- **Hạn chế:** Hiện tại mô hình chỉ phân tích đơn lẻ từng khách hàng; chưa có tác vụ nền (Celery/Cron) phân tích hàng loạt.
- **Hướng phát triển:** Tích hợp sinh email phản hồi tự động theo ngữ cảnh, dự báo rời bỏ nâng cao bằng học máy (Scikit-learn), kết nối đa kênh (Zalo OA / Webhook).

---

## Phụ lục
- Danh sách câu lệnh triển khai dự án (Windows PowerShell).
- Mẫu Prompt AI phân tích khách hàng.
- Tài khoản demo: tự tạo bằng `python manage.py createsuperuser`; không ghi mật khẩu thật vào báo cáo công khai.
