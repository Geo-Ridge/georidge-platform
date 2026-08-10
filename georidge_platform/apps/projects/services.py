from django.conf import settings
from django.utils import timezone

from georidge_platform.apps.audit.models import AuditLog
from georidge_platform.apps.audit.services import log_action
from georidge_platform.apps.qgis_server.services import remap_map_path

from .models import Project

# Statuses a project may be re-validated from (Validate button visibility).
VALIDATE_STATUSES = frozenset({Project.Status.DRAFT, Project.Status.FAILED})


def action_perms(user, project):
    """Actions a user may take on a project, from role + current status.

    Drives the workflow buttons in the UI; views still enforce the same rules
    server-side as a second layer of protection.
    """
    is_owner = project.owner_id == user.id
    can_upload = user.can_upload()
    can_publish = user.can_publish()
    return {
        "can_validate": (is_owner or can_upload) and project.status in VALIDATE_STATUSES,
        "can_publish": can_publish and project.status == Project.Status.READY,
        "can_unpublish": can_publish and project.status == Project.Status.PUBLISHED,
        "can_reactivate": can_publish and project.status == Project.Status.ARCHIVED,
        "can_replace": is_owner or can_upload,
        "can_delete": is_owner or user.is_superuser,
    }


def project_history(project, limit=25):
    """Most recent audit entries for a project (workflow history)."""
    return AuditLog.objects.filter(project=project)[:limit]


def generate_service_urls(project):
    map_path = remap_map_path(project.file.path.replace("\\", "/"))
    base = settings.QGIS_SERVER_URL.rstrip("/")
    return {
        "wms_url": f"{base}?MAP={map_path}",
        "wfs_url": f"{base}?MAP={map_path}",
        "wmts_url": f"{base}?MAP={map_path}",
        "capabilities_url": f"{base}?MAP={map_path}&SERVICE=WMS&REQUEST=GetCapabilities",
    }


def publish_project(project, user):
    if project.status != project.Status.READY:
        raise ValueError("Must validate before publishing")
    urls = generate_service_urls(project)
    project.published_by = user
    project.published_at = timezone.now()
    project.published_version = project.version
    project.transition_to(project.Status.PUBLISHED)
    project.save(update_fields=[
        "published_by", "published_at", "published_version",
    ])
    log_action(user, "publish_completed", project=project,
               details={"from": "Ready", "to": "Published", "version": project.version})
    return urls


def unpublish_project(project, user):
    old_status = project.status
    project.published_by = None
    project.published_at = None
    project.published_version = None
    project.transition_to(project.Status.ARCHIVED)
    project.save(update_fields=[
        "published_by", "published_at", "published_version",
    ])
    log_action(user, "unpublish", project=project,
               details={"from": old_status, "to": "Archived"})


def reactivate_project(project, user):
    """Bring an archived project back to Ready (no re-validation required)."""
    old_status = project.status
    project.transition_to(project.Status.READY)
    log_action(user, "reactivate", project=project,
               details={"from": old_status, "to": "Ready"})
