/* CB6 & Beyond - Education hub (bkcb6.app/eduhub)
   Data: NYC Dept. of City Planning Facilities Database (FacDB), ji82-xba5
   Schools and childcare / pre-K. Public libraries live on a separate hub. */
(function () {
  'use strict';
  var BASE = 'data/eduhub/';
  var BORO = { mn: 'Manhattan', bx: 'Bronx', bk: 'Brooklyn', qn: 'Queens', si: 'Staten Island' };

  /* One colour per school level, plus childcare. Every colour appears in the key. */
  var LEVEL = {
    'Elementary':          { c: '#1b6ca8', g: 'school', k: 'Elementary school' },
    'K-8':                 { c: '#4b9fd5', g: 'school', k: 'K-8 school' },
    'Middle':              { c: '#0f766e', g: 'school', k: 'Middle school' },
    'Secondary (6-12)':    { c: '#7a3ea8', g: 'cap',    k: 'Secondary school, grades 6-12' },
    'High school':         { c: '#06024D', g: 'cap',    k: 'High school' },
    'K-12':                { c: '#b4436c', g: 'cap',    k: 'K-12 school, all grades' },
    'Level not published': { c: '#8a8f9e', g: 'school', k: 'School, grade level not published' }
  };
  var LEVEL_ORDER = ['Elementary', 'K-8', 'Middle', 'Secondary (6-12)', 'High school', 'K-12', 'Level not published'];
  var CHILDCARE = { c: '#f47920', g: 'child', k: 'Childcare, day care & pre-K' };
  var ZOOM_FOR_SITES = 14;

  /* Glyphs: schoolhouse, graduation cap, child. Drawn white on the level colour. */
  var GLYPH = {
    school: '<path d="M12 3 3 8v2h18V8zM5 11v7H3v2h18v-2h-2v-7h-2v7h-3v-7h-2v7H7v-7z"/>',
    cap: '<path d="M12 3 1 8l11 5 9-4.1V15h2V8zM5 12.2V16c0 1.7 3.1 3 7 3s7-1.3 7-3v-3.8l-7 3.2z"/>',
    child: '<path d="M12 2a3 3 0 1 1 0 6 3 3 0 0 1 0-6zM7.5 9h9A2.5 2.5 0 0 1 19 11.5V15h-2v6h-2v-6h-2v6H9v-6H7v-3.5A2.5 2.5 0 0 1 7.5 9z"/>'
  };

  var active = { school: true, childcare: true };
  var levelOn = {};
  LEVEL_ORDER.forEach(function (l) { levelOn[l] = true; });
  var query = '';
  var items = [], map = null, siteLayer = null, shapeLayer = null, markers = [];
  var siteMode = 'auto', forceSites = false;

  function $(s, r) { return (r || document).querySelector(s); }
  function el(t, c, tx) { var e = document.createElement(t); if (c) e.className = c; if (tx != null) e.textContent = tx; return e; }
  function num(n) { return (n || 0).toLocaleString('en-US'); }
  function esc(s) { return String(s == null ? '' : s); }

  var KEEP = /^(P\.S\.|I\.S\.|M\.S\.|J\.H\.S\.|PS|IS|MS|HS|JHS|YMCA|YWCA|NYC|DOE|CUNY|SUNY|KIPP|UPK|LLC|INC|LTD|ACS|II|III|IV|VI|VII|VIII|IX|XI|XII)$/;
  function titleWord(w) {
    if (!w) return w;
    if (/^\d/.test(w)) return w.toLowerCase();
    var bare = w.replace(/[^A-Za-z.\-']/g, '');
    if (KEEP.test(bare.toUpperCase())) return w.toUpperCase();
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

  function styleFor(it) {
    if (it.c === 'childcare') return CHILDCARE;
    return LEVEL[it.lvl] || LEVEL['Level not published'];
  }
  function labelFor(it) {
    return it.c === 'childcare' ? it.s : (it.lvl || 'Level not published');
  }

  function pinIcon(st) {
    var html = '<span class="pin" style="--pin:' + st.c + '">' +
      '<span class="pin-head"><svg viewBox="0 0 24 24" aria-hidden="true">' + GLYPH[st.g] + '</svg></span>' +
      '<span class="pin-tip"></span></span>';
    return L.divIcon({ className: 'pin-wrap', html: html, iconSize: [30, 38], iconAnchor: [15, 38], popupAnchor: [0, -34] });
  }

  /* ---------- map ---------- */
  function initMap(center, zoom) {
    map = L.map('map', { scrollWheelZoom: false, zoomControl: true }).setView(center, zoom);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap contributors, &copy; CARTO', maxZoom: 19, subdomains: 'abcd'
    }).addTo(map);
    shapeLayer = L.layerGroup().addTo(map);
    siteLayer = L.layerGroup().addTo(map);
    map.on('click', function () { map.scrollWheelZoom.enable(); });
    return map;
  }

  function buildMarkers(list) {
    markers = [];
    list.forEach(function (it) {
      if (it.lat == null || it.lon == null) return;
      var st = styleFor(it);
      var m = L.marker([it.lat, it.lon], { icon: pinIcon(st), riseOnHover: true });
      m.bindPopup('<strong>' + title(it.n) + '</strong><br>' +
        '<span style="color:#5a5f7a">' + esc(it.c === 'childcare' ? CHILDCARE.k : (LEVEL[it.lvl] || LEVEL['Level not published']).k) + '</span><br>' +
        title(it.a) + (it.z ? ', ' + esc(it.z) : '') +
        (it.cd ? '<br>' + cdLabel(it.cd) : '') +
        (it.csd ? '<br>School district ' + it.csd : '') +
        (it.cap ? '<br>Reported capacity: ' + num(it.cap) : ''));
      it._m = m;
      markers.push(m);
    });
  }

  function matches(it) {
    if (!active[it.c]) return false;
    if (it.c === 'school' && !levelOn[it.lvl || 'Level not published']) return false;
    if (!query) return true;
    var q = query.toLowerCase();
    return (it.n + ' ' + it.a + ' ' + it.s + ' ' + (it.lvl || '') + ' ' + (it.op || '') + ' ' + (it.z || '')).toLowerCase().indexOf(q) > -1;
  }

  function showSites() {
    return forceSites || siteMode === 'always' || (map && map.getZoom() >= ZOOM_FOR_SITES);
  }

  function drawSites() {
    siteLayer.clearLayers();
    if (!showSites()) return 0;
    var vis = items.filter(matches);
    vis.forEach(function (it) { if (it._m) it._m.addTo(siteLayer); });
    return vis.length;
  }

  function cdLabel(cd) {
    var p = cd.split('-');
    return BORO[p[0]] + ' CD ' + p[1];
  }

  /* ---------- choropleth ---------- */
  function shade(v, max) {
    if (!v) return '#eef0f7';
    var t = Math.pow(v / max, 0.6);
    var stops = [[238, 240, 247], [176, 196, 226], [110, 145, 200], [56, 92, 165], [13, 27, 75]];
    var i = Math.min(stops.length - 2, Math.floor(t * (stops.length - 1)));
    var f = t * (stops.length - 1) - i;
    var a = stops[i], b = stops[i + 1];
    return 'rgb(' + Math.round(a[0] + (b[0] - a[0]) * f) + ',' +
      Math.round(a[1] + (b[1] - a[1]) * f) + ',' +
      Math.round(a[2] + (b[2] - a[2]) * f) + ')';
  }

  function choropleth(gj, counts, max, hrefFor, nameFor) {
    return L.geoJSON(gj, {
      style: function (f) {
        var k = f.properties.cd != null ? f.properties.cd : f.properties.csd;
        return { color: '#fff', weight: 1.2, fillColor: shade(counts[k] || 0, max), fillOpacity: 0.85 };
      },
      onEachFeature: function (f, l) {
        var k = f.properties.cd != null ? f.properties.cd : f.properties.csd;
        var n = counts[k] || 0;
        l.bindTooltip('<strong>' + nameFor(k, f) + '</strong><br>' + num(n) + ' schools and childcare sites', { sticky: true });
        l.on('mouseover', function () { l.setStyle({ weight: 3, color: '#f47920' }); l.bringToFront(); });
        l.on('mouseout', function () { l.setStyle({ weight: 1.2, color: '#fff' }); });
        l.on('click', function () { if (hrefFor) window.location.href = hrefFor(k); });
      }
    });
  }

  /* ---------- key + controls ---------- */
  function buildKey(host, opts) {
    if (!host) return;
    host.innerHTML = '';
    if (opts.shading) {
      var s = el('div', 'key-block');
      s.appendChild(el('div', 'key-h', 'District shading'));
      var ramp = el('div', 'ramp');
      [0.02, 0.25, 0.5, 0.75, 1].forEach(function (t) {
        var b = el('i'); b.style.background = shade(t * opts.max, opts.max); ramp.appendChild(b);
      });
      s.appendChild(ramp);
      s.appendChild(el('div', 'key-scale', 'Fewer sites   \u2192   ' + num(opts.max) + ' in the busiest district'));
      s.appendChild(el('div', 'key-note', 'Zoom in past street level, or press Show every site, to swap the shading for individual pins.'));
      host.appendChild(s);
    }
    var k = el('div', 'key-block');
    k.appendChild(el('div', 'key-h', 'Map pins'));
    var list = el('div', 'key-items');
    LEVEL_ORDER.forEach(function (l) { list.appendChild(keyItem(LEVEL[l], LEVEL[l].k)); });
    list.appendChild(keyItem(CHILDCARE, CHILDCARE.k));
    k.appendChild(list);
    host.appendChild(k);
  }

  function keyItem(st, label) {
    var d = el('span', 'key-item');
    d.innerHTML = '<span class="pin mini" style="--pin:' + st.c + '"><span class="pin-head">' +
      '<svg viewBox="0 0 24 24" aria-hidden="true">' + GLYPH[st.g] + '</svg></span><span class="pin-tip"></span></span>';
    d.appendChild(el('span', null, label));
    return d;
  }

  function buildLevelChips(host, onChange) {
    if (!host) return;
    host.innerHTML = '';
    LEVEL_ORDER.forEach(function (l) {
      var b = el('button', 'chip lvl');
      b.type = 'button';
      b.setAttribute('aria-pressed', 'true');
      b.style.setProperty('--pin', LEVEL[l].c);
      b.textContent = l;
      b.addEventListener('click', function () {
        levelOn[l] = !levelOn[l];
        b.setAttribute('aria-pressed', levelOn[l] ? 'true' : 'false');
        onChange();
      });
      host.appendChild(b);
    });
  }

  function wireControls(onChange) {
    var box = $('#q');
    if (box) box.addEventListener('input', function () { query = box.value.trim(); onChange(); });
    Array.prototype.forEach.call(document.querySelectorAll('.chip[data-cat]'), function (c) {
      c.addEventListener('click', function () {
        var k = c.getAttribute('data-cat');
        active[k] = !active[k];
        c.setAttribute('aria-pressed', active[k] ? 'true' : 'false');
        onChange();
      });
    });
    buildLevelChips($('#levelchips'), onChange);
    var t = $('#sites-toggle');
    if (t) t.addEventListener('click', function () {
      forceSites = !forceSites;
      t.setAttribute('aria-pressed', forceSites ? 'true' : 'false');
      t.textContent = forceSites ? 'Show district shading' : 'Show every site';
      onChange();
    });
  }

  function setText(sel, v) { var e = $(sel); if (e) e.textContent = v; }

  function counts(list) {
    var c = { school: 0, childcare: 0, total: 0 };
    list.forEach(function (it) { c[it.c]++; c.total++; });
    return c;
  }

  function setCounts(vis) {
    var c = counts(vis);
    setText('#c-total', num(c.total));
    setText('#c-school', num(c.school));
    setText('#c-childcare', num(c.childcare));
    var prek = vis.filter(function (i) { return i.s === 'Pre-K / 3-K'; }).length;
    setText('#c-prek', num(prek));
  }

  /* ---------- overview pages (citywide, borough, CSD hub) ---------- */
  function overview(cfg) {
    Promise.all(cfg.loads.map(get)).then(function (res) {
      cfg.ready(res);
      wireControls(refresh);
      map.on('zoomend', function () { refresh(); });
      refresh();
    }).catch(function (e) {
      var t = $(cfg.status);
      if (t) t.textContent = 'Could not load the data. ' + e.message;
    });

    function refresh() {
      var vis = items.filter(matches);
      var on = showSites();
      shapeLayer.eachLayer(function (l) { if (l.setStyle) l.setStyle({ fillOpacity: on ? 0.12 : 0.85 }); });
      drawSites();
      setText('#map-count', on ? num(vis.length) + ' sites shown' : 'Districts shaded by how many sites they hold');
      var t = $('#sites-toggle');
      if (t && !forceSites) t.textContent = on ? 'Show district shading' : 'Show every site';
    }
  }

  /* ---------- citywide hub ---------- */
  function hub() {
    var S;
    overview({
      status: '#hub-status',
      loads: [BASE + 'summary.json', BASE + 'all.json', BASE + 'districts.geojson'],
      ready: function (res) {
        S = res[0]; items = res[1];
        buildStats(S); buildBorough(S); buildTable(S); buildIndex(S); buildAudit(S);
        initMap([40.7128, -73.94], 11);
        var c = {}; S.districts.forEach(function (d) { c[d.cd] = d.total; });
        var names = {}; S.districts.forEach(function (d) { names[d.cd] = cdLabel(d.cd) + ' \u2014 ' + d.name; });
        choropleth(res[2], c, S.max_district_total,
          function (k) { return 'eduhub-' + k; },
          function (k) { return names[k]; }).addTo(shapeLayer);
        buildMarkers(items);
        buildKey($('#mapkey'), { shading: true, max: S.max_district_total });
      }
    });

    function buildStats(s) {
      var c = s.citywide, host = $('#citystats'); host.innerHTML = '';
      [['all', c.total, 'Schools & childcare sites'], ['school', c.school, 'Schools'],
       ['school', c['lvl::Elementary'], 'Elementary schools'], ['school', c['lvl::High school'], 'High schools'],
       ['childcare', c.childcare, 'Childcare & pre-K']].forEach(function (r) {
        var d = el('div', 'stat ' + r[0]);
        d.appendChild(el('div', 'v', num(r[1])));
        d.appendChild(el('div', 'l', r[2]));
        host.appendChild(d);
      });
    }

    function buildBorough(s) {
      var rows = Object.keys(BORO).map(function (b) {
        var v = s.borough[b], n = s.districts.filter(function (d) { return d.boro === b; }).length;
        return ['<a href="eduhub-' + b + '">' + BORO[b] + '</a>', n, v.school, v['lvl::Elementary'],
                v['lvl::Middle'], v['lvl::High school'], v.childcare, v.total];
      });
      var t = tableEl(['Borough', 'Districts', 'Schools', 'Elementary', 'Middle', 'High', 'Childcare & pre-K', 'All sites'], rows);
      var host = $('#boroughtable'); host.innerHTML = ''; host.appendChild(t);
    }

    function buildTable(s) {
      var rows = s.districts.map(function (d) {
        return ['<a href="eduhub-' + d.cd + '">' + cdLabel(d.cd) + '</a>', d.name, d.school,
                d['lvl::Elementary'], d['lvl::K-8'], d['lvl::Middle'], d['lvl::High school'],
                d.childcare, d.total, d.csd.length ? d.csd.join(', ') : 'not published'];
      });
      var t = tableEl(['District', 'Area', 'Schools', 'Elementary', 'K-8', 'Middle', 'High', 'Childcare & pre-K', 'All sites', 'School districts'], rows);
      var order = ['mn', 'bx', 'bk', 'qn', 'si'];
      Array.prototype.forEach.call(t.tBodies[0].rows, function (tr, k) {
        var d = s.districts[k];
        tr.cells[0].dataset.v = order.indexOf(d.boro) * 100 + d.num;
      });
      var host = $('#districttable'); host.innerHTML = ''; host.appendChild(t);
      var box = $('#dq');
      if (box) box.addEventListener('input', function () {
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
        bl.href = 'eduhub-' + b; bl.style.color = 'inherit';
        bh.appendChild(bl); host.appendChild(bh);
        var g = el('div', 'districtgrid');
        s.districts.filter(function (d) { return d.boro === b; }).forEach(function (d) {
          var a = el('a', 'dlink');
          a.href = 'eduhub-' + d.cd;
          a.appendChild(el('b', null, 'CD ' + d.num + '  ' + d.name));
          a.appendChild(el('span', null, num(d.school) + ' schools  /  ' + num(d.childcare) + ' childcare'));
          g.appendChild(a);
        });
        host.appendChild(g);
      });
    }

    function buildAudit(s) {
      var host = $('#audit'); host.innerHTML = '';
      host.appendChild(el('p', 'note',
        'Source records: ' + num(s.record_count) + '. Placed in a community district: ' + num(s.assigned) + '. ' +
        'Of those, ' + num(s.mapped) + ' have coordinates and appear on the map; ' + num(s.assigned_no_coords) +
        (s.assigned_no_coords === 1 ? ' appears' : ' appear') + ' in a district directory only. ' +
        'Not placeable: ' + num(s.unassigned) + '. ' +
        num(s.mapped) + ' + ' + num(s.assigned_no_coords) + ' + ' + num(s.unassigned) + ' = ' + num(s.record_count) + '.'));
      var ul = el('ul', 'note');
      (s.no_coord_records || []).forEach(function (r) {
        ul.appendChild(el('li', null, title(r.name) + ' (' + r.sub + ', ' + r.cd.toUpperCase() + '): ' + r.note));
      });
      (s.unassigned_records || []).forEach(function (r) {
        ul.appendChild(el('li', null, title(r.name) + ' (' + r.sub + ', ZIP ' + r.zip + '): ' + r.note));
      });
      if (ul.children.length) host.appendChild(ul);
    }
  }

  /* ---------- borough page ---------- */
  function borough(b) {
    overview({
      status: '#boro-status',
      loads: [BASE + 'boro-' + b + '.json', BASE + 'summary.json', BASE + 'districts.geojson'],
      ready: function (res) {
        var d = res[0], s = res[1];
        items = d.items;
        initMap([40.7, -73.95], 11);
        var mine = s.districts.filter(function (x) { return x.boro === b; });
        var c = {}, names = {}, max = 0;
        mine.forEach(function (x) { c[x.cd] = x.total; names[x.cd] = cdLabel(x.cd) + ' \u2014 ' + x.name; if (x.total > max) max = x.total; });
        var gj = { type: 'FeatureCollection', features: res[2].features.filter(function (f) { return f.properties.cd.indexOf(b + '-') === 0; }) };
        var lay = choropleth(gj, c, max, function (k) { return 'eduhub-' + k; }, function (k) { return names[k]; });
        lay.addTo(shapeLayer);
        map.fitBounds(lay.getBounds(), { padding: [14, 14] });
        buildMarkers(items);
        buildKey($('#mapkey'), { shading: true, max: max });
        buildBoroTable(s, b);
      }
    });

    function buildBoroTable(s, b) {
      var host = $('#boro-districts'); if (!host) return;
      var rows = s.districts.filter(function (d) { return d.boro === b; }).map(function (d) {
        return ['<a href="eduhub-' + d.cd + '">CD ' + d.num + '</a>', d.name, d.school,
                d['lvl::Elementary'], d['lvl::K-8'], d['lvl::Middle'], d['lvl::High school'],
                d.childcare, d.total, d.csd.length ? d.csd.join(', ') : 'not published'];
      });
      var t = tableEl(['District', 'Area', 'Schools', 'Elementary', 'K-8', 'Middle', 'High', 'Childcare & pre-K', 'All sites', 'School districts'], rows);
      host.innerHTML = ''; host.appendChild(t);
    }
  }

  /* ---------- one district / one school district ---------- */
  function detail(cfg) {
    Promise.all(cfg.loads.map(get)).then(function (res) {
      cfg.ready(res);
      siteMode = 'always';
      wireControls(render);
      buildKey($('#mapkey'), { shading: false });
      render();
    }).catch(function (e) {
      var t = $(cfg.status);
      if (t) t.textContent = 'Could not load the data. ' + e.message;
    });
    function render() {
      var vis = items.filter(matches);
      siteLayer.clearLayers();
      vis.forEach(function (it) { if (it._m) it._m.addTo(siteLayer); });
      setCounts(vis);
      cfg.cards(vis);
    }
  }

  function cardList(vis) {
    var host = $('#cards'); if (!host) return;
    host.innerHTML = '';
    if (!vis.length) { host.innerHTML = '<div class="empty">No sites match this filter. Clear the search box or turn a category back on.</div>'; return; }
    vis.forEach(function (it) {
      var st = styleFor(it);
      var c = el('div', 'card');
      var tag = el('span', 'tag', labelFor(it));
      tag.style.background = st.c;
      c.appendChild(tag);
      c.appendChild(el('h3', null, title(it.n)));
      var m = el('div', 'meta');
      m.innerHTML = title(it.a) + (it.z ? ', ' + esc(it.z) : '') +
        (it.cap ? '<br>Reported capacity ' + num(it.cap) : '') + (it.ot ? '<br>' + esc(it.ot) : '');
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

  function district(cd) {
    detail({
      status: '#cards',
      loads: [BASE + cd + '.json', BASE + 'districts.geojson', BASE + 'csd-summary.json', BASE + 'school-districts.geojson'],
      cards: cardList,
      ready: function (res) {
        var d = res[0], gj = res[1], cs = res[2], sd = res[3];
        items = d.items;
        initMap([40.7, -73.95], 12);
        var f = gj.features.filter(function (x) { return x.properties.cd === cd; });
        var bound = L.geoJSON({ type: 'FeatureCollection', features: f }, {
          style: { color: '#06024D', weight: 2.5, fill: true, fillColor: '#06024D', fillOpacity: 0.04 }
        }).addTo(shapeLayer);
        map.fitBounds(bound.getBounds(), { padding: [16, 16] });
        var rows = cs.by_cd[cd] || [];
        var only = { type: 'FeatureCollection', features: sd.features.filter(function (x) {
          return rows.some(function (r) { return r.csd === x.properties.csd; }); }) };
        var csdLayer = L.geoJSON(only, {
          style: { color: '#7a3ea8', weight: 2, fill: false, dashArray: '5 4', opacity: 0.85 },
          onEachFeature: function (ft, l) { l.bindTooltip(ft.properties.name, { sticky: true }); }
        });
        var tog = $('#csd-toggle');
        if (tog) tog.addEventListener('click', function () {
          var on = tog.getAttribute('aria-pressed') === 'true';
          if (on) { map.removeLayer(csdLayer); tog.setAttribute('aria-pressed', 'false'); }
          else { csdLayer.addTo(map); tog.setAttribute('aria-pressed', 'true'); }
        });
        var host = $('#cd-overlap');
        if (host) { host.innerHTML = ''; host.appendChild(overlapTable(rows, 'byCd')); }
        var lead = $('#overlap-lead');
        if (lead) lead.textContent = rows.length === 1
          ? 'This community district sits entirely inside one school district.'
          : 'This community district is split across ' + rows.length + ' school districts.';
        buildMarkers(items);
      }
    });
  }

  function csdPage(n) {
    detail({
      status: '#cards',
      loads: [BASE + 'csd-' + n + '.json', BASE + 'csd-summary.json', BASE + 'school-districts.geojson', BASE + 'districts.geojson'],
      cards: cardList,
      ready: function (res) {
        var d = res[0], s = res[1], sd = res[2], cdgj = res[3];
        var meta = s.csds.filter(function (x) { return x.csd === n; })[0];
        items = d.items;
        initMap([40.7, -73.95], 12);
        var cdKeys = meta.cds.map(function (x) { return x.cd; });
        L.geoJSON({ type: 'FeatureCollection', features: cdgj.features.filter(function (f) { return cdKeys.indexOf(f.properties.cd) > -1; }) }, {
          style: { color: '#06024D', weight: 1.4, fill: true, fillColor: '#06024D', fillOpacity: 0.04 },
          onEachFeature: function (ft, l) { l.bindTooltip(ft.properties.name, { sticky: true }); }
        }).addTo(shapeLayer);
        var bound = L.geoJSON({ type: 'FeatureCollection', features: sd.features.filter(function (x) { return x.properties.csd === n; }) }, {
          style: { color: '#7a3ea8', weight: 2.5, fill: false, dashArray: '5 4' }
        }).addTo(shapeLayer);
        map.fitBounds(bound.getBounds(), { padding: [16, 16] });
        var host = $('#csd-overlap');
        if (host) { host.innerHTML = ''; host.appendChild(overlapTable(meta.cds, 'byCsd')); }
        buildMarkers(items);
      }
    });
  }

  /* ---------- school district hub ---------- */
  function csdHub() {
    overview({
      status: '#csdhub-status',
      loads: [BASE + 'csd-summary.json', BASE + 'all.json', BASE + 'school-districts.geojson',
              BASE + 'districts.geojson', BASE + 'summary.json'],
      ready: function (res) {
        var s = res[0]; items = res[1];
        res[4].districts.forEach(function (d) { cdName[d.cd] = d.name; });
        buildCsdStats(s); buildCsdTable(s); buildCrosswalk(s); buildCsdIndex(s); buildCsdAudit(s);
        initMap([40.7128, -73.94], 11);
        var c = {}, max = 0;
        s.csds.forEach(function (x) { c[x.csd] = x.total; if (x.total > max) max = x.total; });
        L.geoJSON(res[3], { style: { color: '#06024D', weight: 0.7, fill: false, opacity: 0.3 } }).addTo(shapeLayer);
        choropleth(res[2], c, max, function (k) { return 'eduhub-csd-' + k; },
          function (k) { return 'Community School District ' + k; }).addTo(shapeLayer);
        buildMarkers(items);
        buildKey($('#mapkey'), { shading: true, max: max });
      }
    });

    function buildCsdStats(s) {
      var host = $('#csdstats'); host.innerHTML = '';
      var sch = 0, cc = 0, el1 = 0, hs = 0;
      s.csds.forEach(function (c) { sch += c.school; cc += c.childcare; el1 += c['lvl::Elementary']; hs += c['lvl::High school']; });
      [['all', s.in_csd, 'Sites in a school district'], ['all', s.csds.length, 'School districts'],
       ['school', sch, 'Schools'], ['school', el1, 'Elementary schools'], ['childcare', cc, 'Childcare & pre-K']]
        .forEach(function (r) {
          var d = el('div', 'stat ' + r[0]);
          d.appendChild(el('div', 'v', num(r[1])));
          d.appendChild(el('div', 'l', r[2]));
          host.appendChild(d);
        });
    }

    function buildCsdTable(s) {
      var rows = s.csds.map(function (c) {
        return ['<a href="eduhub-csd-' + c.csd + '">CSD ' + c.csd + '</a>', c.cds.length, c.school,
                c['lvl::Elementary'], c['lvl::K-8'], c['lvl::Middle'], c['lvl::High school'], c.childcare, c.total];
      });
      var t = tableEl(['School district', 'Community districts', 'Schools', 'Elementary', 'K-8', 'Middle', 'High', 'Childcare & pre-K', 'All sites'], rows);
      Array.prototype.forEach.call(t.tBodies[0].rows, function (tr, k) { tr.cells[0].dataset.v = s.csds[k].csd; });
      var host = $('#csdtable'); host.innerHTML = ''; host.appendChild(t);
    }

    function buildCrosswalk(s) {
      var host = $('#crosswalk');
      var t = document.createElement('table');
      var tr = t.createTHead().insertRow();
      ['Community district', 'Area', 'School districts it covers', 'Split'].forEach(function (h) {
        var th = document.createElement('th'); th.textContent = h; tr.appendChild(th);
      });
      var tb = t.createTBody();
      Object.keys(s.by_cd).forEach(function (cd) {
        var rows = s.by_cd[cd], row = tb.insertRow();
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
        a.appendChild(el('span', null, num(c.school) + ' schools  /  ' + num(c.childcare) + ' childcare  /  ' + c.cds.length + ' community districts'));
        g.appendChild(a);
      });
      host.appendChild(g);
    }

    function buildCsdAudit(s) {
      var host = $('#csdaudit'); host.innerHTML = '';
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
  }

  var cdName = {};

  /* ---------- shared table helpers ---------- */
  function overlapTable(rows, mode) {
    var t = document.createElement('table');
    var heads = mode === 'byCd'
      ? ['School district', 'Share of this community district', 'Share of that school district', 'Square miles', 'Schools & childcare']
      : ['Community district', 'Share of this school district', 'Share of that community district', 'Square miles', 'Schools & childcare'];
    var tr = t.createTHead().insertRow();
    heads.forEach(function (h, i) {
      var th = document.createElement('th');
      if (i > 0) th.className = 'num';
      th.textContent = h; tr.appendChild(th);
    });
    var tb = t.createTBody();
    rows.forEach(function (r) {
      var row = tb.insertRow(), c0 = row.insertCell();
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

  function tableEl(heads, rows) {
    var t = document.createElement('table');
    var tr = t.createTHead().insertRow();
    heads.forEach(function (h, i) {
      var th = document.createElement('th');
      if (i > 1) th.className = 'num';
      th.textContent = h; th.tabIndex = 0;
      th.addEventListener('click', function () { sortBy(t, i, th); });
      th.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); sortBy(t, i, th); } });
      tr.appendChild(th);
    });
    var tb = t.createTBody();
    rows.forEach(function (r) {
      var row = tb.insertRow();
      r.forEach(function (v, i) {
        var td = row.insertCell();
        if (typeof v === 'number') { td.className = i > 1 ? 'num' : ''; td.textContent = num(v); td.dataset.v = v; }
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

  window.EDU = { hub: hub, district: district, borough: borough, csdHub: csdHub, csdPage: csdPage };
})();
