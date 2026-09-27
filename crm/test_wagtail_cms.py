from django.test import TestCase
from django.urls import reverse
from wagtail.models import Page, Site
from wagtail.snippets.models import get_snippet_models

from crm.models import Customer, LandingPage


class WagtailHomepageTests(TestCase):
    def test_crm_snippets_are_registered_with_custom_viewsets(self):
        names = {model.__name__ for model in get_snippet_models()}

        self.assertTrue({"Customer", "Interaction", "LeadRequest", "CareTask", "AIAnalysis"}.issubset(names))
        self.assertEqual(Customer.snippet_viewset.list_display[0], "full_name")

    def test_published_landing_page_renders_on_site_root(self):
        root = Page.get_first_root_node()
        homepage = root.add_child(instance=LandingPage(
            title="Trang chủ kiểm thử",
            slug="trang-chu-kiem-thu",
            hero_title="Quản lý doanh nghiệp tốt hơn",
            hero_emphasis="cùng CRM",
            hero_text="Nội dung được quản lý trong Wagtail.",
            solutions=[{
                "type": "solution",
                "value": {
                    "icon": "✳", "category": "CRM", "title": "Quản lý khách hàng",
                    "description": "Hồ sơ tập trung.", "link_label": "Tìm hiểu",
                },
            }],
        ))
        homepage.save_revision().publish()
        Site.objects.update(hostname="testserver", port=80, root_page=homepage, is_default_site=True)

        response = self.client.get(reverse("landing_page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nội dung được quản lý trong Wagtail.")
        self.assertContains(response, "Quản lý khách hàng")
