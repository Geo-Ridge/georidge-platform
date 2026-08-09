from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "georidge_platform.apps.projects"
    label = "projects"

    def ready(self):
        import georidge_platform.apps.projects.signals  # noqa: F401
