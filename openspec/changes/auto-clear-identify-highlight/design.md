## Context

The identify flow draws a blue highlight geometry on the map (`identify-manager.js` → `highlightSource.addFeatures`). Today the highlight is only removed by:
- A manual "Clear Highlight"/"Clear" button (qwc2, mapstore, mapguide), or
- Starting a new identify click (`handleIdentifyClick` calls `clearHighlight()` first).

The `identify-clear` CustomEvent already exists and `identify-manager.js:174` already listens to it and clears the highlight. So the building blocks are present — we just need to **fire the event at the right moments** and **remove the manual buttons**.

## Decision

### 1. Reuse the existing event
No new event, no new listener. Just dispatch `new CustomEvent('identify-clear', { bubbles: true })` from each close/hide point. `identify-manager.js` already handles it.

### 2. Popup close (`identify-popup.js`)
The close button handler (currently only `popup.style.display = 'none'`) will additionally dispatch `identify-clear`. This clears the map highlight when the floating popup is dismissed.

### 3. Dock/panel hide — full collapse only
Each layout's dock-toggle function dispatches `identify-clear` **only when the panel transitions to the collapsed/hidden state**, not on every toggle call:
- `qwc2-slide-panel.js` `togglePanel()`: dispatch when `isOpen` becomes false.
- `lizmap.html` `lizToggleDock()` / `lizSwitchTab()` (collapse branch): dispatch.
- `mapguide.html` `toggleDock()` (collapse branch): dispatch.
- `mapstore-sidebar.js` / `mapstore-layers-panel.js` close handler: dispatch.

Tab switches *within* a dock (Layers ⇄ Info) must NOT dispatch — the identify display is still visible.

### 4. Remove manual clear buttons
- Delete the qwc2 trash "Clear Highlight" button (`qwc2.html`) and `window.qwc2ClearHighlight` in `qwc2-navbar.js`.
- Delete the mapstore sidebar "Clear" button (`mapstore.html`) and `window.mapstoreClearHighlight` in `mapstore-sidebar.js`.
- Delete the mapguide info-footer "Clear" button (`mapguide.html`) and its wiring in `identify-manager.js` (lines ~125, 163–172, guarded by `if (clearBtn)` so removal is safe).
- Lizmap: no manual button exists — nothing to remove.

### 5. Measure-clear untouched
`window.measureClear()` (clear.svg) is a separate concern (measurement geometry) and stays.

## Edge Cases
- **Repeated identifies**: `handleIdentifyClick` clears the previous highlight before drawing the new one, so normal identify-to-identify flow is unaffected.
- **Popup + dock both open (qwc2/mapstore)**: closing the popup clears the highlight even if the dock still shows info text. Per explicit decision; documented as tradeoff in proposal.
- **No identify active**: dispatching `identify-clear` with an empty `highlightSource` is a no-op (`clear()` on empty source is safe).

## Verification
- qwc2: identify feature → popup + highlight appear → close popup → highlight gone. Collapse slide panel → highlight gone.
- mapstore: identify → sidebar + popup → close popup / close sidebar → highlight gone.
- lizmap: identify → dock + highlight → collapse dock → highlight gone.
- mapguide: identify → dock + highlight → collapse dock → highlight gone; info-footer "Clear" button gone.
- Tab switch Layers⇄Info within any dock → highlight stays.
- New identify click after close → old cleared, new drawn (unchanged).
