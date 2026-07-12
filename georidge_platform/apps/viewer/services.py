import io
import json
import logging
import os
import zipfile

from django.conf import settings
from django.http import FileResponse

from georidge_platform.apps.qgis_server.services import get_layer_fields, get_wms_layers
from georidge_platform.apps.viewer.models import LayerSearchConfig, ThemeProfile

logger = logging.getLogger(__name__)


def sync_search_layers(project):
    """Sync LayerSearchConfig rows from QGIS Server.

    Called after project save. Creates configs for new queryable layers,
    deactivates configs for removed layers, and updates field lists for
    existing layers while preserving checked fields.
    """
    try:
        layers = get_wms_layers(project)
    except Exception:
        logger.warning("sync_search_layers: get_wms_layers failed for project %s", project.pk)
        return

    queryable = [l for l in layers if l.get("queryable")]
    active_names = {l["name"] for l in queryable}
    existing = {c.layer_name: c for c in LayerSearchConfig.objects.filter(project=project)}

    # Deactivate configs for layers no longer in the project
    for layer_name, config in existing.items():
        if layer_name not in active_names:
            config.active = False
            config.save(update_fields=["active"])
            logger.info("Deactivated search config for layer '%s' (project %s)", layer_name, project.pk)

    # Create/update configs for current layers
    for layer in queryable:
        name = layer["name"]
        title = layer["title"]
        try:
            fields = get_layer_fields(project, name)
        except Exception:
            fields = []

        if name in existing:
            config = existing[name]
            old_fields = set(config.searchable_fields or [])
            new_fields = set(fields)
            # Preserve checked fields that still exist
            preserved = [f for f in config.searchable_fields if f in new_fields]
            config.searchable_fields = preserved
            config.available_fields = fields
            config.layer_title = title
            if not config.active:
                config.active = True
            config.save(update_fields=["searchable_fields", "available_fields", "layer_title", "active"])
            logger.info(
                "Updated search config for layer '%s' (project %s): %d fields preserved, %d available",
                name, project.pk, len(preserved), len(fields),
            )
        else:
            config = LayerSearchConfig.objects.create(
                project=project,
                layer_name=name,
                layer_title=title,
                searchable_fields=fields,
                available_fields=fields,
                active=True,
            )
            logger.info(
                "Created search config for layer '%s' (project %s): %d fields",
                name, project.pk, len(fields),
            )


def _get_icon_dir():
    return os.path.join(
        os.path.dirname(__file__), "static", "viewer", "icons"
    )


def export_theme_zip(theme):
    """Build a ZIP in memory containing theme.json, images, and icon set."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        data = {
            "name": theme.name,
            "description": theme.description,
            "primary_color": theme.primary_color,
            "secondary_color": theme.secondary_color,
            "background_color": theme.background_color,
            "surface_color": theme.surface_color,
            "text_color": theme.text_color,
            "text_muted_color": theme.text_muted_color,
            "border_color": theme.border_color,
            "toolbar_bg": theme.toolbar_bg,
            "toolbar_border": theme.toolbar_border,
            "panel_bg": theme.panel_bg,
            "panel_border": theme.panel_border,
            "statusbar_bg": theme.statusbar_bg,
            "statusbar_border": theme.statusbar_border,
            "accent_color": theme.accent_color,
            "danger_color": theme.danger_color,
            "success_color": theme.success_color,
            "warning_color": theme.warning_color,
            "show_legend": theme.show_legend,
            "show_toolbar": theme.show_toolbar,
            "show_statusbar": theme.show_statusbar,
            "show_banner": theme.show_banner,
            "banner_title": theme.banner_title,
            "banner_subtitle": theme.banner_subtitle,
            "banner_bg": theme.banner_bg,
            "banner_text_color": theme.banner_text_color,
            "banner_height": theme.banner_height,
            "icon_set": theme.icon_set,
            "layout_preset": theme.layout_preset,
            "has_logo": bool(theme.logo),
            "has_banner_image": bool(theme.banner_image),
        }
        zf.writestr("theme.json", json.dumps(data, indent=2))

        if theme.logo and theme.logo.path and os.path.exists(theme.logo.path):
            ext = os.path.splitext(theme.logo.name)[1] or ".png"
            zf.write(theme.logo.path, f"logo{ext}")

        if theme.banner_image and theme.banner_image.path and os.path.exists(theme.banner_image.path):
            ext = os.path.splitext(theme.banner_image.name)[1] or ".jpg"
            zf.write(theme.banner_image.path, f"banner{ext}")

        icon_dir = os.path.join(_get_icon_dir(), theme.icon_set)
        if os.path.isdir(icon_dir):
            for filename in sorted(os.listdir(icon_dir)):
                filepath = os.path.join(icon_dir, filename)
                if os.path.isfile(filepath):
                    zf.write(filepath, f"icons/{theme.icon_set}/{filename}")

    buf.seek(0)
    slug = theme.name.lower().replace(" ", "-").replace("_", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    response = FileResponse(buf, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="theme-{slug}.zip"'
    return response
