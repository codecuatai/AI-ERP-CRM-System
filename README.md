# AI CRM — CRM cho doanh nghiệp cung cấp giải pháp chuyển đổi số

Ứng dụng CRM cho phép doanh nghiệp cung cấp giải pháp chuyển đổi số quản lý khách hàng B2B, lịch sử tư vấn/triển khai và phân tích tiềm năng bằng Gemini AI. Nếu không có API key, hệ thống tự dùng bộ quy tắc cục bộ.

## Dự án là gì?

**AI CRM** là hệ thống quản lý quan hệ khách hàng dành cho một doanh nghiệp cung cấp các giải pháp chuyển đổi số. Doanh nghiệp có thể tư vấn, bán và triển khai các giải pháp như phần mềm quản lý kho, POS, CRM, hạ tầng máy chủ, sao lưu dữ liệu hoặc tích hợp hệ thống cho các khách hàng doanh nghiệp khác.

Trong bối cảnh này, khách hàng trong database là các doanh nghiệp đang tìm hiểu, mua hoặc sử dụng giải pháp chuyển đổi số. Nhân viên kinh doanh cần theo dõi nhu cầu, lịch sử trao đổi, giá trị đã chi tiêu và dấu hiệu cần chăm sóc tiếp. AI hỗ trợ trả lời câu hỏi: **khách hàng nào cần được ưu tiên và bước chăm sóc tiếp theo nên là gì?**

Khách chủ động gửi nhu cầu qua form công khai; hệ thống lưu yêu cầu và tạo hồ sơ khách hàng nếu email chưa có. Nhân viên làm việc theo các khu vực riêng: **Tổng quan** để xem việc quá hạn/hôm nay/sắp tới, **Yêu cầu tư vấn** để tiếp nhận và cập nhật trạng thái, **Khách hàng** để tìm hồ sơ và xem lịch sử, **Việc chăm sóc** để giao và theo dõi hành động. Từ một lead, nhân viên có thể chủ động gửi email kèm link bảo mật để khách bổ sung thông tin; phản hồi được lưu vào CRM và chỉ được đưa vào phân tích AI nếu khách đồng ý riêng. Đề xuất AI có thể được chuyển thành việc chăm sóc nháp, nhưng chỉ được lưu sau khi nhân viên kiểm tra và xác nhận. Wagtail CMS dùng để quản lý dữ liệu chi tiết. Phần phân tích gọi Google Gemini khi có API key; nếu API không có hoặc gặp lỗi, hệ thống tự chuyển sang quy tắc cục bộ để ứng dụng vẫn hoạt động.

Đây là một đồ án tập trung vào luồng CRM cốt lõi, không phải hệ thống ERP hay hệ thống quản lý toàn bộ quy trình triển khai chuyển đổi số. Phạm vi chính là:

```text
Khách gửi form → LeadRequest → Nhân viên gửi email hỏi thêm
                                      ↓
                    Khách trả lời link bảo mật → CRM lưu phản hồi
                                      ↓
                       AI phân tích nếu khách đã consent riêng
                                      ↓
                   Nhân viên xác nhận → Việc chăm sóc có hạn xử lý
```

### Mục tiêu của dự án

- Tập trung thông tin khách hàng trong một hệ thống duy nhất.
- Theo dõi lịch sử email, điện thoại và gặp mặt.
- Tự động phân khúc và chấm điểm khách hàng từ 0 đến 100.
- Đưa ra nhận định và đề xuất tiếp theo cho nhân viên kinh doanh.
- Có chế độ fallback bằng rules khi thiếu API key, mất kết nối hoặc Gemini trả lỗi.

## Mục lục

- [Dự án là gì?](#dự-án-là-gì)
- [Tính năng chính](#tính-năng-chính)
- [Mô hình dữ liệu](#mô-hình-dữ-liệu)
- [Bắt đầu nhanh](#bắt-đầu-nhanh)
- [Truy cập ứng dụng](#truy-cập-ứng-dụng)
- [Cấu hình Gemini tùy chọn](#cấu-hình-gemini-tùy-chọn)
- [Gửi email hỏi thêm thông tin](#gửi-email-hỏi-thêm-thông-tin)
- [Demo trong 5 phút](#demo-trong-5-phút)
- [Kịch bản video demo chi tiết](docs/kich-ban-demo.md)
- [Dữ liệu mẫu](#dữ-liệu-mẫu)
- [Cách phân tích AI hoạt động](#cách-phân-tích-ai-hoạt-động)
- [Cấu trúc chính](#cấu-trúc-chính)
- [Frontend và build giao diện](#frontend-và-build-giao-diện)
- [Git workflow và CI](#git-workflow-và-ci)
- [Xử lý lỗi thường gặp](#xử-lý-lỗi-thường-gặp)
- [Kiểm thử thủ công](#kiểm-thử-thủ-công)
- [Giới hạn và hướng phát triển](#giới-hạn-và-hướng-phát-triển)
- [Roadmap tính năng chi tiết](docs/lo-trinh-tinh-nang.md)
- [Hướng dẫn cho AI agent](AGENTS.md)
- [Checklist trước khi nộp](#checklist-trước-khi-nộp)

## Tính năng chính

- **Quản lý khách hàng:** họ tên, email, số điện thoại, công ty, nguồn khách hàng, ghi chú, tổng chi tiêu và trạng thái hoạt động.
- **Landing page công khai:** giới thiệu giải pháp và form tư vấn; thu nhóm giải pháp, nhu cầu, email bắt buộc, điện thoại/công ty tùy chọn.
- **Consent tách mục đích:** đồng ý tiếp nhận/phản hồi là bắt buộc; đồng ý AI là tùy chọn, được lưu riêng cùng thời điểm/phiên bản. Lead không đồng ý AI vẫn được tiếp nhận nhưng không thể chạy phân tích.
- **Thông báo quyền riêng tư:** có trang riêng nêu dữ liệu, mục đích, AI/Gemini, thời hạn demo và cách liên hệ; cấu hình đơn vị thật trước khi thu dữ liệu thật.
- **Quản lý tương tác:** ghi lại email, điện thoại, gặp mặt hoặc hình thức khác; mỗi tương tác thuộc về một khách hàng.
- **Email hỏi thêm thông tin:** nhân viên chủ động gửi form follow-up từ lead; khách trả lời bằng link bảo mật, hết hạn và chỉ dùng để gửi một lần.
- **Lưu phản hồi theo lead:** CRM lưu câu trả lời, trạng thái email và hiển thị phản hồi trên trang yêu cầu/hồ sơ khách hàng.
- **Consent AI riêng cho phản hồi:** câu trả lời bổ sung chỉ được AI phân tích nếu khách đồng ý ngay trên form đó.
- **Dashboard:** hiển thị tổng khách hàng đang hoạt động, số khách hàng VIP, số khách hàng chưa phân tích và tổng chi tiêu.
- **Việc chăm sóc khách hàng:** tạo từ hồ sơ hoặc đề xuất AI; gắn khách hàng, người phụ trách, loại việc, hạn, ưu tiên và trạng thái; có danh sách tìm/lọc riêng.
- **Giao dịch doanh thu tối giản:** ghi nhận giao dịch đã chốt/hủy gắn với khách hàng để demo báo cáo theo tháng; không thay thế nghiệp vụ kế toán hay quản lý đơn hàng đầy đủ.
- **Theo dõi hạn xử lý:** dashboard chia việc đang mở thành quá hạn, đến hạn hôm nay và sắp tới; việc hoàn tất được loại khỏi các hàng đợi này.
- **Tìm kiếm và lọc:** tìm theo tên, email, công ty; lọc theo phân khúc AI.
- **Hồ sơ khách hàng:** xem thông tin liên hệ, tổng chi tiêu, timeline trao đổi, kết quả AI mới nhất và lịch sử các lần phân tích trước.
- **Phân tích AI:** trả về phân khúc, điểm tiềm năng, nhận định, đề xuất hành động và nguồn phân tích (`gemini` hoặc `rules`).
- **Quản trị bằng Wagtail:** quản lý dữ liệu tại **Snippets → Khách hàng**, **Yêu cầu tư vấn**, **Lịch sử tương tác** và **Kết quả phân tích AI**.
- **Wagtail CMS cho landing page:** chỉnh sửa nội dung trang chủ, danh mục giải pháp và quy trình tư vấn trong Pages; các Snippet có tìm kiếm, bộ lọc và trang xem chi tiết.
- **Hàng đợi ưu tiên:** sắp xếp khách cần chăm sóc theo điểm AI, nguy cơ rời bỏ, việc quá hạn và thời gian chưa tương tác; mỗi thứ tự có lý do giải thích.
- **Trợ lý soạn email:** tạo bản nháp theo mục tiêu/giọng văn/độ dài bằng Gemini hoặc mẫu cục bộ; không tự gửi. Nhân viên chỉ ghi vào lịch sử sau khi xác nhận đã gửi.
- **Báo cáo và CSV:** báo cáo phân khúc, lead, việc chăm sóc; xuất danh sách CSV có thể giữ bộ lọc tìm kiếm hiện tại.
- **Phân quyền CRM:** hai nhóm `CRM - Nhân viên` và `CRM - Quản lý`; lệnh thiết lập cấp quyền frontend, quyền snippet phù hợp và quyền truy cập Wagtail Admin.
- **Responsive UI:** giao diện Django Templates + Tailwind CSS, có sidebar desktop và menu mobile.

Các phân khúc được hỗ trợ: **Chưa phân loại**, **VIP**, **Tiềm năng**, **Ngủ đông** và **Nguy cơ rời bỏ**.

## Mô hình dữ liệu

| Model | Vai trò | Dữ liệu chính |
|---|---|---|
| `Customer` | Hồ sơ khách hàng | Thông tin liên hệ, công ty, nguồn, ghi chú, tổng chi tiêu, trạng thái, phân khúc và điểm AI mới nhất |
| `LandingPage` | Trang Wagtail CMS | Nội dung landing page, danh mục giải pháp và các bước tư vấn; không thay thế model dữ liệu CRM |
| `Interaction` | Lịch sử trao đổi | Khách hàng, hình thức, chủ đề, nội dung và thời điểm; quan hệ nhiều-một với `Customer` |
| `LeadRequest` | Yêu cầu gửi từ form công khai | Nhóm giải pháp, nhu cầu, trạng thái, consent tiếp nhận và consent AI riêng kèm dấu thời gian/phiên bản |
| `LeadFollowUp` | Email hỏi thêm do nhân viên chủ động gửi | Câu hỏi, nhân viên gửi, hash token, hạn trả lời, trạng thái gửi/phản hồi/thu hồi |
| `LeadFollowUpResponse` | Câu trả lời từ form follow-up | Khó khăn, kết quả mong muốn, thời điểm triển khai, thời gian liên hệ và consent AI riêng |
| `AIAnalysis` | Lịch sử phân tích | Khách hàng, phân khúc, điểm, nhận định, đề xuất, nguồn phân tích và thời điểm; lưu lại mỗi lần bấm phân tích |
| `CareTask` | Việc chăm sóc khách hàng | Khách hàng, nội dung, loại việc, người phụ trách, hạn, ưu tiên, trạng thái và thời điểm hoàn tất |
| `SalesRecord` | Giao dịch doanh thu tối giản | Mã giao dịch demo, khách hàng, giá trị, ngày chốt và trạng thái đã chốt/đã hủy; không phải phân hệ kế toán |

`Customer.ai_segment` và `Customer.ai_score` lưu kết quả mới nhất để Dashboard lọc/hiển thị nhanh. Các bản ghi `AIAnalysis` giữ lịch sử cũ để có thể xem lại.

## Bắt đầu nhanh

### Yêu cầu

- Python 3.11 hoặc 3.12
- Windows 10/11, macOS hoặc Linux
- Trình duyệt hiện đại; giao diện đã được đóng gói trong dự án, không cần CDN

Thư viện Python chính:

| Gói | Vai trò |
|---|---|
| `wagtail>=7.0,<9.0` | CMS và giao diện quản trị |
| `google-genai>=1.0.0` | Gọi Google Gemini khi có API key |
| `python-dotenv>=1.0.0` | Đọc cấu hình từ `.env` |
| `requirements-postgres.txt` | Driver PostgreSQL tùy chọn cho demo Superset |
| SQLite | Cơ sở dữ liệu mặc định, không cần cài thêm |

Mở Terminal/PowerShell tại thư mục chứa `manage.py` rồi chạy các lệnh sau.

**Windows PowerShell:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py setup_cms_homepage
python manage.py setup_crm_groups
# Chỉ chạy lệnh này nếu muốn có dữ liệu giả lập để demo:
# python manage.py seed_crm_data
python manage.py createsuperuser
python manage.py runserver
```

**macOS / Linux:** chạy:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py setup_cms_homepage
python manage.py setup_crm_groups
# Chỉ chạy lệnh này nếu muốn có dữ liệu giả lập để demo:
# python manage.py seed_crm_data
python manage.py createsuperuser
python manage.py runserver
```

Nếu PowerShell chặn kích hoạt môi trường ảo, chạy một lần:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Hoặc bỏ qua bước kích hoạt và dùng `.venv\Scripts\python.exe` thay cho `python`.

Migration ban đầu đã được lưu trong dự án nên cài mới chỉ cần chạy `migrate`. Chỉ chạy `makemigrations` khi thay đổi model. Lệnh `seed_crm_data` tạo dữ liệu mẫu nhưng không tạo tài khoản đăng nhập; tài khoản đó được tạo ở bước `createsuperuser`.

### Nạp dữ liệu khách hàng thật

Ứng dụng không thể tự tạo dữ liệu khách hàng thật nếu chưa có nguồn dữ liệu. Để bắt đầu với hồ sơ thật, có thể tiếp nhận yêu cầu từ form công khai hoặc nhập CSV do doanh nghiệp xuất từ nguồn đang sử dụng. Không chạy `seed_crm_data` trong database muốn dùng dữ liệu thật; lệnh đó chỉ tạo hồ sơ giả lập để demo.

CSV cần có cột `full_name,email`; các cột còn lại là tùy chọn: `phone,company,source,notes,total_spent,is_active`. Ví dụ:

```csv
full_name,email,phone,company,source,notes,total_spent,is_active
Nguyễn Văn A,contact@congty.vn,0900000000,Công ty ABC,Giới thiệu,Quan tâm phần mềm CRM,0,true
```

Kiểm tra file trước khi nhập, không thay đổi database:

```powershell
python manage.py import_crm_customers .\khach-hang.csv --dry-run
```

Nhập hồ sơ mới; email đã có trong database mặc định được bỏ qua để bảo vệ dữ liệu đang lưu:

```powershell
python manage.py import_crm_customers .\khach-hang.csv
```

Chỉ thêm `--update` khi muốn cập nhật hồ sơ trùng email theo các cột trong file. Bản ghi trong CSV phải dùng UTF-8; email được chuẩn hóa chữ thường. Lệnh này chỉ nhập hồ sơ khách hàng, chưa nhập lịch sử tương tác/đơn hàng từ hệ thống khác.

## Truy cập ứng dụng

Sau khi chạy `runserver`, mở một trong các địa chỉ dưới đây. Dashboard và hồ sơ yêu cầu đăng nhập; nếu chưa đăng nhập, Django chuyển bạn đến trang đăng nhập Wagtail:

| Địa chỉ | Chức năng |
|---|---|
| [CRM Tổng quan](http://127.0.0.1:8000/crm/) | Số liệu chính, yêu cầu gần đây và hồ sơ chờ phân tích |
| [Danh sách khách hàng](http://127.0.0.1:8000/crm/customers/) | Tìm kiếm, lọc, phân trang và mở hồ sơ khách hàng |
| [Khách hàng cần ưu tiên](http://127.0.0.1:8000/crm/uu-tien/) | Hàng đợi chăm sóc có giải thích lý do ưu tiên |
| [Hộp thư yêu cầu tư vấn](http://127.0.0.1:8000/crm/yeu-cau/) | Tìm yêu cầu, lọc trạng thái, cập nhật tiến độ và mở hồ sơ |
| [Việc chăm sóc](http://127.0.0.1:8000/crm/viec/) | Tạo, tìm, lọc, cập nhật và hoàn tất việc chăm sóc |
| [Báo cáo CRM](http://127.0.0.1:8000/crm/bao-cao/) | Tổng hợp khách hàng, lead và việc chăm sóc |
| [Landing page](http://127.0.0.1:8000/) | Giới thiệu giải pháp và form công khai ở cuối trang |
| [Form yêu cầu tư vấn riêng](http://127.0.0.1:8000/crm/dang-ky-tu-van/) | Form công khai độc lập, dùng chung luồng lưu dữ liệu |
| [Thông báo quyền riêng tư](http://127.0.0.1:8000/chinh-sach-du-lieu/) | Dữ liệu thu thập, mục đích, AI, lưu trữ và cách liên hệ |
| [Wagtail Admin](http://127.0.0.1:8000/admin/) | Quản lý khách hàng, yêu cầu tư vấn và tương tác |

Để chỉnh trang chủ, đăng nhập Wagtail Admin → **Pages** → chọn **Trang chủ doanh nghiệp** → Edit. Nếu thêm tài khoản nhân viên, thêm tài khoản vào một trong hai nhóm CRM bằng **Users**. Tài khoản cần `is_staff` để mở Wagtail Admin; lệnh `setup_crm_groups` không tự cấp quyền cho tài khoản cụ thể.

## Cấu hình Gemini tùy chọn

Lệnh `Copy-Item .env.example .env` đã tạo file `.env`. Mở file này và điền:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

Có thể lấy API key tại [Google AI Studio](https://aistudio.google.com/). Sau khi sửa `.env`, khởi động lại server. Không commit `.env` hoặc dữ liệu khách hàng thật lên Git.

Không có `GEMINI_API_KEY` cũng không sao: phân tích vẫn chạy bằng rules fallback và kết quả vẫn được lưu, nhưng đây là phân tích quy tắc cục bộ chứ không phải Gemini. Trên hồ sơ khách hàng, nút **Phân tích ngay** gửi thông tin CRM hiện có đến Gemini khi key hợp lệ; nếu phân tích bằng fallback, giao diện sẽ ghi rõ nguồn. Chỉ nhập dữ liệu khách hàng khi doanh nghiệp có quyền sử dụng và đã thông báo/thu consent phù hợp. Với lead gửi form công khai, nội dung chỉ được gửi phân tích nếu khách đã đồng ý AI riêng.

## Gửi email hỏi thêm thông tin

Mặc định môi trường phát triển dùng `django.core.mail.backends.console.EmailBackend`, nên không gửi email thật. Khi nhân viên bấm **Gửi form hỏi thêm** tại `/crm/yeu-cau/`, email được in trong terminal chạy Django. Mở URL trong email để thử form trả lời.

Để gửi email thật, cấu hình trong `.env`:

```dotenv
PUBLIC_SITE_URL=https://crm.example.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-smtp-user
EMAIL_HOST_PASSWORD=your-smtp-password
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
DEFAULT_FROM_EMAIL=DigiFlow <no-reply@example.com>
LEAD_FOLLOW_UP_LINK_TTL_DAYS=7
```

Thay giá trị mẫu bằng domain HTTPS và thông tin SMTP của đơn vị; không commit thông tin xác thực. Nhân viên phải chủ động bấm gửi—khách nộp form landing page không tự nhận email follow-up. Link chỉ nhận một phản hồi, hết hạn theo `LEAD_FOLLOW_UP_LINK_TTL_DAYS`, và có thể thu hồi trước khi khách trả lời. `PUBLIC_SITE_URL` phải là domain do đơn vị vận hành kiểm soát.

## Cấu hình production tối thiểu

`config.settings.dev` chỉ dành cho local (`DEBUG=True`, SQLite). Khi triển khai, đặt biến môi trường `DJANGO_SETTINGS_MODULE=config.settings.prod` ở nền tảng hosting và cung cấp:

```dotenv
DJANGO_SECRET_KEY=<chuỗi ngẫu nhiên riêng, ít nhất 50 ký tự>
DJANGO_ALLOWED_HOSTS=crm.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://crm.example.com
PUBLIC_SITE_URL=https://crm.example.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=<tài khoản SMTP>
EMAIL_HOST_PASSWORD=<mật khẩu SMTP>
EMAIL_USE_TLS=true
```

Profile production từ chối secret yếu/thiếu, wildcard host, URL public không HTTPS, host/CSRF origin không khớp và backend email console; đồng thời bật cookie bảo mật, HTTPS redirect và HSTS. Cần cấu hình HTTPS tại proxy/hosting, đặt đúng host/origin và dùng database có lưu trữ bền vững. Nếu proxy kết thúc TLS, chỉ đặt `DJANGO_BEHIND_TLS_PROXY=true` khi proxy tin cậy luôn ghi đè `X-Forwarded-Proto` và app không thể truy cập trực tiếp từ client ngoài. Profile mặc định vẫn dùng SQLite, nhưng hỗ trợ chuyển sang PostgreSQL qua `DJANGO_DATABASE_URL`; production cần database/backup bền vững phù hợp tải thực tế. Không dùng file `.env` trong repo để chứa secret production.

## Demo trong 5 phút

1. Mở [Landing page](http://127.0.0.1:8000/) và gửi yêu cầu ở khu vực liên hệ cuối trang.
2. Đăng nhập bằng tài khoản nhân viên tại khu vực CRM hoặc Wagtail Admin.
3. Mở [Hộp thư yêu cầu tư vấn](http://127.0.0.1:8000/crm/yeu-cau/) để xem yêu cầu, nhóm giải pháp khách quan tâm và cập nhật trạng thái.
4. Mở hồ sơ khách hàng từ yêu cầu hoặc tìm trong [Danh sách khách hàng](http://127.0.0.1:8000/crm/customers/); lịch sử trao đổi và phân tích nằm trong hồ sơ riêng.
5. Trên lead, chọn **Gửi form hỏi thêm**, chỉnh nội dung email nếu cần rồi gửi. Khi phát triển local, email được in ở terminal; mở link để thử form phản hồi.
6. Phản hồi xuất hiện trong lịch sử yêu cầu và timeline khách hàng. Khách có thể chọn consent AI riêng cho câu trả lời follow-up.
7. Nếu khách đã đồng ý phân tích AI, mở hồ sơ và chọn **Phân tích ngay** để xem phân khúc, điểm tiềm năng, nhận định và đề xuất; nếu chưa đồng ý, dữ liệu vẫn được tiếp nhận nhưng không gửi đi phân tích.
8. Trong hồ sơ khách hàng, tạo việc chăm sóc thủ công hoặc chọn **Tạo việc từ đề xuất này**. Kiểm tra tiêu đề/hạn/ưu tiên rồi mới lưu; việc sẽ xuất hiện ở dashboard theo ngày đến hạn.
9. Mở **Việc chăm sóc** để tìm, lọc, sửa trạng thái hoặc đánh dấu hoàn tất.
10. Dùng **Soạn email** ở hồ sơ khách hàng để tạo bản nháp; chỉnh nội dung, tự gửi bên ngoài nếu cần, rồi chỉ xác nhận trong CRM sau khi đã gửi.
11. Mở **Khách hàng cần ưu tiên** và **Báo cáo** để xem các hàng đợi/chỉ số; danh sách có thể tải xuống dưới dạng CSV.

Để kiểm tra fallback, để trống `GEMINI_API_KEY`, khởi động lại server và phân tích lại.

## Dữ liệu mẫu

Lệnh `python manage.py seed_crm_data` tạo dữ liệu phục vụ trình diễn. Ngoài 6 hồ sơ mẫu ban đầu, lệnh bổ sung 24 doanh nghiệp giả lập với email thuộc miền `.test`:

- Tổng 30 hồ sơ trong database mới; 24 hồ sơ thêm có tên/công ty và ghi chú ghi rõ là dữ liệu giả lập.
- 58 lịch sử tương tác trong database mới, xen kẽ email, điện thoại và gặp mặt.
- 24 yêu cầu tư vấn mẫu với trạng thái mới/đã liên hệ/đã xử lý và có/không đồng ý AI để minh họa quyền riêng tư.
- Kết quả phân tích mẫu cho hồ sơ được giả lập đã đồng ý AI; không gọi Gemini khi seed.
- 19 việc chăm sóc với trạng thái hoàn tất/đang làm/cần làm, hạn quá khứ/hôm nay/tương lai.

Lệnh seed dùng email, nội dung yêu cầu, chủ đề tương tác và tiêu đề việc để tránh tạo trùng khi chạy lại; không ghi đè hồ sơ đã tồn tại. Các thông tin liên hệ mới đều là dữ liệu demo, không dùng dữ liệu khách thật. Lệnh này chỉ tạo dữ liệu, không tạo tài khoản đăng nhập. Chạy lại lệnh an toàn nếu muốn bổ sung các bản ghi demo còn thiếu.

Lệnh seed cũng tạo 12 giao dịch doanh thu giả lập theo các tháng gần nhất, dùng mã `DEMO-REV-*`; một giao dịch đã hủy để minh họa lọc trạng thái. Đây là dữ liệu demo, không phải doanh thu thật.

## Kết nối Apache Superset

Superset chạy riêng trong Docker Compose, đọc PostgreSQL qua tài khoản `superset_ro`. Cấu hình này dành cho demo local với dữ liệu giả lập; không mở cổng dashboard/database ra mạng công khai và không dùng database thật trong lần chạy seed.

### Khởi chạy trên Windows

Yêu cầu Docker Desktop chạy Linux containers/WSL2 và Python dependencies của dự án.

1. Tạo `.env` từ `.env.example`, sau đó thay tất cả giá trị `replace-with-*` bằng giá trị riêng cho local. Tạo key bằng `openssl rand -hex 32`; các mật khẩu database nên dùng ký tự chữ/số để URI đơn giản. Không dùng thông tin demo trong production. Cài thêm driver PostgreSQL bằng `pip install -r requirements-postgres.txt`.
2. Cấu hình Django dùng PostgreSQL trong `.env`:

   ```dotenv
   DJANGO_DATABASE_URL=postgresql://crm_app:YOUR_CRM_PASSWORD@127.0.0.1:5433/crm
   ```

   Đặt `CRM_DB_NAME=crm`, `CRM_DB_USER=crm_app` và `CRM_DB_PASSWORD=YOUR_CRM_PASSWORD` tương ứng. Đặt thêm mật khẩu riêng `CRM_DB_ADMIN_PASSWORD` cho tài khoản khởi tạo PostgreSQL; Django không dùng tài khoản admin này. Nếu cổng `5433` hoặc `8088` đang dùng, đổi `CRM_DB_HOST_PORT` hoặc `SUPERSET_HOST_PORT` và cập nhật URL tương ứng.

3. Khởi động PostgreSQL CRM và Superset:

   ```powershell
   docker compose --env-file .env -f docker-compose.superset.yml up -d crm-db superset-meta-db superset-init superset
   ```

4. Trong môi trường Python đã cài dependencies, chạy migration, dữ liệu mẫu và tạo view analytics:

   ```powershell
   python manage.py migrate
   python manage.py seed_crm_data
   python manage.py setup_superset_analytics
   python manage.py runserver
   ```

   Django trên máy host kết nối PostgreSQL ở `127.0.0.1:5433`; Superset trong Docker kết nối database bằng hostname `crm-db`.

5. Sau khi migration và view analytics đã sẵn sàng, chạy bootstrap để tự đăng nhập bằng tài khoản admin, đăng ký database/dataset và tạo dashboard cùng bốn biểu đồ:

   ```powershell
   docker compose --env-file .env -f docker-compose.superset.yml run --rm superset-bootstrap
   ```

   Nếu cần chạy lại sau khi chỉnh dữ liệu hoặc xóa metadata, chạy lại lệnh trên hoặc chạy từ PowerShell:

   ```powershell
   $env:SUPERSET_URL = "http://127.0.0.1:8088"
   python superset/bootstrap_superset.py
   ```

   Mở [Superset](http://127.0.0.1:8088), đăng nhập bằng `SUPERSET_ADMIN_USERNAME` và `SUPERSET_ADMIN_PASSWORD` trong `.env`. Kết nối được tạo tự động với URI:

   ```text
   postgresql://superset_ro:<SUPERSET_READONLY_PASSWORD>@crm-db:5432/crm
   ```

   Kết nối này dùng tài khoản chỉ đọc; bốn dataset trong schema `analytics` được bootstrap tự động.

6. Dashboard đã tạo có slug `crm-analytics-dashboard` và bốn biểu đồ:

   - Khách hàng theo tháng/phân khúc: dataset `customer_monthly`, metric `SUM(customer_count)`.
   - Lead theo tháng/trạng thái/giải pháp: dataset `lead_pipeline`, metric `SUM(lead_count)`.
   - Việc chăm sóc/quá hạn: dataset `care_task_summary`, metric `SUM(task_count)` hoặc `SUM(overdue_count)`.
   - Doanh thu đã chốt theo tháng: dataset `revenue_transactions`, temporal column `closed_at`, metric `SUM(won_revenue)`; giao dịch `VOID` có doanh thu bằng 0.

   Có thể mở trực tiếp [dashboard CRM](http://127.0.0.1:8088/superset/dashboard/crm-analytics-dashboard/) sau khi đăng nhập. Nếu muốn chỉnh màu, bộ lọc hoặc bố cục, dùng **Edit dashboard** trong Superset; chạy lại bootstrap sẽ cập nhật lại bốn biểu đồ và bố cục chuẩn.

7. Đối chiếu dữ liệu hiển thị trước khi demo/nộp bài. Lệnh này so sánh tổng khách hàng, lead, việc chăm sóc và doanh thu WON giữa bảng CRM và bốn view analytics:

   ```powershell
   python manage.py verify_superset_analytics
   ```

   Lệnh phải in bốn dòng `PASS` và `Analytics views match CRM source data.`. Nếu dùng PostgreSQL trong Docker, chạy lệnh sau khi đã đặt `DJANGO_DATABASE_URL` trong `.env`; SQLite local sẽ báo rõ rằng cần PostgreSQL.

Các view trong schema `analytics` chỉ chứa chỉ số cần thiết, không có tên, email, số điện thoại, ghi chú hay nội dung tương tác. Superset metadata nằm trong PostgreSQL volume riêng. Lệnh `setup_superset_analytics` chỉ hỗ trợ PostgreSQL và cấp quyền đọc schema view cho role `superset_ro`.

Để dừng dịch vụ, chạy `docker compose --env-file .env -f docker-compose.superset.yml down`. Lệnh `down -v` xóa cả database demo và dashboard Superset; chỉ dùng nếu muốn xóa các volume này.

## Cách phân tích AI hoạt động

Khi nhân viên bấm **Phân tích ngay**:

1. Với lead từ form công khai, chỉ yêu cầu ban đầu hoặc phản hồi follow-up có consent AI riêng mới được đưa vào phân tích. Prompt không gồm tên/email/số điện thoại hoặc khung giờ liên hệ; nội dung khách tự nhập vẫn có thể chứa thông tin nhận diện.
2. Với hồ sơ nội bộ không có lead công khai, hệ thống dùng tối đa 20 tương tác gần nhất theo luồng demo.
3. Nếu có `GEMINI_API_KEY`, dữ liệu được gửi đến model trong `GEMINI_MODEL` với yêu cầu trả về JSON.
4. Kết quả Gemini được kiểm tra: phân khúc phải hợp lệ, điểm được giới hạn trong khoảng 0–100, nội dung được cắt theo giới hạn lưu trữ.
5. Nếu không có key, Gemini trả lỗi, JSON không hợp lệ hoặc kết quả không hợp lệ, hệ thống dùng `_rule_based_analysis()`.
6. Tạo một bản ghi `AIAnalysis`, cập nhật phân khúc và điểm mới nhất trên `Customer`, sau đó quay lại hồ sơ khách hàng.

Quy tắc cục bộ hiện tại:

| Điều kiện | Kết quả mặc định |
|---|---|
| Tổng chi tiêu từ 20.000.000 VNĐ | `VIP`, điểm 90 |
| Nội dung có từ khóa như “giá”, “báo giá”, “tư vấn”, “triển khai”, “demo” | `Tiềm năng`, điểm 75 |
| Không có tương tác và chưa chi tiêu | `Chưa phân loại`, điểm 25 |
| Các trường hợp còn lại | `Tiềm năng`, điểm 55 |

Rules chỉ là cơ chế dự phòng minh họa; Gemini có thể trả thêm các phân khúc `Ngủ đông` hoặc `Nguy cơ rời bỏ` dựa trên ngữ cảnh.

## Cấu trúc chính

| Thư mục/file | Vai trò |
|---|---|
| `config/` | Cấu hình Django/Wagtail và URL |
| `crm/` | Model, form, view, dịch vụ AI, test và management commands |
| `crm/models.py` | Model CRM, `CareTask` và Wagtail `LandingPage` |
| `crm/forms.py` | Form tư vấn công khai, follow-up, email nháp, consent và việc chăm sóc |
| `crm/wagtail_hooks.py` | Cấu hình tìm kiếm/lọc/xem chi tiết cho Snippets |
| `crm/services/email_draft_service.py` | Soạn email nháp có fallback và giới hạn dữ liệu gửi AI |
| `crm/migrations/` | Migration database của dự án |
| `crm/test_*.py`, `crm/tests.py` | Test AI, view, form lead/follow-up và browser E2E (`test_browser_e2e.py`) |
| `crm/templates/crm/` | Landing page CMS, CRM, email nháp/follow-up, báo cáo và form phản hồi |
| `crm/static/crm/` | CSS và JavaScript; Django phục vụ trực tiếp |
| `tailwind/` | Mã nguồn CSS Tailwind và công cụ build giao diện (tùy chọn) |
| `docs/` | Dàn ý báo cáo và roadmap tính năng |
| `AGENTS.md` | Quy tắc làm việc và nhiệm vụ dành cho AI agent |
| `.env.example` | Mẫu biến môi trường |

```text
day6AIERPandCRM/
├── config/                       # Settings, URL, ASGI/WSGI
├── crm/
│   ├── models.py                 # Customer, Interaction, LeadRequest, FollowUp, AIAnalysis
│   ├── forms.py                  # Form tư vấn, email follow-up và phản hồi
│   ├── views.py                  # CRM, gửi email và form trả lời bảo mật
│   ├── migrations/               # Migration database
│   ├── services/ai_service.py    # Gemini và rules fallback
│   ├── management/commands/      # Lệnh seed dữ liệu mẫu
│   ├── test_*.py, tests.py       # Test tự động
│   ├── templates/crm/            # Landing page, CRM, email và form follow-up
│   └── static/crm/               # CSS đã build và JavaScript mobile menu
├── tailwind/                     # Nguồn CSS và công cụ build Tailwind
│   ├── src/input.css             # CSS nguồn: component và utility Tailwind
│   ├── tailwind.config.js        # Cấu hình Tailwind, quét class trong template Django
│   └── package.json              # Lệnh build/watch CSS
├── docs/                         # Dàn ý báo cáo và roadmap tính năng
├── AGENTS.md                     # Hướng dẫn cho AI agent
├── .github/                      # GitHub Actions và mẫu Pull Request
├── manage.py                     # Điểm vào của Django
├── requirements.txt              # Thư viện Python
├── requirements-e2e.txt          # Playwright cho browser E2E tùy chọn
├── .env.example                  # Mẫu biến môi trường
└── README.md                     # Tài liệu dự án
```

Các thư mục `.venv/` và `tailwind/node_modules/` được tạo tự động trên máy cá nhân; không cần đưa lên Git.

## Frontend và build giao diện

Frontend dùng **Django Templates + Tailwind CSS 3**. Các trang HTML thuộc app Django nằm trong `crm/templates/crm/`; CSS/JavaScript mà Django phục vụ nằm trong `crm/static/crm/`. Thư mục `tailwind/` chứa CSS nguồn (`src/input.css`) và công cụ build, không phải một frontend React tách biệt. Người chỉ chạy ứng dụng không cần cài Node.js; CSS đã build sẵn. Khi muốn sửa giao diện, cài Node.js, mở terminal tại `tailwind/`, rồi chạy `npm install` và `npm run css:watch`. Lệnh `npm run css:build` tạo lại file CSS sau khi chỉnh sửa.

Các file giao diện chính:

- `crm/templates/crm/landing_page.html`: trang giới thiệu tổ chức, giải pháp và form nhận yêu cầu tư vấn tại `/`.
- `crm/templates/crm/privacy_notice.html`: thông báo mẫu về xử lý dữ liệu tại `/chinh-sach-du-lieu/`.
- `crm/templates/crm/includes/lead_request_form.html`: form dùng chung cho landing page và trang đăng ký riêng.
- `crm/templates/crm/lead_request.html`: trang đăng ký tư vấn riêng tại `/crm/dang-ky-tu-van/`.
- `crm/templates/crm/dashboard.html`: trung tâm tổng quan và các lối tắt theo công việc.
- `crm/templates/crm/customer_list.html`: danh sách khách hàng, tìm kiếm, lọc và phân trang.
- `crm/templates/crm/lead_request_list.html`: hộp thư lead và cập nhật trạng thái tiếp nhận.
- `crm/templates/crm/customer_detail.html`: hồ sơ, timeline tương tác, nút phân tích và lịch sử AI.
- `crm/templates/crm/base.html`: layout, sidebar, menu mobile và liên kết Wagtail Admin.
- `crm/static/crm/css/app.css`: CSS Tailwind đã build sẵn để chạy ngay.
- `crm/static/crm/js/app.js`: mở/đóng menu trên màn hình nhỏ.

Tên thương hiệu trên trang công khai lấy từ `PUBLIC_BRAND_NAME` trong file `.env` (mặc định `DigiFlow`). Có thể điền `PUBLIC_CONTACT_EMAIL` để hiển thị email liên hệ. Trước khi thu dữ liệu thật, thay `PUBLIC_DATA_CONTROLLER_NAME`, cấu hình `PUBLIC_PRIVACY_EMAIL` và đặt `PUBLIC_DATA_RETENTION_NOTICE` theo chính sách đã được đơn vị vận hành phê duyệt.

Để phát triển giao diện:

```powershell
cd tailwind
npm install
npm run css:watch
```

Trong một terminal khác, chạy Django bằng `python manage.py runserver`. Khi build một lần thay vì theo dõi liên tục, dùng `npm run css:build`.

Luồng xử lý:

```text
Khách gửi form → Customer + LeadRequest + Interaction → Nhân viên duyệt trong Wagtail
                                                        ↓
                                             AI service (khi nhân viên kích hoạt)
                                      ├─ Có API key: gọi Gemini
                                      └─ Không có/lỗi: rules fallback
                                                    ↓
                                      AIAnalysis → Dashboard / hồ sơ khách hàng
```

Form tách consent tiếp nhận/phản hồi khỏi consent AI tùy chọn; consent cho câu trả lời follow-up được hỏi riêng. Nộp form landing page không tự gửi email follow-up; nhân viên chủ động gửi. Gemini chỉ nhận nội dung đã đồng ý phân tích, không gửi tên/email/số điện thoại hoặc khung giờ liên hệ. Google nêu rõ điều khoản dùng dữ liệu khác nhau giữa dịch vụ miễn phí và trả phí; dịch vụ miễn phí có thể dùng nội dung gửi lên để cải thiện dịch vụ và cho người đánh giá xử lý nội dung. Vì vậy không nhập dữ liệu nhạy cảm, cá nhân hoặc bí mật vào prompt miễn phí; xem [điều khoản Gemini API](https://ai.google.dev/gemini-api/terms). Trang `/chinh-sach-du-lieu/` là thông báo mẫu, chưa phải chứng nhận tuân thủ pháp luật.

## Git workflow và CI

Repo chỉ có một nhánh chính là `main`. Mỗi thay đổi phải được thực hiện trên nhánh riêng rồi mở Pull Request vào `main`:

```text
main ← feature/* hoặc fix/*
```

GitHub Actions nằm tại `.github/workflows/ci.yml` và tự chạy khi có Pull Request vào `main` hoặc commit mới trên `main`.

CI kiểm tra backend, giao diện và lỗ hổng dependency:

- **Backend:** cài Python 3.11 và 3.12, kiểm tra migration đã được commit, migrate database, chạy `manage.py check` và toàn bộ test Django.
- **Frontend:** cài Node.js 20, chạy `npm ci` và build Tailwind CSS.
- **Dependency security:** `pip-audit` kiểm tra thư viện Python (trên Python 3.12) và `npm audit --audit-level=high` kiểm tra package frontend.

Không cần `GEMINI_API_KEY` trong CI; test fallback không gọi API thật. Trên GitHub nên bật bảo vệ nhánh `main`, bắt buộc Pull Request và yêu cầu cả hai job CI hoàn thành thành công trước khi merge.

## Xử lý lỗi thường gặp

| Lỗi | Cách xử lý |
|---|---|
| `No module named 'wagtail'` | Kích hoạt `.venv`, sau đó chạy `pip install -r requirements.txt` |
| Pylance gạch đỏ thuộc tính Django như `.objects` | Chọn đúng interpreter `.venv`; cài dependencies bằng `pip install -r requirements.txt`, sau đó chạy **Python: Restart Language Server** trong VS Code |
| `No module named 'crm'` | Chạy lệnh tại đúng thư mục chứa `manage.py` |
| `no such table` | Chạy `python manage.py migrate` |
| Không tìm thấy `seed_crm_data` | Kiểm tra `crm/management/__init__.py` và `crm/management/commands/__init__.py` |
| Trang trắng hoặc lỗi 500 | Xem traceback trong terminal đang chạy server |
| Gemini lỗi 429 | Hệ thống tự chuyển sang phân tích bằng rules |
| Lỗi `ExecutionPolicy` | Chạy lệnh `Set-ExecutionPolicy` ở phần Bắt đầu nhanh |

## Kiểm thử thủ công

Có thể chạy các test tự động của form bằng `python manage.py test crm`; ngoài ra kiểm tra luồng thủ công theo các kịch bản sau:

Chạy E2E qua trình duyệt Chromium trên database test cô lập:

```powershell
python -m pip install -r requirements-e2e.txt
playwright install chromium
$env:RUN_BROWSER_E2E = "1"
python manage.py test crm.test_browser_e2e --verbosity=2
Remove-Item Env:RUN_BROWSER_E2E
```

Test trình duyệt gửi form lead công khai, đăng nhập Wagtail bằng tài khoản chỉ tồn tại trong test database, chạy phân tích rules fallback rồi tạo việc chăm sóc. Không cần Gemini API key, không gửi email thật và không ghi dữ liệu vào database local. CI cài Chromium và chạy test này tự động trên Python 3.12.

| Kịch bản | Thao tác | Kết quả mong đợi |
|---|---|---|
| Quản trị dữ liệu | Vào Admin, tạo khách hàng và hai tương tác | Dữ liệu xuất hiện trong các Snippets tương ứng |
| Form công khai | Gửi form không đăng nhập; thử bỏ consent bắt buộc, bật/tắt consent AI, gửi email trùng và điền trường ẩn | Form ghi nhóm giải pháp; AI opt-in được lưu riêng, không đồng ý vẫn gửi được; lead không đồng ý không thể phân tích; email trùng dùng lại hồ sơ; bot trap bị từ chối |
| Landing page | Mở `/`, bấm điều hướng dịch vụ/liên hệ rồi gửi form | Trang công khai hiện đầy đủ nội dung, form hoạt động và gửi đến luồng lead hiện có |
| Email demo | Mở trang chủ và thông báo quyền riêng tư với email `.test` | Email được đánh dấu là minh họa, không có liên kết mailto giả |
| Đăng nhập | Mở `/admin/login/` | Nhãn, tiêu đề và thao tác đăng nhập hiển thị bằng tiếng Việt |
| Tổng quan | Mở `/crm/` | Thấy số liệu chính, yêu cầu gần đây và hồ sơ chờ phân tích; các khu vực có lối đi riêng |
| Danh bạ khách hàng | Mở `/crm/customers/`, tìm theo tên/email/công ty, lọc phân khúc | Danh sách phân trang; mở từng hồ sơ riêng |
| Hộp thư yêu cầu | Mở `/crm/yeu-cau/`, tìm/lọc theo trạng thái rồi đổi trạng thái | Yêu cầu được tìm thấy, trạng thái mới được lưu và phản hồi thành công |
| Email follow-up | Mở lead, chọn **Gửi form hỏi thêm**, gửi bằng console email, mở link ở terminal | Link mở form, khách gửi một phản hồi và CRM hiển thị nội dung; gửi lại lần hai bị chặn |
| Thu hồi link | Trên trang follow-up, thu hồi một link đang chờ phản hồi | Link bị thu hồi không còn truy cập được |
| Consent phản hồi AI | Gửi một phản hồi có consent và một phản hồi không consent, sau đó chạy phân tích | Chỉ nội dung đã đồng ý được dùng; thông tin liên hệ và khung giờ không được đưa vào prompt |
| Phân tích online | Điền `GEMINI_API_KEY`, mở hồ sơ và bấm **Phân tích ngay** | Hiển thị kết quả, nguồn là Gemini nếu API trả về hợp lệ |
| Phân tích fallback | Bỏ trống API key hoặc dùng key lỗi rồi phân tích | Không crash; kết quả có nguồn phân tích cục bộ |
| Lưu lịch sử | Phân tích cùng một khách hàng nhiều lần | Mỗi lần tạo một `AIAnalysis`, kết quả mới nhất cập nhật trên hồ sơ |

## Giới hạn và hướng phát triển

Đây là phiên bản đồ án/demo nên có một số giới hạn:

- Mặc định local dùng SQLite và `DEBUG=True`; có profile production riêng, nhưng vẫn cần người triển khai cấu hình HTTPS, SMTP, database bền vững và backup.
- Chưa có phân tích hàng loạt, tác vụ nền hoặc lập lịch tự động.
- Rules fallback là logic minh họa dựa trên tổng chi tiêu, số tương tác và từ khóa.
- Đã có nhóm quyền CRM Nhân viên/CRM Quản lý và kiểm tra quyền tại các màn hình/nghiệp vụ; chưa có ma trận phân quyền cấu hình linh hoạt theo từng trường dữ liệu.
- Form công khai chưa có rate limit/WAF tích hợp; trước khi mở internet nhận dữ liệu thật cần bật giới hạn request tại reverse proxy/CDN/WAF.

Roadmap chi tiết, có phân biệt tính năng đã triển khai và phần còn thiếu, nằm tại [docs/lo-trinh-tinh-nang.md](docs/lo-trinh-tinh-nang.md). Phần bổ sung thiết thực tiếp theo là nhập CSV có kiểm tra/xem trước và mở rộng báo cáo theo thời gian.

## Đối chiếu checklist đồ án

| Yêu cầu | Trạng thái | Bằng chứng trong dự án / cách trình bày khi demo |
|---|---|---|
| 1. Cài đặt Python và khởi tạo Wagtail | Hoàn thành | `requirements.txt` khai báo Wagtail và các thư viện; `config/settings/` cấu hình dự án; phần [Bắt đầu nhanh](#bắt-đầu-nhanh) hướng dẫn tạo môi trường, migrate và chạy ứng dụng. |
| 2. Model tùy chỉnh quản lý dữ liệu | Hoàn thành | `crm/models.py` có `Customer`, `LeadRequest`, `Interaction`, `AIAnalysis`, `CareTask` và `LandingPage`; `crm/wagtail_hooks.py` đưa các model CRM vào Snippets để quản trị trong Wagtail. |
| 3. Tích hợp AI | Hoàn thành | `crm/services/ai_service.py` gọi Google Gemini khi có `GEMINI_API_KEY`, kiểm tra kết quả và dùng rules fallback khi thiếu key hoặc API lỗi. Có thể demo fallback không cần API key; demo Gemini trực tiếp cần cấu hình key riêng trong `.env`. |
| 4. Giao diện cho người dùng tương tác với AI | Hoàn thành | `crm/views.py` và `crm/templates/crm/` cung cấp hồ sơ khách hàng, thao tác phân tích, hàng đợi ưu tiên và tạo việc chăm sóc từ đề xuất. Luồng mẫu có trong `crm/test_e2e_flow.py`. |
| 5. Kiểm thử luồng và tài liệu triển khai | Hoàn thành | `README.md` có cài đặt, cấu hình, seed dữ liệu, chạy ứng dụng và kịch bản kiểm tra; `crm/test_e2e_flow.py` kiểm tra luồng form công khai → phân tích AI fallback → tạo việc chăm sóc. Chạy `python manage.py test` để kiểm tra toàn bộ test Django. |

Phạm vi sản phẩm là **CRM cơ bản tích hợp Wagtail và AI**, đúng nhánh CRM của đề bài; dự án không tuyên bố là ERP đầy đủ. Khi quay demo, dùng dữ liệu giả từ `python manage.py seed_crm_data`; không đưa API key hoặc dữ liệu khách thật lên màn hình.

## Checklist trước khi nộp

- [ ] Cài thành công `requirements.txt`
- [ ] Chạy được migration và seed dữ liệu mẫu
- [ ] Form công khai tạo được yêu cầu tư vấn; yêu cầu xuất hiện trong Wagtail và timeline khách hàng
- [ ] Đăng nhập được Wagtail Admin
- [ ] Dashboard hiển thị tổng quan và lối tắt đến từng khu vực
- [ ] Hộp thư yêu cầu tư vấn lọc và cập nhật được trạng thái
- [ ] Nhân viên gửi email hỏi thêm; link phản hồi dùng một lần, hết hạn và thu hồi được
- [ ] CRM lưu phản hồi và chỉ phân tích nội dung có consent AI riêng
- [ ] Danh sách khách hàng tìm kiếm, lọc và phân trang được
- [ ] Hồ sơ hiển thị lịch sử tương tác
- [ ] Phân tích AI trả về kết quả bằng Gemini hoặc rules
- [ ] Kết quả được lưu trong **Snippets → Kết quả phân tích AI**
- [ ] Phân tích vẫn chạy khi bỏ `GEMINI_API_KEY`
- [ ] README và báo cáo mô tả đúng phạm vi đề tài
