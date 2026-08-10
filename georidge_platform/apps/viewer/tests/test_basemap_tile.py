"""Unit tests for the base-map tile proxy (upstream fetch is mocked)."""

import io
import tempfile
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse

from georidge_platform.apps.accounts.models import Tenant, User
from georidge_platform.apps.projects.models import Project
from georidge_platform.apps.viewer.models import BaseMap

TEMP_MEDIA = tempfile.mkdtemp()

URLOPEN = "georidge_platform.apps.viewer.views.urllib.request.urlopen"


class FakeResponse:
    def __init__(self, body, content_type="image/png"):
        self._body = body if isinstance(body, bytes) else body.encode()
        self._content_type = content_type

    def read(self):
        return self._body

    @property
    def headers(self):
        class _H:
            def get_content_type(self):
                return self._ct

            _ct = self._content_type

        return _H()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class BaseMapTileViewTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Co", slug="test")
        self.publisher = User.objects.create_user(
            email="publisher@example.com",
            password="testpass123",
            role=User.Role.PUBLISHER,
            tenant=self.tenant,
        )
        self.tenant_base = f"/{self.tenant.slug}"
        self.client.login(email=self.publisher.email, password="testpass123")
        self.osm = BaseMap.objects.create(
            name="OpenStreetMap",
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            is_active=True,
            tenant=None,
        )

    def _url(self, name, *args):
        return self.tenant_base + reverse(name, args=args)

    def _create_project(self, status=Project.Status.PUBLISHED):
        f = io.BytesIO(b"mock qgz content")
        f.name = "test.qgz"
        self.client.post(self._url("projects:upload"), {"name": "Test Project", "file": f})
        project = Project.objects.first()
        project.status = status
        project.save(update_fields=["status"])
        return project

    def test_tile_proxied_with_headers_and_cache(self):
        project = self._create_project()
        body = b"\x89PNG fake tile"
        with mock.patch(URLOPEN, return_value=FakeResponse(body)) as m:
            resp = self.client.get(
                self._url("viewer:basemap-tile", project.pk, self.osm.pk, "5/3/2.png")
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, body)
        self.assertEqual(resp["Content-Type"], "image/png")
        self.assertEqual(resp["Cache-Control"], "public, max-age=86400")
        m.assert_called_once()
        req = m.call_args[0][0]
        self.assertEqual(req.full_url, "https://tile.openstreetmap.org/5/3/2.png")
        headers = {k.lower(): v for k, v in req.headers.items()}
        self.assertIn("GeoRidge", headers["user-agent"])
        self.assertIn("://", headers["referer"])

    def test_bad_tile_path_rejected_before_upstream(self):
        project = self._create_project()
        with mock.patch(URLOPEN) as m:
            resp = self.client.get(
                self._url("viewer:basemap-tile", project.pk, self.osm.pk, "not/a/tile")
            )
        self.assertEqual(resp.status_code, 404)
        m.assert_not_called()

    def test_tile_path_with_extra_segments_rejected(self):
        project = self._create_project()
        with mock.patch(URLOPEN) as m:
            resp = self.client.get(
                self._url("viewer:basemap-tile", project.pk, self.osm.pk, "5/3/2.png/extra")
            )
        self.assertEqual(resp.status_code, 404)
        m.assert_not_called()

    def test_upstream_error_returns_502(self):
        project = self._create_project()
        with mock.patch(URLOPEN, side_effect=OSError("boom")):
            resp = self.client.get(
                self._url("viewer:basemap-tile", project.pk, self.osm.pk, "5/3/2.png")
            )
        self.assertEqual(resp.status_code, 502)

    def test_inactive_base_map_404(self):
        project = self._create_project()
        self.osm.is_active = False
        self.osm.save(update_fields=["is_active"])
        with mock.patch(URLOPEN) as m:
            resp = self.client.get(
                self._url("viewer:basemap-tile", project.pk, self.osm.pk, "5/3/2.png")
            )
        self.assertEqual(resp.status_code, 404)
        m.assert_not_called()

    def test_anonymous_public_project_allowed(self):
        project = self._create_project(status=Project.Status.PUBLISHED)
        self.client.logout()
        with mock.patch(URLOPEN, return_value=FakeResponse(b"x")):
            resp = self.client.get(
                self._url("viewer:basemap-tile", project.pk, self.osm.pk, "5/3/2.png")
            )
        self.assertEqual(resp.status_code, 200)

    def test_anonymous_draft_project_blocked(self):
        project = self._create_project(status=Project.Status.DRAFT)
        self.client.logout()
        with mock.patch(URLOPEN) as m:
            resp = self.client.get(
                self._url("viewer:basemap-tile", project.pk, self.osm.pk, "5/3/2.png")
            )
        self.assertEqual(resp.status_code, 403)
        m.assert_not_called()

    def test_path_subdomain_token_cannot_break_out(self):
        # An {s} placeholder in the template PATH is substituted from the
        # request, so it must not be able to smuggle arbitrary path segments
        # or alter the upstream host (SSRF guard).
        self.osm.url = "https://tile.example.com/tiles/{s}/{z}/{x}/{y}.png"
        self.osm.save(update_fields=["url"])
        project = self._create_project()
        # Non-alphanumeric {s} value -> rejected before any fetch.
        with mock.patch(URLOPEN) as m:
            resp = self.client.get(
                self._url("viewer:basemap-tile", project.pk, self.osm.pk, "tiles/evil.example/5/3/2.png")
            )
        self.assertEqual(resp.status_code, 404)
        m.assert_not_called()
        # A legitimate value still proxies correctly.
        with mock.patch(URLOPEN, return_value=FakeResponse(b"x")) as m:
            resp = self.client.get(
                self._url("viewer:basemap-tile", project.pk, self.osm.pk, "tiles/a/5/3/2.png")
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            m.call_args[0][0].full_url,
            "https://tile.example.com/tiles/a/5/3/2.png",
        )


class XyzTemplateRegexTests(TestCase):
    def test_osm_template(self):
        from georidge_platform.apps.viewer.views import _xyz_template_regex

        regex = _xyz_template_regex("{z}/{x}/{y}.png")
        m = __import__("re").fullmatch(regex, "5/3/2.png")
        self.assertIsNotNone(m)
        self.assertEqual(m.groupdict(), {"z": "5", "x": "3", "y": "2"})
        self.assertIsNone(__import__("re").fullmatch(regex, "a/b.png"))

    def test_esri_template_with_yx_order(self):
        from georidge_platform.apps.viewer.views import _xyz_template_regex

        regex = _xyz_template_regex("MapServer/tile/{z}/{y}/{x}")
        m = __import__("re").fullmatch(regex, "MapServer/tile/5/2/3")
        self.assertIsNotNone(m)
        self.assertEqual(m.groupdict(), {"z": "5", "x": "3", "y": "2"})

    def test_template_with_subdomains(self):
        from georidge_platform.apps.viewer.views import _xyz_template_regex

        regex = _xyz_template_regex("tiles/{z}/{x}/{y}.png")
        m = __import__("re").fullmatch(regex, "tiles/5/3/2.png")
        self.assertIsNotNone(m)
        self.assertEqual(m.groupdict(), {"z": "5", "x": "3", "y": "2"})
