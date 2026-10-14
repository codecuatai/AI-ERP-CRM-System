from django.core.management.base import BaseCommand
from wagtail.models import Page, Site

from crm.models import LandingPage


class Command(BaseCommand):
    help = "Tạo trang chủ Wagtail mẫu và gán làm trang chủ của Site mặc định."

    def handle(self, *args, **options):
        root = Page.get_first_root_node()
        homepage = LandingPage.objects.filter(slug="trang-chu-doanh-nghiep").first() or LandingPage.objects.first()
        created = False
        if homepage is None:
            created = True
            homepage = LandingPage(slug="trang-chu-doanh-nghiep")

        homepage.title = "Trang chủ doanh nghiệp"
        homepage.hero_title = "Nền tảng Quản trị & AI CRM cho"
        homepage.hero_emphasis = "Doanh nghiệp B2B Đột phá"
        homepage.hero_text = "Hợp nhất toàn bộ dữ liệu khách hàng B2B, chuẩn hóa phễu bán hàng và tự động phân tích tiềm năng chốt đơn với Trợ lý AI Gemini thế hệ mới."
        homepage.solutions_heading = "Bộ 4 Giải pháp Công nghệ Chuyển đổi số Toàn diện"
        homepage.solutions_intro = "Từng mảnh ghép công nghệ được thiết kế tương thích cao, giải quyết chính xác bài toán nghẽn vận hành và mở rộng quy mô doanh nghiệp."
        homepage.approach_heading = "Quy trình 4 Bước Triển khai Chặt chẽ & Đo lường được"
        homepage.approach_intro = "Một giải pháp thành công bắt đầu từ sự thấu hiểu quy trình thực tế. DigiFlow đồng hành xuyên suốt từ khảo sát, cấu hình mô phỏng đến đào tạo vận hành."
        homepage.contact_heading = "Sẵn sàng Tăng tốc Vận hành cùng DigiFlow?"
        homepage.contact_intro = "Đăng ký trao đổi nhu cầu ngay hôm nay. Đội ngũ chuyên gia DigiFlow sẽ khảo sát hiện trạng và gửi phương án kiến trúc giải pháp tối ưu trong 24 giờ."
        homepage.solutions = [
            {"type": "solution", "value": {"icon": "👥", "category": "01 · CRM & KHÁCH HÀNG", "title": "CRM & Phân tích Khách hàng AI", "description": "Quản lý 360° hồ sơ B2B, chấm điểm tiềm năng chốt đơn, hàng đợi ưu tiên cho kinh doanh và gợi ý kịch bản chăm sóc thông minh.", "link_label": "Tìm hiểu giải pháp CRM"}},
            {"type": "solution", "value": {"icon": "📦", "category": "02 · QUẢN LÝ KHO & ERP", "title": "Quản lý Kho & Vận hành ERP", "description": "Kiểm soát xuất nhập tồn đa điểm theo thời gian thực, cảnh báo tồn kho an toàn và tối ưu chuỗi cung ứng sản xuất kinh doanh.", "link_label": "Tìm hiểu giải pháp Kho & ERP"}},
            {"type": "solution", "value": {"icon": "💳", "category": "03 · POS & BÁN HÀNG ĐA KÊNH", "title": "POS & Bán hàng Đa kênh", "description": "Tính tiền tốc độ cao, quét mã QR/thẻ ngân hàng tức thời, in hóa đơn điện tử chuẩn thuế và đồng bộ tức thì về kho trung tâm.", "link_label": "Tìm hiểu giải pháp POS"}},
            {"type": "solution", "value": {"icon": "☁️", "category": "04 · HẠ TẦNG & BẢO MẬT", "title": "Hạ tầng Cloud & Sao lưu Dữ liệu", "description": "Triển khai máy chủ đám mây độc lập, sao lưu tự động định kỳ 256-bit và bảo mật dữ liệu theo Nghị định 13.", "link_label": "Tìm hiểu giải pháp Hạ tầng"}},
        ]
        homepage.approach_steps = [
            {"type": "step", "value": {"title": "Khảo sát & Phân tích hiện trạng", "description": "Lắng nghe trực tiếp bài toán vận hành, luồng dữ liệu và điểm nghẽn của doanh nghiệp."}},
            {"type": "step", "value": {"title": "Thiết kế kiến trúc & Demo thực tế", "description": "Xây dựng mô hình luồng dữ liệu, cấu hình mô phỏng CRM/ERP trực quan trên bài toán thật."}},
            {"type": "step", "value": {"title": "Triển khai Docker hóa & Đồng bộ dữ liệu", "description": "Cài đặt máy chủ riêng biệt, chuyển giao dữ liệu an toàn và đào tạo nhân sự sử dụng thành thạo."}},
            {"type": "step", "value": {"title": "AI Đồng hành & Tối ưu hóa liên tục", "description": "Theo dõi tỷ lệ chuyển đổi, tinh chỉnh mô hình chấm điểm AI Gemini và hỗ trợ kỹ thuật 24/7."}},
        ]
        if created:
            root.add_child(instance=homepage)
        homepage.save_revision().publish()
        if created:
            self.stdout.write(self.style.SUCCESS("Created and published the sample Wagtail homepage."))
        else:
            self.stdout.write(self.style.SUCCESS("Updated and published the Wagtail homepage."))
        site = Site.objects.filter(is_default_site=True).first()
        if site is None:
            site = Site.objects.order_by("pk").first()
        if site is None:
            Site.objects.create(hostname="localhost", port=8000, root_page=homepage, is_default_site=True)
        elif site.root_page_id != homepage.pk:
            site.root_page = homepage
            site.save(update_fields=["root_page"])
        self.stdout.write(self.style.SUCCESS("Assigned the default Wagtail Site homepage."))
