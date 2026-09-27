from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from wagtail.models import GroupPagePermission

from crm.models import LandingPage


class Command(BaseCommand):
    help = "Create/update CRM Staff and CRM Manager groups with scoped Wagtail and CRM permissions."

    def handle(self, *args, **options):
        crm_content_types = ContentType.objects.filter(app_label="crm")
        crm_permissions = Permission.objects.filter(content_type__in=crm_content_types)
        staff_permissions = crm_permissions.exclude(codename__startswith="delete_")
        staff_permissions = staff_permissions | Permission.objects.filter(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        manager_permissions = crm_permissions | Permission.objects.filter(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )

        for name, permissions in (
            ("CRM - Nhân viên", staff_permissions),
            ("CRM - Quản lý", manager_permissions),
        ):
            group, _created = Group.objects.get_or_create(name=name)
            group.permissions.set(permissions.distinct())
            homepage = LandingPage.objects.filter(slug="trang-chu-doanh-nghiep").first()
            if homepage:
                for permission_type in ("change", "publish"):
                    page_permission = Permission.objects.get(
                        content_type__app_label="wagtailcore",
                        content_type__model="page",
                        codename=f"{permission_type}_page",
                    )
                    GroupPagePermission.objects.get_or_create(
                        page=homepage, group=group, permission=page_permission
                    )
            label = "CRM staff" if name.endswith("Nhân viên") else "CRM manager"
            self.stdout.write(f"Configured {label} group ({group.permissions.count()} permissions).")
