"""
URL chính của ứng dụng:
  /admin/      → Wagtail Admin
  /crm/        → App CRM Frontend (dashboard, detail, analyze)
  /            → Trang landing giới thiệu doanh nghiệp
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from crm import views as crm_views
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

urlpatterns = [
    # Landing page công khai; CRM nội bộ nằm riêng dưới /crm/.
    path("", crm_views.landing_page, name="landing_page"),
    path("chinh-sach-du-lieu/", crm_views.privacy_notice, name="privacy_notice"),

    # Django Admin (phòng hờ)
    path("django-admin/", admin.site.urls),

    # Wagtail Admin chính
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),

    # Khu vực quản lý khách hàng
    path("crm/", include("crm.urls")),

    # Wagtail Page Tree: homepage is routed above for compatibility with the landing form.
    path("pages/", include(wagtail_urls)),
    path("", include(wagtail_urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
