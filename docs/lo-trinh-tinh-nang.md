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

### Module TH2 đã triển khai; đang kiểm chứng chất lượng AI

- PostgreSQL có schema `analytics`, bốn view nghiệp vụ, sáu bảng phân tích và role `superset_ro` chỉ đọc. SQLite có biểu đồ CRM cục bộ.
- Bootstrap REST tạo/cập nhật 10 dataset, 12 chart và 2 dashboard; đã kiểm tra truy vấn và hiển thị trực tiếp trên Superset.
- Bộ mở rộng riêng tạo thêm 20 chart và 1 dashboard Superset từ các dataset analytics sẵn có; không thêm model, dữ liệu seed hay quy trình AI mới.
- MCP stdio có bảy tool, gồm khám phá dataset/cột, tạo chart và dashboard có xác nhận; SQL dùng `superset_ro`. Chưa có HTTP MCP. Đã kiểm tra tạo thật, gọi lại không trùng, quyền truy cập và render trên Superset.
- Sáu phương pháp hiện tại: chấm điểm lead bằng công thức sigmoid, sentiment/churn từ lexicon, RFM theo tâm tham chiếu cố định, dự báo baseline/tuyến tính/trung bình với kiểm định quá khứ, đóng góp công thức, bất thường theo quy tắc/Z-score. Không mô tả thành Random Forest, K-Means đã huấn luyện, Prophet hoặc SHAP.
- Đã sửa consent từng nội dung chat/phản hồi, dự báo đọc sai doanh thu, lỗi nút đồng bộ, form follow-up bị CSRF và tràn ngang mobile. Có 8 tình huống tư vấn B2B minh họa và bộ kiểm tra hồi quy.
- Đánh giá tính từ dữ liệu kiểm thử và backtest, không dùng số liệu ghi cứng. Bộ tình huống có dùng để sửa mô hình, chưa chứng minh hiệu quả trên khách hàng thật. Dữ liệu demo hiện chọn baseline, MAE 3,5 triệu VNĐ thay vì hồi quy 4,43 triệu; không suy rộng ra tương lai.
- Tailwind đã nâng lên 4.3.3 và watcher 2.6.0, audit npm/Python không còn cảnh báo đã biết tại thời điểm kiểm tra. Browser E2E có Chromium/Firefox/WebKit; SMTP gửi và bị từ chối được kiểm tra qua loopback. Chi tiết: [hoàn thiện TH2](hoan-thien-th2.md).
- Kết quả và giới hạn: [báo cáo kiểm thử](kiem-thu-e2e-va-danh-gia-ai.md), [báo cáo kỹ thuật TH2](bao-cao-ky-thuat-th2.md).
- Nhúng dashboard AI bằng Embedded SDK và guest token có hạn/tự gia hạn sau kiểm tra quyền CRM; không cần đăng nhập Superset riêng. Hai tab biểu đồ đã hợp nhất thành Superset Live Workspace: tám biểu đồ nhúng riêng, mỗi biểu đồ có đoạn phân tích ngay phía dưới. Biểu đồ CRM thay thế tại cùng vị trí khi Superset lỗi; tải PNG/phóng to và tab bảng tổng hợp vẫn được giữ. Nhận xét theo quy tắc, không theo bộ lọc tương tác của iframe; quyền xem vẫn là toàn bộ analytics, chưa có RLS theo nhân viên. Cách cấu hình và kiểm tra: [README](../README.md#hiển-thị-superset-ngay-trong-trang-báo-cáo).

**Việc tiếp theo:** tập dữ liệu có nguồn/consent và nhãn độc lập; đánh giá dự báo ngoài mẫu với baseline; kiểm thử khả dụng với nhân viên thực tế; duy trì audit dependency.

Bổ sung thiết kế ngày **18/10/2026**, chưa triển khai mô hình mới: [báo cáo kỹ thuật mục 7](bao-cao-ky-thuat-th2.md#7-đề-xuất-nhiều-mô-hình-và-phương-pháp-ứng-dụng-ai--mục-6) mô tả các ứng viên cho lead, sentiment, churn, phân cụm, dự báo, bất thường và RAG; mỗi hướng có dữ liệu cần thu, baseline, metric và ứng dụng BI. Ưu tiên hoàn thành dữ liệu/nhãn độc lập trước thử mô hình đơn giản, sau đó mới quyết định tích hợp. Theo dõi model version/batch, giao diện phản hồi nhãn và thí điểm lợi ích kinh doanh vẫn là công việc đề xuất, chưa đánh dấu hoàn thành.

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
- Đã có CLI `import_crm_customers` với `--dry-run`, kiểm tra toàn bộ file trước khi ghi, bỏ qua email trùng hoặc cập nhật có chủ đích; chưa có màn hình nhập CSV trong frontend.

Đây là tính năng thực tế với nhóm người dùng không chuyên kỹ thuật. Nên bắt đầu bằng CSV, chưa cần hỗ trợ Excel nhiều sheet.

### Đã hoàn thành cơ bản: Báo cáo hiệu quả chăm sóc

- Số khách hàng theo phân khúc và số khách mới trong 30 ngày gần đây.
- Số yêu cầu tư vấn theo trạng thái.
- Số việc chăm sóc theo trạng thái và tổng việc quá hạn.
- Có biểu đồ ECharts trong CRM và dashboard Superset; frontend CRM chưa có bộ lọc thời gian tùy chọn hoặc xuất báo cáo tổng hợp riêng.

Chỉ nên biểu diễn chỉ số mà dữ liệu hiện có hỗ trợ; chưa nên gọi đây là dự báo doanh thu nếu chưa có dữ liệu đơn hàng đáng tin cậy.

## Thứ tự triển khai đề xuất

| Giai đoạn | Nội dung | Kết quả nhìn thấy khi demo |
|---|---|---|
| Đã có | Form tiếp nhận, email follow-up do nhân viên gửi và form phản hồi bảo mật | Nhân viên gửi link; khách bổ sung thông tin; CRM lưu phản hồi và consent |
| Đã có | Việc chăm sóc, hạn hoàn thành và trạng thái | Tạo việc từ hồ sơ/gợi ý AI; xem việc hôm nay, quá hạn, sắp tới |
| Đã làm | Wagtail CMS, Snippets và quyền nhóm | Chỉnh sửa trang chủ, tìm/lọc dữ liệu và cấp quyền theo vai trò |
| Đã làm | Trợ lý soạn email có người duyệt | Tạo bản nháp; nhân viên kiểm tra và tự gửi ngoài hệ thống |
| Đã làm | Hàng đợi khách hàng cần ưu tiên | Xem khách cần chăm sóc trước cùng lý do |
| Đã làm một phần | CSV và báo cáo cơ bản | Xuất danh sách, xem số liệu; nhập CSV qua CLI, chưa có giao diện nhập |

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
