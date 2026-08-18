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
    document.querySelectorAll('.zbtn').forEach(function (b) {
      var on = !state.query && b.dataset.mode === state.mode;
      b.classList.toggle('on', on);
      if (b.dataset.color) {
        b.style.background = on ? b.dataset.color : '#fff';
        b.style.color = on ? '#fff' : b.dataset.color;
      }
    });
  }

  window.initZoningMap = function (opts) {
    PLACES = opts.places || [];
    TILE_PREFIX = opts.prefix || '';
    var el = document.getElementById('zmap');
    if (el && window.L) {
      map = L.map('zmap', { scrollWheelZoom: false });
      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO', maxZoom: 19
      }).addTo(map);
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
        var s = document.getElementById('zsearch');
        if (s) s.value = '';
        refresh();
      });
    });
    var s = document.getElementById('zsearch');
    if (s) {
      s.addEventListener('input', function () { state.query = s.value; refresh(); });
    }
    refresh();
  };
})();
