/* ny4p-embed.js: New Yorkers for Parks' open space profile for a district, on its profile.
   <div data-ny4p data-cd="BK06"></div>   a community district: NY4P's 2021 Open Space Profile (its numbers, against the
                                          city, with the district's rank of 59, and both pages: the map and the statistics)
   <div data-ny4p data-cc="39"></div>     a City Council district: NY4P's 2015 City Council District Profile (both pages)
   The pages are NY4P's own, from their PDFs; the numbers are from parks-policy/ny4p.json. Loads when opened, or with the
   section it sits in. */
(function () {
  var BORO = { BK: 'Brooklyn', BX: 'Bronx', MN: 'Manhattan', QN: 'Queens', SI: 'Staten Island' };
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var ord = function (n) { var s = ['th', 'st', 'nd', 'rd'], v = n % 100; return n + (s[(v - 20) % 10] || s[v] || s[0]); };
  var KEY = ['walk', 'per1k', 'pctParkland', 'parkland', 'canopy', 'playgrounds', 'gardens', 'condition', 'clean', 'c311', 'volunteer', 'pop', 'income', 'poverty', 'asthma', 'life', 'air'];
  var B = function () { return window.NY4P_BASE || ''; };
  var DATA = null;
  function data() { return DATA || (DATA = fetch(B() + '/parks-policy/ny4p.json').then(function (r) { return r.json(); })); }
  function css() {
    if (document.getElementById('ny4p-css')) return;
    var s = document.createElement('style'); s.id = 'ny4p-css';
    s.textContent = '.n4x{border:1px solid #e5e2db;border-radius:12px;background:#fff;margin-top:10px;overflow:hidden}'
      + '.n4x>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:10px;padding:10px 12px;font:700 .9rem "DM Sans",sans-serif;color:#0d1b4b}'
      + '.n4x>summary::-webkit-details-marker{display:none}.n4x>summary img{height:34px;width:auto;flex:none}'
      + '.n4x>summary:after{content:"\\25BE";margin-left:auto;color:#f47920}.n4x[open]>summary:after{content:"\\25B4"}'
      + '.n4x .n4b{padding:0 12px 12px;font:400 .86rem/1.45 "DM Sans",sans-serif;color:#2b2a27}'
      + '.n4x .n4l{font:700 .62rem "DM Mono",monospace;text-transform:uppercase;letter-spacing:.08em;color:#6b6760;margin:12px 0 6px}'
      + '.n4x table{width:100%;border-collapse:collapse;font-size:.82rem;min-width:0;table-layout:auto}.n4x td,.n4x th{padding:6px 4px;border-bottom:1px solid #eee;text-align:left;vertical-align:top}'
      + '.n4x th{font:700 .62rem "DM Mono",monospace;text-transform:uppercase;letter-spacing:.06em;color:#6b6760}.n4x td.v{font-weight:700;color:#0d1b4b;white-space:nowrap}.n4x td.c{color:#6b6760;white-space:nowrap}'
      + '.n4x .n4p{display:block;width:100%;height:auto;border:1px solid #e5e2db;border-radius:8px;margin:6px 0}'
      + '.n4x .n4f{font-size:.78rem;color:#6b6760;margin-top:8px}.n4x .n4f a{color:#0d1b4b;font-weight:700}';
    document.head.appendChild(s);
  }
  function pages(base, n) {
    var h = '';
    for (var i = 1; i <= n; i++) h += '<a href="' + base + '-' + i + '.jpg" target="_blank" rel="noopener"><img class="n4p" loading="lazy" src="' + base + '-' + i + '.jpg" alt="New Yorkers for Parks profile, page ' + i + '"></a>';
    return h;
  }
  function community(box, code) {
    var b = code.slice(0, 2), n = +code.slice(2), pdf = 'https://www.ny4p.org/client-uploads/pdf/District-Profiles-2021/NY4P-Profiles_' + b + n + '.pdf';
    data().then(function (P) {
      var d = P.d[code], s = P.s[code];
      var rows = '';
      if (d) KEY.forEach(function (k) {
        var m = P.metrics.filter(function (x) { return x.k === k; })[0]; if (!m || d[k] == null) return;
        var c = P.nycS && P.nycS[k] != null ? P.nycS[k] : (P.nyc[k] != null ? P.nyc[k] : '');
        var r = d.rk && d.rk[k] ? ord(d.rk[k]) + ' of 59' : '';
        rows += '<tr><td>' + esc(m.l) + '</td><td class="v">' + esc(s[k]) + '</td><td class="c">' + esc(c) + '</td><td class="c">' + esc(r) + '</td></tr>';
      });
      box.innerHTML = '<div class="n4l">' + esc(BORO[b]) + ' Community District ' + n + ', 2021</div>'
        + (rows ? '<table><tr><th></th><th>District</th><th>City</th><th>Rank</th></tr>' + rows + '</table>' : '')
        + '<div class="n4l">The profile</div>' + pages(B() + '/ny4p/img/cd' + code, 2)
        + '<div class="n4f">From <a href="https://www.ny4p.org/data-and-research/research-library/open-space-profiles" target="_blank" rel="noopener">New Yorkers for Parks, 2021 Open Space Profiles</a>. Ranks: 1 is the highest of the 59 districts. '
        + '<a href="' + pdf + '" target="_blank" rel="noopener">The PDF &#8599;</a> &middot; <a href="' + pdf.replace('NY4P-Profiles_', 'NY4P-Profiles-Spanish_') + '" target="_blank" rel="noopener">En espa&ntilde;ol &#8599;</a></div>';
    }).catch(function () { box.innerHTML = pages(B() + '/ny4p/img/cd' + code, 2); });
  }
  function council(box, cc) {
    var n = ('0' + cc).slice(-2), pdf = 'https://www.ny4p.org/client-uploads/pdf/District-Profiles/NY4P_CCDP_2015_' + n + '.pdf';
    box.innerHTML = '<div class="n4l">City Council District ' + (+cc) + ', 2015</div>'
      + '<div>New Yorkers for Parks’ profile of the district as its lines were drawn in 2015, before the 2023 redistricting: its parks, park access, amenities, park funding and the people it serves.</div>'
      + pages(B() + '/ny4p/img/cc' + n, 2)
      + '<div class="n4f">From <a href="https://www.ny4p.org/data-and-research/research-library/city-council-district-profile" target="_blank" rel="noopener">New Yorkers for Parks, 2015 City Council District Profiles</a>. '
      + '<a href="' + pdf + '" target="_blank" rel="noopener">The PDF &#8599;</a></div>';
  }
  function init(el) {
    if (el.dataset.ready) return; el.dataset.ready = '1';
    var cd = el.getAttribute('data-cd'), cc = el.getAttribute('data-cc');
    if (!cd && !cc) return;
    css();
    var d = document.createElement('details'); d.className = 'n4x';
    d.innerHTML = '<summary><img src="' + B() + '/site-icons/ny4p.png" alt="New Yorkers for Parks">Open space profile from New Yorkers for Parks</summary><div class="n4b"></div>';
    var box = d.querySelector('.n4b');
    function load() { if (d.dataset.loaded) return; d.dataset.loaded = '1'; if (cd) community(box, cd); else council(box, cc); }
    d.addEventListener('toggle', function () { if (d.open) load(); });
    el.appendChild(d);
    var fold = el.parentNode && el.parentNode.closest ? el.parentNode.closest('details') : null;
    if (fold) { d.open = true; if (fold.open) load(); else fold.addEventListener('toggle', function () { if (fold.open) load(); }); }
    if (el.hasAttribute('data-open')) { d.open = true; load(); }
  }
  function all() { Array.prototype.forEach.call(document.querySelectorAll('[data-ny4p]'), init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', all); else all();
})();
