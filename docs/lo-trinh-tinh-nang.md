# Lộ trình tính năng — CRM cho doanh nghiệp chuyển đổi số

Tài liệu này phân biệt rõ tính năng **đang có** với tính năng **đề xuất phát triển** cho hệ thống CRM của doanh nghiệp cung cấp giải pháp chuyển đổi số. Mục tiêu là hỗ trợ nhân viên quản lý khách hàng B2B từ lúc tư vấn, demo đến chăm sóc sau triển khai, nhưng vẫn giữ phạm vi vừa sức một đồ án Wagtail/Django.

## Những gì hệ thống đã có

Theo README và mã nguồn hiện tại, dự án đã có:

- Quản lý khách hàng bằng Wagtail: thông tin liên hệ, công ty, nguồn, ghi chú, chi tiêu và trạng thái.
- Landing page giới thiệu giải pháp với form tư vấn công khai: phân loại nhóm giải pháp, thu nhu cầu, tách consent tiếp nhận/phản hồi và consent AI tùy chọn; CRM lưu riêng dấu thời gian/phiên bản. Lead không đồng ý AI vẫn được tiếp nhận, nhưng phân tích bị chặn.
- Ghi lịch sử tương tác: email, điện thoại, gặp mặt hoặc hình thức khác.
- Nhân viên chủ động gửi email hỏi thêm cho lead; khách trả lời form qua link có hạn dùng, dùng một lần và có thể thu hồi. CRM lưu phản hồi trong hồ sơ và ghi nhận riêng consent AI cho từng phản hồi.
- Dashboard tổng quan; danh bạ khách hàng tìm kiếm/lọc/phân trang riêng; hộp thư yêu cầu tư vấn tìm kiếm, lọc trạng thái và cập nhật tiến độ riêng.
- Hồ sơ khách hàng với timeline tương tác và lịch sử phân tích.
- Phân tích từng khách hàng bằng Gemini hoặc rules fallback; lưu phân khúc, điểm, nhận định và đề xuất.
- Giao diện responsive bằng Django Templates và Tailwind CSS.

Các mục trên là phạm vi hiện tại, không phải roadmap mới. Chi tiết vẫn được mô tả trong [README](../README.md#tính-năng-chính).

## Nên phát triển trước

### 1. Hộp việc cần chăm sóc — tính năng ưu tiên cao nhất

Cho phép nhân viên biến đề xuất từ AI thành một việc chăm sóc có người phụ trách, hạn hoàn thành và trạng thái.

- Việc cần làm: liên hệ lại, gọi điện, gửi báo giá, hẹn gặp hoặc việc khác.
- Trường thông tin: khách hàng, nội dung, người phụ trách, ngày đến hạn, mức ưu tiên và trạng thái `Cần làm / Đang làm / Hoàn tất`.
- Dashboard có khu vực “Hôm nay”, “Quá hạn” và “Sắp tới”.
- Từ trang khách hàng, tạo việc mới dựa trên gợi ý AI với nội dung được điền sẵn; nhân viên xác nhận trước khi lưu.

**Tiêu chí hoàn thành:** có thể tạo/sửa/hoàn tất việc; việc gắn đúng khách hàng; Dashboard lọc được việc hôm nay và quá hạn; việc hoàn tất vẫn xem lại được.

**Vì sao đáng làm:** khép kín luồng từ AI phân tích đến hành động thực tế — điểm khác biệt rõ nhất khi trình bày đề tài.

### 2. Trợ lý soạn email có người duyệt

AI tạo bản nháp email dựa trên hồ sơ, các tương tác gần đây và mục tiêu chăm sóc. Nhân viên có thể sửa, sao chép hoặc bỏ bản nháp.

- Chọn mục tiêu: cảm ơn, hỏi thăm, nhắc lịch, gửi báo giá hoặc chăm sóc lại.
- Cho phép chọn giọng văn và độ dài.
- Hiển thị bản nháp để người dùng xem/sửa; chỉ lưu thành tương tác khi nhân viên xác nhận đã gửi.
- Dùng rules fallback hoặc thông báo rõ khi không có dịch vụ AI; không làm mất dữ liệu đang nhập.

**Tiêu chí hoàn thành:** bản nháp có nội dung phù hợp khách hàng; không tự gửi email; người dùng có thể chỉnh sửa và chỉ ghi lịch sử sau khi xác nhận.

**Giới hạn an toàn:** không tự động gửi email/Zalo trong phiên bản đồ án.

### 3. Danh sách khách hàng cần ưu tiên

Tạo một hàng đợi giúp nhân viên biết nên chăm sóc ai trước thay vì chỉ xem danh sách theo thứ tự tên.

- Kết hợp phân khúc/điểm AI, thời điểm tương tác gần nhất và việc chăm sóc còn mở.
- Bộ lọc nhanh: khách VIP, nguy cơ rời bỏ, chưa liên hệ lâu ngày, việc quá hạn.
- Mỗi dòng giải thích lý do ưu tiên, ví dụ: “Nguy cơ rời bỏ” hoặc “Chưa liên hệ trong 30 ngày”.

**Tiêu chí hoàn thành:** thứ tự ưu tiên có quy tắc minh bạch; người dùng lọc được nhóm; mỗi khách hàng mở được hồ sơ hoặc tạo việc chăm sóc ngay.

## Có thể làm nếu còn thời gian

### 4. Nhập và xuất CSV thân thiện với người dùng

- Tải mẫu CSV có sẵn.
- Xem trước dữ liệu và báo lỗi theo dòng trước khi nhập.
- Phát hiện email trùng, trường bắt buộc bị thiếu và dữ liệu không hợp lệ.
- Xuất danh sách theo bộ lọc hiện tại.

Đây là tính năng thực tế với nhóm người dùng không chuyên kỹ thuật. Nên bắt đầu bằng CSV, chưa cần hỗ trợ Excel nhiều sheet.

### 5. Báo cáo hiệu quả chăm sóc

- Số khách hàng theo phân khúc và nguồn.
- Số việc đã hoàn tất, đang mở và quá hạn.
- Xu hướng khách hàng mới theo tháng.
- Bộ lọc theo khoảng thời gian; xuất CSV để đưa vào báo cáo.

Chỉ nên biểu diễn chỉ số mà dữ liệu hiện có hỗ trợ; chưa nên gọi đây là dự báo doanh thu nếu chưa có dữ liệu đơn hàng đáng tin cậy.

## Thứ tự triển khai đề xuất

| Giai đoạn | Nội dung | Kết quả nhìn thấy khi demo |
|---|---|---|
| Đã có | Form tiếp nhận, email follow-up do nhân viên gửi và form phản hồi bảo mật | Nhân viên gửi link; khách bổ sung thông tin; CRM lưu phản hồi và consent |
| 1 | Việc chăm sóc, hạn hoàn thành và trạng thái | Tạo việc từ hồ sơ khách hàng; xem việc hôm nay/quá hạn |
| 2 | Trợ lý soạn email có người duyệt | AI tạo bản nháp theo ngữ cảnh; nhân viên duyệt trước khi ghi nhận đã gửi |
| 3 | Hàng đợi khách hàng cần ưu tiên | Dashboard giải thích khách hàng nào cần chăm sóc trước và vì sao |
| 4 | CSV và báo cáo cơ bản | Nạp dữ liệu nhanh, theo dõi hiệu quả và xuất danh sách |

## Kịch bản demo “đủ wow”

1. Nhân viên mở một khách hàng đang có nguy cơ rời bỏ.
2. Xem lịch sử trao đổi và kết quả AI cùng lý do phân khúc.
3. AI đề xuất liên hệ lại, đồng thời tạo bản nháp email để nhân viên xem và chỉnh sửa.
4. Nhân viên tạo việc “Gọi lại khách hàng” có hạn hoàn thành vào ngày mai.
5. Việc đó xuất hiện trên Dashboard trong nhóm “Sắp tới”; sau khi hoàn tất, trạng thái được cập nhật trên hồ sơ.

Luồng này thể hiện rõ quản trị dữ liệu bằng Wagtail, AI có ngữ cảnh, con người kiểm soát quyết định và hành động được theo dõi đến khi hoàn tất.

## Chưa nên làm trong phạm vi hiện tại

- Tách frontend thành ứng dụng React/Vue độc lập hoặc thêm một máy chủ frontend.
- Cho AI tự gửi email/tin nhắn hoặc tự thay đổi dữ liệu mà không có xác nhận.
- Thêm tồn kho, kế toán, nhân sự hay các phân hệ ERP không phục vụ luồng CRM chính.
- Thêm dự báo nâng cao, phân tích hàng loạt bằng Celery hoặc tích hợp nhiều kênh trước khi hoàn thiện luồng chăm sóc cơ bản.

Nên hoàn thiện và kiểm thử một luồng end-to-end trước khi mở rộng số lượng tính năng.
