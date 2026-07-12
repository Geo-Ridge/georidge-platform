from django.urls import path
from . import views

app_name = "validation"

urlpatterns = [
    path("projects/<int:pk>/validate/", views.validate_view, name="validate"),
]
