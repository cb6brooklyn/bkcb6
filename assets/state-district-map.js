/* state-district-map.js: the district map on a State Senate or Assembly profile outside the city.
   <div data-state-map data-chamber="assembly|senate" data-district="103" data-name="Assembly Member ..."></div>
   with an address box ([data-state-search] input + button), a reset button ([data-state-reset]) and a status line
   ([data-state-status]) beside it. Draws the district from /data/districts/<chamber>-<n>.geojson on the same base map
   as every other profile map, and drops a pin for an address or a tap, saying whether that spot is in the district. */
(function () {
  function ringIn(x, y, r) { var c = false; for (var i = 0, j = r.length - 1; i < r.length; j = i++) { var xi = r[i][0], yi = r[i][1], xj = r[j][0], yj = r[j][1]; if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) c = !c; } return c; }
  function polyIn(x, y, p) { if (!ringIn(x, y, p[0])) return false; for (var i = 1; i < p.length; i++) if (ringIn(x, y, p[i])) return false; return true; }
  function inside(gj, lat, lng) {
    return (gj.features || []).some(function (f) {
      var g = f.geometry; if (!g) return false;
      if (g.type === 'Polygon') return polyIn(lng, lat, g.coordinates);
      if (g.type === 'MultiPolygon') return g.coordinates.some(function (p) { return polyIn(lng, lat, p); });
      return false;
    });
  }
  function init(el) {
    if (!window.L || el.dataset.ready) return; el.dataset.ready = '1';
    var chamber = el.getAttribute('data-chamber'), n = el.getAttribute('data-district');
    var label = (chamber === 'senate' ? 'Senate District ' : 'Assembly District ') + n;
    var box = el.parentNode;
    var status = box.querySelector('[data-state-status]');
    function say(t) { if (status) status.textContent = t || ''; }
    var map = L.map(el, { scrollWheelZoom: false, zoomControl: true });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e', {
      maxZoom: 19, maxNativeZoom: 18, attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    }).addTo(map);
    map.setView([42.9, -75.5], 6);
    var gj = null, bounds = null, pin = null;
    function home() { if (bounds) map.fitBounds(bounds, { padding: [16, 16] }); }
    function drop(lat, lng, what) {
      if (pin) { map.removeLayer(pin); pin = null; }
      pin = L.marker([lat, lng]).addTo(map);
      var inn = gj ? inside(gj, lat, lng) : null;
      say((what ? what + ': ' : 'That spot is ') + (inn === null ? '' : inn ? 'inside ' + label + '.' : 'outside ' + label + '.'));
      if (inn === false && bounds) {
        try { map.fitBounds(L.latLngBounds([bounds.getSouthWest(), bounds.getNorthEast(), L.latLng(lat, lng)]), { padding: [24, 24] }); }
        catch (e) { map.setView([lat, lng], 10); }
      } else if (what) map.setView([lat, lng], 13);
    }
    fetch('/data/districts/' + chamber + '-' + n + '.geojson').then(function (r) { return r.json(); }).then(function (d) {
      gj = d;
      var lyr = L.geoJSON(d, { style: { color: '#0d1b4b', weight: 3, fillColor: '#f47920', fillOpacity: 0.16 } }).addTo(map);
      bounds = lyr.getBounds(); home(); say('');
    }).catch(function () { say('The district map did not load.'); });
    if (map.on) map.on('click', function (e) { if (e && e.latlng) drop(e.latlng.lat, e.latlng.lng); });
    var input = box.querySelector('[data-state-search] input'), btn = box.querySelector('[data-state-search] button');
    function find() {
      var q = (input && input.value || '').trim(); if (!q) return;
      say('Looking up ' + q + '…');
      fetch('https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=us&viewbox=-79.8,45.1,-71.8,40.4&bounded=1&q=' + encodeURIComponent(q))
        .then(function (r) { return r.json(); })
        .then(function (a) { if (!a || !a.length) { say('No match in New York State for ' + q + '.'); return; } drop(+a[0].lat, +a[0].lon, a[0].display_name.split(',').slice(0, 3).join(',')); })
        .catch(function () { say('The address lookup did not answer. Try again.'); });
    }
    if (btn) btn.addEventListener('click', find);
    if (input) input.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); find(); } });
    var reset = box.querySelector('[data-state-reset]');
    if (reset) reset.addEventListener('click', function () { if (pin) { map.removeLayer(pin); pin = null; } if (input) input.value = ''; say(''); home(); });
  }
  function all() { Array.prototype.forEach.call(document.querySelectorAll('[data-state-map]'), init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', all); else all();
})();
