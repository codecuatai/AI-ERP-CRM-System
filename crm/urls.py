from django.urls import path
from . import views

app_name = "crm"
urlpatterns = [
    path("dang-ky-tu-van/", views.public_lead_request, name="lead_request"),
    path("da-gui-yeu-cau/", views.public_lead_request_success, name="lead_request_success"),
    path("", views.dashboard, name="dashboard"),
    path("customers/", views.customer_list, name="customers"),
    path("customers/<int:pk>/", views.customer_detail, name="customer_detail"),
    path("customers/<int:pk>/analyze/", views.analyze_customer_view, name="analyze_customer"),
    path("yeu-cau/", views.lead_request_list, name="lead_requests"),
    path("yeu-cau/<int:pk>/trang-thai/", views.update_lead_request_status, name="update_lead_request_status"),
    path("yeu-cau/<int:pk>/gui-form-bo-sung/", views.lead_follow_up, name="lead_follow_up"),
    path("yeu-cau/<int:pk>/form-bo-sung/<int:follow_up_id>/thu-hoi/", views.revoke_lead_follow_up, name="revoke_lead_follow_up"),
    path("bo-sung-thong-tin/<str:token>/", views.lead_follow_up_reply, name="lead_follow_up_reply"),
]
