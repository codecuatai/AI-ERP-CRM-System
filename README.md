# AI CRM — CRM cho doanh nghiệp cung cấp giải pháp chuyển đổi số

Ứng dụng CRM cho phép doanh nghiệp cung cấp giải pháp chuyển đổi số quản lý khách hàng B2B, lịch sử tư vấn/triển khai và phân tích tiềm năng bằng Gemini AI. Nếu không có API key, hệ thống tự dùng bộ quy tắc cục bộ.

## Dự án là gì?

**AI CRM** là hệ thống quản lý quan hệ khách hàng dành cho một doanh nghiệp cung cấp các giải pháp chuyển đổi số. Doanh nghiệp có thể tư vấn, bán và triển khai các giải pháp như phần mềm quản lý kho, POS, CRM, hạ tầng máy chủ, sao lưu dữ liệu hoặc tích hợp hệ thống cho các khách hàng doanh nghiệp khác.

Trong bối cảnh này, khách hàng trong database là các doanh nghiệp đang tìm hiểu, mua hoặc sử dụng giải pháp chuyển đổi số. Nhân viên kinh doanh cần theo dõi nhu cầu, lịch sử trao đổi, giá trị đã chi tiêu và dấu hiệu cần chăm sóc tiếp. AI hỗ trợ trả lời câu hỏi: **khách hàng nào cần được ưu tiên và bước chăm sóc tiếp theo nên là gì?**

Khách chủ động gửi nhu cầu qua form công khai; hệ thống lưu yêu cầu và tạo hồ sơ khách hàng nếu email chưa có. Nhân viên làm việc theo các khu vực riêng: **Tổng quan** để xem việc cần chú ý, **Yêu cầu tư vấn** để tiếp nhận và cập nhật trạng thái, **Khách hàng** để tìm hồ sơ và xem lịch sử. Wagtail CMS dùng để quản lý dữ liệu chi tiết. Từ hồ sơ, nhân viên có thể bấm **Phân tích ngay** nếu khách đã đồng ý xử lý AI. Phần phân tích gọi Google Gemini khi có API key; nếu API không có hoặc gặp lỗi, hệ thống tự chuyển sang quy tắc cục bộ để ứng dụng vẫn hoạt động.

Đây là một đồ án tập trung vào luồng CRM cốt lõi, không phải hệ thống ERP hay hệ thống quản lý toàn bộ quy trình triển khai chuyển đổi số. Phạm vi chính là:

```text
Khách gửi form → Wagtail nhận LeadRequest → Nhân viên xem hồ sơ
                                             ↓
                                  Phân tích AI → Đề xuất chăm sóc
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
- [Demo trong 5 phút](#demo-trong-5-phút)
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
- **Dashboard:** hiển thị tổng khách hàng đang hoạt động, số khách hàng VIP, số khách hàng chưa phân tích và tổng chi tiêu.
- **Tìm kiếm và lọc:** tìm theo tên, email, công ty; lọc theo phân khúc AI.
- **Hồ sơ khách hàng:** xem thông tin liên hệ, tổng chi tiêu, timeline trao đổi, kết quả AI mới nhất và lịch sử các lần phân tích trước.
- **Phân tích AI:** trả về phân khúc, điểm tiềm năng, nhận định, đề xuất hành động và nguồn phân tích (`gemini` hoặc `rules`).
- **Quản trị bằng Wagtail:** quản lý dữ liệu tại **Snippets → Khách hàng**, **Yêu cầu tư vấn**, **Lịch sử tương tác** và **Kết quả phân tích AI**.
- **Responsive UI:** giao diện Django Templates + Tailwind CSS, có sidebar desktop và menu mobile.

Các phân khúc được hỗ trợ: **Chưa phân loại**, **VIP**, **Tiềm năng**, **Ngủ đông** và **Nguy cơ rời bỏ**.

## Mô hình dữ liệu

| Model | Vai trò | Dữ liệu chính |
|---|---|---|
| `Customer` | Hồ sơ khách hàng | Thông tin liên hệ, công ty, nguồn, ghi chú, tổng chi tiêu, trạng thái, phân khúc và điểm AI mới nhất |
| `Interaction` | Lịch sử trao đổi | Khách hàng, hình thức, chủ đề, nội dung và thời điểm; quan hệ nhiều-một với `Customer` |
| `LeadRequest` | Yêu cầu gửi từ form công khai | Nhóm giải pháp, nhu cầu, trạng thái, consent tiếp nhận và consent AI riêng kèm dấu thời gian/phiên bản |
| `AIAnalysis` | Lịch sử phân tích | Khách hàng, phân khúc, điểm, nhận định, đề xuất, nguồn phân tích và thời điểm; lưu lại mỗi lần bấm phân tích |

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
python manage.py seed_crm_data
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
python manage.py seed_crm_data
python manage.py createsuperuser
python manage.py runserver
```

Nếu PowerShell chặn kích hoạt môi trường ảo, chạy một lần:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Hoặc bỏ qua bước kích hoạt và dùng `.venv\Scripts\python.exe` thay cho `python`.

Migration ban đầu đã được lưu trong dự án nên cài mới chỉ cần chạy `migrate`. Chỉ chạy `makemigrations` khi thay đổi model. Lệnh `seed_crm_data` tạo dữ liệu mẫu nhưng không tạo tài khoản đăng nhập; tài khoản đó được tạo ở bước `createsuperuser`.

## Truy cập ứng dụng

Sau khi chạy `runserver`, mở. Dashboard và hồ sơ yêu cầu đăng nhập; nếu chưa đăng nhập, Django chuyển bạn đến trang đăng nhập Wagtail:

| Địa chỉ | Chức năng |
|---|---|
| [CRM Tổng quan](http://127.0.0.1:8000/crm/) | Số liệu chính, yêu cầu gần đây và hồ sơ chờ phân tích |
| [Danh sách khách hàng](http://127.0.0.1:8000/crm/customers/) | Tìm kiếm, lọc, phân trang và mở hồ sơ khách hàng |
| [Hộp thư yêu cầu tư vấn](http://127.0.0.1:8000/crm/yeu-cau/) | Tìm yêu cầu, lọc trạng thái, cập nhật tiến độ và mở hồ sơ |
| [Landing page](http://127.0.0.1:8000/) | Giới thiệu giải pháp và form công khai ở cuối trang |
| [Form yêu cầu tư vấn riêng](http://127.0.0.1:8000/crm/dang-ky-tu-van/) | Form công khai độc lập, dùng chung luồng lưu dữ liệu |
| [Thông báo quyền riêng tư](http://127.0.0.1:8000/chinh-sach-du-lieu/) | Dữ liệu thu thập, mục đích, AI, lưu trữ và cách liên hệ |
| [Wagtail Admin](http://127.0.0.1:8000/admin/) | Quản lý khách hàng, yêu cầu tư vấn và tương tác |

## Cấu hình Gemini tùy chọn

Lệnh `Copy-Item .env.example .env` đã tạo file `.env`. Mở file này và điền:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

Có thể lấy API key tại [Google AI Studio](https://aistudio.google.com/). Sau khi sửa `.env`, khởi động lại server. Không commit `.env` hoặc dữ liệu khách hàng thật lên Git.

Không có `GEMINI_API_KEY` cũng không sao: phân tích vẫn chạy bằng rules fallback và kết quả vẫn được lưu.

## Demo trong 5 phút

1. Mở [Landing page](http://127.0.0.1:8000/) và gửi yêu cầu ở khu vực liên hệ cuối trang.
2. Đăng nhập bằng tài khoản nhân viên tại khu vực CRM hoặc Wagtail Admin.
3. Mở [Hộp thư yêu cầu tư vấn](http://127.0.0.1:8000/crm/yeu-cau/) để xem yêu cầu, nhóm giải pháp khách quan tâm và cập nhật trạng thái.
4. Mở hồ sơ khách hàng từ yêu cầu hoặc tìm trong [Danh sách khách hàng](http://127.0.0.1:8000/crm/customers/); lịch sử trao đổi và phân tích nằm trong hồ sơ riêng.
5. Nếu khách đã bật đồng ý phân tích AI trên form, chọn **Phân tích ngay**. Nếu không, yêu cầu vẫn được lưu và nhân viên vẫn có thể phản hồi, nhưng phân tích AI sẽ không chạy.
6. Kiểm tra phân khúc, điểm tiềm năng, nhận định và đề xuất hành động.

Để kiểm tra fallback, để trống `GEMINI_API_KEY`, khởi động lại server và phân tích lại.

## Dữ liệu mẫu

Lệnh `python manage.py seed_crm_data` tạo dữ liệu phục vụ trình diễn:

- 6 khách hàng mẫu thuộc nhiều bối cảnh khác nhau.
- 12 lịch sử tương tác gồm email, điện thoại và gặp mặt.
- 2 bản ghi `AIAnalysis` có sẵn để Dashboard và hồ sơ hiển thị ngay.
- 4 khách hàng chưa có phân tích để trình diễn nút **Phân tích ngay**.

Lệnh seed dùng email và chủ đề tương tác để tránh tạo trùng khi chạy lại. Lệnh này chỉ tạo dữ liệu, không tạo tài khoản đăng nhập.

## Cách phân tích AI hoạt động

Khi nhân viên bấm **Phân tích ngay**:

1. Với lead từ form công khai, chỉ những yêu cầu đã bật consent AI mới được đưa vào phân tích; không đồng ý thì backend chặn cả thao tác phân tích. Dữ liệu gửi Gemini chỉ gồm nhóm giải pháp và nội dung yêu cầu được đồng ý, không gồm tên/email/số điện thoại.
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
| `crm/` | Model, form, view, dịch vụ AI, test và lệnh seed |
| `crm/models.py` | `Customer`, `Interaction`, `LeadRequest`, `AIAnalysis` |
| `crm/forms.py` | Form yêu cầu tư vấn công khai và kiểm tra đồng ý/honeypot |
| `crm/migrations/` | Migration database của dự án |
| `crm/test_*.py`, `crm/tests.py` | Test AI, view và form tiếp nhận lead |
| `crm/templates/crm/` | Landing page công khai, form tư vấn và giao diện CRM nội bộ |
| `crm/static/crm/` | CSS và JavaScript; Django phục vụ trực tiếp |
| `tailwind/` | Mã nguồn CSS Tailwind và công cụ build giao diện (tùy chọn) |
| `docs/` | Dàn ý báo cáo và roadmap tính năng |
| `AGENTS.md` | Quy tắc làm việc và nhiệm vụ dành cho AI agent |
| `.env.example` | Mẫu biến môi trường |

```text
day6AIERPandCRM/
├── config/                       # Settings, URL, ASGI/WSGI
├── crm/
│   ├── models.py                 # Customer, Interaction, LeadRequest, AIAnalysis
│   ├── forms.py                  # Form yêu cầu tư vấn công khai
│   ├── views.py                  # Form công khai, thông báo quyền riêng tư, CRM và phân tích
│   ├── migrations/               # Migration database
│   ├── services/ai_service.py    # Gemini và rules fallback
│   ├── management/commands/      # Lệnh seed dữ liệu mẫu
│   ├── test_*.py, tests.py       # Test tự động
│   ├── templates/crm/            # Landing page, form công khai, Dashboard, hồ sơ
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

Form tách consent bắt buộc để tiếp nhận/phản hồi khỏi consent AI tùy chọn; lưu riêng thời điểm và phiên bản. Gemini chỉ nhận nội dung nhu cầu và nhóm giải pháp của những lead đã đồng ý, không gửi tên/email/số điện thoại. Form không tự chạy AI, gửi email hay theo dõi hành vi. Google nêu rõ điều khoản dùng dữ liệu khác nhau giữa dịch vụ miễn phí và trả phí; dịch vụ miễn phí có thể dùng nội dung gửi lên để cải thiện dịch vụ và cho người đánh giá xử lý nội dung. Vì vậy không nhập dữ liệu nhạy cảm, cá nhân hoặc bí mật vào prompt miễn phí; xem [điều khoản Gemini API](https://ai.google.dev/gemini-api/terms). Trang `/chinh-sach-du-lieu/` là thông báo mẫu, chưa phải chứng nhận tuân thủ pháp luật.

## Git workflow và CI

Repo chỉ có một nhánh chính là `main`. Mỗi thay đổi phải được thực hiện trên nhánh riêng rồi mở Pull Request vào `main`:

```text
main ← feature/* hoặc fix/*
```

GitHub Actions nằm tại `.github/workflows/ci.yml` và tự chạy khi có Pull Request vào `main` hoặc commit mới trên `main`.

CI kiểm tra hai phần:

- **Backend:** cài Python 3.11 và 3.12, kiểm tra migration đã được commit, migrate database, chạy `manage.py check` và toàn bộ test Django.
- **Frontend:** cài Node.js 20, chạy `npm ci` và build Tailwind CSS.

Không cần `GEMINI_API_KEY` trong CI; test fallback không gọi API thật. Trên GitHub nên bật bảo vệ nhánh `main`, bắt buộc Pull Request và yêu cầu cả hai job CI hoàn thành thành công trước khi merge.

## Xử lý lỗi thường gặp

| Lỗi | Cách xử lý |
|---|---|
| `No module named 'wagtail'` | Kích hoạt `.venv`, sau đó chạy `pip install -r requirements.txt` |
| `No module named 'crm'` | Chạy lệnh tại đúng thư mục chứa `manage.py` |
| `no such table` | Chạy `python manage.py migrate` |
| Không tìm thấy `seed_crm_data` | Kiểm tra `crm/management/__init__.py` và `crm/management/commands/__init__.py` |
| Trang trắng hoặc lỗi 500 | Xem traceback trong terminal đang chạy server |
| Gemini lỗi 429 | Hệ thống tự chuyển sang phân tích bằng rules |
| Lỗi `ExecutionPolicy` | Chạy lệnh `Set-ExecutionPolicy` ở phần Bắt đầu nhanh |

## Kiểm thử thủ công

Có thể chạy các test tự động của form bằng `python manage.py test crm`; ngoài ra kiểm tra luồng thủ công theo các kịch bản sau:

| Kịch bản | Thao tác | Kết quả mong đợi |
|---|---|---|
| Quản trị dữ liệu | Vào Admin, tạo khách hàng và hai tương tác | Dữ liệu xuất hiện trong các Snippets tương ứng |
| Form công khai | Gửi form không đăng nhập; thử bỏ consent bắt buộc, bật/tắt consent AI, gửi email trùng và điền trường ẩn | Form ghi nhóm giải pháp; AI opt-in được lưu riêng, không đồng ý vẫn gửi được; lead không đồng ý không thể phân tích; email trùng dùng lại hồ sơ; bot trap bị từ chối |
| Landing page | Mở `/`, bấm điều hướng dịch vụ/liên hệ rồi gửi form | Trang công khai hiện đầy đủ nội dung, form hoạt động và gửi đến luồng lead hiện có |
| Tổng quan | Mở `/crm/` | Thấy số liệu chính, yêu cầu gần đây và hồ sơ chờ phân tích; các khu vực có lối đi riêng |
| Danh bạ khách hàng | Mở `/crm/customers/`, tìm theo tên/email/công ty, lọc phân khúc | Danh sách phân trang; mở từng hồ sơ riêng |
| Hộp thư yêu cầu | Mở `/crm/yeu-cau/`, tìm/lọc theo trạng thái rồi đổi trạng thái | Yêu cầu được tìm thấy, trạng thái mới được lưu và phản hồi thành công |
| Phân tích online | Điền `GEMINI_API_KEY`, mở hồ sơ và bấm **Phân tích ngay** | Hiển thị kết quả, nguồn là Gemini nếu API trả về hợp lệ |
| Phân tích fallback | Bỏ trống API key hoặc dùng key lỗi rồi phân tích | Không crash; kết quả có nguồn phân tích cục bộ |
| Lưu lịch sử | Phân tích cùng một khách hàng nhiều lần | Mỗi lần tạo một `AIAnalysis`, kết quả mới nhất cập nhật trên hồ sơ |

## Giới hạn và hướng phát triển

Đây là phiên bản demo/chạy local nên có một số giới hạn:

- Dùng SQLite và `DEBUG=True`, chưa cấu hình cho môi trường production.
- Chưa có phân tích hàng loạt, tác vụ nền hoặc lập lịch tự động.
- Rules fallback là logic minh họa dựa trên tổng chi tiêu, số tương tác và từ khóa.
- Chưa có phân quyền nghiệp vụ chi tiết ngoài yêu cầu đăng nhập.

Roadmap chi tiết, có phân biệt tính năng hiện có và đề xuất mới, nằm tại [docs/lo-trinh-tinh-nang.md](docs/lo-trinh-tinh-nang.md). Ưu tiên đề xuất là biến gợi ý AI thành việc chăm sóc có hạn hoàn thành, sau đó thêm soạn email có người duyệt và danh sách khách hàng cần ưu tiên.

## Checklist trước khi nộp

- [ ] Cài thành công `requirements.txt`
- [ ] Chạy được migration và seed dữ liệu mẫu
- [ ] Form công khai tạo được yêu cầu tư vấn; yêu cầu xuất hiện trong Wagtail và timeline khách hàng
- [ ] Đăng nhập được Wagtail Admin
- [ ] Dashboard hiển thị tổng quan và lối tắt đến từng khu vực
- [ ] Hộp thư yêu cầu tư vấn lọc và cập nhật được trạng thái
- [ ] Danh sách khách hàng tìm kiếm, lọc và phân trang được
- [ ] Hồ sơ hiển thị lịch sử tương tác
- [ ] Phân tích AI trả về kết quả bằng Gemini hoặc rules
- [ ] Kết quả được lưu trong **Snippets → Kết quả phân tích AI**
- [ ] Phân tích vẫn chạy khi bỏ `GEMINI_API_KEY`
- [ ] README và báo cáo mô tả đúng phạm vi đề tài
