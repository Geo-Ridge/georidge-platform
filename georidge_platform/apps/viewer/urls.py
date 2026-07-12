from django.urls import path
from . import views

app_name = "viewer"

urlpatterns = [
    path("<int:pk>/view/", views.view_view, name="view"),
    path("<int:pk>/legend/", views.legend_panel, name="legend"),
    path("<int:pk>/layers/", views.layers_panel, name="layers"),
    path("<int:pk>/toolbar/", views.toolbar_panel, name="toolbar"),
    path("<int:pk>/identify/", views.identify_view, name="identify"),
    path("<int:pk>/search/", views.search_view, name="search"),
    path("<int:pk>/wms/", views.wms_proxy_view, name="wms"),
]
