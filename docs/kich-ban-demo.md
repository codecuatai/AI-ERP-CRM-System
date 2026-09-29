# Kịch bản video demo AI CRM với Wagtail

**Thời lượng mục tiêu:** 8–10 phút  
**Phạm vi:** CRM cơ bản cho doanh nghiệp B2B cung cấp giải pháp chuyển đổi số. Kịch bản đối chiếu đầy đủ 5 yêu cầu của đề bài.  
**Nhân vật demo:** nhân viên kinh doanh và khách hàng giả định **Công ty Minh Phát**, quan tâm đến giải pháp quản lý kho/POS.

> Dùng dữ liệu giả lập. Không để lộ `.env`, API key, mật khẩu hoặc thông tin khách hàng thật trên video.

## Chuẩn bị trước khi quay

1. Mở PowerShell tại thư mục chứa `manage.py` và dùng Python 3.11 hoặc 3.12.
2. Cài dependencies nếu máy chưa có:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Khởi tạo database, trang CMS, nhóm quyền và dữ liệu demo. Tạo superuser nếu máy chưa có tài khoản:

   ```powershell
   .\.venv\Scripts\python.exe manage.py migrate
   .\.venv\Scripts\python.exe manage.py setup_cms_homepage
   .\.venv\Scripts\python.exe manage.py setup_crm_groups
   .\.venv\Scripts\python.exe manage.py seed_crm_data
   # Chỉ chạy nếu database chưa có tài khoản đăng nhập
   .\.venv\Scripts\python.exe manage.py createsuperuser
   .\.venv\Scripts\python.exe manage.py runserver
   ```

   `seed_crm_data` tạo khách hàng và tương tác giả để các danh sách CRM có dữ liệu. Lệnh không tạo tài khoản đăng nhập.

4. Chọn cách trình diễn AI:
   - **Gemini:** cấu hình `GEMINI_API_KEY` trong `.env`, khởi động lại server và xác nhận phân tích trả về nguồn `gemini`.
   - **Fallback:** để trống `GEMINI_API_KEY`; hệ thống vẫn phân tích bằng rules và cần hiện rõ nguồn `rules`.

   Không nhập key thật vào slide, video hoặc README. Không khẳng định kết quả đến từ Gemini nếu giao diện đang ghi `rules`.

5. Đăng nhập bằng superuser hoặc tài khoản staff đã được cấp quyền CRM. Nếu tạo tài khoản mới, thêm tài khoản vào nhóm CRM phù hợp theo hướng dẫn trong README.
6. Mở sẵn các trang để chuyển nhanh khi quay:
   - Landing page: `http://127.0.0.1:8000/`
   - Form tư vấn: `http://127.0.0.1:8000/crm/dang-ky-tu-van/`
   - CRM tổng quan: `http://127.0.0.1:8000/crm/`
   - Hộp thư yêu cầu: `http://127.0.0.1:8000/crm/yeu-cau/`
   - Wagtail Admin: `http://127.0.0.1:8000/admin/`
7. Chạy các lệnh kiểm tra trước buổi quay; chỉ đưa kết quả thực tế vào video:

   ```powershell
   .\.venv\Scripts\python.exe manage.py check
   .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
   .\.venv\Scripts\python.exe manage.py test
   ```

## Kịch bản chi tiết

### 0:00–0:35 — Giới thiệu đề tài

**Trên màn hình:** Slide tiêu đề, sau đó chuyển sang trang công khai.

**Lời dẫn:**

> “Đây là hệ thống CRM cơ bản tích hợp AI, xây dựng trên Wagtail và Django. Hệ thống dành cho doanh nghiệp tư vấn giải pháp chuyển đổi số B2B. Nhân viên có thể tiếp nhận yêu cầu, quản lý hồ sơ khách hàng, xem gợi ý AI và theo dõi các việc chăm sóc. Trong video, em sẽ trình bày luồng dữ liệu từ giao diện quản trị đến AI và trở lại giao diện CRM.”

**Checklist:** Nêu rõ nhánh sản phẩm là CRM, một lựa chọn được đề bài cho phép.

### 0:35–1:25 — Môi trường Python và Wagtail

**Thao tác:** Hiện terminal trong vài giây với phiên bản Python, `requirements.txt` và lệnh chạy server. Không cần quay thời gian chờ cài package.

```powershell
python --version
python manage.py runserver
```

**Lời dẫn:**

> “Môi trường dùng Python 3.11/3.12. Wagtail và thư viện AI được khai báo trong `requirements.txt`. Dự án dùng SQLite cho môi trường demo; các bước tạo môi trường, migrate database, khởi tạo CMS và nạp dữ liệu giả được hướng dẫn trong README.”

**Trên màn hình:** Mở trang chủ tại `127.0.0.1:8000`.

> “Đây là landing page được quản lý bằng Wagtail. Khách hàng có thể xem giải pháp và gửi yêu cầu tư vấn ngay trên giao diện công khai.”

**Checklist 1:** Python, dependencies, dự án Wagtail đã khởi chạy.

### 1:25–2:40 — Model CRM được quản trị trong Wagtail

**Thao tác:** Vào Wagtail Admin → **Snippets** → mở lần lượt **Khách hàng**, **Yêu cầu tư vấn**, **Lịch sử tương tác**. Chọn Công ty Minh Phát hoặc bản ghi giả lập tương đương.

**Lời dẫn:**

> “Các model CRM được định nghĩa trong `crm/models.py`. Ví dụ, `Customer` lưu thông tin doanh nghiệp và trạng thái khách hàng; `LeadRequest` lưu nhu cầu tư vấn; `Interaction` lưu lịch sử trao đổi; `AIAnalysis` lưu các lần phân tích; `CareTask` lưu việc cần theo dõi. Các loại dữ liệu này được đăng ký thành Snippets để nhân viên quản trị trong Wagtail.”

**Thao tác:** Mở hồ sơ khách hàng và chỉ vào công ty, email demo, giải pháp quan tâm hoặc ghi chú. Tránh mở rộng nhiều bản ghi không cần thiết.

> “Công ty Minh Phát đang tìm hiểu giải pháp quản lý kho và POS. Thông tin và lịch sử này là đầu vào cho bước phân tích tiếp theo.”

**Checklist 2:** Cho thấy model tùy chỉnh và khả năng quản trị dữ liệu qua Wagtail.

### 2:40–3:40 — Gửi yêu cầu từ frontend

**Thao tác:** Mở form trên landing page hoặc `/crm/dang-ky-tu-van/`. Điền dữ liệu giả lập mới, ví dụ:

- Họ tên: `Nguyễn Minh Anh`
- Email: `minhanh-demo@example.test`
- Công ty: `Công ty Minh Phát`
- Nhóm giải pháp: quản lý kho hoặc POS
- Nhu cầu: `Đang tìm giải pháp theo dõi tồn kho và đồng bộ dữ liệu bán hàng.`
- Bật đồng ý tiếp nhận; chọn đồng ý phân tích AI nếu muốn trình diễn phân tích lead này.

**Lời dẫn:**

> “Khách gửi nhu cầu ở giao diện công khai. Đồng ý tiếp nhận và đồng ý phân tích AI là hai lựa chọn riêng. Khi gửi thành công, hệ thống tạo hoặc liên kết hồ sơ khách hàng, lưu yêu cầu tư vấn và ghi lại tương tác ban đầu.”

**Thao tác:** Gửi form; hiện trang xác nhận. Sau đó mở hộp thư yêu cầu trong CRM để cho thấy lead đã được lưu.

**Checklist 4:** Người dùng tương tác qua giao diện frontend; dữ liệu được chuyển vào CRM.

### 3:40–5:10 — Phân tích khách hàng bằng AI

**Thao tác:** Mở hồ sơ khách hàng vừa gửi hoặc khách hàng demo có quyền phân tích; bấm **Phân tích ngay**.

**Lời dẫn khi dùng Gemini:**

> “Nhân viên chủ động yêu cầu phân tích. Khi đã cấu hình Gemini, dịch vụ gửi nội dung được phép sử dụng đến Google Gemini, kiểm tra cấu trúc kết quả rồi hiển thị phân khúc, điểm, nhận định và đề xuất.”

**Lời dẫn khi dùng fallback:**

> “Ở máy demo này chưa cấu hình Gemini, nên hệ thống chạy rules fallback. Gợi ý vẫn hoạt động và giao diện ghi rõ nguồn là `rules`; hệ thống không giả vờ rằng đây là kết quả Gemini.”

**Thao tác:** Chỉ vào phân khúc, điểm, nhận định, đề xuất và nhãn nguồn hiển thị. Nêu một kết quả thực tế đang có trên màn hình, không đọc kết quả đã chuẩn bị nếu khác.

> “AI đóng vai trò hỗ trợ. Nhân viên xem xét kết quả trước khi quyết định hành động. Với lead công khai, nội dung chỉ được phân tích khi khách đã đồng ý AI.”

**Checklist 3:** Trình bày API AI, kết quả thông minh, nguồn kết quả và fallback.

### 5:10–6:20 — Biến đề xuất thành việc chăm sóc

**Thao tác:** Từ hồ sơ hoặc đề xuất, chọn tạo việc chăm sóc; nhập tiêu đề như `Gọi trao đổi nhu cầu quản lý kho`, chọn hạn và mức ưu tiên rồi lưu.

**Lời dẫn:**

> “Từ đề xuất, nhân viên có thể tạo việc chăm sóc có người phụ trách, ngày đến hạn, mức ưu tiên và trạng thái. Nhân viên kiểm tra thông tin trước khi lưu; AI không tự thay đổi dữ liệu quan trọng.”

**Thao tác:** Mở mục **Việc chăm sóc** hoặc dashboard để cho thấy công việc vừa tạo xuất hiện trong danh sách. Nếu còn thời gian, đổi trạng thái sang đang làm rồi quay lại hồ sơ.

> “Như vậy kết quả phân tích không dừng ở một đoạn văn; nó có thể trở thành hành động theo dõi được trong CRM.”

**Checklist 4:** Tương tác AI trên giao diện và theo dõi được hành động phát sinh.

### 6:20–7:15 — Wagtail CMS và nội dung website

**Thao tác:** Trong Wagtail Admin, mở **Pages** → chọn **Trang chủ doanh nghiệp** → Edit hoặc Preview. Có thể mở Snippets nếu cần nhắc lại việc quản trị dữ liệu.

**Lời dẫn:**

> “Wagtail còn quản lý nội dung landing page như tiêu đề, giới thiệu giải pháp và quy trình tư vấn. Đây là lớp CMS hỗ trợ nội dung website, còn model và các luồng khách hàng thuộc phần CRM.”

Không cần mở Images hoặc Documents nếu thư viện trống; chúng không phải dữ liệu bắt buộc của luồng CRM.

### 7:15–8:20 — Kiểm thử và tài liệu triển khai

**Thao tác:** Mở README tại phần Bắt đầu nhanh, Cấu hình Gemini và Kiểm thử thủ công. Sau đó hiện terminal với kết quả kiểm tra đã chạy.

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

**Lời dẫn:**

> “README hướng dẫn cài Python dependencies, cấu hình môi trường, migrate database, khởi tạo trang CMS và nhóm quyền, nạp dữ liệu demo, rồi chạy server. Luồng test end-to-end kiểm tra việc gửi yêu cầu, phân tích fallback và tạo việc chăm sóc. Đây là kết quả kiểm thử của phiên bản hiện tại.”

Đọc đúng kết quả trong terminal. Nếu test trình duyệt tùy chọn bị skip, giải thích đây là test cần cài thêm Chromium; không trình bày nó như test đã chạy thành công.

**Checklist 5:** Cho thấy kiểm thử luồng và bộ tài liệu hướng dẫn triển khai.

### 8:20–8:45 — Kết luận

**Trên màn hình:** Quay về hồ sơ khách hàng hoặc dashboard có công việc vừa tạo.

**Lời dẫn:**

> “Tóm lại, hệ thống dùng Wagtail để quản trị nội dung và dữ liệu CRM, cung cấp frontend cho khách và nhân viên, tích hợp Gemini với rules fallback, rồi chuyển gợi ý thành việc chăm sóc do nhân viên xác nhận. Đây là CRM cơ bản theo phạm vi đề bài, không phải ERP đầy đủ.”

## Bảng đối chiếu 5 checklist

| Mục | Đoạn video | Bằng chứng chính |
|---|---|---|
| 1. Môi trường Python và Wagtail | 0:35–1:25 | `requirements.txt`, cấu hình Django/Wagtail, lệnh chạy ứng dụng và README |
| 2. Model tùy chỉnh | 1:25–2:40 | `crm/models.py`, Snippets trong Wagtail Admin |
| 3. Tích hợp AI | 3:40–5:10 | Gemini/rules, kết quả phân tích và nhãn nguồn |
| 4. Frontend tương tác AI | 2:40–6:20 | Form công khai, hồ sơ khách hàng, phân tích và việc chăm sóc |
| 5. Kiểm thử và tài liệu | 7:15–8:20 | Test end-to-end, kết quả lệnh kiểm tra, README triển khai |

## Nếu gặp sự cố khi quay

- **Không có API key hoặc Gemini lỗi:** dùng rules fallback, xác nhận giao diện ghi nguồn `rules`, tiếp tục demo.
- **Form lead đã dùng email:** tạo email demo mới thuộc miền `.test` hoặc dùng hồ sơ giả lập khác.
- **Snippets không có dữ liệu:** chạy `seed_crm_data` rồi tải lại trang; không dùng dữ liệu thật.
- **Trang con Pages báo 0 trang:** mở trang gốc **Trang chủ doanh nghiệp** để sửa/xem trước; trang này không cần trang con để demo CMS.
- **Email follow-up:** local mặc định in email ra terminal; không cần gửi email thật để hoàn thành luồng CRM chính.
- **Test trình duyệt bị bỏ qua:** test Django end-to-end vẫn kiểm tra luồng ứng dụng; chỉ trình bày browser E2E là đã chạy nếu đã cài requirements và Chromium theo README.
