(function() {
  'use strict';

  var toolBtns = document.querySelectorAll('.qwc2-navbar-btn[data-tool]');

  function clearToolActive() {
    toolBtns.forEach(function(b) { b.classList.remove('active'); });
  }

  var origSetTool = window.setTool;
  window.setTool = function(tool) {
    origSetTool(tool);
    clearToolActive();
    toolBtns.forEach(function(b) {
      if (b.getAttribute('data-tool') === tool) {
        b.classList.add('active');
      }
    });
  };

  window.qwc2Geolocate = function() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(function(pos) {
      var view = window.viewerMap.getView();
      view.setCenter(ol.proj.fromLonLat([pos.coords.longitude, pos.coords.latitude]));
      view.setResolution(2.388657133911758);
    }, function() {
      console.warn('Geolocation failed');
    });
  };
})();
