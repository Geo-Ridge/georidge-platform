(function() {
  var panel = document.getElementById('qwc2-slide-panel');
  var hamburger = document.getElementById('qwc2-hamburger');
  var backdrop = document.getElementById('qwc2-backdrop');

  function togglePanel() {
    if (!panel) return;
    var isOpen = panel.classList.toggle('open');
    if (backdrop) backdrop.style.display = isOpen ? 'block' : 'none';
  }

  if (hamburger) hamburger.addEventListener('click', togglePanel);
  if (backdrop) backdrop.addEventListener('click', togglePanel);

  document.querySelectorAll('.qwc2-slide-tab').forEach(function(tab) {
    tab.addEventListener('click', function() {
      var tabId = this.getAttribute('data-tab');
      document.querySelectorAll('.qwc2-slide-tab').forEach(function(t) { t.classList.remove('active'); });
      document.querySelectorAll('.qwc2-slide-content').forEach(function(c) { c.classList.remove('active'); });
      this.classList.add('active');
      var content = document.getElementById('qwc2-slide-' + tabId);
      if (content) content.classList.add('active');
    });
  });
})();
