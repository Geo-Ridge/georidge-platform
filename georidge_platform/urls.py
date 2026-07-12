from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


def root_redirect(request):
    return redirect("/admin/")


urlpatterns = [
    path("", root_redirect),
    path("admin/", admin.site.urls),
    path("accounts/", include("georidge_platform.apps.accounts.urls")),

    path("datasources/", include("georidge_platform.apps.datasources.urls")),
    path("projects/", include("georidge_platform.apps.projects.urls")),
    path("", include("georidge_platform.apps.validation.urls")),
    path("qgis-server/", include("georidge_platform.apps.qgis_server.urls")),
    path("viewer/", include("georidge_platform.apps.viewer.urls")),
    path("audit/", include("georidge_platform.apps.audit.urls")),
    path("monitoring/", include("georidge_platform.apps.monitoring.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
