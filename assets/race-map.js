/* One contest by election district: header with the result, a map shaded by
   margin, donuts for EDs carried and votes, and a searchable ED directory.
   Reads data-race-map="<scope>" data-contest="<key>" data-colors="#a,#b,..."
   data-title="..." data-date="..." and loads /data/edresults/<scope>.json. */
(function () {
  var NAVY = '#0d1b4b', BORDER = '#e5e2db', GREY = '#b8b2a4';

  function esc(v) {
    return String(v == null ? '' : v).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function fmt(n) { return Math.round(n).toLocaleString('en-US'); }
  function pct(a, b) { return b ? (100 * a / b).toFixed(1) + '%' : '\u2014'; }
  function hex2rgb(h) {
    h = h.replace('#', ''); if (h.length === 3) h = h.replace(/(.)/g, '$1$1');
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }
  function rgba(h, a) { var c = hex2rgb(h); return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + a.toFixed(3) + ')'; }

  /* ray casting, works on Polygon and MultiPolygon */
  function inRing(pt, ring) {
    var x = pt[0], y = pt[1], inside = false;
    for (var i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      var xi = ring[i][0], yi = ring[i][1], xj = ring[j][0], yj = ring[j][1];
      if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) inside = !inside;
    }
    return inside;
  }
  function inPoly(pt, geom) {
    var polys = geom.type === 'Polygon' ? [geom.coordinates] : geom.type === 'MultiPolygon' ? geom.coordinates : [];
    for (var p = 0; p < polys.length; p++) {
      if (!inRing(pt, polys[p][0])) continue;
      var hole = false;
      for (var h = 1; h < polys[p].length; h++) if (inRing(pt, polys[p][h])) { hole = true; break; }
      if (!hole) return true;
    }
    return false;
  }

  function donut(slices, big, small) {
    var R = 60, r = 40, C = 75, tot = 0, i;
    for (i = 0; i < slices.length; i++) tot += slices[i].v;
    var h = '<svg viewBox="0 0 150 150" role="img">', a0 = -Math.PI / 2;
    for (i = 0; i < slices.length; i++) {
      if (!slices[i].v) continue;
      var a1 = a0 + 2 * Math.PI * slices[i].v / tot, large = (a1 - a0) > Math.PI ? 1 : 0;
      if (slices[i].v === tot) {
        h += '<circle cx="' + C + '" cy="' + C + '" r="' + ((R + r) / 2) + '" fill="none" stroke="' + slices[i].c + '" stroke-width="' + (R - r) + '"/>';
      } else {
        var x0 = C + R * Math.cos(a0), y0 = C + R * Math.sin(a0), x1 = C + R * Math.cos(a1), y1 = C + R * Math.sin(a1);
        var X0 = C + r * Math.cos(a1), Y0 = C + r * Math.sin(a1), X1 = C + r * Math.cos(a0), Y1 = C + r * Math.sin(a0);
        h += '<path d="M' + x0 + ' ' + y0 + 'A' + R + ' ' + R + ' 0 ' + large + ' 1 ' + x1 + ' ' + y1 +
          'L' + X0 + ' ' + Y0 + 'A' + r + ' ' + r + ' 0 ' + large + ' 0 ' + X1 + ' ' + Y1 + 'Z" fill="' + slices[i].c + '" stroke="#fff" stroke-width="1.5"/>';
      }
      a0 = a1;
    }
    h += '<text x="' + C + '" y="' + (C + 4) + '" text-anchor="middle" class="big">' + esc(big) + '</text>';
    h += '<text x="' + C + '" y="' + (C + 20) + '" text-anchor="middle" class="sm">' + esc(small) + '</text>';
    return h + '</svg>';
  }

  function mix(hex, t) { /* t 0 = light tint, 1 = full color */
    var c = hex2rgb(hex), w = [244, 242, 238];
    return 'rgb(' + c.map(function (v, i) { return Math.round(w[i] + (v - w[i]) * t); }).join(',') + ')';
  }
  function css() {
    if (document.getElementById('rcm-css')) return;
    var s = document.createElement('style');
    s.id = 'rcm-css';
    s.textContent = [
      '.rcm{margin-top:8px}',
      '.rcm-card{background:#fff;border:1px solid ' + BORDER + ';border-radius:12px;padding:14px 14px 12px;margin:0 0 12px;box-shadow:0 2px 10px rgba(13,27,75,.05)}',
      '.rcm-card h3{margin:0 0 6px;color:' + NAVY + ';font-size:1.02rem;line-height:1.3}',
      '.rcm-card p{margin:0 0 12px;color:#4b5563;font-size:.84rem;line-height:1.6}',
      '.rcm-eye{font-family:"DM Mono",monospace;font-size:.66rem;letter-spacing:.09em;text-transform:uppercase;color:#6b7280;font-weight:700}',
      '.rcm-when{font-family:"DM Mono",monospace;font-size:.62rem;text-transform:uppercase;letter-spacing:.11em;color:#6b6760;margin-bottom:3px}',
      '.rcm-find{display:flex;gap:6px;margin:0 0 10px}',
      '.rcm-find input{flex:1;min-width:0;font:inherit;font-size:.86rem;padding:10px 12px;border:1.5px solid ' + BORDER + ';border-radius:8px;background:#fff}',
      '.rcm-find button{font:inherit;font-size:.8rem;font-weight:800;padding:10px 13px;border-radius:8px;border:1.5px solid ' + NAVY + ';background:' + NAVY + ';color:#fff;cursor:pointer;white-space:nowrap}',
      '.rcm-find button.gh{background:#fff;color:' + NAVY + '}',
      '.rcm-map{height:460px;border:1px solid ' + BORDER + ';border-radius:10px;overflow:hidden;background:#edf2f7}',
      '.rcm-map .nbhd{background:none;border:0;box-shadow:none;font-family:"DM Sans",sans-serif;font-weight:800;font-size:.72rem;color:' + NAVY + ';text-shadow:0 0 3px #fff,0 0 3px #fff,0 0 5px #fff,0 0 8px #fff;white-space:nowrap;pointer-events:none}',
      '.rcm-map .edlbl{background:none;border:0;box-shadow:none;font-family:"DM Mono",monospace;font-size:.6rem;font-weight:700;color:#fff;text-shadow:0 0 2px rgba(0,0,0,.7),0 0 4px rgba(0,0,0,.5);pointer-events:none;padding:0}',
      '.rcm-map .leaflet-tooltip.edtip{background:rgba(17,24,39,.94);border:0;border-radius:8px;color:#fff;box-shadow:0 8px 28px rgba(0,0,0,.22);padding:8px 10px;font-size:.76rem}',
      '.rcm-note{font-size:.76rem;color:#6b6760;margin:8px 2px 0;min-height:1.1em}',
      '.rcm-key{display:flex;flex-direction:column;gap:12px;margin-top:14px;font-size:.72rem;color:#4b5563}',
      '.rcm-key .sub{font-size:.68rem;line-height:1.5;color:#6b7280;margin-top:-6px}',
      '.rcm-key-row{display:grid;grid-template-columns:112px minmax(0,1fr);gap:8px;align-items:center;margin-bottom:8px}',
      '.rcm-key-lbl{font-size:.74rem;font-weight:800;color:' + NAVY + '}',
      '.rcm-key-bar{position:relative;height:12px;border-radius:999px;border:1px solid rgba(17,24,39,.08)}',
      '.rcm-key-bar .sc{position:absolute;inset:0;border-radius:999px}',
      '.rcm-key-bar .tk{position:absolute;top:14px;transform:translateX(-50%);font-size:.63rem;color:#6b7280;white-space:nowrap;font-family:"DM Mono",monospace}',
      '.rcm-brk{display:grid;grid-template-columns:minmax(90px,.9fr) minmax(0,2fr);gap:12px 14px;align-items:center;margin-top:12px}',
      '.rcm-brk .lb{font-size:.9rem;color:' + NAVY + '}',
      '.rcm-brk .lb.t{font-weight:900}',
      '.rcm-brk .st{display:flex;height:34px;border-radius:7px;overflow:hidden;background:#efede8}',
      '.rcm-brk .st i{display:flex;align-items:center;padding-left:9px;color:#fff;font-family:"DM Mono",monospace;font-size:.86rem;font-weight:700;min-width:0}',
      '.rcm-brk .st i.z{display:none}',
      '.rcm-brk .sm{grid-column:2;margin-top:-8px;font-family:"DM Mono",monospace;font-size:.82rem;font-weight:700}',
      '.rcm-chips{display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:12px;font-family:"DM Mono",monospace;font-size:.76rem;color:#374151}',
      '.rcm-chips i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:7px;vertical-align:-2px}',
      '.rcm-res{display:grid;grid-template-columns:minmax(90px,.9fr) minmax(0,2fr);gap:12px 14px;align-items:center;margin-top:12px}',
      '.rcm-res .n{font-weight:900;font-size:1rem;color:' + NAVY + '}',
      '.rcm-res .tr{height:44px;border-radius:7px;background:#efede8;position:relative;overflow:hidden}',
      '.rcm-res .tr i{position:absolute;left:0;top:0;bottom:0;border-radius:7px;display:flex;align-items:center;justify-content:center;color:#fff;font-family:"DM Mono",monospace;font-size:.88rem;font-weight:700;white-space:nowrap}',
      '.rcm-res .tr b{position:absolute;top:0;bottom:0;display:flex;align-items:center;padding-left:10px;font-family:"DM Mono",monospace;font-size:.86rem;font-weight:700;color:' + NAVY + ';white-space:nowrap}',
      '.rcm-tot{margin-top:12px;font-family:"DM Mono",monospace;font-size:.78rem;color:#6b6760}',
      '.rcm-dn{display:grid;grid-template-columns:150px minmax(0,1fr);gap:14px;align-items:center;margin-top:12px}',
      '@media(max-width:400px){.rcm-dn{grid-template-columns:1fr}}',
      '.rcm-dn svg{width:150px;height:150px;display:block}',
      '.rcm-dn .big{font-family:"DM Mono",monospace;font-weight:700;font-size:1.3rem;fill:' + NAVY + '}',
      '.rcm-dn .sm{font-family:"DM Mono",monospace;font-size:.5rem;fill:#374151;text-transform:uppercase;letter-spacing:.08em}',
      '.rcm-dn .lg{display:flex;flex-direction:column;gap:8px;font-size:.9rem;color:' + NAVY + '}',
      '.rcm-dn .lg i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:8px;vertical-align:-1px}',
      '.rcm-dn .lg b{font-family:"DM Mono",monospace;font-size:1rem}',
      '.rcm-dir{margin-top:12px;border:1px solid ' + BORDER + ';border-radius:12px;background:#fff;overflow:hidden}',
      '.rcm-dir>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:8px;padding:12px 14px;font-weight:800;font-size:.88rem;color:' + NAVY + '}',
      '.rcm-dir>summary::-webkit-details-marker{display:none}',
      '.rcm-dir>summary .arr{margin-left:auto;font-size:.7rem;transition:transform .15s}',
      '.rcm-dir[open]>summary .arr{transform:rotate(180deg)}',
      '.rcm-dir[open]>summary{border-bottom:1px solid ' + BORDER + '}',
      '.rcm-dir .ctl{padding:12px 14px 10px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}',
      '.rcm-dir .ctl input,.rcm-dir .ctl select{font:inherit;font-size:.86rem;padding:9px 11px;border:1.5px solid ' + BORDER + ';border-radius:8px;background:#fff;color:' + NAVY + '}',
      '.rcm-dir .ctl input{flex:1 1 180px;min-width:0}',
      '.rcm-dir .cnt{font-family:"DM Mono",monospace;font-size:.72rem;color:#4b5563;border:1px solid ' + BORDER + ';border-radius:999px;padding:6px 12px}',
      '.rcm-tw{overflow:auto;max-height:520px}',
      '.rcm-t{width:100%;border-collapse:collapse;font-size:.82rem;min-width:560px}',
      '.rcm-t thead tr{background:' + NAVY + '}',
      '.rcm-t th{position:sticky;top:0;background:' + NAVY + ';color:rgba(255,255,255,.75);text-align:left;font-family:"DM Mono",monospace;font-size:.62rem;text-transform:uppercase;letter-spacing:.1em;font-weight:500;padding:11px 12px;white-space:nowrap}',
      '.rcm-t td{padding:11px 12px;border-bottom:1px solid #e5e2db;white-space:nowrap;vertical-align:middle;font-family:"DM Mono",monospace}',
      '.rcm-t td.r,.rcm-t th.r{text-align:right}',
      '.rcm-t td.ed{font-weight:800;color:' + NAVY + '}',
      '.rcm-t td.ed small{display:block;font-family:"DM Sans",sans-serif;font-weight:500;font-size:.66rem;color:#6b7280;margin-top:1px}',
      '.rcm-t td .v{font-weight:800}',
      '.rcm-t td .p{color:#6b7280;font-size:.74rem;margin-left:4px}',
      '.rcm-t td.bl{color:#6b7280}',
      '.rcm-t td .chip{display:inline-block;color:#fff;font-size:.66rem;font-weight:800;padding:4px 8px;border-radius:6px;letter-spacing:.04em}',
      '.rcm-t tr{cursor:pointer}',
      '.rcm-t tbody tr:nth-child(odd) td{background:#f8f7f4}',
      '.rcm-t tbody tr.hit td{background:#fff3e8}',
      '.rcm-pop h4{margin:0 0 2px;font-size:.9rem;color:' + NAVY + '}',
      '.rcm-pop .sub{font-size:.7rem;color:#6b6760;margin-bottom:6px}',
      '.rcm-pop table{border-collapse:collapse;font-size:.78rem;width:100%}',
      '.rcm-pop td{padding:3px 6px 3px 0;vertical-align:top}',
      '.rcm-pop td.r{text-align:right;font-family:"DM Mono",monospace}',
      '.rcm-pop .mg{font-family:"DM Mono",monospace;font-size:.7rem;color:#6b6760;padding-top:5px}'
    ].join('');
    document.head.appendChild(s);
  }

  function init(host) {
    if (host.dataset.rcmReady || !window.L) return;
    host.dataset.rcmReady = '1';
    css();
    var scope = host.getAttribute('data-race-map'), want = host.getAttribute('data-contest');
    var colors = (host.getAttribute('data-colors') || '').split(',').filter(Boolean);
    var colorNames = (host.getAttribute('data-color-names') || '').split(',').filter(Boolean);
    var title = host.getAttribute('data-title') || '', when = host.getAttribute('data-date') || '';
    var areaName = host.getAttribute('data-area') || 'the district';
    var labels = [];
    try { labels = JSON.parse(host.getAttribute('data-labels') || '[]'); } catch (e) { labels = []; }
    host.className = 'rcm';
    host.innerHTML =
      '<div class="rcm-card"><div class="rcm-when">' + esc(when) + '</div><h3>' + esc(title) + '</h3><p data-blurb>Loading results\u2026</p>' +
      '<div class="rcm-find"><input type="search" placeholder="Enter your address, or an ED like 44/17" autocomplete="off" data-q>' +
      '<button type="button" data-go>Find ED</button><button type="button" class="gh" data-rs>Reset</button></div>' +
      '<div class="rcm-map" data-map></div><div class="rcm-note" data-note></div><div class="rcm-key" data-key></div></div>' +
      '<div class="rcm-card"><div class="rcm-eye">Election districts carried</div><div class="rcm-dn" data-dn></div>' +
      '<div class="rcm-eye" style="margin-top:16px">By community board</div><div class="rcm-brk" data-brk></div><div class="rcm-chips" data-chips></div></div>' +
      '<div class="rcm-card"><div class="rcm-eye">First-choice results</div><div class="rcm-res" data-res></div><div class="rcm-tot" data-tot></div></div>' +
      '<details class="rcm-dir" data-dir><summary><span data-dirttl>See how every election district voted</span><span class="arr">&#9660;</span></summary>' +
      '<div class="ctl"><input type="search" placeholder="Filter by ED, e.g. 017/44, or a community board" autocomplete="off" data-flt>' +
      '<select data-ad><option value="">All Assembly Districts</option></select><span class="cnt" data-cnt></span></div>' +
      '<div class="rcm-tw"><table class="rcm-t"><thead><tr><th>ED/AD</th><th class="r" data-th0></th><th class="r" data-th1></th><th class="r" data-th2></th><th class="r">Ballots</th><th>Result</th></tr></thead><tbody data-rows></tbody></table></div></details>';

    var blurbEl = host.querySelector('[data-blurb]'), keyEl = host.querySelector('[data-key]'),
        noteEl = host.querySelector('[data-note]'), dnEl = host.querySelector('[data-dn]'),
        brkEl = host.querySelector('[data-brk]'), chipsEl = host.querySelector('[data-chips]'),
        resEl = host.querySelector('[data-res]'), totEl = host.querySelector('[data-tot]'),
        qEl = host.querySelector('[data-q]'), rowsEl = host.querySelector('[data-rows]'),
        fltEl = host.querySelector('[data-flt]'), adEl = host.querySelector('[data-ad]'),
        cntEl = host.querySelector('[data-cnt]'), dirEl = host.querySelector('[data-dir]');

    var map = L.map(host.querySelector('[data-map]'), { scrollWheelZoom: false });
    L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 19, maxNativeZoom: 16, attribution: 'Esri, HERE, Garmin, &copy; OpenStreetMap contributors' }).addTo(map);
    var refLayer = L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 19, maxNativeZoom: 16, opacity: .55 });

    var data, ci = -1, names = [], eds = [], layer = null, pin = null, home = null, byE = {}, lyrByE = {}, maxM = 0, edLabels = null;

    function colorOf(i) { return colors[i] || GREY; }
    function edLabel(e) { return 'AD ' + e.slice(0, 2) + ' ED ' + parseInt(e.slice(2), 10); }
    function edShort(e) { return e.slice(2) + '/' + e.slice(0, 2); }
    function cbLabel(p) { return (data.cbs || [])[p.b] || ''; }
    function last(n) { return n.split(' ').pop(); }
    function tint(i, m) { var t = maxM ? Math.max(0, Math.min(1, m / maxM)) : 1; return mix(colorOf(i), .28 + t * .72); }

    function styleFor(f) {
      var d = byE[f.properties.e];
      if (!d) return { color: '#fff', weight: .6, fillColor: '#ddd', fillOpacity: .25 };
      return { color: '#fff', weight: 1, fillColor: tint(d.win, d.margin), fillOpacity: .92 };
    }

    function popup(d) {
      var h = '<div class="rcm-pop"><h4>' + esc(edLabel(d.e)) + '</h4><div class="sub">' + esc(cbLabel(d.p)) + '</div><table>';
      d.order.forEach(function (i) {
        if (!d.v[i]) return;
        h += '<tr><td><i style="display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:6px;background:' + colorOf(i) + '"></i>' +
          esc(names[i]) + '</td><td class="r">' + fmt(d.v[i]) + '</td><td class="r">' + pct(d.v[i], d.tot) + '</td></tr>';
      });
      h += '<tr><td class="mg" colspan="3">' + fmt(d.tot) + ' ballots &middot; ' + esc(last(names[d.win])) + ' by ' + d.margin.toFixed(1) + ' points</td></tr>';
      return h + '</table></div>';
    }

    function openED(d) {
      var l = lyrByE[d.e]; if (!l) return;
      var b = l.getBounds();
      map.fitBounds(b, { maxZoom: 16, padding: [40, 40] });
      L.popup({ maxWidth: 300 }).setLatLng(b.getCenter()).setContent(popup(d)).openOn(map);
      Array.prototype.forEach.call(rowsEl.querySelectorAll('tr'), function (tr) {
        tr.classList.toggle('hit', tr.getAttribute('data-e') === d.e);
      });
    }

    function drawEdLabels() {
      var show = map.getZoom() >= 15;
      if (show && !edLabels) {
        edLabels = L.layerGroup();
        eds.forEach(function (x) {
          var l = lyrByE[x.e]; if (!l) return;
          L.marker(l.getBounds().getCenter(), { icon: L.divIcon({ className: 'edlbl', html: String(parseInt(x.e.slice(2), 10)), iconSize: [30, 12], iconAnchor: [15, 6] }), interactive: false }).addTo(edLabels);
        });
      }
      if (edLabels) { if (show) edLabels.addTo(map); else map.removeLayer(edLabels); }
    }

    fetch('/data/edresults/' + scope + '.json').then(function (r) { return r.json(); }).then(function (d) {
      data = d;
      for (var i = 0; i < d.contests.length; i++) if (d.contests[i].k === want) ci = i;
      if (ci < 0) { blurbEl.textContent = 'That contest is not in this file.'; return; }
      names = d.contests[ci].c;
      var totals = names.map(function () { return 0; }), won = names.map(function () { return 0; }), cast = 0, byCB = {};
      d.features.forEach(function (f) {
        var p = f.properties, row = null;
        for (var k = 0; k < p.r.length; k++) if (p.r[k][0] === ci) row = p.r[k];
        if (!row) return;
        var v = names.map(function (_, j) { return row[j + 2] || 0; });
        var order = names.map(function (_, j) { return j; }).sort(function (a, b) { return v[b] - v[a]; });
        var tot = row[1], win = order[0], second = order[1];
        var margin = tot ? 100 * (v[win] - (second == null ? 0 : v[second])) / tot : 0;
        var e = { e: p.e, p: p, v: v, tot: tot, win: win, order: order, margin: margin };
        byE[p.e] = e; eds.push(e);
        for (var j = 0; j < v.length; j++) totals[j] += v[j];
        won[win]++; cast += tot; if (margin > maxM) maxM = margin;
        var cb = cbLabel(p); byCB[cb] = byCB[cb] || { n: 0, w: {} }; byCB[cb].n++; byCB[cb].w[win] = (byCB[cb].w[win] || 0) + 1;
      });
      var order = names.map(function (_, j) { return j; }).sort(function (a, b) { return totals[b] - totals[a]; });
      var lead = order[0], second = order[1];
      maxM = Math.ceil(maxM / 5) * 5;

      /* blurb */
      blurbEl.innerHTML = 'This map shows the winning candidate\u2019s percentage margin in each of the ' + eds.length + ' election districts in ' + esc(areaName) + '. ' +
        (colorNames[lead] ? esc(colorNames[lead].charAt(0).toUpperCase() + colorNames[lead].slice(1)) + ' marks a ' + esc(last(names[lead])) + ' win' : '') +
        (colorNames[second] ? ' and ' + esc(colorNames[second]) + ' marks a ' + esc(last(names[second])) + ' win' : '') + '. Tap any election district for its result, or enter an address to find yours.';

      /* key */
      var mid = (maxM / 2) + '%';
      keyEl.innerHTML = '<div class="rcm-eye">Winning margin by election district</div>' +
        '<div class="sub">Color intensity runs from 0% up to about ' + maxM + '% on this map.</div>' +
        [lead, second].map(function (i) {
          return '<div class="rcm-key-row"><span class="rcm-key-lbl">' + esc(last(names[i])) + '</span><div class="rcm-key-bar">' +
            '<span class="sc" style="background:linear-gradient(90deg,' + mix(colorOf(i), .28) + ',' + colorOf(i) + ')"></span>' +
            '<span class="tk" style="left:0">0%</span><span class="tk" style="left:50%">' + mid + '</span><span class="tk" style="left:100%">' + maxM + '%</span></div></div>';
        }).join('');

      /* map */
      layer = L.geoJSON(d, {
        style: styleFor,
        onEachFeature: function (f, l) {
          lyrByE[f.properties.e] = l;
          var x = byE[f.properties.e];
          if (x) l.bindTooltip(edLabel(x.e) + ' \u00b7 ' + last(names[x.win]) + ' +' + x.margin.toFixed(1) + '%', { className: 'edtip', sticky: true });
          l.on('click', function () { if (x) openED(x); });
        }
      }).addTo(map);
      refLayer.addTo(map);
      labels.forEach(function (lb) {
        L.marker([lb[1], lb[2]], { icon: L.divIcon({ className: 'nbhd', html: esc(lb[0]), iconSize: null }), interactive: false }).addTo(map);
      });
      home = layer.getBounds();
      map.fitBounds(home, { padding: [6, 6] });
      map.on('zoomend', drawEdLabels);
      noteEl.textContent = 'Zoom in to see each election district\u2019s number.';

      /* donut: EDs carried */
      var otherWon = eds.length - won[lead] - won[second];
      var sl = [{ v: won[lead], c: colorOf(lead) }, { v: won[second], c: colorOf(second) }];
      if (otherWon > 0) sl.push({ v: otherWon, c: GREY });
      dnEl.innerHTML = donut(sl, won[lead] + ' of ' + eds.length, last(names[lead])) +
        '<div class="lg"><span><i style="background:' + colorOf(lead) + '"></i>' + esc(names[lead]) + ' <b>' + won[lead] + '</b></span>' +
        '<span><i style="background:' + colorOf(second) + '"></i>' + esc(names[second]) + ' <b>' + won[second] + '</b></span>' +
        (otherWon > 0 ? '<span><i style="background:' + GREY + '"></i>Others <b>' + otherWon + '</b></span>' : '') + '</div>';

      /* breakdown by community board */
      var cbs = Object.keys(byCB).sort(function (a, b) { return byCB[b].n - byCB[a].n; });
      function stack(lb, n, w, bold) {
        var a = w[lead] || 0, b = w[second] || 0, o = n - a - b, top = a >= b ? lead : second, topN = Math.max(a, b);
        return '<div class="lb' + (bold ? ' t' : '') + '">' + esc(lb) + '</div><div class="st">' +
          '<i style="width:' + (100 * a / n) + '%;background:' + colorOf(lead) + '" class="' + (a ? '' : 'z') + '">' + a + '</i>' +
          '<i style="width:' + (100 * b / n) + '%;background:' + colorOf(second) + '" class="' + (b ? '' : 'z') + '">' + b + '</i>' +
          (o > 0 ? '<i style="width:' + (100 * o / n) + '%;background:' + GREY + '">' + o + '</i>' : '') + '</div>' +
          '<div class="sm" style="color:' + colorOf(top) + '">' + esc(last(names[top])) + ' ' + topN + '/' + n + '</div>';
      }
      var totW = {}; totW[lead] = won[lead]; totW[second] = won[second];
      brkEl.innerHTML = cbs.map(function (cb) { return stack(cb, byCB[cb].n, byCB[cb].w, false); }).join('') + stack(areaName.charAt(0).toUpperCase() + areaName.slice(1), eds.length, totW, true);
      chipsEl.innerHTML = '<span><i style="background:' + colorOf(lead) + '"></i>' + esc(last(names[lead])) + '</span><span><i style="background:' + colorOf(second) + '"></i>' + esc(last(names[second])) + '</span>' +
        (otherWon > 0 ? '<span><i style="background:' + GREY + '"></i>Others</span>' : '');

      /* first-choice results */
      resEl.innerHTML = order.filter(function (i) { return totals[i]; }).map(function (i) {
        var share = 100 * totals[i] / cast, txt = fmt(totals[i]) + ' &middot; ' + share.toFixed(1) + '%';
        return '<div class="n">' + esc(/write/i.test(names[i]) ? 'Write-in' : last(names[i])) + '</div><div class="tr">' +
          '<i style="width:' + Math.max(share, 1.2).toFixed(1) + '%;background:' + colorOf(i) + '">' + (share >= 30 ? txt : '') + '</i>' +
          (share < 30 ? '<b style="left:' + Math.max(share, 1.2).toFixed(1) + '%">' + txt + '</b>' : '') + '</div>';
      }).join('');
      totEl.textContent = fmt(cast) + ' ballots with a first choice \u00b7 ' + eds.length + ' election districts';

      /* directory */
      for (var t = 0; t < 3; t++) {
        var th = host.querySelector('[data-th' + t + ']');
        if (th) th.textContent = order[t] != null ? last(names[order[t]]) : '';
      }
      var ads = {};
      eds.forEach(function (x) { ads[x.e.slice(0, 2)] = 1; });
      Object.keys(ads).sort().forEach(function (ad) {
        var o = document.createElement('option'); o.value = ad; o.textContent = 'AD ' + parseInt(ad, 10); adEl.appendChild(o);
      });
      eds.sort(function (a, b) { return a.e < b.e ? -1 : a.e > b.e ? 1 : 0; });
      rowsEl.innerHTML = eds.map(function (x) {
        var cells = '';
        for (var t = 0; t < 3; t++) {
          var i = order[t];
          cells += '<td class="r">' + (i == null ? '' : '<span class="v" style="color:' + colorOf(i) + '">' + fmt(x.v[i]) + '</span><span class="p">(' + pct(x.v[i], x.tot) + ')</span>') + '</td>';
        }
        var srch = (edShort(x.e) + ' ' + edLabel(x.e) + ' ' + x.e.slice(0, 2) + '/' + parseInt(x.e.slice(2), 10) + ' ' + cbLabel(x.p) + ' ' + cbLabel(x.p).replace(/cb\s*(\d)/i, 'cb $1')).toLowerCase();
        return '<tr data-e="' + esc(x.e) + '" data-ad="' + x.e.slice(0, 2) + '" data-s="' + esc(srch) + '">' +
          '<td class="ed">' + esc(edShort(x.e)) + '<small>' + esc(cbLabel(x.p)) + '</small></td>' + cells +
          '<td class="r bl">' + fmt(x.tot) + '</td>' +
          '<td><span class="chip" style="background:' + colorOf(x.win) + '">' + esc(last(names[x.win]).toUpperCase()) + ' +' + x.margin.toFixed(1) + '</span></td></tr>';
      }).join('');
      function applyFilter() {
        var q = fltEl.value.trim().toLowerCase().replace(/\s+/g, ' '), ad = adEl.value, n = 0;
        Array.prototype.forEach.call(rowsEl.querySelectorAll('tr'), function (tr) {
          var ok = (!q || tr.getAttribute('data-s').indexOf(q) !== -1) && (!ad || tr.getAttribute('data-ad') === ad);
          tr.style.display = ok ? '' : 'none'; if (ok) n++;
        });
        cntEl.textContent = n + ' EDs';
      }
      applyFilter();
      rowsEl.addEventListener('click', function (ev) {
        var tr = ev.target.closest('tr[data-e]'); if (!tr) return;
        var x = byE[tr.getAttribute('data-e')]; if (!x) return;
        openED(x);
        host.querySelector('[data-map]').scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
      fltEl.addEventListener('input', applyFilter);
      adEl.addEventListener('change', applyFilter);
      dirEl.addEventListener('toggle', function () { if (dirEl.open) setTimeout(function () { map.invalidateSize(); }, 50); });
    }).catch(function () { blurbEl.textContent = 'Results did not load.'; });

    function showRow(e) {
      dirEl.open = true;
      fltEl.value = ''; adEl.value = '';
      Array.prototype.forEach.call(rowsEl.querySelectorAll('tr'), function (r) { r.style.display = ''; });
      cntEl.textContent = eds.length + ' EDs';
      var tr = rowsEl.querySelector('tr[data-e="' + e + '"]');
      if (tr) tr.scrollIntoView({ block: 'center' });
    }
    function dropPin(lat, lng, label) {
      if (pin) map.removeLayer(pin);
      pin = L.circleMarker([lat, lng], { radius: 7, color: '#fff', weight: 2, fillColor: '#f47920', fillOpacity: 1 }).addTo(map);
      var hit = null;
      for (var i = 0; i < data.features.length; i++) {
        if (inPoly([lng, lat], data.features[i].geometry)) { hit = data.features[i]; break; }
      }
      var d = hit && byE[hit.properties.e];
      if (d) {
        openED(d);
        noteEl.textContent = (label ? label + ' is in ' : 'That spot is in ') + edLabel(d.e) + ', ' + cbLabel(d.p) + ': ' + last(names[d.win]) + ' won it by ' + d.margin.toFixed(1) + ' points.';
        showRow(d.e);
      } else {
        map.setView([lat, lng], 15);
        noteEl.textContent = (label || 'That spot') + ' is outside ' + areaName + '.';
      }
    }
    function find() {
      var q = (qEl.value || '').trim(); if (!q || !data) return;
      var m = q.match(/^\s*(\d{1,3})\s*[\/\-\s]\s*(\d{1,3})\s*$/);
      if (m) {
        var a = m[1], b = m[2], d = byE[a.padStart(2, '0') + b.padStart(3, '0')] || byE[b.padStart(2, '0') + a.padStart(3, '0')];
        if (d) { openED(d); noteEl.textContent = edLabel(d.e) + ', ' + cbLabel(d.p) + ': ' + last(names[d.win]) + ' won it by ' + d.margin.toFixed(1) + ' points.'; showRow(d.e); return; }
        noteEl.textContent = 'No election district ' + q + ' in ' + areaName + '.';
        return;
      }
      noteEl.textContent = 'Looking up that address\u2026';
      fetch('https://geosearch.planninglabs.nyc/v2/search?size=1&text=' + encodeURIComponent(q))
        .then(function (r) { return r.json(); }).then(function (g) {
          var ft = (g.features || [])[0];
          if (!ft) { noteEl.textContent = 'No match for that address.'; return; }
          dropPin(ft.geometry.coordinates[1], ft.geometry.coordinates[0], ft.properties.name || q);
        }).catch(function () { noteEl.textContent = 'Address lookup failed.'; });
    }
    host.querySelector('[data-go]').addEventListener('click', find);
    qEl.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); find(); } });
    map.on('click', function (e) { if (data) dropPin(e.latlng.lat, e.latlng.lng, ''); });
    host.querySelector('[data-rs]').addEventListener('click', function () {
      qEl.value = ''; if (pin) { map.removeLayer(pin); pin = null; }
      map.closePopup(); if (home) map.fitBounds(home, { padding: [6, 6] });
      Array.prototype.forEach.call(rowsEl.querySelectorAll('tr'), function (tr) { tr.classList.remove('hit'); });
      noteEl.textContent = 'Zoom in to see each election district\u2019s number.';
    });
  }

  function boot() {
    if (!window.L) return;
    Array.prototype.forEach.call(document.querySelectorAll('[data-race-map]'), init);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
