## Why

The map viewer needs to be embeddable in external websites as a lightweight lookup tool (e.g., cemetery grave search). The existing layouts (MapGuide, MapStore, QWC2) are full-featured with toolbars, panels, and banners that are unnecessary and visually heavy for embedded use. A minimal theme with just a floating search bar and simple popup provides a clean, focused experience for end users who only need to search and locate features.

## What Changes

- Add a new `map-only` layout template: bare map with floating search overlay, no toolbar, panels, banner, or status bar
- Add `popup_fields` field to `LayerSearchConfig` (comma-separated) so admins control which properties appear in the search result popup
- Create a lightweight popup component that displays the search result label, configured extra fields, and layer title
- Expose search config (including `popup_fields`) in the map-config JSON so the frontend can render popups without additional backend requests
- Dispatch a `search-select` custom event from `search-manager.js` when a result is selected, enabling the popup bridge

## Capabilities

### New Capabilities
- `minimal-theme`: The map-only layout template, floating search bar, simple popup, and associated CSS/JS for an embeddable minimal viewer
- `popup-field-config`: Admin-configurable `popup_fields` on `LayerSearchConfig` that controls which WFS properties display in the search result popup

### Modified Capabilities

## Impact

- **Models**: `LayerSearchConfig` gains one new field (`popup_fields`)
- **Admin**: `LayerSearchConfigAdmin` includes the new field
- **Migration**: Auto-generated migration for the new field
- **Views**: `views.py` adds `search_configs` to the map-config JSON context
- **Templates**: New `layouts/map-only.html` and `viewer.html` dispatcher update
- **CSS**: New `css/layouts/map-only.css`
- **JS**: New `js/search-popup.js`, minor edit to `js/search-manager.js` (add event dispatch)
- **Existing layouts**: No changes — all existing layouts unaffected
