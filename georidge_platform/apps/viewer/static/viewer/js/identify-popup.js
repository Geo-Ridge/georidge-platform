(function() {
  var popup = null;
  var dragging = false;
  var resizing = false;
  var ox = 0;
  var oy = 0;
  var resizeStartX = 0;
  var resizeStartWidth = 0;

  function onDown(e) {
    if (!popup || popup.style.display === 'none') return;
    if (e.button !== 0) return;

    var rect = popup.getBoundingClientRect();
    var onRightEdge = (e.clientX >= rect.right - 6) && (e.clientX <= rect.right + 2) &&
                      (e.clientY >= rect.top) && (e.clientY <= rect.bottom);

    if (onRightEdge) {
      resizing = true;
      resizeStartX = e.clientX;
      resizeStartWidth = popup.offsetWidth;
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      e.preventDefault();
      e.stopPropagation();
      return;
    }

    var header = popup.querySelector('.identify-popup-header');
    if (!header) return;
    var hRect = header.getBoundingClientRect();
    if (e.clientX < hRect.left || e.clientX > hRect.right ||
        e.clientY < hRect.top || e.clientY > hRect.bottom) return;
    dragging = true;
    var popupRect = popup.getBoundingClientRect();
    ox = e.clientX - popupRect.left;
    oy = e.clientY - popupRect.top;
    e.preventDefault();
    e.stopPropagation();
  }
  function onMove(e) {
    if (dragging) {
      e.preventDefault();
      var x = e.clientX - ox;
      var y = e.clientY - oy;
      popup.style.left = x + 'px';
      popup.style.top = y + 'px';
    } else if (resizing) {
      e.preventDefault();
      var dx = e.clientX - resizeStartX;
      var maxW = window.innerWidth * 0.5;
      var w = Math.min(Math.max(resizeStartWidth + dx, 200), maxW);
      popup.style.width = w + 'px';
    }
  }
  function onUp() {
    dragging = false;
    resizing = false;
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }

  document.addEventListener('pointerdown', onDown, true);
  document.addEventListener('pointermove', onMove, true);
  document.addEventListener('pointerup', onUp, true);

  function createPopup() {
    if (popup) return popup;
    popup = document.createElement('div');
    popup.className = 'identify-popup';
    popup.style.cssText = 'position:fixed;z-index:9999;pointer-events:auto;touch-action:none;';

    var header = document.createElement('div');
    header.className = 'identify-popup-header';
    header.style.cssText = 'touch-action:none;cursor:move;pointer-events:auto;';

    var title = document.createElement('span');
    title.className = 'identify-popup-title';
    title.textContent = 'Feature Info';

    var closeBtn = document.createElement('button');
    closeBtn.className = 'identify-popup-close';
    closeBtn.title = 'Close';
    closeBtn.textContent = '\u00d7';
    closeBtn.style.pointerEvents = 'auto';

    var tabContainer = document.createElement('div');
    tabContainer.className = 'identify-popup-tabs';
    tabContainer.style.display = 'none';

    var body = document.createElement('div');
    body.className = 'identify-popup-body';
    body.style.pointerEvents = 'auto';

    header.appendChild(title);
    header.appendChild(closeBtn);
    popup.appendChild(header);
    popup.appendChild(tabContainer);
    popup.appendChild(body);

    closeBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      popup.style.display = 'none';
    });

    document.body.appendChild(popup);
    return popup;
  }

  function renderFeatureTabs(featureTabs) {
    var el = createPopup();
    var tabContainer = el.querySelector('.identify-popup-tabs');
    var body = el.querySelector('.identify-popup-body');

    if (!featureTabs || featureTabs.length === 0) {
      tabContainer.style.display = 'none';
      return;
    }

    function showTabContent(tab) {
      var html = '';
      if (tab.fields && tab.fields.length > 0) {
        html += '<table class="identify-popup-table">';
        html += '<thead><tr><th>Property</th><th>Value</th></tr></thead><tbody>';
        tab.fields.forEach(function(f) {
          html += '<tr><td>' + escapeHtml(f.name) + '</td><td>' + escapeHtml(String(f.value)) + '</td></tr>';
        });
        html += '</tbody></table>';
      }
      if (tab.media && tab.media.length > 0) {
        tab.media.forEach(function(m) {
          if (m.url && /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(m.url)) {
            html += '<div class="identify-popup-media">';
            html += '<img src="' + escapeHtml(m.url) + '" alt="' + escapeHtml(m.field) + '">';
            html += '</div>';
          } else if (m.url) {
            html += '<a href="' + escapeHtml(m.url) + '" target="_blank" class="identify-popup-doc-link">' + escapeHtml(m.field) + '</a>';
          }
        });
      }
      if (!html) html = '<p class="text-muted small">No data</p>';
      body.innerHTML = html;
      renderMedia(body);
    }

    if (featureTabs.length === 1) {
      tabContainer.style.display = 'none';
      showTabContent(featureTabs[0]);
    } else {
      tabContainer.style.display = 'flex';
      tabContainer.innerHTML = '';
      featureTabs.forEach(function(tab, idx) {
        var btn = document.createElement('button');
        btn.className = 'identify-popup-tab' + (idx === 0 ? ' active' : '');
        btn.textContent = tab.name;
        btn.addEventListener('click', function() {
          tabContainer.querySelectorAll('.identify-popup-tab').forEach(function(b) {
            b.classList.remove('active');
          });
          btn.classList.add('active');
          showTabContent(tab);
        });
        tabContainer.appendChild(btn);
      });
      showTabContent(featureTabs[0]);
    }
  }

  function renderHtmlTabs(tabs) {
    var el = createPopup();
    var tabContainer = el.querySelector('.identify-popup-tabs');
    var body = el.querySelector('.identify-popup-body');

    if (!tabs || tabs.length === 0) {
      tabContainer.style.display = 'none';
      return;
    }

    if (tabs.length === 1) {
      tabContainer.style.display = 'none';
      body.innerHTML = tabs[0].html;
      renderMedia(body);
      return;
    }

    tabContainer.style.display = 'flex';
    tabContainer.innerHTML = '';
    tabs.forEach(function(tab, idx) {
      var btn = document.createElement('button');
      btn.className = 'identify-popup-tab' + (idx === 0 ? ' active' : '');
      btn.textContent = tab.name;
      btn.addEventListener('click', function() {
        tabContainer.querySelectorAll('.identify-popup-tab').forEach(function(b) {
          b.classList.remove('active');
        });
        btn.classList.add('active');
        body.innerHTML = tab.html;
        renderMedia(body);
      });
      tabContainer.appendChild(btn);
    });
    body.innerHTML = tabs[0].html;
    renderMedia(body);
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function renderMedia(container) {
    var imgs = container.querySelectorAll('img[src]');
    imgs.forEach(function(img) {
      img.style.maxWidth = '100%';
      img.style.borderRadius = '4px';
      img.style.cursor = 'pointer';
      img.addEventListener('click', function() {
        var overlay = document.createElement('div');
        overlay.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.8);z-index:10000;display:flex;align-items:center;justify-content:center;cursor:pointer;';
        var fullImg = document.createElement('img');
        fullImg.src = img.src;
        fullImg.style.cssText = 'max-width:90vw;max-height:90vh;border-radius:8px;';
        overlay.appendChild(fullImg);
        overlay.addEventListener('click', function() {
          overlay.remove();
        });
        document.body.appendChild(overlay);
      });
    });
    var links = container.querySelectorAll('a[href]');
    links.forEach(function(a) {
      var href = a.getAttribute('href');
      if (/\.(pdf|doc|docx|xls|xlsx)$/i.test(href)) {
        a.style.display = 'inline-flex';
        a.style.alignItems = 'center';
        a.style.gap = '4px';
        a.style.padding = '4px 8px';
        a.style.background = 'var(--surface)';
        a.style.borderRadius = '4px';
        a.style.textDecoration = 'none';
        a.style.color = 'var(--text)';
        a.style.fontSize = '0.82rem';
        a.target = '_blank';
      }
    });
  }

  function showPopup(html, pixel, preParsed) {
    var el = createPopup();
    var tabContainer = el.querySelector('.identify-popup-tabs');
    var body = el.querySelector('.identify-popup-body');

    var featureTabsData = (preParsed && preParsed.featureTabs) || null;
    var qgisHtml = (preParsed && preParsed.qgisHtml) || null;

    var tabsData = null;
    var tabsScript = html.match(/<script type="application\/json" data-tabs>([\s\S]*?)<\/script>/);
    if (tabsScript) {
      try { tabsData = JSON.parse(tabsScript[1]); } catch(e) {}
    }
    html = html.replace(/<script type="application\/json" data-tabs>[\s\S]*?<\/script>/, '');

    if (featureTabsData && featureTabsData.length > 0) {
      renderFeatureTabs(featureTabsData);
    } else if (tabsData && tabsData.length > 0) {
      renderHtmlTabs(tabsData);
    } else if (qgisHtml) {
      tabContainer.style.display = 'none';
      body.innerHTML = qgisHtml;
      renderMedia(body);
    } else {
      tabContainer.style.display = 'none';
      body.innerHTML = html;
      renderMedia(body);
    }

    el.style.display = 'block';
    if (pixel && !el.style.left) {
      var pw = el.offsetWidth || 320;
      el.style.left = Math.min(pixel[0] + 15, window.innerWidth - pw - 10) + 'px';
      el.style.top = Math.min(pixel[1] + 15, window.innerHeight - 370) + 'px';
    }
  }

  document.addEventListener('identify-complete', function(e) {
    if (e.detail && e.detail.html) {
      showPopup(e.detail.html, e.detail.pixel, {
        featureTabs: e.detail.featureTabs,
        qgisHtml: e.detail.qgisHtml,
      });
    }
  });

  document.addEventListener('identify-clear', function() {
    if (popup) popup.style.display = 'none';
  });
})();
