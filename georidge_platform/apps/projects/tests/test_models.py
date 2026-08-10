"""Unit tests for the Project status workflow (no QGIS Server required)."""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from georidge_platform.apps.projects.models import Project


class ProjectTransitionTests(TestCase):
    """transition_to() must enforce the allowed-transition graph."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        self.project = Project.objects.create(
            name="Transition test",
            owner=self.user,
            file=SimpleUploadedFile("p.qgz", b"fake qgz data"),
        )

    def _set_status(self, status):
        """Arrange the project at a status directly (bypassing transition_to)."""
        self.project.status = status
        self.project.save(update_fields=["status"])
        self.project.refresh_from_db()

    def test_draft_to_validating(self):
        self.project.transition_to(Project.Status.VALIDATING)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.VALIDATING)

    def test_validating_to_ready(self):
        self.project.transition_to(Project.Status.VALIDATING)
        self.project.transition_to(Project.Status.READY)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.READY)

    def test_validating_to_failed(self):
        self.project.transition_to(Project.Status.VALIDATING)
        self.project.transition_to(Project.Status.FAILED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.FAILED)

    def test_failed_to_validating_revalidation(self):
        self.project.transition_to(Project.Status.VALIDATING)
        self.project.transition_to(Project.Status.FAILED)
        self.project.transition_to(Project.Status.VALIDATING)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.VALIDATING)

    def test_ready_to_published(self):
        self.project.transition_to(Project.Status.VALIDATING)
        self.project.transition_to(Project.Status.READY)
        self.project.transition_to(Project.Status.PUBLISHED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.PUBLISHED)

    def test_published_to_archived(self):
        self.project.transition_to(Project.Status.VALIDATING)
        self.project.transition_to(Project.Status.READY)
        self.project.transition_to(Project.Status.PUBLISHED)
        self.project.transition_to(Project.Status.ARCHIVED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.ARCHIVED)

    def test_archived_to_ready_reactivation(self):
        self.project.transition_to(Project.Status.VALIDATING)
        self.project.transition_to(Project.Status.READY)
        self.project.transition_to(Project.Status.PUBLISHED)
        self.project.transition_to(Project.Status.ARCHIVED)
        self.project.transition_to(Project.Status.READY)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.READY)

    def test_published_to_draft_rollback(self):
        self.project.transition_to(Project.Status.VALIDATING)
        self.project.transition_to(Project.Status.READY)
        self.project.transition_to(Project.Status.PUBLISHED)
        self.project.transition_to(Project.Status.DRAFT)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.DRAFT)

    def test_draft_to_draft_is_noop(self):
        self.project.transition_to(Project.Status.DRAFT)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.DRAFT)

    def test_draft_to_published_raises(self):
        with self.assertRaises(ValueError):
            self.project.transition_to(Project.Status.PUBLISHED)

    def test_validating_to_published_raises(self):
        self._set_status(Project.Status.VALIDATING)
        with self.assertRaises(ValueError):
            self.project.transition_to(Project.Status.PUBLISHED)

    def test_ready_to_archived_raises(self):
        self._set_status(Project.Status.READY)
        with self.assertRaises(ValueError):
            self.project.transition_to(Project.Status.ARCHIVED)

    def test_archived_to_published_raises(self):
        self._set_status(Project.Status.ARCHIVED)
        with self.assertRaises(ValueError):
            self.project.transition_to(Project.Status.PUBLISHED)

    def test_failed_to_published_raises(self):
        self._set_status(Project.Status.FAILED)
        with self.assertRaises(ValueError):
            self.project.transition_to(Project.Status.PUBLISHED)

    def test_invalid_transition_does_not_change_status(self):
        self._set_status(Project.Status.READY)
        with self.assertRaises(ValueError):
            self.project.transition_to(Project.Status.ARCHIVED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.READY)

    def test_error_message_names_both_states(self):
        self._set_status(Project.Status.DRAFT)
        with self.assertRaises(ValueError) as ctx:
            self.project.transition_to(Project.Status.PUBLISHED)
        message = str(ctx.exception)
        self.assertIn("Draft", message)
        self.assertIn("Published", message)
