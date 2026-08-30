/* 311 dashboard for the hub.
   Every count here comes from precomputed files, so nothing waits on a live
   query: 33159by5-rank/cats/pop for community districts (and citywide and
   borough rollups summed from them), and the senate and assembly rank and cats
   files. Each file totals reports by the location the City mapped them to.
   Charts are hand-drawn SVG so the hub carries no charting dependency. */
(function () {
  'use strict';

  var host = document.getElementById('dash');
  if (!host) return;

  var BOROS = ['Bronx', 'Brooklyn', 'Manhattan', 'Queens', 'Staten Island'];
  var SHORT = { BRONX: 'bx', BROOKLYN: 'bk', MANHATTAN: 'mn', QUEENS: 'qn', 'STATEN ISLAND': 'si' };
  var CAT_LABELS = { parking: 'Parking & Vehicles', housing: 'Housing & Buildings', noise: 'Noise',
    streets: 'Streets & Infrastructure', sanitation: 'Sanitation', social: 'Social & Police',
    snow: 'Snow & Weather', food: 'Food & Business', graffiti: 'Graffiti', trees: 'Trees & Parks', other: 'Other' };
  var CAT_COLORS = { parking: '#c1121f', housing: '#2f5fa8', noise: '#e8a33d', streets: '#1f8a80',
    sanitation: '#5c9a3a', social: '#5f6b7a', snow: '#7fd4e8', food: '#8e4ec6', graffiti: '#d9558f',
    trees: '#2f6b3f', other: '#a8a49c' };
  var CAT_ORDER = Object.keys(CAT_LABELS);
  var FILL = ['#fdf3c8', '#fbe07a', '#f7c948', '#e8a020', '#c2410c', '#8a1c05'];

  var LEVELS = {
    city:     { name: 'Citywide', rank: '/data/311-city-rank.json', cats: '/data/311-city-cats.json' },
    boro:     { name: 'Borough', rank: '/data/311-city-rank.json', cats: '/data/311-city-cats.json',
                geo: '/data/borough-boundaries.geojson', geoKey: function (p) { return p.boroname; } },
    cd:       { name: 'Community district', rank: '/33159by5-rank.json', cats: '/33159by5-cats.json',
                geo: '/cd-boundaries-simple.geojson', geoKey: cdGeoKey },
    senate:   { name: 'Senate district', rank: '/data/senate-311-rank.json', cats: '/data/senate-311-cats.json',
                geo: '/data/senate-districts.geojson', geoKey: function (p) { return String(p.sd); } },
    assembly: { name: 'Assembly district', rank: '/data/assembly-311-rank.json', cats: '/data/assembly-311-cats.json',
                geo: '/data/assembly-districts.geojson', geoKey: function (p) { return String(p.ad); } }
  };
  function cdGeoKey(p) {
    var c = String(p.cd), b = { '1': 'MANHATTAN', '2': 'BRONX', '3': 'BROOKLYN', '4': 'QUEENS', '5': 'STATEN ISLAND' }[c[0]];
    return b ? pad2(c.slice(1)) + ' ' + b : '';
  }
  function pad2(n) { return String(Number(n)) .length < 2 ? '0' + Number(n) : String(Number(n)); }
  function fmt(n) { return Number(n || 0).toLocaleString('en-US'); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
    return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]; }); }
  function el(id) { return document.getElementById(id); }

  var S = { level: 'cd', key: '06 BROOKLYN', year: null, cat: '', view: 'trend' };
  var cache = {}, pop = null, map = null, mapLayers = [];

  function get(url) {
    if (cache[url]) return cache[url];
    cache[url] = fetch(url).then(function (r) {
      if (!r.ok) throw new Error(url + ' returned ' + r.status);
      return r.json();
    });
    return cache[url];
  }
  function baseLevel() { return S.level; }
  function files() {
    var L = LEVELS[baseLevel()];
    return Promise.all([get(L.rank), get(L.cats)]);
  }

  function yearsAvailable(rank) { return Object.keys(rank.years).sort(); }

  // total for the current selection in a given year
  function totalIn(rank, cats, year) {
    var t = rank.years[year]; if (!t) return null;
    var k = S.level === 'city' ? 'NYC' : S.key;
    return S.cat ? catVal(cats, year, k) : (t[k] == null ? null : t[k]);
  }
  function catVal(cats, year, k) {
    var y = cats.years[year]; if (!y || !y[k]) return null;
    return y[k][S.cat] || 0;
  }
  // every unit at the current level, for maps and rankings
  function unitsIn(rank, cats, year) {
    var t = rank.years[year] || {}, out = [];
    Object.keys(t).forEach(function (k) {
      if (k === 'NYC') return;                 // the citywide row is not a unit
      out.push({ key: k, n: S.cat ? (catVal(cats, year, k) || 0) : t[k] });
    });
    return out.sort(function (a, b) { return b.n - a.n; });
  }
  function unitLabel(k) {
    if (S.level === 'boro' || S.level === 'city') return k === 'NYC' ? 'New York City' : k;
    if (baseLevel() === 'cd') {
      var p = k.split(' '), b = p.slice(1).join(' ');
      return b.charAt(0) + b.slice(1).toLowerCase() + ' CD ' + Number(p[0]);
    }
    return (baseLevel() === 'senate' ? 'SD ' : 'AD ') + k;
  }
  function scopeLabel() {
    if (S.level === 'city') return 'New York City';
    if (S.level === 'boro') return S.key;
    return unitLabel(S.key);
  }
  function reportLink() {
    if (S.level === 'city') return '/311-citywide.html';
    if (S.level === 'boro') return '/33159by5.html#level=boro&boro=' + encodeURIComponent(S.key);
    if (S.level === 'senate') return '/311-senate.html?sd=' + S.key + '&year=' + S.year;
    if (S.level === 'assembly') return '/311-assembly.html?ad=' + S.key + '&year=' + S.year;
    var p = S.key.split(' ');
    return '/311-district.html?cd=' + SHORT[p.slice(1).join(' ')] + '-' + Number(p[0]) + '&year=' + S.year;
  }

  /* ---------------- controls ---------------- */
  host.innerHTML =
    '<div class="dsh">' +
      '<div class="dsh-t">311 dashboard<span>Pick a geography, a year and a view. Every figure is precomputed, so nothing waits on a query.</span></div>' +
      '<div class="dsh-r"><label>Geography</label><div class="seg" id="dLevel"></div></div>' +
      '<div class="dsh-r" id="dUnitRow"><label id="dUnitLbl">District</label><select id="dUnit"></select></div>' +
      '<div class="dsh-r dsh-2">' +
        '<div><label>Year</label><select id="dYear"></select></div>' +
        '<div><label>Category</label><select id="dCat"></select></div>' +
      '</div>' +
      '<div class="dsh-r"><label>View</label><div class="seg" id="dView"></div></div>' +
      '<div class="dsh-out" id="dOut"><div class="dsh-load">Loading</div></div>' +
      '<a class="dsh-go" id="dGo" href="#">Open the full report</a>' +
    '</div>';

  el('dLevel').innerHTML = Object.keys(LEVELS).map(function (k) {
    return '<button type="button" data-l="' + k + '">' + LEVELS[k].name + '</button>';
  }).join('');
  el('dView').innerHTML = [['trend', 'Trend'], ['cats', 'Categories'], ['map', 'Map'], ['rank', 'Rankings']]
    .map(function (v) { return '<button type="button" data-v="' + v[0] + '">' + v[1] + '</button>'; }).join('');
  el('dCat').innerHTML = '<option value="">All categories</option>' +
    CAT_ORDER.map(function (c) { return '<option value="' + c + '">' + CAT_LABELS[c] + '</option>'; }).join('');

  el('dLevel').addEventListener('click', function (e) {
    var b = e.target.closest('button[data-l]'); if (!b) return;
    S.level = b.getAttribute('data-l');
    S.key = S.level === 'boro' ? 'Brooklyn' : (S.level === 'cd' ? '06 BROOKLYN' : (S.level === 'senate' ? '26' : '52'));
    if (S.level === 'city') S.key = '';
    if (S.view === 'map' && S.level === 'city') S.view = 'trend';
    boot();
  });
  el('dView').addEventListener('click', function (e) {
    var b = e.target.closest('button[data-v]'); if (!b) return;
    S.view = b.getAttribute('data-v'); render();
  });
  el('dUnit').addEventListener('change', function () { S.key = this.value; render(); });
  el('dYear').addEventListener('change', function () { S.year = this.value; render(); });
  el('dCat').addEventListener('change', function () { S.cat = this.value; render(); });

  function syncSeg() {
    Array.prototype.forEach.call(el('dLevel').children, function (b) {
      b.className = b.getAttribute('data-l') === S.level ? 'on' : '';
    });
    Array.prototype.forEach.call(el('dView').children, function (b) {
      var v = b.getAttribute('data-v');
      b.className = v === S.view ? 'on' : '';
      b.disabled = (v === 'map' || v === 'rank') && S.level === 'city';
    });
  }

  function boot() {
    files().then(function (r) {
      var rank = r[0], cats = r[1], ys = yearsAvailable(rank);
      if (!S.year || ys.indexOf(S.year) === -1) S.year = ys[ys.length - 1];
      el('dYear').innerHTML = ys.slice().reverse().map(function (y) {
        return '<option value="' + y + '">' + y + '</option>';
      }).join('');
      el('dYear').value = S.year;

      var showUnit = (S.level !== 'city');
      el('dUnitRow').style.display = showUnit ? '' : 'none';
      if (showUnit) {
        el('dUnitLbl').textContent = S.level === 'boro' ? 'Borough' : LEVELS[S.level].name;
        var opts;
        {
          opts = Object.keys(rank.years[S.year]).sort(function (a, b) {
            return (S.level === 'cd' || S.level === 'boro') ? a.localeCompare(b) : Number(a) - Number(b);
          }).filter(function (k) { return k !== 'NYC'; }).map(function (k) { return { v: k, t: unitLabel(k) }; });
        }
        el('dUnit').innerHTML = opts.map(function (o) {
          return '<option value="' + esc(o.v) + '">' + esc(o.t) + '</option>';
        }).join('');
        el('dUnit').value = S.key;
      }
      render();
    }).catch(function (err) {
      el('dOut').innerHTML = '<div class="dsh-err">' + esc(err.message) + '</div>';
    });
  }

  /* ---------------- views ---------------- */
  function render() {
    syncSeg();
    el('dGo').setAttribute('href', reportLink());
    files().then(function (r) {
      var rank = r[0], cats = r[1];
      if (S.view === 'trend') return drawTrend(rank, cats);
      if (S.view === 'cats') return drawCats(rank, cats);
      if (S.view === 'rank') return drawRank(rank, cats);
      return drawMap(rank, cats);
    }).catch(function (err) {
      el('dOut').innerHTML = '<div class="dsh-err">' + esc(err.message) + '</div>';
    });
  }

  /* Citywide is a straight count of every report. Boroughs take the ones the City
     labelled, plus the unlabelled ones placed by their coordinates. What is left
     over has neither a borough nor a location and cannot be placed by anyone. */
  var cityRank = null;
  function rollupNote() {
    if (S.level !== 'city' && S.level !== 'boro') return '';
    var u = cityRank && cityRank.unplaceable && cityRank.unplaceable[S.year];
    return u ? ' Reports the City published with a borough are counted there; those it left blank are placed by their coordinates. ' +
      fmt(u) + ' reports in ' + S.year + ' have neither and appear only in the citywide figure.' : '';
  }

  function headline(rank, cats) {
    var n = totalIn(rank, cats, S.year);
    var what = S.cat ? CAT_LABELS[S.cat] + ' reports' : '311 reports';
    var h = '<div class="dsh-h"><b>' + fmt(n) + '</b> ' + what + ' in ' + esc(scopeLabel()) + ', ' + S.year;
    if (S.level === 'cd' && !S.cat && pop && pop.districts[S.key]) {
      var p = pop.districts[S.key].y2010;
      if (p) h += ' <i>' + (n / p * 1000).toFixed(0) + ' per 1,000 residents, 2010 Census</i>';
    }
    if (!S.cat && cats.years[S.year] && cats.years[S.year][S.key] && S.level !== 'city' && S.level !== 'boro') {
      h += ' <i>Most common single type: ' + esc(cats.years[S.year][S.key]._t) +
           ', ' + fmt(cats.years[S.year][S.key]._tn) + '</i>';
    }
    return h + '</div>';
  }

  function drawTrend(rank, cats) {
    var ys = yearsAvailable(rank);
    var pts = ys.map(function (y) { return { y: y, n: totalIn(rank, cats, y) || 0 }; });
    var W = 640, H = 220, PL = 52, PR = 12, PT = 14, PB = 26;
    var max = Math.max.apply(null, pts.map(function (p) { return p.n; })) || 1;
    var x = function (i) { return PL + i * (W - PL - PR) / Math.max(1, pts.length - 1); };
    var yv = function (n) { return PT + (1 - n / max) * (H - PT - PB); };
    var line = pts.map(function (p, i) { return (i ? 'L' : 'M') + x(i).toFixed(1) + ' ' + yv(p.n).toFixed(1); }).join(' ');
    var area = line + ' L' + x(pts.length - 1).toFixed(1) + ' ' + (H - PB) + ' L' + PL + ' ' + (H - PB) + ' Z';
    var grid = '', ticks = 4;
    for (var g = 0; g <= ticks; g++) {
      var v = max * g / ticks, gy = yv(v);
      grid += '<line x1="' + PL + '" x2="' + (W - PR) + '" y1="' + gy.toFixed(1) + '" y2="' + gy.toFixed(1) + '" stroke="#e3e0d2"/>' +
        '<text x="' + (PL - 6) + '" y="' + (gy + 4).toFixed(1) + '" text-anchor="end" class="ax">' +
        (v >= 1000 ? Math.round(v / 1000) + 'k' : Math.round(v)) + '</text>';
    }
    var lab = pts.map(function (p, i) {
      if (pts.length > 9 && i % 2) return '';
      return '<text x="' + x(i).toFixed(1) + '" y="' + (H - 8) + '" text-anchor="middle" class="ax">' + p.y.slice(2) + '</text>';
    }).join('');
    var dots = pts.map(function (p, i) {
      return '<circle cx="' + x(i).toFixed(1) + '" cy="' + yv(p.n).toFixed(1) + '" r="' + (p.y === S.year ? 5 : 3) + '" ' +
        'fill="' + (p.y === S.year ? '#c2410c' : '#1b1b1a') + '"><title>' + p.y + ': ' + fmt(p.n) + '</title></circle>';
    }).join('');
    el('dOut').innerHTML = headline(rank, cats) +
      '<svg viewBox="0 0 ' + W + ' ' + H + '" class="dsh-svg" role="img" aria-label="Reports by year">' +
      grid + '<path d="' + area + '" fill="#f7c94833"/><path d="' + line + '" fill="none" stroke="#1b1b1a" stroke-width="2"/>' +
      dots + lab + '</svg>' +
      '<div class="dsh-n">Every year on file for this geography' +
      (S.level === 'senate' || S.level === 'assembly' ? ', 2020 forward' : ', 2010 forward') +
      '. The filled point is the year selected above.' + rollupNote() + '</div>';
  }

  /* Categories view is a bar chart race over every year on file, the same shape
     as the one on the CB6 311 page: the bars reorder as the years advance so the
     leading complaint is obvious without reading a number. Rows keep their place
     in the DOM and move by transform, which is what lets them slide rather than
     jump. */
  var race = { years: [], i: 0, playing: false, timer: null, ms: 900 };
  var ROWH = 30;

  function catRow(cats, year) {
    var y = cats.years[year] || {};
    return y[S.level === 'city' ? 'NYC' : S.key] || {};
  }

  function drawCats(rank, cats) {
    race.years = yearsAvailable(rank);
    race.i = Math.max(0, race.years.indexOf(S.year));
    stopRace();

    el('dOut').innerHTML = headline(rank, cats) +
      '<div class="rc-top">' +
        '<div><div class="rc-k">Bar chart race</div><div class="rc-y" id="rcYear">' + esc(S.year) + '</div></div>' +
        '<div class="rc-ctl">' +
          '<button type="button" id="rcPlay">&#9654; Play</button>' +
          '<button type="button" id="rcBack" title="Start over">&#8634;</button>' +
          '<span class="rc-sp">Speed<input type="range" id="rcSpeed" min="200" max="2000" step="100" value="1300"></span>' +
        '</div>' +
      '</div>' +
      '<div class="rc-lead" id="rcLead"></div>' +
      '<div class="rc-scrub"><span id="rcMin">' + esc(race.years[0]) + '</span>' +
        '<input type="range" id="rcScrub" min="0" max="' + (race.years.length - 1) + '" value="' + race.i + '">' +
        '<span id="rcMax">' + esc(race.years[race.years.length - 1]) + '</span></div>' +
      '<div class="rc-bars" id="rcBars" style="height:' + (CAT_ORDER.length * ROWH) + 'px">' +
        CAT_ORDER.map(function (c) {
          return '<div class="rc-row" data-c="' + c + '" id="rc-' + c + '">' +
            '<span class="bl">' + CAT_LABELS[c] + '</span>' +
            '<span class="bt"><i style="background:' + CAT_COLORS[c] + '"></i></span>' +
            '<span class="bn"></span></div>';
        }).join('') +
      '</div>' +
      '<div class="dsh-n">Press play to watch the order change year by year, or drag the slider to any year. ' +
      'Tap a bar to filter every other view to that category. The same eleven buckets are used across the site, so years and geographies compare.' +
      rollupNote() + '</div>';

    el('rcPlay').addEventListener('click', function () { race.playing ? stopRace() : playRace(); });
    el('rcBack').addEventListener('click', function () { stopRace(); frame(0, true); });
    el('rcSpeed').addEventListener('input', function () { race.ms = 2200 - Number(this.value); });
    el('rcScrub').addEventListener('input', function () { stopRace(); frame(Number(this.value), true); });
    Array.prototype.forEach.call(el('rcBars').children, function (r) {
      r.addEventListener('click', function () {
        var c = r.getAttribute('data-c');
        S.cat = (S.cat === c) ? '' : c;
        el('dCat').value = S.cat;
        render();
      });
    });
    frame(race.i, true);
  }

  function frame(i, syncYear) {
    if (!el('rcBars')) return;
    race.i = i;
    var year = race.years[i];
    el('rcYear').textContent = year;
    el('rcScrub').value = i;

    files().then(function (r) {
      var row = catRow(r[1], year);
      var vals = CAT_ORDER.map(function (c) { return { c: c, n: row[c] || 0 }; });
      var sum = vals.reduce(function (a, v) { return a + v.n; }, 0) || 1;
      var ranked = vals.slice().sort(function (a, b) { return b.n - a.n; });
      var max = ranked[0].n || 1;
      ranked.forEach(function (v, rank) {
        var node = el('rc-' + v.c);
        if (!node) return;
        node.style.transform = 'translateY(' + (rank * ROWH) + 'px)';
        node.className = 'rc-row' + (S.cat === v.c ? ' on' : '') + (rank === 0 ? ' first' : '');
        node.querySelector('.bt i').style.width = Math.max(1.5, v.n / max * 100).toFixed(1) + '%';
        node.querySelector('.bn').innerHTML = fmt(v.n) + '<em>' + (v.n / sum * 100).toFixed(1) + '%</em>';
      });
      var top = ranked[0];
      el('rcLead').innerHTML = '<b>' + CAT_LABELS[top.c] + '</b> leads ' + esc(scopeLabel()) + ' in ' + year +
        ', ' + fmt(top.n) + ' reports, ' + (top.n / sum * 100).toFixed(0) + '% of everything' +
        (ranked[1] && ranked[1].n ? ', ' + (top.n / ranked[1].n).toFixed(1) + 'x the next category' : '') +
        (row._t ? '<i>Most common single type: ' + esc(row._t) + ', ' + fmt(row._tn) + '</i>' : '');
      if (syncYear && year !== S.year) { S.year = year; el('dYear').value = year; }
    });
  }

  function playRace() {
    if (race.i >= race.years.length - 1) race.i = 0;
    race.playing = true;
    el('rcPlay').innerHTML = '&#10073;&#10073; Pause';
    stepRace();
  }
  // race.i always names the frame currently on screen, so pausing lands on the
  // year the label is showing rather than the one queued next.
  function stepRace() {
    if (!race.playing) return;
    frame(race.i, false);
    race.timer = setTimeout(function () {
      if (!race.playing) return;
      if (race.i >= race.years.length - 1) { stopRace(); return; }
      race.i++;
      stepRace();
    }, race.ms);
  }
  function stopRace() {
    race.playing = false;
    clearTimeout(race.timer);
    var b = el('rcPlay');
    if (b) b.innerHTML = '&#9654; Play';
    var y = race.years[race.i];
    if (y && y !== S.year) { S.year = y; if (el('dYear')) el('dYear').value = y; }
  }

  function drawRank(rank, cats) {
    var us = unitsIn(rank, cats, S.year);
    var all = rank.years[S.year] || {};
    var cityTotal = Object.keys(all).reduce(function (a, k) {
      return a + (S.cat ? (catVal(cats, S.year, k) || 0) : all[k]);
    }, 0) || 1;
    var rows = us.map(function (u, i) {
      return '<tr' + (u.key === S.key ? ' class="me"' : '') + '><td>' + (i + 1) + '</td>' +
        '<td>' + esc(unitLabel(u.key)) + '</td><td class="r">' + fmt(u.n) + '</td>' +
        '<td class="r">' + (u.n / cityTotal * 100).toFixed(1) + '%</td></tr>';
    }).join('');
    el('dOut').innerHTML = headline(rank, cats) +
      '<div class="dsh-tw"><table class="dsh-tbl"><thead><tr><th></th><th>District</th><th class="r">Reports</th>' +
      '<th class="r">Share</th></tr></thead><tbody>' + rows + '</tbody></table></div>' +
      '<div class="dsh-n">Share is of the total for every district shown, same year and category. The highlighted row is your selection.' + rollupNote() + '</div>';
  }

  function drawMap(rank, cats) {
    var L = LEVELS[baseLevel()];
    el('dOut').innerHTML = headline(rank, cats) + '<div class="dsh-legend" id="dLeg"></div>' +
      '<div class="dsh-map" id="dMap"></div>' +
      '<div class="dsh-n">Shaded by report count for the year and category selected. Tap any district to switch to it.' + rollupNote() + '</div>';
    if (typeof L === 'undefined' || typeof window.L === 'undefined') {
      el('dOut').innerHTML = '<div class="dsh-err">The map needs Leaflet, which did not load.</div>';
      return;
    }
    get(LEVELS[baseLevel()].geo).then(function (geo) {
      var us = unitsIn(rank, cats, S.year), vals = us.map(function (u) { return u.n; }).sort(function (a, b) { return a - b; });
      var stops = [0.2, 0.4, 0.6, 0.8, 0.93].map(function (p) { return vals[Math.floor(vals.length * p)] || 0; });
      var byKey = {}; us.forEach(function (u) { byKey[u.key] = u.n; });
      function color(n) {
        if (n == null) return '#e9e7e0';
        for (var i = 0; i < stops.length; i++) if (n < stops[i]) return FILL[i];
        return FILL[FILL.length - 1];
      }
      var node = el('dMap');
      map = window.L.map(node, { scrollWheelZoom: false });
      window.L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e',
        { maxZoom: 19, attribution: '&copy; OpenStreetMap &copy; CARTO' }).addTo(map);
      var keyOf = LEVELS[baseLevel()].geoKey;
      var feats = geo.features.filter(function (f) {
        var k = keyOf(f.properties || {});
        return k && byKey[k] != null;
      });
      var layer = window.L.geoJSON({ type: 'FeatureCollection', features: feats }, {
        style: function (f) {
          var k = keyOf(f.properties);
          return { color: '#fff', weight: 1, opacity: .85, fillColor: color(byKey[k]), fillOpacity: .72 };
        },
        onEachFeature: function (f, ly) {
          var k = keyOf(f.properties);
          ly.bindTooltip(unitLabel(k) + ' \u00b7 ' + fmt(byKey[k]), { sticky: true });
          ly.on('click', function () {
            if (S.level === 'boro') return;
            S.key = k; el('dUnit').value = k; render();
          });
        }
      }).addTo(map);
      var here = feats.filter(function (f) { return keyOf(f.properties) === S.key; });
      if (here.length) {
        var o = window.L.geoJSON({ type: 'FeatureCollection', features: here },
          { style: { color: '#111110', weight: 3, fill: false } }).addTo(map);
        map.fitBounds(o.getBounds(), { padding: [16, 16] });
      } else {
        map.fitBounds(layer.getBounds(), { padding: [10, 10] });
      }
      var bands = ['under ' + fmt(stops[0])];
      for (var i = 1; i < stops.length; i++) bands.push(fmt(stops[i - 1]) + ' to ' + fmt(stops[i]));
      bands.push(fmt(stops[stops.length - 1]) + ' and up');
      el('dLeg').innerHTML = FILL.map(function (c, i) {
        return '<span class="lk"><i style="background:' + c + '"></i>' + bands[i] + '</span>';
      }).join('');
    });
  }

  get('/33159by5-pop.json').then(function (p) { pop = p; }).catch(function () { pop = null; });
  get('/data/311-city-rank.json').then(function (r) { cityRank = r; }).catch(function () { cityRank = null; });
  boot();
})();
