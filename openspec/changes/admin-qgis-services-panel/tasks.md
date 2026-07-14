## 1. Add readonly methods to ProjectAdmin

- [x] 1.1 Add `get_qgis_local_path` readonly method — returns `project.file.path` or "No file uploaded"
- [x] 1.2 Add `get_qgis_server_path` readonly method — returns `remap_map_path(project.file.path)` or "No file uploaded"
- [x] 1.3 Add `get_wms_status` readonly method — calls `validate_on_server()`, returns styled HTML with Online/Offline indicator, layer count, queryable count
- [x] 1.4 Add `get_wfs_status` readonly method — makes a lightweight WFS GetCapabilities request, returns styled HTML with Online/Offline indicator
- [x] 1.5 Add `get_wms_capabilities_link` readonly method — returns `format_html('<a href="..." target="_blank">WMS Capabilities</a>')` pointing to WMS GetCapabilities URL
- [x] 1.6 Add `get_wfs_capabilities_link` readonly method — returns `format_html('<a href="..." target="_blank">WFS Capabilities</a>')` pointing to WFS GetCapabilities URL

## 2. Wire into admin

- [x] 2.1 Add "QGIS Server" fieldset to `ProjectAdmin.fieldsets` after Base Maps, with `collapse` class
- [x] 2.2 Update `get_readonly_fields()` to include QGIS Server readonly fields only when editing (obj is not None)

## 3. Styling

- [x] 3.1 Add inline CSS for the QGIS Server section — green/red status indicators, path display styling
