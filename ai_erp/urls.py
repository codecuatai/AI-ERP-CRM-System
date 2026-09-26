"""
ai_erp/urls.py
Route chính của toàn bộ hệ thống:
  /admin/      → Wagtail Admin
  /crm/        → App CRM Frontend (dashboard, detail, analyze)
  /            → Wagtail Pages (hoặc redirect sang /crm/)
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

urlpatterns = [
    # Trang chủ redirect sang CRM Dashboard
    path("", RedirectView.as_view(url="/crm/", permanent=False), name="home_redirect"),

    # Django Admin (phòng hờ)
    path("django-admin/", admin.site.urls),

    # Wagtail Admin chính
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),

    # App CRM/ERP
    path("crm/", include("crm.urls")),

    # Wagtail Page Tree (luôn để cuối cùng)
    path("pages/", include(wagtail_urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
