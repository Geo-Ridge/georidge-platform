(function() {
  'use strict';

  window.createResizeHandle = function(panel, options) {
    options = options || {};

    panel.classList.add('panel-resizable');

    var minWidth = options.minWidth || 200;
    var maxWidthPct = options.maxWidthPct || 0.5;
    var onResizeEnd = options.onResizeEnd || null;
    var transitioning = options.transitionClass || null;
    var startX = 0;
    var startWidth = 0;
    var dragging = false;

    function onDown(e) {
      if (e.button !== 0) return;
      var rect = panel.getBoundingClientRect();
      if (e.clientX < rect.right - 6) return;
      dragging = true;
      startX = e.clientX;
      startWidth = panel.offsetWidth;
      if (transitioning) {
        panel.style.transition = 'none';
      }
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      e.preventDefault();
    }

    function onMove(e) {
      if (!dragging) return;
      var dx = e.clientX - startX;
      var maxW = window.innerWidth * maxWidthPct;
      var w = Math.min(Math.max(startWidth + dx, minWidth), maxW);
      panel.style.width = w + 'px';
      panel.style.minWidth = w + 'px';
    }

    function onUp() {
      if (!dragging) return;
      dragging = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      if (transitioning) {
        panel.style.transition = '';
      }
      if (onResizeEnd) onResizeEnd();
    }

    document.addEventListener('pointerdown', onDown);
    document.addEventListener('pointermove', onMove);
    document.addEventListener('pointerup', onUp);

    return { destroy: function() {
      document.removeEventListener('pointerdown', onDown);
      document.removeEventListener('pointermove', onMove);
      document.removeEventListener('pointerup', onUp);
      panel.classList.remove('panel-resizable');
    }};
  };
})();
