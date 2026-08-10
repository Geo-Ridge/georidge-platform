"""Unit tests for search_view's WFS search (QGIS Server call is mocked)."""

import io
import json
import tempfile
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse

from georidge_platform.apps.accounts.models import Tenant, User
from georidge_platform.apps.projects.models import Project
from georidge_platform.apps.viewer.models import LayerSearchConfig

TEMP_MEDIA = tempfile.mkdtemp()

URLOPEN = "georidge_platform.apps.viewer.views.urllib.request.urlopen"


class FakeResponse:
    """Minimal context-manager response for urllib.request.urlopen."""

    def __init__(self, body):
        self._body = body if isinstance(body, bytes) else body.encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class SearchViewTests(TestCase):
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

    def _url(self, name, *args):
        return self.tenant_base + reverse(name, args=args)

    def _create_project_with_config(self, fields=("owner", "address")):
        f = io.BytesIO(b"mock qgz content")
        f.name = "test.qgz"
        self.client.post(self._url("projects:upload"), {"name": "Test Project", "file": f})
        project = Project.objects.first()
        project.status = Project.Status.PUBLISHED
        project.save(update_fields=["status"])
        LayerSearchConfig.objects.create(
            project=project,
            layer_name="roads",
            layer_title="Roads",
            searchable_fields=list(fields),
            active=True,
        )
        return project

    def _patch_urlopen(self, body):
        return mock.patch(URLOPEN, return_value=FakeResponse(body))

    def test_search_sends_post_with_filter_in_body(self):
        # Regression: a GET request overflows the URI limit (HTTP 414) once
        # the OGC filter for a layer with many fields gets large. The search
        # must POST the form-urlencoded params so there is no size limit.
        project = self._create_project_with_config()
        body = json.dumps({"type": "FeatureCollection", "features": []})
        with self._patch_urlopen(body) as m:
            resp = self.client.get(self._url("viewer:search", project.pk), {"q": "main road"})
        self.assertEqual(resp.status_code, 200)
        m.assert_called_once()
        req = m.call_args[0][0]
        self.assertEqual(req.get_method(), "POST")
        # No query string on the URL; everything is in the POST body.
        self.assertNotIn("?", req.full_url)
        sent = req.data.decode("utf-8")
        self.assertIn("SERVICE=WFS", sent)
        self.assertIn("REQUEST=GetFeature", sent)
        self.assertIn("TYPENAME=roads", sent)
        self.assertIn("FILTER=", sent)
        # Limit features server-side so broad matches don't load huge payloads.
        self.assertIn("MAXFEATURES=5", sent)  # cfg.max_results default
        # The filter XML must be single-encoded (no %25 double-encoding).
        self.assertNotIn("%25", sent)
        headers = {k.lower(): v for k, v in req.headers.items()}
        self.assertEqual("application/x-www-form-urlencoded", headers["content-type"])

    def test_search_returns_formatted_results(self):
        project = self._create_project_with_config()
        features = [{
            "type": "Feature",
            "id": "roads.1",
            "properties": {"id": "roads.1", "owner": "Smith", "address": "5 Main St"},
            "geometry": {"type": "Point", "coordinates": [10, 20]},
        }]
        body = json.dumps({"type": "FeatureCollection", "features": features})
        with self._patch_urlopen(body):
            resp = self.client.get(self._url("viewer:search", project.pk), {"q": "smith"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        results = data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["layer"], "roads")
        self.assertEqual(results[0]["label"], "roads.1")  # default {id} template
        self.assertEqual(results[0]["bbox"], [10, 20, 10, 20])

    def test_search_skips_layer_when_wfs_errors(self):
        project = self._create_project_with_config()
        with mock.patch(URLOPEN, side_effect=OSError("connection refused")):
            resp = self.client.get(self._url("viewer:search", project.pk), {"q": "smith"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content), {"results": []})

    def test_search_ignores_inactive_and_empty_configs(self):
        project = self._create_project_with_config()
        LayerSearchConfig.objects.create(
            project=project, layer_name="points", layer_title="Points",
            searchable_fields=["name"], active=False,
        )
        LayerSearchConfig.objects.create(
            project=project, layer_name="labels", layer_title="Labels",
            searchable_fields=[], active=True,
        )
        with self._patch_urlopen(json.dumps({"type": "FeatureCollection", "features": []})) as m:
            resp = self.client.get(self._url("viewer:search", project.pk), {"q": "x"})
        self.assertEqual(resp.status_code, 200)
        req = m.call_args[0][0]
        sent = req.data.decode("utf-8")
        self.assertIn("TYPENAME=roads", sent)
        self.assertNotIn("TYPENAME=points", sent)
        self.assertNotIn("TYPENAME=labels", sent)
