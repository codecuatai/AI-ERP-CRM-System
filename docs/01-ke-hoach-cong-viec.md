# Kế hoạch hoàn thiện đề tài AI CRM

## Mục tiêu MVP

Hoàn thành một luồng: quản lý khách hàng và lịch sử tương tác trong Wagtail → phân tích bằng Gemini hoặc quy tắc cục bộ → lưu kết quả → hiển thị trên CRM Dashboard.

## Các phần việc

| Phần | Việc | Kết quả cần có |
|---|---|---|
| Môi trường | Cài requirements, migrate, tạo superuser | Wagtail Admin đăng nhập được |
| Quản lý dữ liệu | Nhập Customer và Interaction bằng Snippets | Có dữ liệu đủ ngữ cảnh để demo |
| AI | Phân loại + nhận định + đề xuất; kiểm tra fallback | Kết quả được lưu thành AIAnalysis |
| Giao diện | Dashboard và trang chi tiết | Xem khách hàng, lịch sử và kết quả |
| Bàn giao | Chụp màn hình, viết báo cáo, chuẩn bị demo | Có hướng dẫn chạy và minh họa luồng |

## Checklist trước khi nộp

- [ ] Cài được repo theo README trên máy mới.
- [ ] Tạo được khách hàng và tương tác trong Wagtail Admin.
- [ ] Dashboard và trang chi tiết hiển thị được dữ liệu.
- [ ] Phân tích hoạt động khi có Gemini key và khi không có key.
- [ ] Kết quả AIAnalysis được lưu và xem lại được.
- [ ] README, ảnh chụp và báo cáo mô tả đúng phạm vi đã làm.

## Kịch bản demo 3–5 phút

Đăng nhập → mở Snippets và nhập một khách hàng → thêm 2–3 tương tác như hỏi giá, hỏi thời gian triển khai → mở dashboard → chọn khách hàng → bấm phân tích → trình bày segment, score, nhận định, đề xuất và bản ghi lịch sử.

Không dùng thông tin cá nhân thật trong dữ liệu demo hoặc gửi dữ liệu đó đến API AI.
