/* CB6 & Beyond - Education hub (bkcb6.app/eduhub)
   Data: NYC Dept. of City Planning Facilities Database (FacDB), ji82-xba5 */
(function () {
  'use strict';
  var BASE = 'data/eduhub/';
  var CAT = { school: 'Schools', childcare: 'Childcare & pre-K', library: 'Libraries' };
  var COLOR = { school: '#06024D', childcare: '#f47920', library: '#1a7f8e' };
  var BORO = { mn: 'Manhattan', bx: 'Bronx', bk: 'Brooklyn', qn: 'Queens', si: 'Staten Island' };
  var active = { school: true, childcare: true, library: true };
  var query = '';
  var items = [], map = null, layer = null, markers = [], boundary = null;

  function $(s, r) { return (r || document).querySelector(s); }
  function el(t, c, tx) { var e = document.createElement(t); if (c) e.className = c; if (tx != null) e.textContent = tx; return e; }
  function num(n) { return (n || 0).toLocaleString('en-US'); }
  function esc(s) { return String(s == null ? '' : s); }
  var KEEP = /^(P\.S\.|I\.S\.|M\.S\.|J\.H\.S\.|PS|IS|MS|HS|JHS|YMCA|YWCA|YM-YWHA|NYC|DOE|CUNY|SUNY|KIPP|UPK|LLC|INC|LTD|UFT|HRA|ACS|NYPL|BPL|QPL|II|III|IV|VI|VII|VIII|IX|XI|XII)$/;
  function titleWord(w) {
    if (!w) return w;
    if (/^\d/.test(w)) return w.toLowerCase();
    var bare = w.replace(/[^A-Za-z.\-']/g, '');
    if (KEEP.test(bare.toUpperCase())) return bare.toUpperCase() === bare ? w : w.toUpperCase();
    if (bare.length > 1 && !/[AEIOUY]/i.test(bare)) return w.toUpperCase();
    return w.charAt(0).toUpperCase() + w.slice(1).toLowerCase();
  }
  function title(s) {
    return esc(s).split(/(\s+)/).map(function (w) {
      return /\s/.test(w) ? w : w.split('-').map(titleWord).join('-');
    }).join('');
  }

  function get(url) {
    return fetch(url, { cache: 'no-cache' }).then(function (r) {
      if (!r.ok) throw new Error(url + ' returned ' + r.status);
      return r.json();
    });
  }

  /* ---------- map ---------- */
  function initMap(center, zoom) {
    map = L.map('map', { scrollWheelZoom: false, zoomControl: true }).setView(center, zoom);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap contributors, &copy; CARTO', maxZoom: 19, subdomains: 'abcd'
    }).addTo(map);
    layer = L.layerGroup().addTo(map);
    map.on('click', function () { map.scrollWheelZoom.enable(); });
    return map;
  }

  function drawMarkers(list) {
    layer.clearLayers();
    markers = [];
    var renderer = L.canvas({ padding: 0.5 });
    list.forEach(function (it) {
      if (it.lat == null || it.lon == null) return;
      var m = L.circleMarker([it.lat, it.lon], {
        renderer: renderer, radius: it.c === 'library' ? 7 : 5,
        color: '#fff', weight: 1.2, fillColor: COLOR[it.c], fillOpacity: 0.9
      });
      var html = '<strong>' + title(it.n) + '</strong><br>' +
        '<span style="color:#5a5f7a">' + esc(it.s) + '</span><br>' + title(it.a) +
        (it.z ? ', ' + esc(it.z) : '') +
        (it.cap ? '<br>Reported capacity: ' + num(it.cap) : '') +
        (it.op && it.op.toLowerCase() !== title(it.n).toLowerCase() ? '<br>Operated by ' + esc(it.op) : '');
      m.bindPopup(html);
      m.addTo(layer);
      it._m = m;
      markers.push(m);
    });
  }

  function matches(it) {
    if (!active[it.c]) return false;
    if (!query) return true;
    var q = query.toLowerCase();
    return (it.n + ' ' + it.a + ' ' + it.s + ' ' + (it.op || '') + ' ' + (it.z || '')).toLowerCase().indexOf(q) > -1;
  }

  /* ---------- controls ---------- */
  function wireControls(onChange) {
    var box = $('#q');
    if (box) {
      box.addEventListener('input', function () { query = box.value.trim(); onChange(); });
    }
    Array.prototype.forEach.call(document.querySelectorAll('.chip[data-cat]'), function (c) {
      c.addEventListener('click', function () {
        var k = c.getAttribute('data-cat');
        active[k] = !active[k];
        c.setAttribute('aria-pressed', active[k] ? 'true' : 'false');
        onChange();
      });
    });
  }

  /* ---------- district page ---------- */
  function district(cd) {
    var wrapEl = $('#cards');
    Promise.all([get(BASE + cd + '.json'), get(BASE + 'districts.geojson'),
                 get(BASE + 'csd-summary.json'), get(BASE + 'school-districts.geojson')])
      .then(function (res) {
        var d = res[0], gj = res[1], cs = res[2], sd = res[3];
        items = d.items;
        initMap([40.7, -73.95], 12);
        var f = gj.features.filter(function (x) { return x.properties.cd === cd; });
        boundary = L.geoJSON({ type: 'FeatureCollection', features: f }, {
          style: { color: '#06024D', weight: 2, fill: true, fillColor: '#06024D', fillOpacity: 0.05, dashArray: '4 3' }
        }).addTo(map);
        map.fitBounds(boundary.getBounds(), { padding: [16, 16] });
        var rows = cs.by_cd[cd] || [];
        var only = { type: 'FeatureCollection', features: sd.features.filter(function (x) {
          return rows.some(function (r) { return r.csd === x.properties.csd; }); }) };
        var csdLayer = csdOverlay(only, null);
        var tog = $('#csd-toggle');
        if (tog) {
          tog.addEventListener('click', function () {
            var on = tog.getAttribute('aria-pressed') === 'true';
            if (on) { map.removeLayer(csdLayer); tog.setAttribute('aria-pressed', 'false'); }
            else { csdLayer.addTo(map); tog.setAttribute('aria-pressed', 'true'); }
          });
        }
        var host = $('#cd-overlap');
        if (host) {
          host.innerHTML = '';
          host.appendChild(overlapTable(rows, 'byCd'));
        }
        var lead = $('#overlap-lead');
        if (lead) {
          lead.textContent = rows.length === 1
            ? 'This community district sits entirely inside one school district.'
            : 'This community district is split across ' + rows.length + ' school districts.';
        }
        drawMarkers(items);
        wireControls(render);
        render();
      })
      .catch(function (e) {
        if (wrapEl) wrapEl.innerHTML = '<div class="empty">Could not load district data. ' + esc(e.message) + '</div>';
      });

    function render() {
      var vis = items.filter(matches);
      markers.forEach(function (m) { layer.removeLayer(m); });
      vis.forEach(function (it) { if (it._m) it._m.addTo(layer); });
      var counts = { school: 0, childcare: 0, library: 0, prek: 0 };
      vis.forEach(function (it) { counts[it.c]++; if (it.s === 'Pre-K / 3-K') counts.prek++; });
      setText('#c-total', num(vis.length));
      setText('#c-school', num(counts.school));
      setText('#c-childcare', num(counts.childcare));
      setText('#c-library', num(counts.library));
      setText('#c-prek', num(counts.prek));
      var host = $('#cards');
      host.innerHTML = '';
      if (!vis.length) { host.innerHTML = '<div class="empty">No sites match this filter. Clear the search box or turn a category back on.</div>'; return; }
      vis.forEach(function (it) {
        var c = el('div', 'card');
        c.appendChild(el('span', 'tag ' + it.c, it.s));
        c.appendChild(el('h3', null, title(it.n)));
        var m = el('div', 'meta');
        m.innerHTML = title(it.a) + (it.z ? ', ' + esc(it.z) : '') +
          (it.cap ? '<br>Reported capacity ' + num(it.cap) : '') +
          (it.ot ? '<br>' + esc(it.ot) : '');
        c.appendChild(m);
        c.addEventListener('click', function () {
          if (!it._m) return;
          map.setView([it.lat, it.lon], 17);
          it._m.openPopup();
          document.getElementById('map').scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
        host.appendChild(c);
      });
    }
  }

  function setText(sel, v) { var e = $(sel); if (e) e.textContent = v; }

  /* ---------- school district (CSD) pages ---------- */
  function csdOverlay(gj, only) {
    var f = only == null ? gj.features : gj.features.filter(function (x) { return x.properties.csd === only; });
    return L.geoJSON({ type: 'FeatureCollection', features: f }, {
      style: { color: '#7a3ea8', weight: 2, fill: false, dashArray: '5 4', opacity: 0.85 },
      onEachFeature: function (ft, l) { l.bindTooltip(ft.properties.name, { sticky: true }); }
    });
  }

  function overlapTable(rows, mode) {
    var t = document.createElement('table');
    var heads = mode === 'byCd'
      ? ['School district', 'Share of this community district', 'Share of that school district', 'Square miles', 'Education sites']
      : ['Community district', 'Share of this school district', 'Share of that community district', 'Square miles', 'Education sites'];
    var tr = t.createTHead().insertRow();
    heads.forEach(function (h, i) {
      var th = document.createElement('th');
      if (i > 0) th.className = 'num';
      th.textContent = h; tr.appendChild(th);
    });
    var tb = t.createTBody();
    rows.forEach(function (r) {
      var row = tb.insertRow();
      var c0 = row.insertCell();
      if (mode === 'byCd') c0.innerHTML = '<a href="eduhub-csd-' + r.csd + '">CSD ' + r.csd + '</a>';
      else c0.innerHTML = '<a href="eduhub-' + r.cd + '">' + cdLabel(r.cd) + '</a>';
      var a = mode === 'byCd' ? r.pct_of_cd : r.pct_of_csd;
      var b = mode === 'byCd' ? r.pct_of_csd : r.pct_of_cd;
      [a.toFixed(1) + '%', b.toFixed(1) + '%', r.sqmi.toFixed(2), num(r.sites)].forEach(function (v) {
        var td = row.insertCell(); td.className = 'num'; td.textContent = v;
      });
    });
    return t;
  }

  function cdLabel(cd) {
    var p = cd.split('-');
    return BORO[p[0]] + ' CD ' + p[1];
  }

  function csdPage(n) {
    Promise.all([get(BASE + 'csd-' + n + '.json'), get(BASE + 'csd-summary.json'),
                 get(BASE + 'school-districts.geojson'), get(BASE + 'districts.geojson')])
      .then(function (res) {
        var d = res[0], s = res[1], sd = res[2], cdgj = res[3];
        var meta = s.csds.filter(function (x) { return x.csd === n; })[0];
        items = d.items;
        initMap([40.7, -73.95], 12);
        var cdKeys = meta.cds.map(function (x) { return x.cd; });
        L.geoJSON({ type: 'FeatureCollection', features: cdgj.features.filter(function (f) { return cdKeys.indexOf(f.properties.cd) > -1; }) }, {
          style: { color: '#06024D', weight: 1.4, fill: true, fillColor: '#06024D', fillOpacity: 0.04 },
          onEachFeature: function (ft, l) { l.bindTooltip(ft.properties.name, { sticky: true }); }
        }).addTo(map);
        boundary = csdOverlay(sd, n).addTo(map);
        map.fitBounds(boundary.getBounds(), { padding: [16, 16] });
        drawMarkers(items);
        var host = $('#csd-overlap');
        if (host) { host.innerHTML = ''; host.appendChild(overlapTable(meta.cds, 'byCsd')); }
        wireControls(render);
        render();
      })
      .catch(function (e) {
        var t = $('#csd-status');
        if (t) t.textContent = 'Could not load school district data. ' + e.message;
      });

    function render() {
      var vis = items.filter(matches);
      markers.forEach(function (m) { layer.removeLayer(m); });
      vis.forEach(function (it) { if (it._m) it._m.addTo(layer); });
      var c = { school: 0, childcare: 0, library: 0, prek: 0 };
      vis.forEach(function (it) { c[it.c]++; if (it.s === 'Pre-K / 3-K') c.prek++; });
      setText('#c-total', num(vis.length));
      setText('#c-school', num(c.school));
      setText('#c-childcare', num(c.childcare));
      setText('#c-prek', num(c.prek));
      setText('#c-library', num(c.library));
    }
  }

  function csdHub() {
    Promise.all([get(BASE + 'csd-summary.json'), get(BASE + 'all.json'),
                 get(BASE + 'school-districts.geojson'), get(BASE + 'districts.geojson'),
                 get(BASE + 'summary.json')])
      .then(function (res) {
        var s = res[0]; items = res[1];
        res[4].districts.forEach(function (d) { cdName[d.cd] = d.name; });
        buildCsdStats(s);
        buildCsdTable(s);
        buildCrosswalk(s);
        buildCsdIndex(s);
        buildCsdAudit(s);
        initMap([40.7128, -73.94], 11);
        L.geoJSON(res[3], { style: { color: '#06024D', weight: 0.8, fill: false, opacity: 0.35 } }).addTo(map);
        csdOverlay(res[2], null).addTo(map);
        drawMarkers(items);
        wireControls(renderMap);
        renderMap();
      })
      .catch(function (e) {
        var t = $('#csdhub-status');
        if (t) t.textContent = 'Could not load school district data. ' + e.message;
      });

    function renderMap() {
      var vis = items.filter(matches);
      markers.forEach(function (m) { layer.removeLayer(m); });
      vis.forEach(function (it) { if (it._m) it._m.addTo(layer); });
      setText('#map-count', num(vis.length));
    }

    function buildCsdStats(s) {
      var host = $('#csdstats'); host.innerHTML = '';
      var sch = 0, cc = 0, lib = 0;
      s.csds.forEach(function (c) { sch += c.school; cc += c.childcare; lib += c.library; });
      [['all', s.in_csd, 'Sites in a school district'], ['all', s.csds.length, 'Community school districts'],
       ['school', sch, 'Schools'], ['childcare', cc, 'Childcare & pre-K'], ['library', lib, 'Public libraries']]
        .forEach(function (r) {
          var d = el('div', 'stat ' + r[0]);
          d.appendChild(el('div', 'v', num(r[1])));
          d.appendChild(el('div', 'l', r[2]));
          host.appendChild(d);
        });
    }

    function buildCsdTable(s) {
      var host = $('#csdtable');
      var t = document.createElement('table');
      var heads = ['School district', 'Square miles', 'Community districts', 'Schools', 'Public K-12', 'Charter', 'Private', 'Special ed', 'Childcare', 'Pre-K / 3-K', 'Libraries', 'All sites'];
      var tr = t.createTHead().insertRow();
      heads.forEach(function (h, i) {
        var th = document.createElement('th');
        if (i > 0) th.className = 'num';
        th.textContent = h; th.tabIndex = 0;
        th.addEventListener('click', function () { sortTable(t, i, th); });
        th.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); sortTable(t, i, th); } });
        tr.appendChild(th);
      });
      var tb = t.createTBody();
      s.csds.forEach(function (c) {
        var row = tb.insertRow();
        var c0 = row.insertCell();
        c0.innerHTML = '<a href="eduhub-csd-' + c.csd + '">CSD ' + c.csd + '</a>';
        c0.dataset.v = c.csd;
        [c.sqmi.toFixed(2), c.cds.length, c.school, c['sub::Public K-12'], c['sub::Charter'],
         c['sub::Private / parochial'], c['sub::Special education'], c.childcare,
         c['sub::Pre-K / 3-K'], c.library, c.total].forEach(function (v) {
          var td = row.insertCell(); td.className = 'num';
          td.textContent = typeof v === 'number' ? num(v) : v;
          td.dataset.v = parseFloat(v);
        });
      });
      host.innerHTML = ''; host.appendChild(t);
    }

    function buildCrosswalk(s) {
      var host = $('#crosswalk');
      var t = document.createElement('table');
      var tr = t.createTHead().insertRow();
      ['Community district', 'Area', 'School districts it covers', 'Split'].forEach(function (h, i) {
        var th = document.createElement('th');
        th.textContent = h; tr.appendChild(th);
      });
      var tb = t.createTBody();
      Object.keys(s.by_cd).forEach(function (cd) {
        var rows = s.by_cd[cd];
        var row = tb.insertRow();
        row.insertCell().innerHTML = '<a href="eduhub-' + cd + '">' + cdLabel(cd) + '</a>';
        row.insertCell().textContent = cdName[cd] || '';
        var c2 = row.insertCell();
        c2.innerHTML = rows.map(function (r) {
          return '<a href="eduhub-csd-' + r.csd + '">CSD ' + r.csd + '</a> ' + r.pct_of_cd.toFixed(0) + '%';
        }).join(' &middot; ');
        c2.style.whiteSpace = 'normal';
        row.insertCell().textContent = rows.length === 1 ? 'whole district' : rows.length + ' school districts';
      });
      host.innerHTML = ''; host.appendChild(t);
      var box = $('#xq');
      if (box) box.addEventListener('input', function () {
        var q = box.value.trim().toLowerCase();
        Array.prototype.forEach.call(tb.rows, function (r) {
          r.style.display = !q || r.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none';
        });
      });
    }

    function buildCsdIndex(s) {
      var host = $('#csdindex'); host.innerHTML = '';
      var g = el('div', 'districtgrid');
      s.csds.forEach(function (c) {
        var a = el('a', 'dlink');
        a.href = 'eduhub-csd-' + c.csd;
        a.appendChild(el('b', null, 'CSD ' + c.csd));
        a.appendChild(el('span', null, num(c.total) + ' sites  /  ' + num(c.school) + ' schools  /  ' + c.cds.length + ' community districts'));
        g.appendChild(a);
      });
      host.appendChild(g);
    }

    function buildCsdAudit(s) {
      var host = $('#csdaudit');
      host.innerHTML = '';
      host.appendChild(el('p', 'note',
        'Source records: ' + num(s.record_count) + '. Placed in a school district: ' + num(s.in_csd) + '. ' +
        'Not placeable: ' + num(s.no_csd) + '. ' + num(s.in_csd) + ' + ' + num(s.no_csd) + ' = ' + num(s.record_count) + '.'));
      if (s.no_csd_records && s.no_csd_records.length) {
        var ul = el('ul', 'note');
        s.no_csd_records.forEach(function (r) {
          ul.appendChild(el('li', null, title(r.name) + ' (' + r.sub + ', ZIP ' + r.zip + '): ' + r.note));
        });
        host.appendChild(ul);
      }
    }

    function sortTable(t, i, th) {
      var cur = th.getAttribute('aria-sort');
      var asc = cur === 'ascending' ? false : (cur === 'descending' ? true : i === 0);
      Array.prototype.forEach.call(t.tHead.rows[0].cells, function (c) { c.removeAttribute('aria-sort'); });
      th.setAttribute('aria-sort', asc ? 'ascending' : 'descending');
      var tb = t.tBodies[0];
      var rows = Array.prototype.slice.call(tb.rows);
      rows.sort(function (a, b) {
        var x = parseFloat(a.cells[i].dataset.v), y = parseFloat(b.cells[i].dataset.v);
        if (x < y) return asc ? -1 : 1;
        if (x > y) return asc ? 1 : -1;
        return 0;
      });
      rows.forEach(function (r) { tb.appendChild(r); });
    }
  }

  var cdName = {};

  /* ---------- borough page ---------- */
  function borough(b) {
    Promise.all([get(BASE + 'boro-' + b + '.json'), get(BASE + 'summary.json'), get(BASE + 'districts.geojson')])
      .then(function (res) {
        var d = res[0], s = res[1], gj = res[2];
        items = d.items;
        initMap([40.7, -73.95], 11);
        var f = gj.features.filter(function (x) { return x.properties.cd.indexOf(b + '-') === 0; });
        boundary = L.geoJSON({ type: 'FeatureCollection', features: f }, {
          style: { color: '#06024D', weight: 1.6, fill: true, fillColor: '#06024D', fillOpacity: 0.04 },
          onEachFeature: function (ft, l) { l.bindTooltip(ft.properties.name, { sticky: true }); }
        }).addTo(map);
        map.fitBounds(boundary.getBounds(), { padding: [14, 14] });
        drawMarkers(items);
        buildBoroTable(s, b);
        wireControls(render);
        render();
      })
      .catch(function (e) {
        var t = $('#boro-status');
        if (t) t.textContent = 'Could not load borough data. ' + e.message;
      });

    function render() {
      var vis = items.filter(matches);
      markers.forEach(function (m) { layer.removeLayer(m); });
      vis.forEach(function (it) { if (it._m) it._m.addTo(layer); });
      var c = { school: 0, childcare: 0, library: 0, prek: 0 };
      vis.forEach(function (it) { c[it.c]++; if (it.s === 'Pre-K / 3-K') c.prek++; });
      setText('#c-total', num(vis.length));
      setText('#c-school', num(c.school));
      setText('#c-childcare', num(c.childcare));
      setText('#c-prek', num(c.prek));
      setText('#c-library', num(c.library));
    }

    function buildBoroTable(s, b) {
      var host = $('#boro-districts');
      if (!host) return;
      var ds = s.districts.filter(function (d) { return d.boro === b; });
      var t = document.createElement('table');
      var heads = ['District', 'Area', 'Schools', 'Public K-12', 'Charter', 'Private', 'Special ed', 'Childcare', 'Pre-K / 3-K', 'Libraries', 'All sites', 'School districts'];
      var tr = t.createTHead().insertRow();
      heads.forEach(function (h, i) {
        var th = document.createElement('th');
        if (i > 1) th.className = 'num';
        th.textContent = h; tr.appendChild(th);
      });
      var tb = t.createTBody();
      ds.forEach(function (d) {
        var row = tb.insertRow();
        var c0 = row.insertCell();
        c0.innerHTML = '<a href="eduhub-' + d.cd + '">CD ' + d.num + '</a>';
        row.insertCell().textContent = d.name;
        [d.school, d['sub::Public K-12'], d['sub::Charter'], d['sub::Private / parochial'],
         d['sub::Special education'], d.childcare, d['sub::Pre-K / 3-K'], d.library, d.total].forEach(function (v) {
          var td = row.insertCell(); td.className = 'num'; td.textContent = num(v);
        });
        row.insertCell().textContent = d.csd.length ? d.csd.join(', ') : 'not published';
      });
      host.innerHTML = ''; host.appendChild(t);
    }
  }

  /* ---------- hub page ---------- */
  function hub() {
    Promise.all([get(BASE + 'summary.json'), get(BASE + 'all.json'), get(BASE + 'districts.geojson')])
      .then(function (res) {
        var s = res[0]; items = res[1];
        buildStats(s);
        buildBorough(s);
        buildTable(s);
        buildIndex(s);
        buildAudit(s);
        initMap([40.7128, -73.94], 11);
        L.geoJSON(res[2], {
          style: { color: '#06024D', weight: 1, fill: false, opacity: 0.45 },
          onEachFeature: function (f, l) { l.bindTooltip(f.properties.name, { sticky: true }); }
        }).addTo(map);
        drawMarkers(items);
        wireControls(renderMap);
        renderMap();
      })
      .catch(function (e) {
        var t = $('#hub-status');
        if (t) t.textContent = 'Could not load the citywide data. ' + e.message;
      });

    function renderMap() {
      var vis = items.filter(matches);
      markers.forEach(function (m) { layer.removeLayer(m); });
      vis.forEach(function (it) { if (it._m) it._m.addTo(layer); });
      setText('#map-count', num(vis.length));
    }

    function buildStats(s) {
      var c = s.citywide;
      var host = $('#citystats'); host.innerHTML = '';
      [['all', c.total, 'Sites citywide'], ['school', c.school, 'Schools'],
       ['childcare', c.childcare, 'Childcare & pre-K'], ['childcare', c['sub::Pre-K / 3-K'], 'DOE pre-K / 3-K sites'],
       ['library', c.library, 'Public libraries']].forEach(function (r) {
        var d = el('div', 'stat ' + r[0]);
        d.appendChild(el('div', 'v', num(r[1])));
        d.appendChild(el('div', 'l', r[2]));
        host.appendChild(d);
      });
    }

    function buildBorough(s) {
      var host = $('#boroughtable');
      var rows = Object.keys(BORO).map(function (b) {
        var v = s.borough[b]; v.key = b; v.name = BORO[b]; return v;
      });
      var t = tableEl(['Borough', 'Districts', 'Schools', 'Childcare & pre-K', 'Pre-K / 3-K', 'Libraries', 'All sites'],
        rows.map(function (r) {
          var n = s.districts.filter(function (d) { return d.boro === r.key; }).length;
          return ['<a href="eduhub-' + r.key + '">' + r.name + '</a>', n,
                  r.school, r.childcare, r['sub::Pre-K / 3-K'], r.library, r.total];
        }), 0);
      host.innerHTML = ''; host.appendChild(t);
    }

    function buildTable(s) {
      var host = $('#districttable');
      var rows = s.districts.map(function (d) {
        return [
          '<a href="eduhub-' + d.cd + '">' + d.boroname + ' CD ' + d.num + '</a>',
          d.name, d.school, d['sub::Public K-12'], d['sub::Charter'], d['sub::Private / parochial'],
          d['sub::Special education'], d.childcare, d['sub::Pre-K / 3-K'], d.library, d.total,
          d.csd.length ? d.csd.join(', ') : 'not published'
        ];
      });
      var t = tableEl(['District', 'Area', 'Schools', 'Public K-12', 'Charter', 'Private', 'Special ed', 'Childcare', 'Pre-K / 3-K', 'Libraries', 'All sites', 'School districts'], rows, 0);
      var order = ['mn', 'bx', 'bk', 'qn', 'si'];
      Array.prototype.forEach.call(t.tBodies[0].rows, function (tr, k) {
        var d = s.districts[k];
        tr.cells[0].dataset.v = order.indexOf(d.boro) * 100 + d.num;
      });
      host.innerHTML = ''; host.appendChild(t);
      var box = $('#dq');
      box.addEventListener('input', function () {
        var q = box.value.trim().toLowerCase();
        Array.prototype.forEach.call(t.tBodies[0].rows, function (tr) {
          tr.style.display = !q || tr.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none';
        });
      });
    }

    function buildIndex(s) {
      var host = $('#dindex'); host.innerHTML = '';
      Object.keys(BORO).forEach(function (b) {
        var bh = el('div', 'borohead');
        var bl = el('a', null, BORO[b] + '  (borough page)');
        bl.href = 'eduhub-' + b;
        bl.style.color = 'inherit';
        bh.appendChild(bl);
        host.appendChild(bh);
        var g = el('div', 'districtgrid');
        s.districts.filter(function (d) { return d.boro === b; }).forEach(function (d) {
          var a = el('a', 'dlink');
          a.href = 'eduhub-' + d.cd;
          a.appendChild(el('b', null, 'CD ' + d.num + '  ' + d.name));
          a.appendChild(el('span', null, num(d.total) + ' sites  /  ' + num(d.school) + ' schools  /  ' + num(d.library) + ' libraries'));
          g.appendChild(a);
        });
        host.appendChild(g);
      });
    }

    function buildAudit(s) {
      var host = $('#audit');
      var lines = ['Source records pulled: ' + num(s.record_count) + '.',
        'Placed in a community district: ' + num(s.assigned) + '.',
        'Of those, ' + num(s.mapped) + ' have coordinates and appear on the maps; ' + num(s.assigned_no_coords) + (s.assigned_no_coords === 1 ? ' appears' : ' appear') + ' in a district directory only.',
        'Not placeable to any district: ' + num(s.unassigned) + '.',
        num(s.mapped) + ' + ' + num(s.assigned_no_coords) + ' + ' + num(s.unassigned) + ' = ' + num(s.record_count) + '.'];
      var p = el('p', 'note', lines.join(' '));
      host.innerHTML = ''; host.appendChild(p);
      var ul = el('ul', 'note');
      (s.no_coord_records || []).forEach(function (r) {
        ul.appendChild(el('li', null, title(r.name) + ' (' + r.sub + ', ' + r.cd.toUpperCase() + '): ' + r.note));
      });
      (s.unassigned_records || []).forEach(function (r) {
        ul.appendChild(el('li', null, title(r.name) + ' (' + r.sub + ', ZIP ' + r.zip + '): ' + r.note));
      });
      if (ul.children.length) host.appendChild(ul);
    }

    function tableEl(heads, rows, sortCol) {
      var t = document.createElement('table');
      var thead = t.createTHead(), tr = thead.insertRow();
      heads.forEach(function (h, i) {
        var th = document.createElement('th');
        if (i > 1) th.className = 'num';
        th.textContent = h;
        th.tabIndex = 0;
        th.addEventListener('click', function () { sortBy(t, i, th); });
        th.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); sortBy(t, i, th); } });
        tr.appendChild(th);
      });
      var tb = t.createTBody();
      rows.forEach(function (r) {
        var row = tb.insertRow();
        r.forEach(function (v, i) {
          var td = row.insertCell();
          if (i > 1 && typeof v === 'number') { td.className = 'num'; td.textContent = num(v); td.dataset.v = v; }
          else if (typeof v === 'string' && v.indexOf('<a') === 0) { td.innerHTML = v; }
          else { td.textContent = v; }
        });
      });
      return t;
    }

    function sortBy(t, i, th) {
      var cur = th.getAttribute('aria-sort');
      var numeric = th.classList.contains('num');
      var asc = cur === 'ascending' ? false : (cur === 'descending' ? true : !numeric);
      Array.prototype.forEach.call(t.tHead.rows[0].cells, function (c) { c.removeAttribute('aria-sort'); });
      th.setAttribute('aria-sort', asc ? 'ascending' : 'descending');
      var tb = t.tBodies[0];
      var rows = Array.prototype.slice.call(tb.rows);
      rows.sort(function (a, b) {
        var x = a.cells[i], y = b.cells[i];
        var xv = x.dataset.v != null ? +x.dataset.v : x.textContent.trim().toLowerCase();
        var yv = y.dataset.v != null ? +y.dataset.v : y.textContent.trim().toLowerCase();
        if (xv < yv) return asc ? -1 : 1;
        if (xv > yv) return asc ? 1 : -1;
        return 0;
      });
      rows.forEach(function (r) { tb.appendChild(r); });
    }
  }

  window.EDU = { hub: hub, district: district, borough: borough, csdHub: csdHub, csdPage: csdPage };
})();
