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
})();
