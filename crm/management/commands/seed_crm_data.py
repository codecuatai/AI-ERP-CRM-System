"""Tạo dữ liệu khách hàng mẫu cho CRM doanh nghiệp chuyển đổi số.
- Tạo khách hàng mẫu ở nhiều phân khúc
- Tạo lịch sử tương tác (email, phone, meeting)
- Tạo sẵn 2 bản ghi phân tích để minh họa giao diện ngay khi khởi động
"""
from django.core.management.base import BaseCommand
from crm.models import Customer, Interaction, AIAnalysis


class Command(BaseCommand):
    help = "Tạo dữ liệu mẫu nhanh cho buổi demo CRM chuyển đổi số (không tạo tài khoản đăng nhập)"

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

        count_c = 0
        count_i = 0
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
                Interaction.objects.get_or_create(
                    customer=cust,
                    subject=subject,
                    defaults={"kind": kind, "content": content}
                )
                count_i += 1

            if s["analysis"] and not cust.ai_analyses.exists():
                AIAnalysis.objects.create(customer=cust, **s["analysis"])

        self.stdout.write(self.style.SUCCESS(
            f"Thành công! Đã tạo {count_c} khách hàng mới và {count_i} tương tác."
        ))
        self.stdout.write(self.style.SUCCESS(
            "Có sẵn 4 khách hàng chưa phân tích để bạn trình diễn nút 'Phân tích bằng AI'!"
        ))
