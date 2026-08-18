/* Map and filtering for the zoning collection pages.
 *
 * Each page hands this a list of places. It draws a pin per place using that
 * place's own tile as the marker, and filters both the map and the tile grid
 * together, so what you see on the map is what you see in the list.
 *
 * Starts on a featured set. Borough buttons add a borough, "All" adds the rest,
 * and the search box filters everything by name or address.
 */
(function () {
  'use strict';

  var map = null, layer = null, PLACES = [], TILE_PREFIX = '', state = {
    mode: 'featured',      // 'featured' | 'all' | a borough name
    query: ''
  };

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c];
    });
  }

  function visible() {
    var q = state.query.trim().toLowerCase();
    return PLACES.filter(function (p) {
      if (q) {
        // a search looks through everything, not just the current slice
        var hay = [p.name, p.addr, p.zoning || '', p.board || '',
                   (p.sports || []).join(' '), (p.teams || []).join(' '),
                   p.kind || ''].join(' ');
        return hay.toLowerCase().indexOf(q) !== -1;
      }
      if (state.mode === 'all') return true;
      if (state.mode === 'featured') return !!p.featured;
      // a mode can be a borough, a sport or a team
      if (p.boro === state.mode) return true;
      if (p.sports && p.sports.indexOf(state.mode) !== -1) return true;
      if (p.teams && p.teams.indexOf(state.mode) !== -1) return true;
      if (p.show && p.show === state.mode) return true;
      return false;
    });
  }

  function drawMap(list) {
    if (!map) return;
    if (layer) map.removeLayer(layer);
    layer = L.layerGroup();
    var pts = [];
    list.forEach(function (p) {
      if (p.lat == null || p.lng == null) return;
      pts.push([p.lat, p.lng]);
      // A glyph pin says what the place is at a glance, ringed in the colours
      // of whoever plays there. Two teams gets a two-colour ring.
      var inner = p.icon
        ? '<span class="zg">' + p.icon + '</span>'
        : '<img src="/tiles/' + TILE_PREFIX + p.slug + '.png" alt="">';
      var ring = '';
      if (p.colors && p.colors.length > 1) {
        ring = 'background:conic-gradient(' + p.colors[0][0] + ' 0 50%,' +
               p.colors[1][0] + ' 50% 100%);';
      } else if (p.color) {
        ring = 'background:' + p.color + ';';
      }
      var icon = L.divIcon({
        className: '',
        html: '<a class="zpin' + (p.icon ? ' glyph' : '') + '" href="/' + TILE_PREFIX + p.slug +
              '" title="' + esc(p.name) + '" style="' + ring + '">' +
              '<span class="zin">' + inner + '</span></a>',
        iconSize: [40, 40], iconAnchor: [20, 20]
      });
      L.marker([p.lat, p.lng], { icon: icon })
        .bindPopup('<div class="zpop"><h4>' + esc(p.name) + '</h4>' +
          '<div class="sub">' + esc(p.addr) + '</div>' +
          '<div class="sub"><b>' + esc(p.board || '') + '</b></div>' +
          '<div class="sub">Zoned ' + esc(p.zoning || '') + '</div>' +
          ((p.teams && p.teams.length) ? '<div class="sub">' + esc(p.teams.join(' \u00b7 ')) + '</div>' : '') +
          (p.kind ? '<div class="sub">' + esc(p.kind) + '</div>' : '') +
          '<a class="go" href="/' + TILE_PREFIX + p.slug + '">Open the full card &rarr;</a></div>')
        .addTo(layer);
    });
    layer.addTo(map);
    if (pts.length) {
      map.fitBounds(L.latLngBounds(pts), { padding: [40, 40], maxZoom: 15 });
    }
  }

  function drawGrid(list) {
    var shown = {};
    list.forEach(function (p) { shown[p.slug] = true; });
    var n = 0;
    document.querySelectorAll('.cell').forEach(function (c) {
      var a = c.querySelector('a.tile');
      if (!a) return;
      var slug = a.getAttribute('href').replace('/', '');
      var on = !!shown[slug];
      c.style.display = on ? '' : 'none';
      if (on) n++;
    });
    // a section with nothing left in it should not leave a stray heading
    document.querySelectorAll('.grid').forEach(function (g) {
      var any = Array.prototype.some.call(g.querySelectorAll('.cell'), function (c) {
        return c.style.display !== 'none';
      });
      g.style.display = any ? '' : 'none';
      var sect = g.previousElementSibling;
      if (sect && sect.classList.contains('sect')) sect.style.display = any ? '' : 'none';
    });
    var count = document.getElementById('zcount');
    if (count) {
      count.textContent = n + (n === 1 ? ' place' : ' places') +
        (state.query ? ' matching "' + state.query + '"' : '');
    }
  }

  function refresh() {
    var list = visible();
    drawMap(list);
    drawGrid(list);
    var selEl = document.getElementById('zselect');
    if (selEl && !state.query && selEl.value !== state.mode) selEl.value = state.mode;
    document.querySelectorAll('.zbtn').forEach(function (b) {
      var on = !state.query && b.dataset.mode === state.mode;
      b.classList.toggle('on', on);
      if (b.dataset.color) {
        b.style.background = on ? b.dataset.color : '#fff';
        b.style.color = on ? '#fff' : b.dataset.color;
      }
    });
  }


  // The same zoning layer the address cards draw: districts from DCP's nyzd
  // service, coloured by family, on the palette the cards already use.
  var ZONE_FILL = {
    'Residential': '#56B4E9', 'Commercial': '#E69F00', 'Manufacturing': '#D55E00',
    'Mixed Use': '#CC79A7', 'Park/Open Space': '#009E73', 'Other': '#999999'
  };
  function zoneFamily(z) {
    z = String(z || '').trim().toUpperCase();
    if (z.indexOf('/') > -1) return 'Mixed Use';
    if (z === 'PARK') return 'Park/Open Space';
    if (/^R/.test(z)) return 'Residential';
    if (/^C/.test(z)) return 'Commercial';
    if (/^M/.test(z)) return 'Manufacturing';
    return 'Other';
  }
  var zoneLayer = null, zoneShown = {};
  function loadZoning() {
    if (!map) return;
    var b = map.getBounds();
    if (map.getZoom() < 12) {                 // too far out to be readable
      if (zoneLayer) { map.removeLayer(zoneLayer); zoneLayer = null; }
      drawLegend({});
      return;
    }
    var env = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].join(',');
    var url = 'https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/nyzd/' +
      'FeatureServer/0/query?where=1%3D1&outFields=ZONEDIST&returnGeometry=true&f=geojson' +
      '&outSR=4326&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects' +
      '&geometry=' + encodeURIComponent(env) + '&resultRecordCount=1200';
    fetch(url).then(function (r) { return r.json(); }).then(function (d) {
      if (!d || !d.features) return;
      if (zoneLayer) map.removeLayer(zoneLayer);
      var fams = {};
      zoneLayer = L.geoJSON(d, {
        style: function (f) {
          var z = (f.properties || {}).ZONEDIST || '';
          var fam = zoneFamily(z);
          fams[fam] = ZONE_FILL[fam];
          return { color: '#374151', weight: 1, opacity: .55,
                   fillColor: ZONE_FILL[fam], fillOpacity: .42 };
        },
        onEachFeature: function (f, l) {
          var z = (f.properties || {}).ZONEDIST || '';
          if (z) l.bindTooltip(z, { sticky: true });
        }
      });
      zoneLayer.addTo(map);
      if (zoneLayer.bringToBack) zoneLayer.bringToBack();
      drawLegend(fams);
    }).catch(function () {});
  }
  function drawLegend(fams) {
    var el = document.getElementById('zlegend');
    if (!el) return;
    var keys = Object.keys(fams);
    if (!keys.length) { el.innerHTML = '<span class="zmuted">Zoom in to shade the zoning districts</span>'; return; }
    el.innerHTML = '<b>Zoning</b>' + keys.sort().map(function (k) {
      return '<span class="zk"><i style="background:' + fams[k] + '"></i>' + k + '</span>';
    }).join('');
  }

  window.initZoningMap = function (opts) {
    PLACES = opts.places || [];
    TILE_PREFIX = opts.prefix || '';
    var el = document.getElementById('zmap');
    if (el && window.L) {
      map = L.map('zmap', { scrollWheelZoom: false });
      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO &middot; zoning from NYC DCP', maxZoom: 19
      }).addTo(map);
      map.on('moveend', loadZoning);
      map.whenReady(function () { setTimeout(loadZoning, 400); });
    }
    // each team pill wears that team's colours
    document.querySelectorAll('.zbtn[data-color]').forEach(function (b) {
      var c = b.dataset.color, c2 = b.dataset.color2 || '#fff';
      b.style.borderColor = c;
      b.style.color = c;
      b.style.boxShadow = 'inset 0 -3px 0 ' + c2;
    });
    document.querySelectorAll('.zbtn').forEach(function (b) {
      b.addEventListener('click', function () {
        state.mode = b.dataset.mode;
        state.query = '';
        var sel = document.getElementById('zselect');
    if (sel) {
      sel.addEventListener('change', function () {
        state.mode = sel.value;
        state.query = '';
        var box = document.getElementById('zsearch');
        if (box) box.value = '';
        refresh();
      });
    }
    var s = document.getElementById('zsearch');
        if (s) s.value = '';
        refresh();
      });
    });
    var sel = document.getElementById('zselect');
    if (sel) {
      sel.addEventListener('change', function () {
        state.mode = sel.value;
        state.query = '';
        var box = document.getElementById('zsearch');
        if (box) box.value = '';
        refresh();
      });
    }
    var s = document.getElementById('zsearch');
    if (s) {
      s.addEventListener('input', function () { state.query = s.value; refresh(); });
    }
    refresh();
  };
})();
