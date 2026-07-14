## Context

GeoRidge Platform has 4 layout presets (mapguide, mapstore, qwc2, map-only). Users want a Lizmap-style layout: thin left icon sidebar + tabbed dock panel. The Lizmap demo uses a left sidebar with icon buttons (Layers, Information, Popup, Dataviz, Filter) that switch tabbed dock content.

## Goals / Non-Goals

**Goals:**
- Add `LIZMAP` layout preset with left icon sidebar + tabbed dock
- Reuse all existing JS modules (no new JS files)
- Seed a "Lizmap Classic" theme with Lizmap's default blue/white colors
- Keep it focused: Layers tab + Feature Info tab only

**Non-Goals:**
- Filter panel (attribute-based filtering)
- Dataviz panel
- Permalink functionality
- Overview map
- New JS modules

## Decisions

### 1. Reuse existing JS modules

All existing JS files work with any layout as long as the DOM element IDs match:
- `#map-canvas` — map container
- `#layer-tree` — layer tree container
- `#info-content` — feature info container
- `#basemap-toggle`, `#basemap-panel`, `#basemap-list` — base map switcher

### 2. No migration needed

`layout_preset` has `max_length=20`. The string `"lizmap"` is 6 chars. Django choices are display-only — no DB constraint enforced.

### 3. Sidebar structure

Two sections:
1. **Top section** — icon buttons (Layers, Identify, Zoom In/Out, Full Extent, Measure, Print)
2. **Bottom section** — tab switcher (Layers tab, Feature Info tab)

This separates tools from navigation, matching Lizmap's approach.

## Risks / Trade-offs

- **Limited feature set** — No filter/dataviz/overview. Users who need those would use Lizmap directly. Acceptable for now.
- **No new JS** — The identify-manager and layer-manager already handle tab switching. The lizmap layout just reorganizes the DOM.
