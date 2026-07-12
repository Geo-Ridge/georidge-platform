## 1. Shared resize utility

- [x] 1.1 Create `viewer/js/panel-resize.js` with `createResizeHandle(panel, options)` function
- [x] 1.2 Create shared CSS for `.panel-resize-handle` in `viewer.css` (invisible bar, cursor, hover state)

## 2. MapGuide layout

- [x] 2.1 Add resize handle div to `layouts/mapguide.html` dock panel
- [x] 2.2 Include `panel-resize.js` and wire up resize on MapGuide panel
- [x] 2.3 Call `map.updateSize()` on resize end, disable transition during drag

## 3. MapStore layout

- [x] 3.1 Add resize handle div to `layouts/mapstore.html` layers panel
- [x] 3.2 Include `panel-resize.js` and wire up resize on MapStore panel
- [x] 3.3 Disable transition during drag

## 4. QWC2 layout

- [x] 4.1 Add resize handle div to `layouts/qwc2.html` slide panel
- [x] 4.2 Include `panel-resize.js` and wire up resize on QWC2 panel
- [x] 4.3 Disable transition during drag

## 5. Identify popup

- [x] 5.1 Add resize handle to identify popup in `identify-popup.js`
- [x] 5.2 Separate resize (right edge) from move (header) hit zones
- [x] 5.3 Fix hardcoded 330px in popup position calculation
