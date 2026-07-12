from django import template

from georidge_platform.apps.accounts.models import User
from georidge_platform.apps.audit.models import AuditLog
from georidge_platform.apps.projects.models import Project
from georidge_platform.apps.qgis_server.services import health_check

register = template.Library()


@register.simple_tag
def get_admin_stats():
    return {
        "total_projects": Project.objects.count(),
        "published_projects": Project.objects.filter(status=Project.Status.PUBLISHED).count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "server_status": health_check(),
        "recent_activity": AuditLog.objects.select_related("user", "project")[:10],
    }
