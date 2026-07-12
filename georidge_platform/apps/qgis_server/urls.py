from django.urls import path
from . import views

app_name = "qgis_server"

urlpatterns = [
    path("status/", views.status_view, name="status"),
]
