(function () {
  var NAVY_LIGHT = '#d7e3ff';
  var NAVY_DARK = '#0d1b4b';
  var ORANGE_LIGHT = '#fde1cf';
  var ORANGE_DARK = '#f47920';
  var SLIWA = '#cc0000';
  var BASE_OUTLINE = '#ffffff';
  var ACTIVE_OUTLINE = '#111827';
  var boroughMaps = {};
  var DEFAULT_CITY_LABEL = 'New York City';

  function injectStyles() {
    if (document.getElementById('winner-margin-rollout-styles')) return;
    var style = document.createElement('style');
    style.id = 'winner-margin-rollout-styles';
    style.textContent = [
      '.winner-margin-card{background:#fff;border:1px solid var(--border,#e5e2db);border-radius:12px;padding:18px 18px 14px;margin:0 0 18px;box-shadow:0 2px 10px rgba(13,27,75,.06)}',
      '.winner-margin-card h3{margin:0 0 8px;color:var(--navy,#0d1b4b);font-size:1.02rem;line-height:1.3}',
      '.winner-margin-card p{margin:0 0 14px;color:#4b5563;font-size:.84rem;line-height:1.65}',
      '.winner-margin-layout{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(280px,.85fr);gap:16px;align-items:stretch}',
      '.winner-margin-map{height:520px;border-radius:10px;overflow:hidden;background:#edf2f7;border:1px solid var(--border,#e5e2db)}',
      '.winner-margin-detail{border:1px solid var(--border,#e5e2db);border-radius:10px;background:#f8f7f4;padding:16px;display:flex;flex-direction:column;gap:12px;min-height:220px}',
      '.winner-margin-detail .eyebrow{font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:#6b7280;font-weight:700}',
      '.winner-margin-detail h4{margin:0;color:var(--navy,#0d1b4b);font-size:1.18rem;line-height:1.2}',
      '.winner-margin-detail .lead{margin:0;color:#111827;font-size:.92rem;line-height:1.6}',
      '.winner-margin-stat-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}',
      '.winner-margin-stat{background:#fff;border:1px solid var(--border,#e5e2db);border-radius:8px;padding:10px 12px}',
      '.winner-margin-stat-label{display:block;font-size:.68rem;letter-spacing:.04em;text-transform:uppercase;color:#6b7280;margin-bottom:4px}',
      '.winner-margin-stat-value{display:block;color:#111827;font-size:.92rem;font-weight:700;line-height:1.4}',
      '.winner-margin-legend{display:flex;flex-direction:column;gap:10px;margin-top:12px;font-size:.72rem;color:#4b5563}',
      '.winner-margin-legend-title{font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:#6b7280;font-weight:700}',
      '.winner-margin-legend-row{display:grid;grid-template-columns:112px minmax(0,1fr) 42px;gap:8px;align-items:center}',
      '.winner-margin-legend-label{font-size:.72rem;font-weight:700;color:#374151}',
      '.winner-margin-legend-bar{position:relative;height:12px;border-radius:999px;border:1px solid rgba(17,24,39,.08);overflow:hidden}',
      '.winner-margin-legend-scale{position:absolute;inset:0}',
      '.winner-margin-legend-tick{position:absolute;top:14px;transform:translateX(-50%);font-size:.63rem;color:#6b7280;white-space:nowrap}',
      '.winner-margin-legend-end{font-size:.72rem;font-weight:700;color:#374151;text-align:right}',
      '.winner-margin-legend-scale.navy{background:linear-gradient(90deg,' + NAVY_LIGHT + ' 0%,' + NAVY_DARK + ' 100%)}',
      '.winner-margin-legend-scale.orange{background:linear-gradient(90deg,' + ORANGE_LIGHT + ' 0%,' + ORANGE_DARK + ' 100%)}',
      '.winner-margin-chip{display:inline-flex;align-items:center;gap:6px;font-size:.72rem;font-weight:700;color:#374151}',
      '.winner-margin-chip-dot{width:10px;height:10px;border-radius:999px;display:inline-block}',
      '.winner-margin-note{font-size:.72rem;color:#6b7280;line-height:1.55}',
      '.winner-margin-map .leaflet-tooltip{background:rgba(17,24,39,.94);border:0;border-radius:8px;color:#fff;box-shadow:0 8px 28px rgba(0,0,0,.22);padding:8px 10px}',
      '@media (max-width: 960px){.winner-margin-layout{grid-template-columns:1fr}.winner-margin-map{height:420px}.winner-margin-detail{min-height:0}}'
    ].join('');
    document.head.appendChild(style);
  }

  function hexToRgb(hex) {
    var normalized = hex.replace('#', '');
    return {
      r: parseInt(normalized.slice(0, 2), 16),
      g: parseInt(normalized.slice(2, 4), 16),
      b: parseInt(normalized.slice(4, 6), 16)
    };
  }

  function rgbToHex(rgb) {
    function part(v) {
      var hex = Math.max(0, Math.min(255, Math.round(v))).toString(16);
      return hex.length === 1 ? '0' + hex : hex;
    }
    return '#' + part(rgb.r) + part(rgb.g) + part(rgb.b);
  }

  function mixColor(start, end, t) {
    var a = hexToRgb(start);
    var b = hexToRgb(end);
    return rgbToHex({
      r: a.r + (b.r - a.r) * t,
      g: a.g + (b.g - a.g) * t,
      b: a.b + (b.b - a.b) * t
    });
  }

  function marginFill(district, maxMargin) {
    var ratio = Math.max(0.14, Math.min(1, (district.margin_pct || 0) / (maxMargin || 1)));
    if (district.winner === 'mamdani') {
      return mixColor(NAVY_LIGHT, NAVY_DARK, ratio);
    }
    return mixColor(ORANGE_LIGHT, ORANGE_DARK, ratio);
  }

  function formatPct(value) {
    return Number(value || 0).toFixed(1).replace('.0', '') + '%';
  }

  function formatMarginLabel(value) {
    return '+' + formatPct(value || 0);
  }

  function winnerColor(district) {
    return district.winner === 'mamdani' ? NAVY_DARK : ORANGE_DARK;
  }

  function legendHtml(maxMargin) {
    var maxLabel = formatMarginLabel(maxMargin || 0);
    return '' +
      '<div class="winner-margin-legend">' +
        '<div class="winner-margin-legend-title">Winning margin by community board</div>' +
        '<div class="winner-margin-legend-row">' +
          '<span class="winner-margin-legend-label">Mamdani</span>' +
          '<div class="winner-margin-legend-bar">' +
            '<span class="winner-margin-legend-scale navy"></span>' +
            '<span class="winner-margin-legend-tick" style="left:0%">0%</span>' +
            '<span class="winner-margin-legend-tick" style="left:50%">'+ formatMarginLabel((maxMargin || 0) / 2) +'</span>' +
            '<span class="winner-margin-legend-tick" style="left:100%">'+ maxLabel +'</span>' +
          '</div>' +
          '<span class="winner-margin-legend-end">'+ maxLabel +'</span>' +
        '</div>' +
        '<div class="winner-margin-legend-row">' +
          '<span class="winner-margin-legend-label">Cuomo</span>' +
          '<div class="winner-margin-legend-bar">' +
            '<span class="winner-margin-legend-scale orange"></span>' +
            '<span class="winner-margin-legend-tick" style="left:0%">0%</span>' +
            '<span class="winner-margin-legend-tick" style="left:50%">'+ formatMarginLabel((maxMargin || 0) / 2) +'</span>' +
            '<span class="winner-margin-legend-tick" style="left:100%">'+ maxLabel +'</span>' +
          '</div>' +
          '<span class="winner-margin-legend-end">'+ maxLabel +'</span>' +
        '</div>' +
      '</div>';
  }

  function detailHtml(district) {
    var winnerSentence = district.winner_name + ' won ' + district.winner_ed_count + ' of ' + district.total_eds + ' election districts in ' + district.district_label + '.';
    return '' +
      '<div class="eyebrow">2025 Mayor by Community Board</div>' +
      '<h4>' + district.district_label + '</h4>' +
      '<p class="lead">' + district.district_label + ' — ' + district.winner_name + ' won this CB district ' + formatPct(district.mamdani_pct) + ' to ' + formatPct(district.cuomo_pct) + ' for Cuomo and ' + formatPct(district.sliwa_pct) + ' for Sliwa.</p>' +
      '<div class="winner-margin-chip"><span class="winner-margin-chip-dot" style="background:' + winnerColor(district) + '"></span><strong>' + winnerSentence + '</strong></div>' +
      '<div class="winner-margin-stat-grid">' +
        '<div class="winner-margin-stat"><span class="winner-margin-stat-label">Winner</span><span class="winner-margin-stat-value">' + district.winner_name + ' by ' + formatPct(district.margin_pct) + '</span></div>' +
        '<div class="winner-margin-stat"><span class="winner-margin-stat-label">EDs won by ' + district.winner_name + '</span><span class="winner-margin-stat-value">' + district.winner_ed_count + ' of ' + district.total_eds + '</span></div>' +
        '<div class="winner-margin-stat"><span class="winner-margin-stat-label">Mamdani</span><span class="winner-margin-stat-value">' + formatPct(district.mamdani_pct) + '</span></div>' +
        '<div class="winner-margin-stat"><span class="winner-margin-stat-label">Cuomo</span><span class="winner-margin-stat-value">' + formatPct(district.cuomo_pct) + '</span></div>' +
      '</div>' +
      '<div class="winner-margin-chip"><span class="winner-margin-chip-dot" style="background:' + SLIWA + '"></span>Sliwa ' + formatPct(district.sliwa_pct) + '</div>' +
      '<div class="winner-margin-note">Hover or click any community board district to compare the winner, the margin, and exactly how many election districts the winning candidate carried there.</div>';
  }

  function fallbackHtml(label) {
    return '' +
      '<div class="eyebrow">2025 Mayor by Community Board</div>' +
      '<h4>' + label + ' map</h4>' +
      '<p class="lead">Hover or click a community board district to see the full Mamdani, Cuomo, and Sliwa split and a plain-language line showing exactly how many election districts the winning candidate carried there.</p>' +
      '<div class="winner-margin-stat-grid">' +
        '<div class="winner-margin-stat"><span class="winner-margin-stat-label">Navy scale</span><span class="winner-margin-stat-value">Mamdani winning margin</span></div>' +
        '<div class="winner-margin-stat"><span class="winner-margin-stat-label">Orange scale</span><span class="winner-margin-stat-value">Cuomo winning margin</span></div>' +
      '</div>' +
      '<div class="winner-margin-chip"><span class="winner-margin-chip-dot" style="background:' + SLIWA + '"></span>Sliwa is included in the hover summary percentages.</div>' +
      '<div class="winner-margin-note">The deeper the color, the wider the winning margin in that district.</div>';
  }

  function ensureCard(container, mapLabel, maxMargin) {
    if (container.querySelector('.winner-margin-card')) return;
    var card = document.createElement('div');
    card.className = 'winner-margin-card';
    card.innerHTML = '' +
      '<h3>' + mapLabel + ' Mayor Winner-Margin Map by Community Board</h3>' +
      '<p>Each community board is shaded by the winning candidate\'s percentage margin. Navy indicates a Mamdani win, orange indicates a Cuomo win, and the legend shows the numeric margin scale used for the shading. Hover or click a district for the full community-board result and the number of election districts the winner carried there.</p>' +
      '<div class="winner-margin-layout">' +
        '<div>' +
          '<div class="winner-margin-map" data-role="map"></div>' +
          legendHtml(maxMargin) +
        '</div>' +
        '<div class="winner-margin-detail" data-role="detail"></div>' +
      '</div>';
    container.insertBefore(card, container.firstChild);
  }

  function setDetail(detailEl, district, mapLabel) {
    detailEl.innerHTML = district ? detailHtml(district) : fallbackHtml(mapLabel);
  }

  function mapStyle(feature, districtData, maxMargin) {
    var district = districtData[feature.properties.boro_cd];
    return {
      color: BASE_OUTLINE,
      weight: 1.2,
      fillColor: district ? marginFill(district, maxMargin) : '#d1d5db',
      fillOpacity: district ? 0.92 : 0.45
    };
  }

  function bindInteractions(layer, district, detailEl, boroughName) {
    layer.on({
      mouseover: function () {
        layer.setStyle({ weight: 2.6, color: ACTIVE_OUTLINE, fillOpacity: 1 });
        if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
          layer.bringToFront();
        }
        setDetail(detailEl, district, boroughName);
      },
      mouseout: function () {
        if (!layer._map) return;
        layer.setStyle({ weight: 1.2, color: BASE_OUTLINE, fillOpacity: 0.92 });
      },
      click: function () {
        setDetail(detailEl, district, boroughName);
      }
    });
    layer.bindTooltip(district.district_label + ' · ' + district.winner_name + ' +' + formatPct(district.margin_pct), { sticky: true, direction: 'top' });
  }

  function renderMap(root, geojson, data) {
    var boroughSlug = root.getAttribute('data-borough');
    var isCitywide = !boroughSlug || boroughSlug === 'citywide' || boroughSlug === 'all';
    var mapLabel = root.getAttribute('data-borough-name') || (isCitywide ? DEFAULT_CITY_LABEL : boroughSlug);
    var districtData = data.districts || {};
    var boroughRows = isCitywide ? Object.keys(districtData).map(function (key) { return districtData[key]; }) : ((data.boroughs && data.boroughs[boroughSlug]) || []);
    if (!boroughRows.length) return;

    ensureCard(root, mapLabel, data.max_margin_pct);
    var mapEl = root.querySelector('[data-role="map"]');
    var detailEl = root.querySelector('[data-role="detail"]');
    setDetail(detailEl, null, mapLabel);

    var mapKey = isCitywide ? 'citywide' : boroughSlug;
    if (boroughMaps[mapKey]) {
      boroughMaps[mapKey].remove();
    }

    var map = L.map(mapEl, { zoomControl: false, attributionControl: false, scrollWheelZoom: false });
    boroughMaps[mapKey] = map;
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19
    }).addTo(map);

    var filtered = {
      type: 'FeatureCollection',
      features: geojson.features.filter(function (feature) {
        var code = String(feature.properties.boro_cd || '');
        if (!districtData[code]) return false;
        return isCitywide ? true : code.charAt(0) === boroughRows[0].boro_cd.charAt(0);
      })
    };

    var layer = L.geoJSON(filtered, {
      style: function (feature) {
        return mapStyle(feature, districtData, data.max_margin_pct);
      },
      onEachFeature: function (feature, eachLayer) {
        var district = districtData[String(feature.properties.boro_cd)];
        if (district) {
          bindInteractions(eachLayer, district, detailEl, mapLabel);
        }
      }
    }).addTo(map);

    map.fitBounds(layer.getBounds(), { padding: isCitywide ? [24, 24] : [14, 14] });
  }

  function init() {
    injectStyles();
    var roots = Array.prototype.slice.call(document.querySelectorAll('[data-winner-margin-root]'));
    if (!roots.length || typeof L === 'undefined') return;
    Promise.all([
      fetch('community-district-boundaries.geojson').then(function (r) { return r.json(); }),
      fetch('data/mayor_cb_winner_margin.json').then(function (r) { return r.json(); })
    ]).then(function (payload) {
      var geojson = payload[0];
      var data = payload[1];
      roots.forEach(function (root) { renderMap(root, geojson, data); });
    }).catch(function (err) {
      console.error('Winner-margin map error:', err);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
