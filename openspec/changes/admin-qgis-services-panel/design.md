## Context

The Project admin change form has no visibility into whether the project's QGIS Server configuration is actually working. Admins must manually construct URLs and test them externally. The `qgis_server/services.py` module already has all the helper functions needed: `remap_map_path()`, `get_wms_layers()`, `validate_on_server()`, `get_layer_fields()`, and `_qgis_url()`.

## Goals / Non-Goals

**Goals:**
- Show local and remapped file paths in a read-only section
- Show WMS and WFS service status with live checks
- Show layer count and queryable count for WMS
- Link to raw WMS/WFS GetCapabilities XML (GeoServer-style)
- Collapsible section (diagnostic info, not always needed)

**Non-Goals:**
- No write/edit capabilities in this section
- No per-layer WFS status (too expensive, WFS DescribeFeatureType is per-layer)
- No caching (admin-only, slow queries acceptable)
- No custom admin template override (use inline readonly fields + format_html)

## Decisions

### 1. Render via readonly methods, not custom template

Use `@admin.display(description=...)` methods on `ProjectAdmin` that return `format_html(...)` with styled HTML. This avoids creating a custom `change_form.html` and keeps everything in Python.

**Alternatives considered:**
- Custom `change_form.html` template — more layout control but adds template file and overrides Django's default admin rendering. Overkill for a single section.

### 2. Place section after Base Maps fieldset

Add a new fieldset "QGIS Server" after the existing Base Maps section. This groups all diagnostic info together at the bottom.

### 3. Make paths and URLs readonly fields

The paths are derived from `project.file.path` and `settings` — they shouldn't be editable. Use `get_readonly_fields()` to add them only when editing an existing object (not on add form).

### 4. Service status computed in methods, not in `__init__`

Each readonly method calls its respective service function directly. If the service is unreachable, show a red "Offline" indicator. This is simple and each method is independently testable.

### 5. Capabilities links open in new tab

Links to raw XML use `target="_blank"` so admins don't lose their place in the change form.

## Risks / Trade-offs

- **Slow page loads** → Mitigated by making the section collapsible (`collapse` class). Admins who don't need it can ignore it.
- **QGIS Server timeout** → Each service check has a 10-second timeout. If QGIS Server is down, the page still loads, just shows "Offline".
- **No WFS layer-level status** → Acceptable trade-off. WFS availability is binary per-project and can be inferred from WMS layer data.

## Migration Plan

No migration needed — this is purely a UI change to the admin interface.
