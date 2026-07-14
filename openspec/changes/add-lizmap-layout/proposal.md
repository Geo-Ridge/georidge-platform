## Why

Users familiar with Lizmap expect a similar UI paradigm: thin left icon sidebar + tabbed dock panel. Adding this as a layout option gives GeoRidge Platform visual parity with Lizmap without replicating its full feature set (filter, dataviz, permalink).

## What Changes

- Add `LIZMAP` to `ThemeProfile.LayoutPreset` choices
- Create `lizmap.html` template with left icon sidebar + tabbed dock panel
- Create `lizmap.css` for layout-specific styling
- Seed a "Lizmap Classic" theme in `DEFAULT_THEMES`

## Capabilities

### New Capabilities
- `lizmap-layout`: Lizmap-style left sidebar with tabbed dock panel (Layers + Feature Info)

### Modified Capabilities
(none)

## Impact

- `models.py` — add LIZMAP choice (no migration, max_length=20 covers it)
- `viewer.html` — add layout dispatch for lizmap
- `layouts/lizmap.html` — new template
- `css/layouts/lizmap.css` — new stylesheet
- `apps.py` — add Lizmap Classic theme to DEFAULT_THEMES
