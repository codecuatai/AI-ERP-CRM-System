from django.core.management.base import BaseCommand
from wagtail.models import Page, Site

from crm.models import LandingPage


class Command(BaseCommand):
    help = "Tạo trang chủ Wagtail mẫu và gán làm trang chủ của Site mặc định."

    def handle(self, *args, **options):
        root = Page.get_first_root_node()
        homepage = LandingPage.objects.filter(slug="trang-chu-doanh-nghiep").first()
        if homepage is None:
            homepage = LandingPage(
                title="Trang chủ doanh nghiệp",
                slug="trang-chu-doanh-nghiep",
                hero_title="Công nghệ nên giúp công việc",
                hero_emphasis="trôi chảy hơn.",
                hero_text="Kết nối quy trình bán hàng, quản lý vận hành và dữ liệu trên những giải pháp phù hợp với cách doanh nghiệp bạn đang làm việc.",
                solutions_heading="Những mảnh ghép cho một vận hành gọn hơn.",
                solutions_intro="Không phải doanh nghiệp nào cũng cần cùng một bộ công cụ. Hãy bắt đầu từ điểm nghẽn đang làm đội ngũ mất thời gian nhất.",
                approach_heading="Bắt đầu từ bài toán. Không bắt đầu từ phần mềm.",
                approach_intro="Một giải pháp có ích phải phù hợp với con người và quy trình sử dụng nó.",
                contact_heading="Chia sẻ điều bạn muốn cải thiện.",
                contact_intro="Chọn nhóm giải pháp và chia sẻ nhu cầu. Đội ngũ sẽ xem xét yêu cầu, sau đó liên hệ để trao đổi bước tiếp theo.",
                solutions=[
                    {"type": "solution", "value": {"icon": "♙", "category": "01 / KHÁCH HÀNG", "title": "CRM & chăm sóc khách hàng", "description": "Quản lý đầu mối, lịch sử tư vấn và cơ hội bán hàng trong một hồ sơ dễ theo dõi.", "link_label": "Trao đổi về CRM"}},
                    {"type": "solution", "value": {"icon": "▤", "category": "02 / VẬN HÀNH", "title": "Quản lý kho & bán hàng", "description": "Kết nối luồng bán hàng với hàng hóa để đội ngũ nắm thông tin nhất quán hơn.", "link_label": "Trao đổi về vận hành"}},
                    {"type": "solution", "value": {"icon": "⌘", "category": "03 / HẠ TẦNG", "title": "Máy chủ & sao lưu dữ liệu", "description": "Rà soát nền tảng lưu trữ, sao lưu và hạ tầng phù hợp với nhu cầu doanh nghiệp.", "link_label": "Trao đổi về hạ tầng"}},
                    {"type": "solution", "value": {"icon": "⤳", "category": "04 / TÍCH HỢP", "title": "Kết nối các hệ thống", "description": "Giảm nhập liệu lặp lại bằng cách xem xét cách các công cụ hiện tại trao đổi dữ liệu.", "link_label": "Trao đổi về tích hợp"}},
                ],
                approach_steps=[
                    {"type": "step", "value": {"title": "Lắng nghe hiện trạng", "description": "Tìm hiểu cách đội ngũ đang làm việc và điều gì cần được cải thiện trước."}},
                    {"type": "step", "value": {"title": "Đề xuất hướng phù hợp", "description": "Thảo luận lựa chọn, phạm vi và các hệ thống cần phối hợp với nhau."}},
                    {"type": "step", "value": {"title": "Triển khai có đồng hành", "description": "Thống nhất cách đưa giải pháp vào quy trình và hỗ trợ đội ngũ tiếp nhận."}},
                ],
            )
            root.add_child(instance=homepage)
            homepage.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("Created and published the sample Wagtail homepage."))
        site = Site.objects.filter(is_default_site=True).first()
        if site is None:
            site = Site.objects.order_by("pk").first()
        if site is None:
            Site.objects.create(hostname="localhost", port=8000, root_page=homepage, is_default_site=True)
        elif site.root_page_id != homepage.pk:
            site.root_page = homepage
            site.save(update_fields=["root_page"])
        self.stdout.write(self.style.SUCCESS("Assigned the default Wagtail Site homepage."))
