import json
import re
import urllib.parse
import urllib.request

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from georidge_platform.apps.projects.models import Project
from georidge_platform.apps.qgis_server.services import get_wms_layer_names, get_wms_layer_tree, remap_map_path
from georidge_platform.apps.viewer.models import BaseMap, LayerSearchConfig, ThemeProfile


def _project_scope(request):
    if request.tenant:
        return {"tenant": request.tenant}
    return {}


def _get_wms_context(project):
    map_path = remap_map_path(project.file.path.replace("\\", "/"))
    base = settings.QGIS_SERVER_URL.rstrip("/")
    wms_url = f"{base}?MAP={map_path}"
    try:
        layer_names = get_wms_layer_names(project)
    except Exception:
        layer_names = []
    try:
        layer_tree = get_wms_layer_tree(project)
    except Exception:
        layer_tree = []
    return {
        "project": project,
        "wms_url": wms_url,
        "wms_layer_name": ",".join(layer_names) if layer_names else project.name,
        "wms_layer_names": layer_names,
        "layer_tree": layer_tree,
    }


def resolve_theme(project, request=None):
    theme_override_pk = None
    if request is not None:
        try:
            theme_override_pk = int(request.GET.get("theme_override", ""))
        except (ValueError, TypeError):
            theme_override_pk = None

    theme_qs = ThemeProfile.objects.filter(tenant=request.tenant) if request.tenant else ThemeProfile.objects.all()

    if theme_override_pk:
        theme = theme_qs.filter(pk=theme_override_pk).first()
        if theme:
            return theme

    if project.theme_id:
        return project.theme

    return theme_qs.filter(is_default=True).first()


def _get_icon_ext(icon_set):
    return "svg"


def rewrite_media_paths(html, project_pk):
    prefix = f"/media/projects/{project_pk}/media/"

    def _rewrite(m):
        attr = m.group(1)
        quote = m.group(2)
        path = m.group(3)
        if path.startswith("media/"):
            return f'{attr}{quote}{prefix}{path[len("media/"):]}{quote}'
        return m.group(0)

    html = re.sub(r'(src=)(["\'])(media/[^"\']*)\2', _rewrite, html)
    html = re.sub(r'(href=)(["\'])(media/[^"\']*)\2', _rewrite, html)
    html = re.sub(r'(action=)(["\'])(media/[^"\']*)\2', _rewrite, html)
    return html


def parse_qgis_form_tabs(html):
    tabs = []
    tab_pattern = re.compile(
        r'<div[^>]*class="[^"]*\btabgroup\b[^"]*"[^>]*data-tabgroup-name="([^"]*)"',
        re.IGNORECASE | re.DOTALL,
    )
    field_pattern = re.compile(
        r'<(?:th|td|div|span|label)[^>]*>\s*(.*?)\s*</(?:th|td|div|span|label)>',
        re.IGNORECASE | re.DOTALL,
    )
    img_pattern = re.compile(
        r'<img[^>]*src="([^"]*)"',
        re.IGNORECASE,
    )

    for match in tab_pattern.finditer(html):
        tab_name = match.group(1).strip()
        start = match.end()
        rest = html[start:]
        next_tab = tab_pattern.search(rest)
        tab_html = rest[:next_tab.start()] if next_tab else rest

        media = [m.group(1) for m in img_pattern.finditer(tab_html)]
        tabs.append({
            "name": tab_name,
            "html": tab_html,
            "media": media,
        })

    return tabs


def _read_qgs_from_qgz(qgz_path):
    """Extract the .qgs XML content from a .qgz archive."""
    import zipfile
    import os
    if not os.path.exists(qgz_path):
        return None
    try:
        with zipfile.ZipFile(qgz_path) as zf:
            for name in zf.namelist():
                if name.endswith(".qgs"):
                    return zf.read(name).decode("utf-8", errors="replace")
    except Exception:
        pass
    return None


def parse_qgs_tab_structure(qgs_content):
    """Parse QGS XML content to extract tab→field mappings from attributeEditorForm."""
    if not qgs_content:
        return []

    tabs = []
    tab_pattern = re.compile(
        r'<attributeEditorContainer[^>]*name="([^"]*)"[^>]*type="Tab"[^>]*>(.*?)</attributeEditorContainer>',
        re.DOTALL,
    )
    field_pattern = re.compile(
        r'<attributeEditorField[^>]*name="([^"]*)"',
    )
    for tab_match in tab_pattern.finditer(qgs_content):
        tab_name = tab_match.group(1).strip()
        tab_body = tab_match.group(2)
        fields = [f.group(1) for f in field_pattern.finditer(tab_body)]
        tabs.append({"name": tab_name, "fields": fields})
    return tabs


def parse_qgs_external_resource_fields(qgs_content):
    """Parse QGS to find fields with ExternalResource image widgets."""
    if not qgs_content:
        return set()

    image_fields = set()
    field_pattern = re.compile(
        r'<field name="([^"]*)"[^>]*>.*?</field>',
        re.DOTALL,
    )
    for m in field_pattern.finditer(qgs_content):
        name = m.group(1)
        block = m.group(0)
        if 'ExternalResource' in block and 'DocumentViewer" type="int" value="1"' in block:
            image_fields.add(name)
    return image_fields


def group_attributes_by_tabs(properties, tab_structure, image_fields):
    """Group feature properties by tab structure, with media detection."""
    if not tab_structure:
        return [{"name": "Attributes", "fields": list(properties.items())}]

    all_tab_fields = set()
    for tab in tab_structure:
        all_tab_fields.update(tab["fields"])

    result = []
    for tab in tab_structure:
        fields = []
        media = []
        for field_name in tab["fields"]:
            value = properties.get(field_name)
            if field_name in image_fields and value:
                media.append({"field": field_name, "path": str(value)})
            if value is not None:
                fields.append({"name": field_name, "value": value})
        result.append({"name": tab["name"], "fields": fields, "media": media})

    extra_fields = []
    for key, value in properties.items():
        if key not in all_tab_fields and value is not None:
            extra_fields.append({"name": key, "value": value})
    if extra_fields:
        result.append({"name": "Other", "fields": extra_fields, "media": []})

    return result

def _get_theme_context(project, request=None):
    theme = resolve_theme(project, request)
    icon_set = theme.icon_set if theme else "default"
    return {
        "theme": theme,
        "theme_css_vars": theme.to_css_vars() if theme else {},
        "icon_set": icon_set,
        "icon_ext": _get_icon_ext(icon_set),
    }


def _get_base_maps_context(project, request):
    if project.base_maps.exists():
        qs = project.base_maps.filter(is_active=True)
    else:
        tenant_filter = models.Q(tenant=request.tenant) | models.Q(tenant=None) if request.tenant else models.Q(tenant=None)
        qs = BaseMap.objects.filter(tenant_filter, is_active=True)
    qs = qs.order_by("sort_order", "name")
    fallback_thumb = staticfiles_storage.url("viewer/icons/globe-fallback.svg")
    base_maps = []
    for bm in qs:
        base_maps.append({
            "name": bm.name,
            "type": bm.type,
            "url": bm.url,
            "attribution": bm.attribution,
            "thumbnailUrl": bm.thumbnail.url if bm.thumbnail else fallback_thumb,
        })
    return base_maps


def _get_wms_context_for_request(project, request):
    ctx = _get_wms_context(project)
    proxy_url = f"{request.tenant_base}/viewer/{project.pk}/wms/"
    ctx["wms_url"] = proxy_url
    ctx.update(_get_theme_context(project, request))
    ctx["base_maps"] = _get_base_maps_context(project, request)
    extent = None
    if project.extent_min_x is not None:
        extent = [
            project.extent_min_x,
            project.extent_min_y,
            project.extent_max_x,
            project.extent_max_y,
        ]
    ctx["extent_json"] = json.dumps(extent)
    ctx["wms_layer_names_json"] = json.dumps(ctx["wms_layer_names"])
    ctx["layer_tree_json"] = json.dumps(ctx["layer_tree"])
    ctx["base_maps_json"] = json.dumps(ctx["base_maps"])
    return ctx


def _build_ogc_filter(query, fields):
    """Build OGC Filter XML for PropertyIsLike over multiple fields."""
    clauses = "\n".join(
        f'<ogc:PropertyIsLike wildCard="*" singleChar="?" escapeChar="!">'
        f'<ogc:PropertyName>{urllib.parse.quote(f)}</ogc:PropertyName>'
        f'<ogc:Literal>*{urllib.parse.quote(query)}*</ogc:Literal>'
        f"</ogc:PropertyIsLike>"
        for f in fields
    )
    if len(fields) == 1:
        return (
            "<Filter xmlns:ogc='http://www.opengis.net/ogc'>"
            f"{clauses}</Filter>"
        )
    return (
        "<Filter xmlns:ogc='http://www.opengis.net/ogc'>"
        f"<ogc:Or>{clauses}</ogc:Or></Filter>"
    )


def _compute_bbox(geojson_geom):
    """Compute [minX, minY, maxX, maxY] from a GeoJSON geometry."""
    coords = geojson_geom.get("coordinates", [])
    coord_type = geojson_geom.get("type", "")
    if coord_type == "Point":
        return [coords[0], coords[1], coords[0], coords[1]]
    if coord_type == "MultiPoint":
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        return [min(xs), min(ys), max(xs), max(ys)]
    # Polygon, MultiLineString, MultiPolygon, GeometryCollection
    all_coords = []
    def _flatten(rings):
        for ring in rings:
            if ring and isinstance(ring[0], (list, tuple)):
                _flatten(ring)
            else:
                all_coords.append(ring)
    _flatten(coords)
    if not all_coords:
        return None
    xs = [c[0] for c in all_coords if len(c) >= 2]
    ys = [c[1] for c in all_coords if len(c) >= 2]
    if not xs or not ys:
        return None
    return [min(xs), min(ys), max(xs), max(ys)]


def search_view(request, pk):
    project = get_object_or_404(Project, pk=pk, **_project_scope(request))
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"results": []})

    global_limit = int(request.GET.get("limit", 20))
    configs = LayerSearchConfig.objects.filter(
        project=project, active=True,
    ).exclude(searchable_fields=[])

    map_path = remap_map_path(project.file.path.replace("\\", "/"))
    qgis_base = settings.QGIS_SERVER_URL.rstrip("/")
    results = []

    for cfg in configs:
        if len(results) >= global_limit:
            break

        fields = cfg.searchable_fields or []
        if not fields:
            continue

        filter_xml = _build_ogc_filter(q, fields)
        params = urllib.parse.urlencode({
            "MAP": map_path,
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "GetFeature",
            "TYPENAME": cfg.layer_name,
            "FILTER": filter_xml,
            "OUTPUTFORMAT": "application/json",
            "SRSNAME": "EPSG:3857",
        })
        wfs_url = f"{qgis_base}?{params}"

        try:
            req = urllib.request.Request(wfs_url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
        except Exception:
            continue

        features = data.get("features", [])[:cfg.max_results]
        for feat in features:
            if len(results) >= global_limit:
                break
            props = feat.get("properties", {})
            template = cfg.label_template or "{id}"
            try:
                label = template.format(**props)
            except Exception:
                label = str(props.get(list(props.keys())[0], "")) if props else cfg.layer_name
            geom = feat.get("geometry")
            bbox = _compute_bbox(geom) if geom else None
            results.append({
                "layer": cfg.layer_name,
                "layer_title": cfg.layer_title or cfg.layer_name,
                "label": label,
                "bbox": bbox,
                "geojson": feat,
            })

    return JsonResponse({"results": results})


def wms_proxy_view(request, pk):
    project = get_object_or_404(Project, pk=pk, **_project_scope(request))
    map_path = remap_map_path(project.file.path.replace("\\", "/"))
    qgis_base = settings.QGIS_SERVER_URL.rstrip("/")
    params = request.GET.copy()
    params["MAP"] = map_path
    qgis_url = f"{qgis_base}?{params.urlencode()}"
    try:
        resp = requests.get(qgis_url, stream=True, timeout=60)
        content_type = resp.headers.get("content-type", "application/octet-stream")
        django_resp = HttpResponse(
            resp.content,
            content_type=content_type,
            status=resp.status_code,
        )
        for header in ["Content-Disposition", "Content-Length"]:
            if header in resp.headers:
                django_resp[header] = resp.headers[header]
        return django_resp
    except requests.exceptions.RequestException as e:
        return HttpResponse(f"WMS proxy error: {e}", status=502)


def view_view(request, pk):
    project = get_object_or_404(Project, pk=pk, **_project_scope(request))
    return render(request, "viewer/viewer.html", _get_wms_context_for_request(project, request))


@login_required
def legend_panel(request, pk):
    project = get_object_or_404(Project, pk=pk, **_project_scope(request))
    return render(request, "viewer/panels/legend.html", {"project": project})


@login_required
def layers_panel(request, pk):
    project = get_object_or_404(Project, pk=pk, **_project_scope(request))
    return render(request, "viewer/panels/layers.html", {"project": project})


@login_required
def toolbar_panel(request, pk):
    return render(request, "viewer/panels/toolbar.html")


def identify_view(request, pk):
    import urllib.request
    import urllib.parse

    i = request.GET.get("i")
    j = request.GET.get("j")
    bbox = request.GET.get("bbox")
    width = request.GET.get("width")
    height = request.GET.get("height")
    layer = request.GET.get("layer", "")
    query_layers = request.GET.get("query_layers", layer)
    project = get_object_or_404(Project, pk=pk, **_project_scope(request))

    if not all([i, j, bbox, width, height]):
        return render(request, "viewer/panels/info.html", {
            "features": [],
            "features_geojson": "[]",
            "error": "Could not retrieve feature information. Please try again.",
        })

    local_path = project.file.path.replace("\\", "/")
    map_path = remap_map_path(local_path)
    base_params = {
        "MAP": map_path,
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetFeatureInfo",
        "LAYERS": layer,
        "QUERY_LAYERS": query_layers,
        "CRS": "EPSG:3857",
        "BBOX": bbox,
        "WIDTH": width,
        "HEIGHT": height,
        "I": i,
        "J": j,
    }

    try:
        json_params = {**base_params, "INFO_FORMAT": "application/json"}
        req = urllib.request.Request(
            f"{settings.QGIS_SERVER_URL.rstrip('/')}?{urllib.parse.urlencode(json_params)}",
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            features = data.get("features", [])
    except Exception:
        return render(request, "viewer/panels/info.html", {
            "features": [],
            "features_geojson": "[]",
            "error": "Could not retrieve feature information. Please try again.",
        })

    html_content = ""
    tabs = []
    try:
        html_params = {**base_params, "INFO_FORMAT": "text/html"}
        req = urllib.request.Request(
            f"{settings.QGIS_SERVER_URL.rstrip('/')}?{urllib.parse.urlencode(html_params)}",
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw_html = resp.read().decode("utf-8", errors="replace")
            html_content = rewrite_media_paths(raw_html, project.pk)
            tabs = parse_qgis_form_tabs(html_content)
    except Exception:
        pass

    grouped = {}
    for f in features:
        fid = f.get("id", "")
        layer_name = fid.split(".")[0] if "." in fid else query_layers.split(",")[0]
        grouped.setdefault(layer_name, []).append(f)

    qgs_content = _read_qgs_from_qgz(local_path)
    tab_structure = parse_qgs_tab_structure(qgs_content)
    image_fields = parse_qgs_external_resource_fields(qgs_content)

    feature_tabs = []
    if features and tab_structure:
        props = features[0].get("properties", {})
        feature_tabs = group_attributes_by_tabs(props, tab_structure, image_fields)
        media_base = f"/media/projects/{project.pk}/media/"
        for tab in feature_tabs:
            for item in tab.get("media", []):
                path = item["path"]
                if path.startswith("media/"):
                    item["url"] = f"/media/projects/{project.pk}/{path}"
                else:
                    item["url"] = f"{media_base}{path}"

    return render(request, "viewer/panels/info.html", {
        "features": features,
        "features_geojson": json.dumps({"type": "FeatureCollection", "features": features}),
        "grouped": grouped,
        "error": None if features else "No features found at this location",
        "html_content": html_content,
        "tabs_json": json.dumps(tabs),
        "feature_tabs_json": json.dumps(feature_tabs),
        "project_pk": project.pk,
    })
