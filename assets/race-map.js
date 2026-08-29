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

  function css() {
    if (document.getElementById('rcm-css')) return;
    var s = document.createElement('style');
    s.id = 'rcm-css';
    s.textContent = [
      '.rcm{margin-top:8px}',
      '.rcm-head{border:1px solid ' + BORDER + ';border-radius:12px;background:#fff;padding:14px 14px 10px;margin-bottom:10px}',
      '.rcm-when{font-family:"DM Mono",monospace;font-size:.62rem;text-transform:uppercase;letter-spacing:.11em;color:#6b6760}',
      '.rcm-title{font-size:1.02rem;font-weight:900;color:' + NAVY + ';margin:3px 0 10px;line-height:1.25}',
      '.rcm-cand{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 10px;align-items:end;margin-top:8px}',
      '.rcm-cand .n{font-weight:800;font-size:.9rem;color:' + NAVY + '}',
      '.rcm-cand .n i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}',
      '.rcm-cand .p{font-family:"DM Mono",monospace;font-weight:700;font-size:1.05rem;color:' + NAVY + ';text-align:right}',
      '.rcm-cand .s{grid-column:1/3;font-family:"DM Mono",monospace;font-size:.66rem;color:#6b6760;margin-top:-2px}',
      '.rcm-cand .bar{grid-column:1/3;height:8px;border-radius:4px;background:#efede8;overflow:hidden}',
      '.rcm-cand .bar i{display:block;height:100%;border-radius:4px}',
      '.rcm-find{display:flex;gap:6px;margin:10px 0 8px}',
      '.rcm-find input{flex:1;min-width:0;font:inherit;font-size:.86rem;padding:9px 11px;border:1.5px solid ' + BORDER + ';border-radius:8px;background:#fff}',
      '.rcm-find button{font:inherit;font-size:.8rem;font-weight:800;padding:9px 12px;border-radius:8px;border:1.5px solid ' + NAVY + ';background:' + NAVY + ';color:#fff;cursor:pointer}',
      '.rcm-find button.gh{background:#fff;color:' + NAVY + '}',
      '.rcm-map{height:360px;border:1px solid ' + BORDER + ';border-radius:12px;overflow:hidden;background:#eee}',
      '.rcm-leg{display:flex;flex-wrap:wrap;gap:6px 16px;align-items:center;margin:8px 2px 0;font-family:"DM Mono",monospace;font-size:.64rem;color:#4a4740}',
      '.rcm-leg .g{display:inline-block;width:64px;height:10px;border-radius:3px;vertical-align:-1px;margin-right:6px;border:1px solid rgba(0,0,0,.08)}',
      '.rcm-note{font-size:.76rem;color:#6b6760;margin:6px 2px 0;min-height:1.1em}',
      '.rcm-charts{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}',
      '@media(max-width:420px){.rcm-charts{grid-template-columns:1fr}}',
      '.rcm-chart{border:1px solid ' + BORDER + ';border-radius:12px;background:#fff;padding:12px 10px 10px;text-align:center}',
      '.rcm-chart .k{font-family:"DM Mono",monospace;font-size:.6rem;text-transform:uppercase;letter-spacing:.1em;color:#6b6760;margin-bottom:6px}',
      '.rcm-chart svg{width:150px;height:150px;display:block;margin:0 auto}',
      '.rcm-chart .big{font-family:"DM Mono",monospace;font-weight:700;font-size:1.25rem;fill:' + NAVY + '}',
      '.rcm-chart .sm{font-family:"DM Mono",monospace;font-size:.5rem;fill:#6b6760;text-transform:uppercase;letter-spacing:.08em}',
      '.rcm-chart .lg{display:flex;flex-wrap:wrap;justify-content:center;gap:4px 12px;margin-top:8px;font-size:.74rem;color:#4a4740}',
      '.rcm-chart .lg i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:-1px}',
      '.rcm-chart .lg b{color:' + NAVY + '}',
      '.rcm-dir{margin-top:12px;border:1px solid ' + BORDER + ';border-radius:12px;background:#fff;overflow:hidden}',
      '.rcm-dir>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:8px;padding:11px 13px;font-weight:800;font-size:.86rem;color:' + NAVY + '}',
      '.rcm-dir>summary::-webkit-details-marker{display:none}',
      '.rcm-dir>summary .arr{margin-left:auto;font-size:.7rem;transition:transform .15s}',
      '.rcm-dir[open]>summary .arr{transform:rotate(180deg)}',
      '.rcm-dir[open]>summary{border-bottom:1px solid ' + BORDER + '}',
      '.rcm-dir .flt{padding:10px 12px 4px}',
      '.rcm-dir .flt input{width:100%;box-sizing:border-box;font:inherit;font-size:.84rem;padding:8px 11px;border:1.5px solid ' + BORDER + ';border-radius:8px}',
      '.rcm-tw{overflow-x:auto;max-height:440px;overflow-y:auto}',
      '.rcm-t{width:100%;border-collapse:collapse;font-size:.78rem;min-width:520px}',
      '.rcm-t th{position:sticky;top:0;background:#faf8f4;text-align:left;font-family:"DM Mono",monospace;font-size:.58rem;text-transform:uppercase;letter-spacing:.08em;color:#6b6760;padding:8px 10px;border-bottom:1px solid ' + BORDER + ';white-space:nowrap}',
      '.rcm-t td{padding:7px 10px;border-bottom:1px solid #f0ede7;white-space:nowrap;vertical-align:middle}',
      '.rcm-t td.r,.rcm-t th.r{text-align:right;font-family:"DM Mono",monospace}',
      '.rcm-t tr{cursor:pointer}',
      '.rcm-t tr:hover td{background:#faf8f4}',
      '.rcm-t tr.hit td{background:#fff6ee}',
      '.rcm-t .w{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:6px;vertical-align:-1px}',
      '.rcm-t .cb{font-size:.68rem;color:#6b6760;display:block;margin-top:1px;white-space:normal}',
      '.rcm-pop h4{margin:0 0 2px;font-size:.9rem;color:' + NAVY + '}',
      '.rcm-pop .sub{font-size:.7rem;color:#6b6760;margin-bottom:6px}',
      '.rcm-pop table{border-collapse:collapse;font-size:.78rem;width:100%}',
      '.rcm-pop td{padding:3px 6px 3px 0;vertical-align:top}',
      '.rcm-pop td.r{text-align:right;font-family:"DM Mono",monospace}',
      '.rcm-pop .mg{font-family:"DM Mono",monospace;font-size:.7rem;color:#6b6760;padding-top:5px}'
    ].join('');
    document.head.appendChild(s);
  }

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

  function init(host) {
    if (host.dataset.rcmReady || !window.L) return;
    host.dataset.rcmReady = '1';
    css();
    var scope = host.getAttribute('data-race-map'), want = host.getAttribute('data-contest');
    var colors = (host.getAttribute('data-colors') || '').split(',').filter(Boolean);
    var title = host.getAttribute('data-title') || '', when = host.getAttribute('data-date') || '';
    host.className = 'rcm';
    host.innerHTML =
      '<div class="rcm-head" data-head>Loading results\u2026</div>' +
      '<div class="rcm-find"><input type="search" placeholder="Search an address, or an ED like 44/17" autocomplete="off" data-q>' +
      '<button type="button" data-go>Find</button><button type="button" class="gh" data-rs>Reset</button></div>' +
      '<div class="rcm-map" data-map></div>' +
      '<div class="rcm-leg" data-leg></div>' +
      '<div class="rcm-note" data-note></div>' +
      '<div class="rcm-charts" data-charts></div>' +
      '<details class="rcm-dir" data-dir><summary><span data-dirttl>Every election district</span><span class="arr">&#9660;</span></summary>' +
      '<div class="flt"><input type="search" placeholder="Filter by ED, assembly district or community board" autocomplete="off" data-flt></div>' +
      '<div class="rcm-tw"><table class="rcm-t"><thead><tr><th>Election district</th><th data-th0></th><th data-th1></th><th data-th2></th><th class="r">Votes</th><th class="r">Margin</th></tr></thead><tbody data-rows></tbody></table></div></details>';

    var headEl = host.querySelector('[data-head]'), legEl = host.querySelector('[data-leg]'),
        noteEl = host.querySelector('[data-note]'), chartsEl = host.querySelector('[data-charts]'),
        qEl = host.querySelector('[data-q]'), rowsEl = host.querySelector('[data-rows]'),
        fltEl = host.querySelector('[data-flt]'), dirEl = host.querySelector('[data-dir]');

    var map = L.map(host.querySelector('[data-map]'), { scrollWheelZoom: false });
    L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 19, maxNativeZoom: 16, attribution: 'Esri, HERE, Garmin, &copy; OpenStreetMap contributors' }).addTo(map);
    L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 19, maxNativeZoom: 19, opacity: .85 }).addTo(map);

    var data, ci = -1, names = [], eds = [], layer = null, pin = null, home = null, byE = {}, lyrByE = {};

    function colorOf(i) { return colors[i] || (i === names.length - 1 && /write/i.test(names[i]) ? GREY : GREY); }
    function edLabel(e) { return 'AD ' + e.slice(0, 2) + ' ED ' + parseInt(e.slice(2), 10); }
    function cbLabel(p) { return (data.cbs || [])[p.b] || ''; }
    function alpha(m) { var t = Math.max(0, Math.min(1, m / 60)); return .22 + t * .68; }

    function styleFor(f) {
      var d = byE[f.properties.e];
      if (!d) return { color: '#fff', weight: .6, fillColor: '#ddd', fillOpacity: .3 };
      return { color: '#fff', weight: .8, fillColor: colorOf(d.win), fillOpacity: alpha(d.margin) };
    }

    function popup(d) {
      var h = '<div class="rcm-pop"><h4>' + esc(edLabel(d.e)) + '</h4><div class="sub">' + esc(cbLabel(d.p)) + '</div><table>';
      d.order.forEach(function (i) {
        if (!d.v[i]) return;
        h += '<tr><td><i class="w" style="display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:6px;background:' + colorOf(i) + '"></i>' +
          esc(names[i]) + '</td><td class="r">' + fmt(d.v[i]) + '</td><td class="r">' + pct(d.v[i], d.tot) + '</td></tr>';
      });
      h += '<tr><td class="mg" colspan="3">' + fmt(d.tot) + ' votes &middot; ' + esc(names[d.win]) + ' by ' + d.margin.toFixed(1) + ' points</td></tr>';
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

    fetch('/data/edresults/' + scope + '.json').then(function (r) { return r.json(); }).then(function (d) {
      data = d;
      for (var i = 0; i < d.contests.length; i++) if (d.contests[i].k === want) ci = i;
      if (ci < 0) { headEl.textContent = 'That contest is not in this file.'; return; }
      names = d.contests[ci].c;
      var totals = names.map(function () { return 0; }), won = names.map(function () { return 0; }), cast = 0;
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
        won[win]++; cast += tot;
      });
      var order = names.map(function (_, j) { return j; }).sort(function (a, b) { return totals[b] - totals[a]; });

      /* header */
      var h = '<div class="rcm-when">' + esc(when) + '</div><div class="rcm-title">' + esc(title) + '</div>';
      order.forEach(function (i) {
        if (!totals[i] || /write/i.test(names[i])) return;
        h += '<div class="rcm-cand"><span class="n"><i style="background:' + colorOf(i) + '"></i>' + esc(names[i]) + '</span>' +
          '<span class="p">' + pct(totals[i], cast) + '</span>' +
          '<span class="bar"><i style="width:' + (100 * totals[i] / cast).toFixed(1) + '%;background:' + colorOf(i) + '"></i></span>' +
          '<span class="s">' + fmt(totals[i]) + ' first choices' + (won[i] ? ' &middot; carried ' + won[i] + ' of ' + eds.length + ' election districts' : '') + '</span></div>';
      });
      h += '<div class="rcm-cand"><span class="s" style="margin-top:8px">' + fmt(cast) + ' ballots with a first choice across ' + eds.length + ' election districts. Shading deepens with the margin.</span></div>';
      headEl.innerHTML = h;

      /* legend */
      legEl.innerHTML = order.slice(0, 2).map(function (i) {
        return '<span><span class="g" style="background:linear-gradient(90deg,' + rgba(colorOf(i), alpha(0)) + ',' + rgba(colorOf(i), alpha(60)) + ')"></span>' +
          esc(names[i]) + ' margin, close to wide</span>';
      }).join('');

      /* map */
      layer = L.geoJSON(d, {
        style: styleFor,
        onEachFeature: function (f, l) {
          lyrByE[f.properties.e] = l;
          l.on('click', function () { var x = byE[f.properties.e]; if (x) openED(x); });
        }
      }).addTo(map);
      home = layer.getBounds();
      map.fitBounds(home, { padding: [12, 12] });
      noteEl.textContent = 'Tap any election district for its result, or search an address to find yours.';

      /* donuts */
      var lead = order[0], second = order[1];
      var edSl = [{ v: won[lead], c: colorOf(lead) }, { v: won[second], c: colorOf(second) }];
      var otherWon = eds.length - won[lead] - won[second];
      if (otherWon > 0) edSl.push({ v: otherWon, c: GREY });
      var voteSl = order.map(function (i) { return { v: totals[i], c: colorOf(i) }; });
      chartsEl.innerHTML =
        '<div class="rcm-chart"><div class="k">Election districts carried</div>' +
        donut(edSl, won[lead] + ' of ' + eds.length, names[lead].split(' ').pop()) +
        '<div class="lg"><span><i style="background:' + colorOf(lead) + '"></i>' + esc(names[lead]) + ' <b>' + won[lead] + '</b></span>' +
        '<span><i style="background:' + colorOf(second) + '"></i>' + esc(names[second]) + ' <b>' + won[second] + '</b></span>' +
        (otherWon > 0 ? '<span><i style="background:' + GREY + '"></i>Others <b>' + otherWon + '</b></span>' : '') + '</div></div>' +
        '<div class="rcm-chart"><div class="k">Share of first choices</div>' +
        donut(voteSl, pct(totals[lead], cast), names[lead].split(' ').pop()) +
        '<div class="lg">' + order.filter(function (i) { return totals[i]; }).map(function (i) {
          return '<span><i style="background:' + colorOf(i) + '"></i>' + esc(names[i]) + ' <b>' + pct(totals[i], cast) + '</b></span>';
        }).join('') + '</div></div>';

      /* directory */
      host.querySelector('[data-dirttl]').textContent = 'Every election district, all ' + eds.length;
      for (var t = 0; t < 3; t++) {
        var th = host.querySelector('[data-th' + t + ']');
        if (th) { th.textContent = order[t] != null ? names[order[t]] : ''; th.className = 'r'; }
      }
      eds.sort(function (a, b) { return a.e < b.e ? -1 : a.e > b.e ? 1 : 0; });
      rowsEl.innerHTML = eds.map(function (x) {
        var cells = '';
        for (var t = 0; t < 3; t++) {
          var i = order[t];
          cells += '<td class="r">' + (i == null ? '' : fmt(x.v[i]) + ' <span style="color:#6b6760">' + pct(x.v[i], x.tot) + '</span>') + '</td>';
        }
        return '<tr data-e="' + esc(x.e) + '" data-s="' + esc((edLabel(x.e) + ' ' + x.e.slice(0, 2) + '/' + parseInt(x.e.slice(2), 10) + ' ' + cbLabel(x.p) + ' ' + cbLabel(x.p).replace(/cb\s*(\d)/i, 'cb $1')).toLowerCase()) + '">' +
          '<td><i class="w" style="background:' + colorOf(x.win) + '"></i>' + esc(edLabel(x.e)) + '<span class="cb">' + esc(cbLabel(x.p)) + '</span></td>' +
          cells + '<td class="r">' + fmt(x.tot) + '</td>' +
          '<td class="r" style="color:' + colorOf(x.win) + ';font-weight:700">' + esc(names[x.win].split(' ').pop()) + ' +' + x.margin.toFixed(1) + '</td></tr>';
      }).join('');
      rowsEl.addEventListener('click', function (ev) {
        var tr = ev.target.closest('tr[data-e]'); if (!tr) return;
        var x = byE[tr.getAttribute('data-e')]; if (!x) return;
        openED(x);
        host.querySelector('[data-map]').scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
      fltEl.addEventListener('input', function () {
        var q = fltEl.value.trim().toLowerCase().replace(/\s+/g, ' ');
        Array.prototype.forEach.call(rowsEl.querySelectorAll('tr'), function (tr) {
          tr.style.display = !q || tr.getAttribute('data-s').indexOf(q) !== -1 ? '' : 'none';
        });
      });
      dirEl.addEventListener('toggle', function () { if (dirEl.open) setTimeout(function () { map.invalidateSize(); }, 50); });
    }).catch(function () { headEl.textContent = 'Results did not load.'; });

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
        noteEl.textContent = (label ? label + ' is in ' : 'That spot is in ') + edLabel(d.e) + ', ' + cbLabel(d.p) + '.';
        dirEl.open = true;
        var tr = rowsEl.querySelector('tr[data-e="' + d.e + '"]');
        if (tr) { fltEl.value = ''; Array.prototype.forEach.call(rowsEl.querySelectorAll('tr'), function (r) { r.style.display = ''; }); tr.scrollIntoView({ block: 'center' }); }
      } else {
        map.setView([lat, lng], 15);
        noteEl.textContent = (label || 'That spot') + ' is outside the district.';
      }
    }
    function find() {
      var q = (qEl.value || '').trim(); if (!q || !data) return;
      var m = q.match(/^\s*(\d{1,2})\s*[\/\-\s]\s*(\d{1,3})\s*$/);
      if (m) {
        var d = byE[m[1].padStart(2, '0') + m[2].padStart(3, '0')];
        if (d) { openED(d); noteEl.textContent = edLabel(d.e) + ', ' + cbLabel(d.p) + '.'; dirEl.open = true; return; }
        noteEl.textContent = 'No election district ' + q + ' in this district.';
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
      map.closePopup(); if (home) map.fitBounds(home, { padding: [12, 12] });
      Array.prototype.forEach.call(rowsEl.querySelectorAll('tr'), function (tr) { tr.classList.remove('hit'); });
      noteEl.textContent = 'Tap any election district for its result, or search an address to find yours.';
    });
  }

  function boot() {
    if (!window.L) return;
    Array.prototype.forEach.call(document.querySelectorAll('[data-race-map]'), init);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
