"""Unit tests for the viewer's pure search helpers (no QGIS Server needed)."""

import urllib.parse

from django.test import SimpleTestCase

from georidge_platform.apps.viewer.views import _build_ogc_filter, _compute_bbox


class BuildOgcFilterTests(SimpleTestCase):
    """_build_ogc_filter must produce valid, single-encoded OGC Filter XML."""

    def test_single_field_has_no_or_wrapper(self):
        filt = _build_ogc_filter("smith", ["owner"])
        self.assertNotIn("<ogc:Or>", filt)
        self.assertIn("<ogc:PropertyName>owner</ogc:PropertyName>", filt)
        self.assertIn("<ogc:Literal>*smith*</ogc:Literal>", filt)

    def test_multiple_fields_wrapped_in_or(self):
        filt = _build_ogc_filter("smith", ["owner", "address"])
        self.assertIn("<ogc:Or>", filt)
        self.assertIn("<ogc:PropertyName>owner</ogc:PropertyName>", filt)
        self.assertIn("<ogc:PropertyName>address</ogc:PropertyName>", filt)

    def test_field_name_with_space_is_not_url_encoded(self):
        # Regression: pre-quoting produced %20 inside the XML, then urlencode
        # re-encoded it to %2520 and the search silently matched nothing.
        filt = _build_ogc_filter("main road", ["Street Name"])
        self.assertIn(">Street Name<", filt)
        self.assertNotIn("%", filt)

    def test_query_with_xml_special_chars_is_entity_escaped(self):
        filt = _build_ogc_filter("a&b<c>d", ["owner"])
        self.assertIn("a&amp;b&lt;c&gt;d", filt)

    def test_query_with_double_quote_is_legal_xml_text(self):
        # Quotes only matter in attributes; text content may contain them.
        filt = _build_ogc_filter('say "hi"', ["owner"])
        self.assertIn('>*say "hi"*<', filt)

    def test_urlencode_applies_single_encoding(self):
        filt = _build_ogc_filter("main road", ["Street Name"])
        params = urllib.parse.urlencode({"FILTER": filt})
        self.assertIn("FILTER=%3C", params)
        self.assertNotIn("%2520", params)

    def test_filter_wraps_ogc_namespace(self):
        filt = _build_ogc_filter("x", ["owner"])
        self.assertIn(
            "<Filter xmlns:ogc='http://www.opengis.net/ogc'>",
            filt,
        )
        self.assertTrue(filt.endswith("</Filter>"))

    def test_empty_fields_does_not_raise(self):
        filt = _build_ogc_filter("x", [])
        self.assertTrue(filt.endswith("</Filter>"))


class ComputeBboxTests(SimpleTestCase):
    """_compute_bbox must derive [minx, miny, maxx, maxy] from GeoJSON."""

    def test_point(self):
        self.assertEqual(
            _compute_bbox({"type": "Point", "coordinates": [10, 20]}),
            [10, 20, 10, 20],
        )

    def test_multipoint(self):
        geom = {"type": "MultiPoint", "coordinates": [[1, 2], [5, 6], [3, 0]]}
        self.assertEqual(_compute_bbox(geom), [1, 0, 5, 6])

    def test_polygon(self):
        geom = {"type": "Polygon", "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 0]]]}
        self.assertEqual(_compute_bbox(geom), [0, 0, 10, 10])

    def test_multipolygon(self):
        geom = {
            "type": "MultiPolygon",
            "coordinates": [
                [[[0, 0], [1, 0], [1, 1], [0, 0]]],
                [[[5, 5], [6, 5], [6, 6], [5, 5]]],
            ],
        }
        self.assertEqual(_compute_bbox(geom), [0, 0, 6, 6])

    def test_multilinestring(self):
        geom = {"type": "MultiLineString", "coordinates": [[[0, 0], [5, 9]], [[10, 20], [30, 40]]]}
        self.assertEqual(_compute_bbox(geom), [0, 0, 30, 40])

    def test_empty_coordinates_returns_none(self):
        self.assertIsNone(_compute_bbox({"type": "Polygon", "coordinates": []}))
