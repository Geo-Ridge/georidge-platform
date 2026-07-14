## Why

The QGS XML parsers for tab structure and image field detection assume a fixed attribute ordering in the XML. QGIS 3.40+ serializes attributes in a different order (alphabetical by attribute name), causing both parsers to silently fail. Projects with tabs and images work in older QGIS versions but break in 3.40+ — no tabs are shown, no images are detected, and no error is reported.

## What Changes

- Replace the regex-based `parse_qgs_tab_structure()` with proper XML parsing that extracts `name` and `type` attributes regardless of order
- Replace the substring-based `parse_qgs_external_resource_fields()` with proper XML parsing that checks for `ExternalResource` widget type and `DocumentViewer` config regardless of attribute order
- Add a fallback in `group_attributes_by_tabs()` so that when `tab_structure` is empty, all fields are shown in a single "Attributes" tab (instead of producing no output)
- Add a fallback in `identify_view` so that when `feature_tabs` is empty but QGIS Server HTML contains tab groups, the HTML tabs are used (existing fallback path already exists, but the gate at line 506 prevents reaching it)

## Capabilities

### New Capabilities
- `qgs-xml-parsing`: Robust parsing of QGIS project XML for tab structure and image field detection, independent of XML attribute ordering

### Modified Capabilities

## Impact

- `georidge_platform/apps/viewer/views.py`: `parse_qgs_tab_structure()`, `parse_qgs_external_resource_fields()`, and the feature_tabs gate in `identify_view()`
- No API changes — this is a backend parsing fix
- No frontend changes — the client already handles the data correctly when it's provided
- Backward compatible — projects that worked before (with the old attribute order) will continue to work
