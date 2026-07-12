## Context

The viewer has three layout presets (MapGuide, MapStore, QWC2), each with a side panel containing layers and feature info tabs, plus a floating identify popup. All panels are hardcoded to 320px width. The side panels use different positioning models:

- **MapGuide**: Flex child in `.viewer-body` — pushes the map
- **MapStore**: Absolute overlay inside `#map-container` — floats over map
- **QWC2**: Absolute overlay with `translateX(-100%)` slide-in — floats over map

The identify popup is a fixed-position floating element (used by MapStore/QWC2 layouts).

## Goals / Non-Goals

**Goals:**
- Users can drag the right edge of side panels and identify popup to resize
- Invisible resize handle (cursor changes on hover)
- MapGuide: map flex-adjusts to panel width change
- MapStore/QWC2: panel grows over map (map unchanged)
- OpenLayers map recalculates viewport after resize
- Saved width persists during session (no localStorage needed)

**Non-Goals:**
- Vertical resize (height is already max-height or full-height)
- Saving preferred width across sessions
- Resizing the 48px MapStore sidebar icon strip
- Resizing the basemap selector

## Decisions

### Decision 1: Shared resize utility function

**Choice:** Create a single `createResizeHandle(element, options)` utility function in a new shared file `viewer/js/panel-resize.js`, included by all three layouts.

**Rationale:** The resize logic (pointerdown tracking, min/max clamping, cursor handling) is identical across all panels. A shared function avoids duplicating ~40 lines of JS across 4 files.

**Alternatives considered:**
- Inline resize JS in each template: Rejected — duplicates code 4 times
- CSS `resize: horizontal`: Rejected — doesn't work well with existing positioning, no cursor customization

### Decision 2: Resize handle is a div element, not CSS pseudo-element

**Choice:** Add a `<div class="panel-resize-handle">` to each panel's HTML, styled as an invisible bar on the right edge.

**Rationale:** A real DOM element is easier to attach pointer events to than a pseudo-element. Pseudo-elements (`::after`) require workaround tricks for event handling.

### Decision 3: Disable CSS transition during drag

**Choice:** Temporarily set `transition: none` on the panel during drag, restore after.

**Rationale:** The existing `transition: width 0.2s ease` on `.dock-panel` causes laggy resize feedback. Disabling it during drag makes the panel follow the cursor precisely.

### Decision 4: Map updateSize() on resize end

**Choice:** Call `map.updateSize()` once on pointerup (not on every pointermove).

**Rationale:** `updateSize()` triggers OpenLayers viewport recalculation. Calling it on every move event is expensive. Calling it once at the end is sufficient and performant.

## Risks / Trade-offs

- **MapGuide map flicker on resize end** → Mitigated by only calling `updateSize()` on pointerup, not during drag
- **Popup goes off-screen if dragged too wide** → Mitigated by clamping max width to 50% of viewport
- **Panel resize handle conflicts with existing drag-to-move on popup header** → Mitigated by separating hit zones: right 6px edge = resize, rest = move

## Migration Plan

No migration needed. Pure client-side JS/CSS change. Deploy and hard-refresh.
