from django.test import TestCase
from django.urls import reverse
from georidge_platform.apps.accounts.models import User
from georidge_platform.apps.projects.models import Project


class RolePermissionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", password="testpass123",
            role=User.Role.ADMIN, is_staff=True,
        )
        self.publisher = User.objects.create_user(
            email="publisher@example.com", password="testpass123",
            role=User.Role.PUBLISHER,
        )
        self.editor = User.objects.create_user(
            email="editor@example.com", password="testpass123",
            role=User.Role.EDITOR,
        )
        self.viewer = User.objects.create_user(
            email="viewer@example.com", password="testpass123",
            role=User.Role.VIEWER,
        )
        self.project = Project.objects.create(
            name="Test Project",
            owner=self.publisher,
            file="projects/test.qgz",
            status=Project.Status.PUBLISHED,
        )

    def _login(self, user):
        self.client.login(email=user.email, password="testpass123")

    def test_admin_can_access_audit(self):
        self._login(self.admin)
        resp = self.client.get(reverse("audit:list"))
        self.assertEqual(resp.status_code, 200)

    def test_non_admin_cannot_access_audit(self):
        for user in [self.publisher, self.editor, self.viewer]:
            self._login(user)
            resp = self.client.get(reverse("audit:list"))
            self.assertEqual(resp.status_code, 302)

    def test_admin_can_access_monitoring(self):
        self._login(self.admin)
        resp = self.client.get(reverse("monitoring:index"))
        self.assertEqual(resp.status_code, 200)

    def test_publisher_can_unpublish(self):
        self._login(self.publisher)
        self.project.status = Project.Status.PUBLISHED
        self.project.published_by = self.publisher
        self.project.published_version = 1
        self.project.save(update_fields=[
            "status", "published_by", "published_version",
        ])
        resp = self.client.post(
            reverse("projects:unpublish", args=[self.project.pk]),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 200)

    def test_editor_cannot_publish(self):
        self._login(self.editor)
        resp = self.client.post(
            reverse("projects:publish", args=[self.project.pk]),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 403)
