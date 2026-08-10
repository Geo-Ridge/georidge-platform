import json
import re
import urllib.parse
import urllib.request
from xml.sax.saxutils import escape as xml_escape

import bleach
import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.clickjacking import xframe_options_exempt

from georidge_platform.apps.projects.models import Project
from georidge_platform.apps.qgis_server.services import (
    get_print_layouts,
    get_wms_layer_names,
    get_wms_layer_tree,
    remap_map_path,
)
from georidge_platform.apps.viewer.models import BaseMap, LayerSearchConfig, ThemeProfile


def _project_scope(request):
    if request.tenant:
        return {"tenant": request.tenant}
    return {}


def _can_view_project(request, project):
    """Status workflow access gate for the viewer and its data endpoints.

    Published projects are open to the public. Every other status (Draft,
    Validating, Ready, Failed, Archived) is viewable by any logged-in user so
    the team can preview/test it. Anonymous users are blocked from
    non-published projects.
    """
    if project.status == Project.Status.PUBLISHED:
        return True
    return request.user.is_authenticated


def _get_project_for_viewer(request, pk):
    project = get_object_or_404(Project, pk=pk, **_project_scope(request))
    if not _can_view_project(request, project):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    return project


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
    import os
    import zipfile
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

    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(qgs_content)
    except ET.ParseError:
        return []

    tabs = []
    for container in root.iter("attributeEditorContainer"):
        if container.get("type") != "Tab":
            continue
        tab_name = (container.get("name") or "").strip()
        fields = []
        for field_el in container.iter("attributeEditorField"):
            fname = field_el.get("name")
            if fname:
                fields.append(fname.strip())
        tabs.append({"name": tab_name, "fields": fields})
    return tabs


def parse_qgs_external_resource_fields(qgs_content):
    """Parse QGS to find fields with ExternalResource image widgets."""
    if not qgs_content:
        return set()

    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(qgs_content)
    except ET.ParseError:
        return set()

    image_fields = set()
    for field_el in root.iter("field"):
        field_name = field_el.get("name")
        if not field_name:
            continue
        edit_widget = field_el.find("editWidget")
        if edit_widget is None or edit_widget.get("type") != "ExternalResource":
            continue
        for option in edit_widget.iter("Option"):
            if (option.get("name") == "DocumentViewer"
                    and option.get("type") == "int"
                    and option.get("value") == "1"):
                image_fields.add(field_name.strip())
                break
    return image_fields


def _escape_json_for_script(text):
    """Make a JSON document safe to embed inside an inline <script> block.

    The HTML parser terminates a script element on the first ``</script`` (or
    ``<!--``) sequence regardless of surrounding quotes, so a feature attribute
    value like ``</script><script>alert(1)</script>`` embedded verbatim in a
    ``<script type="application/json">`` block would break out and execute.
    Replacing ``&``, ``<`` and ``>`` with their JSON unicode escapes keeps the
    payload valid JSON (JSON.parse transparently decodes them back) while
    removing every literal ``<`` from the script block.
    """
    return (
        text.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


# Tags/attributes QGIS GetFeatureInfo output may legitimately use. Everything
# else (scripts, event handlers, style, javascript: URLs, ...) is stripped.
_SANITIZE_TAGS = {
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption",
    "colgroup", "col", "div", "span", "p", "br", "hr", "b", "strong",
    "i", "em", "u", "s", "sub", "sup", "small", "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "h5", "h6", "img", "a",
}
_SANITIZE_ATTRS = {
    "img": ["src", "alt", "width", "height"],
    "a": ["href", "target", "rel", "title"],
    "th": ["colspan", "rowspan"],
    "td": ["colspan", "rowspan"],
    "div": ["class", "id", "data-tabgroup-name"],
    "*": ["class"],
}
_SANITIZE_PROTOCOLS = {"http", "https", "mailto"}


def sanitize_qgis_html(html):
    """Strip active content from QGIS GetFeatureInfo HTML.

    Feature attribute values are embedded by QGIS Server into the returned
    HTML, so a value like ``<img src=x onerror=alert(1)>`` would execute when
    the fragment is injected with innerHTML. Whitelist the structural tags
    QGIS produces and drop everything else (scripts, handlers, style,
    javascript: URLs). Relative URLs (e.g. project media) are preserved.
    """
    cleaned = bleach.clean(
        html,
        tags=_SANITIZE_TAGS,
        attributes=_SANITIZE_ATTRS,
        protocols=_SANITIZE_PROTOCOLS,
        strip=True,
    )
    # bleach cannot rewrite attributes, so force rel="noopener" onto any
    # target="_blank" anchor that survived (reverse-tabnabbing hardening).
    return re.sub(
        r'(<a\b[^>]*?target="_blank"[^>]*?)>',
        lambda m: m.group(1) + ' rel="noopener">' if "rel=" not in m.group(1) else m.group(0),
        cleaned,
    )


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
        # Tiles are proxied through this app (base_map_tile_view) so the
        # browser never hits the provider directly: third-party tile servers
        # (OSM et al.) reject browser requests that lack a Referer and their
        # CORS rules vary, while the server-side fetch sends a proper
        # User-Agent/Referer. tileUrl keeps the {z}/{x}/{y}(/{s}) template.
        suffix = urllib.parse.urlsplit(bm.url).path.lstrip("/")
        base_maps.append({
            "name": bm.name,
            "type": bm.type,
            "url": bm.url,
            "tileUrl": (
                f"{request.tenant_base}/viewer/{project.pk}/basemap/{bm.pk}/tile/{suffix}"
                if suffix
                else ""
            ),
            "attribution": bm.attribution,
            "thumbnailUrl": bm.thumbnail.url if bm.thumbnail else fallback_thumb,
            "minZoom": bm.min_zoom,
            "maxZoom": bm.max_zoom,
        })
    return base_maps


_XYZ_PLACEHOLDER = re.compile(r"(\{[a-zA-Z0-9_]+\})")


def _xyz_template_regex(template_path):
    """Turn an XYZ URL path template into a regex capturing z/x/y(/s).

    '{z}/{x}/{y}.png' -> '^(?P<z>[^/]+)/(?P<x>[^/]+)/(?P<y>[^/]+)\\.png$'
    """
    pattern = ""
    for token in _XYZ_PLACEHOLDER.split(template_path):
        if re.fullmatch(r"\{[a-zA-Z0-9_]+\}", token or ""):
            pattern += f"(?P<{token[1:-1]}>[^/]+)"
        else:
            pattern += re.escape(token)
    return f"^{pattern}$"


def base_map_tile_view(request, pk, bm_id, tile_path):
    """Proxy a base map XYZ tile through the app (see _get_base_maps_context)."""
    from django.http import Http404

    project = _get_project_for_viewer(request, pk)
    bm = get_object_or_404(BaseMap, pk=bm_id, is_active=True)
    if request.tenant and bm.tenant is not None and bm.tenant_id != request.tenant.pk:
        raise Http404
    if project.base_maps.exists() and not project.base_maps.filter(pk=bm.pk).exists():
        raise Http404

    parsed = urllib.parse.urlsplit(bm.url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return HttpResponse("Base map tile: invalid base map URL", status=400, content_type="text/plain")

    match = re.fullmatch(_xyz_template_regex(parsed.path.lstrip("/")), tile_path)
    if not match:
        return HttpResponse("Base map tile: bad tile path", status=404, content_type="text/plain")
    groups = match.groupdict()
    try:
        z, x, y = (int(groups.get(n, -1)) for n in ("z", "x", "y"))
    except (TypeError, ValueError):
        return HttpResponse("Base map tile: bad tile path", status=404, content_type="text/plain")
    if z < 0 or x < 0 or y < 0 or z > 25:
        return HttpResponse("Base map tile: bad tile path", status=404, content_type="text/plain")
    # Non-numeric tokens (e.g. an {s} subdomain placeholder) are substituted
    # raw, so constrain them and verify the netloc never changes: the tile
    # path must not be able to redirect the upstream host.
    for name, value in groups.items():
        if name not in ("z", "x", "y") and not re.fullmatch(r"[a-z0-9]+", value or "", re.IGNORECASE):
            return HttpResponse("Base map tile: bad tile path", status=404, content_type="text/plain")

    upstream = bm.url
    for name, value in groups.items():
        upstream = upstream.replace("{" + name + "}", value)
    if urllib.parse.urlsplit(upstream).netloc != parsed.netloc:
        return HttpResponse("Base map tile: bad tile path", status=404, content_type="text/plain")

    try:
        req = urllib.request.Request(
            upstream,
            method="GET",
            headers={
                "User-Agent": "GeoRidge/1.0 (georidge platform viewer)",
                "Referer": f"{request.scheme}://{request.get_host()}/",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read()
            content_type = resp.headers.get_content_type() or "image/png"
    except Exception:
        return HttpResponse("Base map tile: upstream error", status=502, content_type="text/plain")

    django_resp = HttpResponse(body, content_type=content_type)
    # Tiles are immutable; let the browser cache them to keep app traffic low.
    django_resp["Cache-Control"] = "public, max-age=86400"
    return django_resp


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
    # The layout templates embed every *_json value inside an inline
    # <script id="map-config"> block, so none may contain a literal </script>
    # (layer names / print layout names come from tenant-uploaded .qgz files).
    ctx["extent_json"] = _escape_json_for_script(json.dumps(extent))
    ctx["wms_layer_names_json"] = _escape_json_for_script(json.dumps(ctx["wms_layer_names"]))
    ctx["layer_tree_json"] = _escape_json_for_script(json.dumps(ctx["layer_tree"]))
    ctx["base_maps_json"] = _escape_json_for_script(json.dumps(ctx["base_maps"]))
    ctx["print_layouts"] = get_print_layouts(project)
    ctx["print_layouts_json"] = _escape_json_for_script(json.dumps(ctx["print_layouts"]))
    ctx["is_preview"] = project.status != Project.Status.PUBLISHED

    search_configs = LayerSearchConfig.objects.filter(project=project, active=True).exclude(searchable_fields=[])
    ctx["search_configs_json"] = _escape_json_for_script(json.dumps([
        {
            "layer": cfg.layer_name,
            "popup_fields": [f.strip() for f in (cfg.popup_fields or "").split(",") if f.strip()],
        }
        for cfg in search_configs
    ]))

    return ctx


def _build_ogc_filter(query, fields):
    """Build OGC Filter XML for PropertyIsLike over multiple fields.

    Field names and the query are XML-escaped (not URL-quoted): the caller
    passes the whole filter through urllib.parse.urlencode, which performs
    the single URL-encoding of the FILTER parameter. URL-quoting here would
    double-encode (e.g. %20 -> %2520) and break searches for field names or
    values containing spaces/special characters.
    """
    clauses = "\n".join(
        f'<ogc:PropertyIsLike wildCard="*" singleChar="?" escapeChar="!">'
        f'<ogc:PropertyName>{xml_escape(f)}</ogc:PropertyName>'
        f'<ogc:Literal>*{xml_escape(query)}*</ogc:Literal>'
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
    project = _get_project_for_viewer(request, pk)
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
        # POST the params as form-urlencoded instead of GET: a search across a
        # layer with many fields produces an OGC Filter that overflows the URI
        # length limit on GET (HTTP 414 Request-URI Too Large), silently
        # swallowing every result. QGIS Server accepts the same parameters in
        # a POST body with no practical size limit.
        params = urllib.parse.urlencode({
            "MAP": map_path,
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "GetFeature",
            "TYPENAME": cfg.layer_name,
            "FILTER": filter_xml,
            "OUTPUTFORMAT": "application/json",
            "SRSNAME": "EPSG:3857",
            # Limit server-side: a broad filter over a large layer can match
            # tens of thousands of features, and loading that whole payload
            # before slicing client-side is slow and memory-heavy.
            "MAXFEATURES": cfg.max_results,
        }).encode("utf-8")
        req = urllib.request.Request(qgis_base, data=params, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
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


# OGC services/operations the web viewer is allowed to run through the WMS
# proxy. The proxy exists solely to serve map tiles, legends and feature-info
# to the browser; everything else (WFS bulk GetFeature export, WCS,
# GetPrint, GetProjectSettings, ...) is rejected with 403 before it reaches
# QGIS Server. Search and identify do NOT use the proxy (they call QGIS
# Server server-side), so restricting it to WMS breaks nothing in the viewer.
# Values are upper-cased for a case-insensitive compare (OGC parameter names
# are case-insensitive per spec).
ALLOWED_PROXY_SERVICES = {"WMS"}
ALLOWED_PROXY_WMS_OPERATIONS = {
    "GETMAP",
    "GETFEATUREINFO",
    "GETLEGENDGRAPHIC",
    "GETCAPABILITIES",
}


def wms_proxy_view(request, pk):
    project = _get_project_for_viewer(request, pk)
    params = request.GET.copy()

    # Reject duplicate SERVICE/REQUEST parameters: QueryDict only exposes the
    # last value for a repeated key, while urlencode() forwards them all, so
    # an attacker could smuggle a disallowed operation in the first occurrence
    # (e.g. SERVICE=WFS&SERVICE=WMS). Names are compared case-insensitively;
    # lists() is used because keys()/items() collapse duplicates to last value.
    if any(
        sum(len(vals) for k, vals in request.GET.lists() if k.upper() == name) > 1
        for name in ("SERVICE", "REQUEST")
    ):
        return HttpResponse(
            "WMS proxy: duplicate SERVICE/REQUEST parameters not allowed",
            status=403,
            content_type="text/plain",
        )

    # WMS-only allow-list: reject any OGC service/operation the web viewer
    # never needs before it reaches QGIS Server. Both the parameter names and
    # values are case-insensitive (OGC spec), so normalize both.
    params_upper = {k.upper(): v for k, v in request.GET.items()}
    service = params_upper.get("SERVICE", "").upper()
    request_op = params_upper.get("REQUEST", "").upper()
    if (
        service not in ALLOWED_PROXY_SERVICES
        or request_op not in ALLOWED_PROXY_WMS_OPERATIONS
    ):
        return HttpResponse(
            "WMS proxy: operation not allowed",
            status=403,
            content_type="text/plain",
        )

    map_path = remap_map_path(project.file.path.replace("\\", "/"))
    qgis_base = settings.QGIS_SERVER_URL.rstrip("/")
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


@xframe_options_exempt
def view_view(request, pk):
    try:
        project = _get_project_for_viewer(request, pk)
    except PermissionDenied:
        # Non-published projects need a login; send anonymous visitors to the
        # login page (with a return link) instead of a bare 403. Data endpoints
        # keep raising PermissionDenied so the viewer JS sees a 403.
        if not request.user.is_authenticated:
            # The middleware strips the tenant slug from request.path, so
            # rebuild the full path (with tenant prefix) for the ?next= link.
            from django.utils.http import urlencode
            next_url = request.tenant_base + request.get_full_path()
            from django.urls import reverse
            login_url = request.tenant_base + reverse("accounts:login")
            return HttpResponseRedirect(f"{login_url}?{urlencode({'next': next_url})}")
        raise
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
    import urllib.parse
    import urllib.request

    i = request.GET.get("i")
    j = request.GET.get("j")
    bbox = request.GET.get("bbox")
    width = request.GET.get("width")
    height = request.GET.get("height")
    layer = request.GET.get("layer", "")
    query_layers = request.GET.get("query_layers", layer)
    project = _get_project_for_viewer(request, pk)

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
            # Parse the tab structure from the unsanitized HTML first (the
            # parser keys off class/data attributes), then sanitize every
            # fragment the browser will inject via innerHTML.
            tabs = parse_qgis_form_tabs(html_content)
            html_content = sanitize_qgis_html(html_content)
            for tab in tabs:
                tab["html"] = sanitize_qgis_html(tab["html"])
    except Exception:
        pass

    # QGIS Server GetFeatureInfo returns null geometry; backfill geometries via
    # WFS GetFeature (by feature id) so the viewer can highlight features.
    feature_ids = [f.get("id") for f in features if f.get("id")]
    if feature_ids and any(f.get("geometry") is None for f in features):
        typenames = sorted({fid.split(".")[0] for fid in feature_ids if "." in fid})
        geom_by_id = {}
        for typename in typenames:
            ids_for_layer = [fid for fid in feature_ids if fid.split(".")[0] == typename]
            wfs_params = urllib.parse.urlencode({
                "MAP": map_path,
                "SERVICE": "WFS",
                "VERSION": "2.0.0",
                "REQUEST": "GetFeature",
                "TYPENAMES": typename,
                "FEATUREID": ",".join(ids_for_layer),
                "OUTPUTFORMAT": "application/json",
                "SRSNAME": "EPSG:3857",
            })
            try:
                req = urllib.request.Request(
                    f"{settings.QGIS_SERVER_URL.rstrip('/')}?{wfs_params}",
                    method="GET",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    wfs_data = json.loads(resp.read())
                for wf in wfs_data.get("features", []):
                    if wf.get("id") and wf.get("geometry"):
                        geom_by_id[wf["id"]] = wf["geometry"]
            except Exception:
                continue
        for f in features:
            if f.get("geometry") is None and f.get("id") in geom_by_id:
                f["geometry"] = geom_by_id[f["id"]]

    grouped = {}
    for f in features:
        fid = f.get("id", "")
        layer_name = fid.split(".")[0] if "." in fid else query_layers.split(",")[0]
        grouped.setdefault(layer_name, []).append(f)

    qgs_content = _read_qgs_from_qgz(local_path)
    tab_structure = parse_qgs_tab_structure(qgs_content)
    image_fields = parse_qgs_external_resource_fields(qgs_content)

    feature_tabs = []
    if features:
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
        # All four payloads are embedded inside inline <script> blocks, so they
        # must not be able to terminate the block (see _escape_json_for_script).
        "features_geojson": _escape_json_for_script(
            json.dumps({"type": "FeatureCollection", "features": features})
        ),
        "grouped": grouped,
        "error": None if features else "No features found at this location",
        "html_content": _escape_json_for_script(html_content),
        "tabs_json": _escape_json_for_script(json.dumps(tabs)),
        "feature_tabs_json": _escape_json_for_script(json.dumps(feature_tabs)),
        "project_pk": project.pk,
    })
