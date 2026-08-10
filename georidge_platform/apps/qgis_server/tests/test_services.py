"""Unit tests for qgis_server service helpers (no live QGIS Server needed)."""

import io
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings

from georidge_platform.apps.projects.models import Project
from georidge_platform.apps.qgis_server.services import (
    _extent_from_wms_layer,
    _find_text,
    _wgs84_to_web_mercator,
    get_print_layouts,
    remap_map_path,
)

WMS_NS = "http://www.opengis.net/wms"

TEMP_MEDIA = tempfile.mkdtemp()


class RemapMapPathTests(SimpleTestCase):
    @override_settings(QGIS_SERVER_MAP_PATH_PREFIX="")
    def test_no_prefix_returns_path_unchanged(self):
        self.assertEqual(remap_map_path("/app/media/projects/5/a.qgz"), "/app/media/projects/5/a.qgz")

    @override_settings(QGIS_SERVER_MAP_PATH_PREFIX="/var/www/qgis-server/media")
    def test_prefix_rewrites_app_media_root(self):
        self.assertEqual(
            remap_map_path("/app/media/projects/5/a.qgz"),
            "/var/www/qgis-server/media/projects/5/a.qgz",
        )


class WebMercatorTests(SimpleTestCase):
    def test_origin_maps_to_origin(self):
        # tan(pi/4) is not exactly 1 in floating point, so compare with tolerance.
        x, y = _wgs84_to_web_mercator(0, 0)
        self.assertAlmostEqual(x, 0.0, places=6)
        self.assertAlmostEqual(y, 0.0, places=6)

    def test_known_longitude(self):
        x, y = _wgs84_to_web_mercator(10, 0)
        self.assertAlmostEqual(x, 1113194.9078, places=0)
        self.assertAlmostEqual(y, 0.0, places=0)

    def test_known_latitude(self):
        x, y = _wgs84_to_web_mercator(0, 5)
        self.assertAlmostEqual(x, 0.0, places=0)
        self.assertAlmostEqual(y, 557305.2, places=0)


class FindTextTests(SimpleTestCase):
    def test_finds_namespaced_element(self):
        el = ET.fromstring(
            f'<Layer xmlns="{WMS_NS}"><Name>points</Name></Layer>'
        )
        self.assertEqual(_find_text(el, "Name"), "points")

    def test_finds_unprefixed_element(self):
        el = ET.fromstring("<Layer><Name>points</Name></Layer>")
        self.assertEqual(_find_text(el, "Name"), "points")

    def test_missing_element_returns_none(self):
        el = ET.fromstring(f'<Layer xmlns="{WMS_NS}"></Layer>')
        self.assertIsNone(_find_text(el, "Name"))


class ExtentFromWmsLayerTests(SimpleTestCase):
    def _layer(self, xml):
        return ET.fromstring(f'<Layer xmlns="{WMS_NS}">{xml}</Layer>')

    def test_uses_ex_geographic_bounding_box_in_web_mercator(self):
        layer = self._layer(
            "<Name>points</Name>"
            "<EX_GeographicBoundingBox>"
            "<westBoundLongitude>-10</westBoundLongitude>"
            "<eastBoundLongitude>10</eastBoundLongitude>"
            "<southBoundLatitude>-5</southBoundLatitude>"
            "<northBoundLatitude>5</northBoundLatitude>"
            "</EX_GeographicBoundingBox>"
        )
        minx, miny, maxx, maxy = _extent_from_wms_layer(layer)
        self.assertAlmostEqual(minx, -1113194.9078, places=0)
        self.assertAlmostEqual(miny, -557305.2, places=0)
        self.assertAlmostEqual(maxx, 1113194.9078, places=0)
        self.assertAlmostEqual(maxy, 557305.2, places=0)

    def test_falls_back_to_bounding_box(self):
        layer = self._layer(
            '<BoundingBox CRS="EPSG:3857" minx="0" miny="0" maxx="1000" maxy="2000"/>'
        )
        self.assertEqual(_extent_from_wms_layer(layer), (0.0, 0.0, 1000.0, 2000.0))

    def test_no_bounds_returns_none(self):
        layer = self._layer("<Name>points</Name>")
        self.assertIsNone(_extent_from_wms_layer(layer))


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class GetPrintLayoutsTests(TestCase):
    """get_print_layouts parses <Layout> names out of an embedded .qgs."""

    def _project_with_qgz(self, qgs_xml):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("project.qgs", qgs_xml)
        buf.seek(0)
        user = get_user_model().objects.create_user(
            email="owner@example.com", password="testpass123"
        )
        return Project.objects.create(
            name="Print test",
            owner=user,
            file=SimpleUploadedFile("print.qgz", buf.read()),
        )

    def test_returns_layout_names(self):
        project = self._project_with_qgz(
            '<qgis><Layout name="A4 landscape"/><Layout name="A4 portrait"/></qgis>'
        )
        self.assertEqual(
            get_print_layouts(project),
            ["A4 landscape", "A4 portrait"],
        )

    def test_no_layouts_returns_empty_list(self):
        project = self._project_with_qgz("<qgis><Layouts/></qgis>")
        self.assertEqual(get_print_layouts(project), [])
