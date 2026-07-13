## Context

The GeoRidge map viewer currently has three layout presets (MapGuide, MapStore, QWC2), all full-featured with toolbars, panels, and banners. A fourth preset `map-only` exists in the model choices but has no template — it silently falls back to MapGuide.

The use case is embedding the viewer in external websites (e.g., cemetery lookup tools) where users search for a feature by name, see results in a dropdown, select one, and view a simple popup with key details. No layer management, measurement, printing, or other GIS tools are needed.

The existing search infrastructure (backend WFS search endpoint + frontend search-manager.js) already handles search input, dropdown results, and zoom-to-feature. The missing pieces are: (1) a bare-bones layout template, (2) a popup that shows search result data, and (3) admin configuration of which fields appear in that popup.

## Goals / Non-Goals

**Goals:**
- Create a working `map-only` layout: full-viewport map with floating search bar and simple popup
- Add `popup_fields` to `LayerSearchConfig` so admins control popup content per layer
- Expose search config in map-config JSON so the frontend can render popups client-side
- Dispatch a `search-select` event from search-manager.js to decouple search from popup rendering

**Non-Goals:**
- Full identify-on-click (map clicks do nothing in this layout)
- Layer toggling, measurement, printing, basemap switching
- Drag/resize on the popup (it's a simple static overlay)
- Modifying any existing layout behavior

## Decisions

### 1. New template vs. CSS overrides on QWC2

**Decision:** New `layouts/map-only.html` template.

**Rationale:** QWC2's navbar HTML renders ~70 lines of toolbar buttons, hamburger menu, slide panel, and basemap selector. Hiding all of this via CSS is fragile — any future QWC2 update could break the minimal theme. A dedicated template is ~55 lines and includes only what's needed.

### 2. Popup content: backend vs. frontend rendering

**Decision:** Frontend renders popup from `popup_fields` config exposed in map-config JSON.

**Rationale:** The search endpoint already returns all WFS properties in the GeoJSON feature. Adding `popup_fields` to the response would require backend changes to every search result. Instead, expose the search configs (including `popup_fields`) once in the map-config JSON, and let the frontend filter properties client-side. Zero backend changes to the search view.

### 3. Search → popup bridging: event dispatch

**Decision:** search-manager.js dispatches a `search-select` custom event; a new `search-popup.js` listens and renders.

**Rationale:** Keeps search-manager.js focused on search logic. The popup is a separate concern. Custom events are the existing pattern (see `identify-complete`, `identify-clear`). No coupling between search and popup modules.

### 4. popup_fields format: comma-separated CharField

**Decision:** Simple comma-separated text in admin, parsed to array by frontend.

**Rationale:** Matches the admin simplicity of the rest of `LayerSearchConfig`. JSONField would be stricter but requires JSON editing in admin — overkill for a list of field names. The frontend splits on comma and trims whitespace.

### 5. Map click behavior in map-only layout

**Decision:** Map clicks are ignored (identify-manager.js is not loaded).

**Rationale:** The minimal theme is search-only. Loading identify-manager would fire WMS GetFeatureInfo on every click with no popup to display the results. Omitting it keeps the JS payload small and avoids confusing empty-click behavior.

## Risks / Trade-offs

- **popup_fields mismatch**: Admin enters a field name that doesn't exist in the WFS properties → popup shows nothing for that field. **Mitigation:** Frontend silently skips missing fields. No error shown.

- **Search config not found for layer**: Feature's layer doesn't have a `popup_fields` config → popup falls back to showing just the label. **Mitigation:** search-popup.js checks config by layer name, falls back gracefully.

- **Embedded iframe blocking**: Django's `XFrameOptionsMiddleware` blocks framing by default. **Mitigation:** Not addressed in this change — requires separate deployment config (CSP header or middleware override). Out of scope for the theme itself.
