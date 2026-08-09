(function() {
  'use strict';

  var map = window.viewerMap;
  if (!map) return;

  // ---- Measure vector layer ----
  var measureSource = new ol.source.Vector();
  var measureLayer = new ol.layer.Vector({
    source: measureSource,
    style: new ol.style.Style({
      fill: new ol.style.Fill({ color: 'rgba(255, 152, 0, 0.15)' }),
      stroke: new ol.style.Stroke({ color: '#ff9800', width: 2, lineDash: [6, 3] }),
      image: new ol.style.Circle({
        radius: 4,
        fill: new ol.style.Fill({ color: '#ff9800' }),
      }),
    }),
  });
  measureLayer.set('name', 'measure');
  map.addLayer(measureLayer);
  map.getLayers().remove(measureLayer);
  map.getLayers().push(measureLayer);

  // ---- On-map tooltip ----
  var tooltipEl = document.createElement('div');
  tooltipEl.className = 'measure-tooltip';
  var tooltipOverlay = new ol.Overlay({
    element: tooltipEl,
    offset: [10, -10],
    positioning: 'bottom-left',
    stopEvent: false,
  });
  map.addOverlay(tooltipOverlay);

  // ---- Units ----
  var UNITS = [
    { id: 'm', label: 'Meters', distLabel: 'm', distFactor: 1, areaFactor: 1, areaLabel: 'm²' },
    { id: 'km', label: 'Kilometers', distLabel: 'km', distFactor: 0.001, areaFactor: 0.000001, areaLabel: 'km²' },
    { id: 'ft', label: 'Feet', distLabel: 'ft', distFactor: 3.28084, areaFactor: 10.7639, areaLabel: 'ft²' },
    { id: 'mi', label: 'Miles', distLabel: 'mi', distFactor: 0.000621371, areaFactor: 0.000000386102, areaLabel: 'mi²' },
    { id: 'yd', label: 'Yards', distLabel: 'yd', distFactor: 1.09361, areaFactor: 1.19599, areaLabel: 'yd²' },
    { id: 'nmi', label: 'Nautical miles', distLabel: 'nmi', distFactor: 0.000539957, areaFactor: 0.000000291553, areaLabel: 'nmi²' },
  ];
  var unit = UNITS[0];

  function getUnitById(id) {
    for (var i = 0; i < UNITS.length; i++) {
      if (UNITS[i].id === id) return UNITS[i];
    }
    return UNITS[0];
  }

  function fmt(v) {
    if (!isFinite(v)) return '—';
    if (v >= 100) return v.toFixed(0);
    if (v >= 10) return v.toFixed(1);
    if (v >= 1) return v.toFixed(2);
    return v.toFixed(3);
  }
  function fmtDist(meters) { return fmt(meters * unit.distFactor); }
  function fmtArea(sqMeters) { return fmt(sqMeters * unit.areaFactor); }

  // ---- Bearing ----
  var CARDINALS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
  function bearingBetween(c1, c2) {
    var p1 = ol.proj.toLonLat(c1);
    var p2 = ol.proj.toLonLat(c2);
    var dLon = (p2[0] - p1[0]) * Math.PI / 180;
    var lat1 = p1[1] * Math.PI / 180;
    var lat2 = p2[1] * Math.PI / 180;
    var y = Math.sin(dLon) * Math.cos(lat2);
    var x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
    return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
  }
  function bearingLabel(deg) {
    return deg.toFixed(1) + '° ' + CARDINALS[Math.round(deg / 45) % 8];
  }

  // ---- Measure widget (shared across all layouts, MapStore-style) ----
  var widget = null;
  var widgetDist = null;
  var widgetArea = null;
  var widgetBearing = null;
  var widgetSegList = null;
  var widgetUnits = null;
  var currentMode = null;   // 'distance' | 'area'
  var currentGeom = null;   // sketch / last-drawn geometry
  var lastCoord = null;
  var currentMeasureMode = 'measure-distance';  // last mode used by the single Measure button

  function buildWidget() {
    var el = document.createElement('div');
    el.className = 'measure-widget';
    el.style.display = 'none';
    el.innerHTML =
      '<div class="measure-widget-header">' +
        '<span class="measure-widget-title">Measure</span>' +
        '<button type="button" class="measure-widget-close" title="Close">&times;</button>' +
      '</div>' +
      '<div class="measure-widget-body">' +
        '<div class="measure-widget-modes">' +
          '<button type="button" class="measure-widget-mode" data-mode="distance">Distance</button>' +
          '<button type="button" class="measure-widget-mode" data-mode="area">Area</button>' +
        '</div>' +
        '<div class="measure-widget-row">' +
          '<span class="measure-widget-label">Distance</span>' +
          '<span class="measure-widget-value measure-widget-dist">—</span>' +
        '</div>' +
        '<div class="measure-widget-row">' +
          '<span class="measure-widget-label">Area</span>' +
          '<span class="measure-widget-value measure-widget-area">—</span>' +
        '</div>' +
        '<div class="measure-widget-row">' +
          '<span class="measure-widget-label">Bearing</span>' +
          '<span class="measure-widget-value measure-widget-bearing">—</span>' +
        '</div>' +
        '<div class="measure-widget-segments">' +
          '<div class="measure-widget-label">Segments</div>' +
          '<ul class="measure-widget-seglist"></ul>' +
        '</div>' +
        '<div class="measure-widget-controls">' +
          '<select class="measure-widget-units" title="Units"></select>' +
          '<button type="button" class="measure-widget-clear">Clear</button>' +
        '</div>' +
      '</div>';
    var sel = el.querySelector('.measure-widget-units');
    UNITS.forEach(function(u) {
      var opt = document.createElement('option');
      opt.value = u.id;
      opt.textContent = u.label;
      sel.appendChild(opt);
    });
    sel.value = unit.id;
    sel.addEventListener('change', function() { setUnit(getUnitById(sel.value)); });
    el.querySelectorAll('.measure-widget-mode').forEach(function(b) {
      b.addEventListener('click', function() {
        setMeasureMode(this.getAttribute('data-mode'));
      });
    });
    // Closing the panel fully exits measure mode (deactivates the draw tool,
    // restores the cursor, de-highlights the button) so we never leave an
    // invisible active tool behind.
    el.querySelector('.measure-widget-close').addEventListener('click', function() {
      window.measureClear();
    });

    el.querySelector('.measure-widget-clear').addEventListener('click', function() {
      window.measureClear();
    });
    map.getTargetElement().appendChild(el);
    widgetDist = el.querySelector('.measure-widget-dist');
    widgetArea = el.querySelector('.measure-widget-area');
    widgetBearing = el.querySelector('.measure-widget-bearing');
    widgetSegList = el.querySelector('.measure-widget-seglist');
    widgetUnits = sel;
    return el;
  }

  function showWidget(mode) {
    if (!widget) widget = buildWidget();
    widget.style.display = '';
    currentMode = mode;
    currentGeom = null;
    updateWidget();
    updateWidgetModeUI();
  }

  function updateWidgetModeUI() {
    if (!widget) return;
    var activeMode = window.__currentTool === 'measure-area' ? 'area' : 'distance';
    widget.querySelectorAll('.measure-widget-mode').forEach(function(b) {
      b.classList.toggle('measure-widget-mode-active', b.getAttribute('data-mode') === activeMode);
    });
  }

  // Switch the active measure type (used by the widget's Distance/Area toggle).
  function setMeasureMode(mode) {
    currentMeasureMode = mode === 'area' ? 'measure-area' : 'measure-distance';
    if (window.__currentTool === 'measure-distance' || window.__currentTool === 'measure-area') {
      window.setTool(currentMeasureMode);
    }
    updateWidgetModeUI();
  }

  function hideWidget() {
    if (widget) widget.style.display = 'none';
    currentMode = null;
    currentGeom = null;
  }

  function updateWidget() {
    if (!widget) return;
    if (currentMode === 'distance' && currentGeom) {
      var coords = currentGeom.getCoordinates();
      var total = ol.sphere.getLength(currentGeom, { projection: 'EPSG:3857' });
      widgetDist.textContent = fmtDist(total) + ' ' + unit.distLabel;
      widgetArea.textContent = '—';
      if (coords.length >= 2) {
        widgetBearing.textContent = bearingLabel(bearingBetween(coords[coords.length - 2], coords[coords.length - 1]));
      } else {
        widgetBearing.textContent = '—';
      }
      widgetSegList.innerHTML = '';
      for (var i = 0; i < coords.length - 1; i++) {
        var li = document.createElement('li');
        var segLen = ol.sphere.getLength(
          new ol.geom.LineString([coords[i], coords[i + 1]]),
          { projection: 'EPSG:3857' }
        );
        li.textContent = 'Segment ' + (i + 1) + ': ' + fmtDist(segLen) + ' ' + unit.distLabel;
        widgetSegList.appendChild(li);
      }
      var totalLi = document.createElement('li');
      totalLi.className = 'measure-widget-total';
      totalLi.textContent = 'Total: ' + fmtDist(total) + ' ' + unit.distLabel;
      widgetSegList.appendChild(totalLi);
    } else if (currentMode === 'area' && currentGeom) {
      var area = ol.sphere.getArea(currentGeom, { projection: 'EPSG:3857' });
      var perimeter = ol.sphere.getLength(currentGeom, { projection: 'EPSG:3857' });
      widgetDist.textContent = '—';
      widgetArea.textContent = fmtArea(area) + ' ' + unit.areaLabel;
      widgetBearing.textContent = '—';
      widgetSegList.innerHTML = '';
      var liPerim = document.createElement('li');
      liPerim.textContent = 'Perimeter: ' + fmtDist(perimeter) + ' ' + unit.distLabel;
      widgetSegList.appendChild(liPerim);
    } else {
      widgetDist.textContent = '—';
      widgetArea.textContent = '—';
      widgetBearing.textContent = '—';
      widgetSegList.innerHTML = '';
    }
  }

  function setUnit(u) {
    unit = u;
    if (widgetUnits) widgetUnits.value = u.id;
    updateWidget();
    refreshTooltip();
  }

  function refreshTooltip() {
    if (!currentGeom || !lastCoord) return;
    if (currentMode === 'distance') {
      var total = ol.sphere.getLength(currentGeom, { projection: 'EPSG:3857' });
      tooltipEl.textContent = 'Distance: ' + fmtDist(total) + ' ' + unit.distLabel;
    } else if (currentMode === 'area') {
      var area = ol.sphere.getArea(currentGeom, { projection: 'EPSG:3857' });
      var perim = ol.sphere.getLength(currentGeom, { projection: 'EPSG:3857' });
      tooltipEl.textContent = 'Area: ' + fmtArea(area) + ' ' + unit.areaLabel + ' | Perimeter: ' + fmtDist(perim) + ' ' + unit.distLabel;
    }
  }

  function clearMeasure() {
    abortDraw();
    measureSource.clear();
    tooltipOverlay.setPosition(undefined);
    tooltipEl.style.display = 'none';
    drawDistance.setActive(false);
    drawArea.setActive(false);
    currentMode = null;
    currentGeom = null;
  }

  var activeDraw = null;
  var activeListener = null;

  function abortDraw() {
    if (activeDraw) {
      activeDraw.finishDrawing();
      activeDraw = null;
    }
    if (activeListener) {
      ol.Observable.unByKey(activeListener);
      activeListener = null;
    }
    lastCoord = null;
  }

  // ---- Distance draw ----
  var drawDistance = new ol.interaction.Draw({
    type: 'LineString',
    source: measureSource,
    style: new ol.style.Style({
      stroke: new ol.style.Stroke({ color: '#ff9800', width: 2, lineDash: [6, 3] }),
      image: new ol.style.Circle({
        radius: 4,
        fill: new ol.style.Fill({ color: '#ff9800' }),
      }),
    }),
  });
  drawDistance.on('drawstart', function(e) {
    abortDraw();
    activeDraw = drawDistance;
    tooltipEl.style.display = '';
    currentMode = 'distance';
    currentGeom = e.feature.getGeometry();
    updateWidget();
    var geom = currentGeom;
    activeListener = geom.on('change', function() {
      var coords = geom.getCoordinates();
      if (coords.length < 2) return;
      lastCoord = coords[coords.length - 1];
      var totalLength = ol.sphere.getLength(geom, { projection: 'EPSG:3857' });
      var segLen = ol.sphere.getLength(
        new ol.geom.LineString([coords[coords.length - 2], coords[coords.length - 1]]),
        { projection: 'EPSG:3857' }
      );
      tooltipEl.textContent = 'Seg: ' + fmtDist(segLen) + ' ' + unit.distLabel + ' | Total: ' + fmtDist(totalLength) + ' ' + unit.distLabel;
      tooltipOverlay.setPosition(lastCoord);
      updateWidget();
    });
  });
  drawDistance.on('drawend', function(e) {
    if (activeListener) {
      ol.Observable.unByKey(activeListener);
      activeListener = null;
    }
    var geom = e.feature.getGeometry();
    currentGeom = geom;
    var coords = geom.getCoordinates();
    lastCoord = coords[coords.length - 1];
    var totalLength = ol.sphere.getLength(geom, { projection: 'EPSG:3857' });
    tooltipEl.textContent = 'Distance: ' + fmtDist(totalLength) + ' ' + unit.distLabel;
    tooltipOverlay.setPosition(lastCoord);
    updateWidget();
    activeDraw = null;
  });
  map.addInteraction(drawDistance);
  drawDistance.setActive(false);

  // ---- Area draw ----
  var drawArea = new ol.interaction.Draw({
    type: 'Polygon',
    source: measureSource,
    style: new ol.style.Style({
      fill: new ol.style.Fill({ color: 'rgba(255, 152, 0, 0.15)' }),
      stroke: new ol.style.Stroke({ color: '#ff9800', width: 2, lineDash: [6, 3] }),
      image: new ol.style.Circle({
        radius: 4,
        fill: new ol.style.Fill({ color: '#ff9800' }),
      }),
    }),
  });
  drawArea.on('drawstart', function(e) {
    abortDraw();
    activeDraw = drawArea;
    tooltipEl.style.display = '';
    currentMode = 'area';
    currentGeom = e.feature.getGeometry();
    updateWidget();
    var geom = currentGeom;
    activeListener = geom.on('change', function() {
      var area = ol.sphere.getArea(geom, { projection: 'EPSG:3857' });
      var perimeter = ol.sphere.getLength(geom, { projection: 'EPSG:3857' });
      lastCoord = ol.extent.getCenter(geom.getExtent());
      tooltipEl.innerHTML = 'Area: ' + fmtArea(area) + ' ' + unit.areaLabel + '<br>Perimeter: ' + fmtDist(perimeter) + ' ' + unit.distLabel;
      tooltipOverlay.setPosition(lastCoord);
      updateWidget();
    });
  });
  drawArea.on('drawend', function(e) {
    if (activeListener) {
      ol.Observable.unByKey(activeListener);
      activeListener = null;
    }
    var geom = e.feature.getGeometry();
    currentGeom = geom;
    var area = ol.sphere.getArea(geom, { projection: 'EPSG:3857' });
    var perimeter = ol.sphere.getLength(geom, { projection: 'EPSG:3857' });
    lastCoord = ol.extent.getCenter(geom.getExtent());
    tooltipEl.innerHTML = 'Area: ' + fmtArea(area) + ' ' + unit.areaLabel + '<br>Perimeter: ' + fmtDist(perimeter) + ' ' + unit.distLabel;
    tooltipOverlay.setPosition(lastCoord);
    updateWidget();
    activeDraw = null;
  });
  map.addInteraction(drawArea);
  drawArea.setActive(false);

  // ---- Public API ----
  // The Clear button (any layout or the widget) is a direct action, not routed
  // through setTool: fully exit measure mode — restore pan navigation, drop the
  // crosshair cursor back to the default pointer, and de-highlight any measure
  // tool button still marked active.
  window.measureClear = function() {
    clearMeasure();
    hideWidget();
    if (window.__currentTool === 'measure-distance' || window.__currentTool === 'measure-area') {
      window.__currentTool = 'pan';
      map.getTargetElement().style.cursor = '';
    }
    updateMeasureButtonActive();
  };

  // Single Measure button across all layouts: toggle measure mode on/off.
  window.toggleMeasure = function() {
    if (window.__currentTool === 'measure-distance' || window.__currentTool === 'measure-area') {
      window.measureClear();
    } else {
      window.setTool(currentMeasureMode);
    }
  };

  // Highlight the shared measure button ([data-tool="measure"]) when a measure
  // tool is active. Uses its own class so it works across every layout without
  // depending on each theme's active-class name.
  function updateMeasureButtonActive() {
    var isMeasure = window.__currentTool === 'measure-distance' || window.__currentTool === 'measure-area';
    document.querySelectorAll('[data-tool="measure"]').forEach(function(b) {
      b.classList.toggle('measure-active', isMeasure);
    });
  }

  // Cycle through the unit list (backwards compatible with the legacy
  // "Toggle Units" toolbar buttons).
  window.measureToggleUnits = function() {
    var idx = UNITS.indexOf(unit);
    setUnit(UNITS[(idx + 1) % UNITS.length]);
  };

  var origSetTool = window.setTool;
  window.setTool = function(tool) {
    origSetTool(tool);
    drawDistance.setActive(tool === 'measure-distance');
    drawArea.setActive(tool === 'measure-area');
    if (tool === 'measure-distance' || tool === 'measure-area') {
      showWidget(tool === 'measure-distance' ? 'distance' : 'area');
    } else {
      clearMeasure();
      hideWidget();
    }
    var el = map.getTargetElement();
    if (tool === 'measure-distance' || tool === 'measure-area') {
      el.style.cursor = 'crosshair';
    }
    updateMeasureButtonActive();
  };
})();
