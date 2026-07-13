(function() {
  'use strict';

  var configEl = document.getElementById('map-config');
  if (!configEl) return;
  var config = JSON.parse(configEl.textContent);

  var extentData = config.extent;
  var baseMaps = config.baseMaps;

  window.iconBase = config.iconBase || '/static/viewer/icons/default/';
  window.iconExt = config.iconExt || 'svg';
  window.iconFallbackBase = '/static/viewer/icons/default/';

  window.resolveIcon = function(name) {
    return window.iconBase + name + '.' + window.iconExt;
  };

  window.applyIconFallbacks = function(root) {
    root = root || document;
    root.querySelectorAll('img[src*="/viewer/icons/"]').forEach(function(img) {
      img.onerror = function() {
        var src = img.src;
        var base = window.iconBase;
        var fallback = window.iconFallbackBase;
        if (base && src.indexOf(base) !== -1) {
          img.src = src.replace(base, fallback).replace(/\.\w+$/, '.svg');
        }
        img.onerror = null;
      };
    });
  };

  var map = new ol.Map({
    target: 'map-canvas',
    layers: [],
    view: new ol.View({ center: [0, 0], zoom: 2 }),
    controls: ol.control.defaults.defaults({ attribution: false }),
    interactions: ol.interaction.defaults.defaults({ dragPan: false }),
  });

  if (extentData) {
    map.getView().fit(extentData, { duration: 0, maxZoom: 16 });
  }

  window.__currentTool = 'pan';
  var pointerDragHandler = new ol.interaction.DragPan({
    condition: function() { return window.__currentTool === 'pan'; },
  });
  map.addInteraction(pointerDragHandler);

  var dragZoom = new ol.interaction.DragBox({
    condition: function() { return window.__currentTool === 'zoomrect'; },
  });
  dragZoom.on('boxend', function() {
    var extent = dragZoom.getGeometry().getExtent();
    map.getView().fit(extent, { duration: 300, maxZoom: 16 });
  });
  map.addInteraction(dragZoom);

  // Base map layer
  var baseLayer;
  function initBaseLayer(index) {
    if (baseLayer) {
      map.removeLayer(baseLayer);
    }
    var bm = baseMaps && baseMaps.length > 0 ? baseMaps[index || 0] : null;
    if (bm) {
      baseLayer = new ol.layer.Tile({
        source: new ol.source.XYZ({ url: bm.url, crossOrigin: 'anonymous' }),
      });
    } else {
      baseLayer = new ol.layer.Tile({
        source: new ol.source.OSM({ crossOrigin: 'anonymous' }),
      });
    }
    baseLayer.set('__base', true);
    map.getLayers().insertAt(0, baseLayer);
  }

  initBaseLayer(0);

  window.viewerMap = map;

  window.switchBaseMap = function(index) {
    initBaseLayer(index);
  };

  window.setTool = function(tool) {
    window.__currentTool = tool;
    if (tool === 'pan') {
      map.getTargetElement().style.cursor = 'grab';
    } else if (tool === 'identify') {
      map.getTargetElement().style.cursor = 'crosshair';
    } else if (tool === 'zoomrect') {
      map.getTargetElement().style.cursor = 'crosshair';
    }
  };

  map.getView().on('change:resolution', function() {
    var res = map.getView().getResolution();
    var scale = Math.round(res * 1000 * 39.37);
    var el = document.getElementById('scale-display');
    if (el) el.textContent = 'Scale: 1:' + scale.toLocaleString();
  });

  map.on('pointermove', function(e) {
    var coords = ol.coordinate.toStringHDMS(ol.proj.toLonLat(e.coordinate));
    var el = document.getElementById('coords-display');
    if (el) el.textContent = 'Coordinates: ' + coords;
  });

  window.zoomIn = function() {
    map.getView().animate({ zoom: map.getView().getZoom() + 1 });
  };
  window.zoomOut = function() {
    map.getView().animate({ zoom: map.getView().getZoom() - 1 });
  };
  window.homeExtent = function() {
    if (extentData) {
      map.getView().fit(extentData, { duration: 500, maxZoom: 16 });
    } else {
      map.getView().animate({ center: [0, 0], zoom: 2 });
    }
  };
  window.printMap = function() {
    map.once('rendercomplete', function() {
      var canvas = map.getViewport().querySelector('canvas');
      var link = document.createElement('a');
      link.download = 'map.png';
      link.href = canvas.toDataURL('image/png');
      link.click();
    });
    map.renderSync();
  };

  if (window.initLayerManager) {
    window.initLayerManager(config, map);
  }

  // If no WMS layers were added (no initLayerManager, or empty layer tree), fall back
  if (map.getLayers().getLength() <= 1 && config.wmsUrl && config.layerName) {
    map.addLayer(new ol.layer.Tile({
      source: new ol.source.TileWMS({
        url: config.wmsUrl,
        params: { LAYERS: config.layerName, TILED: true },
        serverType: 'qgis',
      }),
    }));
  }

  if (window.initIdentifyManager) {
    window.initIdentifyManager(config, map);
  }

  window.applyIconFallbacks();
})();
