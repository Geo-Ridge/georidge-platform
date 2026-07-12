from django.conf import settings
from django.utils import timezone
from georidge_platform.apps.audit.services import log_action


def generate_service_urls(project):
    map_path = project.file.path.replace("\\", "/")
    base = settings.QGIS_SERVER_URL.rstrip("/")
    return {
        "wms_url": f"{base}/?MAP={map_path}",
        "wfs_url": f"{base}/?MAP={map_path}",
        "wmts_url": f"{base}/?MAP={map_path}",
        "capabilities_url": f"{base}/?MAP={map_path}&SERVICE=WMS&REQUEST=GetCapabilities",
    }


def publish_project(project, user):
    if project.status != project.Status.READY:
        raise ValueError("Must validate before publishing")
    urls = generate_service_urls(project)
    project.published_by = user
    project.published_at = timezone.now()
    project.published_version = project.version
    project.status = project.Status.PUBLISHED
    project.save(update_fields=[
        "published_by", "published_at", "published_version", "status",
    ])
    log_action(user, "publish_completed", project=project)
    return urls


def unpublish_project(project, user):
    project.published_by = None
    project.published_at = None
    project.published_version = None
    project.status = project.Status.ARCHIVED
    project.save(update_fields=[
        "published_by", "published_at", "published_version", "status",
    ])
    log_action(user, "unpublish", project=project)
