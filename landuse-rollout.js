(function(){
  var LAND_USE_LABELS = {
    '01': 'One & Two Family Buildings',
    '02': 'Multi-Family Walk-Up Buildings',
    '03': 'Multi-Family Elevator Buildings',
    '04': 'Mixed Residential & Commercial Buildings',
    '05': 'Commercial & Office Buildings',
    '06': 'Industrial & Manufacturing',
    '07': 'Transportation & Utility',
    '08': 'Public Facilities & Institutions',
    '09': 'Open Space & Outdoor Recreation',
    '10': 'Parking Facilities',
    '11': 'Vacant Land'
  };
  var LAND_USE_COLORS = {
    '01': '#FEFFA8',
    '02': '#FCB842',
    '03': '#B16E00',
    '04': '#ff8341',
    '05': '#fc2929',
    '06': '#E362FB',
    '07': '#E0BEEB',
    '08': '#44A3D5',
    '09': '#78D271',
    '10': '#BAB8B6',
    '11': '#555555'
  };
  var BOROUGH_INFO = {
    bk: {digit: '3', short: 'BK', name: 'Brooklyn', page: 'brooklyn.html'},
    bx: {digit: '2', short: 'BX', name: 'Bronx', page: 'bronx.html'},
    mn: {digit: '1', short: 'MN', name: 'Manhattan', page: 'manhattan.html'},
    qn: {digit: '4', short: 'QN', name: 'Queens', page: 'queens.html'},
    si: {digit: '5', short: 'SI', name: 'Staten Island', page: 'statenisland.html'}
  };
  var FEATURE_SERVICE_URL = 'https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/MAPPLUTO/FeatureServer/0';
  var ESRI_LEAFLET_SRC = 'https://unpkg.com/esri-leaflet@3.0.14/dist/esri-leaflet.js';

  function normalizeLandUse(code){
    var normalized = String(code == null ? '' : code).replace(/\.0+$/, '');
    if (!normalized) return '';
    if (normalized.length === 1) normalized = '0' + normalized;
    return normalized;
  }
  function getLandUseLabel(code){
    var normalized = normalizeLandUse(code);
    if (!normalized) return 'Not available';
    return LAND_USE_LABELS[normalized] ? LAND_USE_LABELS[normalized] + ' (' + normalized + ')' : 'Land use code ' + normalized;
  }
  function getLandUseColor(code){
    var normalized = normalizeLandUse(code);
    return LAND_USE_COLORS[normalized] || '#9aa0a6';
  }
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
    if (document.getElementById('landuse-rollout-style')) return;
    var style = document.createElement('style');
    style.id = 'landuse-rollout-style';
    style.textContent = '' +
      '.map-wrap{background:#fff;border:1px solid #e5e2db;border-radius:14px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.05)}' +
      '.map-header{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;padding:18px 18px 12px;background:#fff;border-bottom:1px solid #e5e2db;flex-wrap:wrap}' +
      '.map-header h3{margin:0;font-size:1.02rem;color:#0d1b4b}' +
      '.map-header a{font-size:.8rem;font-weight:700;color:#f47920;text-decoration:none}' +
      '.zoning-stat-row{display:flex;flex-wrap:wrap;gap:16px;padding:14px 18px;background:#f8f7f4;border-bottom:1px solid #e5e2db}' +
      '.zoning-stat{display:flex;flex-direction:column;gap:2px}' +
      '.zoning-stat-label{font-size:.58rem;font-family:\'DM Mono\',monospace;text-transform:uppercase;letter-spacing:.08em;color:#6b6760}' +
      '.zoning-stat-value{font-size:.92rem;font-weight:700;color:#0d1b4b}' +
      '.leaflet-map{height:420px;width:100%;background:#eef2f4}' +
      '.zoning-legend{display:flex;flex-wrap:wrap;gap:8px 14px;padding:14px 18px 18px;background:#fff;border-top:1px solid #e5e2db}' +
      '.zoning-legend-item{display:inline-flex;align-items:center;gap:8px;font-size:.74rem;color:#0d1b4b}' +
      '.zoning-legend-swatch{width:12px;height:12px;border-radius:3px;display:inline-block;box-shadow:inset 0 0 0 1px rgba(0,0,0,.12)}' +
      '.landuse-inline-note{margin:10px 18px 0;font-size:.8rem;line-height:1.55;color:#6b6760}' +
      '.landuse-legend-grid{display:flex;flex-wrap:wrap;gap:8px 14px}' +
      '.landuse-map-shell{padding:0 18px 18px;background:#fff}' +
      '.landuse-map-note{padding:0 18px 16px;font-size:.78rem;line-height:1.6;color:#6b6760;background:#fff}' +
      '.landuse-result-popup{font-family:\'DM Sans\',sans-serif;line-height:1.45}' +
      '.landuse-result-popup strong{color:#0d1b4b}' +
      '.landuse-zoom-hint{font-size:.78rem;color:#6b6760;margin-top:8px}';
    document.head.appendChild(style);
  }
  function replaceLandUseGroupText(root){
    if (!root) return;
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    var node;
    while ((node = walker.nextNode())) {
      if (!node.nodeValue) continue;
      node.nodeValue = node.nodeValue
        .replace(/land use group/gi, function(match){ return match === match.toUpperCase() ? 'LAND USE CATEGORY' : 'land use category'; })
        .replace(/Land Use Group/g, 'Land Use Category')
        .replace(/zoning, and land use category/g, 'zoning and land use category');
    }
  }
  function observeForLabelPatches(){
    replaceLandUseGroupText(document.body);
    var observer = new MutationObserver(function(mutations){
      mutations.forEach(function(mutation){
        mutation.addedNodes && mutation.addedNodes.forEach(function(node){
          if (node && node.nodeType === 1) replaceLandUseGroupText(node);
          if (node && node.nodeType === 3 && node.parentNode) replaceLandUseGroupText(node.parentNode);
        });
      });
    });
    observer.observe(document.body, {childList: true, subtree: true, characterData: true});
  }
  function loadExternalScript(src){
    return new Promise(function(resolve, reject){
      var existing = document.querySelector('script[data-src="' + src + '"]');
      if (existing && existing.dataset.loaded === 'true') { resolve(); return; }
      if (existing) {
        existing.addEventListener('load', function(){ resolve(); }, {once:true});
        existing.addEventListener('error', function(){ reject(new Error('Failed to load ' + src)); }, {once:true});
        return;
      }
      var script = document.createElement('script');
      script.src = src;
      script.async = true;
      script.dataset.src = src;
      script.addEventListener('load', function(){ script.dataset.loaded = 'true'; resolve(); }, {once:true});
      script.addEventListener('error', function(){ reject(new Error('Failed to load ' + src)); }, {once:true});
      document.head.appendChild(script);
    });
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
        domPrefix: 'cb' + slug + district,
        boundaryLabel: BOROUGH_INFO[slug].short + ' CB' + district,
        title: BOROUGH_INFO[slug].name + ' Community Board ' + district,
        toggleIcon: '🏘',
        sectionTitle: 'Land Use Map',
        sectionHeading: 'Land Use — ' + BOROUGH_INFO[slug].short + ' CB' + district,
        dataLink: 'https://www.nyc.gov/content/planning/pages/resources/datasets/mappluto'
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
        domPrefix: boroughSlug + '-borough',
        boundaryLabel: BOROUGH_INFO[boroughSlug].name,
        title: BOROUGH_INFO[boroughSlug].name,
        toggleIcon: '🏘',
        sectionTitle: BOROUGH_INFO[boroughSlug].name + ' Land Use Map',
        sectionHeading: BOROUGH_INFO[boroughSlug].name + ' Land Use Categories',
        dataLink: 'https://www.nyc.gov/content/planning/pages/resources/datasets/mappluto'
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
      return String(feature.properties && feature.properties.boro_cd || '').charAt(0) === context.borough.digit;
    });
  }
  function makeSectionHtml(context){
    var wrapperClass = context.type === 'cb' ? 'drop-section' : 'boro-drop-section';
    var toggleClass = context.type === 'cb' ? 'drop-toggle' : 'boro-drop-toggle';
    var bodyClass = context.type === 'cb' ? 'drop-body' : 'boro-drop-body';
    var sectionId = context.type === 'cb' ? 'sec-landuse' : 'sec-landuse';
    return '' +
      '<div class="' + wrapperClass + '" id="' + sectionId + '">' +
        '<button class="' + toggleClass + '" type="button" id="' + context.domPrefix + '-landuse-toggle">' +
          context.toggleIcon + ' ' + context.sectionTitle +
          '<span class="' + (context.type === 'cb' ? 'drop-arr' : 'boro-drop-arr') + '">▼</span>' +
        '</button>' +
        '<div class="' + bodyClass + '">' +
          '<div class="map-wrap">' +
            '<div class="map-header">' +
              '<h3>' + context.sectionHeading + '</h3>' +
              '<a href="' + context.dataLink + '" target="_blank">NYC Planning data ↗</a>' +
            '</div>' +
            '<div class="zoning-stat-row">' +
              '<div class="zoning-stat"><span class="zoning-stat-label">Boundary</span><span class="zoning-stat-value">' + escapeHtml(context.boundaryLabel) + '</span></div>' +
              '<div class="zoning-stat"><span class="zoning-stat-label">Land Use Classes</span><span class="zoning-stat-value">11</span></div>' +
              '<div class="zoning-stat"><span class="zoning-stat-label">Parcel Detail</span><span class="zoning-stat-value">Zoom in</span></div>' +
            '</div>' +
            '<p class="landuse-inline-note">This map colors tax lots by the official PLUTO land-use category. Zoom in to street level to inspect individual lots and click any parcel for its category label.</p>' +
            '<div class="landuse-map-shell zoning-map-shell">' +
              '<div id="' + context.domPrefix + '-landuse-map" class="leaflet-map" aria-label="Leaflet land use map for ' + escapeHtml(context.title) + '"></div>' +
            '</div>' +
            '<div class="landuse-map-note zoning-map-note" id="' + context.domPrefix + '-landuse-note">Loading land-use categories and boundary geometry…</div>' +
            '<div class="zoning-legend landuse-legend-grid">' +
              '<span class="zoning-legend-item"><span class="zoning-legend-swatch" style="background:#FEFFA8"></span>One &amp; Two Family</span>' +
              '<span class="zoning-legend-item"><span class="zoning-legend-swatch" style="background:#FCB842"></span>Walk-Up Multi-Family</span>' +
              '<span class="zoning-legend-item"><span class="zoning-legend-swatch" style="background:#B16E00"></span>Elevator Multi-Family</span>' +
              '<span class="zoning-legend-item"><span class="zoning-legend-swatch" style="background:#ff8341"></span>Mixed Residential / Commercial</span>' +
              '<span class="zoning-legend-item"><span class="zoning-legend-swatch" style="background:#fc2929"></span>Commercial / Office</span>' +
              '<span class="zoning-legend-item"><span class="zoning-legend-swatch" style="background:#E362FB"></span>Industrial / Manufacturing</span>' +
              '<span class="zoning-legend-item"><span class="zoning-legend-swatch" style="background:#E0BEEB"></span>Transportation / Utility</span>' +
              '<span class="zoning-legend-item"><span class="zoning-legend-swatch" style="background:#44A3D5"></span>Public Facilities</span>' +
              '<span class="zoning-legend-item"><span class="zoning-legend-swatch" style="background:#78D271"></span>Open Space</span>' +
              '<span class="zoning-legend-item"><span class="zoning-legend-swatch" style="background:#BAB8B6"></span>Parking</span>' +
              '<span class="zoning-legend-item"><span class="zoning-legend-swatch" style="background:#555555"></span>Vacant Land</span>' +
              '<span class="zoning-legend-item"><span class="zoning-legend-swatch" style="background:#0d1b4b"></span>' + escapeHtml(context.boundaryLabel) + ' outline</span>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</div>';
  }
  function insertTocLink(context){
    if (document.querySelector('a[href="#sec-landuse"]')) return;
    var zoningLink = document.querySelector('a[href="#sec-zoning"]');
    if (!zoningLink) return;
    var anchor = document.createElement('a');
    anchor.href = '#sec-landuse';
    anchor.innerHTML = (context.type === 'cb'
      ? '🏘 Land Use Map<span class="toc-entry-sub">Tax lots by PLUTO category</span>'
      : '🏘 Land Use Map<span class="toc-entry-sub">Tax lots by PLUTO category</span>');
    zoningLink.insertAdjacentElement('afterend', anchor);
  }
  function insertSection(context){
    if (document.getElementById(context.domPrefix + '-landuse-map')) return;
    var zoningSection = document.getElementById('sec-zoning');
    if (!zoningSection) return;
    zoningSection.insertAdjacentHTML('afterend', makeSectionHtml(context));
    insertTocLink(context);
  }
  function attachToggle(context){
    var btn = document.getElementById(context.domPrefix + '-landuse-toggle');
    if (!btn || btn.dataset.bound === 'true') return;
    btn.dataset.bound = 'true';
    btn.addEventListener('click', function(){
      var body = btn.nextElementSibling;
      if (!body) return;
      var open = body.classList.toggle('open');
      btn.classList.toggle('open', open);
      if (open) {
        setTimeout(function(){ initializeLandUseMap(context); }, 180);
      }
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
  async function initializeLandUseMap(context){
    if (context.mapInitialized || context.mapLoading) return;
    var mapId = context.domPrefix + '-landuse-map';
    var mapEl = document.getElementById(mapId);
    var noteEl = document.getElementById(context.domPrefix + '-landuse-note');
    if (!mapEl || typeof L === 'undefined') return;
    context.mapLoading = true;
    try {
      await loadExternalScript(ESRI_LEAFLET_SRC);
      if (!L.esri || !L.esri.featureLayer) throw new Error('Esri Leaflet plugin unavailable');
      var boundaryData = await fetchJson('nyc_cb_boundaries.geojson');
      var boundaryFeatures = getTargetBoundaryFeatures(boundaryData, context);
      if (!boundaryFeatures.length) throw new Error('Boundary not found');
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
      var minParcelZoom = context.type === 'cb' ? 14 : 15;
      var communityDistrictCode = parseInt(String(context.borough.digit) + String(context.district).padStart(2, '0'), 10);
      var whereClause = context.type === 'cb'
        ? 'BoroCode = ' + parseInt(context.borough.digit, 10) + ' AND CD = ' + communityDistrictCode
        : 'BoroCode = ' + parseInt(context.borough.digit, 10);
      var parcelLayer = L.esri.featureLayer({
        url: FEATURE_SERVICE_URL,
        where: whereClause,
        precision: 5,
        simplifyFactor: 0.35,
        fields: ['Address', 'LandUse', 'BBL', 'BoroCode', 'CD'],
        style: function(feature){
          var code = normalizeLandUse(feature && feature.properties && feature.properties.LandUse);
          return {
            color: '#ffffff',
            weight: 0.35,
            opacity: 0.8,
            fillColor: getLandUseColor(code),
            fillOpacity: 0.72
          };
        },
        onEachFeature: function(feature, layer){
          var props = (feature && feature.properties) || {};
          var address = props.Address || 'Tax lot';
          var bbl = props.BBL ? '<br><span style="font-size:.8rem;color:#6b6760">BBL ' + escapeHtml(props.BBL) + '</span>' : '';
          var popupHtml = '<div class="landuse-result-popup"><strong>' + escapeHtml(address) + '</strong><br>' + escapeHtml(getLandUseLabel(props.LandUse)) + bbl + '</div>';
          layer.bindPopup(popupHtml, {maxWidth: 260});
        }
      });
      function syncParcelLayer(){
        if (map.getZoom() >= minParcelZoom) {
          if (!map.hasLayer(parcelLayer)) parcelLayer.addTo(map);
          if (noteEl) noteEl.textContent = 'Parcel land-use colors are active. Click any visible lot for its category label.';
        } else {
          if (map.hasLayer(parcelLayer)) map.removeLayer(parcelLayer);
          if (noteEl) noteEl.textContent = 'Zoom in further to load parcel-level land-use polygons from live MapPLUTO service.';
        }
      }
      map.on('zoomend', syncParcelLayer);
      context.map = map;
      context.parcelLayer = parcelLayer;
      context.boundaryLayer = boundaryLayer;
      context.bounds = boundaryLayer.getBounds();
      if (context.bounds && context.bounds.isValid()) {
        map.fitBounds(context.bounds, {padding:[18,18]});
      }
      setTimeout(function(){
        map.invalidateSize();
        if (context.bounds && context.bounds.isValid()) map.fitBounds(context.bounds, {padding:[18,18]});
      }, 250);
      syncParcelLayer();
      context.mapInitialized = true;
    } catch (err) {
      console.error(err);
      if (noteEl) noteEl.textContent = 'The land-use map could not be loaded right now. Please try refreshing the page.';
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
    observeForLabelPatches();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, {once:true});
  } else {
    init();
  }
})();
