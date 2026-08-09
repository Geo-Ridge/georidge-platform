import uuid

from django.conf import settings
from django.db import models
from georidge_platform.apps.accounts.models import Tenant


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

    # Legal status transitions for the project workflow. The status field can
    # only move between these states; every caller must go through
    # transition_to() (or a service that uses it).
    ALLOWED_TRANSITIONS = {
        Status.DRAFT: {Status.VALIDATING, Status.DRAFT},
        Status.VALIDATING: {Status.READY, Status.FAILED, Status.DRAFT},
        Status.READY: {Status.PUBLISHED, Status.DRAFT},
        Status.PUBLISHED: {Status.ARCHIVED, Status.DRAFT},
        Status.ARCHIVED: {Status.READY, Status.DRAFT},
        Status.FAILED: {Status.VALIDATING, Status.DRAFT},
    }

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def transition_to(self, new_status):
        """Move the project to a new status, enforcing the workflow rules.

        Raises ValueError if the transition is not allowed from the current
        status. Persists immediately; callers that update other fields at the
        same time should save again (or rely on this save).
        """
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition from {self.get_status_display()} to "
                f"{dict(Project.Status.choices).get(new_status, new_status)}"
            )
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])

    def __str__(self):
        return self.name
