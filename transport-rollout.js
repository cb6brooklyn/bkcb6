(function(){
  var path = (location.pathname || '').split('/').pop() || 'index.html';
  if (!/^(cb-[a-z]{2}-\d+|brooklyn|bronx|manhattan|queens|staten-island|statenisland)\.html$/.test(path)) return;
  var isBorough = !/^cb-/.test(path);
  var classes = {
    section: isBorough ? 'boro-drop-section' : 'drop-section',
    toggle: isBorough ? 'boro-drop-toggle' : 'drop-toggle',
    body: isBorough ? 'boro-drop-body' : 'drop-body',
    tocBody: isBorough ? 'boro-toc-body' : 'cb-toc-body',
    tocSub: isBorough ? 'boro-toc-entry-sub' : 'toc-sub'
  };
  var configs = [
    {key:'bike', icon:'🚲', title:'Bike Map', source:'https://www.nyc.gov/html/dot/html/bicyclists/bikemaps.shtml', note:'Bike routes clipped to the current boundary.', id:'sec-bike-map'},
    {key:'subway', icon:'🚇', title:'Subway Map', source:'https://data.ny.gov/Transportation/MTA-Subway-Stations/39hk-dx4f', note:'Subway stations within the current boundary.', id:'sec-subway-map'},
    {key:'truck', icon:'🚚', title:'Truck Route Map', source:'https://www.nyc.gov/html/dot/html/motorist/trucks.shtml', note:'Official truck route segments clipped to the current boundary.', id:'sec-truck-map'},
    {key:'speed', icon:'🛣', title:'Speed Limit Map', source:'https://data.cityofnewyork.us/Transportation/VZV-Speed-Limits/qtik-bcvk', note:'Posted speed-limit segments clipped to the current boundary.', id:'sec-speed-map'}
  ];
  var state = {dataPromise:null,maps:{}};

  function ensureStyles(){
    if (document.getElementById('transport-rollout-inline-styles')) return;
    var style = document.createElement('style');
    style.id = 'transport-rollout-inline-styles';
    style.textContent = ''+
      '.leaflet-map{width:100%;height:640px;background:#eef3f8;}' +
      '.zoning-map-shell{padding:0 18px 18px;background:#fff;}' +
      '.zoning-map-note{padding:0 18px 16px;font-size:.78rem;line-height:1.6;color:#6b6760;background:#fff;}' +
      '@media(max-width:600px){.leaflet-map{height:440px;}}';
    document.head.appendChild(style);
  }

  function inject(){
    ensureStyles();
    if (document.querySelector('[data-transport-rollout="true"]')) return;
    var anchor = document.getElementById('sec-parks') || document.getElementById('sec-landuse') || document.getElementById('sec-zoning');
    if (!anchor) return;
    var html = configs.map(function(cfg){ return buildSection(cfg); }).join('\n');
    var wrapper = document.createElement('div');
    wrapper.setAttribute('data-transport-rollout','true');
    wrapper.innerHTML = html;
    anchor.insertAdjacentElement('afterend', wrapper);
    wrapper.querySelectorAll('[data-transport-toggle]').forEach(function(btn){
      btn.addEventListener('click', function(){ toggleSection(btn); });
    });
    injectToc();
  }

  function buildSection(cfg){
    var pageLabel = isBorough ? document.title.replace(/\s*\|.*$/,'').trim() : document.title.replace(/\s*\|.*$/,'').trim();
    return ''+
      '<div class="'+classes.section+'" id="'+cfg.id+'">'+
        '<button class="'+classes.toggle+'" type="button" data-transport-toggle="'+cfg.key+'">'+
          cfg.icon+' '+pageLabel+' '+cfg.title+
          '<span class="'+(isBorough ? 'boro-drop-arr' : 'drop-arr')+'">▼</span>'+
        '</button>'+
        '<div class="'+classes.body+'">'+
          '<div class="map-wrap">'+
            '<div class="map-header"><h3>'+pageLabel+' '+cfg.title+'</h3><a href="'+cfg.source+'" target="_blank">Source ↗</a></div>'+
            '<div class="zoning-stat-row" id="transport-'+cfg.key+'-stats"></div>'+
            '<div style="padding:0 18px 12px;font-size:.82rem;color:#6b6760;line-height:1.6">'+cfg.note+'</div>'+
            '<div class="zoning-map-shell"><div id="transport-'+cfg.key+'-map" class="leaflet-map" aria-label="'+pageLabel+' '+cfg.title+'"></div></div>'+
            '<div class="zoning-map-note" id="transport-'+cfg.key+'-note">Open this section to load the map.</div>'+
            '<div class="zoning-legend" id="transport-'+cfg.key+'-legend"></div>'+
          '</div>'+
        '</div>'+
      '</div>';
  }

  function injectToc(){
    var toc = document.getElementById(classes.tocBody);
    if (!toc) return;
    configs.forEach(function(cfg){
      if (toc.querySelector('a[href="#'+cfg.id+'"]')) return;
      var a = document.createElement('a');
      a.href = '#'+cfg.id;
      a.innerHTML = cfg.icon+' '+(isBorough ? document.title.replace(/\s*\|.*$/,'').trim()+' ' : '')+cfg.title+'<span class="'+classes.tocSub+'">Interactive '+cfg.title.toLowerCase()+' for this boundary</span>';
      toc.insertBefore(a, toc.firstChild ? toc.firstChild.nextSibling : null);
    });
  }

  function toggleSection(btn){
    var body = btn.nextElementSibling;
    var open = btn.classList.contains('open');
    btn.classList.toggle('open', !open);
    body.classList.toggle('open', !open);
    if (!open){ initMap(btn.getAttribute('data-transport-toggle')); }
  }

  function getData(){
    if (!state.dataPromise){
      state.dataPromise = fetch('transport-data/' + path.replace(/\.html$/, '.json')).then(function(resp){
        if (!resp.ok) throw new Error('Failed to load transport data');
        return resp.json();
      });
    }
    return state.dataPromise;
  }

  function buildStats(container, summary){
    container.innerHTML = '';
    (summary || []).forEach(function(item){
      var div = document.createElement('div');
      div.className = 'zoning-stat';
      div.innerHTML = '<span class="zoning-stat-label">'+escapeHtml(item.label || '')+'</span><span class="zoning-stat-value">'+escapeHtml(item.value || '')+'</span>';
      container.appendChild(div);
    });
  }

  function setLegend(kind){
    var legend = document.getElementById('transport-'+kind+'-legend');
    if (!legend) return;
    var items = {
      bike:[['#1d4ed8','Protected'],['#0f766e','Greenway'],['#f59e0b','Buffered / Conventional'],['#6b7280','Shared / Link'],['#ef4444','Retired']],
      subway:[['#0d1b4b','Subway Station'],['#f47920','ADA Accessible']],
      truck:[['#0d9488','Through'],['#2563eb','Local'],['#f59e0b','Limited Local']],
      speed:[['#2a9d8f','20 mph or less'],['#4c78a8','25 mph'],['#f4a261','30 mph'],['#e63946','35+ mph'],['#111827','School Zone']]
    }[kind] || [];
    legend.innerHTML = items.map(function(item){ return '<span class="zoning-legend-item"><span class="zoning-legend-swatch" style="background:'+item[0]+'"></span>'+item[1]+'</span>'; }).join('');
  }

  function escapeHtml(value){
    return String(value == null ? '' : value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  }

  function bikeColor(props){
    var text = [props.ft_facilit, props.tf_facilit, props.facilitycl, props.allclasses, props.grnwy, props.status].join(' ').toLowerCase();
    if (text.indexOf('retired') !== -1) return '#ef4444';
    if (text.indexOf('greenway') !== -1) return '#0f766e';
    if (text.indexOf('protected') !== -1) return '#1d4ed8';
    if (text.indexOf('buffered') !== -1 || text.indexOf('conventional') !== -1) return '#f59e0b';
    return '#6b7280';
  }

  function truckColor(props){
    var t = String(props.routetype || '').toLowerCase();
    if (t === 'through') return '#0d9488';
    if (t === 'local') return '#2563eb';
    return '#f59e0b';
  }

  function speedColor(props){
    var sl = parseInt(props.postvz_sl || '0', 10) || 0;
    if (sl <= 20 && sl > 0) return '#2a9d8f';
    if (sl <= 25) return '#4c78a8';
    if (sl <= 30) return '#f4a261';
    return '#e63946';
  }

  function subwayColor(props){
    var ada = String(props.ada || '').toLowerCase();
    return (ada === 'true' || ada === 'yes' || ada === '1') ? '#f47920' : '#0d1b4b';
  }

  function linePopup(kind, props){
    if (kind === 'bike') return '<strong>'+escapeHtml(props.street || 'Bike Route')+'</strong><br>'+escapeHtml([props.fromstreet, props.tostreet].filter(Boolean).join(' to '))+'<br><span style="font-size:.8rem;color:#666">'+escapeHtml([props.status, props.ft_facilit || props.tf_facilit || props.allclasses, props.grnwy].filter(Boolean).join(' · '))+'</span>';
    if (kind === 'truck') return '<strong>'+escapeHtml(props.street || 'Truck Route')+'</strong><br><span style="font-size:.8rem;color:#666">'+escapeHtml([props.routetype, props.nyc_reg].filter(Boolean).join(' · '))+'</span>';
    return '<strong>'+escapeHtml(props.street || 'Speed Limit Segment')+'</strong><br><span style="font-size:.8rem;color:#666">Posted: '+escapeHtml(props.postvz_sl || '—')+' mph'+(String(props.postvz_sg || '').toUpperCase()==='YES' ? ' · School Zone' : '')+'</span>';
  }

  function initMap(kind){
    if (state.maps[kind]) { state.maps[kind].invalidateSize(); return; }
    var mapEl = document.getElementById('transport-'+kind+'-map');
    var noteEl = document.getElementById('transport-'+kind+'-note');
    var statsEl = document.getElementById('transport-'+kind+'-stats');
    if (!mapEl || typeof L === 'undefined') return;
    noteEl.textContent = 'Loading map data…';
    getData().then(function(data){
      var section = data[kind];
      var boundary = data.boundary;
      var map = L.map(mapEl, {scrollWheelZoom:false});
      state.maps[kind] = map;
      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{attribution:'© OpenStreetMap © CARTO',maxZoom:19}).addTo(map);
      var boundaryLayer = L.geoJSON(boundary,{style:function(){return {color:'#0d1b4b',weight:2,fill:false,opacity:0.95};}}).addTo(map);
      if (kind === 'subway'){
        var layer = L.geoJSON(section,{pointToLayer:function(feature, latlng){return L.circleMarker(latlng,{radius:6,color:'#ffffff',weight:1,fillColor:subwayColor(feature.properties || {}),fillOpacity:0.95});},onEachFeature:function(feature, layer){var p = feature.properties || {};layer.bindPopup('<strong>'+escapeHtml(p.stop_name || 'Station')+'</strong><br><span style="font-size:.8rem;color:#666">'+escapeHtml([p.line, p.daytime_routes, p.structure].filter(Boolean).join(' · '))+'</span>');}}).addTo(map);
        if (layer.getBounds && layer.getBounds().isValid()) map.fitBounds(layer.getBounds().pad(0.12));
        else if (boundaryLayer.getBounds().isValid()) map.fitBounds(boundaryLayer.getBounds().pad(0.08));
      } else {
        var styleFn = kind === 'bike' ? function(f){return {color:bikeColor(f.properties || {}),weight:4,opacity:0.9};} : kind === 'truck' ? function(f){return {color:truckColor(f.properties || {}),weight:4,opacity:0.9};} : function(f){return {color:speedColor(f.properties || {}),weight:String((f.properties || {}).postvz_sg || '').toUpperCase()==='YES' ? 5 : 4,opacity:0.9,dashArray:String((f.properties || {}).postvz_sg || '').toUpperCase()==='YES' ? '8 4' : null};};
        var layer = L.geoJSON(section,{style:styleFn,onEachFeature:function(feature, layer){layer.bindPopup(linePopup(kind, feature.properties || {}));}}).addTo(map);
        if (layer.getBounds && layer.getBounds().isValid()) map.fitBounds(layer.getBounds().pad(0.12));
        else if (boundaryLayer.getBounds().isValid()) map.fitBounds(boundaryLayer.getBounds().pad(0.08));
      }
      buildStats(statsEl, section.summary || []);
      setLegend(kind);
      noteEl.textContent = ((section.features || []).length ? (section.features || []).length + ' mapped features loaded.' : 'No mapped features fell inside this boundary.');
      setTimeout(function(){ map.invalidateSize(); }, 120);
    }).catch(function(err){
      noteEl.textContent = 'Could not load this map.';
      console.error(err);
    });
  }

  inject();
})();
