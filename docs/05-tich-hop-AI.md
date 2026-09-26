# Tích hợp AI cho MVP CRM

## Luồng

```text
Customer + Interaction
        ↓
crm/services/ai_service.py
        ↓
Gemini (nếu có GEMINI_API_KEY) hoặc quy tắc cục bộ
        ↓
Kiểm tra phân khúc/điểm và lưu AIAnalysis
        ↓
Dashboard hiển thị nhận định và đề xuất
```

## Kết quả mong đợi

AI trả về JSON với `segment`, `score`, `summary` và `recommendation`. Segment phải thuộc `VIP`, `POTENTIAL`, `HIBERNATING`, `CHURN_RISK`, `UNCLASSIFIED`; score nằm trong khoảng 0–100. Service xác thực phân khúc, giới hạn điểm, và dùng kết quả quy tắc cục bộ nếu Gemini chưa cấu hình, lỗi mạng hoặc trả kết quả không hợp lệ.

## Cấu hình

Trong `.env`:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

SDK đang dùng là `google-genai`. Không commit key vào Git. Với dữ liệu trình diễn, chỉ dùng thông tin giả lập; nội dung khách hàng được gửi đến Gemini khi bật API.

## Tiêu chí demo

1. Tạo khách hàng và một vài tương tác trong Wagtail Admin.
2. Nhấn **Phân tích bằng AI** ở trang chi tiết CRM.
3. Xác nhận phân khúc, điểm và đề xuất xuất hiện; một bản ghi lịch sử được lưu.
4. Thử để trống API key và xác nhận luồng vẫn hoạt động bằng quy tắc cục bộ.
