/* The district in numbers: on each Council, Assembly, State Senate and Congress profile.
   <div data-district-dash="council-39"></div> reads /data/dashboards/council-39.json (scripts/district_dashboards.py).
   Every figure is as published for the district itself: population from the body that drew the lines, 311 requests
   counted by district. Figures that only exist by community district are left to each community board's page. */
(function () {
  'use strict';
  var CAT = { parking: ['Parking and vehicles', '#c1121f'], housing: ['Housing and buildings', '#2f5fa8'], noise: ['Noise', '#e8a33d'],
    streets: ['Streets and sidewalks', '#1f8a80'], sanitation: ['Sanitation', '#5c9a3a'], social: ['Social services and police', '#5f6b7a'],
    snow: ['Snow and ice', '#7fd4e8'], food: ['Food and business', '#8e4ec6'], graffiti: ['Graffiti', '#d9558f'], trees: ['Trees', '#2f6b3f'],
    other: ['Other', '#a8a49c'] };
  var RACE = ['#0d1b4b', '#f47920', '#0f766e', '#7c3aed', '#a8a49c'];
  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (m) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m]; }); }
  function fmt(n) { return Number(n).toLocaleString('en-US'); }
  function pct(a, b) { return b ? Math.round(a / b * 1000) / 10 : 0; }
  function css() {
    if (document.getElementById('ddash-css')) return;
    var s = document.createElement('style'); s.id = 'ddash-css';
    s.textContent = '.dd{font-family:"DM Sans",sans-serif;color:#0d1b4b}'
      + '.dd-tiles{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:4px 0 16px}'
      + '@media(min-width:640px){.dd-tiles{grid-template-columns:repeat(4,1fr)}}'
      + '.dd-tile{background:#fff;border:1.5px solid #e5e2db;border-radius:14px;padding:12px 14px}'
      + '.dd-tile .v{font-size:1.55rem;font-weight:800;line-height:1.1;letter-spacing:-.01em}'
      + '.dd-tile .v.sm{font-size:1rem;line-height:1.25}'
      + '.dd-tile .k{font-family:"DM Mono",monospace;font-size:.62rem;letter-spacing:.08em;text-transform:uppercase;color:#6b6760;margin-top:6px;line-height:1.35}'
      + '.dd-card{background:#fff;border:1.5px solid #e5e2db;border-radius:14px;padding:14px 16px;margin:0 0 14px}'
      + '.dd-card h3{margin:0 0 2px;font-size:1.02rem;font-weight:800}'
      + '.dd-card .sub{font-size:.8rem;color:#6b6760;margin:0 0 12px}'
      + '.dd-row{display:grid;grid-template-columns:minmax(110px,40%) 1fr auto;align-items:center;gap:10px;margin:7px 0;font-size:.86rem}'
      + '.dd-bar{height:14px;border-radius:7px;background:#f1efe9;overflow:hidden}'
      + '.dd-bar span{display:block;height:100%;border-radius:7px}'
      + '.dd-row .n{font-family:"DM Mono",monospace;font-size:.75rem;color:#374151;white-space:nowrap;text-align:right}'
      + '.dd-cols{display:flex;align-items:flex-end;gap:8px;height:150px;margin:8px 0 4px;padding-top:18px}'
      + '.dd-col{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;min-width:0}'
      + '.dd-col .b{width:100%;max-width:46px;border-radius:7px 7px 0 0;background:#0d1b4b;position:relative}'
      + '.dd-col .b.ytd{background:repeating-linear-gradient(45deg,#f47920,#f47920 5px,#f9a466 5px,#f9a466 10px)}'
      + '.dd-col .t{font-family:"DM Mono",monospace;font-size:.6rem;color:#374151;margin-bottom:3px;white-space:nowrap}'
      + '.dd-col .y{font-family:"DM Mono",monospace;font-size:.68rem;color:#6b6760;margin-top:5px}'
      + '.dd-chips{display:flex;flex-wrap:wrap;gap:8px}'
      + '.dd-chip{display:inline-flex;align-items:center;gap:8px;border:1.5px solid #e5e2db;border-radius:999px;padding:4px 12px 4px 4px;text-decoration:none;color:#0d1b4b;font-weight:600;font-size:.88rem;background:#fff}'
      + '.dd-chip img{width:28px;height:28px;border-radius:50%;object-fit:contain;background:#fff}'
      + '.dd-chip small{display:block;font-weight:500;font-size:.7rem;color:#6b6760}'
      + '.dd-tbl{overflow-x:auto;-webkit-overflow-scrolling:touch}'
      + '.dd-tbl table{border-collapse:collapse;width:100%;min-width:640px;font-size:.84rem}'
      + '.dd-tbl th{font-family:"DM Mono",monospace;font-size:.6rem;letter-spacing:.06em;text-transform:uppercase;color:#6b6760;text-align:right;padding:6px 8px;border-bottom:1.5px solid #e5e2db;vertical-align:bottom}'
      + '.dd-tbl th:first-child,.dd-tbl td:first-child{text-align:left}'
      + '.dd-tbl th small,.dd-tbl td small{display:block;text-transform:none;letter-spacing:0;font-size:.62rem;color:#9ca3af;font-weight:400}'
      + '.dd-tbl td{text-align:right;padding:7px 8px;border-bottom:1px solid #f1efe9;font-weight:600}'
      + '.dd-tbl td a{color:#0d1b4b}' + '.dd-tbl td:first-child,.dd-tbl th:first-child{white-space:nowrap;min-width:120px}' + '.dd-tbl td{white-space:nowrap}' + '.dd-tbl th{min-width:96px}'
      + '.dd-tbl tr.city td{color:#6b6760;font-weight:500}'
      + '.dd-src{font-family:"DM Mono",monospace;font-size:.62rem;color:#6b6760;line-height:1.5;margin-top:4px}';
    document.head.appendChild(s);
  }
  function bars(rows, total, color) {
    var max = Math.max.apply(null, rows.map(function (r) { return r[1]; }).concat([1]));
    return rows.map(function (r, i) {
      var c = typeof color === 'function' ? color(r, i) : color;
      return '<div class="dd-row"><span>' + esc(r[0]) + '</span><span class="dd-bar"><span style="width:' + (r[1] / max * 100).toFixed(1) + '%;background:' + c + '"></span></span>'
        + '<span class="n">' + fmt(r[1]) + (total ? ' · ' + pct(r[1], total) + '%' : '') + '</span></div>';
    }).join('');
  }
  function render(el, d) {
    css();
    var h = '<div class="dd">', p = d.population, s = d['311'] || {}, yrs = Object.keys(s.years || {}).sort();
    var now = new Date().getFullYear(), full = yrs.filter(function (y) { return +y < now; }), last = full[full.length - 1], cur = String(now);
    var cats = (s.cats || {})[last] || {};
    var tiles = [];
    if (p) tiles.push(['<div class="v">' + fmt(p.pop) + '</div>', 'Residents · ' + esc(p.pop_label)]);
    if (last) tiles.push(['<div class="v">' + fmt(s.years[last]) + '</div>', '311 requests in ' + last]);
    if (s.years && s.years[cur] != null) tiles.push(['<div class="v">' + fmt(s.years[cur]) + '</div>', '311 requests in ' + cur + ' so far' + (d['311_built'] ? ', through ' + esc(d['311_built']) : '')]);
    if (cats._t) tiles.push(['<div class="v sm">' + esc(cats._t) + '</div>', 'Most common 311 request in ' + last + ' · ' + fmt(cats._tn)]);
    h += '<div class="dd-tiles">' + tiles.map(function (t) { return '<div class="dd-tile">' + t[0] + '<div class="k">' + t[1] + '</div></div>'; }).join('') + '</div>';
    if (p && p.race) {
      var rr = Object.keys(p.race).map(function (k) { return [k, p.race[k]]; });
      var tot = p.race_of === 'all residents' ? p.pop : p.vap;
      h += '<div class="dd-card"><h3>Who lives here</h3><p class="sub">Race and ethnicity of ' + esc(p.race_of) + ', 2020 Census' + (p.race_of !== 'all residents' ? ' (' + fmt(p.vap) + ' people), as the Districting Commission published it' : '') + '</p>'
        + bars(rr, tot, function (r, i) { return RACE[i % RACE.length]; }) + '</div>';
    }
    if (yrs.length) {
      var mx = Math.max.apply(null, yrs.map(function (y) { return s.years[y]; }));
      h += '<div class="dd-card"><h3>311 requests each year</h3><p class="sub">Every request to 311 ' + (d.district.indexOf('council') === 0 ? 'the City recorded in this council district' : 'made from a location inside the district') + (s.years[cur] != null ? '. ' + cur + ' is the year so far.' : '') + '</p><div class="dd-cols">'
        + yrs.map(function (y) { var v = s.years[y]; return '<div class="dd-col"><div class="t">' + fmt(v) + '</div><div class="b' + (y === cur ? ' ytd' : '') + '" style="height:' + Math.max(2, v / mx * 100).toFixed(1) + '%"></div><div class="y">' + y + '</div></div>'; }).join('')
        + '</div></div>';
    }
    if (last && Object.keys(cats).length) {
      var cr = Object.keys(CAT).filter(function (k) { return cats[k]; }).map(function (k) { return [CAT[k][0], cats[k], k]; }).sort(function (a, b) { return b[1] - a[1]; });
      var ct = cr.reduce(function (a, r) { return a + r[1]; }, 0);
      h += '<div class="dd-card"><h3>What people called 311 about in ' + last + '</h3><p class="sub">' + fmt(ct) + ' requests, grouped by kind</p>'
        + bars(cr, ct, function (r) { return CAT[r[2]][1]; }) + '</div>';
    }
    if (d.boards && d.boards.length && (X.wk || X.resp)) {
      var BN = { '1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island' };
      var boros = []; d.boards.forEach(function (b) { var n = BN[b.cd.charAt(0)]; if (n && boros.indexOf(n) < 0) boros.push(n); });
      var W = X.wk || {}, Wd = (W.d || {})[d.district], wkE = W.week || '';
      var spark = function (arr, color, unit) { arr = arr || []; var mx = Math.max.apply(null, arr.filter(function (v) { return v != null; }).concat([0.0001])); return '<div class="dd-cols" style="height:90px">' + arr.map(function (v, i) { return '<div class="dd-col"><div class="t">' + (i === arr.length - 1 && v != null ? (unit === '%' ? v + '%' : fmt(v)) : '') + '</div><div class="b" style="background:' + color + ';height:' + (v == null ? 0 : Math.max(2, v / mx * 100)).toFixed(1) + '%"></div></div>'; }).join('') + '</div>'; };
      var lab = function (t) { return '<div style="font-family:DM Mono,monospace;font-size:.62rem;letter-spacing:.08em;text-transform:uppercase;color:#6b6760">' + t + '</div>'; };
      var chg = function (arr) { if (!arr || arr.length < 2) return ''; var a2 = arr[arr.length - 2], b2 = arr[arr.length - 1]; if (a2 == null || b2 == null) return ''; return b2 > a2 ? '<b style="color:#b91c1c">up</b> from ' + a2 + '%' : b2 < a2 ? '<b style="color:#15803d">down</b> from ' + a2 + '%' : 'same as the week before'; };
      h += '<div class="dd-card"><h3>COVID-19 and flu this week</h3><p class="sub">Week ending ' + esc(wkE) + ', from the Health Department\u2019s weekly respiratory illness data.</p>';
      if (Wd) {
        h += '<div class="dd-tiles" style="margin:0 0 10px">'
          + '<div class="dd-tile"><div class="v">' + (Wd.covid == null ? '\u2013' : Wd.covid) + '</div><div class="k">COVID-19 cases per 100,000 residents this week*</div></div>'
          + '<div class="dd-tile"><div class="v">' + (Wd.flu == null ? '\u2013' : Wd.flu) + '</div><div class="k">Flu cases per 100,000 residents this week*</div></div>'
          + '<div class="dd-tile"><div class="v">' + (Wd.ed == null ? '\u2013' : Wd.ed + '%') + '</div><div class="k">Emergency room visits for respiratory illness*</div></div></div>';
      }
      boros.forEach(function (bn) {
        var ce = W.covid_ed && W.covid_ed[bn], fe = W.flu_ed && W.flu_ed[bn];
        h += '<div style="margin:12px 0 4px;font-weight:800">' + esc(bn) + '</div>';
        if (ce) h += '<p class="sub" style="margin:0 0 6px">Emergency room visits with a COVID-19 diagnosis: <b>' + ce[ce.length - 1] + '%</b>, ' + chg(ce) + '. With a flu diagnosis: <b>' + fe[fe.length - 1] + '%</b>, ' + chg(fe) + '.</p>';
        h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px"><div>' + lab('COVID-19 ER visits, % of all') + spark(ce, '#6d28d9', '%') + '</div><div>' + lab('Flu ER visits, % of all') + spark(fe, '#0f766e', '%') + '</div>'
          + (X.resp ? '<div>' + lab('COVID-19 cases') + spark(X.resp.covid[bn], '#6d28d9') + '</div><div>' + lab('Flu cases') + spark(X.resp.flu[bn], '#0f766e') + '</div>' : '') + '</div>';
      });
      var Z = X.zip && X.zip.d && X.zip.d[d.district];
    if (Z) {
      var zc = X.zip.city || {};
      var zt = [[fmt(Z.cases), 'COVID-19 cases since 2020*', fmt(Z.case_rate) + ' per 100,000 \u00b7 city ' + fmt(zc.case_rate)],
                [fmt(Z.deaths), 'COVID-19 deaths since 2020*', fmt(Z.death_rate) + ' per 100,000 \u00b7 city ' + fmt(zc.death_rate)],
                [Z.vax_pct + '%', 'Residents with at least one COVID-19 vaccine dose*', 'city ' + zc.vax_pct + '%']];
      h += '<div class="dd-card"><h3>COVID-19 since 2020*</h3><p class="sub">Cases and deaths through ' + esc(X.zip.cases_asof) + '; vaccination as of ' + esc(X.zip.vax_asof) + ', when the Health Department stopped updating it.</p>'
        + '<div class="dd-tiles" style="margin:0 0 8px">' + zt.map(function (t) { return '<div class="dd-tile"><div class="v">' + t[0] + '</div><div class="k">' + t[1] + '</div><div class="k" style="margin-top:3px">' + t[2] + '</div></div>'; }).join('') + '</div>'
        + '<div class="dd-src">* Estimated. The Health Department publishes these only by ZIP code. Each ZIP code\u2019s counts are split by the share of its land inside the district, which assumes people and cases are spread evenly across the ZIP code, so the figures point the right way but are not exact. ZIP codes counted, with the share of each inside the district: '
        + Z.zips.filter(function (z) { return z[0] !== '99999'; }).map(function (z) { return esc(z[0]) + ' ' + z[1] + '%'; }).join(', ') + '. City figures count only cases with a known ZIP code. Vaccination can read above 100% in some ZIP codes, as the Health Department notes, because its population figures are estimates. Source: ' + esc(X.zip.sources) + '.</div></div>';
    }
    if (d.boards && d.boards.length) {
      var CD = X.cd || {}, M = (X.cd && X.cd.chp) || {}, C = (X.cd && X.cd.cd) || {};
      var f1 = function (v, u) { return v == null ? '\u2013' : (u === 'percent' ? (Math.round(v * 10) / 10) + '%' : u === 'people' ? fmt(Math.round(v)) : (Math.round(v * 10) / 10)); };
      var cols = ['Overall_Pop', 'Life_Expectancy', 'Flu_Vaccination', 'Poverty', 'Rent_Burden'].filter(function (k) { return M[k]; });
      h += '<div class="dd-card"><h3>By community district</h3><p class="sub">Some figures are only published by community district, so they are shown for each community district this district covers, with how many of its ' + fmt(d.eds) + ' election districts fall in each. They are not added together.</p>'
        + '<div class="dd-chips" style="margin-bottom:12px">' + d.boards.map(function (b) { return '<a class="dd-chip" href="' + esc(b.url) + '"><img src="/app/data/Logos/cb' + esc(b.cd) + '.png" alt="" onerror="this.style.display=\'none\'"><span>' + esc(b.name) + '<small>' + fmt(b.eds) + ' election district' + (b.eds === 1 ? '' : 's') + '</small></span></a>'; }).join('') + '</div>';
      if (cols.length) {
        h += '<div class="dd-tbl"><table><thead><tr><th>Community district</th>' + cols.map(function (k) { return '<th>' + esc(M[k].label) + '<small>' + esc(M[k].years) + '</small></th>'; }).join('')
          + '<th>COVID-19 vaccine, 1+ dose*<small>as of ' + esc((X.zip || {}).vax_asof || '') + '</small></th><th>Trash and recycling<small>' + esc((X.cd.dsny_months || []).join(' to ')) + '</small></th></tr></thead><tbody>'
          + d.boards.map(function (b) { var v = C[b.cd] || {}, t = v.dsny; return '<tr><td><a href="' + esc(b.url) + '">' + esc(b.name.replace(' Community Board ', ' CB')) + '</a></td>' + cols.map(function (k) { return '<td>' + f1(v[k], M[k].unit) + '</td>'; }).join('')
            + '<td>' + (X.zip && X.zip.d['cb-' + b.cd] ? X.zip.d['cb-' + b.cd].vax_pct + '%' : '\u2013') + '</td>'
            + '<td>' + (t ? fmt(t.refuse + t.paper + t.mgp + t.organics) + ' tons<small>' + t.diversion + '% recycled or composted</small>' : '\u2013') + '</td></tr>'; }).join('')
          + '<tr class="city"><td>New York City</td>' + cols.map(function (k) { return '<td>' + f1((X.cd.city || {})[k], M[k].unit) + '</td>'; }).join('') + '<td>' + (X.zip && X.zip.city ? X.zip.city.vax_pct + '%' : '') + '</td><td></td></tr>'
          + '</tbody></table></div><div class="dd-src">' + esc(X.cd.chp_source) + '. ' + cols.map(function (k) { return esc(M[k].label) + ': ' + esc(M[k].def) + ' (' + esc(M[k].src.replace(/\s+/g, ' ')) + ')'; }).join('. ') + '. Trash and recycling: ' + esc(X.cd.dsny_source) + ', tons collected over the 12 months. * COVID-19 vaccine: estimated from ZIP codes, as above.</div>';
      }
      h += '</div>';
    }
    h += '<div class="dd-src">Borough figures are as published, one bar per week from ' + esc((W.covid_ed || {}).weeks ? W.covid_ed.weeks[0] : '') + '. '
        + (Wd ? '* Estimated. The Health Department publishes case rates and emergency room visits by United Hospital Fund neighborhood; these are the average of the neighborhoods this district covers, weighted by the share of its land in each: ' + Wd.uhf.map(function (u) { return esc(u[0]) + ' ' + u[1] + '%'; }).join(', ') + '. ' : '')
        + 'Source: ' + esc(W.source || (X.resp || {}).source || '') + '; www.nyc.gov/assets/doh/respiratory-illness-data.</div></div>';
    }
    h += '<div class="dd-src">Population: ' + esc(d.population_source) + '. 311: ' + esc(d['311_source']) + '.</div></div>';
    el.innerHTML = h;
  }
  var X = {};
  function go() {
    var j = function (u) { return fetch(u).then(function (r) { return r.json(); }).catch(function () { return null; }); };
    [].forEach.call(document.querySelectorAll('[data-district-dash]'), function (el) {
      Promise.all([j('/data/dashboards/' + el.getAttribute('data-district-dash') + '.json'), j('/data/dashboards/_cd.json'), j('/data/dashboards/_resp.json'), j('/data/dashboards/_zip.json'), j('/data/dashboards/_wk.json')])
        .then(function (r) { if (!r[0]) return; X.cd = r[1]; X.resp = r[2]; X.zip = r[3]; X.wk = r[4]; render(el, r[0]); });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
})();
