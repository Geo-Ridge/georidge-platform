## Why

The viewer panels (layers panel, feature info panel, and identify popup) are all hardcoded to 320px width across all three layout presets. Users cannot adjust panel sizes to suit their screen or workflow — a wide monitor wastes space, while a small screen cramps the content.

## What Changes

- Add an invisible drag handle on the right edge of the main side panel in all three layouts (MapGuide, MapStore, QWC2)
- Add an invisible drag handle on the right edge of the floating identify popup
- Dragging the handle resizes the panel width (min ~200px, max ~50% viewport)
- MapGuide: map flex-adjusts as the panel grows/shrinks
- MapStore/QWC2: panel grows over the map (map unchanged)
- Identify popup: resizes in place, retains drag-to-move on header

## Capabilities

### New Capabilities
- `resizable-side-panel`: Main side panel (layers + info tabs) is resizable via invisible drag handle on right edge
- `resizable-identify-popup`: Floating identify popup is resizable via invisible drag handle on right edge

### Modified Capabilities

## Impact

- `viewer.css` — shared resize handle styles (invisible bar, cursor, transitions)
- `layouts/mapguide.html` — add resize handle div, JS for resize logic
- `layouts/mapstore.html` — add resize handle div, JS for resize logic
- `layouts/qwc2.html` — add resize handle div, JS for resize logic
- `static/viewer/js/identify-popup.js` — add resize handle to popup, resize logic
- `static/viewer/js/mapstore-layers-panel.js` — handle panel resize
- `static/viewer/js/qwc2-slide-panel.js` — handle panel resize
- `static/viewer/css/layouts/mapstore.css` — panel width override styles
- `static/viewer/css/layouts/qwc2.css` — panel width override styles
