# Checklist kiểm thử CRM

Lần chạy: **29/09/2026**, bản `591cfa5` + test QA. Người phụ trách: **[Tên thành viên 1]**.

**Đạt (tự động)** nghĩa là assertion đã chạy thành công trên dữ liệu giả. Không đồng nghĩa đã quan sát giao diện, thao tác bằng chuột hoặc kiểm tra mobile. **Không đạt** có Bug ID. **Chưa kiểm tra** phải được thành viên 1 chạy tiếp, điền thực tế/ngày/người kiểm tra và bằng chứng.

Trong cột bằng chứng: `QA` = `crm.test_qa.QAEdgeCaseTests`; `Views` = `crm.test_views.CRMViewTests`; `Public` = `crm.tests.PublicLeadRequestTests`; `FollowUp` = `crm.test_follow_up.LeadFollowUpFlowTests`; `AI` = `crm.test_ai_service.RuleBasedAnalysisTests`. Log: [backend-tests.txt](evidence/backend-tests.txt).

## Chức năng đã thực thi

| ID | Màn hình / thao tác / dữ liệu | Kết quả mong đợi và thực tế | Trạng thái | Bằng chứng (tên test) |
|---|---|---|---|---|
| QA-01 | Mở 16 màn hình công khai/CRM | HTTP 200, render thành công | Đạt (tự động) | QA.test_screens_and_rendered_internal_links_resolve |
| QA-02 | Mở các link nội bộ tuyệt đối có trong 16 màn hình | Theo redirect đến HTTP 200 với quản trị viên | Đạt (tự động) | QA.test_screens_and_rendered_internal_links_resolve |
| QA-03 | CSS và JS của CRM | Django tìm thấy asset | Đạt (tự động) | QA.test_static_assets_exist |
| QA-04 | 5 Snippet: Khách, Lead, Tương tác, Việc, AI; list/add/edit/inspect | 20 trang render HTTP 200 với quản trị viên | Đạt (tự động) | QA.test_snippet_list_add_edit_inspect_screens |
| QA-05 | Landing CMS được publish | Nội dung CMS xuất hiện ở trang gốc | Đạt (tự động) | crm.test_wagtail_cms.WagtailHomepageTests.test_published_landing_page_renders_on_site_root |
| QA-06 | Form tư vấn hợp lệ | Tạo khách, lead và tương tác, chuyển trang thành công | Đạt (tự động) | Public.test_submission_creates_customer_request_and_interaction |
| QA-07 | Bỏ trống/tất cả khoảng trắng ở trường bắt buộc | Lỗi đúng trường, không ghi thêm dữ liệu | Đạt (tự động) | QA.test_required_fields_reject_empty_and_whitespace |
| QA-08 | Email sai, lựa chọn giải pháp không tồn tại | Báo lỗi, không tạo lead | Đạt (tự động) | QA.test_invalid_email_and_solution_are_rejected |
| QA-09 | Tên/công ty 160–161; điện thoại 30–31; nhu cầu 2000–2001 ký tự | Đúng giới hạn được nhận, vượt giới hạn bị từ chối | Đạt (tự động) | QA.test_public_field_lengths_at_and_over_limit |
| QA-10 | Tiếng Việt, nháy đơn, &, chuỗi script trong nhu cầu | Dữ liệu lưu đúng; HTML escape script trong hồ sơ | Đạt (tự động) | QA.test_special_characters_round_trip_and_are_html_escaped |
| QA-11 | Gửi form không CSRF | HTTP 403, không tạo lead | Đạt (tự động) | QA.test_public_post_requires_csrf |
| QA-12 | Honeypot có nội dung | Không tạo khách | Đạt (tự động) | Public.test_honeypot_submission_is_rejected |
| QA-13 | Email khách đã có, khác chữ hoa/thường | Dùng lại khách, không ghi đè tên cũ | Đạt (tự động) | Public.test_repeat_email_reuses_customer_case_insensitively |
| QA-14 | Consent AI bật/tắt | Lưu riêng; không consent vẫn gửi yêu cầu được | Đạt (tự động) | Public.test_ai_consent_is_optional_and_recorded_separately |
| QA-15 | Người chưa đăng nhập / thiếu quyền mở CRM | Chuyển đăng nhập / HTTP 403 | Đạt (tự động) | QA.test_internal_screens_require_login_and_permission |
| QA-16 | Chỉ có access_crm gọi phân tích, xuất CSV, tạo việc, cập nhật lead, gửi hỏi thêm | HTTP 403; không phát sinh phân tích, việc hoặc email | Đạt (tự động) | QA.test_access_permission_alone_cannot_analyze_export_or_manage |
| QA-17 | GET các action chỉ nhận POST | Phân tích, đổi trạng thái, thu hồi link trả 405 | Đạt (tự động) | QA.test_post_only_actions_reject_get |
| QA-18 | ID khách/việc/lead/email không tồn tại | HTTP 404 | Đạt (tự động) | QA.test_missing_objects_return_404 |
| QA-19 | Tìm kiếm ký tự đặc biệt; page=abc/-1/99999 ở 4 danh sách | Không lỗi 500; trang hợp lệ | Đạt (tự động) | QA.test_invalid_pagination_and_search_do_not_crash |
| QA-20 | 16 khách, từ khóa QA & POS và VIP, chuyển trang 2 | Giữ bộ lọc; còn 1 khách trang 2 | Đạt (tự động) | QA.test_customer_pagination_keeps_filters |
| QA-21 | Dashboard có việc quá hạn/hôm nay/sắp tới/đã xong | Chia nhóm đúng, bỏ việc hoàn tất | Đạt (tự động) | Views.test_dashboard_groups_overdue_today_and_upcoming_tasks |
| QA-22 | Lọc lead và cập nhật trạng thái hợp lệ | Danh sách và trạng thái đúng | Đạt (tự động) | Views.test_lead_request_list_filters_by_status; test_staff_can_update_lead_request_status |
| QA-23 | POST trạng thái lead không hợp lệ | Thông báo lỗi, giữ trạng thái cũ | Đạt (tự động) | QA.test_invalid_lead_status_preserves_data |
| QA-24 | Tạo việc từ khách | Lưu đúng khách, tự gán người thao tác | Đạt (tự động) | Views.test_user_can_create_care_task_and_get_assigned_automatically |
| QA-25 | Tên việc trắng, ngày 30/02, ưu tiên/khách sai | Báo lỗi, không tạo việc | Đạt (tự động) | QA.test_invalid_task_fields_do_not_save |
| QA-26 | Sửa customer ẩn khi tạo việc từ một hồ sơ | Việc vẫn thuộc khách trong URL | Đạt (tự động) | QA.test_customer_bound_task_ignores_tampered_customer |
| QA-27 | Hoàn tất việc | Lưu DONE và thời điểm hoàn tất | Đạt (tự động) | Views.test_task_can_be_completed_from_edit_form |
| QA-28 | Tạo việc từ gợi ý AI | Chỉ điền nháp, chưa lưu | Đạt (tự động) | Views.test_ai_recommendation_prefills_task_but_does_not_save_automatically |
| QA-29 | Hàng đợi ưu tiên và lọc nguy cơ rời bỏ | Hiện lý do; chỉ nhóm phù hợp | Đạt (tự động) | Views.test_priority_queue_explains_why_customer_needs_attention; test_priority_queue_quick_filter_shows_only_matching_customers |
| QA-30 | Thiếu API key / lỗi timeout / output AI sai | Fallback rules, không crash | Đạt (tự động) | AI.test_missing_api_key_uses_rules_fallback; QA.test_gemini_errors_and_malformed_output_fall_back |
| QA-31 | Lead/phản hồi thiếu consent AI | Chặn phân tích hoặc loại khỏi prompt; không đưa trường liên hệ vào prompt đã giới hạn | Đạt (tự động) | AI.test_gemini_prompt_for_public_lead_excludes_contact_and_unconsented_requests; test_gemini_prompt_includes_only_consented_follow_up_answers_without_identity |
| QA-32 | Tạo email nháp / xác nhận một lần | Chưa xác nhận không log/gửi; xác nhận lưu tương tác | Đạt (tự động) | Views.test_email_draft_is_generated_without_sending_or_logging; test_email_is_logged_only_after_explicit_user_confirmation |
| QA-33 | Xác nhận email trắng | Báo lỗi, không log/gửi | Đạt (tự động) | QA.test_empty_email_confirmation_does_not_log_or_send |
| QA-34 | Gửi lại cùng xác nhận email hai lần | Cần một tương tác; thực tế có hai | **Không đạt** | BUG-002 |
| QA-35 | Staff gửi follow-up; người không staff bị chặn; SMTP giả lỗi | Gửi đúng khi đủ quyền; thất bại không log thành công | Đạt (tự động) | FollowUp.test_staff_can_send_follow_up_email_and_create_activity; test_non_staff_user_cannot_send_follow_up_email; test_email_failure_revokes_link_and_does_not_log_successful_contact |
| QA-36 | Trả lời link follow-up hai lần | Chỉ một phản hồi được lưu | Đạt (tự động) | FollowUp.test_customer_can_submit_response_once_and_it_is_saved_to_customer_timeline |
| QA-37 | Link sai, hết hạn, thu hồi | Chặn truy cập theo trạng thái | Đạt (tự động) | FollowUp.test_expired_link_is_rejected_and_marked_expired; test_invalid_or_revoked_link_does_not_expose_lead_data |
| QA-38 | Chủ động gửi follow-up mới | Thu hồi link trước đó | Đạt (tự động) | FollowUp.test_sending_a_new_follow_up_invalidates_the_previous_open_link |
| QA-39 | Gửi lại cùng POST follow-up hai lần | Cần một lần gửi; thực tế hai email, link đầu bị thu hồi | **Không đạt** | BUG-003 |
| QA-40 | CSV lọc theo q/segment/active; Unicode, dấu phẩy, xuống dòng | Đúng khách, đọc lại đủ dữ liệu | Đạt (tự động) | QA.test_csv_filters_and_special_characters |
| QA-41 | CSV có chuỗi bắt đầu công thức | Tiền tố công thức được vô hiệu hóa cho mẫu đã thử | Đạt (tự động) | Views.test_customer_export_neutralizes_spreadsheet_formulas |
| QA-42 | CSV điểm AI và chi tiêu bằng 0 | Cần số 0; thực tế ô rỗng | **Không đạt** | BUG-001 |
| QA-43 | Báo cáo tổng số khách/việc trên fixture | Giá trị kiểm tra khớp database | Đạt (tự động) | Views.test_report_shows_existing_crm_counts |
| QA-44 | Nhãn điều hướng ở Báo cáo | Cần Báo cáo; thực tế Khách hàng | **Không đạt** | BUG-004 |

## Kiểm tra thủ công cần tiếp tục

Điền kết quả cho từng mục và lưu ảnh/log kèm browser, kích thước màn hình và commit. Các mục này **chưa được thực thi trong lần bàn giao**.

| ID | Cách thử | Tiêu chí đạt | Trạng thái / thực tế / bằng chứng |
|---|---|---|---|
| MAN-01 | Chrome và Edge desktop 1366×768: đi qua mọi màn hình QA-01 và Snippet | Chữ Việt đúng; không mất nút, che form; CSS/JS tải thành công | Chưa kiểm tra |
| MAN-02 | Mobile 375×812 và 390×844; mở menu, đóng bằng X/overlay/Escape | Menu thao tác đúng; nội dung đọc được; bảng cuộn trong vùng phù hợp | Chưa kiểm tra |
| MAN-03 | Landing: bấm logo, Giải pháp, Cách làm, Liên hệ, CTA, chính sách, email liên hệ | Đi đúng anchor/URL; menu mobile và trạng thái focus rõ | Chưa kiểm tra |
| MAN-04 | Tab/Shift+Tab/Enter qua form và menu; thử phóng to 200% | Đọc/nhập được; focus nhìn thấy; thông báo lỗi gắn đúng trường | Chưa kiểm tra |
| MAN-05 | Đăng nhập đúng/sai; đăng xuất; Back và mở URL nội bộ; thử nhóm Nhân viên/Quản lý | Phiên và quyền đúng, không truy cập dữ liệu sau logout | Chưa kiểm tra |
| MAN-06 | Form tư vấn: nút gửi, Enter, lỗi HTML5/server; gửi thành công rồi refresh | Thông báo rõ, dữ liệu nhập còn khi lỗi; refresh GET không gửi thêm | Chưa kiểm tra |
| MAN-07 | Tất cả bộ lọc/nút Xóa lọc/Trước/Sau, màn hình danh sách rỗng | URL, bộ lọc và kết quả nhất quán; nút disabled đúng | Chưa kiểm tra |
| MAN-08 | Tạo/sửa/hoàn tất/mở lại việc; thử nút Quay lại/Hủy; bấm Lưu liên tiếp | Không lưu khi hủy; thời điểm hoàn tất đúng; không tạo việc ngoài ý muốn | Chưa kiểm tra |
| MAN-09 | Soạn email: đổi mọi mục tiêu/giọng/độ dài, sửa nháp, quay lại; double-click xác nhận | Nội dung hợp lý; không gửi thật; sau fix BUG-002 không ghi trùng | Chưa kiểm tra |
| MAN-10 | Follow-up dùng console email: bấm gửi liên tiếp, mở link, trả lời và refresh | Sau fix BUG-003 không gửi trùng; trả lời một lần; lỗi/hết hạn rõ ràng | Chưa kiểm tra |
| MAN-11 | Wagtail 5 Snippet: tạo/sửa/tìm/lọc/xem; xóa bản ghi giả bằng Quản lý | Dữ liệu và thông báo đúng; Nhân viên không được xóa; xác nhận trước xóa | Chưa kiểm tra |
| MAN-12 | Wagtail Pages: sửa nội dung, preview, publish và mở landing | Nội dung đúng bản publish; form tư vấn vẫn hoạt động | Chưa kiểm tra |
| MAN-13 | Export CSV từ Khách hàng và Báo cáo rồi mở Excel | Dấu tiếng Việt/cột đúng; lọc đúng; sau fix BUG-001 số 0 còn nguyên | Chưa kiểm tra |
| MAN-14 | Gemini thật với dữ liệu giả đã consent; thử khi API lỗi | Kết quả/nguồn hợp lệ; lỗi có fallback; không gửi dữ liệu thiếu consent | Chưa kiểm tra |
| MAN-15 | End-to-end trên browser: lead → follow-up → phản hồi → AI → việc → hoàn tất → báo cáo | Dữ liệu nối đúng khách; mọi bước có thông báo và kết quả kiểm chứng | Chưa kiểm tra |
| MAN-16 | Hai tab hoặc request đồng thời gửi cùng form; mô phỏng mạng chậm/mất kết nối | Không lỗi 500; không gửi/log ngoài ý muốn; không mất nội dung chưa lưu | Chưa kiểm tra |

Chưa thực hiện load test, audit dependency, kiểm thử production/SMTP thật hoặc toàn bộ tổ hợp quyền. Link smoke tự động chỉ bao phủ link nội bộ tuyệt đối xuất hiện trên dữ liệu fixture với superuser; không kiểm tra anchor, liên kết ngoài, JavaScript hay mọi bản ghi trong database.
