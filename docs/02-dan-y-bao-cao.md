# Dàn ý báo cáo AI CRM với Wagtail

## Chương 1. Mở đầu

- Bối cảnh doanh nghiệp cần theo dõi khách hàng và lịch sử trao đổi.
- Mục tiêu: quản lý dữ liệu bằng Wagtail, dùng AI hỗ trợ phân loại và đề xuất chăm sóc.
- Phạm vi: Customer, Interaction, phân tích AI và dashboard; không triển khai ERP đầy đủ.

## Chương 2. Cơ sở lý thuyết

- CRM và quy trình chăm sóc khách hàng.
- Wagtail CMS, Django ORM và Snippets.
- Mô hình ngôn ngữ lớn và tích hợp Gemini API.
- Phân loại khách hàng dựa trên thông tin chi tiêu và nội dung tương tác.

## Chương 3. Phân tích và thiết kế

- Vai trò nhân viên CRM và các yêu cầu chức năng.
- ERD Customer 1—n Interaction, Customer 1—n AIAnalysis.
- Luồng xử lý: dữ liệu CRM → AI service → Gemini/quy tắc cục bộ → kết quả lưu trong database.
- Wireframe dashboard và trang chi tiết khách hàng.

## Chương 4. Cài đặt

- Môi trường Python, Django, Wagtail và SQLite.
- Các model trong `crm/models.py` và phần quản trị Snippets.
- AI service trong `crm/services/ai_service.py`, cấu hình API key và chế độ fallback.
- Dashboard, trang chi tiết và thao tác POST có CSRF.
- Chụp ảnh Wagtail Admin, dữ liệu tương tác, nút phân tích và kết quả.

## Chương 5. Đánh giá

- Tạo dữ liệu khách hàng và tương tác.
- Phân tích khi có API key, kiểm tra kết quả được lưu.
- Phân tích khi bỏ API key hoặc API lỗi, kiểm tra fallback cục bộ.
- Nêu hạn chế: phân loại còn phụ thuộc chất lượng dữ liệu và chưa có workflow kinh doanh nâng cao.

## Chương 6. Kết luận và hướng phát triển

- Tổng kết luồng quản trị dữ liệu, phân tích và hiển thị.
- Hướng phát triển: gợi ý email, phân quyền nhân viên, báo cáo, tích hợp đơn hàng sau khi MVP ổn định.

## Kịch bản demo

Tạo khách hàng trong Wagtail → thêm lịch sử hỏi giá/tư vấn → mở dashboard → bấm **Phân tích bằng AI** → giải thích phân khúc, điểm, nhận định và đề xuất đã lưu.
