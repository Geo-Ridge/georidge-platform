(function() {
  var sidebarBtns = document.querySelectorAll('.ms-sidebar-btn[data-tool]');

  var origSetTool = window.setTool;
  window.setTool = function(tool) {
    if (origSetTool) origSetTool(tool);
    sidebarBtns.forEach(function(b) {
      b.classList.toggle('ms-sidebar-active', b.getAttribute('data-tool') === tool);
    });
  };

  window.mapstoreGeolocate = function() {
    var map = window.viewerMap;
    if (!map || !navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(function(pos) {
      var coords = ol.proj.fromLonLat([pos.coords.longitude, pos.coords.latitude]);
      map.getView().animate({ center: coords, zoom: 14, duration: 500 });
    });
  };
})();
