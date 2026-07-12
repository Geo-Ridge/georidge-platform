from django.urls import path
from . import views

app_name = "projects"

urlpatterns = [
    path("", views.list_view, name="list"),
    path("upload/", views.upload, name="upload"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/delete/", views.delete_view, name="delete"),
    path("<int:pk>/publish/", views.publish_view, name="publish"),
    path("<int:pk>/unpublish/", views.unpublish_view, name="unpublish"),
]
