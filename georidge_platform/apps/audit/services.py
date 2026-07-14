from .models import AuditLog


def log_action(user, action, request=None, project=None, details=None, tenant=None):
    ip = None
    if request:
        ip = request.META.get("REMOTE_ADDR")
    if not tenant and project:
        tenant = project.tenant
    AuditLog.objects.create(
        user=user,
        action=action,
        project=project,
        tenant=tenant,
        ip_address=ip,
        details=details or {},
    )
