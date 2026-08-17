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
  /* Colours for the school district slices inside one community district,
     assigned largest share first so the dominant CSD always reads strongest. */
  var SPLIT = ['#7a3ea8', '#f47920', '#1b6ca8', '#0f766e', '#b4436c'];

  function splitBar(rows, host, unit) {
    if (!host) return;
    host.innerHTML = '';
    var bar = el('div', 'splitbar');
    rows.forEach(function (r, i) {
      var seg = el('span', 'splitseg');
      seg.style.width = Math.max(r.pct, 2) + '%';
      seg.style.background = SPLIT[i % SPLIT.length];
      seg.title = r.label + ' \u2014 ' + r.pct.toFixed(1) + '%';
      if (r.pct >= 8) seg.textContent = r.pct.toFixed(0) + '%';
      bar.appendChild(seg);
    });
    host.appendChild(bar);
    var keys = el('div', 'splitkeys');
    rows.forEach(function (r, i) {
      var k = el('span', 'splitkey');
      var sw = el('i'); sw.style.background = SPLIT[i % SPLIT.length];
      k.appendChild(sw);
      k.appendChild(el('span', null, r.label + '  ' + r.pct.toFixed(1) + '%' +
        (r.sites != null ? '  \u00b7  ' + num(r.sites) + ' ' + (r.sites === 1 ? unit.replace(/s$/, '') : unit) : '')));
      keys.appendChild(k);
    });
    host.appendChild(keys);
  }

  function splitSentence(name, rows) {
    if (!rows.length) return '';
    if (rows.length === 1) {
      return rows[0].pct_of_cd >= 99.9
        ? name + ' sits entirely inside School District ' + rows[0].csd + '.'
        : name + ' is served by one school district, School District ' + rows[0].csd + ', covering ' +
          rows[0].pct_of_cd.toFixed(1) + '% of its land; the remainder falls outside any school district boundary.';
    }
    var first = rows[0], rest = rows.slice(1);
    var tail = rest.map(function (r) { return 'District ' + r.csd + ' (' + r.pct_of_cd.toFixed(0) + '%)'; });
    var joined = tail.length === 1 ? tail[0] : tail.slice(0, -1).join(', ') + ' and ' + tail[tail.length - 1];
    var lead = first.pct_of_cd >= 75 ? 'is mostly' : (first.pct_of_cd >= 50 ? 'is mainly' : 'leans toward');
    return name + ' ' + lead + ' School District ' + first.csd + ' (' + first.pct_of_cd.toFixed(0) +
      '%), with ' + (rest.length === 1 && rest[0].pct_of_cd < 15 ? 'a slice in ' : 'the rest in ') + joined + '.';
  }

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

  /* Colour schemes for the district map. A raw count mostly tells you how big
     a district is, so it is not the default: borough and school district are
     categorical and answer a question someone actually has. */
  var BOROCOL = { mn: '#1b6ca8', bx: '#0f766e', bk: '#f47920', qn: '#7a3ea8', si: '#b4436c' };
  var SPLITCOL = { 1: '#cfd6e6', 2: '#8fa6cf', 3: '#4b6fae', 4: '#22417f', 5: '#06024D' };
  var CSDCOL = ['#1b6ca8', '#f47920', '#0f766e', '#7a3ea8', '#b4436c', '#4b9fd5', '#c9820f',
                '#2f8f5b', '#9b5bc4', '#d1567f', '#06024D', '#e0952f', '#3aa0a0', '#8c6d3f',
                '#5b7fd4', '#d0483a'];

  var SCHEMES = {
    borough: {
      label: 'Borough',
      blurb: 'The five boroughs, so the map reads as the city you know before anything else.',
      color: function (d) { return BOROCOL[d.boro]; },
      value: function (d) { return BORO[d.boro]; },
      legend: function (ds) {
        return Object.keys(BORO).map(function (b) {
          return { c: BOROCOL[b], t: BORO[b] + '  (' + ds.filter(function (d) { return d.boro === b; }).length + ' districts)' };
        });
      }
    },
    csd: {
      label: 'School district',
      blurb: 'Each community district takes the colour of the school district covering most of it, and its label shows that district number. There are 32 school districts and 16 colours, so a colour repeats across the city; the D number on the label is what identifies it.',
      color: function (d) { return d.csd_main ? CSDCOL[(d.csd_main - 1) % CSDCOL.length] : '#dfe3ee'; },
      value: function (d) { return d.csd_main ? 'Mostly School District ' + d.csd_main : 'No school district'; },
      legend: function (ds) {
        var seen = {};
        ds.forEach(function (d) { if (d.csd_main) seen[d.csd_main] = true; });
        return Object.keys(seen).sort(function (a, b) { return a - b; }).map(function (n) {
          return { c: CSDCOL[(n - 1) % CSDCOL.length], t: 'CSD ' + n };
        });
      }
    },
    split: {
      label: 'How many school districts',
      blurb: 'How many school districts each community district is cut into. Darker means a board dealing with more superintendents for one neighbourhood.',
      color: function (d) { return SPLITCOL[Math.min(d.csd_count || 1, 5)]; },
      value: function (d) { return d.csd_count === 1 ? 'One school district' : d.csd_count + ' school districts'; },
      legend: function (ds) {
        return [1, 2, 3, 4, 5].filter(function (n) {
          return ds.some(function (d) { return (d.csd_count || 1) === n; });
        }).map(function (n) {
          var c = ds.filter(function (d) { return (d.csd_count || 1) === n; }).length;
          return { c: SPLITCOL[n], t: (n === 1 ? 'One school district' : n + ' school districts') + '  (' + c + ')' };
        });
      }
    },
    density: {
      label: 'Sites per square mile',
      blurb: 'Schools and childcare per square mile, which unlike a raw count does not simply reward a district for being large.',
      seq: true,
      color: function (d, max) { return shade(d.per_sqmi, max); },
      metric: function (d) { return d.per_sqmi; },
      value: function (d) { return d.per_sqmi + ' per square mile' }
    },
    total: {
      label: 'Total sites',
      blurb: 'The raw count. Useful for a total, but it largely tracks how big the district is, so read it next to the per square mile view.',
      seq: true,
      color: function (d, max) { return shade(d.total, max); },
      metric: function (d) { return d.total; },
      value: function (d) { return num(d.total) + ' sites' }
    }
  };
  var scheme = 'borough';

  var labelLayer = null, pickedKey = null;

  var recBy = {}, schemeMax = 1, activeScheme = null;

  var LABELVAL = {
    borough: function (d) { return num(d.total); },
    csd: function (d) { return d.csd_main ? 'D' + d.csd_main : '\u2014'; },
    split: function (d) { return (d.csd_count || 1) + (d.csd_count === 1 ? ' dist' : ' dists'); },
    density: function (d) { return d.per_sqmi + '/mi'; },
    total: function (d) { return num(d.total); }
  };

  function fillFor(k) {
    var sc = SCHEMES[scheme];
    var d = recBy[k];
    if (!d || !sc) return '#eef0f7';
    return sc.seq ? sc.color(d, schemeMax) : sc.color(d);
  }

  function choropleth(gj, counts, max, hrefFor, nameFor) {
    var shapes = {};
    var lay = L.geoJSON(gj, {
      style: function (f) {
        var k = f.properties.cd != null ? f.properties.cd : f.properties.csd;
        return { color: '#fff', weight: 1.2, fillColor: activeScheme ? fillFor(k) : shade(counts[k] || 0, max), fillOpacity: 0.85 };
      },
      onEachFeature: function (f, l) {
        var k = f.properties.cd != null ? f.properties.cd : f.properties.csd;
        shapes[k] = l;
        l.on('mouseover', function () { if (k !== pickedKey) l.setStyle({ weight: 2.5, color: '#f47920' }); l.bringToFront(); });
        l.on('mouseout', function () { if (k !== pickedKey) l.setStyle({ weight: 1.2, color: '#fff' }); });
        l.on('click', function () { pick(k); });
      }
    });

    /* Permanent name + count on every district, so the map reads without hovering.
       Hover and tap are extras, not the only way in. */
    labelLayer = L.layerGroup();
    gj.features.forEach(function (f) {
      var k = f.properties.cd != null ? f.properties.cd : f.properties.csd;
      if (f.properties.lx == null) return;
      var n = counts[k] || 0;
      function labelHtml() {
        var d = recBy[k];
        var v = (activeScheme && d && LABELVAL[scheme]) ? LABELVAL[scheme](d) : num(n);
        return '<span class="dlabel"><b>' + esc(f.properties.short) + '</b><i>' + esc(v) + '</i></span>';
      }
      var m = L.marker([f.properties.ly, f.properties.lx], {
        interactive: true, keyboard: false,
        icon: L.divIcon({ className: 'dlabel-wrap', html: labelHtml(), iconSize: [58, 30], iconAnchor: [29, 15] })
      });
      m.relabel = function () {
        m.setIcon(L.divIcon({ className: 'dlabel-wrap', html: labelHtml(), iconSize: [58, 30], iconAnchor: [29, 15] }));
      };
      m.on('click', function () { pick(k); });
      m.addTo(labelLayer);
    });

    lay.pick = pick;
    lay.labels = labelLayer;
    lay.hrefFor = hrefFor;
    lay.restyle = function () {
      lay.eachLayer(function (l) {
        var k = l.feature.properties.cd != null ? l.feature.properties.cd : l.feature.properties.csd;
        if (k !== pickedKey) l.setStyle({ fillColor: fillFor(k), color: '#fff', weight: 1.2 });
        else l.setStyle({ fillColor: fillFor(k) });
      });
      labelLayer.eachLayer(function (m) { if (m.relabel) m.relabel(); });
    };

    function pick(k) {
      if (pickedKey && shapes[pickedKey]) shapes[pickedKey].setStyle({ weight: 1.2, color: '#fff' });
      pickedKey = k;
      if (shapes[k]) { shapes[k].setStyle({ weight: 3.5, color: '#f47920' }); shapes[k].bringToFront(); }
      var host = $('#picked');
      if (!host) return;
      host.innerHTML = '';
      host.appendChild(el('div', 'picked-name', nameFor(k)));
      host.appendChild(el('div', 'picked-n', num(counts[k] || 0) + ' schools and childcare sites'));
      var a = el('a', 'btn solid picked-go', 'Open this page');
      a.href = hrefFor(k);
      host.appendChild(a);
      host.hidden = false;
    }
    return lay;
  }

  /* ---------- key + controls ---------- */
  function buildSchemePicker(host, ds, onChange) {
    if (!host) return;
    host.innerHTML = '';
    Object.keys(SCHEMES).forEach(function (k) {
      var b = el('button', 'chip scheme');
      b.type = 'button';
      b.setAttribute('aria-pressed', k === scheme ? 'true' : 'false');
      b.textContent = SCHEMES[k].label;
      b.addEventListener('click', function () {
        scheme = k;
        Array.prototype.forEach.call(host.children, function (o) { o.setAttribute('aria-pressed', 'false'); });
        b.setAttribute('aria-pressed', 'true');
        setSchemeMax(ds);
        onChange();
      });
      host.appendChild(b);
    });
  }

  function setSchemeMax(ds) {
    var sc = SCHEMES[scheme];
    schemeMax = sc.seq ? Math.max.apply(null, ds.map(sc.metric)) : 1;
  }

  function schemeLegend(host, ds) {
    if (!host) return;
    host.innerHTML = '';
    var sc = SCHEMES[scheme];
    var blk = el('div', 'key-block');
    blk.appendChild(el('div', 'key-h', 'Colour: ' + sc.label));
    if (sc.seq) {
      var ramp = el('div', 'ramp');
      [0.02, 0.25, 0.5, 0.75, 1].forEach(function (t) {
        var i = el('i'); i.style.background = shade(t * schemeMax, schemeMax); ramp.appendChild(i);
      });
      blk.appendChild(ramp);
      var lo = Math.min.apply(null, ds.map(sc.metric));
      blk.appendChild(el('div', 'key-scale', lo + '   \u2192   ' + schemeMax + ' in the highest district'));
    } else {
      var list = el('div', 'key-items');
      sc.legend(ds).forEach(function (r) {
        var d = el('span', 'key-item');
        var sw = el('i', 'kswatch fill'); sw.style.setProperty('--c', r.c); sw.style.opacity = 1;
        d.appendChild(sw); d.appendChild(el('span', null, r.t));
        list.appendChild(d);
      });
      blk.appendChild(list);
    }
    blk.appendChild(el('div', 'key-note', sc.blurb));
    host.appendChild(blk);
  }

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
      if (labelLayer) {
        if (on) map.removeLayer(labelLayer);
        else if (!map.hasLayer(labelLayer)) labelLayer.addTo(map);
      }
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
        var c = {}; S.districts.forEach(function (d) { c[d.cd] = d.total; recBy[d.cd] = d; });
        var names = {}; S.districts.forEach(function (d) { names[d.cd] = cdLabel(d.cd) + ' \u2014 ' + d.name; });
        activeScheme = true;
        setSchemeMax(S.districts);
        var lay = choropleth(res[2], c, S.max_district_total,
          function (k) { return 'eduhub-' + k; },
          function (k) { return names[k]; });
        lay.addTo(shapeLayer);
        buildMarkers(items);
        buildSchemePicker($('#schemechips'), S.districts, function () {
          lay.restyle();
          schemeLegend($('#schemekey'), S.districts);
        });
        schemeLegend($('#schemekey'), S.districts);
        buildKey($('#mapkey'), { shading: false });
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
        mine.forEach(function (x) { c[x.cd] = x.total; recBy[x.cd] = x; names[x.cd] = cdLabel(x.cd) + ' \u2014 ' + x.name; if (x.total > max) max = x.total; });
        var gj = { type: 'FeatureCollection', features: res[2].features.filter(function (f) { return f.properties.cd.indexOf(b + '-') === 0; }) };
        activeScheme = true;
        scheme = 'csd';
        setSchemeMax(mine);
        var lay = choropleth(gj, c, max, function (k) { return 'eduhub-' + k; }, function (k) { return names[k]; });
        lay.addTo(shapeLayer);
        map.fitBounds(lay.getBounds(), { padding: [14, 14] });
        buildMarkers(items);
        buildSchemePicker($('#schemechips'), mine, function () {
          lay.restyle();
          schemeLegend($('#schemekey'), mine);
        });
        schemeLegend($('#schemekey'), mine);
        buildKey($('#mapkey'), { shading: false });
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
      loads: [BASE + cd + '.json', BASE + 'districts.geojson', BASE + 'csd-summary.json',
              BASE + 'cd-csd-overlap.geojson'],
      cards: cardList,
      ready: function (res) {
        var d = res[0], gj = res[1], cs = res[2], ov = res[3];
        items = d.items;
        initMap([40.7, -73.95], 12);
        var f = gj.features.filter(function (x) { return x.properties.cd === cd; });
        var bound = L.geoJSON({ type: 'FeatureCollection', features: f }, {
          style: { color: '#06024D', weight: 3, fill: false }
        }).addTo(shapeLayer);
        map.fitBounds(bound.getBounds(), { padding: [16, 16] });

        var rows = cs.by_cd[cd] || [];
        var rank = {};
        rows.forEach(function (r, i) { rank[r.csd] = i; });

        /* Fill the district with one patch per school district it falls in,
           so the split is visible on the map itself, not just in a table. */
        var pieces = ov.features.filter(function (x) { return x.properties.cd === cd; });
        var splitLayer = L.layerGroup();
        L.geoJSON({ type: 'FeatureCollection', features: pieces }, {
          style: function (ft) {
            var col = SPLIT[rank[ft.properties.csd] % SPLIT.length];
            return { color: col, weight: 3, fill: true, fillColor: col, fillOpacity: 0.3 };
          },
          onEachFeature: function (ft, l) {
            var pr = ft.properties;
            l.bindTooltip('<strong>School District ' + pr.csd + '</strong><br>' +
              pr.pct_of_cd.toFixed(1) + '% of this community district<br>' +
              num(pr.sites) + ' schools and childcare ' + (pr.sites === 1 ? 'site' : 'sites'), { sticky: true });
          }
        }).addTo(splitLayer);
        /* Stamp the school district number on each patch so it reads under the pins. */
        pieces.forEach(function (ft) {
          if (ft.properties.lx == null) return;
          var col = SPLIT[rank[ft.properties.csd] % SPLIT.length];
          L.marker([ft.properties.ly, ft.properties.lx], {
            interactive: false, keyboard: false, zIndexOffset: -500,
            icon: L.divIcon({ className: 'dlabel-wrap',
              html: '<span class="csdstamp" style="--c:' + col + '">D' + ft.properties.csd + '</span>',
              iconSize: [46, 22], iconAnchor: [23, 11] })
          }).addTo(splitLayer);
        });
        splitLayer.addTo(map);

        var tog = $('#csd-toggle');
        if (tog) {
          tog.setAttribute('aria-pressed', 'true');
          tog.textContent = 'Hide school district split';
          tog.addEventListener('click', function () {
            var on = tog.getAttribute('aria-pressed') === 'true';
            if (on) { map.removeLayer(splitLayer); tog.setAttribute('aria-pressed', 'false'); tog.textContent = 'Show school district split'; }
            else { splitLayer.addTo(map); tog.setAttribute('aria-pressed', 'true'); tog.textContent = 'Hide school district split'; }
          });
        }

        var host = $('#cd-overlap');
        if (host) { host.innerHTML = ''; host.appendChild(overlapTable(rows, 'byCd')); }
        splitBar(rows.map(function (r) {
          return { pct: r.pct_of_cd, csd: r.csd, sites: r.sites, label: 'School District ' + r.csd };
        }), $('#splitbar'), 'sites');
        var lead = $('#overlap-lead');
        if (lead) lead.textContent = splitSentence(d.name, rows);
        var mapLead = $('#map-split-note');
        if (mapLead) mapLead.textContent = rows.length === 1
          ? 'The whole district is one school district, so the fill is a single colour.'
          : 'The coloured patches inside the district boundary are its ' + rows.length + ' school districts.';
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
      ['Community district', 'Area', 'School districts it covers', 'Share of the district', 'Split'].forEach(function (h) {
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
        var c3 = row.insertCell();
        var mini = el('span', 'minibar');
        rows.forEach(function (r, i) {
          var seg = el('i');
          seg.style.width = Math.max(r.pct_of_cd, 2) + '%';
          seg.style.background = SPLIT[i % SPLIT.length];
          seg.title = 'CSD ' + r.csd + ' \u2014 ' + r.pct_of_cd.toFixed(1) + '%';
          mini.appendChild(seg);
        });
        c3.appendChild(mini);
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


  /* ---------- zoned school finder ---------- */
  var ZLV = [
    { k: 'elementary', label: 'Elementary zone', c: '#1b6ca8' },
    { k: 'middle',     label: 'Middle school zone', c: '#0f766e' },
    { k: 'high',       label: 'High school zone', c: '#06024D' }
  ];
  var zoneData = {}, zoneLayer = null, zoneLevel = 'elementary', hereMarker = null;

  function loadZone(k) {
    if (zoneData[k]) return Promise.resolve(zoneData[k]);
    return get(BASE + 'zones-' + k + '.geojson').then(function (g) { zoneData[k] = g; return g; });
  }

  /* Ray casting against a GeoJSON Polygon / MultiPolygon ring set. */
  function inRing(pt, ring) {
    var x = pt[0], y = pt[1], inside = false;
    for (var i = 0, jj = ring.length - 1; i < ring.length; jj = i++) {
      var xi = ring[i][0], yi = ring[i][1], xj = ring[jj][0], yj = ring[jj][1];
      if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) inside = !inside;
    }
    return inside;
  }
  function inPolygon(pt, poly) {
    if (!inRing(pt, poly[0])) return false;
    for (var i = 1; i < poly.length; i++) if (inRing(pt, poly[i])) return false;
    return true;
  }
  function findZone(gj, lon, lat) {
    var pt = [lon, lat];
    for (var i = 0; i < gj.features.length; i++) {
      var g = gj.features[i].geometry;
      if (g.type === 'Polygon') { if (inPolygon(pt, g.coordinates)) return gj.features[i]; }
      else if (g.type === 'MultiPolygon') {
        for (var m = 0; m < g.coordinates.length; m++) if (inPolygon(pt, g.coordinates[m])) return gj.features[i];
      }
    }
    return null;
  }

  function zoneStyle(k) {
    var c = ZLV.filter(function (z) { return z.k === k; })[0].c;
    return function (f) {
      return f.properties.zoned
        ? { color: c, weight: 1.2, fillColor: c, fillOpacity: 0.14 }
        : { color: '#9aa0b0', weight: 1, fillColor: '#9aa0b0', fillOpacity: 0.1, dashArray: '3 3' };
    };
  }

  function zoneName(f) {
    var p = f.properties;
    if (p.schools && p.schools.length) {
      return p.schools.map(function (s) { return s.name ? title(s.name) : s.dbn; }).join(' / ');
    }
    return p.remarks ? p.remarks : 'No zoned school';
  }

  function zoneSchoolLines(f) {
    var p = f.properties;
    if (!p.schools || !p.schools.length) {
      return '<div class="zline muted">' + esc(p.remarks || 'No zoned school for this area.') + '</div>';
    }
    return p.schools.map(function (s) {
      return '<div class="zline"><b>' + (s.name ? title(s.name) : esc(s.dbn)) + '</b>' +
        '<span>' + esc(s.dbn) + (s.grades ? ' \u00b7 grades ' + esc(s.grades) : '') + '</span>' +
        (s.addr ? '<span>' + title(s.addr) + '</span>' : '') +
        (s.phone ? '<span>' + esc(s.phone) + '</span>' : '') +
        (s.name ? '' : '<span class="muted">Name not in the published DOE directory for this code.</span>') +
        '</div>';
    }).join('');
  }

  function zonesPage() {
    var summary = null, csdGj = null, cdGj = null;
    var LABEL_ZOOM = 13, LABEL_CAP = 60;
    var show = { zone: true, cd: false, csd: false };
    var zoneShapes = null, labelGroup = null, cdLayer = null, csdLayer = null;

    Promise.all([loadZone('elementary'), get(BASE + 'districts.geojson'),
                 get(BASE + 'school-districts.geojson'), get(BASE + 'summary.json')])
      .then(function (res) {
        cdGj = res[1]; csdGj = res[2]; summary = res[3];
        initMap([40.7128, -73.94], 11);
        labelGroup = L.layerGroup().addTo(map);
        buildOverlays();
        drawZones();
        buildZoneChips();
        buildOverlayChips();
        buildJumpers();
        buildDirectory();
        wireAddress();
        zoneKey();
        map.on('moveend zoomend', refreshLabels);
      })
      .catch(function (e) {
        var t = $('#zone-status');
        if (t) t.textContent = 'Could not load the zone data. ' + e.message;
      });

    function zoneKey() {
      var host = $('#mapkey'); if (!host) return;
      host.innerHTML = '';
      var k = el('div', 'key-block');
      k.appendChild(el('div', 'key-h', 'What the map shows'));
      var list = el('div', 'key-items');
      var z = ZLV.filter(function (x) { return x.k === zoneLevel; })[0];
      [['fill', z.c, z.label + ' with a zoned school'],
       ['hatch', '#9aa0b0', 'No zoned school here (park, cemetery, airport, or choice district)'],
       ['line', '#06024D', 'Community district boundary'],
       ['dash', '#7a3ea8', 'School district boundary'],
       ['dot', '#f47920', 'The address you looked up']].forEach(function (r) {
        var d = el('span', 'key-item');
        var sw = el('i', 'kswatch ' + r[0]);
        sw.style.setProperty('--c', r[1]);
        d.appendChild(sw);
        d.appendChild(el('span', null, r[2]));
        list.appendChild(d);
      });
      k.appendChild(list);
      k.appendChild(el('div', 'key-note', 'Zone numbers appear on the map once you zoom in. Use Jump to, or the address box above, to get somewhere quickly.'));
      host.appendChild(k);
    }

    function buildOverlays() {
      cdLayer = L.geoJSON(cdGj, {
        style: { color: '#06024D', weight: 2, fill: false, opacity: 0.9 },
        onEachFeature: function (f, l) { l.bindTooltip(cdLabel(f.properties.cd) + ' \u2014 ' + f.properties.name, { sticky: true }); }
      });
      csdLayer = L.geoJSON(csdGj, {
        style: { color: '#7a3ea8', weight: 2, fill: false, dashArray: '6 4', opacity: 0.9 },
        onEachFeature: function (f, l) { l.bindTooltip(f.properties.name, { sticky: true }); }
      });
    }

    function drawZones() {
      shapeLayer.clearLayers();
      if (!show.zone) { refreshLabels(); return; }
      zoneShapes = L.geoJSON(zoneData[zoneLevel], {
        style: zoneStyle(zoneLevel),
        onEachFeature: function (f, l) {
          l.bindTooltip('<strong>' + zoneName(f) + '</strong>' +
            (f.properties.csd ? '<br>School District ' + esc(f.properties.csd) : ''), { sticky: true });
        }
      }).addTo(shapeLayer);
      refreshLabels();
    }

    /* Zone numbers only when they can be read: past a zoom threshold, only for
       zones currently on screen, and capped so a dense borough never floods. */
    function refreshLabels() {
      if (!labelGroup) return;
      labelGroup.clearLayers();
      var note = $('#label-note');
      if (!show.zone) { if (note) note.textContent = 'Zone shading is off.'; return; }
      if (map.getZoom() < LABEL_ZOOM) {
        if (note) note.textContent = 'Zoom in to see the zone numbers on the map.';
        return;
      }
      var b = map.getBounds(), shown = 0, inView = 0;
      zoneData[zoneLevel].features.forEach(function (f) {
        if (!f.properties.label || f.properties.lx == null) return;
        if (!b.contains([f.properties.ly, f.properties.lx])) return;
        inView++;
        if (shown >= LABEL_CAP) return;
        shown++;
        L.marker([f.properties.ly, f.properties.lx], {
          interactive: false, keyboard: false,
          icon: L.divIcon({ className: 'dlabel-wrap',
            html: '<span class="zlabel">' + esc(f.properties.label) + '</span>',
            iconSize: [34, 18], iconAnchor: [17, 9] })
        }).addTo(labelGroup);
      });
      if (note) note.textContent = inView > shown
        ? 'Showing ' + shown + ' of ' + inView + ' zone numbers in view. Zoom in for the rest.'
        : shown + ' zone ' + (shown === 1 ? 'number' : 'numbers') + ' in view.';
    }

    function buildZoneChips() {
      var host = $('#zonechips'); if (!host) return;
      host.innerHTML = '';
      ZLV.forEach(function (z) {
        var b = el('button', 'chip lvl');
        b.type = 'button';
        b.style.setProperty('--pin', z.c);
        b.setAttribute('aria-pressed', z.k === zoneLevel ? 'true' : 'false');
        b.textContent = z.label;
        b.addEventListener('click', function () {
          zoneLevel = z.k;
          show.zone = true;
          var zt = $('#t-zone'); if (zt) zt.setAttribute('aria-pressed', 'true');
          Array.prototype.forEach.call(host.children, function (o) { o.setAttribute('aria-pressed', 'false'); });
          b.setAttribute('aria-pressed', 'true');
          loadZone(z.k).then(function () { drawZones(); buildDirectory(); zoneKey(); });
        });
        host.appendChild(b);
      });
    }

    function buildOverlayChips() {
      var host = $('#overlaychips'); if (!host) return;
      host.innerHTML = '';
      [{ id: 't-zone', k: 'zone', label: 'Zone shading', c: '#1b6ca8' },
       { id: 't-cd', k: 'cd', label: 'Community districts', c: '#06024D' },
       { id: 't-csd', k: 'csd', label: 'School districts', c: '#7a3ea8' }].forEach(function (o) {
        var b = el('button', 'chip lvl');
        b.type = 'button'; b.id = o.id;
        b.style.setProperty('--pin', o.c);
        b.setAttribute('aria-pressed', show[o.k] ? 'true' : 'false');
        b.textContent = o.label;
        b.addEventListener('click', function () {
          show[o.k] = !show[o.k];
          b.setAttribute('aria-pressed', show[o.k] ? 'true' : 'false');
          if (o.k === 'zone') drawZones();
          if (o.k === 'cd') show.cd ? cdLayer.addTo(map) : map.removeLayer(cdLayer);
          if (o.k === 'csd') show.csd ? csdLayer.addTo(map) : map.removeLayer(csdLayer);
        });
        host.appendChild(b);
      });
    }

    /* Quick jumps: pick a community district or a school district and the map
       flies there, instead of pinch-zooming around the whole city. */
    function buildJumpers() {
      var a = $('#jump-cd'), c = $('#jump-csd');
      if (a) {
        a.innerHTML = '<option value="">Jump to a community district...</option>';
        summary.districts.forEach(function (d) {
          var o = document.createElement('option');
          o.value = d.cd; o.textContent = cdLabel(d.cd) + ' \u2014 ' + d.name;
          a.appendChild(o);
        });
        a.addEventListener('change', function () {
          if (!a.value) return;
          var f = cdGj.features.filter(function (x) { return x.properties.cd === a.value; })[0];
          if (!f) return;
          if (!show.cd) { show.cd = true; cdLayer.addTo(map); var t = $('#t-cd'); if (t) t.setAttribute('aria-pressed', 'true'); }
          map.fitBounds(L.geoJSON(f).getBounds(), { padding: [20, 20] });
          if (c) c.value = '';
          document.getElementById('map').scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
      }
      if (c) {
        c.innerHTML = '<option value="">Jump to a school district...</option>';
        csdGj.features.slice().sort(function (x, y) { return x.properties.csd - y.properties.csd; })
          .forEach(function (f) {
            var o = document.createElement('option');
            o.value = f.properties.csd; o.textContent = 'School District ' + f.properties.csd;
            c.appendChild(o);
          });
        c.addEventListener('change', function () {
          if (!c.value) return;
          var f = csdGj.features.filter(function (x) { return String(x.properties.csd) === c.value; })[0];
          if (!f) return;
          if (!show.csd) { show.csd = true; csdLayer.addTo(map); var t = $('#t-csd'); if (t) t.setAttribute('aria-pressed', 'true'); }
          map.fitBounds(L.geoJSON(f).getBounds(), { padding: [20, 20] });
          if (a) a.value = '';
          document.getElementById('map').scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
      }
    }

    function buildDirectory() {
      var host = $('#zonecards'); if (!host) return;
      var gj = zoneData[zoneLevel];
      var q = ($('#zq') ? $('#zq').value : '').trim().toLowerCase();
      var rows = gj.features.filter(function (f) {
        if (!q) return true;
        return (zoneName(f) + ' ' + (f.properties.label || '') + ' ' + (f.properties.csd || '') + ' ' +
          (f.properties.schools || []).map(function (s) { return s.dbn + ' ' + s.addr; }).join(' ')).toLowerCase().indexOf(q) > -1;
      });
      setText('#zone-count', num(rows.length) + ' of ' + num(gj.features.length) + ' zones');
      host.innerHTML = '';
      if (!rows.length) { host.innerHTML = '<div class="empty">No zones match that search.</div>'; return; }
      rows.forEach(function (f) {
        var c = el('div', 'card');
        var t = el('span', 'tag');
        t.style.background = ZLV.filter(function (z) { return z.k === zoneLevel; })[0].c;
        t.textContent = f.properties.zoned ? 'Zone ' + (f.properties.label || f.properties.schools[0].dbn) : 'No zoned school';
        c.appendChild(t);
        c.appendChild(el('h3', null, zoneName(f)));
        var m = el('div', 'meta');
        m.innerHTML = (f.properties.csd ? 'School District ' + esc(f.properties.csd) : '') +
          ((f.properties.schools || []).filter(function (s) { return s.addr; })
            .map(function (s) { return '<br>' + title(s.addr); }).join(''));
        c.appendChild(m);
        c.addEventListener('click', function () {
          if (f.properties.lx == null) return;
          map.setView([f.properties.ly, f.properties.lx], 14);
          document.getElementById('map').scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
        host.appendChild(c);
      });
    }

    function wireAddress() {
      var box = $('#addr'), btn = $('#addr-go');
      if (!box) return;
      var zbox = $('#zq');
      if (zbox) zbox.addEventListener('input', buildDirectory);
      function run() {
        var v = box.value.trim();
        if (!v) return;
        var out = $('#addr-result');
        out.hidden = false;
        out.innerHTML = '<div class="loading">Looking up that address...</div>';
        fetch('https://geosearch.planninglabs.nyc/v2/search?size=5&text=' + encodeURIComponent(v))
          .then(function (r) { return r.json(); })
          .then(function (d) {
            if (!d.features || !d.features.length) {
              out.innerHTML = '<div class="empty">No New York City address matched that. Try adding the borough, for example "250 Baltic Street Brooklyn".</div>';
              return;
            }
            var f = d.features[0], lon = f.geometry.coordinates[0], lat = f.geometry.coordinates[1];
            return Promise.all(ZLV.map(function (z) { return loadZone(z.k); })).then(function () {
              showResult(f, lon, lat, out);
              alternatives(d.features, out);
            });
          })
          .catch(function (e) { out.innerHTML = '<div class="empty">Address lookup failed. ' + esc(e.message) + '</div>'; });
      }
      btn.addEventListener('click', run);
      box.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); run(); } });
    }

    function alternatives(feats, out) {
      /* The geocoder guesses. Show the other candidates so a wrong borough is
         obvious and one tap away from being corrected. */
      var others = feats.slice(1).filter(function (f) {
        return f.properties.label && f.properties.label !== feats[0].properties.label;
      });
      if (!others.length) return;
      var box = el('div', 'alts');
      box.appendChild(el('div', 'alts-h', 'Not the right one? Other addresses matched that search:'));
      others.forEach(function (f) {
        var a = el('button', 'altbtn', f.properties.label);
        a.type = 'button';
        a.addEventListener('click', function () {
          showResult(f, f.geometry.coordinates[0], f.geometry.coordinates[1], out);
          alternatives([f].concat(feats.filter(function (x) { return x !== f; })), out);
        });
        box.appendChild(a);
      });
      out.appendChild(box);
    }

    function showResult(f, lon, lat, out) {
      var cd = findZone(cdGj, lon, lat), csd = findZone(csdGj, lon, lat);
      out.innerHTML = '';
      var h = el('div', 'res-head', f.properties.label || 'That address');
      out.appendChild(h);
      var ctx = el('div', 'res-ctx');
      var cdKey = cd ? cd.properties.cd : null;
      var dRec = cdKey && summary ? summary.districts.filter(function (x) { return x.cd === cdKey; })[0] : null;
      ctx.innerHTML = (dRec ? '<a href="eduhub-' + cdKey + '">' + cdLabel(cdKey) + ' \u2014 ' + esc(dRec.name) + '</a>' : 'Community district not found') +
        (csd ? '  \u00b7  <a href="eduhub-csd-' + csd.properties.csd + '">School District ' + csd.properties.csd + '</a>' : '');
      out.appendChild(ctx);
      ZLV.forEach(function (z) {
        var zf = findZone(zoneData[z.k], lon, lat);
        var block = el('div', 'res-zone');
        var head = el('div', 'res-zone-h');
        head.innerHTML = '<i style="background:' + z.c + '"></i>' + z.label +
          '<img src="assets/eduhub/doe.png" alt="NYC Department of Education" loading="lazy">';
        block.appendChild(head);
        var body = el('div', 'res-zone-b');
        body.innerHTML = zf ? zoneSchoolLines(zf)
          : '<div class="zline muted">This address is not inside a published ' + z.label.toLowerCase() + '.</div>';
        block.appendChild(body);
        out.appendChild(block);
      });
      out.appendChild(el('p', 'note', 'Zone boundaries are the DOE 2024-2025 school zones. Zoning does not guarantee placement, and many high schools admit citywide rather than by zone. Confirm with the school or your enrollment office.'));
      if (hereMarker) map.removeLayer(hereMarker);
      hereMarker = L.marker([lat, lon], {
        icon: L.divIcon({ className: 'dlabel-wrap', html: '<span class="herepin"></span>', iconSize: [22, 22], iconAnchor: [11, 11] })
      }).addTo(map);
      map.setView([lat, lon], 15);
      document.getElementById('map').scrollIntoView({ behavior: 'smooth', block: 'center' });
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

  window.EDU = { hub: hub, district: district, borough: borough, csdHub: csdHub, csdPage: csdPage, zones: zonesPage };
})();
