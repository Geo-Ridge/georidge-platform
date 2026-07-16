(function() {
  var panel = document.getElementById('ms-layers-panel');
  var toggle = document.getElementById('ms-layers-toggle');
  var close = document.getElementById('ms-layers-close');

  if (toggle) {
    toggle.addEventListener('click', function() {
      if (panel) panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
    });
  }

  if (close) {
    close.addEventListener('click', function() {
      if (panel) panel.style.display = 'none';
      document.dispatchEvent(new CustomEvent('identify-clear', { bubbles: true }));
    });
  }

  document.querySelectorAll('.ms-layers-tab').forEach(function(tab) {
    tab.addEventListener('click', function() {
      var tabId = this.getAttribute('data-tab');
      document.querySelectorAll('.ms-layers-tab').forEach(function(t) { t.classList.remove('active'); });
      document.querySelectorAll('.ms-layers-content').forEach(function(c) { c.classList.remove('active'); });
      this.classList.add('active');
      var content = document.getElementById('ms-dock-' + tabId);
      if (content) content.classList.add('active');
    });
  });
})();
