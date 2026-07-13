(function() {
  'use strict';

  var configEl = document.getElementById('map-config');
  if (!configEl) return;
  var config = JSON.parse(configEl.textContent);
  var searchConfigs = config.searchConfigs || [];

  var popup = null;

  function getPopupFields(layerName) {
    for (var i = 0; i < searchConfigs.length; i++) {
      if (searchConfigs[i].layer === layerName) {
        return searchConfigs[i].popup_fields || [];
      }
    }
    return [];
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function renderPopup(detail) {
    if (!popup) {
      popup = document.createElement('div');
      popup.className = 'map-only-popup';
      document.body.appendChild(popup);
    }

    var html = '<button class="map-only-popup-close" title="Close">&times;</button>';
    html += '<div class="map-only-popup-label">' + escapeHtml(detail.label || '') + '</div>';

    var popupFields = getPopupFields(detail.layer);
    if (popupFields.length > 0 && detail.geojson && detail.geojson.properties) {
      var props = detail.geojson.properties;
      var fieldHtml = '';
      for (var i = 0; i < popupFields.length; i++) {
        var fieldName = popupFields[i];
        var value = props[fieldName];
        if (value !== undefined && value !== null && value !== '') {
          fieldHtml += '<div>' + escapeHtml(fieldName) + ': ' + escapeHtml(String(value)) + '</div>';
        }
      }
      if (fieldHtml) {
        html += '<div class="map-only-popup-fields">' + fieldHtml + '</div>';
      }
    }

    html += '<div class="map-only-popup-layer">' + escapeHtml(detail.layer_title || '') + '</div>';

    popup.innerHTML = html;
    popup.style.display = 'block';

    popup.querySelector('.map-only-popup-close').addEventListener('click', function(e) {
      e.stopPropagation();
      popup.style.display = 'none';
    });
  }

  document.addEventListener('search-select', function(e) {
    if (e.detail) {
      renderPopup(e.detail);
    }
  });

  document.addEventListener('click', function(e) {
    if (popup && popup.style.display !== 'none' && !popup.contains(e.target)) {
      popup.style.display = 'none';
    }
  });
})();
