import io
import tempfile
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse
from georidge_platform.apps.accounts.models import Tenant, User
from georidge_platform.apps.audit.models import AuditLog
from georidge_platform.apps.projects.models import Project
from georidge_platform.apps.projects.services import publish_project
from georidge_platform.apps.validation.services import ValidationReport

TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class WorkflowTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Co", slug="test")
        self.publisher = User.objects.create_user(
            email="publisher@example.com",
            password="testpass123",
            role=User.Role.PUBLISHER,
            tenant=self.tenant,
        )
        self.viewer = User.objects.create_user(
            email="viewer@example.com",
            password="testpass123",
            role=User.Role.VIEWER,
            tenant=self.tenant,
        )
        self.editor = User.objects.create_user(
            email="editor@example.com",
            password="testpass123",
            role=User.Role.EDITOR,
            tenant=self.tenant,
        )
        # The TenancyMiddleware requires a tenant slug prefix on every path.
        self.tenant_base = f"/{self.tenant.slug}"

    def _url(self, name, *args):
        return self.tenant_base + reverse(name, args=args)

    def _login(self, user):
        self.client.login(email=user.email, password="testpass123")

    def _create_qgz(self, name="test.qgz"):
        f = io.BytesIO(b"mock qgz content")
        f.name = name
        return f

    def _create_project(self, status=Project.Status.DRAFT):
        self._login(self.publisher)
        qgz = self._create_qgz()
        self.client.post(self._url("projects:upload"), {
            "name": "Test Project",
            "file": qgz,
        })
        project = Project.objects.first()
        project.status = status
        project.save(update_fields=["status"])
        return project

    def test_upload_creates_draft(self):
        self._login(self.publisher)
        qgz = self._create_qgz()
        resp = self.client.post(self._url("projects:upload"), {
            "name": "Test Project",
            "file": qgz,
        })
        self.assertEqual(resp.status_code, 302)
        project = Project.objects.first()
        self.assertIsNotNone(project)
        self.assertEqual(project.status, Project.Status.DRAFT)
        self.assertEqual(project.tenant_id, self.tenant.id)

    def test_non_qgz_rejected(self):
        self._login(self.publisher)
        bad_file = self._create_qgz("test.txt")
        resp = self.client.post(self._url("projects:upload"), {
            "name": "Bad Project",
            "file": bad_file,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, ".qgz or .zip")

    def test_dashboard_requires_login(self):
        resp = self.client.get(self._url("projects:list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    def test_project_list_filters(self):
        self._login(self.publisher)
        qgz = self._create_qgz()
        self.client.post(self._url("projects:upload"), {
            "name": "Project A",
            "file": qgz,
        })
        resp = self.client.get(self._url("projects:list") + "?status=Draft")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Project A")

    def test_owner_can_delete(self):
        self._login(self.publisher)
        qgz = self._create_qgz()
        self.client.post(self._url("projects:upload"), {
            "name": "Deletable",
            "file": qgz,
        })
        project = Project.objects.first()
        self.assertIsNotNone(project)
        resp = self.client.post(self._url("projects:delete", project.pk))
        self.assertRedirects(resp, self._url("projects:list"))
        self.assertEqual(Project.objects.count(), 0)

    def test_non_owner_cannot_delete(self):
        self._login(self.publisher)
        qgz = self._create_qgz()
        self.client.post(self._url("projects:upload"), {
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
            tenant=self.tenant,
        )
        self.client.login(email=other.email, password="testpass123")
        resp = self.client.post(self._url("projects:delete", project.pk))
        self.assertEqual(resp.status_code, 403)

    def test_publish_requires_validation(self):
        self._login(self.publisher)
        qgz = self._create_qgz()
        self.client.post(self._url("projects:upload"), {
            "name": "Unvalidated",
            "file": qgz,
        })
        project = Project.objects.first()
        self.assertIsNotNone(project)
        resp = self.client.post(
            self._url("projects:publish", project.pk),
            HTTP_HX_REQUEST="true",
        )
        self.assertContains(resp, "Must validate before publishing")

    def test_role_enforcement_publish(self):
        self._login(self.editor)
        qgz = self._create_qgz()
        self.client.post(self._url("projects:upload"), {
            "name": "Editor Project",
            "file": qgz,
        })
        project = Project.objects.first()
        self.assertIsNotNone(project)
        resp = self.client.post(self._url("projects:publish", project.pk))
        self.assertEqual(resp.status_code, 403)

    # ---- Status workflow: transition rules ----

    def test_transition_rules_enforced(self):
        project = self._create_project()
        # Draft -> Published is illegal; Draft -> Validating -> Ready -> Published is legal.
        with self.assertRaises(ValueError):
            project.transition_to(Project.Status.PUBLISHED)
        project.transition_to(Project.Status.VALIDATING)
        project.transition_to(Project.Status.READY)
        project.transition_to(Project.Status.PUBLISHED)
        with self.assertRaises(ValueError):
            project.transition_to(Project.Status.READY)  # Published -> Ready illegal
        project.transition_to(Project.Status.ARCHIVED)
        project.transition_to(Project.Status.READY)  # Archived -> Ready (re-activate)
        project.transition_to(Project.Status.DRAFT)  # new file resets to Draft

    def test_validation_sets_validating_then_ready_and_logs(self):
        project = self._create_project()
        with mock.patch("georidge_platform.apps.validation.views.validate_project") as m:
            m.return_value = ValidationReport(valid=True, layer_count=3)
            resp = self.client.post(
                self._url("validation:validate", project.pk),
                HTTP_HX_REQUEST="true",
            )
        self.assertEqual(resp.status_code, 200)
        project.refresh_from_db()
        self.assertEqual(project.status, Project.Status.READY)
        actions = list(AuditLog.objects.filter(project=project).values_list("action", flat=True))
        self.assertIn("validation_started", actions)
        self.assertIn("validation_completed", actions)

    def test_validation_failed_status_and_role_denied(self):
        project = self._create_project()
        with mock.patch("georidge_platform.apps.validation.views.validate_project") as m:
            m.return_value = ValidationReport(valid=False, errors=["Layer(s) not valid"])
            resp = self.client.post(self._url("validation:validate", project.pk))
        self.assertEqual(resp.status_code, 200)
        project.refresh_from_db()
        self.assertEqual(project.status, Project.Status.FAILED)
        # Failed -> re-validate is legal; Viewer cannot validate.
        self.client.logout()
        self._login(self.viewer)
        resp = self.client.post(self._url("validation:validate", project.pk))
        self.assertEqual(resp.status_code, 403)

    def test_reactivate_archived_to_ready(self):
        project = self._create_project(status=Project.Status.ARCHIVED)
        self.client.logout()
        self._login(self.editor)
        resp = self.client.post(self._url("projects:reactivate", project.pk))
        self.assertEqual(resp.status_code, 403)
        self.client.logout()
        self._login(self.publisher)
        resp = self.client.post(self._url("projects:reactivate", project.pk))
        self.assertEqual(resp.status_code, 200)
        project.refresh_from_db()
        self.assertEqual(project.status, Project.Status.READY)
        self.assertTrue(AuditLog.objects.filter(project=project, action="reactivate").exists())

    def test_publish_logs_history_with_from_to(self):
        project = self._create_project(status=Project.Status.READY)
        publish_project(project, self.publisher)
        entry = AuditLog.objects.get(project=project, action="publish_completed")
        self.assertEqual(entry.details.get("from"), "Ready")
        self.assertEqual(entry.details.get("to"), "Published")

    def test_detail_page_shows_history_and_status(self):
        project = self._create_project(status=Project.Status.READY)
        publish_project(project, self.publisher)
        resp = self.client.get(self._url("projects:detail", project.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Status history")
        self.assertContains(resp, "Publish Completed")  # action_label filter

    # ---- Status workflow: viewer access + preview banner ----

    def test_viewer_redirects_anonymous_to_login_on_non_published(self):
        project = self._create_project(status=Project.Status.DRAFT)
        self.client.logout()
        resp = self.client.get(self._url("viewer:view", project.pk))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)
        # After login the same URL serves the preview with a banner.
        self._login(self.viewer)
        resp = self.client.get(self._url("viewer:view", project.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Draft for testing only")

    def test_viewer_allows_any_logged_in_user_on_draft_with_banner(self):
        project = self._create_project(status=Project.Status.DRAFT)
        self.client.logout()
        self._login(self.viewer)
        resp = self.client.get(self._url("viewer:view", project.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Draft for testing only")

    def test_viewer_public_when_published_no_banner(self):
        project = self._create_project(status=Project.Status.READY)
        publish_project(project, self.publisher)
        self.client.logout()
        resp = self.client.get(self._url("viewer:view", project.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "Draft for testing only")

    def test_wms_proxy_gated_for_anonymous(self):
        project = self._create_project(status=Project.Status.DRAFT)
        self.client.logout()
        resp = self.client.get(self._url("viewer:wms", project.pk), {"REQUEST": "GetCapabilities"})
        self.assertEqual(resp.status_code, 403)

    # ---- Status workflow: replace file ----

    def test_replace_file_bumps_version_resets_to_draft(self):
        project = self._create_project(status=Project.Status.READY)
        new_file = self._create_qgz("replacement.qgz")
        resp = self.client.post(self._url("projects:replace", project.pk), {"file": new_file})
        self.assertEqual(resp.status_code, 302)
        project.refresh_from_db()
        self.assertEqual(project.status, Project.Status.DRAFT)
        self.assertEqual(project.version, 2)
        self.assertTrue(AuditLog.objects.filter(project=project, action="file_replaced").exists())

    def test_replace_file_role_denied_for_viewer(self):
        project = self._create_project()
        self.client.logout()
        self._login(self.viewer)
        resp = self.client.post(self._url("projects:replace", project.pk), {"file": self._create_qgz()})
        self.assertEqual(resp.status_code, 403)
