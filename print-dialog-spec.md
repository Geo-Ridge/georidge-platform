# Print Dialog — Specification

Status: Draft (pre-implementation)
Date: 2026-08-09
Author: Buffy (interviewed product owner)

## 1. Summary

Replace the viewer's current one-click print button — which simply downloads a PNG
of the OpenLayers canvas at on-screen resolution (`printMap()` in `map-core.js`) —
with a proper **print dialog** that offers:

- A **preview map** inside the dialog (MapStore-style) that the user can pan/zoom to
  define the printed area.
- **QGIS Server print layouts** (via `GetPrint`) when the project's `.qgz` contains
  them, plus a client-side "Plain map" export path that works for every project.
- Output as **PDF** and **JPG** downloads, at **DPI presets (72 / 150 / 300)**, on
  **A4 portrait or landscape**.

## 2. Current state (context gathered)

- Print entry points: one button per layout — `templates/viewer/layouts/{lizmap,qwc2,mapguide,mapstore}.html`
  and `templates/viewer/panels/toolbar.html` — all calling `window.printMap()`.
- `printMap()` (`georidge_platform/apps/viewer/static/viewer/js/map-core.js`):
  grabs the visible `<canvas>` and downloads `map.png` via `canvas.toDataURL('image/png')`.
  No options, no resolution control, no furniture.
- The viewer already proxies arbitrary WMS GET params to QGIS Server through
  `wms_proxy_view` (`georidge_platform/apps/viewer/views.py`, route
  `{tenant_base}/viewer/{pk}/wms/`), forwarding `Content-Disposition`/`Content-Length`
  headers. **GetPrint can flow through this proxy with zero new server infrastructure.**
- Base maps, theme, layer tree and search configs are serialized into the page as a
  `<script id="map-config">` JSON blob used by `map-core.js`, `layer-manager.js`, etc.
- `hideBaseMap()` + "No basemap" option already exist in the viewer (recent work).

### QGIS Server GetPrint findings (verified against the live server)

- `REQUEST=GetPrint` is a WMS vendor request that renders a QGIS print layout to
  PDF/PNG/SVG/JPG.
- This server version expects the **`TEMPLATE=<layout name>`** parameter (the modern
  docs name it `LAYOUT`; the live server rejects a missing template with
  `MissingParameterValue: The TEMPLATE parameter is missing.` and a bogus one with
  `InvalidParameterValue: The TEMPLATE parameter is invalid.`). The app should send
  both `TEMPLATE` and `LAYOUT` to be robust across QGIS Server versions.
- Extent override: `map0:extent=minx,miny,maxx,maxy` (or `map0:scale=`) — the layout's
  first map item (`map0`) extent is replaced by the requested one.
- Other params: `FORMAT=pdf|png|svg|jpg`, `DPI=<int>`, `VERSION=1.3.0`, `SERVICE=WMS`.
- Layout enumeration: **this QGIS Server version does not advertise its layouts**
  (no `PrintLayoutList` in GetProjectSettings). Layouts must be enumerated by parsing
  the project `.qgz` (a ZIP containing a `.qgs` XML; layouts appear as
  `<Layout name="...">`). The Django app can do this since media is on its filesystem.
- Reality check: only **project 6** (`cemetery.qgz`) currently contains a print layout
  ("Ownership Certificate"); projects 1–5, 7, 19 have none. Project 6 is currently
  unloadable on QGIS Server ("Layer(s) not valid" — missing data sources), so its
  layout cannot be served until the project is fixed.

## 3. Goals

1. Give users a real print dialog with a pan/zoomable preview map.
2. Use QGIS Server print layouts when available (professional output: title blocks,
   north arrow, scale bar, legend as authored in QGIS Desktop).
3. Guarantee every project can still be printed via a client-side "Plain map" fallback.
4. Offer PDF + JPG downloads at 72/150/300 DPI on A4 portrait/landscape.
5. Respect the current viewer state (visible layers, opacities) for client-side prints.
6. White paper background for all printed output.

## 4. Non-goals (explicitly out of scope)

- Sending output to a physical printer via the browser print dialog (not selected).
- PNG as an offered format (not selected; JPG + PDF chosen).
- Remembering user settings between sessions (explicitly declined — always defaults).
- Creating/editing QGIS print layouts from the app (authoring stays in QGIS Desktop).
- Atlas / multi-page / tiled output for large extents.
- Paper sizes other than A4 portrait/landscape (e.g. Letter/A3) in v1.

## 5. Decisions (from the interview)

| # | Question | Decision |
|---|----------|----------|
| 1 | Overall approach | **Hybrid** — GetPrint when the project has layouts, client-side otherwise |
| 2 | Output formats | **PDF + JPG** |
| 3 | Printed area | **Preview map inside the dialog**, pan/zoom to set the area (MapStore pattern) |
| 4 | Layout presentation | **Dropdown** of the project's layouts + a **"Plain map (client-side)"** entry |
| 5 | Client-side furniture | **Title, Legend, North arrow, Scale bar, Date + author** (all of them) |
| 6 | Paper size | **A4 portrait / A4 landscape** |
| 7 | Resolution | **DPI presets: 72 / 150 / 300** |
| 8 | Preview ↔ main map | Preview **opens on the main map's current view, then is independent** |
| 9 | Layer state | Client-side print **respects layers-panel visibility + opacity sliders** |
| 10 | Background | **White**, always, on paper |
| 11 | Persistence | **None** — dialog always opens with defaults |
| 12 | Filename | **`{sanitized-project-name}_{YYYY-MM-DD}.{ext}`** (e.g. `Cemetery-Map_2026-08-09.pdf`) |
| 13 | Layout render failure | **Auto-fallback to client-side with a notice** |
| 14 | Preview basemap | **Same base map as the main viewer**, with a small switcher incl. "No basemap" |
| 15 | Layouts with fixed content | **"Use preview extent" checkbox, per layout** (see §7.6) |

## 6. Functional requirements

### 6.1 Print dialog

- A modal dialog opened by every print button (all 5 layouts) via a shared
  `window.openPrintDialog()`.
- Contains:
  1. **Preview map** (the primary control) — see §6.2.
  2. **Layout dropdown** — the project's QGIS print layouts + "Plain map (client-side)".
     Default selection: first layout if any, else "Plain map (client-side)".
  3. **Format**: PDF / JPG (radio).
  4. **Paper**: A4 portrait / A4 landscape (radio).
  5. **DPI**: 72 / 150 / 300 (dropdown).
  6. **Furniture toggles** (client-side path only; hidden/disabled when a QGIS layout
     is selected since the layout defines its own): Title, Legend, North arrow,
     Scale bar, Date + author. Title is an editable text field defaulting to the
     project name; Date + author includes a timestamp and an optional author field.
  7. **"Use preview extent" checkbox** — enabled only when a layout is selected and the
     layout is considered extent-overridable (see §7.6).
  8. **Export button** → downloads the chosen file; **Cancel / close** (Esc, overlay
     click) → dismisses.
- No settings persistence; defaults every open.

### 6.2 Preview map

- A small OpenLayers map inside the dialog.
- Initializes to the **main map's current view** (center + zoom), then is fully
  independent (pan/zoom only affect the print).
- Shows the same WMS data layers as the main map **in the same render order**
  (reuse the reverse-tree logic from `layer-manager.js`), respecting the current
  layers-panel visibility/opacity state, plus the current base map.
- Has a **small basemap switcher** (same base maps as the main viewer, including the
  existing "No basemap" option).
- Its viewport defines the printed extent; when the layout dropdown is on
  "Plain map (client-side)" the preview extent is used directly; for QGIS layouts it
  is applied only when "Use preview extent" is checked.

### 6.3 QGIS layout path (GetPrint)

- Request through the existing `wms_proxy_view`:
  `GET {tenant_base}/viewer/{pk}/wms/?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetPrint&TEMPLATE={layout}&LAYOUT={layout}&FORMAT=pdf|jpg&DPI={dpi}[&map0:extent=minx,miny,maxx,maxy]`
  (send both `TEMPLATE` and `LAYOUT` for cross-version compatibility; URL-encode the
  layout name).
- The proxy's existing header pass-through yields the correct
  `Content-Disposition`; trigger a download of `{project}_{date}.{ext}`.
- On QGIS `ServiceException` (e.g. `Layer(s) not valid`, invalid template) →
  **auto-fallback**: show a notice ("QGIS layout failed to render — exported a plain
  map instead") and run the client-side path with the current dialog settings.

### 6.4 Client-side "Plain map" path

- Build a temporary OpenLayers map at the chosen paper dimensions
  (A4 at the chosen DPI: e.g. 2480×3508 px @ 300 DPI portrait, landscape swapped),
  view fitted to the preview extent.
- Layers: the same WMS sources as the preview/main map for **visible** layers,
  each with its current opacity; white background; no base map tiles on paper
  (decision #10 — white).
- Furniture drawn as canvas/HTML-to-canvas overlays: title (editable), legend
  (QGIS `GetLegendGraphic` images per layer — reuse the `legendUrl()` helper pattern
  already in `layer-manager.js`), scale bar (computed from view resolution),
  north arrow (icon), date + author line.
- Render → JPG (`canvas.toDataURL('image/jpeg')`) and/or PDF (see §7.4 for the PDF
  library decision). Download as `{project}_{date}.{ext}`.

### 6.5 Layout enumeration

- New server-side helper (e.g. in `georidge_platform/apps/qgis_server/services.py`):
  `get_print_layouts(project)` — open `project.file` (ZIP), read the `.qgs`, regex
  `<Layout name="...">`, return sorted list of names. Return `[]` on any error.
- Viewer page context (`_get_wms_context_for_request`) adds `print_layouts` (and a
  `print_layouts_json`) to the map-config blob so the dialog can populate the dropdown
  without an extra round-trip.

## 7. Edge cases & open questions

1. **Project 6 today**: has a layout but fails on QGIS Server → exercise the
   auto-fallback path (§6.3) and surface a clear notice. This is also the live test
   case for layout failure handling.
2. **Project with zero layouts** → dropdown shows only "Plain map (client-side)";
   no GetPrint attempts.
3. **Layout name with spaces/special chars** (e.g. "Ownership Certificate") → must be
   URL-encoded in the GetPrint request; verified needed (a space breaks the URL).
4. **No basemap selected in the main viewer** → preview inherits it; paper is still
   white (§6.4).
5. **Preview extent empty/broken** (e.g. no extent data at all) → default to the
   main map's full-extent view.
6. **"Use preview extent" per layout** — how to know whether a layout's map can be
   overridden? Options: (a) always enable and let QGIS apply `map0:extent` (it does
   for any layout with a map item), (b) parse the layout XML to detect whether it has
   a map item, (c) attempt and surface the server error. **Open question — likely (a)
   with sensible default checked.**
7. **PDF generation for the client-side path** — needs a client-side library
   (e.g. `jsPDF` + embedding the JPG, or `html2pdf`). This is the only new front-end
   dependency. **Open question: acceptable to add `jsPDF` (or prefer server-side PDF
   via QGIS `GetMap FORMAT=application/pdf` at the chosen extent/DPI — which avoids a
   new dependency but lacks furniture)?**
8. **Scale bar units** — derive from the project CRS / view resolution; metric
   (m/km) for projected CRS, degrees for geographic. Confirm preferred default.
9. **North arrow icon source** — add a dedicated SVG to `viewer/icons/{icon_set}/` or
   reuse an existing arrow icon if present in the theme sets.
10. **Where the dialog markup lives** — shared partial (e.g.
    `templates/viewer/panels/print-dialog.html`) included once by `viewer.html` so all
    layouts get it, plus `print-dialog.js` and CSS in the viewer static bundle. Confirm
    this matches how the other shared panels are wired.

## 8. Proposed implementation sketch (for the build phase)

- `georidge_platform/apps/qgis_server/services.py`: `get_print_layouts(project)`.
- `georidge_platform/apps/viewer/views.py`: add `print_layouts_json` to map-config ctx.
- New static: `viewer/js/print-dialog.js` (openPrintDialog, preview map, GetPrint
  call, client-side render, download); reuse `legendUrl()` pattern and the reverse
  layer-order logic; reuse `hideBaseMap()`-style base handling for the preview
  switcher.
- New template partial `templates/viewer/panels/print-dialog.html` + CSS in
  `viewer.css` (theme-aware, consistent with existing panels).
- `map-core.js`: replace `printMap()` body with `openPrintDialog()` (keep the old
  PNG export only as an internal helper if needed for the client-side path).
- Update the 5 layout print buttons if needed (they already call
  `window.printMap()`; repoint to `window.openPrintDialog()`).
- Validation: JS syntax check, rebuild image, redeploy, verify the served dialog,
  layout dropdown (project 6 vs 5), GetPrint request through the proxy, fallback
  path, JPG/PDF download headers.

## 9. Acceptance criteria

- [ ] Clicking Print in any of the 5 layouts opens the dialog with a preview map at
      the current view.
- [ ] Panning/zooming the preview changes the printed area (verified by output).
- [ ] Project 6: "Ownership Certificate" appears in the dropdown; selecting it and
      exporting hits the WMS proxy with a valid GetPrint request.
- [ ] Project 5: no layouts → only "Plain map (client-side)" is offered and it
      exports successfully as both JPG and PDF.
- [ ] Layout failure (e.g. project 6 while unloadable) auto-falls back to
      client-side with a visible notice.
- [ ] Client-side export respects hidden layers and per-layer opacity from the panel.
- [ ] Output is A4 at the chosen DPI/orientation, white background, with the enabled
      furniture (title, legend, north arrow, scale bar, date/author).
- [ ] Filenames follow `{project}_{YYYY-MM-DD}.{ext}`.
- [ ] Dialog always opens with defaults (no persistence).
