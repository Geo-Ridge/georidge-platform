from .models import AuditLog


def log_action(user, action, request=None, project=None, details=None):
    ip = None
    if request:
        ip = request.META.get("REMOTE_ADDR")
    AuditLog.objects.create(
        user=user,
        action=action,
        project=project,
        ip_address=ip,
        details=details or {},
    )
