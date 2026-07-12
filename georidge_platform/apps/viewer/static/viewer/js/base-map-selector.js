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

  function buildList() {
    list.innerHTML = '';
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

    if (window.switchBaseMap) {
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
