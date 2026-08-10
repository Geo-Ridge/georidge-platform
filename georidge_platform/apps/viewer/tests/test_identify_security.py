"""Unit tests for the identify XSS hardening (escaping + sanitization)."""

import json

from django.template import Context, Engine
from django.test import SimpleTestCase

from georidge_platform.apps.viewer.views import (
    _escape_json_for_script,
    sanitize_qgis_html,
)


class EscapeJsonForScriptTests(SimpleTestCase):
    """_escape_json_for_script must remove every script-terminating sequence."""

    def test_escapes_script_closing_sequence(self):
        payload = json.dumps("</script><script>alert(1)</script>")
        escaped = _escape_json_for_script(payload)
        self.assertNotIn("</script", escaped)
        self.assertNotIn("<script", escaped)
        # Still valid JSON: JSON.parse round-trips back to the original value.
        self.assertEqual(json.loads(escaped), "</script><script>alert(1)</script>")

    def test_escapes_all_angle_brackets_and_ampersands(self):
        escaped = _escape_json_for_script(json.dumps('<a href="x">&'))
        self.assertNotIn("<", escaped)
        self.assertNotIn(">", escaped)
        self.assertNotIn("&", escaped)
        self.assertEqual(json.loads(escaped), '<a href="x">&')

    def test_normal_payload_semantics_unchanged(self):
        payload = json.dumps({"a": [1, 2], "b": "hello world"})
        self.assertEqual(json.loads(_escape_json_for_script(payload)), json.loads(payload))

    def test_escapes_html_comment_sequence(self):
        escaped = _escape_json_for_script(json.dumps("<!-- comment -->"))
        self.assertNotIn("<!--", escaped)
        self.assertEqual(json.loads(escaped), "<!-- comment -->")

    def test_layer_tree_payload_with_malicious_layer_name(self):
        # Layer/print-layout names come from tenant-uploaded .qgz files and are
        # embedded in the viewer's map-config block — same breakout class.
        layer_tree = [{"name": "</script><script>alert(1)</script>", "title": "Map"}]
        escaped = _escape_json_for_script(json.dumps(layer_tree))
        self.assertNotIn("</script", escaped)
        self.assertEqual(json.loads(escaped), layer_tree)


class SanitizeQgisHtmlTests(SimpleTestCase):
    """sanitize_qgis_html must strip active content but keep table structure."""

    def test_strips_script_tags(self):
        html = "<table><tr><td>value<script>alert(1)</script></td></tr></table>"
        out = sanitize_qgis_html(html)
        self.assertNotIn("<script", out)
        self.assertIn("value", out)

    def test_strips_event_handlers(self):
        html = '<img src="x" onerror="alert(1)"><table><tr><td>ok</td></tr></table>'
        out = sanitize_qgis_html(html)
        self.assertNotIn("onerror", out)

    def test_strips_javascript_urls(self):
        html = '<a href="javascript:alert(1)">click</a>'
        out = sanitize_qgis_html(html)
        self.assertNotIn("javascript:", out)
        self.assertIn("click", out)

    def test_keeps_tables_and_relative_media_urls(self):
        html = (
            "<table><tr><th>a</th></tr><tr><td>"
            '<img src="/media/projects/5/x.png" alt="photo">'
            "</td></tr></table>"
        )
        out = sanitize_qgis_html(html)
        self.assertIn("<table>", out)
        self.assertIn('<img src="/media/projects/5/x.png"', out)

    def test_strips_style_attributes(self):
        out = sanitize_qgis_html('<td style="background:red">x</td>')
        self.assertNotIn("style=", out)

    def test_keeps_escaped_feature_value_text(self):
        # Values QGIS already escaped must pass through harmlessly.
        out = sanitize_qgis_html("<td>&lt;img src=x onerror=alert(1)&gt;</td>")
        self.assertIn("&lt;img", out)

    def test_keeps_tabgroup_structure_attributes(self):
        html = (
            '<div class="tabgroup" data-tabgroup-name="Details">'
            "<table><tr><td>v</td></tr></table></div>"
        )
        out = sanitize_qgis_html(html)
        self.assertIn('class="tabgroup"', out)
        self.assertIn('data-tabgroup-name="Details"', out)
        self.assertIn("v", out)

    def test_forces_noopener_on_blank_target_links(self):
        out = sanitize_qgis_html('<a href="/media/x.pdf" target="_blank">doc</a>')
        self.assertIn('target="_blank" rel="noopener"', out)

    def test_does_not_duplicate_existing_rel(self):
        out = sanitize_qgis_html('<a href="/x" target="_blank" rel="nofollow">doc</a>')
        self.assertEqual(out.count('rel="'), 1)
        self.assertIn('rel="nofollow"', out)


class InfoTemplateRenderTests(SimpleTestCase):
    """info.html must never emit a literal </script> inside its JSON blocks."""

    def _render(self, **ctx):
        engine = Engine.get_default()
        template = engine.get_template("viewer/panels/info.html")
        defaults = {
            "error": None,
            "grouped": {},
            "features_geojson": "[]",
            "html_content": "",
            "tabs_json": "[]",
            "feature_tabs_json": "[]",
            "project_pk": 1,
        }
        defaults.update(ctx)
        return template.render(Context(defaults))

    def _assert_no_breakout(self, html, escaped_marker="\\u003c/script"):
        # The payload must be escaped (its literal < becomes \u003c) and the
        # only </script> sequences in the page must be the template's own
        # closers — one per opening <script type="application/json"> block.
        self.assertIn(escaped_marker, html)
        self.assertEqual(
            html.count("</script>"),
            html.count('<script type="application/json"'),
        )

    def test_feature_payload_cannot_break_out_of_script_block(self):
        payload = _escape_json_for_script(
            json.dumps({
                "type": "FeatureCollection",
                "features": [{"properties": {"owner": "</script><script>alert(1)</script>"}}],
            })
        )
        self._assert_no_breakout(self._render(features_geojson=payload))

    def test_html_content_payload_cannot_break_out(self):
        html = self._render(
            html_content=_escape_json_for_script("</script><script>alert(1)</script>")
        )
        self._assert_no_breakout(html)

    def test_tabs_payload_cannot_break_out(self):
        tabs = _escape_json_for_script(
            json.dumps([{"name": "T", "html": "</script><b>x</b>", "media": []}])
        )
        self._assert_no_breakout(self._render(tabs_json=tabs))

    def test_feature_tabs_payload_cannot_break_out(self):
        tabs = _escape_json_for_script(
            json.dumps([{"name": "T", "fields": [{"name": "k", "value": "</script>"}], "media": []}])
        )
        self._assert_no_breakout(self._render(feature_tabs_json=tabs))
