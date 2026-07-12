(function() {
  var sidebarBtns = document.querySelectorAll('.ms-sidebar-btn[data-tool]');
  sidebarBtns.forEach(function(btn) {
    btn.addEventListener('click', function() {
      sidebarBtns.forEach(function(b) { b.classList.remove('ms-sidebar-active'); });
      btn.classList.add('ms-sidebar-active');
    });
  });

  window.mapstoreGeolocate = function() {
    var map = window.viewerMap;
    if (!map || !navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(function(pos) {
      var coords = ol.proj.fromLonLat([pos.coords.longitude, pos.coords.latitude]);
      map.getView().animate({ center: coords, zoom: 14, duration: 500 });
    });
  };

  window.mapstoreClearHighlight = function() {
    var infoEl = document.getElementById('info-content');
    if (infoEl) infoEl.innerHTML = '<p class="text-muted small">Click on the map to identify features.</p>';
    var clearBtn = document.getElementById('clear-identify');
    if (clearBtn) clearBtn.style.display = 'none';
    var event = new CustomEvent('identify-clear', { bubbles: true });
    document.dispatchEvent(event);
  };
})();
