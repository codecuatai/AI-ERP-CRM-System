# Bug Tracker

Bản kiểm tra: `591cfa5` + các test QA trên nhánh `test/member-1-qa`. Ngày phát hiện: **29/09/2026**.

Người phát hiện: kiểm thử tự động hỗ trợ Thành viên 1; người phụ trách xác nhận: **[Tên thành viên 1]**. Người nhận sửa đề xuất: **Thành viên 2 [chưa điền tên]**. Chưa có commit sửa hoặc xác nhận đóng lỗi.

Mức độ: **Cao** ảnh hưởng giao tiếp/dữ liệu nghiệp vụ; **Trung bình** làm sai kết quả hoặc lịch sử; **Thấp** sai thông tin giao diện. Ưu tiên **P1** sửa trước nghiệm thu, **P2** sửa trong đợt tiếp theo, **P3** cải thiện giao diện. Mức độ và ưu tiên là đánh giá QA ban đầu.

| ID | Chức năng / tiêu đề | Mức độ | Ưu tiên | Trạng thái | Người sửa | Commit sửa | Re-test sau sửa |
|---|---|---|---|---|---|---|---|
| BUG-001 | CSV biến số 0 thành ô rỗng | Trung bình | P2 | Mới | Thành viên 2 | Chưa có | Chưa thực hiện |
| BUG-002 | Gửi lại xác nhận email tạo lịch sử trùng | Trung bình | P2 | Mới | Thành viên 2 | Chưa có | Chưa thực hiện |
| BUG-003 | Gửi lại form hỏi thêm gửi hai email, thu hồi link đầu | Cao | P1 | Mới | Thành viên 2 | Chưa có | Chưa thực hiện |
| BUG-004 | Trang báo cáo hiện nhãn điều hướng “Khách hàng” | Thấp | P3 | Mới | Thành viên 2 | Chưa có | Chưa thực hiện |

## BUG-001 — CSV làm mất giá trị 0

- **Tiền điều kiện:** tài khoản có `export_crm_data`; khách có điểm AI = 0 và tổng chi tiêu = 0.
- **Bước tái hiện:** tạo khách giả với hai giá trị trên → mở Khách hàng → Xuất CSV → đọc dòng của khách trong file bằng CSV reader hoặc Excel.
- **Mong đợi:** cột Điểm AI và Tổng chi tiêu đều chứa `0`.
- **Thực tế:** cả hai ô rỗng, assertion cho kết quả `('', '') != ('0', '0')`.
- **Tác động:** mất phân biệt số 0 với dữ liệu chưa có khi dùng file báo cáo.
- **Vị trí cần xem:** `crm/views.py`, hàm `export_customers_csv`, `safe_cell` dùng `str(value or "")`.
- **Bằng chứng:** [known-bugs.txt](evidence/known-bugs.txt), `test_bug_001_csv_preserves_zero`.
- **Re-test:** chạy test trên; bổ sung số dương, Unicode, dấu phẩy/xuống dòng và công thức bảng tính. Cách sửa vẫn phải giữ bảo vệ công thức CSV.

```powershell
.venv\Scripts\python.exe manage.py test crm.qa_known_bugs.KnownBugReTests.test_bug_001_csv_preserves_zero
```

## BUG-002 — Lặp xác nhận email tạo hai tương tác

- **Tiền điều kiện:** tài khoản vào CRM; một khách giả; bản nháp có nội dung hợp lệ.
- **Bước tái hiện:** mở Soạn email → nhập bản nháp → gửi POST `action=record_sent` → gửi lại nguyên POST đó trước khi thay đổi nội dung (mô phỏng bấm liên tiếp hoặc trình duyệt gửi lại request) → xem timeline.
- **Mong đợi theo tiêu chí chống thao tác lặp:** cùng một lần xác nhận chỉ ghi một tương tác. Một email mới được gửi có chủ đích vẫn có thể ghi nhận riêng.
- **Thực tế:** tạo 2 `Interaction` loại EMAIL cho cùng nội dung; không có email thực nào được gửi bởi màn hình này.
- **Tác động:** lịch sử giao tiếp bị nhân đôi, gây hiểu nhầm số lần đã chăm sóc khách.
- **Vị trí cần xem:** `crm/views.py::customer_email_draft`, nhánh `record_sent`; `crm/templates/crm/email_draft.html`.
- **Bằng chứng:** [known-bugs.txt](evidence/known-bugs.txt), `test_bug_002_replayed_email_confirmation_logs_once`, kết quả `2 != 1`.
- **Giới hạn chứng minh:** đã tái hiện bằng hai POST tuần tự giống nhau, chưa thử double-click thật hoặc hai request đồng thời trên trình duyệt.
- **Re-test:** cùng một form/request bị gửi lại chỉ tạo một tương tác; mở một lần soạn mới vẫn ghi được email mới. Cần cập nhật test dùng mã chống gửi lặp nếu bản sửa bổ sung mã này.

```powershell
.venv\Scripts\python.exe manage.py test crm.qa_known_bugs.KnownBugReTests.test_bug_002_replayed_email_confirmation_logs_once
```

## BUG-003 — Lặp gửi follow-up tạo hai email và làm hỏng link đầu

- **Tiền điều kiện:** staff có `manage_crm_leads`; lead giả; backend email locmem trong test, console nếu thử thủ công.
- **Bước tái hiện:** mở Gửi form hỏi thêm → nhập câu hỏi → gửi hai POST giống nhau tới `/crm/yeu-cau/<id>/gui-form-bo-sung/` → kiểm tra hộp thư giả và trạng thái hai follow-up.
- **Mong đợi theo tiêu chí chống thao tác lặp:** gửi lại cùng lần submit chỉ phát một email, một follow-up, link email đó vẫn dùng được. Hành động gửi follow-up mới có chủ đích vẫn phải tạo link mới và thu hồi link cũ theo chức năng hiện tại.
- **Thực tế:** 2 email, 2 follow-up; bản đầu bị `REVOKED`. Kết quả `(2, 2, 1)` thay vì `(1, 1, 0)` cho số email/follow-up/link thu hồi.
- **Tác động:** khách nhận email trùng và có thể mở link đầu đã vô hiệu.
- **Vị trí cần xem:** `crm/views.py::lead_follow_up`, bước tạo follow-up, gửi mail và thu hồi link trước.
- **Bằng chứng:** [known-bugs.txt](evidence/known-bugs.txt), `test_bug_003_replayed_follow_up_sends_once`. Email chỉ nằm trong bộ nhớ, không gửi ra ngoài.
- **Giới hạn chứng minh:** replay POST tuần tự; chưa kiểm tra gửi đồng thời hoặc SMTP thật.
- **Re-test:** replay cùng lần submit không gửi trùng; gửi follow-up mới có chủ đích vẫn hoạt động; kiểm tra thêm gửi thất bại, hết hạn, thu hồi và trả lời một lần. Nếu bổ sung mã chống gửi lặp, test cần lấy mã từ GET form rồi dùng lại cho cả hai POST.

```powershell
.venv\Scripts\python.exe manage.py test crm.qa_known_bugs.KnownBugReTests.test_bug_003_replayed_follow_up_sends_once
```

## BUG-004 — Nhãn điều hướng trang báo cáo sai

- **Tiền điều kiện:** tài khoản có `access_crm`.
- **Bước tái hiện:** mở `/crm/bao-cao/` → đọc nhãn điều hướng trên thanh đầu trang.
- **Mong đợi:** `CRM / Báo cáo`.
- **Thực tế:** HTML render có `CRM / Khách hàng`, dù tiêu đề chính là Báo cáo CRM.
- **Tác động:** thông tin vị trí trang không nhất quán.
- **Vị trí cần xem:** `crm/templates/crm/base.html`, `.topbar-label`.
- **Bằng chứng:** [known-bugs.txt](evidence/known-bugs.txt), `test_bug_004_report_breadcrumb_identifies_report`; xác nhận từ HTML response, chưa chụp ảnh trình duyệt.
- **Re-test:** kiểm tra nhãn đúng tại Báo cáo; kiểm tra Tổng quan, Khách hàng, Ưu tiên, Soạn email và Việc chăm sóc để tránh lỗi tương tự.

```powershell
.venv\Scripts\python.exe manage.py test crm.qa_known_bugs.KnownBugReTests.test_bug_004_report_breadcrumb_identifies_report
```

## Lịch sử kiểm tra / re-test

| Ngày | Bug | Bản kiểm tra | Người kiểm tra | Kết quả | Quyết định |
|---|---|---|---|---|---|
| 29/09/2026 | BUG-001…004 | `591cfa5` + bộ test QA | Kiểm thử tự động hỗ trợ TV1 | 4/4 test tiêu chí mong đợi thất bại; tái hiện được lỗi | Giữ Mới; bàn giao TV2 |

Đây là lần xác nhận lỗi ban đầu, **không phải re-test sau sửa**. Dùng [mẫu re-test](README.md#cách-duy-trì-bug-tracker) khi có commit sửa; không ghi đè lịch sử này.
