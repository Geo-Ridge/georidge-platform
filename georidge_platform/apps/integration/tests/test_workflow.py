import io
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings
from django.urls import reverse
from georidge_platform.apps.accounts.models import User
from georidge_platform.apps.projects.models import Project

TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class WorkflowTests(TestCase):
    def setUp(self):
        self.publisher = User.objects.create_user(
            email="publisher@example.com",
            password="testpass123",
            role=User.Role.PUBLISHER,
        )
        self.viewer = User.objects.create_user(
            email="viewer@example.com",
            password="testpass123",
            role=User.Role.VIEWER,
        )
        self.editor = User.objects.create_user(
            email="editor@example.com",
            password="testpass123",
            role=User.Role.EDITOR,
        )

    def _login(self, user):
        self.client.login(email=user.email, password="testpass123")

    def _create_qgz(self, name="test.qgz"):
        f = io.BytesIO(b"mock qgz content")
        f.name = name
        return f

    def test_upload_creates_draft(self):
        self._login(self.publisher)
        qgz = self._create_qgz()
        resp = self.client.post(reverse("projects:upload"), {
            "name": "Test Project",
            "file": qgz,
        })
        self.assertEqual(resp.status_code, 302)
        project = Project.objects.first()
        self.assertIsNotNone(project)
        self.assertEqual(project.status, Project.Status.DRAFT)

    def test_non_qgz_rejected(self):
        self._login(self.publisher)
        bad_file = self._create_qgz("test.txt")
        resp = self.client.post(reverse("projects:upload"), {
            "name": "Bad Project",
            "file": bad_file,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, ".qgz or .zip")

    def test_validation_requires_login(self):
        resp = self.client.get(reverse("dashboard:index"))
        self.assertRedirects(resp, f"{reverse('accounts:login')}?next={reverse('dashboard:index')}")

    def test_project_list_filters(self):
        self._login(self.publisher)
        qgz = self._create_qgz()
        self.client.post(reverse("projects:upload"), {
            "name": "Project A",
            "file": qgz,
        })
        resp = self.client.get(reverse("projects:list") + "?status=Draft")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Project A")

    def test_owner_can_delete(self):
        self._login(self.publisher)
        qgz = self._create_qgz()
        self.client.post(reverse("projects:upload"), {
            "name": "Deletable",
            "file": qgz,
        })
        project = Project.objects.first()
        self.assertIsNotNone(project)
        resp = self.client.post(reverse("projects:delete", args=[project.pk]))
        self.assertRedirects(resp, reverse("projects:list"))
        self.assertEqual(Project.objects.count(), 0)

    def test_non_owner_cannot_delete(self):
        self._login(self.publisher)
        qgz = self._create_qgz()
        self.client.post(reverse("projects:upload"), {
            "name": "Mine",
            "file": qgz,
        })
        project = Project.objects.first()
        self.assertIsNotNone(project)
        self.client.logout()
        other = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            role=User.Role.EDITOR,
        )
        self.client.login(email=other.email, password="testpass123")
        resp = self.client.post(reverse("projects:delete", args=[project.pk]))
        self.assertEqual(resp.status_code, 403)

    def test_publish_requires_validation(self):
        self._login(self.publisher)
        qgz = self._create_qgz()
        self.client.post(reverse("projects:upload"), {
            "name": "Unvalidated",
            "file": qgz,
        })
        project = Project.objects.first()
        self.assertIsNotNone(project)
        resp = self.client.post(
            reverse("projects:publish", args=[project.pk]),
            HTTP_HX_REQUEST="true",
        )
        self.assertContains(resp, "Must validate before publishing")

    def test_role_enforcement_publish(self):
        self._login(self.editor)
        qgz = self._create_qgz()
        self.client.post(reverse("projects:upload"), {
            "name": "Editor Project",
            "file": qgz,
        })
        project = Project.objects.first()
        self.assertIsNotNone(project)
        resp = self.client.post(reverse("projects:publish", args=[project.pk]))
        self.assertEqual(resp.status_code, 403)

