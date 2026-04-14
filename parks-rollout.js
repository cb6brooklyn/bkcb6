(function(){
  var BOROUGH_INFO = {
    bk: {digit: '3', short: 'BK', name: 'Brooklyn', page: 'brooklyn.html', parksCode: 'B'},
    bx: {digit: '2', short: 'BX', name: 'Bronx', page: 'bronx.html', parksCode: 'X'},
    mn: {digit: '1', short: 'MN', name: 'Manhattan', page: 'manhattan.html', parksCode: 'M'},
    qn: {digit: '4', short: 'QN', name: 'Queens', page: 'queens.html', parksCode: 'Q'},
    si: {digit: '5', short: 'SI', name: 'Staten Island', page: 'statenisland.html', parksCode: 'R'}
  };

  var PARKS_DATA_URL = 'Parks_Properties_20260414.geojson';
  var CATEGORY_COLORS = {
    'Neighborhood Park': '#66bb6a',
    'Community Park': '#2e7d32',
    'Playground': '#42a5f5',
    'Jointly Operated Playground': '#1e88e5',
    'Triangle/Plaza': '#f9a825',
    'Garden': '#8bc34a',
    'Nature Area': '#00695c',
    'Recreational Field/Courts': '#8e24aa',
    'Waterfront Facility': '#26a69a',
    'Parkway': '#6d4c41',
    'Strip': '#90a4ae',
    'Mall': '#ff7043',
    'Flagship Park': '#2e7d32',
    'Historic House Park': '#795548',
    'Buildings/Institutions': '#546e7a',
    'Managed Sites': '#607d8b',
    'Undeveloped': '#bdbdbd',
    'Cemetery': '#9e9d24',
    'Lot': '#bcaaa4',
    'Operations': '#78909c',
    'Other': '#9aa0a6'
  };

  function escapeHtml(value){
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  async function fetchJson(url){
    var resp = await fetch(url);
    if (!resp.ok) throw new Error('Request failed: ' + resp.status);
    return await resp.json();
  }

  function ensureStyle(){
    if (document.getElementById('parks-rollout-style')) return;
    var style = document.createElement('style');
    style.id = 'parks-rollout-style';
    style.textContent = '' +
      '.parks-wrap{background:#fff;border:1px solid #e5e2db;border-radius:14px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.05)}' +
      '.parks-header{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;padding:18px 18px 12px;background:#fff;border-bottom:1px solid #e5e2db;flex-wrap:wrap}' +
      '.parks-header h3{margin:0;font-size:1.02rem;color:#0d1b4b}' +
      '.parks-header a{font-size:.8rem;font-weight:700;color:#f47920;text-decoration:none}' +
      '.parks-stat-row{display:flex;flex-wrap:wrap;gap:16px;padding:14px 18px;background:#f8f7f4;border-bottom:1px solid #e5e2db}' +
      '.parks-stat{display:flex;flex-direction:column;gap:2px}' +
      '.parks-stat-label{font-size:.58rem;font-family:\'DM Mono\',monospace;text-transform:uppercase;letter-spacing:.08em;color:#6b6760}' +
      '.parks-stat-value{font-size:.92rem;font-weight:700;color:#0d1b4b}' +
      '.parks-map-shell{padding:0 18px 18px;background:#fff}' +
      '.parks-leaflet-map{height:420px;width:100%;background:#eef2f4}' +
      '.parks-inline-note{margin:10px 18px 0;font-size:.8rem;line-height:1.55;color:#6b6760}' +
      '.parks-map-note{padding:0 18px 16px;font-size:.78rem;line-height:1.6;color:#6b6760;background:#fff}' +
      '.parks-legend{display:flex;flex-wrap:wrap;gap:8px 14px;padding:14px 18px 18px;background:#fff;border-top:1px solid #e5e2db}' +
      '.parks-legend-item{display:inline-flex;align-items:center;gap:8px;font-size:.74rem;color:#0d1b4b}' +
      '.parks-legend-swatch{width:12px;height:12px;border-radius:3px;display:inline-block;box-shadow:inset 0 0 0 1px rgba(0,0,0,.12)}' +
      '.parks-popup{font-family:\'DM Sans\',sans-serif;line-height:1.45}' +
      '.parks-popup strong{color:#0d1b4b}';
    document.head.appendChild(style);
  }

  function getPageContext(){
    var path = (location.pathname || '').split('/').pop();
    var cbMatch = path.match(/^cb\-(bk|bx|mn|qn|si)\-(\d+)\.html$/i);
    if (cbMatch) {
      var slug = cbMatch[1].toLowerCase();
      var district = String(parseInt(cbMatch[2], 10));
      return {
        type: 'cb',
        slug: slug,
        borough: BOROUGH_INFO[slug],
        district: district,
        boroCd: BOROUGH_INFO[slug].digit + district.padStart(2, '0'),
        domPrefix: 'parks' + slug + district,
        boundaryLabel: BOROUGH_INFO[slug].short + ' CB' + district,
        title: BOROUGH_INFO[slug].name + ' Community Board ' + district,
        sectionTitle: 'NYC Parks Map',
        sectionHeading: 'NYC Parks — ' + BOROUGH_INFO[slug].short + ' CB' + district,
        dataLink: 'https://data.cityofnewyork.us/Recreation/Parks-Properties/enfh-gkve'
      };
    }
    var boroughPages = {
      'brooklyn.html': 'bk',
      'bronx.html': 'bx',
      'manhattan.html': 'mn',
      'queens.html': 'qn',
      'statenisland.html': 'si'
    };
    var boroughSlug = boroughPages[path];
    if (boroughSlug) {
      return {
        type: 'borough',
        slug: boroughSlug,
        borough: BOROUGH_INFO[boroughSlug],
        domPrefix: 'parks-' + boroughSlug + '-borough',
        boundaryLabel: BOROUGH_INFO[boroughSlug].name,
        title: BOROUGH_INFO[boroughSlug].name,
        sectionTitle: BOROUGH_INFO[boroughSlug].name + ' Parks Map',
        sectionHeading: BOROUGH_INFO[boroughSlug].name + ' NYC Parks Properties',
        dataLink: 'https://data.cityofnewyork.us/Recreation/Parks-Properties/enfh-gkve'
      };
    }
    return null;
  }

  function getTargetBoundaryFeatures(boundaryData, context){
    var features = (boundaryData && boundaryData.features) || [];
    if (context.type === 'cb') {
      return features.filter(function(feature){
        return String(feature.properties && feature.properties.boro_cd) === context.boroCd;
      });
    }
    return features.filter(function(feature){
      return String((feature.properties && feature.properties.boro_cd) || '').charAt(0) === context.borough.digit;
    });
  }

  function parseCommunityBoards(raw){
    var str = String(raw == null ? '' : raw).replace(/[^0-9]/g, '');
    if (!str) return [];
    var boards = [];
    for (var i = 0; i < str.length; i += 3) {
      var part = str.slice(i, i + 3);
      if (part.length === 3) boards.push(part);
    }
    return boards;
  }

  function featureMatchesContext(feature, context){
    var props = (feature && feature.properties) || {};
    if (context.type === 'borough') return String(props.borough || '').toUpperCase() === context.borough.parksCode;
    return parseCommunityBoards(props.communityboard).indexOf(context.boroCd) !== -1;
  }

  function getCategory(typecategory){
    var label = String(typecategory || '').trim();
    return label && CATEGORY_COLORS[label] ? label : (label || 'Other');
  }

  function getCategoryColor(typecategory){
    return CATEGORY_COLORS[getCategory(typecategory)] || CATEGORY_COLORS.Other;
  }

  function formatAcres(value){
    var num = Number(value);
    if (!isFinite(num)) return 'Not listed';
    return num.toLocaleString(undefined, {maximumFractionDigits: 1}) + ' acres';
  }

  function computeStats(features){
    var totalAcres = 0;
    var validAcres = 0;
    features.forEach(function(feature){
      var acres = Number(feature && feature.properties && feature.properties.acres);
      if (isFinite(acres)) {
        totalAcres += acres;
        validAcres += 1;
      }
    });
    return {
      siteCount: features.length,
      acresLabel: validAcres ? totalAcres.toLocaleString(undefined, {maximumFractionDigits: 1}) : '0'
    };
  }

  function buildLegend(){
    var labels = ['Neighborhood Park','Community Park','Playground','Jointly Operated Playground','Triangle/Plaza','Garden','Nature Area','Recreational Field/Courts','Waterfront Facility','Other'];
    return labels.map(function(label){
      return '<span class="parks-legend-item"><span class="parks-legend-swatch" style="background:' + getCategoryColor(label) + '"></span>' + escapeHtml(label) + '</span>';
    }).join('');
  }

  function makeSectionHtml(context){
    var wrapperClass = context.type === 'cb' ? 'drop-section' : 'boro-drop-section';
    var toggleClass = context.type === 'cb' ? 'drop-toggle' : 'boro-drop-toggle';
    var bodyClass = context.type === 'cb' ? 'drop-body' : 'boro-drop-body';
    return '' +
      '<div class="' + wrapperClass + '" id="sec-parks">' +
        '<button class="' + toggleClass + '" type="button" id="' + context.domPrefix + '-toggle">' +
          '🌳 ' + context.sectionTitle +
          '<span class="' + (context.type === 'cb' ? 'drop-arr' : 'boro-drop-arr') + '">▼</span>' +
        '</button>' +
        '<div class="' + bodyClass + '">' +
          '<div class="parks-wrap">' +
            '<div class="parks-header">' +
              '<h3>' + context.sectionHeading + '</h3>' +
              '<a href="' + context.dataLink + '" target="_blank">NYC Parks data ↗</a>' +
            '</div>' +
            '<div class="parks-stat-row">' +
              '<div class="parks-stat"><span class="parks-stat-label">Boundary</span><span class="parks-stat-value">' + escapeHtml(context.boundaryLabel) + '</span></div>' +
              '<div class="parks-stat"><span class="parks-stat-label">Park Sites</span><span class="parks-stat-value" id="' + context.domPrefix + '-count">Loading…</span></div>' +
              '<div class="parks-stat"><span class="parks-stat-label">Mapped Acres</span><span class="parks-stat-value" id="' + context.domPrefix + '-acres">Loading…</span></div>' +
            '</div>' +
            '<p class="parks-inline-note">This map shows NYC Parks properties within the selected boundary. Click any site for its park name, property type, and mapped acreage.</p>' +
            '<div class="parks-map-shell"><div id="' + context.domPrefix + '-map" class="parks-leaflet-map" aria-label="Leaflet parks map for ' + escapeHtml(context.title) + '"></div></div>' +
            '<div class="parks-map-note" id="' + context.domPrefix + '-note">Loading parks properties and boundary geometry…</div>' +
            '<div class="parks-legend">' + buildLegend() + '<span class="parks-legend-item"><span class="parks-legend-swatch" style="background:#0d1b4b"></span>' + escapeHtml(context.boundaryLabel) + ' outline</span></div>' +
          '</div>' +
        '</div>' +
      '</div>';
  }

  function insertTocLink(context){
    if (document.querySelector('a[href="#sec-parks"]')) return;
    var anchorAfter = document.querySelector('a[href="#sec-landuse"]') || document.querySelector('a[href="#sec-zoning"]');
    if (!anchorAfter) return;
    var anchor = document.createElement('a');
    anchor.href = '#sec-parks';
    anchor.innerHTML = '🌳 NYC Parks Map<span class="' + (context.type === 'cb' ? 'toc-entry-sub' : 'boro-toc-entry-sub') + '">Park sites, type, and acreage</span>';
    anchorAfter.insertAdjacentElement('afterend', anchor);
  }

  function insertSection(context){
    if (document.getElementById(context.domPrefix + '-map')) return;
    var sectionAnchor = document.getElementById('sec-landuse') || document.getElementById('sec-zoning');
    if (!sectionAnchor) return;
    sectionAnchor.insertAdjacentHTML('afterend', makeSectionHtml(context));
    insertTocLink(context);
  }

  function attachToggle(context){
    var btn = document.getElementById(context.domPrefix + '-toggle');
    if (!btn || btn.dataset.bound === 'true') return;
    btn.dataset.bound = 'true';
    btn.addEventListener('click', function(){
      var body = btn.nextElementSibling;
      if (!body) return;
      var open = body.classList.toggle('open');
      btn.classList.toggle('open', open);
      if (open) setTimeout(function(){ initializeParksMap(context); }, 180);
    });
  }

  function boundaryStyle(context){
    return {
      color: '#0d1b4b',
      weight: context.type === 'cb' ? 3 : 2.2,
      fillOpacity: 0,
      opacity: 1
    };
  }

  async function initializeParksMap(context){
    if (context.mapInitialized || context.mapLoading) return;
    var mapId = context.domPrefix + '-map';
    var mapEl = document.getElementById(mapId);
    var noteEl = document.getElementById(context.domPrefix + '-note');
    var countEl = document.getElementById(context.domPrefix + '-count');
    var acresEl = document.getElementById(context.domPrefix + '-acres');
    if (!mapEl || typeof L === 'undefined') return;
    context.mapLoading = true;
    try {
      var data = await Promise.all([
        fetchJson('nyc_cb_boundaries.geojson'),
        fetchJson(PARKS_DATA_URL)
      ]);
      var boundaryData = data[0];
      var parksData = data[1];
      var boundaryFeatures = getTargetBoundaryFeatures(boundaryData, context);
      if (!boundaryFeatures.length) throw new Error('Boundary not found');
      var parkFeatures = ((parksData && parksData.features) || []).filter(function(feature){
        return featureMatchesContext(feature, context);
      });
      var stats = computeStats(parkFeatures);
      if (countEl) countEl.textContent = stats.siteCount.toLocaleString();
      if (acresEl) acresEl.textContent = stats.acresLabel;

      var map = L.map(mapId, {
        scrollWheelZoom: false,
        zoomControl: true,
        minZoom: context.type === 'cb' ? 11 : 9
      });
      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap © CARTO',
        maxZoom: 20
      }).addTo(map);

      var boundaryLayer = L.geoJSON({type:'FeatureCollection', features: boundaryFeatures}, {style: boundaryStyle(context)}).addTo(map);
      var parksLayer = L.geoJSON({type:'FeatureCollection', features: parkFeatures}, {
        style: function(feature){
          return {
            color: '#ffffff',
            weight: 0.8,
            opacity: 0.9,
            fillColor: getCategoryColor(feature && feature.properties && feature.properties.typecategory),
            fillOpacity: 0.72
          };
        },
        onEachFeature: function(feature, layer){
          var props = (feature && feature.properties) || {};
          var name = props.signname || props.name311 || 'NYC Parks property';
          var typecategory = getCategory(props.typecategory);
          var popupHtml = '<div class="parks-popup"><strong>' + escapeHtml(name) + '</strong><br>' + escapeHtml(typecategory) + '<br><span style="font-size:.8rem;color:#6b6760">' + escapeHtml(formatAcres(props.acres)) + '</span>' + (props.location ? '<br><span style="font-size:.8rem;color:#6b6760">' + escapeHtml(props.location) + '</span>' : '') + '</div>';
          layer.bindPopup(popupHtml, {maxWidth: 280});
        }
      }).addTo(map);

      var bounds = boundaryLayer.getBounds();
      if ((!bounds || !bounds.isValid()) && parksLayer.getBounds && parksLayer.getBounds().isValid()) bounds = parksLayer.getBounds();
      if (bounds && bounds.isValid()) map.fitBounds(bounds, {padding:[18,18]});
      setTimeout(function(){
        map.invalidateSize();
        if (bounds && bounds.isValid()) map.fitBounds(bounds, {padding:[18,18]});
      }, 250);
      if (noteEl) noteEl.textContent = parkFeatures.length ? 'NYC Parks properties are active. Click any highlighted site for the property name and type.' : 'No parks properties were found for this boundary in the attached dataset.';
      context.map = map;
      context.mapInitialized = true;
    } catch (err) {
      console.error(err);
      if (noteEl) noteEl.textContent = 'The parks map could not be loaded right now. Please try refreshing the page.';
      if (countEl) countEl.textContent = 'Unavailable';
      if (acresEl) acresEl.textContent = 'Unavailable';
    } finally {
      context.mapLoading = false;
    }
  }

  function init(){
    var context = getPageContext();
    if (!context) return;
    ensureStyle();
    insertSection(context);
    attachToggle(context);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, {once:true});
  } else {
    init();
  }
})();
