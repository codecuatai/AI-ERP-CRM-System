from django.urls import path
from . import views

app_name = "crm"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("customers/<int:pk>/", views.customer_detail, name="customer_detail"),
    path("customers/<int:pk>/analyze/", views.analyze_customer_view, name="analyze_customer"),
]
