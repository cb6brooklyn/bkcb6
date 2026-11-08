/* Shared labels for every district map on the site: neighborhood names for
   a frame of reference, the district's own name, and the borough.
   window.MapLabels.add(map, { bounds, district, districtLatLng, boroughs })
   bounds: Leaflet bounds of the district; neighborhoods within a padded copy
   are labeled. district: text for the district label, placed at districtLatLng
   (or the bounds' center). boroughs: array of borough names to label. */
(function () {
  var BORO = { Brooklyn: [40.6543, -73.94865], Manhattan: [40.78799, -73.96068], Queens: [40.7043, -73.86526], Bronx: [40.85598, -73.86638], 'Staten Island': [40.57251, -74.15483] };
  var data = null, pending = null;
  function css() {
    if (document.getElementById('maplbl-css')) return;
    var s = document.createElement('style'); s.id = 'maplbl-css';
    s.textContent = '.maplbl{background:none;border:0;box-shadow:none;white-space:nowrap;pointer-events:none;text-align:center;line-height:1.1}' +
      '.maplbl.nb{font-family:"DM Sans",sans-serif;font-weight:800;font-size:.7rem;color:#374151;text-shadow:0 0 3px #fff,0 0 3px #fff,0 0 5px #fff,0 0 8px #fff;letter-spacing:.01em}' +
      '.maplbl.dist{font-family:"DM Sans",sans-serif;font-weight:900;font-size:.86rem;color:#fff;background:#0d1b4b;padding:3px 9px;border-radius:999px;box-shadow:0 1px 4px rgba(0,0,0,.35);letter-spacing:.02em}' +
      '.maplbl.lblhide{visibility:hidden}' +
      '.maplbl.boro{font-family:"DM Mono",monospace;font-weight:700;font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:#6b7280;text-shadow:0 0 3px #fff,0 0 5px #fff,0 0 8px #fff}';
    document.head.appendChild(s);
  }
  function load() {
    if (data) return Promise.resolve(data);
    if (!pending) pending = fetch('/data/neighborhood-labels.json').then(function (r) { return r.json(); }).then(function (d) { data = d; return d; }).catch(function () { return []; });
    return pending;
  }
  function esc(v) { return String(v == null ? '' : v).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function mk(latlng, cls, html, z) {
    return L.marker(latlng, { icon: L.divIcon({ className: 'maplbl ' + cls, html: esc(html), iconSize: null }), interactive: false, zIndexOffset: z || 0 });
  }
  function add(map, o) {
    if (!window.L || !map) return;
    css(); o = o || {};
    var nbGroup = L.layerGroup(), fixed = L.layerGroup().addTo(map);
    var b = o.bounds;
    if (o.district) fixed.addLayer(mk(o.districtLatLng || (b && b.getCenter()) || map.getCenter(), 'dist', o.district, 500));
    var boros = o.boroughs;
    if (!boros && b) {
      boros = Object.keys(BORO).filter(function (n) { return b.pad(0.6).contains(BORO[n]); });
      if (!boros.length) { var c = b.getCenter(), best = null, bd = 1e9; Object.keys(BORO).forEach(function (n) { var dd = Math.pow(BORO[n][0] - c.lat, 2) + Math.pow(BORO[n][1] - c.lng, 2); if (dd < bd) { bd = dd; best = n; } }); boros = [best]; }
    }
    o.boroughs = boros || [];
    o.boroughs.forEach(function (n) { if (BORO[n]) fixed.addLayer(mk(BORO[n], 'boro', n, 400)); });
    load().then(function (d) {
      var pad = b ? b.pad(0.15) : null;
      d.forEach(function (n) {
        if (pad && !pad.contains([n.y, n.x])) return;
        if (o.boroughsOnly && (o.boroughs || []).indexOf(n.b) === -1) return;
        nbGroup.addLayer(mk([n.y, n.x], 'nb', n.n, 300));
      });
      function sync() {
        var show = map.getZoom() >= (o.minZoom || 12);
        if (show && !map.hasLayer(nbGroup)) nbGroup.addTo(map);
        if (!show && map.hasLayer(nbGroup)) map.removeLayer(nbGroup);
      }
      map.on('zoomend', sync); sync();
      // no label sits on another: the district's name and the boroughs first, then neighborhoods in the district,
      // then the rest; any that would overlap one already shown is hidden until the map moves and it fits
      function declutter() {
        var root = map.getContainer ? map.getContainer() : document;
        var els = [].slice.call(root.querySelectorAll('.maplbl'));
        var rank = function (e) { return e.classList.contains('dist') ? 0 : e.classList.contains('boro') ? 1 : 2; };
        els.sort(function (a, b) { return rank(a) - rank(b); });
        var placed = [], extra = [].slice.call(root.querySelectorAll('.pmap-office'));
        extra.forEach(function (e) { var r = e.getBoundingClientRect(); if (r.width) placed.push(r); });
        els.forEach(function (e) {
          e.classList.remove('lblhide'); e.style.opacity = '';
          var r = e.getBoundingClientRect(); if (!r.width) return;
          var hit = placed.some(function (q) { return !(r.right + 3 < q.left || r.left - 3 > q.right || r.bottom + 2 < q.top || r.top - 2 > q.bottom); });
          if (hit && rank(e) > 0) { e.classList.add('lblhide'); e.style.opacity = '0'; } else placed.push(r);
        });
      }
      var tmr = null;
      function later() { clearTimeout(tmr); tmr = setTimeout(declutter, 120); }
      setTimeout(declutter, 600); setTimeout(declutter, 1500);
      // the map draws its labels again as it pans, zooms and scrolls into view, so keep checking while the page is up
      setInterval(function () { if (!document.hidden) declutter(); }, 1000);
      try { map.on('moveend', later); } catch (e) {}
      try { map.on('zoomend', later); } catch (e) {}
      window.__mapDeclutter = declutter;
    });
    return { neighborhoods: nbGroup, fixed: fixed };
  }
  window.MapLabels = { add: add };
})();
