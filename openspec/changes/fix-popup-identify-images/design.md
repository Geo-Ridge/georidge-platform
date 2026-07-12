## Context

Feature info images are broken in MapStore and QWC2 layout presets. The identify flow involves two JS modules:

1. `identify-manager.js` — processes the XHR response, extracts structured data (`data-feature-tabs`, `data-qgis-html`), renders to `#info-content`, then **strips** the data from the HTML before dispatching `identify-complete`
2. `identify-popup.js` — listens for `identify-complete`, receives cleaned HTML, tries to re-parse the same JSON payloads — but they're gone

MapGuide works because it never loads `identify-popup.js` and renders directly to `#info-content` with full data. MapStore and QWC2 use the popup, which falls back to plain property tables with no images.

Key difference: `identify-manager.js` strips `data-feature-tabs` and `data-qgis-html` (lines 106, 113) but does NOT strip `data-tabs` (raw HTML tabgroups). So the popup's fallback to `data-tabs` partially works when QGIS forms have tabgroups, but the structured media data from `data-feature-tabs` (with proper image field detection) is always lost.

## Goals / Non-Goals

**Goals:**
- Feature info images display correctly in MapStore and QWC2 layouts
- Structured `featureTabs` data (with properly resolved image URLs) reaches the popup
- No change to MapGuide behavior (it already works)

**Non-Goals:**
- Changing the server-side rendering or template structure
- Modifying the `#info-content` panel rendering path
- Changing the popup UI/design

## Decisions

### Decision 1: Pass pre-parsed data through the event detail

**Choice:** Add `featureTabs`, `qgisHtml`, and `tabsHtml` to the `identify-complete` event detail.

**Rationale:** The data is already parsed by `identify-manager.js`. Passing it through the event avoids redundant regex parsing in the popup and ensures the popup gets the same structured data that the panel uses.

**Alternatives considered:**
- Don't strip the data from HTML (let popup re-parse): Rejected because it means two modules independently parsing the same HTML, which is fragile and wasteful
- Have a shared data store: Rejected as over-engineered for this case

### Decision 2: Popup uses pre-parsed data with HTML fallback

**Choice:** `identify-popup.js` checks `event.detail.featureTabs` first, then `event.detail.qgisHtml`, then falls back to parsing `data-tabs` from the HTML (which is NOT stripped by the manager).

**Rationale:** The `data-tabs` script tag is never stripped by `identify-manager.js`, so it remains available in the HTML as a fallback. This preserves the existing behavior for cases where structured data isn't available.

## Risks / Trade-offs

- **Event API change**: The `identify-complete` event gains new properties. Any external code listening to this event is unaffected (extra properties are ignored). → Low risk.
- **No regression for MapGuide**: MapGuide doesn't listen to `identify-complete` for popup rendering. The event change is invisible to it. → Zero risk.

## Migration Plan

No migration needed. Pure client-side JS change. Deploy and hard-refresh to pick up new static files.
