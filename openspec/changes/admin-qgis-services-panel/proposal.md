## Why

The Django admin is the primary interface for managing projects, but there's no way to verify that a project's QGIS Server configuration is working without manually constructing URLs and hitting the API from outside. Admins need to see paths, service status, and access raw capabilities XML directly in the change view.

## What Changes

- Add a read-only "QGIS Server" section to the Project admin change form
- Display local and remapped file paths for the project
- Show WMS and WFS service availability with live status checks
- Show layer count and queryable layer count for WMS
- Provide links to raw WMS/WFS GetCapabilities XML (GeoServer-style)
- Section is collapsible since it's diagnostic info

## Capabilities

### New Capabilities
- `admin-qgis-info-panel`: Read-only QGIS Server info section in Project admin change view showing paths, service status, and capabilities links

### Modified Capabilities
(none)

## Impact

- `georidge_platform/apps/projects/admin.py` — `ProjectAdmin` custom template and context
- `templates/admin/projects/project/change_form.html` — new template override or inline section
- Live QGIS Server queries on admin page load (acceptable for admin-only use)
