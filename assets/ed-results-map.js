/* ED-level election results: dashboard, toggles, address search, per-ED detail.
   Reads data-ed-results="<scope>" and loads /data/edresults/<scope>.json. */
(function () {
  'use strict';
  var NAVY = '#0d1b4b', ORANGE = '#f47920', BORDER = '#e5e2db';
  var PAL = [NAVY, ORANGE, '#5a9e6f', '#8e2b20', '#7b6cd0', '#b8860b', '#2e7d8f', '#b8b2a4'];

  function esc(v) {
    return String(v == null ? '' : v).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function fmt(n) { return Math.round(n).toLocaleString('en-US'); }
  function css() {
    if (document.getElementById('edrm-css')) return;
    var s = document.createElement('style');
    s.id = 'edrm-css';
    s.textContent = [
      '.edrm{border:1px solid ' + BORDER + ';border-radius:12px;overflow:hidden;background:#fff}',
      '.edrm-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:' + BORDER + '}',
      '@media(max-width:560px){.edrm-kpis{grid-template-columns:repeat(2,1fr)}}',
      '.edrm-kpi{background:#fff;padding:11px 12px}',
      '.edrm-kpi .k{font-family:"DM Mono",monospace;font-size:.56rem;text-transform:uppercase;',
      'letter-spacing:.1em;color:#666}',
      '.edrm-kpi .v{font-size:1.15rem;font-weight:900;color:' + NAVY + ';line-height:1.2;margin-top:3px}',
      '.edrm-kpi .s{font-size:.7rem;color:#666;margin-top:1px}',
      '.edrm-bar{padding:10px 12px;border-top:1px solid ' + BORDER + ';background:#faf9f6}',
      '.edrm-grp{font-family:"DM Mono",monospace;font-size:.55rem;text-transform:uppercase;',
      'letter-spacing:.1em;color:#666;margin:6px 0 4px}',
      '.edrm-chips{display:flex;flex-wrap:wrap;gap:5px}',
      '.edrm-chip{font-family:"DM Mono",monospace;font-size:.68rem;padding:4px 9px;border:1px solid ' + BORDER + ';',
      'border-radius:20px;background:#fff;cursor:pointer;color:#333;white-space:nowrap}',
      '.edrm-chip.on{background:' + NAVY + ';border-color:' + NAVY + ';color:#fff;font-weight:700}',
      '.edrm-find{display:flex;gap:6px;padding:10px 12px;border-top:1px solid ' + BORDER + '}',
      '.edrm-find input{flex:1;min-width:0;padding:8px 10px;border:1px solid ' + BORDER + ';border-radius:8px;',
      'font-family:inherit;font-size:.85rem;background:#faf9f6}',
      '.edrm-find button{padding:8px 14px;border:0;border-radius:8px;background:' + ORANGE + ';color:#fff;',
      'font-weight:700;font-size:.82rem;cursor:pointer;font-family:inherit}',
      '.edrm-find button.gh{background:#fff;color:' + NAVY + ';border:1px solid ' + BORDER + '}',
      '.edrm-map{height:430px;width:100%;background:#eceff3}',
      '.edrm-note{padding:8px 12px;font-family:"DM Mono",monospace;font-size:.66rem;color:#666;',
      'border-top:1px solid ' + BORDER + ';background:#faf9f6}',
      '.edrm-leg{display:flex;flex-wrap:wrap;gap:9px;padding:9px 12px;border-top:1px solid ' + BORDER + '}',
      '.edrm-leg span{display:inline-flex;align-items:center;gap:5px;font-size:.75rem;color:#333}',
      '.edrm-leg i{width:12px;height:12px;border-radius:3px;display:inline-block}',
      '.edrm-pop h4{margin:0 0 5px;font-size:.9rem;color:' + NAVY + '}',
      '.edrm-pop .sub{font-family:"DM Mono",monospace;font-size:.64rem;color:#666;margin-bottom:7px}',
      '.edrm-pop table{border-collapse:collapse;font-size:.74rem;width:100%}',
      '.edrm-pop td{padding:2px 6px 2px 0;vertical-align:top}',
      '.edrm-pop .cn{font-weight:700;color:' + NAVY + '}',
      '.edrm-pop .gh{font-family:"DM Mono",monospace;font-size:.58rem;text-transform:uppercase;',
      'letter-spacing:.08em;color:' + ORANGE + ';padding-top:6px}'
    ].join('');
    document.head.appendChild(s);
  }

  function init(host) {
    if (host.dataset.edrmReady) return;
    host.dataset.edrmReady = '1';
    css();
    var scope = host.getAttribute('data-ed-results');
    host.className = 'edrm';
    host.innerHTML =
      '<div class="edrm-kpis" data-k></div>' +
      '<div class="edrm-bar" data-bar></div>' +
      '<div class="edrm-find"><input type="search" placeholder="Search an address or an ED, e.g. 44/1" ' +
      'autocomplete="off" data-q><button type="button" data-go>Find</button>' +
      '<button type="button" class="gh" data-rs>Reset</button></div>' +
      '<div class="edrm-map" data-map></div>' +
      '<div class="edrm-leg" data-leg></div>' +
      '<div class="edrm-note" data-note>Loading results\u2026</div>';

    var kEl = host.querySelector('[data-k]'), barEl = host.querySelector('[data-bar]'),
        legEl = host.querySelector('[data-leg]'), noteEl = host.querySelector('[data-note]'),
        qEl = host.querySelector('[data-q]');

    var map = L.map(host.querySelector('[data-map]'), { scrollWheelZoom: false });
    L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 19, maxNativeZoom: 16, attribution: 'Esri, HERE, Garmin, &copy; OpenStreetMap contributors' }).addTo(map);
    L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 19, maxNativeZoom: 19, opacity: .85 }).addTo(map);

    var data, contests = [], current = null, layer = null, pin = null, home = null;

    fetch('/data/edresults/' + scope + '.json').then(function (r) { return r.json(); }).then(function (d) {
      data = d;
      var use = [];
      d.features.forEach(function (f) {
        f.properties.r.forEach(function (row) { use[row[0]] = (use[row[0]] || 0) + 1; });
      });
      contests = d.contests.map(function (c, i) { return i; })
        .filter(function (i) { return use[i]; })
        .sort(function (a, b) { return use[b] - use[a]; });
      current = contests[0];
      drawBar();
      layer = L.geoJSON(d, {
        style: styleFor,
        onEachFeature: function (f, l) {
          l.on('click', function () { l.bindPopup(popup(f.properties), { maxWidth: 300 }).openPopup(); });
        }
      }).addTo(map);
      home = layer.getBounds();
      map.fitBounds(home, { padding: [12, 12] });
      render();
    }).catch(function () { noteEl.textContent = 'Results did not load.'; });

    /* rows are [contestIndex, total, votes in the contest's own candidate order] */
    function rowFor(p, ci) {
      for (var i = 0; i < p.r.length; i++) if (p.r[i][0] === ci) return p.r[i];
      return null;
    }
    function cands(ci) { return data.contests[ci].c; }
    function edLabel(p) {
      return 'AD ' + p.e.slice(0, 2) + ' ED ' + p.e.slice(2);
    }
    function cbLabel(p) { return (data.cbs || [])[p.b] || ''; }

    function group(ci) {
      var k = data.contests[ci].k;
      return k.slice(0, 3) === 'g25' ? 'November 2025 general'
        : k.slice(0, 3) === 'p25' ? 'June 2025 Democratic primary'
        : 'June 2026 Democratic primary';
    }
    function label(ci) { return data.contests[ci].k.slice(4); }

    function drawBar() {
      var groups = {};
      contests.forEach(function (k) { (groups[group(k)] = groups[group(k)] || []).push(k); });
      barEl.innerHTML = Object.keys(groups).map(function (g) {
        return '<div class="edrm-grp">' + esc(g) + '</div><div class="edrm-chips">' +
          groups[g].map(function (k) {
            return '<button type="button" class="edrm-chip" data-c="' + esc(k) + '">' + esc(label(k)) + '</button>';
          }).join('') + '</div>';
      }).join('');
      barEl.addEventListener('click', function (e) {
        var b = e.target.closest('[data-c]'); if (!b) return;
        current = parseInt(b.getAttribute('data-c'), 10); render();
      });
    }

    var cache = {};
    function totals() {
      if (cache[current]) return cache[current];
      var acc = {}, tot = 0, won = {}, eds = 0, names = cands(current);
      data.features.forEach(function (f) {
        var row = rowFor(f.properties, current); if (!row) return;
        var w = f.properties.w == null ? 1 : f.properties.w;
        tot += row[1] * w; eds++;
        var best = -1, lead = null;
        for (var i = 0; i < names.length; i++) {
          var v = row[i + 2] || 0;
          acc[names[i]] = (acc[names[i]] || 0) + v * w;
          if (v > best) { best = v; lead = names[i]; }
        }
        if (lead) won[lead] = (won[lead] || 0) + 1;
      });
      var order = Object.keys(acc).sort(function (a, b) { return acc[b] - acc[a]; });
      return (cache[current] = { acc: acc, tot: tot, won: won, order: order, eds: eds });
    }

    function colorOf(name) {
      var i = totals().order.indexOf(name);
      return i < 0 ? '#b8b2a4' : PAL[i % PAL.length];
    }
    function styleFor(f) {
      var row = rowFor(f.properties, current);
      if (!row) return { color: '#fff', weight: .6, fillColor: '#ddd', fillOpacity: .35 };
      var names = cands(current), best = -1, lead = null;
      for (var i = 0; i < names.length; i++) {
        if ((row[i + 2] || 0) > best) { best = row[i + 2] || 0; lead = names[i]; }
      }
      return { color: '#fff', weight: .7, fillColor: colorOf(lead), fillOpacity: .72 };
    }

    function popup(p) {
      var groups = {};
      p.r.forEach(function (row) { (groups[group(row[0])] = groups[group(row[0])] || []).push(row); });
      var h = '<div class="edrm-pop"><h4>' + esc(edLabel(p)) + '</h4><div class="sub">' +
        esc(cbLabel(p)) + '</div><table>';
      Object.keys(groups).forEach(function (g) {
        h += '<tr><td colspan="3" class="gh">' + esc(g) + '</td></tr>';
        groups[g].forEach(function (row) {
          var names = cands(row[0]), tot = row[1];
          var pairs = names.map(function (nm, i) { return [nm, row[i + 2] || 0]; })
            .filter(function (x) { return x[1]; })
            .sort(function (a, b) { return b[1] - a[1]; });
          h += '<tr><td class="cn">' + esc(label(row[0])) + '</td><td>' +
            pairs.map(function (x) {
              return esc(x[0]) + ' ' + fmt(x[1]) + ' (' + (100 * x[1] / tot).toFixed(1) + '%)';
            }).join('<br>') + '</td><td style="text-align:right;font-family:\'DM Mono\',monospace">' +
            fmt(tot) + '</td></tr>';
        });
      });
      return h + '</table></div>';
    }

    function render() {
      Array.prototype.forEach.call(barEl.querySelectorAll('[data-c]'), function (b) {
        b.classList.toggle('on', parseInt(b.getAttribute('data-c'), 10) === current);
      });
      var t = totals(), lead = t.order[0], second = t.order[1];
      var leadWon = t.won[lead] || 0, edsWith = t.eds;
      kEl.innerHTML =
        kpi('Contest', label(current), group(current)) +
        kpi('Votes cast', fmt(t.tot), edsWith + ' election districts') +
        kpi(lead ? esc(lead) : 'Leader', lead ? (100 * t.acc[lead] / t.tot).toFixed(1) + '%' : '\u2014',
            lead ? fmt(t.acc[lead]) + ' votes' : '') +
        kpi('EDs carried', leadWon + ' of ' + edsWith,
            second ? esc(second) + ' ' + (t.won[second] || 0) : '');
      legEl.innerHTML = t.order.slice(0, 6).map(function (nm) {
        return '<span><i style="background:' + colorOf(nm) + '"></i>' + esc(nm) + '</span>';
      }).join('');
      noteEl.textContent = 'Tap any election district for its full results.';
      if (layer) layer.setStyle(styleFor);
    }
    function kpi(k, v, s) {
      return '<div class="edrm-kpi"><div class="k">' + k + '</div><div class="v">' + v +
        '</div><div class="s">' + (s || '') + '</div></div>';
    }

    function openED(f) {
      var b = L.geoJSON(f).getBounds();
      map.fitBounds(b, { maxZoom: 16, padding: [40, 40] });
      L.popup({ maxWidth: 300 }).setLatLng(b.getCenter()).setContent(popup(f.properties)).openOn(map);
    }
    function find() {
      var q = (qEl.value || '').trim(); if (!q || !data) return;
      var m = q.match(/^\s*(\d{1,2})\s*[\/\-\s]\s*(\d{1,3})\s*$/);
      if (m) {
        var want = m[1].padStart(2, '0') + m[2].padStart(3, '0');
        var hit = data.features.filter(function (f) { return f.properties.e === want; })[0];
        if (hit) { openED(hit); noteEl.textContent = edLabel(hit.properties); return; }
        noteEl.textContent = 'No election district ' + q + ' in this view.';
        return;
      }
      noteEl.textContent = 'Looking up that address\u2026';
      fetch('https://geosearch.planninglabs.nyc/v2/search?size=1&text=' + encodeURIComponent(q))
        .then(function (r) { return r.json(); }).then(function (g) {
          var ft = (g.features || [])[0];
          if (!ft) { noteEl.textContent = 'No match for that address.'; return; }
          var ll = L.latLng(ft.geometry.coordinates[1], ft.geometry.coordinates[0]);
          if (pin) map.removeLayer(pin);
          pin = L.circleMarker(ll, { radius: 7, color: '#fff', weight: 3, fillColor: ORANGE, fillOpacity: 1 }).addTo(map);
          var hit = null;
          layer.eachLayer(function (l) { if (!hit && l.getBounds().contains(ll) && inside(ll, l)) hit = l.feature; });
          if (hit) { openED(hit); noteEl.textContent = ft.properties.label + ' \u00b7 ' + edLabel(hit.properties); }
          else { map.setView(ll, 15); noteEl.textContent = ft.properties.label + ' is outside this view.'; }
        }).catch(function () { noteEl.textContent = 'Address lookup failed.'; });
    }
    function inside(ll, l) {
      var rings = l.feature.geometry.type === 'Polygon' ? [l.feature.geometry.coordinates]
        : l.feature.geometry.coordinates;
      for (var i = 0; i < rings.length; i++) if (pip(ll.lng, ll.lat, rings[i][0])) return true;
      return false;
    }
    function pip(x, y, ring) {
      var inS = false;
      for (var i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        var xi = ring[i][0], yi = ring[i][1], xj = ring[j][0], yj = ring[j][1];
        if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) inS = !inS;
      }
      return inS;
    }
    host.querySelector('[data-go]').addEventListener('click', find);
    qEl.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); find(); } });
    var rs = host.querySelector('button.gh');
    if (rs) rs.addEventListener('click', function () {
      qEl.value = ''; if (pin) { map.removeLayer(pin); pin = null; }
      map.closePopup(); if (home) map.fitBounds(home, { padding: [12, 12] });
      noteEl.textContent = 'Tap any election district for its full results.';
    });
  }

  function boot() {
    if (!window.L) return;
    Array.prototype.forEach.call(document.querySelectorAll('[data-ed-results]'), init);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
