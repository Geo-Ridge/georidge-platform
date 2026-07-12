import math
import os
import shutil
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET

from django.conf import settings

WMS_NS = "http://www.opengis.net/wms"

HALF_CIRCUMFERENCE = 20037508.34


def _wgs84_to_web_mercator(lon, lat):
    x = lon * HALF_CIRCUMFERENCE / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180) * HALF_CIRCUMFERENCE / 180
    return x, y


def _qgis_url(map_path, service_params=None):
    base = settings.QGIS_SERVER_URL.rstrip("/")
    params = service_params or {}
    params.setdefault("SERVICE", "WMS")
    params.setdefault("REQUEST", "GetCapabilities")
    qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    return f"{base}/?MAP={map_path}&{qs}"


def _get_qgis_version():
    try:
        import subprocess
        r = subprocess.run(
            [settings.QGIS_PYTHON, "-c", "from qgis.core import Qgis; print(Qgis.version())"],
            capture_output=True, text=True, timeout=10,
        )
        version = r.stdout.strip()
        return version if version else None
    except Exception:
        return None


def health_check():
    try:
        req = urllib.request.Request(
            settings.QGIS_SERVER_URL.rstrip("/"),
            method="GET",
        )
        urllib.request.urlopen(req, timeout=5)
        version = _get_qgis_version()
        result = {"status": "online"}
        if version:
            result["version"] = version
        return result
    except Exception:
        return {"status": "offline"}


def validate_on_server(project):
    map_path = project.file.path.replace("\\", "/")
    url = _qgis_url(map_path)
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
        root = ET.fromstring(body)
        service_exception = root.find(".//ServiceException")
        if service_exception is not None:
            return {
                "valid": False,
                "errors": [service_exception.text or "Unknown QGIS Server error"],
                "layer_count": 0,
            }
        cap_layer = root.find(f".//{{{WMS_NS}}}Capability/{{{WMS_NS}}}Layer")
        if cap_layer is None:
            cap_layer = root.find(".//Capability/Layer")
        child_layers = cap_layer.findall(f"{{{WMS_NS}}}Layer") if cap_layer is not None else []
        if not child_layers and cap_layer is not None:
            child_layers = cap_layer.findall("Layer")
        return {
            "valid": True,
            "errors": [],
            "warnings": [],
            "layer_count": max(len(child_layers), 1),
        }
    except ET.ParseError:
        return {
            "valid": False,
            "errors": ["QGIS Server returned invalid XML"],
            "layer_count": 0,
        }
    except urllib.error.HTTPError as e:
        return {
            "valid": False,
            "errors": [f"QGIS Server error: {e.code} {e.reason}"],
            "layer_count": 0,
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"QGIS Server unreachable: {str(e)}"],
            "layer_count": 0,
        }


def _find_text(parent, tag):
    el = parent.find(f"{{{WMS_NS}}}{tag}")
    if el is None:
        el = parent.find(tag)
    return el.text.strip() if el is not None and el.text else None


def _find_bool(parent, tag, default=False):
    val = _find_text(parent, tag)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes")


def _parse_layer_tree(xml_layer):
    name = _find_text(xml_layer, "Name")
    title = _find_text(xml_layer, "Title") or name
    queryable = xml_layer.get("queryable", "0") in ("1", "true")
    crs = []
    for crs_tag in ("CRS", "crs"):
        for el in xml_layer.findall(f"{{{WMS_NS}}}{crs_tag}") or xml_layer.findall(crs_tag):
            if el.text:
                crs.append(el.text.strip())
    styles = []
    for style_tag in ("Style", "style"):
        for sel in xml_layer.findall(f"{{{WMS_NS}}}{style_tag}") or xml_layer.findall(style_tag):
            sname = _find_text(sel, "Name") or ""
            stitle = _find_text(sel, "Title") or sname
            styles.append({"name": sname, "title": stitle})

    child_layers = xml_layer.findall(f"{{{WMS_NS}}}Layer")
    if not child_layers:
        child_layers = xml_layer.findall("Layer")

    if child_layers:
        children = [_parse_layer_tree(cl) for cl in child_layers]
        if name:
            return {
                "name": name,
                "title": title,
                "type": "group",
                "queryable": queryable,
                "children": children,
            }
        return {
            "title": title or "Group",
            "type": "group",
            "children": children,
        }

    return {
        "name": name or "",
        "title": title or name or "",
        "type": "layer",
        "queryable": queryable,
        "crs": crs,
        "styles": styles,
    }


def get_wms_layer_names(project):
    map_path = project.file.path.replace("\\", "/")
    url = _qgis_url(map_path)
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
        root = ET.fromstring(body)
        cap_layer = root.find(f".//{{{WMS_NS}}}Capability/{{{WMS_NS}}}Layer")
        if cap_layer is None:
            cap_layer = root.find(".//Capability/Layer")
        if cap_layer is None:
            return []
        child_layers = cap_layer.findall(f"{{{WMS_NS}}}Layer")
        if not child_layers and cap_layer is not None:
            child_layers = cap_layer.findall("Layer")
        names = []
        for cl in child_layers:
            name_el = cl.find(f"{{{WMS_NS}}}Name")
            if name_el is None:
                name_el = cl.find("Name")
            if name_el is not None and name_el.text:
                names.append(name_el.text)
        return names
    except Exception:
        return []


def get_wms_layer_tree(project):
    map_path = project.file.path.replace("\\", "/")
    url = _qgis_url(map_path)
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
        root = ET.fromstring(body)
        cap_layer = root.find(f".//{{{WMS_NS}}}Capability/{{{WMS_NS}}}Layer")
        if cap_layer is None:
            cap_layer = root.find(".//Capability/Layer")
        if cap_layer is None:
            return []
        child_layers = cap_layer.findall(f"{{{WMS_NS}}}Layer")
        if not child_layers:
            child_layers = cap_layer.findall("Layer")
        return [_parse_layer_tree(cl) for cl in child_layers]
    except Exception:
        return []
        child_layers = cap_layer.findall(f"{{{WMS_NS}}}Layer") if cap_layer is not None else []
        if not child_layers and cap_layer is not None:
            child_layers = cap_layer.findall("Layer")
        names = []
        for cl in child_layers:
            name_el = cl.find(f"{{{WMS_NS}}}Name")
            if name_el is None:
                name_el = cl.find("Name")
            if name_el is not None and name_el.text:
                names.append(name_el.text)
        return names
    except Exception:
        return []


def _collect_layers(xml_layer, result):
    """Recursively collect named layers from a WMS Layer element tree."""
    name = _find_text(xml_layer, "Name")
    child_layers = xml_layer.findall(f"{{{WMS_NS}}}Layer")
    if not child_layers:
        child_layers = xml_layer.findall("Layer")
    if child_layers:
        if name:
            result.append({
                "name": name,
                "title": _find_text(xml_layer, "Title") or name,
                "queryable": xml_layer.get("queryable", "0") in ("1", "true"),
            })
        for cl in child_layers:
            _collect_layers(cl, result)
    else:
        if name:
            result.append({
                "name": name,
                "title": _find_text(xml_layer, "Title") or name,
                "queryable": xml_layer.get("queryable", "0") in ("1", "true"),
            })


def get_wms_layers(project):
    """Fetch flat layer list from WMS GetCapabilities, recursing into groups.

    Returns list of dicts: {name, title, queryable}
    """
    map_path = project.file.path.replace("\\", "/")
    url = _qgis_url(map_path)
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
        root = ET.fromstring(body)
        cap_layer = root.find(f".//{{{WMS_NS}}}Capability/{{{WMS_NS}}}Layer")
        if cap_layer is None:
            cap_layer = root.find(".//Capability/Layer")
        if cap_layer is None:
            return []
        result = []
        _collect_layers(cap_layer, result)
        return result
    except Exception:
        return []


def get_layer_fields(project, layer_name):
    """Fetch field names for a layer via WFS DescribeFeatureType.

    Returns list of field name strings, or [] on error.
    """
    map_path = project.file.path.replace("\\", "/")
    url = _qgis_url(map_path, {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "DescribeFeatureType",
        "TYPENAME": layer_name,
    })
    WFS_NS = "http://www.opengis.net/wfs"
    XSD_NS = "http://www.w3.org/2001/XMLSchema"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
        root = ET.fromstring(body)
        # Fields are <xsd:element> inside <xsd:sequence>
        for seq in root.iter(f"{{{XSD_NS}}}sequence"):
            fields = []
            for el in seq.iter(f"{{{XSD_NS}}}element"):
                name = el.attrib.get("name")
                if name:
                    fields.append(name)
            return fields
        return []
    except Exception:
        return []


def get_extent_via_server(project):
    map_path = project.file.path.replace("\\", "/")
    url = _qgis_url(map_path)
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
        root = ET.fromstring(body)
        root_layer = root.find(f".//{{{WMS_NS}}}Capability/{{{WMS_NS}}}Layer")
        if root_layer is None:
            root_layer = root.find(".//Capability/Layer")
        if root_layer is None:
            return None
        geo_bbox = root_layer.find(f"{{{WMS_NS}}}EX_GeographicBoundingBox")
        if geo_bbox is None:
            geo_bbox = root_layer.find("EX_GeographicBoundingBox")
        if geo_bbox is not None:
            def _txt(tag):
                el = geo_bbox.find(f"{{{WMS_NS}}}{tag}")
                if el is None:
                    el = geo_bbox.find(tag)
                return float(el.text) if el is not None and el.text else 0
            minx, miny = _wgs84_to_web_mercator(
                _txt("westBoundLongitude"),
                _txt("southBoundLatitude"),
            )
            maxx, maxy = _wgs84_to_web_mercator(
                _txt("eastBoundLongitude"),
                _txt("northBoundLatitude"),
            )
            return (minx, miny, maxx, maxy)
        bbox = root_layer.find(f"{{{WMS_NS}}}BoundingBox")
        if bbox is None:
            bbox = root_layer.find("BoundingBox")
        if bbox is not None:
            return (
                float(bbox.attrib.get("minx", 0)),
                float(bbox.attrib.get("miny", 0)),
                float(bbox.attrib.get("maxx", 0)),
                float(bbox.attrib.get("maxy", 0)),
            )
        return None
    except Exception:
        return None