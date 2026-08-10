(function() {
  'use strict';

  var configEl = document.getElementById('map-config');
  if (!configEl) return;
  var config;
  try {
    config = JSON.parse(configEl.textContent);
  } catch (e) {
    return;
  }

  var projectName = config.projectName || (document.title ? document.title.split('—')[0].trim() : 'map');
  var layouts = config.printLayouts || [];
  var PLAIN = '__plain__';

  var dialog = null;
  var previewMap = null;
  var previewBaseLayer = null;
  var currentBaseIndex = 0;

  // ------------------------------------------------------------------
  // helpers
  // ------------------------------------------------------------------
  function sanitizeName(s) {
    return String(s || 'map').replace(/[^\w -]/g, '').replace(/\s+/g, '-').replace(/-+/g, '-');
  }
  function todayStr() {
    var d = new Date();
    var mm = String(d.getMonth() + 1).padStart(2, '0');
    var dd = String(d.getDate()).padStart(2, '0');
    return d.getFullYear() + '-' + mm + '-' + dd;
  }
  function makeFilename(ext) {
    return sanitizeName(projectName) + '_' + todayStr() + '.' + ext;
  }
  function downloadBlob(blob, filename) {
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(function() {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 200);
  }
  function downloadCanvas(canvas, mime, filename, quality) {
    var a = document.createElement('a');
    a.href = canvas.toDataURL(mime, quality == null ? 0.92 : quality);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(function() { document.body.removeChild(a); }, 200);
  }
  function loadImage(src) {
    return new Promise(function(resolve, reject) {
      var img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = function() { resolve(img); };
      img.onerror = function() { reject(new Error('Failed to load ' + src.slice(0, 120))); };
      img.src = src;
    });
  }

  // Visible WMS data layers of the main map, bottom -> top (QGIS/GetMap order),
  // with their current opacity — respects the layers panel state.
  function getPrintLayerState() {
    var treeNames = [];
    function walk(nodes) {
      (nodes || []).forEach(function(n) {
        if (n.type === 'layer' && n.name) treeNames.push(n.name);
        else if (n.type === 'group') walk(n.children);
      });
    }
    walk(config.layerTree);
    var names = [];
    var opacities = [];
    var map = window.viewerMap;
    if (map && treeNames.length) {
      map.getLayers().forEach(function(l) {
        var name = l.get('name');
        if (name && treeNames.indexOf(name) !== -1) {
          var op = l.getOpacity();
          if (l.getVisible() && op > 0) {
            names.push(name);
            opacities.push(Math.round(op * 100));
          }
        }
      });
    }
    return { names: names, opacities: opacities };
  }

  function previewExtent() {
    if (!previewMap) return null;
    return previewMap.getView().calculateExtent(previewMap.getSize());
  }

  // ------------------------------------------------------------------
  // preview map
  // ------------------------------------------------------------------
  function createWmsLayer(name, opacity) {
    return new ol.layer.Tile({
      source: new ol.source.TileWMS({
        url: config.wmsUrl,
        params: { LAYERS: name, TILED: true },
        serverType: 'qgis',
      }),
      opacity: opacity == null ? 1 : opacity,
    });
  }

  function addPreviewBase(index) {
    if (previewBaseLayer) {
      previewMap.removeLayer(previewBaseLayer);
      previewBaseLayer = null;
    }
    var bm = config.baseMaps && config.baseMaps.length ? config.baseMaps[index] : null;
    if (bm) {
      previewBaseLayer = new ol.layer.Tile({
        source: new ol.source.XYZ({
          // Prefer the app-side tile proxy (see map-core.js for the reason).
          url: bm.tileUrl || bm.url,
          crossOrigin: 'anonymous',
          minZoom: typeof bm.minZoom === 'number' ? bm.minZoom : 0,
          maxZoom: typeof bm.maxZoom === 'number' ? bm.maxZoom : 19,
        }),
      });
      previewMap.getLayers().insertAt(0, previewBaseLayer);
    }
  }

  function buildPreviewMap() {
    var target = dialog.querySelector('.print-preview-canvas');
    var viewOpts = { center: [0, 0], zoom: 2 };
    var mainMap = window.viewerMap;
    if (mainMap) {
      var mv = mainMap.getView();
      var c = mv.getCenter();
      if (c) viewOpts.center = c.slice();
      if (mv.getZoom() != null) viewOpts.zoom = mv.getZoom();
    }
    previewMap = new ol.Map({ target: target, layers: [], view: new ol.View(viewOpts) });

    var state = getPrintLayerState();
    state.names.forEach(function(name, i) {
      previewMap.addLayer(createWmsLayer(name, state.opacities[i] / 100));
    });
    addPreviewBase(currentBaseIndex);
    setTimeout(function() { previewMap.updateSize(); }, 50);
  }

  // ------------------------------------------------------------------
  // dialog UI
  // ------------------------------------------------------------------
  function openDialog() {
    closeDialog();
    dialog = document.createElement('div');
    dialog.className = 'print-dialog-overlay';
    dialog.innerHTML =
      '<div class="print-dialog">' +
      '  <div class="print-dialog-header">' +
      '    <span class="print-dialog-title">Print Map</span>' +
      '    <button type="button" class="print-dialog-close" title="Close">&times;</button>' +
      '  </div>' +
      '  <div class="print-dialog-body">' +
      '    <div class="print-preview-wrap">' +
      '      <div class="print-preview-label">Preview — pan / zoom to set the printed area</div>' +
      '      <div class="print-preview-canvas"></div>' +
      '      <div class="print-preview-foot">' +
      '        <label>Base map</label>' +
      '        <select class="print-preview-basemap"></select>' +
      '      </div>' +
      '    </div>' +
      '    <div class="print-dialog-controls">' +
      '      <div class="print-field">' +
      '        <label for="print-layout">Layout</label>' +
      '        <select id="print-layout" class="print-layout"></select>' +
      '      </div>' +
      '      <label class="print-check print-use-extent-row">' +
      '        <input type="checkbox" class="print-use-extent" checked> Use preview extent' +
      '      </label>' +
      '      <div class="print-field">' +
      '        <label for="print-format">Format</label>' +
      '        <select id="print-format" class="print-format">' +
      '          <option value="pdf">PDF</option>' +
      '          <option value="jpg">JPG</option>' +
      '        </select>' +
      '      </div>' +
      '      <div class="print-field print-paper-row">' +
      '        <label for="print-paper">Paper</label>' +
      '        <select id="print-paper" class="print-paper">' +
      '          <option value="portrait">A4 Portrait</option>' +
      '          <option value="landscape">A4 Landscape</option>' +
      '        </select>' +
      '      </div>' +
      '      <div class="print-field">' +
      '        <label for="print-dpi">Resolution</label>' +
      '        <select id="print-dpi" class="print-dpi">' +
      '          <option value="72">72 DPI</option>' +
      '          <option value="150" selected>150 DPI</option>' +
      '          <option value="300">300 DPI</option>' +
      '        </select>' +
      '      </div>' +
      '      <div class="print-furniture">' +
      '        <label class="print-check"><input type="checkbox" class="print-f-title" checked> Title</label>' +
      '        <input type="text" class="print-title-text" placeholder="Map title (defaults to project name)">' +
      '        <label class="print-check"><input type="checkbox" class="print-f-legend" checked> Legend</label>' +
      '        <label class="print-check"><input type="checkbox" class="print-f-scale" checked> Scale bar</label>' +
      '        <label class="print-check"><input type="checkbox" class="print-f-north" checked> North arrow</label>' +
      '        <label class="print-check"><input type="checkbox" class="print-f-date" checked> Date &amp; author</label>' +
      '        <input type="text" class="print-author-text" placeholder="Author (optional)">' +
      '      </div>' +
      '      <div class="print-dialog-actions">' +
      '        <button type="button" class="print-cancel-btn">Cancel</button>' +
      '        <button type="button" class="print-export-btn">Export</button>' +
      '      </div>' +
      '      <div class="print-notice" style="display:none"></div>' +
      '    </div>' +
      '  </div>' +
      '</div>';
    document.body.appendChild(dialog);

    // --- layout dropdown ---
    var layoutSel = dialog.querySelector('.print-layout');
    layouts.forEach(function(name) {
      var opt = document.createElement('option');
      opt.value = name;
      opt.textContent = name;
      layoutSel.appendChild(opt);
    });
    var plainOpt = document.createElement('option');
    plainOpt.value = PLAIN;
    plainOpt.textContent = 'Plain map (client-side)';
    layoutSel.appendChild(plainOpt);
    layoutSel.value = layouts.length ? layouts[0] : PLAIN;

    // --- preview base map dropdown ---
    var baseSel = dialog.querySelector('.print-preview-basemap');
    config.baseMaps.forEach(function(bm, i) {
      var opt = document.createElement('option');
      opt.value = i;
      opt.textContent = bm.name;
      baseSel.appendChild(opt);
    });
    var noneOpt = document.createElement('option');
    noneOpt.value = '-1';
    noneOpt.textContent = 'No basemap';
    baseSel.appendChild(noneOpt);
    baseSel.value = currentBaseIndex;

    function syncControls() {
      var isPlain = layoutSel.value === PLAIN;
      dialog.querySelectorAll('.print-paper-row, .print-furniture').forEach(function(el) {
        el.style.display = isPlain ? '' : 'none';
      });
      dialog.querySelector('.print-use-extent-row').style.display = isPlain ? 'none' : '';
    }
    layoutSel.addEventListener('change', syncControls);
    syncControls();

    baseSel.addEventListener('change', function() {
      currentBaseIndex = parseInt(baseSel.value, 10);
      addPreviewBase(currentBaseIndex);
    });

    // --- close handlers ---
    var close = function() { closeDialog(); };
    dialog.querySelector('.print-dialog-close').addEventListener('click', close);
    dialog.querySelector('.print-cancel-btn').addEventListener('click', close);
    dialog.addEventListener('click', function(e) {
      if (e.target === dialog) close();
    });
    window.__printEscHandler = function esc(e) {
      if (e.key === 'Escape' && dialog) close();
    };
    document.addEventListener('keydown', window.__printEscHandler);

    // --- export ---
    dialog.querySelector('.print-export-btn').addEventListener('click', onExport);

    buildPreviewMap();
  }

  function closeDialog() {
    if (window.__printEscHandler) {
      document.removeEventListener('keydown', window.__printEscHandler);
      window.__printEscHandler = null;
    }
    if (previewMap) {
      previewMap.setTarget(null);
      previewMap = null;
      previewBaseLayer = null;
    }
    if (dialog) {
      dialog.parentNode && dialog.parentNode.removeChild(dialog);
      dialog = null;
    }
  }

  function setBusy(busy) {
    var btn = dialog && dialog.querySelector('.print-export-btn');
    if (btn) {
      btn.disabled = busy;
      btn.textContent = busy ? 'Rendering…' : 'Export';
    }
  }

  function showNotice(msg, kind) {
    var el = dialog && dialog.querySelector('.print-notice');
    if (!el) return;
    el.textContent = msg;
    el.style.display = 'block';
    el.className = 'print-notice ' + (kind === 'warn' ? 'print-notice-warn' : 'print-notice-ok');
  }

  // ------------------------------------------------------------------
  // QGIS layout path (GetPrint via the WMS proxy)
  // ------------------------------------------------------------------
  function exportWithLayout(layout, fmt) {
    var params = new URLSearchParams();
    params.set('SERVICE', 'WMS');
    params.set('VERSION', '1.3.0');
    params.set('REQUEST', 'GetPrint');
    params.set('TEMPLATE', layout); // this server version
    params.set('LAYOUT', layout);   // newer docs alias
    params.set('FORMAT', fmt === 'pdf' ? 'pdf' : 'jpg');
    params.set('DPI', dialog.querySelector('.print-dpi').value);
    params.set('CRS', 'EPSG:3857');
    if (dialog.querySelector('.print-use-extent').checked) {
      var ext = previewExtent();
      if (ext) params.set('map0:EXTENT', ext.join(','));
    }
    var state = getPrintLayerState();
    if (state.names.length) {
      params.set('map0:LAYERS', state.names.join(','));
      // OPACITIES is a top-level GetPrint parameter on a 0-255 scale
      // (parallel to map0:LAYERS order, first value = bottom layer).
      params.set('OPACITIES', state.opacities.map(function(o) { return Math.round(o * 2.55); }).join(','));
    }
    setBusy(true);
    showNotice('Rendering with layout "' + layout + '"…', 'ok');
    fetch(config.wmsUrl + '?' + params.toString(), { credentials: 'same-origin' })
      .then(function(resp) {
        var ct = (resp.headers.get('content-type') || '').toLowerCase();
        var isError = !resp.ok || ct.indexOf('xml') !== -1 || ct.indexOf('text') !== -1 || ct.indexOf('html') !== -1;
        return resp.blob().then(function(blob) {
          if (isError) {
            return new Promise(function(resolve, reject) {
              var reader = new FileReader();
              reader.onload = function() {
                reject(new Error(String(reader.result).replace(/<[^>]+>/g, ' ').trim().slice(0, 200) || ('HTTP ' + resp.status)));
              };
              reader.onerror = function() { reject(new Error('QGIS print error (HTTP ' + resp.status + ')')); };
              reader.readAsText(blob);
            });
          }
          return blob;
        });
      })
      .then(function(blob) {
        downloadBlob(blob, makeFilename(fmt));
        showNotice('Downloaded: ' + makeFilename(fmt), 'ok');
      })
      .catch(function(err) {
        console.warn('GetPrint failed — falling back to client-side:', err);
        showNotice('QGIS layout failed to render — exporting a plain map instead.', 'warn');
        clientSideExport(fmt);
      })
      .finally(function() { setBusy(false); });
  }

  // ------------------------------------------------------------------
  // client-side path (GetMap compositing + furniture)
  // ------------------------------------------------------------------
  function clientSideExport(fmt) {
    var dpi = parseInt(dialog.querySelector('.print-dpi').value, 10) || 150;
    var landscape = dialog.querySelector('.print-paper').value === 'landscape';
    var mm = landscape ? [297, 210] : [210, 297];
    var W = Math.round((mm[0] * dpi) / 25.4);
    var H = Math.round((mm[1] * dpi) / 25.4);
    var ext = previewExtent();
    if (!ext) {
      showNotice('Preview map is not ready.', 'warn');
      return;
    }
    var state = getPrintLayerState();

    var canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    var ctx = canvas.getContext('2d');
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, W, H);

    setBusy(true);
    showNotice('Rendering plain map…', 'ok');

    // Draw each visible WMS layer bottom -> top, pixel-exact at print size.
    var tasks = state.names.map(function(name, i) {
      var qs = new URLSearchParams({
        SERVICE: 'WMS',
        VERSION: '1.3.0',
        REQUEST: 'GetMap',
        LAYERS: name,
        STYLES: '',
        CRS: 'EPSG:3857',
        BBOX: ext.join(','),
        WIDTH: String(W),
        HEIGHT: String(H),
        FORMAT: 'image/png',
        TRANSPARENT: 'TRUE',
      });
      return loadImage(config.wmsUrl + '?' + qs.toString()).then(function(img) {
        ctx.globalAlpha = state.opacities[i] / 100;
        ctx.drawImage(img, 0, 0, W, H);
        ctx.globalAlpha = 1;
      }, function() {
        console.warn('Skipping layer that failed to render:', name);
      });
    });

    Promise.all(tasks)
      .then(function() {
        return drawFurniture(ctx, canvas, dpi, ext, W, H, state.names);
      })
      .then(function() {
        if (fmt === 'pdf') {
          exportPdf(canvas, W, H, landscape);
        } else {
          downloadCanvas(canvas, 'image/jpeg', makeFilename('jpg'), 0.92);
          showNotice('Downloaded: ' + makeFilename('jpg'), 'ok');
        }
      })
      .catch(function(err) {
        console.error('Client-side print failed:', err);
        showNotice('Client-side render failed: ' + err.message, 'warn');
      })
      .finally(function() { setBusy(false); });
  }

  function legendImageUrl(name) {
    var qs = new URLSearchParams({
      SERVICE: 'WMS',
      VERSION: '1.3.0',
      REQUEST: 'GetLegendGraphic',
      LAYER: name,
      FORMAT: 'image/png',
    });
    return config.wmsUrl + '?' + qs.toString();
  }

  function niceScale(metersPerPixel, targetPx) {
    var raw = metersPerPixel * targetPx;
    var mag = Math.pow(10, Math.floor(Math.log(raw) / Math.LN10));
    var norm = raw / mag;
    var nice = norm < 1.5 ? 1 : norm < 3.5 ? 2 : norm < 7.5 ? 5 : 10;
    return nice * mag;
  }

  function drawFurniture(ctx, canvas, dpi, ext, W, H, layerNames) {
    var s = dpi / 150; // scale factor for furniture sizes
    var margin = Math.round(28 * s);
    var fTitle = dialog.querySelector('.print-f-title').checked;
    var fLegend = dialog.querySelector('.print-f-legend').checked;
    var fScale = dialog.querySelector('.print-f-scale').checked;
    var fNorth = dialog.querySelector('.print-f-north').checked;
    var fDate = dialog.querySelector('.print-f-date').checked;
    var titleText = dialog.querySelector('.print-title-text').value.trim() || projectName;
    var authorText = dialog.querySelector('.print-author-text').value.trim();

    var y = margin;

    // Title + date/author header
    if (fTitle && titleText) {
      ctx.font = 'bold ' + Math.round(30 * s) + 'px sans-serif';
      ctx.fillStyle = '#111111';
      ctx.textAlign = 'center';
      ctx.fillText(titleText, W / 2, y);
      ctx.textAlign = 'left';
      y += Math.round(42 * s);
    }
    if (fDate) {
      var dateLine = todayStr() + (authorText ? '  •  ' + authorText : '');
      ctx.font = Math.round(13 * s) + 'px sans-serif';
      ctx.fillStyle = '#555555';
      ctx.textAlign = 'right';
      ctx.fillText(dateLine, W - margin, y - Math.round(14 * s));
      ctx.textAlign = 'left';
    }

    // Legend (right side, below the header)
    var legendX = W - margin;
    var legendY = y + Math.round(6 * s);
    var maxLegendH = H * 0.62;
    var entries = [];
    function fetchLegend(name) {
      return loadImage(legendImageUrl(name)).then(function(img) {
        entries.push({ name: name, img: img });
      });
    }
    var legendOrder = fLegend ? layerNames.slice().reverse() : [];
    var legendTasks = legendOrder.map(fetchLegend);
    return Promise.all(legendTasks).then(function() {
      if (fLegend && entries.length) {
        var rowH = Math.round(26 * s);
        var maxRows = Math.floor(maxLegendH / rowH);
        var shown = entries.slice(0, maxRows);
        var boxW = Math.round(170 * s);
        var boxH = shown.length * rowH + Math.round(8 * s);
        var bx = legendX - boxW;
        var by = legendY;
        ctx.fillStyle = 'rgba(255,255,255,0.92)';
        ctx.fillRect(bx - Math.round(6 * s), by - Math.round(4 * s), boxW + Math.round(12 * s), boxH + Math.round(8 * s));
        ctx.strokeStyle = '#cccccc';
        ctx.lineWidth = 1;
        ctx.strokeRect(bx - Math.round(6 * s), by - Math.round(4 * s), boxW + Math.round(12 * s), boxH + Math.round(8 * s));
        shown.forEach(function(en) {
          var imgH = Math.round(16 * s);
          var imgW = en.img.width && en.img.height ? Math.round(en.img.width * (imgH / en.img.height)) : Math.round(24 * s);
          ctx.font = 'bold ' + Math.round(11 * s) + 'px sans-serif';
          ctx.fillStyle = '#222222';
          ctx.fillText(en.name, bx, by + Math.round(14 * s));
          ctx.drawImage(en.img, bx + boxW - imgW, by + Math.round(2 * s), imgW, imgH);
          by += rowH;
        });
        if (entries.length > shown.length) {
          ctx.font = Math.round(10 * s) + 'px sans-serif';
          ctx.fillStyle = '#777777';
          ctx.fillText('+' + (entries.length - shown.length) + ' more', bx, by);
        }
      }

      // Scale bar (bottom-left)
      if (fScale) {
        var res = (ext[2] - ext[0]) / W;
        var dist = niceScale(res, 150 * s);
        var barPx = dist / res;
        var sbY = H - margin;
        var sbX = margin;
        ctx.strokeStyle = '#222222';
        ctx.fillStyle = '#222222';
        ctx.lineWidth = 2 * s;
        var seg = Math.round(barPx / 2);
        ctx.fillRect(sbX, sbY - Math.round(2 * s), seg, Math.round(4 * s));
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(sbX + seg, sbY - Math.round(2 * s), seg, Math.round(4 * s));
        ctx.strokeRect(sbX, sbY - Math.round(2 * s), barPx, Math.round(4 * s));
        var label = dist >= 1000 ? (dist / 1000) + ' km' : dist + ' m';
        ctx.font = Math.round(11 * s) + 'px sans-serif';
        ctx.fillStyle = '#222222';
        ctx.fillText(label, sbX + barPx / 2 - ctx.measureText(label).width / 2, sbY - Math.round(8 * s));
      }

      // North arrow (bottom-right)
      if (fNorth) {
        var nx = W - margin - Math.round(20 * s);
        var ny = H - margin - Math.round(10 * s);
        var r = Math.round(14 * s);
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(nx, ny, r + Math.round(3 * s), 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#222222';
        ctx.lineWidth = 1.5 * s;
        ctx.beginPath();
        ctx.arc(nx, ny, r, 0, Math.PI * 2);
        ctx.stroke();
        ctx.fillStyle = '#222222';
        ctx.beginPath();
        ctx.moveTo(nx, ny - r);
        ctx.lineTo(nx - r * 0.62, ny + r * 0.55);
        ctx.lineTo(nx, ny + r * 0.18);
        ctx.lineTo(nx + r * 0.62, ny + r * 0.55);
        ctx.closePath();
        ctx.fill();
        ctx.font = 'bold ' + Math.round(11 * s) + 'px sans-serif';
        ctx.fillStyle = '#222222';
        ctx.textAlign = 'center';
        ctx.fillText('N', nx, ny - r - Math.round(4 * s));
        ctx.textAlign = 'left';
      }
    });
  }

  function exportPdf(canvas, W, H, landscape) {
    if (!window.jspdf || !window.jspdf.jsPDF) {
      showNotice('PDF library not loaded — exporting JPG instead.', 'warn');
      downloadCanvas(canvas, 'image/jpeg', makeFilename('jpg'), 0.92);
      return;
    }
    var mmW = landscape ? 297 : 210;
    var mmH = landscape ? 210 : 297;
    // Page must be a true physical A4: jsPDF's px unit is 96 DPI, so pass mm.
    var pdf = new window.jspdf.jsPDF({
      orientation: landscape ? 'l' : 'p',
      unit: 'mm',
      format: [mmW, mmH],
      compress: true,
    });
    pdf.addImage(canvas.toDataURL('image/jpeg', 0.92), 'JPEG', 0, 0, mmW, mmH);
    pdf.save(makeFilename('pdf'));
    showNotice('Downloaded: ' + makeFilename('pdf'), 'ok');
  }

  function onExport() {
    if (!dialog || !previewMap) return;
    var layout = dialog.querySelector('.print-layout').value;
    var fmt = dialog.querySelector('.print-format').value;
    if (layout !== PLAIN) {
      exportWithLayout(layout, fmt);
    } else {
      clientSideExport(fmt);
    }
  }

  // ------------------------------------------------------------------
  // entry point (called from the print button / printMap)
  // ------------------------------------------------------------------
  window.openPrintDialog = openDialog;
})();
