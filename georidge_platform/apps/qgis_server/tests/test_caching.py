"""Unit tests for the WMS GetCapabilities cache (no live QGIS Server)."""

import os
import urllib.error
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from georidge_platform.apps.projects.models import Project
from georidge_platform.apps.qgis_server.services import (
    get_extent_via_server,
    get_layer_extent_via_server,
    get_wms_layer_names,
    get_wms_layer_tree,
    get_wms_layers,
    validate_on_server,
)

CAPABILITIES_XML = """<?xml version="1.0" encoding="UTF-8"?>
<WMS_Capabilities xmlns="http://www.opengis.net/wms">
  <Capability>
    <Layer>
      <Name>root</Name>
      <Title>Root</Title>
      <EX_GeographicBoundingBox>
        <westBoundLongitude>-10</westBoundLongitude>
        <eastBoundLongitude>10</eastBoundLongitude>
        <southBoundLatitude>-5</southBoundLatitude>
        <northBoundLatitude>5</northBoundLatitude>
      </EX_GeographicBoundingBox>
      <Layer queryable="1">
        <Name>points</Name>
        <Title>Points</Title>
        <EX_GeographicBoundingBox>
          <westBoundLongitude>-10</westBoundLongitude>
          <eastBoundLongitude>10</eastBoundLongitude>
          <southBoundLatitude>-5</southBoundLatitude>
          <northBoundLatitude>5</northBoundLatitude>
        </EX_GeographicBoundingBox>
      </Layer>
    </Layer>
  </Capability>
</WMS_Capabilities>
"""

URLOPEN = "georidge_platform.apps.qgis_server.services.urllib.request.urlopen"


class FakeResponse:
    """Minimal context-manager response for urllib.request.urlopen."""

    def __init__(self, body):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._body


class CapabilitiesCacheTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        self.project = Project.objects.create(
            name="Cache test",
            owner=self.user,
            file=SimpleUploadedFile("cache.qgz", b"fake qgz"),
        )

    def tearDown(self):
        cache.clear()

    def _patch_urlopen(self, body=CAPABILITIES_XML):
        return mock.patch(URLOPEN, return_value=FakeResponse(body.encode()))

    def test_repeated_calls_within_ttl_fetch_once(self):
        with self._patch_urlopen() as mock_urlopen:
            self.assertEqual(get_wms_layer_names(self.project), ["points"])
            self.assertEqual(get_wms_layer_names(self.project), ["points"])
            self.assertEqual(get_wms_layer_names(self.project), ["points"])
        self.assertEqual(mock_urlopen.call_count, 1)

    def test_all_read_functions_share_one_fetch(self):
        with self._patch_urlopen() as mock_urlopen:
            get_wms_layer_names(self.project)
            get_wms_layer_tree(self.project)
            get_wms_layers(self.project)
            extent = get_extent_via_server(self.project)
            layer_extent = get_layer_extent_via_server(self.project, "points")
        self.assertEqual(mock_urlopen.call_count, 1)
        # -10 deg longitude in web mercator
        self.assertAlmostEqual(extent[0], -1113194.9078, places=0)
        self.assertAlmostEqual(layer_extent[0], -1113194.9078, places=0)

    def test_file_change_invalidates_cache(self):
        with self._patch_urlopen() as mock_urlopen:
            self.assertEqual(get_wms_layer_names(self.project), ["points"])
            # Simulate a .qgz replacement: rewrite the file with new content
            # (different size) and a bumped mtime. No DB save, so no signals.
            path = self.project.file.path
            with open(path, "wb") as fh:
                fh.write(b"a different, longer qgz payload")
            st = os.stat(path)
            os.utime(path, (st.st_atime + 5, st.st_mtime + 5))
            self.assertEqual(get_wms_layer_names(self.project), ["points"])
        self.assertEqual(mock_urlopen.call_count, 2)

    @override_settings(QGIS_CAPABILITIES_CACHE_TTL=0)
    def test_zero_ttl_disables_caching(self):
        with self._patch_urlopen() as mock_urlopen:
            get_wms_layer_names(self.project)
            get_wms_layer_names(self.project)
        self.assertEqual(mock_urlopen.call_count, 2)

    def test_failure_is_not_cached(self):
        with mock.patch(URLOPEN, side_effect=urllib.error.URLError("boom")):
            self.assertEqual(get_wms_layer_names(self.project), [])
        # Once the server is back, the next call must fetch again rather than
        # serve a cached failure.
        with self._patch_urlopen() as mock_urlopen:
            self.assertEqual(get_wms_layer_names(self.project), ["points"])
        self.assertEqual(mock_urlopen.call_count, 1)

    def test_validate_on_server_remains_live(self):
        # Validation/status must reflect live state — deliberately uncached.
        with self._patch_urlopen() as mock_urlopen:
            validate_on_server(self.project)
            validate_on_server(self.project)
        self.assertEqual(mock_urlopen.call_count, 2)
