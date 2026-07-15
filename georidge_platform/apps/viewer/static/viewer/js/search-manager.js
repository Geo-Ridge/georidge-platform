(function() {
  'use strict';

  var configEl = document.getElementById('map-config');
  if (!configEl) return;
  var config = JSON.parse(configEl.textContent);

  var searchSource = new ol.source.Vector();
  var searchLayer = new ol.layer.Vector({
    source: searchSource,
    style: function(feature) {
      var geom = feature.getGeometry();
      if (!geom) return;
      var geomType = geom.getType();
      if (geomType.indexOf('Point') !== -1) {
        return new ol.style.Style({
          image: new ol.style.Circle({
            radius: 10,
            fill: new ol.style.Fill({ color: 'rgba(255, 193, 7, 0.4)' }),
            stroke: new ol.style.Stroke({ color: '#ff9800', width: 3 }),
          }),
        });
      }
      if (geomType.indexOf('LineString') !== -1) {
        return new ol.style.Style({
          stroke: new ol.style.Stroke({ color: '#ff9800', width: 4 }),
        });
      }
      return new ol.style.Style({
        fill: new ol.style.Fill({ color: 'rgba(255, 193, 7, 0.2)' }),
        stroke: new ol.style.Stroke({ color: '#ff9800', width: 3 }),
      });
    },
  });
  searchLayer.set('name', 'search-highlight');

  var container = document.getElementById('toolbar-container');
  var searchWrap;
  if (container) {
    searchWrap = document.createElement('div');
    searchWrap.className = 'search-wrap';
    container.appendChild(searchWrap);
  } else {
    var mapOnlySearch = document.querySelector('.map-only-search');
    var qwc2Search = document.querySelector('.qwc2-search-wrap');
    var lizSearch = document.querySelector('.liz-search-wrap');
    var target = mapOnlySearch || qwc2Search || lizSearch;
    if (!target) return;
    searchWrap = target;
    searchWrap.classList.add('search-wrap');
  }

  var iconBase = config.iconBase || '/static/viewer/icons/default/';
  var iconExt = config.iconExt || 'svg';

  searchWrap.innerHTML =
    '<img class="search-icon" src="' + iconBase + 'search.' + iconExt + '" width="14" height="14" alt="Search">'
    + '<input type="text" class="search-input" placeholder="Search features…">'
    + '<div class="search-dropdown" style="display:none"></div>';

  var input = searchWrap.querySelector('.search-input');
  var dropdown = searchWrap.querySelector('.search-dropdown');
  var searchIcon = searchWrap.querySelector('.search-icon');
  if (searchIcon && window.applyIconFallbacks) window.applyIconFallbacks(searchWrap);
  var timer = null;
  var lastQuery = '';

  function doSearch(query) {
    if (query === lastQuery) return;
    lastQuery = query;
    if (query.length < 2) {
      dropdown.style.display = 'none';
      return;
    }
    var tenantBase = config.tenantBase || '';
    var xhr = new XMLHttpRequest();
    xhr.open('GET', tenantBase + '/viewer/' + config.projectPk + '/search/?q=' + encodeURIComponent(query), true);
    xhr.onload = function() {
      if (xhr.status !== 200) return;
      try {
        var data = JSON.parse(xhr.responseText);
        renderResults(data.results || []);
      } catch (ex) {
        // ignore
      }
    };
    xhr.send();
  }

  function clearSearchHighlight() {
    searchSource.clear();
    var map = window.viewerMap;
    if (map && searchLayer.get('__in_map')) {
      map.removeLayer(searchLayer);
      searchLayer.set('__in_map', false);
    }
  }

  function renderResults(results) {
    dropdown.innerHTML = '';
    if (results.length === 0) {
      dropdown.style.display = 'none';
      return;
    }

    var byLayer = {};
    results.forEach(function(r) {
      var key = r.layer_title || r.layer;
      if (!byLayer[key]) byLayer[key] = [];
      byLayer[key].push(r);
    });

    Object.keys(byLayer).forEach(function(layerTitle) {
      var group = document.createElement('div');
      group.className = 'search-result-group';

      var header = document.createElement('div');
      header.className = 'search-result-group-header';
      header.textContent = layerTitle;
      group.appendChild(header);

      byLayer[layerTitle].forEach(function(r) {
        var item = document.createElement('div');
        item.className = 'search-result-item';
        item.textContent = r.label;
        item.addEventListener('click', function() {
          selectResult(r);
        });
        group.appendChild(item);
      });

      dropdown.appendChild(group);
    });

    dropdown.style.display = '';
  }

  function selectResult(result) {
    dropdown.style.display = 'none';
    input.blur();

    var map = window.viewerMap;
    if (!map) return;

    clearSearchHighlight();

    if (result.geojson) {
      var features = new ol.format.GeoJSON().readFeatures(result.geojson, {
        dataProjection: 'EPSG:3857',
        featureProjection: 'EPSG:3857',
      });
      if (features.length > 0) {
        searchSource.addFeatures(features);
        if (!searchLayer.get('__in_map')) {
          map.addLayer(searchLayer);
          searchLayer.set('__in_map', true);
          // Move to top
          map.getLayers().remove(searchLayer);
          map.getLayers().push(searchLayer);
        }
        var extent = searchSource.getExtent();
        if (extent && !isNaN(extent[0])) {
          map.getView().fit(extent, { duration: 300, maxZoom: 18 });
        }
      }
    } else if (result.bbox) {
      map.getView().fit(result.bbox, { duration: 300, maxZoom: 18 });
    }

    document.dispatchEvent(new CustomEvent('search-select', {
      detail: {
        label: result.label,
        layer_title: result.layer_title,
        layer: result.layer,
        bbox: result.bbox,
        geojson: result.geojson,
      },
      bubbles: true,
    }));
  }

  // Debounced input handler
  input.addEventListener('input', function() {
    var val = input.value.trim();
    if (timer) clearTimeout(timer);
    timer = setTimeout(function() {
      doSearch(val);
    }, 300);
  });

  // Close on Escape
  input.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      dropdown.style.display = 'none';
      input.blur();
    }
  });

  // Close on blur (with delay for click inside dropdown)
  input.addEventListener('blur', function() {
    setTimeout(function() {
      dropdown.style.display = 'none';
    }, 200);
  });

  // Close on outside click
  document.addEventListener('click', function(e) {
    if (!searchWrap.contains(e.target)) {
      dropdown.style.display = 'none';
    }
  });

  // Expose clear for other modules
  window.clearSearchHighlight = clearSearchHighlight;
})();
