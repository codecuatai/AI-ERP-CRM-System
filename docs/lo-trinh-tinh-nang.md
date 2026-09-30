# Lộ trình tính năng — CRM cho doanh nghiệp chuyển đổi số

Tài liệu này phân biệt rõ tính năng **đang có** với tính năng **đề xuất phát triển** cho hệ thống CRM của doanh nghiệp cung cấp giải pháp chuyển đổi số. Mục tiêu là hỗ trợ nhân viên quản lý khách hàng B2B từ lúc tư vấn, demo đến chăm sóc sau triển khai, nhưng vẫn giữ phạm vi vừa sức một đồ án Wagtail/Django.

## Những gì hệ thống đã có

Theo README và mã nguồn hiện tại, dự án đã có:

- Quản lý khách hàng bằng Wagtail: thông tin liên hệ, công ty, nguồn, ghi chú, chi tiêu và trạng thái.
- Landing page giới thiệu giải pháp với form tư vấn công khai: phân loại nhóm giải pháp, thu nhu cầu, tách consent tiếp nhận/phản hồi và consent AI tùy chọn; CRM lưu riêng dấu thời gian/phiên bản. Lead không đồng ý AI vẫn được tiếp nhận, nhưng phân tích bị chặn.
- Ghi lịch sử tương tác: email, điện thoại, gặp mặt hoặc hình thức khác.
- Nhân viên chủ động gửi email hỏi thêm cho lead; khách trả lời form qua link có hạn dùng, dùng một lần và có thể thu hồi. CRM lưu phản hồi trong hồ sơ và ghi nhận riêng consent AI cho từng phản hồi.
- Dashboard tổng quan; danh bạ khách hàng tìm kiếm/lọc/phân trang riêng; hộp thư yêu cầu tư vấn tìm kiếm, lọc trạng thái và cập nhật tiến độ riêng.
- Việc chăm sóc khách hàng: tạo từ hồ sơ/đề xuất AI, người phụ trách, loại việc, hạn, ưu tiên, trạng thái; dashboard chia quá hạn/hôm nay/sắp tới; có danh sách riêng và chỉnh sửa/hoàn tất.
- Hồ sơ khách hàng với timeline tương tác và lịch sử phân tích.
- Phân tích từng khách hàng bằng Gemini hoặc rules fallback; lưu phân khúc, điểm, nhận định và đề xuất.
- Giao diện responsive bằng Django Templates và Tailwind CSS.
- Landing page là Wagtail `LandingPage`, cho phép biên tập nội dung, danh mục giải pháp và quy trình tư vấn trong Pages.
- Wagtail Snippets có danh sách cấu hình tìm kiếm/lọc/xem chi tiết; có nhóm quyền CRM Nhân viên và CRM Quản lý.
- Trợ lý tạo email nháp theo mục tiêu/giọng văn/độ dài; Gemini chỉ dùng dữ liệu khách đã consent; fallback cục bộ; không tự gửi.
- Hàng đợi ưu tiên có điểm và lý do minh bạch theo phân khúc, điểm AI, việc quá hạn và thời gian từ lần tương tác.
- Báo cáo tổng hợp CRM và xuất danh sách khách hàng CSV theo bộ lọc.

Các mục trên là phạm vi hiện tại, không phải roadmap mới. Chi tiết vẫn được mô tả trong [README](../README.md#tính-năng-chính).

## Các tính năng đã triển khai

### Đã hoàn thành phần tích hợp dữ liệu: Apache Superset

- Django có thể dùng PostgreSQL tùy chọn, SQLite vẫn là mặc định local.
- Superset chạy riêng bằng Docker Compose, dùng database metadata riêng và tài khoản CRM chỉ đọc.
- Lệnh `setup_superset_analytics` tạo schema view chỉ chứa chỉ số cần thiết, không lộ thông tin liên hệ/nội dung tương tác.
- Seed thêm giao dịch doanh thu giả lập để demo biểu đồ theo thời gian; đây không phải nghiệp vụ kế toán hoặc dữ liệu doanh thu thật.
- README hướng dẫn khởi động database, kết nối SQLAlchemy URI, chọn dataset, tạo chart/dashboard và đối chiếu kết quả.

**Bước demo trong Superset:** thêm kết nối theo URI, đăng ký bốn dataset analytics, rồi tạo/publish chart và dashboard theo hướng dẫn README. Dữ liệu giao dịch là giả lập, không phải doanh thu thật.

### Đã hoàn thành: Trợ lý soạn email có người duyệt

AI tạo bản nháp email theo mục tiêu chăm sóc và dữ liệu được phép dùng trong luồng hiện tại; nhân viên có thể sửa, sao chép hoặc bỏ bản nháp. Không nên mô tả rằng tính năng luôn sử dụng lịch sử tương tác gần đây: email draft giới hạn ngữ cảnh theo service và consent.

- Chọn mục tiêu: cảm ơn, hỏi thăm, nhắc lịch, gửi báo giá hoặc chăm sóc lại.
- Cho phép chọn giọng văn và độ dài.
- Hiển thị bản nháp để người dùng xem/sửa; chỉ lưu thành tương tác khi nhân viên xác nhận đã gửi.
- Dùng rules fallback hoặc thông báo rõ khi không có dịch vụ AI; không làm mất dữ liệu đang nhập.

**Tiêu chí hoàn thành:** bản nháp có nội dung phù hợp khách hàng; không tự gửi email; người dùng có thể chỉnh sửa và chỉ ghi lịch sử sau khi xác nhận.

**Giới hạn an toàn:** không tự động gửi email/Zalo trong phiên bản đồ án.

### Đã hoàn thành: Danh sách khách hàng cần ưu tiên

Tạo một hàng đợi giúp nhân viên biết nên chăm sóc ai trước thay vì chỉ xem danh sách theo thứ tự tên.

- Kết hợp phân khúc/điểm AI, thời điểm tương tác gần nhất và việc chăm sóc còn mở.
- Bộ lọc nhanh: khách VIP, nguy cơ rời bỏ, chưa liên hệ lâu ngày, việc quá hạn.
- Mỗi dòng giải thích lý do ưu tiên, ví dụ: “Nguy cơ rời bỏ” hoặc “Chưa liên hệ trong 30 ngày”.

**Tiêu chí hoàn thành:** thứ tự ưu tiên có quy tắc minh bạch; người dùng lọc được nhóm; mỗi khách hàng mở được hồ sơ hoặc tạo việc chăm sóc ngay.

## Phần còn thiếu có thể phát triển tiếp

### Đã hoàn thành một phần: Xuất CSV và báo cáo cơ bản

- Xuất danh sách khách hàng theo bộ lọc hiện tại và xem báo cáo CRM.
- Chưa có nhập CSV, xem trước hay báo lỗi theo dòng; đây là phần tiếp theo nếu cần nạp dữ liệu hàng loạt.

Đây là tính năng thực tế với nhóm người dùng không chuyên kỹ thuật. Nên bắt đầu bằng CSV, chưa cần hỗ trợ Excel nhiều sheet.

### Đã hoàn thành cơ bản: Báo cáo hiệu quả chăm sóc

- Số khách hàng theo phân khúc và số khách mới trong 30 ngày gần đây.
- Số yêu cầu tư vấn theo trạng thái.
- Số việc chăm sóc theo trạng thái và tổng việc quá hạn.
- Chưa có bộ lọc khoảng thời gian tùy chọn, nhóm theo nguồn, biểu đồ hay xuất báo cáo tổng hợp riêng.

Chỉ nên biểu diễn chỉ số mà dữ liệu hiện có hỗ trợ; chưa nên gọi đây là dự báo doanh thu nếu chưa có dữ liệu đơn hàng đáng tin cậy.

## Thứ tự triển khai đề xuất

| Giai đoạn | Nội dung | Kết quả nhìn thấy khi demo |
|---|---|---|
| Đã có | Form tiếp nhận, email follow-up do nhân viên gửi và form phản hồi bảo mật | Nhân viên gửi link; khách bổ sung thông tin; CRM lưu phản hồi và consent |
| Đã có | Việc chăm sóc, hạn hoàn thành và trạng thái | Tạo việc từ hồ sơ/gợi ý AI; xem việc hôm nay, quá hạn, sắp tới |
| Đã làm | Wagtail CMS, Snippets và quyền nhóm | Chỉnh sửa trang chủ, tìm/lọc dữ liệu và cấp quyền theo vai trò |
| Đã làm | Trợ lý soạn email có người duyệt | Tạo bản nháp; nhân viên kiểm tra và tự gửi ngoài hệ thống |
| Đã làm | Hàng đợi khách hàng cần ưu tiên | Xem khách cần chăm sóc trước cùng lý do |
| Đã làm một phần | CSV và báo cáo cơ bản | Xuất danh sách, xem số liệu; chưa hỗ trợ nhập CSV |

## Kịch bản demo “đủ wow”

1. Nhân viên mở một khách hàng đang có nguy cơ rời bỏ.
2. Xem lịch sử trao đổi và kết quả AI cùng lý do phân khúc.
3. AI đề xuất liên hệ lại; nhân viên chuyển đề xuất thành việc nháp, kiểm tra và xác nhận.
4. Nhân viên tạo việc “Gọi lại khách hàng” có hạn hoàn thành vào ngày mai.
5. Việc đó xuất hiện trên Dashboard trong nhóm “Sắp tới”; sau khi hoàn tất, trạng thái được cập nhật trên hồ sơ.

Luồng này thể hiện rõ quản trị dữ liệu bằng Wagtail, AI có ngữ cảnh, con người kiểm soát quyết định và hành động được theo dõi đến khi hoàn tất.

## Chưa nên làm trong phạm vi hiện tại

- Tách frontend thành ứng dụng React/Vue độc lập hoặc thêm một máy chủ frontend.
- Cho AI tự gửi email/tin nhắn hoặc tự thay đổi dữ liệu mà không có xác nhận.
- Thêm tồn kho, kế toán, nhân sự hay các phân hệ ERP không phục vụ luồng CRM chính.
- Thêm dự báo nâng cao, phân tích hàng loạt bằng Celery hoặc tích hợp nhiều kênh trước khi hoàn thiện luồng chăm sóc cơ bản.

Nên hoàn thiện và kiểm thử một luồng end-to-end trước khi mở rộng số lượng tính năng.
