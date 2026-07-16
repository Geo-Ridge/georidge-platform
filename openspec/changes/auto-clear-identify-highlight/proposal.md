## Why

In other mapping applications, selecting a feature shows a popup or populates a dock with the feature info, and **closing that popup or hiding that dock automatically clears the on-map highlight**. GeoRidge Platform does not do this today:

- The identify highlight (blue geometry drawn on the map) only disappears when the user manually clicks a "Clear Highlight"/"Clear" button, or starts a new identify click.
- Closing the floating identify popup (`identify-popup.js`) only hides the popup — the highlight stays on the map.
- Collapsing/hiding the info dock/panel (`qwc2-slide-panel.js`, `lizmap`/`mapguide` dock toggles, `mapstore` sidebar) does not clear the highlight either.

This leaves stale highlights on the map and makes the dedicated "Clear Highlight" button a required manual step that other apps don't need.

## What Changes

- **Auto-clear on close/hide**: Dispatching the existing `identify-clear` event whenever an identify display is closed or fully hidden/collapsed. The event already exists and `identify-manager.js` already listens to it to call `highlightSource.clear()`.
- **Full hide/collapse only**: Switching tabs *within* a dock (e.g. Layers ⇄ Info) does **not** clear the highlight — only a full hide/collapse of the identify display does.
- **Remove manual "Clear Highlight" buttons**: The dedicated identify-clear buttons are removed from every layout (qwc2 trash button, mapstore sidebar clear, mapguide info-footer "Clear"). The measure-clear button is untouched.

## Affected close/hide points (dispatch `identify-clear`)

1. **Popup close button** — `identify-popup.js` close handler.
2. **QWC2 slide panel** — `qwc2-slide-panel.js` `togglePanel` when closing.
3. **Lizmap dock** — `lizmap.html` inline `lizToggleDock` / `lizSwitchTab` when collapsing.
4. **MapGuide dock** — `mapguide.html` inline `toggleDock` when collapsing.
5. **MapStore sidebar/panel** — `mapstore-sidebar.js` / `mapstore-layers-panel.js` close.

## Removed manual buttons

- `qwc2.html` trash "Clear Highlight" button + `qwc2ClearHighlight` in `qwc2-navbar.js`.
- `mapstore.html` sidebar "Clear" button + `mapstoreClearHighlight` in `mapstore-sidebar.js`.
- `mapguide.html` info-footer "Clear" button + its wiring in `identify-manager.js`.
- (Lizmap has no manual clear button today — nothing to remove.)

## Capabilities

### New Capabilities
- `auto-clear-identify-highlight`: Closing or fully hiding any identify display (popup or dock/panel) automatically clears the map highlight. The manual clear-highlight button is removed; full hide/collapse only (tab switches within a dock do not clear).

### Modified Capabilities
(none)

## Impact

- `apps/viewer/static/viewer/js/identify-popup.js` — close button dispatches `identify-clear`.
- `apps/viewer/static/viewer/js/qwc2-slide-panel.js` — dispatch on close.
- `apps/viewer/static/viewer/js/mapstore-sidebar.js` / `mapstore-layers-panel.js` — dispatch on close.
- `templates/viewer/layouts/lizmap.html` — inline dock toggle dispatches on collapse.
- `templates/viewer/layouts/mapguide.html` — inline dock toggle dispatches on collapse; remove clear button.
- `templates/viewer/layouts/qwc2.html` — remove trash button.
- `templates/viewer/layouts/mapstore.html` — remove sidebar clear button.
- `apps/viewer/static/viewer/js/qwc2-navbar.js` — remove `qwc2ClearHighlight`.
- `apps/viewer/static/viewer/js/mapstore-sidebar.js` — remove `mapstoreClearHighlight`.
- `apps/viewer/static/viewer/js/identify-manager.js` — remove `clear-identify` button wiring (now dead).

## Known Tradeoff

In **qwc2** and **mapstore** both a floating popup AND the dock can show the same identify result simultaneously. Under the rule "closing/hiding any identify display clears the highlight", closing only the popup clears the highlight even though the dock still shows the info text (highlight gone, text remains). This follows the explicit decision; no ref-counting is added. Revisit if this proves confusing in practice.
