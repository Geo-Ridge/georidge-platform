from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .services import log_action
from georidge_platform.apps.core.middleware import get_current_request

User = get_user_model()


def _get_user_and_tenant():
    request = get_current_request()
    user = getattr(request, "user", None) if request else None
    tenant = getattr(request, "tenant", None) if request else None
    return user, tenant


@receiver(post_save, sender="projects.Project")
def log_project_save(sender, instance, created, **kwargs):
    user, tenant = _get_user_and_tenant()
    action = "project_created" if created else "project_updated"
    log_action(user, action, project=instance, tenant=tenant or instance.tenant)


@receiver(post_delete, sender="projects.Project")
def log_project_delete(sender, instance, **kwargs):
    user, tenant = _get_user_and_tenant()
    log_action(user, "project_deleted", project=instance, tenant=tenant or instance.tenant)


@receiver(post_save, sender=User)
def log_user_save(sender, instance, created, **kwargs):
    user, tenant = _get_user_and_tenant()
    action = "user_created" if created else "user_updated"
    log_action(user, action, details={"target_user_id": instance.pk})


@receiver(post_delete, sender=User)
def log_user_delete(sender, instance, **kwargs):
    user, tenant = _get_user_and_tenant()
    log_action(user, "user_deleted", details={"target_user_id": instance.pk})
