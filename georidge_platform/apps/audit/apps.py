from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "georidge_platform.apps.audit"
    label = "audit"

    def ready(self):
        import georidge_platform.apps.audit.signals  # noqa: F401
