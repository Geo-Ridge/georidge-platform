## 1. Model & Admin

- [x] 1.1 Add `popup_fields` CharField to `LayerSearchConfig` model (max_length=512, blank=True, default="") with help_text describing comma-separated format
- [x] 1.2 Add `popup_fields` to `LayerSearchConfigAdmin` fieldsets
- [x] 1.3 Generate and run migration for the new field

## 2. Backend: Map-Config Context

- [x] 2.1 Update `views.py` `_get_wms_context_for_request` to include `search_configs` in the map-config JSON (array of `{ layer, popup_fields }` for active configs, with `popup_fields` parsed from comma-separated string to array)
- [x] 2.2 Update `map-only.html` map-config `<script>` block to include `searchConfigs` from context

## 3. Backend: Dispatcher

- [x] 3.1 Add `elif theme.layout_preset == "map-only"` branch to `viewer.html` to include `viewer/layouts/map-only.html`

## 4. Frontend: Map-Only Template

- [x] 4.1 Create `templates/viewer/layouts/map-only.html` — full-viewport map with floating search container, zoom controls, and script includes for `map-core.js`, `search-manager.js`, `search-popup.js`

## 5. Frontend: Map-Only CSS

- [x] 5.1 Create `static/viewer/css/layouts/map-only.css` — floating search bar positioning (absolute, top-center), simple popup styling, zoom controls positioning, body/html reset for full viewport

## 6. Frontend: Search-Select Event

- [x] 6.1 Edit `search-manager.js` `selectResult()` function to dispatch a `search-select` CustomEvent on `document` with `detail: { label, layer_title, layer, bbox, geojson }`

## 7. Frontend: Search Popup

- [x] 7.1 Create `static/viewer/js/search-popup.js` — listen for `search-select` event, read `searchConfigs` from map-config JSON, look up `popup_fields` by layer name, render simple positioned popup with label + filtered properties + layer title, dismiss on outside click
