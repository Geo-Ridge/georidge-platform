(function() {
  'use strict';

  var highlightLayer = null;
  var highlightSource = null;
  var projectPk = null;
  var lastPixel = null;
  var lastCoordinate = null;

  function createHighlightLayer() {
    highlightSource = new ol.source.Vector();
    highlightLayer = new ol.layer.Vector({
      source: highlightSource,
      style: function(feature) {
        var geom = feature.getGeometry();
        if (!geom) return;
        var geomType = geom.getType();
        if (geomType.indexOf('Point') !== -1) {
          return new ol.style.Style({
            image: new ol.style.Circle({
              radius: 8,
              fill: new ol.style.Fill({ color: 'rgba(13, 110, 253, 0.3)' }),
              stroke: new ol.style.Stroke({ color: '#0d6efd', width: 3 }),
            }),
          });
        }
        if (geomType.indexOf('LineString') !== -1) {
          return new ol.style.Style({
            stroke: new ol.style.Stroke({ color: '#0d6efd', width: 3 }),
          });
        }
        return new ol.style.Style({
          fill: new ol.style.Fill({ color: 'rgba(13, 110, 253, 0.15)' }),
          stroke: new ol.style.Stroke({ color: '#0d6efd', width: 3 }),
        });
      },
    });
    highlightLayer.set('name', 'identify-highlight');
    highlightLayer.setZIndex(9999);
    return highlightLayer;
  }

  function clearHighlight() {
    if (highlightSource) highlightSource.clear();
  }
  window.clearHighlight = clearHighlight;

  function handleIdentifyClick(e, map, config) {
    if (!highlightLayer || !highlightSource) return;
    clearHighlight();
    lastPixel = e.pixel;
    lastCoordinate = e.coordinate;

    var queryLayers = [];
    if (window.getQueryableLayers) {
      queryLayers = window.getQueryableLayers();
    } else if (config.layerName) {
      queryLayers = [config.layerName];
    }
    if (queryLayers.length === 0) return;

    var pixel = e.pixel;
    var view = map.getView();
    var size = map.getSize();
    var extent = view.calculateExtent(size);
    var xhr = new XMLHttpRequest();
    var tenantBase = config.tenantBase || '';
    xhr.open('GET', tenantBase + '/viewer/' + config.projectPk + '/identify/'
      + '?i=' + Math.round(pixel[0])
      + '&j=' + Math.round(pixel[1])
      + '&bbox=' + extent.join(',')
      + '&width=' + size[0]
      + '&height=' + size[1]
      + '&layer=' + encodeURIComponent(config.layerName || '')
      + '&query_layers=' + encodeURIComponent(queryLayers.join(',')), true);
    xhr.onload = function() {
      if (window.identifyCallback) {
        window.identifyCallback(xhr.responseText);
        return;
      }
      var html = xhr.responseText;
      var infoEl = document.getElementById('info-content');
      var featuresMatch = html.match(/<script type="application\/json" data-features>([\s\S]*?)<\/script>/);
      var hasFeatures = false;
      if (featuresMatch) {
        try {
          var geojson = JSON.parse(featuresMatch[1]);
          if (geojson.features && geojson.features.length > 0) {
            hasFeatures = true;
            highlightSource.addFeatures(
              new ol.format.GeoJSON().readFeatures(geojson, {
                dataProjection: 'EPSG:3857',
                featureProjection: 'EPSG:3857',
              })
            );
          }
        } catch (ex) {
          // ignore parse errors
        }
        html = html.replace(/<script type="application\/json" data-features>[\s\S]*?<\/script>/, '');
      }

      var featureTabs = null;
      var ftMatch = html.match(/<script type="application\/json" data-feature-tabs>([\s\S]*?)<\/script>/);
      if (ftMatch) {
        try { featureTabs = JSON.parse(ftMatch[1]); } catch(e) {}
        html = html.replace(/<script type="application\/json" data-feature-tabs>[\s\S]*?<\/script>/, '');
      }

      var qgisHtml = null;
      var qgisMatch = html.match(/<script type="application\/json" data-qgis-html>([\s\S]*?)<\/script>/);
      if (qgisMatch) {
        try { qgisHtml = JSON.parse(qgisMatch[1]); } catch(e) {}
        html = html.replace(/<script type="application\/json" data-qgis-html>[\s\S]*?<\/script>/, '');
      }

      if (infoEl) {
        if (featureTabs && featureTabs.length > 0) {
          infoEl.innerHTML = renderFeatureTabsHtml(featureTabs);
        } else if (qgisHtml) {
          infoEl.innerHTML = qgisHtml;
        } else {
          infoEl.innerHTML = html;
        }
        renderMedia(infoEl);
        var infoContent = document.getElementById('dock-info');
        if (infoContent && !infoContent.classList.contains('active')) {
          var infoTab = document.querySelector('.dock-tab[data-tab="info"]');
          if (infoTab) infoTab.click();
        }
      }

      document.dispatchEvent(new CustomEvent('identify-complete', {
        detail: {
          html: html,
          hasFeatures: hasFeatures,
          pixel: lastPixel,
          coordinate: lastCoordinate,
          featureTabs: featureTabs,
          qgisHtml: qgisHtml,
        },
        bubbles: true,
      }));
    };
    xhr.send();
  }

  window.initIdentifyManager = function(config, map) {
    projectPk = config.projectPk;
    var hl = createHighlightLayer();
    map.addLayer(hl);
    // Move highlight to top (last index)
    map.getLayers().remove(hl);
    map.getLayers().push(hl);

    var identifyDisabledTools = { zoomrect: true, 'measure-distance': true, 'measure-area': true };
    map.on('click', function(e) {
      if (window.__currentTool && identifyDisabledTools[window.__currentTool]) return;
      handleIdentifyClick(e, map, config);
    });

    document.addEventListener('identify-clear', function() {
      clearHighlight();
    });

    var infoEl = document.getElementById('info-content');
    if (infoEl) {
      infoEl.addEventListener('click', function(e) {
        var btn = e.target.closest('.identify-popup-tab');
        if (!btn) return;
        var idx = btn.getAttribute('data-tab-idx');
        infoEl.querySelectorAll('.identify-popup-tab').forEach(function(b) { b.classList.remove('active'); });
        btn.classList.add('active');
        infoEl.querySelectorAll('.feature-tab-panel').forEach(function(p) { p.style.display = 'none'; });
        var panel = infoEl.querySelector('.feature-tab-panel[data-tab-idx="' + idx + '"]');
        if (panel) panel.style.display = '';
      });
    }
  };

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function renderMedia(container) {
    var imgs = container.querySelectorAll('img[src]');
    imgs.forEach(function(img) {
      img.addEventListener('click', function() {
        var overlay = document.createElement('div');
        overlay.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.8);z-index:10000;display:flex;align-items:center;justify-content:center;cursor:pointer;';
        var fullImg = document.createElement('img');
        fullImg.src = img.src;
        fullImg.style.cssText = 'max-width:90vw;max-height:90vh;border-radius:8px;';
        overlay.appendChild(fullImg);
        overlay.addEventListener('click', function() {
          overlay.remove();
        });
        document.body.appendChild(overlay);
      });
    });
  }

  function renderFeatureTabsHtml(featureTabs) {
    if (!featureTabs || featureTabs.length === 0) {
      return '<p class="text-muted small">No features found at this location</p>';
    }
    var out = '';
    if (featureTabs.length > 1) {
      out += '<div class="identify-popup-tabs" style="display:flex;position:static;border-bottom:1px solid var(--border);">';
      featureTabs.forEach(function(tab, idx) {
        out += '<button class="identify-popup-tab' + (idx === 0 ? ' active' : '') + '" data-tab-idx="' + idx + '">' + escapeHtml(tab.name) + '</button>';
      });
      out += '</div>';
    }
    featureTabs.forEach(function(tab, idx) {
      out += '<div class="feature-tab-panel" data-tab-idx="' + idx + '" style="' + (idx > 0 ? 'display:none;' : '') + '">';
      if (tab.fields && tab.fields.length > 0) {
        out += '<table class="table table-sm table-bordered small mb-0"><thead><tr><th>Property</th><th>Value</th></tr></thead><tbody>';
        tab.fields.forEach(function(f) {
          out += '<tr><td>' + escapeHtml(f.name) + '</td><td>' + escapeHtml(String(f.value)) + '</td></tr>';
        });
        out += '</tbody></table>';
      }
      if (tab.media && tab.media.length > 0) {
        tab.media.forEach(function(m) {
          if (m.url && /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(m.url)) {
            out += '<div style="margin-top:8px;"><img src="' + escapeHtml(m.url) + '" style="max-width:100%;border-radius:4px;cursor:pointer;" alt="' + escapeHtml(m.field) + '"></div>';
          } else if (m.url) {
            out += '<a href="' + escapeHtml(m.url) + '" target="_blank" style="display:inline-flex;align-items:center;gap:4px;padding:4px 8px;background:var(--surface);border-radius:4px;text-decoration:none;color:var(--text);font-size:0.82rem;margin-top:4px;">' + escapeHtml(m.field) + '</a>';
          }
        });
      }
      out += '</div>';
    });
    return out;
  }
})();
