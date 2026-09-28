"""Seed fictional CRM demo records without touching real customer entries.

Creates sample customers, leads with varied AI consent, interactions, analysis
results, and care tasks. All added contact email addresses use the reserved
``.test`` domain and rerunning the command is idempotent.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from crm.models import AIAnalysis, CareTask, Customer, Interaction, LeadRequest


class Command(BaseCommand):
    help = "Tạo dữ liệu mẫu nhanh cho buổi demo CRM chuyển đổi số (không tạo tài khoản đăng nhập)"

    def _additional_customer_samples(self):
        """Create deterministic fictional B2B records for a fuller local demo."""
        solutions = [
            LeadRequest.SolutionInterest.CRM,
            LeadRequest.SolutionInterest.ERP,
            LeadRequest.SolutionInterest.INFRASTRUCTURE,
            LeadRequest.SolutionInterest.INTEGRATION,
            LeadRequest.SolutionInterest.AI,
        ]
        segments = [
            Customer.Segment.VIP,
            Customer.Segment.POTENTIAL,
            Customer.Segment.HIBERNATING,
            Customer.Segment.CHURN_RISK,
            Customer.Segment.UNCLASSIFIED,
        ]
        sources = ["Website", "Hội thảo", "Giới thiệu", "LinkedIn", "Sự kiện demo"]
        statuses = [LeadRequest.Status.NEW, LeadRequest.Status.CONTACTED, LeadRequest.Status.COMPLETED]
        examples = []

        for index in range(1, 25):
            solution = solutions[(index - 1) % len(solutions)]
            solution_label = dict(LeadRequest.SolutionInterest.choices)[solution]
            has_ai_consent = index % 4 != 0
            segment = segments[(index - 1) % len(segments)] if has_ai_consent else Customer.Segment.UNCLASSIFIED
            score = {
                Customer.Segment.VIP: 90,
                Customer.Segment.POTENTIAL: 76,
                Customer.Segment.HIBERNATING: 43,
                Customer.Segment.CHURN_RISK: 31,
                Customer.Segment.UNCLASSIFIED: 0,
            }[segment]
            company = f"Doanh nghiệp mẫu DigiFlow {index:02d}"
            request_text = (
                f"Dữ liệu demo giả lập: doanh nghiệp đang tìm hiểu {solution_label}; "
                "cần tư vấn quy trình, phạm vi triển khai và phương án tích hợp phù hợp."
            )
            examples.append({
                "full_name": f"Khách hàng mẫu {index:02d}",
                "email": f"demo.customer{index:02d}@digiflow.test",
                "phone": f"000000{index:04d}",
                "company": company,
                "source": sources[(index - 1) % len(sources)],
                "total_spent": index * 3_250_000 if index % 3 == 0 else 0,
                "notes": "Dữ liệu giả lập do lệnh seed tạo; không đại diện khách hàng thật.",
                "ai_segment": segment,
                "ai_score": score,
                "solution": solution,
                "lead_status": statuses[(index - 1) % len(statuses)],
                "ai_consent": has_ai_consent,
                "request_text": request_text,
                "interactions": [
                    (
                        "EMAIL",
                        f"Demo {index:02d}: tiếp nhận nhu cầu {solution_label}",
                        f"Đã ghi nhận nhu cầu giả lập của {company}; nhân viên sẽ rà soát phạm vi phù hợp.",
                    ),
                    (
                        "PHONE" if index % 2 else "MEETING",
                        f"Demo {index:02d}: trao đổi bước tiếp theo",
                        "Tình huống minh họa nội bộ; không phải nội dung trao đổi với khách hàng thật.",
                    ),
                ],
                "analysis": {
                    "segment": segment,
                    "score": score,
                    "summary": f"Phân tích minh họa cho nhu cầu {solution_label.lower()} của {company}.",
                    "recommendation": "Nhân viên xác nhận nhu cầu, sau đó lên lịch trao đổi hoặc demo phù hợp.",
                    "provider": "rules",
                } if has_ai_consent else None,
            })

        return examples

    def handle(self, *args, **options):
        # Dữ liệu khách hàng mẫu
        samples = [
            {
                "full_name": "Công ty TNHH Công nghệ Alpha",
                "email": "contact@alpha-tech.vn",
                "phone": "0901234567",
                "company": "Alpha Tech Vietnam",
                "source": "Website",
                "total_spent": 45000000,
                "notes": "Khách hàng doanh nghiệp công nghệ, đã ký 2 hợp đồng dịch vụ lớn.",
                "ai_segment": Customer.Segment.VIP,
                "ai_score": 95,
                "interactions": [
                    ("EMAIL", "Hỏi báo giá nâng cấp máy chủ", "Chúng tôi muốn xin báo giá mở rộng cụm máy chủ và giải pháp backup dự phòng."),
                    ("MEETING", "Họp nghiệm thu giai đoạn 1", "Hai bên thống nhất nghiệm thu triển khai phần mềm quản lý giai đoạn 1 đúng hạn."),
                ],
                "analysis": {
                    "segment": Customer.Segment.VIP,
                    "score": 95,
                    "summary": "Doanh nghiệp giá trị cao, chi tiêu 45 triệu, tần suất tương tác ổn định.",
                    "recommendation": "Duy trì chăm sóc cấp cao, đề xuất gói bảo trì 24/7 và ký hợp đồng bảo dưỡng năm tiếp theo.",
                    "provider": "sample",
                }
            },
            {
                "full_name": "Trần Thị Mai Hương",
                "email": "huong.ttm@saigon-logistics.com",
                "phone": "0912345678",
                "company": "Saigon Logistics",
                "source": "Hội thảo",
                "total_spent": 12000000,
                "notes": "Quan tâm đến giải pháp quản trị kho và theo dõi vận chuyển tự động.",
                "ai_segment": Customer.Segment.POTENTIAL,
                "ai_score": 75,
                "interactions": [
                    ("PHONE", "Tư vấn phần mềm quản lý kho", "Khách hỏi chi phí triển khai hệ thống quét mã vạch cho 3 kho bãi tại TP.HCM."),
                    ("EMAIL", "Gửi tài liệu giải pháp", "Đã gửi bản demo và tài liệu kỹ thuật cho chị Hương xem xét cùng ban giám đốc."),
                ],
                "analysis": {
                    "segment": Customer.Segment.POTENTIAL,
                    "score": 75,
                    "summary": "Nhu cầu rõ ràng về số hóa kho bãi, tương tác tích cực sau hội thảo.",
                    "recommendation": "Lên lịch demo trực tiếp 15 phút với ban điều hành để chốt hợp đồng trong tháng.",
                    "provider": "rules",
                }
            },
            {
                "full_name": "Nguyễn Hoàng Nam",
                "email": "nam.nguyen@gmail.com",
                "phone": "0988776655",
                "company": "Cá nhân",
                "source": "Facebook Ads",
                "total_spent": 2500000,
                "notes": "Khách hàng cá nhân tự doanh, đang tìm hiểu công cụ CRM quản lý đơn hàng.",
                "ai_segment": Customer.Segment.UNCLASSIFIED,
                "ai_score": 0,
                "interactions": [
                    ("EMAIL", "Hỏi bảng giá gói cơ bản", "Mình muốn hỏi gói CRM cho cá nhân 1-2 người dùng giá bao nhiêu/tháng?"),
                ],
                "analysis": None  # Để chưa phân tích cho demo bấm nút!
            },
            {
                "full_name": "Chuỗi Cà phê Ban Mê",
                "email": "cskh@banmecafe.vn",
                "phone": "0933221100",
                "company": "CTCP Cà phê Ban Mê",
                "source": "Giới thiệu",
                "total_spent": 18500000,
                "notes": "Đang mở rộng 5 cửa hàng mới tại miền Trung.",
                "ai_segment": Customer.Segment.UNCLASSIFIED,
                "ai_score": 0,
                "interactions": [
                    ("MEETING", "Khảo sát nhu cầu POS", "Họp khảo sát kết nối hệ thống CRM với phần mềm bán hàng POS hiện tại."),
                    ("PHONE", "Hỏi chính sách đại lý", "Quan tâm mức chiết khấu khi mua bản quyền theo chuỗi trên 10 điểm."),
                ],
                "analysis": None  # Để chưa phân tích cho demo bấm nút!
            },
            {
                "full_name": "Vũ Đình Trọng",
                "email": "trong.vd@gmail.com",
                "phone": "0944556677",
                "company": "Cá nhân",
                "source": "Google",
                "total_spent": 500000,
                "notes": "Từng khiếu nại về tốc độ phản hồi hỗ trợ kỹ thuật chậm trễ.",
                "ai_segment": Customer.Segment.UNCLASSIFIED,
                "ai_score": 0,
                "interactions": [
                    ("EMAIL", "Phàn nàn về lỗi đồng bộ dữ liệu", "Hệ thống bị treo khi xuất báo cáo, tôi gửi ticket 3 ngày chưa thấy ai trả lời."),
                    ("PHONE", "Gọi điện bức xúc", "Khách gọi lên hotline bày tỏ không hài lòng về dịch vụ hỗ trợ."),
                ],
                "analysis": None  # Để chưa phân tích cho demo bấm nút!
            },
            {
                "full_name": "Công ty CP Dược phẩm Đại Nam",
                "email": "info@dainam-pharma.vn",
                "phone": "0909998877",
                "company": "Dược phẩm Đại Nam",
                "source": "Website",
                "total_spent": 28000000,
                "notes": "Doanh nghiệp phân phối dược, yêu cầu bảo mật thông tin cao.",
                "ai_segment": Customer.Segment.UNCLASSIFIED,
                "ai_score": 0,
                "interactions": [
                    ("EMAIL", "Yêu cầu hợp đồng SLA và cam kết bảo mật", "Gửi bản dự thảo thỏa thuận bảo mật NDA trước khi tích hợp hệ thống."),
                ],
                "analysis": None
            },
        ]

        additional_samples = self._additional_customer_samples()
        samples.extend(additional_samples)

        count_c = 0
        count_i = 0
        count_l = 0
        count_a = 0
        count_t = 0
        for s in samples:
            cust, created = Customer.objects.get_or_create(
                email=s["email"],
                defaults={
                    "full_name": s["full_name"],
                    "phone": s["phone"],
                    "company": s["company"],
                    "source": s["source"],
                    "notes": s["notes"],
                    "total_spent": s["total_spent"],
                    "ai_segment": s["ai_segment"],
                    "ai_score": s["ai_score"],
                }
            )
            if created:
                count_c += 1

            for kind, subject, content in s["interactions"]:
                _, interaction_created = Interaction.objects.get_or_create(
                    customer=cust,
                    subject=subject,
                    defaults={"kind": kind, "content": content}
                )
                count_i += int(interaction_created)

            if "request_text" in s:
                _, lead_created = LeadRequest.objects.get_or_create(
                    customer=cust,
                    request_text=s["request_text"],
                    defaults={
                        "solution_interest": s["solution"],
                        "status": s["lead_status"],
                        "ai_processing_consent": s["ai_consent"],
                        "ai_processing_consent_at": timezone.now() if s["ai_consent"] else None,
                    },
                )
                count_l += int(lead_created)

            if s["analysis"] and not cust.ai_analyses.exists():
                AIAnalysis.objects.create(customer=cust, **s["analysis"])
                count_a += 1

        task_samples = [
            ("huong.ttm@saigon-logistics.com", "Gọi trao đổi về demo quản lý kho", "CALL", -2, "HIGH"),
            ("contact@alpha-tech.vn", "Gửi đề xuất bảo trì máy chủ", "QUOTE", 0, "MEDIUM"),
            ("cskh@banmecafe.vn", "Hẹn khảo sát nhu cầu POS", "MEETING", 3, "MEDIUM"),
        ]
        for email, title, kind, days_from_today, priority in task_samples:
            customer = Customer.objects.get(email=email)
            _, task_created = CareTask.objects.get_or_create(
                customer=customer,
                title=title,
                defaults={
                    "kind": kind,
                    "due_at": timezone.localdate() + timedelta(days=days_from_today),
                    "priority": priority,
                    "status": CareTask.Status.TODO,
                    "description": "Việc mẫu để minh họa hộp theo dõi chăm sóc khách hàng.",
                },
            )
            count_t += int(task_created)

        task_statuses = [CareTask.Status.TODO, CareTask.Status.IN_PROGRESS, CareTask.Status.DONE]
        due_offsets = [-8, -2, 0, 1, 5, 12]
        task_kinds = [CareTask.Kind.CALL, CareTask.Kind.MEETING, CareTask.Kind.FOLLOW_UP]
        for index, sample in enumerate(additional_samples, start=1):
            if index % 3 == 0:
                continue
            customer = Customer.objects.get(email=sample["email"])
            status = task_statuses[index % len(task_statuses)]
            title = (
                f"Demo {index:02d}: chăm sóc nhu cầu "
                f"{dict(LeadRequest.SolutionInterest.choices)[sample['solution']]}"
            )
            _, task_created = CareTask.objects.get_or_create(
                customer=customer,
                title=title,
                defaults={
                    "kind": task_kinds[index % len(task_kinds)],
                    "due_at": timezone.localdate() + timedelta(days=due_offsets[index % len(due_offsets)]),
                    "priority": CareTask.Priority.HIGH if index % 4 == 0 else CareTask.Priority.MEDIUM,
                    "status": status,
                    "completed_at": timezone.now() if status == CareTask.Status.DONE else None,
                    "description": "Việc chăm sóc minh họa cho dữ liệu demo giả lập.",
                },
            )
            count_t += int(task_created)

        self.stdout.write(self.style.SUCCESS(
            f"Created {count_c} customers, {count_l} leads, {count_i} interactions, "
            f"{count_a} analyses and {count_t} care tasks."
        ))
        self.stdout.write(self.style.SUCCESS("All added contacts and company details are fictional demo records."))
