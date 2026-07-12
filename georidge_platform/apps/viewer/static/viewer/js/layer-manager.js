(function() {
  'use strict';

  var olLayers = {};

  function legendUrl(wmsUrl, name) {
    return wmsUrl + '?SERVICE=WMS&REQUEST=GetLegendGraphic&LAYER=' + encodeURIComponent(name) + '&FORMAT=image/png';
  }

  function createOlLayer(wmsUrl, name) {
    var src = new ol.source.TileWMS({
      url: wmsUrl,
      params: { LAYERS: name, TILED: true },
      serverType: 'qgis',
    });
    var layer = new ol.layer.Tile({ source: src });
    layer.set('name', name);
    olLayers[name] = layer;
    return layer;
  }

  var iconBase = '/static/viewer/icons/default/';
  var iconExt = 'svg';

  function buildUI(nodes, wmsUrl, map, parentEl, groupLayerNames) {
    nodes.forEach(function(node) {
      if (node.type === 'group') {
        var groupName = node.name || node.title || 'Group';
        var container = document.createElement('div');
        container.className = 'layer-group';

        var header = document.createElement('div');
        header.className = 'layer-group-header';

        var toggle = document.createElement('span');
        toggle.className = 'layer-group-toggle';
        var toggleImg = document.createElement('img');
        toggleImg.src = iconBase + 'group-expand.' + iconExt;
        toggleImg.width = 12;
        toggleImg.height = 12;
        toggleImg.alt = '';
        toggle.appendChild(toggleImg);
        toggle.addEventListener('click', function() {
          var children = container.querySelector('.layer-group-children');
          var expanded = children.style.display !== 'none';
          children.style.display = expanded ? 'none' : 'block';
          toggleImg.src = iconBase + (expanded ? 'group-expand.' + iconExt : 'group-collapse.' + iconExt);
        });

        var cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.checked = true;
        cb.addEventListener('change', function() {
          toggleChildLayers(container, cb.checked);
        });

        var label = document.createElement('span');
        label.className = 'layer-group-label small';
        label.textContent = groupName;

        header.appendChild(toggle);
        header.appendChild(cb);
        header.appendChild(label);

        var children = document.createElement('div');
        children.className = 'layer-group-children';

        container.appendChild(header);
        container.appendChild(children);
        parentEl.appendChild(container);

        var childNames = (groupLayerNames && groupLayerNames[node.name]) || [];
        buildUI(node.children || [], wmsUrl, map, children, groupLayerNames);
      } else if (node.type === 'layer' && node.name) {
        var layer = createOlLayer(wmsUrl, node.name);
        map.addLayer(layer);

        var item = document.createElement('div');
        item.className = 'layer-item';
        item.dataset.layerName = node.name;

        var cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.checked = true;
        cb.addEventListener('change', function() {
          layer.setVisible(cb.checked);
        });

        var img = document.createElement('img');
        img.className = 'legend-img';
        img.src = legendUrl(wmsUrl, node.name);
        img.alt = '';

        var span = document.createElement('span');
        span.className = 'small';
        span.textContent = node.title || node.name;

        var opacityContainer = document.createElement('span');
        opacityContainer.className = 'layer-opacity';
        var range = document.createElement('input');
        range.type = 'range';
        range.min = '0';
        range.max = '1';
        range.step = '0.1';
        range.value = '1';
        range.title = 'Opacity';
        range.addEventListener('input', function() {
          layer.setOpacity(parseFloat(range.value));
        });
        opacityContainer.appendChild(range);

        item.appendChild(cb);
        item.appendChild(img);
        item.appendChild(span);
        item.appendChild(opacityContainer);
        parentEl.appendChild(item);
      }
    });
  }

  function toggleChildLayers(container, visible) {
    var items = container.querySelectorAll('.layer-item[data-layer-name]');
    items.forEach(function(item) {
      var name = item.dataset.layerName;
      var cb = item.querySelector('input[type="checkbox"]');
      if (cb) cb.checked = visible;
      if (olLayers[name]) olLayers[name].setVisible(visible);
    });
    var subContainers = container.querySelectorAll('.layer-group');
    subContainers.forEach(function(sub) {
      var subCb = sub.querySelector('.layer-group-header > input[type="checkbox"]');
      if (subCb) subCb.checked = visible;
      toggleChildLayers(sub, visible);
    });
  }

  function setupDragDrop(container) {
    var items = container.querySelectorAll('.layer-item[draggable]');
    // drag-drop is set up per-group in renderLayerGroups
  }

  function renderLayerGroups(nodes, wmsUrl, map, parentEl, groupLayerNames) {
    nodes.forEach(function(node) {
      if (node.type === 'group') {
        var groupChildren = parentEl.querySelector('.layer-group:last-child .layer-group-children');
        if (groupChildren) {
          makeSortable(groupChildren);
        }
      }
    });
  }

  function makeSortable(container) {
    var draggingIndex = null;
    container.addEventListener('dragstart', function(e) {
      var item = e.target.closest('.layer-item');
      if (!item) return;
      draggingIndex = Array.prototype.indexOf.call(container.children, item);
      item.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
    });
    container.addEventListener('dragover', function(e) {
      var item = e.target.closest('.layer-item');
      if (!item) return;
      e.preventDefault();
      item.classList.add('drag-over');
    });
    container.addEventListener('dragend', function() {
      draggingIndex = null;
      container.querySelectorAll('.drag-over').forEach(function(el) { el.classList.remove('drag-over'); });
      container.querySelectorAll('.dragging').forEach(function(el) { el.classList.remove('dragging'); });
    });
    container.addEventListener('drop', function(e) {
      e.preventDefault();
      var target = e.target.closest('.layer-item');
      if (!target || draggingIndex === null) return;
      var toIndex = Array.prototype.indexOf.call(container.children, target);
      if (draggingIndex !== toIndex) {
        var items = Array.prototype.slice.call(container.children);
        var dragged = items[draggingIndex];
        container.insertBefore(dragged, toIndex > draggingIndex ? target.nextSibling : target);
        reorderMapLayers();
      }
      draggingIndex = null;
    });
  }

  function reorderMapLayers() {
    var tree = document.getElementById('layer-tree');
    var names = [];
    tree.querySelectorAll('.layer-item[data-layer-name]').forEach(function(item) {
      names.push(item.dataset.layerName);
    });
    var map = window.viewerMap;
    if (!map) return;
    names.forEach(function(name) {
      var layer = olLayers[name];
      if (layer) map.removeLayer(layer);
    });
    names.forEach(function(name) {
      var layer = olLayers[name];
      if (layer) map.addLayer(layer);
    });
    // Ensure base map stays at bottom
    map.getLayers().forEach(function(l) {
      if (l.get('__base')) {
        map.removeLayer(l);
        map.getLayers().insertAt(0, l);
      }
    });
  }

  function getQueryableLayerNames(nodes) {
    var names = [];
    nodes.forEach(function(node) {
      if (node.type === 'layer' && node.name) {
        if (node.queryable) names.push(node.name);
      } else if (node.type === 'group') {
        names = names.concat(getQueryableLayerNames(node.children || []));
      }
    });
    return names;
  }

  window.initLayerManager = function(config, map) {
    window.viewerMap = map;
    var tree = document.getElementById('layer-tree');
    if (!tree || !config.layerTree) return;
    tree.innerHTML = '';
    if (config.iconBase) iconBase = config.iconBase;
    if (config.iconExt) iconExt = config.iconExt;

    buildUI(config.layerTree, config.wmsUrl, map, tree);
    makeSortable(tree);

    if (window.applyIconFallbacks) window.applyIconFallbacks(tree);

    // Re-apply draggable and sortable to leaf items
    tree.querySelectorAll('.layer-item').forEach(function(item) {
      item.draggable = true;
    });
    tree.querySelectorAll('.layer-group-children').forEach(function(container) {
      makeSortable(container);
    });

    window.getQueryableLayers = function() {
      return getQueryableLayerNames(config.layerTree);
    };
  };
})();
