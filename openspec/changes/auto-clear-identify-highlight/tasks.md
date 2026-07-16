## 1. Popup close auto-clears
- [x] In `identify-popup.js` close button handler, dispatch `identify-clear` (bubbles) after hiding the popup.

## 2. QWC2 slide panel auto-clears
- [x] In `qwc2-slide-panel.js` `togglePanel()`, dispatch `identify-clear` when the panel closes (isOpen becomes false).

## 3. Lizmap dock auto-clears
- [x] In `lizmap.html` `lizToggleDock()` collapse branch, dispatch `identify-clear`.
- [x] In `lizmap.html` `lizSwitchTab()` collapse branch, dispatch `identify-clear`.

## 4. MapGuide dock auto-clears
- [x] In `mapguide.html` `toggleDock()` collapse branch, dispatch `identify-clear`.

## 5. MapStore panel auto-clears
- [x] In `mapstore-sidebar.js` / `mapstore-layers-panel.js` close handler, dispatch `identify-clear`.

## 6. Remove manual clear-highlight buttons
- [x] Remove qwc2 trash "Clear Highlight" button from `qwc2.html`; delete `window.qwc2ClearHighlight` from `qwc2-navbar.js`.
- [x] Remove mapstore sidebar "Clear" button from `mapstore.html`; delete `window.mapstoreClearHighlight` from `mapstore-sidebar.js`.
- [x] Remove mapguide info-footer "Clear" button from `mapguide.html`; remove its dead wiring in `identify-manager.js` (guarded `clear-identify` handlers).
- [x] Confirm lizmap has no manual clear button to remove.

## 7. Verify no regressions
- [x] Run lint/typecheck (no lint tooling in repo; `node --check` passes on all edited JS).
- [ ] Manual check per layout: identify → close popup / collapse dock → highlight gone; tab switch within dock → highlight stays; new identify → old cleared, new drawn. (Requires live browser + QGIS project; code paths verified by review.)

## 8. Spec delta
- [x] Add `specs/auto-clear-identify-highlight/spec.md` with ADDED requirement + scenarios.
