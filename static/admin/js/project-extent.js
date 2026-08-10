(function() {
  'use strict';

  function init() {
    var select = document.getElementById('id_set_extent_layer');
    if (!select) return;

    var fieldIds = ['extent_min_x', 'extent_min_y', 'extent_max_x', 'extent_max_y'];
    var fields = {};
    fieldIds.forEach(function(name) {
      fields[name] = document.getElementById('id_' + name);
    });

    var status = document.createElement('span');
    status.style.cssText = 'margin-left:8px;font-size:12px;color:#666;vertical-align:middle;';

    var row = select.closest('.form-row, .fieldBox') || select.parentNode;
    row.appendChild(status);

    // Endpoint lives at /admin/projects/project/<pk>/extent/ — derive from the
    // current change-form URL (…/<pk>/change/).
    function extentUrl(layer) {
      var base = window.location.pathname.replace(/\/change\/?$/, '');
      return base + '/extent/?layer=' + encodeURIComponent(layer);
    }

    function setStatus(text, ok) {
      status.textContent = text;
      status.style.color = ok ? '#2e7d32' : '#c62828';
    }

    select.addEventListener('change', function() {
      var layer = select.value;
      if (!layer) {
        setStatus('', true);
        return;
      }
      setStatus('Fetching layer extent…', true);
      fetch(extentUrl(layer))
        .then(function(resp) {
          if (!resp.ok) return resp.json().then(function(d) { throw new Error(d.error || 'Request failed'); });
          return resp.json();
        })
        .then(function(data) {
          if (!data.extent || data.extent.length !== 4) {
            throw new Error('Unexpected response');
          }
          fieldIds.forEach(function(name, i) {
            if (fields[name]) fields[name].value = data.extent[i];
          });
          setStatus('Extent set from layer.', true);
        })
        .catch(function(err) {
          setStatus('Could not load extent: ' + err.message, false);
        });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
