## Why

Feature info images are broken in MapStore and QWC2 layout presets. When a user clicks a feature on the map, the identify popup shows property data but images from ExternalResource fields are missing. MapGuide layout works correctly because it renders directly to `#info-content`, while the popup path (used by MapStore/QWC2) receives HTML with image data already stripped.

## What Changes

- Modify `identify-manager.js` to pass parsed `featureTabs` and `qgisHtml` data through the `identify-complete` event detail instead of only passing cleaned HTML
- Modify `identify-popup.js` to consume pre-parsed data from the event detail rather than re-parsing JSON from stripped HTML
- Ensure all three layout presets (MapGuide, MapStore, QWC2) display feature info images correctly

## Capabilities

### New Capabilities
- `feature-info-images`: Feature info panel correctly displays images from QGIS ExternalResource fields across all layout presets

### Modified Capabilities

## Impact

- `georidge_platform/apps/viewer/static/viewer/js/identify-manager.js` — event dispatch includes parsed data
- `georidge_platform/apps/viewer/static/viewer/js/identify-popup.js` — consumes pre-parsed data instead of re-parsing HTML
