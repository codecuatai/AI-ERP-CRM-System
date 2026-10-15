# Kịch bản video demo TH2 (4–5 phút)

Kịch bản cập nhật ngày 15/10/2026 theo mã nguồn và kết quả kiểm thử. Không đọc số liệu Accuracy/ROC-AUC/Silhouette/MAE ghi cứng trong bản tài liệu cũ.

## Chuẩn bị

- Khởi động CRM, PostgreSQL và Superset; đăng nhập bằng tài khoản đã cấu hình trong `.env`.
- Dữ liệu `scenario.*@consultation.test` là minh họa B2B, không phải khách hàng thật.
- Nếu cần tạo lại: `python manage.py seed_consultation_scenarios --analyze`.
- Chạy `python manage.py setup_superset_analytics` và bootstrap trước khi quay; không mở file `.env` hoặc hiện khóa/mật khẩu trong video.

## 0:00–0:40 — Bài toán và kiến trúc

Giới thiệu CRM quản lý tư vấn chuyển đổi số B2B. Trình bày luồng CRM → PostgreSQL → pipeline có consent → schema analytics → Superset/MCP. Phân biệt dữ liệu tác nghiệp, kết quả dẫn xuất và metadata Superset.

## 0:40–1:40 — Ngữ cảnh tư vấn và AI có người duyệt

- Mở hồ sơ “Minh họa An Phúc”: 12 sales, 4 bảng tính, cần CRM; ngân sách còn trình duyệt.
- Xem lịch sử chat, phân tích mới nhất, nguồn Gemini và checklist hành động. Giải thích vì sao chưa duyệt ngân sách không đồng nghĩa đã tạm dừng.
- Mở “Minh họa Hạ tầng Sao Mai”: sự cố backup, nguy cơ hủy; ưu tiên hỗ trợ thay vì bán thêm.
- Cho thấy hồ sơ “Minh họa Riêng tư” không consent nên không có kết quả AI và nút phân tích bị chặn.

Lời dẫn: “Đây là dữ liệu minh họa do nhóm biên soạn. Nhân viên phải kiểm tra đề xuất; AI không tự gửi email.”

## 1:40–2:20 — Biến đề xuất thành hành động

Chọn một mục checklist → tạo việc chăm sóc → kiểm tra hạn và nội dung → xác nhận lưu. Tạo email nháp nhưng không bấm xác nhận đã gửi nếu chưa gửi ngoài thực tế. Có thể trình bày follow-up qua môi trường test với email backend trong bộ nhớ.

## 2:20–3:20 — Superset và MCP

- Trong báo cáo CRM, bấm “Làm mới dữ liệu phân tích”; chỉ người có quyền phân tích được thực hiện.
- Mở hai dashboard Superset, xem nhóm lead, sentiment/churn, RFM tham chiếu, dự báo hồi quy và đóng góp công thức.
- Chạy `python manage.py run_superset_mcp --test` và trình bày kết quả thực.
- Giải thích chart được dựng bằng bootstrap REST, MCP hỗ trợ danh sách dashboard, insights, SQL chỉ đọc và refresh có xác nhận. Chưa có HTTP MCP hay MCP tự tạo chart.

## 3:20–4:20 — Đánh giá AI trung thực

Mở các JSON và [báo cáo kiểm thử](kiem-thu-e2e-va-danh-gia-ai.md):

- Gemini khớp 7/7 nhãn kỳ vọng trên bộ minh họa có consent, sau khi đã sửa prompt bằng chính các ca này. Không suy rộng thành độ chính xác 100% ngoài thực tế.
- Sentiment đúng 19/20, còn sai một câu mỉa mai.
- Dự báo doanh thu demo có MAE khoảng 4,43 triệu VNĐ; baseline tháng trước tốt hơn với 3,5 triệu VNĐ. Chưa dùng dự báo này cho quyết định kinh doanh.
- Không gọi RFM là K-Means đã huấn luyện, hồi quy là Prophet hoặc đóng góp công thức là SHAP.

## 4:20–5:00 — Kiểm thử phần mềm và giới hạn

Cho thấy kết quả từ [test-results.json](validation/test-results.json), ảnh desktop/mobile và dashboard Superset kiểm tra trực tiếp. Kết thúc bằng phạm vi đã kiểm chứng và hướng tiếp theo: bộ nhãn độc lập, dữ liệu có nguồn/consent, so sánh baseline, thử usability với nhân viên thực tế và xử lý dependency frontend.
