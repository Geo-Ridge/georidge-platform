import io
import tempfile
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse

from georidge_platform.apps.accounts.models import Tenant, User
from georidge_platform.apps.projects.models import Project

TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class WmsProxyAllowListTests(TestCase):
    """The WMS proxy must only forward WMS map operations to QGIS Server.

    Everything else (WFS bulk export, WCS, unknown ops, missing params) gets
    a 403 without ever reaching QGIS.
    """

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Co", slug="test")
        self.publisher = User.objects.create_user(
            email="publisher@example.com",
            password="testpass123",
            role=User.Role.PUBLISHER,
            tenant=self.tenant,
        )
        # The TenancyMiddleware requires a tenant slug prefix on every path.
        self.tenant_base = f"/{self.tenant.slug}"
        self.client.login(email=self.publisher.email, password="testpass123")

    def _url(self, name, *args):
        return self.tenant_base + reverse(name, args=args)

    def _create_published_project(self):
        f = io.BytesIO(b"mock qgz content")
        f.name = "test.qgz"
        self.client.post(self._url("projects:upload"), {"name": "Test Project", "file": f})
        project = Project.objects.first()
        project.status = Project.Status.PUBLISHED
        project.save(update_fields=["status"])
        return project

    def _get(self, project, params):
        return self.client.get(self._url("viewer:wms", project.pk), params)

    def _mock_qgis(self, content=b"ok", content_type="image/png"):
        m = mock.patch("georidge_platform.apps.viewer.views.requests.get")
        mock_get = m.start()
        mock_get.return_value.status_code = 200
        mock_get.return_value.headers = {"content-type": content_type, "Content-Length": str(len(content))}
        mock_get.return_value.content = content
        self.addCleanup(m.stop)
        return mock_get

    # ---- Allowed WMS operations forward through ----

    def test_getmap_allowed(self):
        project = self._create_published_project()
        mock_get = self._mock_qgis()
        resp = self._get(project, {
            "SERVICE": "WMS", "REQUEST": "GetMap",
            "LAYERS": "roads", "BBOX": "0,0,1,1", "WIDTH": "256", "HEIGHT": "256",
        })
        self.assertEqual(resp.status_code, 200)
        mock_get.assert_called_once()
        url = mock_get.call_args[0][0]
        self.assertIn("SERVICE=WMS", url)
        self.assertIn("REQUEST=GetMap", url)
        # MAP is always forced to the project file, never attacker-supplied.
        self.assertIn("MAP=", url)

    def test_getlegendgraphic_allowed(self):
        project = self._create_published_project()
        mock_get = self._mock_qgis()
        resp = self._get(project, {"SERVICE": "WMS", "REQUEST": "GetLegendGraphic", "LAYER": "roads"})
        self.assertEqual(resp.status_code, 200)
        mock_get.assert_called_once()

    def test_getfeatureinfo_allowed(self):
        project = self._create_published_project()
        mock_get = self._mock_qgis(content=b"{}", content_type="application/json")
        resp = self._get(project, {"SERVICE": "WMS", "REQUEST": "GetFeatureInfo", "I": "1", "J": "1"})
        self.assertEqual(resp.status_code, 200)
        mock_get.assert_called_once()

    def test_getcapabilities_allowed(self):
        project = self._create_published_project()
        mock_get = self._mock_qgis(content=b"<WMS_Capabilities/>", content_type="text/xml")
        resp = self._get(project, {"SERVICE": "WMS", "REQUEST": "GetCapabilities"})
        self.assertEqual(resp.status_code, 200)
        mock_get.assert_called_once()

    def test_case_insensitive_params_allowed(self):
        project = self._create_published_project()
        mock_get = self._mock_qgis()
        resp = self._get(project, {"service": "wms", "request": "getmap"})
        self.assertEqual(resp.status_code, 200)
        mock_get.assert_called_once()

    # ---- Disallowed operations are blocked before reaching QGIS ----

    def test_wfs_getfeature_blocked(self):
        project = self._create_published_project()
        mock_get = self._mock_qgis()
        resp = self._get(project, {"SERVICE": "WFS", "REQUEST": "GetFeature", "TYPENAME": "roads"})
        self.assertEqual(resp.status_code, 403)
        mock_get.assert_not_called()

    def test_wcs_blocked(self):
        project = self._create_published_project()
        mock_get = self._mock_qgis()
        resp = self._get(project, {"SERVICE": "WCS", "REQUEST": "GetCoverage"})
        self.assertEqual(resp.status_code, 403)
        mock_get.assert_not_called()

    def test_unknown_wms_operation_blocked(self):
        project = self._create_published_project()
        mock_get = self._mock_qgis()
        resp = self._get(project, {"SERVICE": "WMS", "REQUEST": "GetProjectSettings"})
        self.assertEqual(resp.status_code, 403)
        mock_get.assert_not_called()

    def test_missing_service_blocked(self):
        project = self._create_published_project()
        mock_get = self._mock_qgis()
        resp = self._get(project, {"REQUEST": "GetMap"})
        self.assertEqual(resp.status_code, 403)
        mock_get.assert_not_called()

    def test_missing_request_blocked(self):
        project = self._create_published_project()
        mock_get = self._mock_qgis()
        resp = self._get(project, {"SERVICE": "WMS"})
        self.assertEqual(resp.status_code, 403)
        mock_get.assert_not_called()

    def test_attacker_map_param_cannot_override(self):
        project = self._create_published_project()
        mock_get = self._mock_qgis()
        resp = self._get(project, {
            "SERVICE": "WMS", "REQUEST": "GetMap", "MAP": "/etc/passwd",
        })
        self.assertEqual(resp.status_code, 200)
        url = mock_get.call_args[0][0]
        # The forwarded MAP is the project's remapped path, not the attacker's.
        self.assertNotIn("/etc/passwd", url)

    def test_duplicate_service_params_blocked(self):
        # HTTP parameter pollution: QueryDict exposes only the last value, so
        # SERVICE=WMS (allowed) would mask SERVICE=WFS, but urlencode forwards
        # both and QGIS may honor the first. Duplicates are rejected outright.
        project = self._create_published_project()
        mock_get = self._mock_qgis()
        url = self._url("viewer:wms", project.pk)
        resp = self.client.get(
            url + "?SERVICE=WFS&SERVICE=WMS&REQUEST=GetFeature&REQUEST=GetMap"
        )
        self.assertEqual(resp.status_code, 403)
        mock_get.assert_not_called()

    def test_mixed_case_duplicate_service_params_blocked(self):
        project = self._create_published_project()
        mock_get = self._mock_qgis()
        url = self._url("viewer:wms", project.pk)
        resp = self.client.get(url + "?service=wms&SERVICE=WFS&REQUEST=GetMap")
        self.assertEqual(resp.status_code, 403)
        mock_get.assert_not_called()
