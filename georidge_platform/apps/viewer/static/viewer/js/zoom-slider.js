(function() {
  var slider = document.getElementById('zoom-slider');
  var range = document.getElementById('zoom-slider-range');
  var btnIn = document.getElementById('zoom-slider-in');
  var btnOut = document.getElementById('zoom-slider-out');
  var map = window.viewerMap;
  if (!slider || !range || !map) return;

  range.min = 0;
  range.max = 28;

  function updateSlider() {
    var zoom = map.getView().getZoom();
    if (zoom !== undefined) range.value = Math.round(zoom);
  }

  range.addEventListener('input', function() {
    map.getView().animate({ zoom: parseFloat(this.value), duration: 100 });
  });

  if (btnIn) btnIn.addEventListener('click', window.zoomIn);
  if (btnOut) btnOut.addEventListener('click', window.zoomOut);

  map.getView().on('change:resolution', updateSlider);
  slider.classList.add('active');
  updateSlider();
})();
