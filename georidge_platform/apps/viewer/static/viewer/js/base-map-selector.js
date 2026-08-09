(function() {
  'use strict';

  var configEl = document.getElementById('map-config');
  if (!configEl) return;
  var config = JSON.parse(configEl.textContent);
  var baseMaps = config.baseMaps;
  if (!baseMaps || baseMaps.length === 0) return;

  var toggleBtn = document.getElementById('basemap-toggle');
  var panel = document.getElementById('basemap-panel');
  var list = document.getElementById('basemap-list');

  var activeIndex = 0;

  var NONE_INDEX = -1;
  var noneThumb = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">' +
    '<rect width="64" height="64" fill="#f4f4f5" stroke="#cbd5e1" stroke-dasharray="4 3"/>' +
    '<circle cx="32" cy="32" r="13" fill="none" stroke="#94a3b8" stroke-width="3"/>' +
    '<line x1="22" y1="42" x2="42" y2="22" stroke="#94a3b8" stroke-width="3"/>' +
    '</svg>'
  );

  function buildList() {
    list.innerHTML = '';

    // "No basemap" option first: hides the base layer, data layers only.
    var noneItem = document.createElement('div');
    noneItem.className = 'basemap-item' + (activeIndex === NONE_INDEX ? ' active' : '');
    noneItem.dataset.index = NONE_INDEX;
    noneItem.title = 'No basemap — data layers only';

    var noneImg = document.createElement('img');
    noneImg.className = 'basemap-thumb';
    noneImg.src = noneThumb;
    noneImg.width = 64;
    noneImg.height = 64;
    noneImg.alt = 'No basemap';

    var noneLabel = document.createElement('span');
    noneLabel.className = 'basemap-label';
    noneLabel.textContent = 'No basemap';

    noneItem.appendChild(noneImg);
    noneItem.appendChild(noneLabel);
    noneItem.addEventListener('click', function() {
      selectBaseMap(NONE_INDEX);
    });
    list.appendChild(noneItem);

    baseMaps.forEach(function(bm, i) {
      var item = document.createElement('div');
      item.className = 'basemap-item' + (i === activeIndex ? ' active' : '');
      item.dataset.index = i;

      var img = document.createElement('img');
      img.className = 'basemap-thumb';
      img.src = bm.thumbnailUrl;
      img.width = 64;
      img.height = 64;
      img.alt = bm.name;
      img.loading = 'lazy';

      var label = document.createElement('span');
      label.className = 'basemap-label';
      label.textContent = bm.name;

      item.appendChild(img);
      item.appendChild(label);

      item.addEventListener('click', function() {
        selectBaseMap(i);
      });

      list.appendChild(item);
    });
  }

  function selectBaseMap(index) {
    if (index === activeIndex) return;
    activeIndex = index;

    var oldItems = list.querySelectorAll('.basemap-item');
    oldItems.forEach(function(el) { el.classList.remove('active'); });
    var newItem = list.querySelector('.basemap-item[data-index="' + index + '"]');
    if (newItem) newItem.classList.add('active');

    if (index === NONE_INDEX) {
      if (window.hideBaseMap) window.hideBaseMap();
    } else if (window.switchBaseMap) {
      window.switchBaseMap(index);
    }
  }

  function initBaseMap() {
    if (window.__baseLayerInitialized) return;
    window.__baseLayerInitialized = true;

    // Called by map-core.js after map is created
  }

  toggleBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    var isOpen = panel.style.display !== 'none';
    panel.style.display = isOpen ? 'none' : 'block';
  });

  document.addEventListener('click', function(e) {
    if (panel.style.display !== 'none') {
      var sel = document.getElementById('basemap-selector');
      if (!sel.contains(e.target)) {
        panel.style.display = 'none';
      }
    }
  });

  buildList();
  window.__baseMaps = baseMaps;

})();
