(function() {
  'use strict';

  var map = window.viewerMap;
  if (!map) return;

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

  var tooltipEl = document.createElement('div');
  tooltipEl.className = 'measure-tooltip';
  var tooltipOverlay = new ol.Overlay({
    element: tooltipEl,
    offset: [10, -10],
    positioning: 'bottom-left',
    stopEvent: false,
  });
  map.addOverlay(tooltipOverlay);

  var imperial = false;

  function formatLength(meters) {
    if (imperial) {
      var ft = meters * 3.28084;
      if (ft < 528) return ft.toFixed(1) + ' ft';
      return (ft / 5280).toFixed(2) + ' mi';
    }
    if (meters < 1000) return meters.toFixed(1) + ' m';
    return (meters / 1000).toFixed(3) + ' km';
  }

  function formatArea(sqMeters) {
    if (imperial) {
      var sqFt = sqMeters * 10.7639;
      if (sqFt < 43560) return sqFt.toFixed(0) + ' ft²';
      return (sqFt / 43560).toFixed(2) + ' ac';
    }
    if (sqMeters < 10000) return sqMeters.toFixed(1) + ' m²';
    return (sqMeters / 10000).toFixed(3) + ' ha';
  }

  function formatSegmentLength(meters, total) {
    var seg = formatLength(meters);
    var tot = formatLength(total);
    return seg + ' | Total: ' + tot;
  }

  function clearMeasure() {
    abortDraw();
    measureSource.clear();
    tooltipOverlay.setPosition(undefined);
    tooltipEl.style.display = 'none';
    drawDistance.setActive(false);
    drawArea.setActive(false);
  }

  var activeDraw = null;
  var activeListener = null;
  var lastCoord = null;

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

  // Distance draw
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
    var geom = e.feature.getGeometry();
    activeListener = geom.on('change', function() {
      var coords = geom.getCoordinates();
      if (coords.length < 2) return;
      lastCoord = coords[coords.length - 1];
      var totalLength = ol.sphere.getLength(geom, { projection: 'EPSG:3857' });
      tooltipEl.textContent = formatLength(totalLength);
      tooltipOverlay.setPosition(lastCoord);
    });
  });
  drawDistance.on('drawend', function(e) {
    if (activeListener) {
      ol.Observable.unByKey(activeListener);
      activeListener = null;
    }
    var geom = e.feature.getGeometry();
    var totalLength = ol.sphere.getLength(geom, { projection: 'EPSG:3857' });
    var coords = geom.getCoordinates();
    lastCoord = coords[coords.length - 1];
    tooltipEl.textContent = 'Distance: ' + formatLength(totalLength);
    tooltipOverlay.setPosition(lastCoord);
    activeDraw = null;
  });
  map.addInteraction(drawDistance);
  drawDistance.setActive(false);

  // Area draw
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
    var geom = e.feature.getGeometry();
    activeListener = geom.on('change', function() {
      var area = ol.sphere.getArea(geom, { projection: 'EPSG:3857' });
      var perimeter = ol.sphere.getLength(geom, { projection: 'EPSG:3857' });
      lastCoord = ol.extent.getCenter(geom.getExtent());
      tooltipEl.innerHTML = 'Area: ' + formatArea(area) + '<br>Perimeter: ' + formatLength(perimeter);
      tooltipOverlay.setPosition(lastCoord);
    });
  });
  drawArea.on('drawend', function(e) {
    if (activeListener) {
      ol.Observable.unByKey(activeListener);
      activeListener = null;
    }
    var geom = e.feature.getGeometry();
    var area = ol.sphere.getArea(geom, { projection: 'EPSG:3857' });
    var perimeter = ol.sphere.getLength(geom, { projection: 'EPSG:3857' });
    lastCoord = ol.extent.getCenter(geom.getExtent());
    tooltipEl.innerHTML = 'Area: ' + formatArea(area) + '<br>Perimeter: ' + formatLength(perimeter);
    tooltipOverlay.setPosition(lastCoord);
    activeDraw = null;
  });
  map.addInteraction(drawArea);
  drawArea.setActive(false);

  // Register tool names
  window.measureClear = clearMeasure;
  window.measureToggleUnits = function() {
    imperial = !imperial;
    if (tooltipEl.textContent && tooltipEl.textContent !== '') {
      var features = measureSource.getFeatures();
      if (features.length > 0) {
        var geom = features[features.length - 1].getGeometry();
        if (geom) {
          var type = geom.getType();
          if (type === 'LineString') {
            var length = ol.sphere.getLength(geom, { projection: 'EPSG:3857' });
            tooltipEl.textContent = 'Distance: ' + formatLength(length);
          } else if (type === 'Polygon') {
            var area = ol.sphere.getArea(geom, { projection: 'EPSG:3857' });
            var perim = ol.sphere.getLength(geom, { projection: 'EPSG:3857' });
            tooltipEl.innerHTML = 'Area: ' + formatArea(area) + '<br>Perimeter: ' + formatLength(perim);
          }
        }
      }
    }
  };

  var origSetTool = window.setTool;
  window.setTool = function(tool) {
    origSetTool(tool);
    drawDistance.setActive(tool === 'measure-distance');
    drawArea.setActive(tool === 'measure-area');
    if (tool !== 'measure-distance' && tool !== 'measure-area') {
      clearMeasure();
    }
    var el = map.getTargetElement();
    if (tool === 'measure-distance' || tool === 'measure-area') {
      el.style.cursor = 'crosshair';
    }
  };
})();
