(function () {
  var NAVY_LIGHT = '#d7e3ff';
  var NAVY_DARK = '#0d1b4b';
  var ORANGE_LIGHT = '#fde1cf';
  var ORANGE_DARK = '#f47920';
  var SLIWA = '#cc0000';
  var BASE_OUTLINE = '#ffffff';
  var ACTIVE_OUTLINE = '#111827';
  var DEFAULT_CITY_LABEL = 'New York City';
  var geojsonPromise = null;
  var dataCache = {};
  var roots = [];

  var RACE_CONFIG = {
    MAYOR: {
      dataPath: 'data/mayor_cb_winner_margin.json',
      eyebrow: '2025 Mayor by Community Board',
      cardTitle: 'Mayor Winner-Margin Map by Community Board',
      intro: 'This map shows the winning candidate\'s percentage margin in each community board. Navy marks a Mamdani win and orange marks a Cuomo win.',
      legendTitle: 'Winning margin by community board',
      navyLabel: 'Mamdani',
      orangeLabel: 'Cuomo',
      winnerKey: 'winner',
      navyWinnerValue: 'mamdani',
      yesPctKey: 'mamdani_pct',
      noPctKey: 'cuomo_pct',
      yesLabel: 'Mamdani',
      noLabel: 'Cuomo',
      thirdLabel: 'Sliwa',
      thirdPctKey: 'sliwa_pct',
      fallbackLead: 'Select a community board to see the Mamdani, Cuomo, and Sliwa vote split there.',
      fallbackNote: 'Select any district to see the winner, the vote split, and how many election districts the winner carried there.',
      leadBuilder: function (district) {
        return district.district_label + ' — ' + district.winner_name + ' won this CB district ' + formatPct(district.mamdani_pct) + ' to ' + formatPct(district.cuomo_pct) + ' for Cuomo and ' + formatPct(district.sliwa_pct) + ' for Sliwa, and carried ' + district.winner_ed_count + ' of ' + district.total_eds + ' election districts here.';
      },
      tooltipBuilder: function (district) {
        return district.district_label + ' · ' + district.winner_name + ' +' + formatPct(district.margin_pct) + ' · ' + district.winner_ed_count + ' of ' + district.total_eds + ' EDs';
      }
    },
    Q2: {
      dataPath: 'data/ballot_q2_cb_winner_margin.json',
      eyebrow: '2025 Ballot Question 2 by Community Board',
      cardTitle: 'Question 2 Approval Margin Map by Community Board',
      intro: 'This map shows the approval margin in each community board. Navy marks Yes / Approve and orange marks No / Disapprove.',
      legendTitle: 'Approval margin by community board',
      navyLabel: 'Yes / Approve',
      orangeLabel: 'No / Disapprove',
      winnerKey: 'winner',
      navyWinnerValue: 'yes',
      yesPctKey: 'yes_pct',
      noPctKey: 'no_pct',
      yesLabel: 'Yes / Approve',
      noLabel: 'No / Disapprove',
      fallbackLead: 'Select a community board to see the Yes / Approve and No / Disapprove vote split there.',
      fallbackNote: 'Select any district to see the winning side, the vote split, and how many election districts that side carried there.',
      leadBuilder: function (district) {
        return district.district_label + ' — ' + district.winner_name + ' won this CB district ' + formatPct(district.yes_pct) + ' to ' + formatPct(district.no_pct) + ', and carried ' + district.winner_ed_count + ' of ' + district.total_eds + ' election districts here.';
      },
      tooltipBuilder: function (district) {
        return district.district_label + ' · ' + district.winner_name + ' +' + formatPct(district.margin_pct) + ' · ' + district.winner_ed_count + ' of ' + district.total_eds + ' EDs';
      }
    },
    Q3: {
      dataPath: 'data/ballot_q3_cb_winner_margin.json',
      eyebrow: '2025 Ballot Question 3 by Community Board',
      cardTitle: 'Question 3 Approval Margin Map by Community Board',
      intro: 'This map shows the approval margin in each community board. Navy marks Yes / Approve and orange marks No / Disapprove.',
      legendTitle: 'Approval margin by community board',
      navyLabel: 'Yes / Approve',
      orangeLabel: 'No / Disapprove',
      winnerKey: 'winner',
      navyWinnerValue: 'yes',
      yesPctKey: 'yes_pct',
      noPctKey: 'no_pct',
      yesLabel: 'Yes / Approve',
      noLabel: 'No / Disapprove',
      fallbackLead: 'Select a community board to see the Yes / Approve and No / Disapprove vote split there.',
      fallbackNote: 'Select any district to see the winning side, the vote split, and how many election districts that side carried there.',
      leadBuilder: function (district) {
        return district.district_label + ' — ' + district.winner_name + ' won this CB district ' + formatPct(district.yes_pct) + ' to ' + formatPct(district.no_pct) + ', and carried ' + district.winner_ed_count + ' of ' + district.total_eds + ' election districts here.';
      },
      tooltipBuilder: function (district) {
        return district.district_label + ' · ' + district.winner_name + ' +' + formatPct(district.margin_pct) + ' · ' + district.winner_ed_count + ' of ' + district.total_eds + ' EDs';
      }
    },
    Q4: {
      dataPath: 'data/ballot_q4_cb_winner_margin.json',
      eyebrow: '2025 Ballot Question 4 by Community Board',
      cardTitle: 'Question 4 Approval Margin Map by Community Board',
      intro: 'This map shows the approval margin in each community board. Navy marks Yes / Approve and orange marks No / Disapprove.',
      legendTitle: 'Approval margin by community board',
      navyLabel: 'Yes / Approve',
      orangeLabel: 'No / Disapprove',
      winnerKey: 'winner',
      navyWinnerValue: 'yes',
      yesPctKey: 'yes_pct',
      noPctKey: 'no_pct',
      yesLabel: 'Yes / Approve',
      noLabel: 'No / Disapprove',
      fallbackLead: 'Select a community board to see the Yes / Approve and No / Disapprove vote split there.',
      fallbackNote: 'Select any district to see the winning side, the vote split, and how many election districts that side carried there.',
      leadBuilder: function (district) {
        return district.district_label + ' — ' + district.winner_name + ' won this CB district ' + formatPct(district.yes_pct) + ' to ' + formatPct(district.no_pct) + ', and carried ' + district.winner_ed_count + ' of ' + district.total_eds + ' election districts here.';
      },
      tooltipBuilder: function (district) {
        return district.district_label + ' · ' + district.winner_name + ' +' + formatPct(district.margin_pct) + ' · ' + district.winner_ed_count + ' of ' + district.total_eds + ' EDs';
      }
    }
  };

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
      '.winner-margin-legend-subtitle{font-size:.68rem;line-height:1.5;color:#6b7280;margin-top:-4px}',
      '.winner-margin-legend-row{display:grid;grid-template-columns:112px minmax(0,1fr);gap:8px;align-items:center}',
      '.winner-margin-legend-label{font-size:.72rem;font-weight:700;color:#374151}',
      '.winner-margin-legend-bar{position:relative;height:12px;border-radius:999px;border:1px solid rgba(17,24,39,.08);overflow:hidden}',
      '.winner-margin-legend-scale{position:absolute;inset:0}',
      '.winner-margin-legend-tick{position:absolute;top:14px;transform:translateX(-50%);font-size:.63rem;color:#6b7280;white-space:nowrap}',
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

  function formatPct(value) {
    return Number(value || 0).toFixed(1).replace('.0', '') + '%';
  }

  function formatMarginLabel(value) {
    return '+' + formatPct(value || 0);
  }

  function getActiveTabRace() {
    var activeTab = document.querySelector('.q-tab.active[data-q]');
    return activeTab ? String(activeTab.getAttribute('data-q') || '').toUpperCase() : '';
  }

  function resolveRace(root) {
    var requested = String(root.getAttribute('data-race') || 'MAYOR').toUpperCase();
    if (requested === 'ACTIVE') {
      requested = String(document.body.getAttribute('data-winner-margin-race') || getActiveTabRace() || 'MAYOR').toUpperCase();
    }
    return RACE_CONFIG[requested] ? requested : 'MAYOR';
  }

  function loadGeojson() {
    if (!geojsonPromise) {
      geojsonPromise = fetch('community-district-boundaries.geojson').then(function (r) { return r.json(); });
    }
    return geojsonPromise;
  }

  function loadData(race) {
    if (!dataCache[race]) {
      dataCache[race] = fetch(RACE_CONFIG[race].dataPath).then(function (r) { return r.json(); });
    }
    return dataCache[race];
  }

  function marginFill(district, maxMargin, config) {
    var ratio = Math.max(0.14, Math.min(1, (district.margin_pct || 0) / (maxMargin || 1)));
    if (district[config.winnerKey] === config.navyWinnerValue) {
      return mixColor(NAVY_LIGHT, NAVY_DARK, ratio);
    }
    return mixColor(ORANGE_LIGHT, ORANGE_DARK, ratio);
  }

  function winnerColor(district, config) {
    return district[config.winnerKey] === config.navyWinnerValue ? NAVY_DARK : ORANGE_DARK;
  }

  function roundedLegendMax(maxMargin) {
    var value = maxMargin || 0;
    if (!value) return 0;
    return Math.ceil(value / 5) * 5;
  }

  function legendTickLabel(value) {
    if (!value) return '0%';
    var rounded = Math.round(value * 10) / 10;
    return (Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1).replace(/\.0$/, '')) + '%';
  }

  function legendHtml(maxMargin, config) {
    var legendMax = roundedLegendMax(maxMargin || 0);
    var midpointLabel = legendTickLabel(legendMax / 2);
    var maxLabel = legendTickLabel(legendMax);
    return '' +
      '<div class="winner-margin-legend">' +
        '<div class="winner-margin-legend-title">' + config.legendTitle + '</div>' +
        '<div class="winner-margin-legend-subtitle">Color intensity runs from 0% up to about ' + maxLabel + ' on this map.</div>' +
        '<div class="winner-margin-legend-row">' +
          '<span class="winner-margin-legend-label">' + config.navyLabel + '</span>' +
          '<div class="winner-margin-legend-bar">' +
            '<span class="winner-margin-legend-scale navy"></span>' +
            '<span class="winner-margin-legend-tick" style="left:0%">0%</span>' +
            '<span class="winner-margin-legend-tick" style="left:50%">' + midpointLabel + '</span>' +
            '<span class="winner-margin-legend-tick" style="left:100%">' + maxLabel + '</span>' +
          '</div>' +
        '</div>' +
        '<div class="winner-margin-legend-row">' +
          '<span class="winner-margin-legend-label">' + config.orangeLabel + '</span>' +
          '<div class="winner-margin-legend-bar">' +
            '<span class="winner-margin-legend-scale orange"></span>' +
            '<span class="winner-margin-legend-tick" style="left:0%">0%</span>' +
            '<span class="winner-margin-legend-tick" style="left:50%">' + midpointLabel + '</span>' +
            '<span class="winner-margin-legend-tick" style="left:100%">' + maxLabel + '</span>' +
          '</div>' +
        '</div>' +
      '</div>';
  }

  function detailHtml(district, config) {
    var winnerSentence = district.winner_name + ' won ' + district.winner_ed_count + ' of ' + district.total_eds + ' election districts in ' + district.district_label + '.';
    var thirdLine = '';
    if (config.thirdLabel && config.thirdPctKey) {
      thirdLine = '<div class="winner-margin-chip"><span class="winner-margin-chip-dot" style="background:' + SLIWA + '"></span>' + config.thirdLabel + ' ' + formatPct(district[config.thirdPctKey]) + '</div>';
    }
    return '' +
      '<div class="eyebrow">' + config.eyebrow + '</div>' +
      '<h4>' + district.district_label + '</h4>' +
      '<p class="lead">' + config.leadBuilder(district) + '</p>' +
      '<div class="winner-margin-chip"><span class="winner-margin-chip-dot" style="background:' + winnerColor(district, config) + '"></span><strong>' + winnerSentence + '</strong></div>' +
      '<div class="winner-margin-stat-grid">' +
        '<div class="winner-margin-stat"><span class="winner-margin-stat-label">Winner</span><span class="winner-margin-stat-value">' + district.winner_name + ' by ' + formatPct(district.margin_pct) + '</span></div>' +
        '<div class="winner-margin-stat"><span class="winner-margin-stat-label">Election districts carried</span><span class="winner-margin-stat-value">' + district.winner_name + ': ' + district.winner_ed_count + ' of ' + district.total_eds + '</span></div>' +
        '<div class="winner-margin-stat"><span class="winner-margin-stat-label">' + config.yesLabel + '</span><span class="winner-margin-stat-value">' + formatPct(district[config.yesPctKey]) + '</span></div>' +
        '<div class="winner-margin-stat"><span class="winner-margin-stat-label">' + config.noLabel + '</span><span class="winner-margin-stat-value">' + formatPct(district[config.noPctKey]) + '</span></div>' +
      '</div>' +
      thirdLine +
      '<div class="winner-margin-note">Select any community board to compare the winner, the margin, and the number of election districts carried there.</div>';
  }

  function fallbackHtml(label, config) {
    return '' +
      '<div class="eyebrow">' + config.eyebrow + '</div>' +
      '<h4>' + label + ' map</h4>' +
      '<p class="lead">' + config.fallbackLead + '</p>' +
      '<div class="winner-margin-stat-grid">' +
        '<div class="winner-margin-stat"><span class="winner-margin-stat-label">Navy scale</span><span class="winner-margin-stat-value">' + config.navyLabel + ' winning margin</span></div>' +
        '<div class="winner-margin-stat"><span class="winner-margin-stat-label">Orange scale</span><span class="winner-margin-stat-value">' + config.orangeLabel + ' winning margin</span></div>' +
      '</div>' +
      '<div class="winner-margin-note">' + config.fallbackNote + '</div>';
  }

  function buildCardHtml(mapLabel, data, config) {
    return '' +
      '<h3>' + mapLabel + ' ' + config.cardTitle + '</h3>' +
      '<p>' + config.intro + '</p>' +
      '<div class="winner-margin-layout">' +
        '<div>' +
          '<div class="winner-margin-map" data-role="map"></div>' +
          legendHtml(data.max_margin_pct, config) +
        '</div>' +
        '<div class="winner-margin-detail" data-role="detail"></div>' +
      '</div>';
  }

  function setDetail(detailEl, district, mapLabel, config) {
    detailEl.innerHTML = district ? detailHtml(district, config) : fallbackHtml(mapLabel, config);
  }

  function mapStyle(feature, districtData, maxMargin, config) {
    var district = districtData[feature.properties.boro_cd];
    return {
      color: BASE_OUTLINE,
      weight: 1.2,
      fillColor: district ? marginFill(district, maxMargin, config) : '#d1d5db',
      fillOpacity: district ? 0.92 : 0.45
    };
  }

  function bindInteractions(layer, district, detailEl, mapLabel, config) {
    layer.on({
      mouseover: function () {
        layer.setStyle({ weight: 2.6, color: ACTIVE_OUTLINE, fillOpacity: 1 });
        if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
          layer.bringToFront();
        }
        setDetail(detailEl, district, mapLabel, config);
      },
      mouseout: function () {
        if (!layer._map) return;
        layer.setStyle({ weight: 1.2, color: BASE_OUTLINE, fillOpacity: 0.92 });
      },
      click: function () {
        setDetail(detailEl, district, mapLabel, config);
      }
    });
    layer.bindTooltip(config.tooltipBuilder(district), { sticky: true, direction: 'top' });
  }

  function teardownRoot(root) {
    if (root._winnerMarginMap) {
      root._winnerMarginMap.remove();
      root._winnerMarginMap = null;
    }
    var existing = root.querySelector('.winner-margin-card');
    if (existing) existing.remove();
  }

  function renderMap(root, geojson, data, config, race) {
    var boroughSlug = root.getAttribute('data-borough');
    var isCitywide = !boroughSlug || boroughSlug === 'citywide' || boroughSlug === 'all';
    var mapLabel = root.getAttribute('data-borough-name') || (isCitywide ? DEFAULT_CITY_LABEL : boroughSlug);
    var districtData = data.districts || {};
    var boroughRows = isCitywide ? Object.keys(districtData).map(function (key) { return districtData[key]; }) : ((data.boroughs && data.boroughs[boroughSlug]) || []);
    if (!boroughRows.length) return;

    teardownRoot(root);
    root.setAttribute('data-rendered-race', race);

    var card = document.createElement('div');
    card.className = 'winner-margin-card';
    card.innerHTML = buildCardHtml(mapLabel, data, config);
    root.insertBefore(card, root.firstChild);

    var mapEl = root.querySelector('[data-role="map"]');
    var detailEl = root.querySelector('[data-role="detail"]');
    setDetail(detailEl, null, mapLabel, config);

    var map = L.map(mapEl, { zoomControl: false, attributionControl: false, scrollWheelZoom: false });
    root._winnerMarginMap = map;
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19
    }).addTo(map);

    var filtered = {
      type: 'FeatureCollection',
      features: geojson.features.filter(function (feature) {
        var code = String(feature.properties.boro_cd || '');
        if (!districtData[code]) return false;
        return isCitywide ? true : boroughRows.length && code.charAt(0) === boroughRows[0].boro_cd.charAt(0);
      })
    };

    var layer = L.geoJSON(filtered, {
      style: function (feature) {
        return mapStyle(feature, districtData, data.max_margin_pct, config);
      },
      onEachFeature: function (feature, eachLayer) {
        var district = districtData[String(feature.properties.boro_cd)];
        if (district) {
          bindInteractions(eachLayer, district, detailEl, mapLabel, config);
        }
      }
    }).addTo(map);

    map.fitBounds(layer.getBounds(), { padding: isCitywide ? [24, 24] : [14, 14] });
  }

  function renderRoot(root, geojson) {
    var race = resolveRace(root);
    var config = RACE_CONFIG[race];
    root.setAttribute('data-pending-race', race);
    loadData(race).then(function (data) {
      if (root.getAttribute('data-pending-race') !== race) return;
      renderMap(root, geojson, data, config, race);
    }).catch(function (err) {
      console.error('Winner-margin map data error:', race, err);
    });
  }

  function rerenderAll() {
    loadGeojson().then(function (geojson) {
      roots.forEach(function (root) { renderRoot(root, geojson); });
    }).catch(function (err) {
      console.error('Winner-margin map error:', err);
    });
  }

  function init() {
    injectStyles();
    roots = Array.prototype.slice.call(document.querySelectorAll('[data-winner-margin-root]'));
    if (!roots.length || typeof L === 'undefined') return;
    rerenderAll();
    document.addEventListener('winner-margin-race-change', rerenderAll);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
