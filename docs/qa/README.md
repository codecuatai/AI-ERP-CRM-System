# Bàn giao QA — Thành viên 1

Người phụ trách: **[Điền tên thành viên 1]**. Người sửa lỗi: **[Điền tên thành viên 2]**.

Mục tiêu: kiểm tra tính đúng đắn và ổn định của CRM B2B; ghi lỗi có thể tái hiện, theo dõi sửa lỗi và xác nhận bằng re-test.

## Sản phẩm bàn giao

- [CSV test case](test-cases.csv): 80 test case đã thực thi, gồm 76 PASS và 4 FAIL; UTF-8 BOM để mở bằng Excel.
- [Bug Tracker](bug-tracker.md): 4 lỗi đã tái hiện, mức độ, bước thực hiện, kết quả mong đợi/thực tế, người xử lý và lịch sử re-test.
- [Checklist kiểm thử](checklist.md): kết quả đã kiểm tra và danh sách cần thử tiếp trên trình duyệt.
- [Báo cáo lần chạy 29/09/2026](bao-cao-2026-09-29.md): môi trường, kết quả và giới hạn.
- [20 test QA bổ sung](../../crm/test_qa.py): chạy cùng bộ test thông thường.
- [4 test tái hiện lỗi mở](../../crm/qa_known_bugs.py): chạy riêng, hiện **thất bại**; không được hiểu bộ test thông thường xanh là đã hết lỗi.
- [Bằng chứng thực thi](evidence/): log Django check, migration check, toàn bộ test và test lỗi mở.

## Chuẩn bị và chạy lại

Dùng dữ liệu giả (`example.test`), cơ sở dữ liệu thử nghiệm và email console/locmem. Django test tự tạo, hủy database riêng; không cần seed vào `db.sqlite3` để chạy test. API Gemini trong test QA được tắt hoặc mock; email không được gửi ra ngoài.

Tại thư mục gốc, dùng Python 3.11/3.12 theo README và cài `requirements.txt`, sau đó:

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe manage.py test --verbosity=2
.venv\Scripts\python.exe manage.py test crm.qa_known_bugs --verbosity=2
```

Lệnh cuối cố ý kiểm tra hành vi **đúng mong đợi** của các lỗi đang mở và hiện trả exit code 1. Không dùng `skip`/`expectedFailure` để coi lỗi là đạt. File `qa_known_bugs.py` được chạy tường minh, không thuộc mẫu `test*.py` của CI hiện tại. Trước khi nghiệm thu phải chạy cả hai bộ. Sau khi sửa, chuyển test tương ứng sang `test_qa.py` để CI bảo vệ lâu dài.

Kiểm tra build frontend:

```powershell
Push-Location tailwind
npm.cmd ci
npm.cmd run css:build
Pop-Location
```

Để thử thủ công, dùng bản sao môi trường local riêng. Đặt `DJANGO_DATABASE_PATH` trỏ tới database QA, `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`, `GEMINI_API_KEY` rỗng, rồi chạy `migrate`, `setup_cms_homepage`, `setup_crm_groups`, `seed_crm_data`, `createsuperuser`, `runserver` theo README. Không chạy seed hoặc sửa/xóa hồ sơ trên database chứa dữ liệu thật. Với Gemini thật, dùng riêng dữ liệu giả có consent và ghi rõ lần chạy đó.

Chuẩn bị tài khoản: quản trị viên; staff thuộc nhóm CRM Nhân viên; CRM Quản lý; người chỉ có `access_crm`; người đăng nhập nhưng không có quyền; khách chưa đăng nhập. Tạo khách đang hoạt động/ngừng hoạt động, các phân khúc, ít nhất 16 khách để phân trang, lead có/không consent và việc quá hạn/hôm nay/sắp tới/hoàn tất.

## Cách duy trì Bug Tracker

1. Thành viên 1 chạy checklist sau mỗi bản bàn giao, ghi ngày, commit, môi trường, dữ liệu và bằng chứng. Mục chưa chạy giữ `Chưa kiểm tra`; không tích đạt theo suy đoán.
2. Khi gặp lỗi, thêm ID `BUG-xxx`; ghi từng bước, mong đợi/thực tế, mức độ, ưu tiên và test liên quan. Ảnh/log chỉ dùng dữ liệu giả, không chứa token phản hồi hoặc mật khẩu.
3. Giao thành viên 2: `Mới → Đang sửa`. Người sửa điền commit/PR và cách sửa rồi chuyển `Chờ re-test`.
4. Thành viên 1 checkout bản sửa, chạy test lỗi cụ thể, thử lại thao tác trên trình duyệt và chạy hồi quy các luồng liên quan. Ghi kết quả vào lịch sử, giữ lại lần thất bại trước.
5. Chỉ chuyển `Đã đóng` khi re-test đạt và có bằng chứng/commit. Nếu vẫn lỗi chuyển `Mở lại`. Báo cáo “đã fix” của người sửa chưa đủ để đóng lỗi.

Mẫu ghi một lần re-test:

| Ngày | Bug | Commit/PR bản sửa | Môi trường | Người kiểm tra | Lệnh/thao tác | Mong đợi | Thực tế | Kết quả | Bằng chứng |
|---|---|---|---|---|---|---|---|---|---|
| … | BUG-… | … | … | … | … | … | … | Đạt/Không đạt/Bị chặn | … |

**Điều kiện bàn giao đạt:** check/migration/test/build thành công; lỗi cao được đóng sau re-test; các mục giao diện/mobile và luồng trình duyệt đã có kết quả; lỗi còn lại được ghi rõ để nhóm quyết định. Hiện chưa đủ điều kiện kết luận toàn bộ ứng dụng đạt QA.
