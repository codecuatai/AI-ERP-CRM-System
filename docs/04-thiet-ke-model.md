# Thiết kế dữ liệu MVP AI CRM

Các model được quản lý bằng Wagtail Snippets trong `crm/models.py`.

```text
Customer 1 ──── * Interaction
Customer 1 ──── * AIAnalysis
```

## Customer

Thông tin liên hệ và bối cảnh kinh doanh: `full_name`, `email`, `phone`, `company`, `source`, `notes`, `total_spent`, `is_active`. Hai trường `ai_segment` và `ai_score` lưu kết quả phân loại mới nhất để dashboard hiển thị nhanh.

## Interaction

Mỗi tương tác tham chiếu một khách hàng, gồm `kind`, `subject`, `content` và `occurred_at`. AI dùng nội dung này cùng thông tin khách hàng làm ngữ cảnh phân tích.

## AIAnalysis

Lưu lịch sử từng lần phân tích: `segment`, `score`, `summary`, `recommendation`, `provider` và `created_at`. Bản ghi này cho phép xem lại nhận định cũ; `provider` cho biết kết quả đến từ Gemini hay quy tắc cục bộ.

Phạm vi ban đầu không có Order, kho hay kế toán. Có thể mở rộng khi luồng CRM/AI đã chạy ổn định.
