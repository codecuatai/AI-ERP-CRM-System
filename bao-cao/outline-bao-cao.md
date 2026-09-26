# Dàn ý báo cáo nộp (rút gọn — copy vào Word)

**Đề tài:** Xây dựng hệ thống AI ERP/CRM đơn giản với Wagtail CMS
**Môn:** Hệ thống Kinh doanh Thông minh — Day 6

## 1. Mở đầu
- Bối cảnh: quản lý KH bằng Excel rời rạc, không cảnh báo rời bỏ.
- Mục tiêu: (1) số hóa KH/đơn hàng bằng Wagtail; (2) AI phân loại + gợi ý email; (3) dashboard.
- Phạm vi: CRM cơ bản, dùng API AI có sẵn.

## 2. Cơ sở lý thuyết
- 2.1 ERP vs CRM (bảng so sánh, chốt chọn CRM).
- 2.2 Wagtail CMS: Snippet, ModelAdmin, Page; vì sao hơn Django admin thuần.
- 2.3 So sánh Gemini 1.5 Flash vs GPT-4o-mini (giá/tốc độ/quota) → chọn Gemini demo.
- 2.4 RFM + mapping 4 nhóm VIP/Tiềm năng/Ngủ đông/Rời bỏ.

## 3. Thiết kế
- 3.1 ERD: Customer 1—n Order, Customer 1—n Ticket (vẽ dbdiagram.io).
- 3.2 Sequence: Admin nhập → DB → nút AI → API → lưu ai_segment → dashboard.
- 3.3 Wireframe dashboard (bảng + badge + modal email).

## 4. Triển khai (chương chính, kèm ảnh)
- 4.1 `pip install -r requirements.txt`, `wagtail start ai_erp`, migrate, superuser.
- 4.2 Code `crm/models.py` (trích `demo/models_demo.py`).
- 4.3 Code `crm/ai_services.py` (rule-based + Gemini + fallback).
- 4.4 Dashboard + 2 nút AI (ảnh `demo/templates_demo.html`).
- 4.5 Dữ liệu: 12 KH + 20 đơn (`demo/data_mau.json`).

## 5. Kiểm thử
| Kịch bản | Thao tác | Kết quả |
|----------|----------|---------|
| KT1 | Tạo KH → bấm phân loại AI | ai_segment được điền |
| KT2 | Xóa key/ngắt mạng | fallback rule-based, không crash |
| KT3 | Bấm gợi ý email + báo cáo tuần | modal hiện đúng |

## 6. Kết luận
- Đạt 5/5 checklist, luồng Admin→AI→Frontend chạy được.
- Hạn chế: phụ thuộc API ngoài, chưa phân quyền sâu.
- Hướng phát triển: chatbot, dự báo churn ML, gửi mail thật qua Gmail/Zalo OA.

**Phụ lục:** prompt AI, link GitHub, video demo 3–5 phút.
