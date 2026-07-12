import uuid

from django.conf import settings
from django.db import models
from georidge_platform.apps.accounts.models import Tenant


def _sync_search(project):
    try:
        from georidge_platform.apps.viewer.services import sync_search_layers
        sync_search_layers(project)
    except Exception:
        import logging
        logging.getLogger(__name__).warning("sync_search_layers failed for project %s", project.pk)


def project_file_path(instance, filename):
    return f"projects/{instance.pk or uuid.uuid4().hex}/{filename}"


class Project(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="projects",
    )
    theme = models.ForeignKey(
        "viewer.ThemeProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )

    class Status(models.TextChoices):
        DRAFT = "Draft", "Draft"
        VALIDATING = "Validating", "Validating"
        READY = "Ready", "Ready"
        PUBLISHED = "Published", "Published"
        ARCHIVED = "Archived", "Archived"
        FAILED = "Failed", "Failed"

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=project_file_path)
    base_maps = models.ManyToManyField(
        "viewer.BaseMap",
        blank=True,
        help_text="Base maps available for this project. Leave empty to use all active base maps for the tenant.",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    version = models.IntegerField(default=1)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="published_projects",
    )
    published_at = models.DateTimeField(null=True, blank=True)
    published_version = models.IntegerField(null=True, blank=True)
    extent_min_x = models.FloatField(null=True, blank=True)
    extent_min_y = models.FloatField(null=True, blank=True)
    extent_max_x = models.FloatField(null=True, blank=True)
    extent_max_y = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
