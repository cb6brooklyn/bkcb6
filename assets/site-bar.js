/* bkcb6.app site bar: one strip on every page. Logo home, the page's section, search of every page, App Store.
   Hidden inside the apps (bkcb:, ?app=1), inside frames and on ?embed= pages.
   Section rules are written by tools/build_site_index.py; edit them there. */
(function () {
  'use strict';
  function hidden() {
    try {
      var q = location.search || '';
      if (self !== top) return true;
      if (location.protocol === 'bkcb:' || /[?&]app=1\b/.test(q) || /[?&]embed=/.test(q) || /[?&]nobar\b/.test(q)) return true;
      if (sessionStorage.getItem('bkapp') === '1' || /^bkcb:/.test(document.referrer)) return true;
      if (document.documentElement.hasAttribute('data-nobar')) return true;
    } catch (e) { return true; }
    return false;
  }

  /*sections*/var SECTIONS=[["Apps", "/apps/", "^(apps/|appstore|privacy-)"], ["Calendar & News", "/calendar.html", "^(calendar|e/|news|today/|flyer-|civic-calendar|press/)"], ["Elections", "/elections.html", "(election|ballot|vote|voting|poll|primary|november2026|throughtime|comptroller-results|ad52-results|edhistory|cbhistory|results|registration|enrollment|ed-map|turnout)"], ["CB6", "/", "^(index\\.html$|minutes|board|committees|budget|survey|districtneeds|district-needs|jobs|250baltic|about|help|faq|contact|members|civic-handbook|handbook|hubs|250-baltic|cb6-faq|resolutions|letters|cb6-logo|cb6-map|cb6_|cb6-isometric|homemap|planning-map-cb6|welcome|crossword|puzzle|game|jeopardy|quiz|civics|glossary|recommended|reading|cb6-electeds|cb6-)"], ["Housing", "/rent.html", "(^rent|rents|housing|allhousing|lessexpensive|nycha|lotter|^cd/|affordab)"], ["Government", "/government/", "^(who|am[a-z]|sen[a-z]|cm[a-z]|council|senate|assembly|congress|cb-|cbmap|cb6-legislative|district-map|mydistricts|gov/|government|govhub|agencies|agency|charter|orgchart|org-chart|comptroller|mayor|bp|borough|directory\\.html|jointinterest|beyondcb6|citywide|nyc-|state|federal|cuny-trustees|publicadvocate|public-advocate|electeds|brooklyn|bronx|manhattan|queens|staten|bayridge|hanif|gounardes|simon|reynoso|lander|mamdani|hochul|velazquez|goldman|schumer|gillibrand|dinapoli|levine|williams|adams|governors)"], ["Land Use", "/useofland/", "(landuse|land-use|zoning|zoned|lots|useofland|builtmap|built|gowanus|bmt|lpc|landmark|preservation|rezon|ulurp|compplan|fhgs|permit|ownership|buildings|building-|^p/|27-buildings|226-kane|557-6|kane-street|historic|density|fair-housing|marine-terminal|pluto|lot-)"], ["Transportation", "/transport", "(transport|truck|speed|bqe|bike|subway|bus-|buses|parking|visionzero|vision-zero|bergndean|bergen|ferry|citibike|citi-bike|streets|crash|sammy|mta|transit|dot-)"], ["Parks", "/parks/", "(^park/|^parks|treepruning|tree|playground|community-garden|^garden|greenway|openstreets|open-streets|pops|waterfront|esplanade|dog-run|pool)"], ["Schools", "/eduhub", "(^school|eduhub|schooldistrict|college|cuny|childcare|child-care|prek|pre-k|3k|education|universit)"], ["Services", "/311-hub", "(^311|sanitation|dsny|mailbox|postal|usps|trash|recycl|compost|services|dob|hpd|dep-|water|noise|weather|flood|heat|alert|emergency|evacuation|hurricane|cooling|cooldown|complaint|health)"], ["Safety", "/publicsafety/", "(safety|precinct|sector/|crime|nypd|fdny|arrest|shooting|violation|camera|ticket)"], ["Culture", "/culture/", "(culture|museum|cinema|theatre|theater|library|librar|stadium|^c/|place|galler|venue|film|^art|music|bookstore|openstudios|studios)"], ["Directory", "/o/", "(^org|^o/|orgs|business|^biz|liquor|food-drink|food-stores|hardware|bids?\\b|restaurant|shop|coop|bid-|nonprofit|community-groups|sale-listings|listings)"], ["More", "/hubs.html", "."]];/*/sections*/
  /*prefix*/var PREFIX_RULES=[["Schools", "^(school-|college-|eduhub)"], ["Culture", "^(library-|museum-|cinema-|theatre-|theater-|place-|art-|gallery-|venue-)"], ["Directory", "^(org-|biz-)"], ["Land Use", "^(building-|reviewing\\.html|lamp\\.html)"], ["CB6", "^(search/|hubs\\.html)"], ["Parks", "^(park-|garden-|playground-)"], ["Transportation", "^(bqe|transport|truck)"]];/*/prefix*/
  /*text*/var TEXT_RULES=[["Schools", "(school|preschool|playschool|academy|\\bps \\d|\\bms \\d|\\bps k|day care|daycare|montessori|\\bprep\\b|kids|learning center|education council|camp )"], ["Government", "(districts & research|census atlas|neighborhoods|representative|senator|attorney general|governor|district attorney|council member|councilmember|assembly|state senate|city council|comptroller|public advocate|borough president|mayor|elected official)"], ["Elections", "(election|ballot|voting)"], ["CB6", "(cb6 (full board|business|committee|calendar)|draft agenda|robert|community board 6|district manager|resources & maps|privacy policy|support)"], ["Housing", "(housing|tenant|rent)"], ["Land Use", "(zoning|land use|liquor|ulurp|architecture)"], ["Parks", "(garden|park alliance|playground|parks activities|old stone house)"], ["Culture", "(arts?\\b|cinema|music|performance|theater|theatre|gallery|studio|dance|brewery|bookstore|books|cafe|coffee|lobster|restaurant)"], ["Services", "(311|trash|collection|sanitation|supermarket|greenmarket|farmers market)"], ["Safety", "(crime|arrests|justice center|firefighters)"], ["Directory", "(brooklyn\\.|organization|business|collective|association|initiative|civic council|dsa|soccer|salon|certified|portside|resilient|union hall)"]];/*/text*/

  function sectionOf(path, title, desc) {
    var p = (path || '').toLowerCase().replace(/^\//, '').replace(/^bk\//, '');
    if (/^block\//.test(p)) return ['Blocks', '/blocks/'];
    if (/^search\//.test(p)) return null;
    var i, m;
    for (i = 0; i < PREFIX_RULES.length; i++) {
      if (new RegExp(PREFIX_RULES[i][1]).test(p)) return bySec(PREFIX_RULES[i][0]);
    }
    for (i = 0; i < SECTIONS.length; i++) {
      if (SECTIONS[i][0] === 'More') break;
      if (new RegExp(SECTIONS[i][2]).test(p)) return [SECTIONS[i][0], SECTIONS[i][1]];
    }
    var t = ((title || '') + ' ' + (desc || '')).toLowerCase();
    for (i = 0; i < TEXT_RULES.length; i++) {
      if (new RegExp(TEXT_RULES[i][1]).test(t)) return bySec(TEXT_RULES[i][0]);
    }
    return null;
  }
  function bySec(name) {
    for (var i = 0; i < SECTIONS.length; i++) if (SECTIONS[i][0] === name) return [name, SECTIONS[i][1]];
    return null;
  }
  function hubOf(name) { var s = bySec(name); return s ? s[1] : '/hubs.html'; }

  var CSS = '#cb6bar{position:relative;z-index:9000;background:#0d1b4b;color:#fff;font:500 14px/1.2 "DM Sans",system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}' +
    '#cb6bar *{box-sizing:border-box}' +
    '#cb6bar .cb6b-in{display:flex;align-items:center;gap:10px;max-width:1200px;margin:0 auto;padding:8px 12px;min-height:52px}' +
    '#cb6bar a{color:#fff;text-decoration:none}' +
    '#cb6bar .cb6b-logo{display:flex;align-items:center;gap:8px;flex:none}' +
    '#cb6bar .cb6b-logo img{width:34px;height:34px;border-radius:8px;display:block}' +
    '#cb6bar .cb6b-wm{font-weight:700;font-size:15px;letter-spacing:.01em;white-space:nowrap}' +
    '#cb6bar .cb6b-sec{flex:none;display:inline-flex;align-items:center;gap:6px;border:1.5px solid #f47920;color:#fff;border-radius:999px;padding:5px 11px;font-size:13px;font-weight:600;white-space:nowrap;max-width:46vw;overflow:hidden;text-overflow:ellipsis}' +
    '#cb6bar .cb6b-sec:hover{background:#f47920}' +
    '#cb6bar .cb6b-sec small{opacity:.75;font-weight:500}' +
    '#cb6bar .cb6b-s{flex:1 1 auto;position:relative;min-width:0}' +
    '#cb6bar .cb6b-s input{width:100%;height:36px;border:0;border-radius:10px;padding:0 12px 0 34px;font:inherit;font-size:15px;color:#0d1b4b;background:#fff;outline:0;-webkit-appearance:none;appearance:none}' +
    '#cb6bar .cb6b-s input::placeholder{color:#6b7280}' +
    '#cb6bar .cb6b-s input:focus{box-shadow:0 0 0 3px rgba(244,121,32,.55)}' +
    '#cb6bar .cb6b-s svg{position:absolute;left:11px;top:10px;width:16px;height:16px;pointer-events:none}' +
    '#cb6bar .cb6b-app{flex:none;line-height:0}' +
    '#cb6bar .cb6b-app img{height:30px;width:auto;display:block;border:0}' +
    '#cb6bar .cb6b-home{flex:none;font-weight:600;font-size:13px;opacity:.9;padding:6px 4px}' +
    '#cb6bar .cb6b-home:hover{color:#f47920;opacity:1}' +
    '#cb6bar .cb6b-r{display:none;position:absolute;left:0;right:0;top:42px;background:#fff;color:#0d1b4b;border-radius:12px;box-shadow:0 14px 40px rgba(6,2,77,.35);max-height:min(70vh,560px);overflow:auto;padding:6px;z-index:9001;text-align:left}' +
    '#cb6bar .cb6b-r.on{display:block}' +
    '#cb6bar .cb6b-r a{display:block;color:#0d1b4b;padding:8px 10px;border-radius:8px;line-height:1.25}' +
    '#cb6bar .cb6b-r a.sel,#cb6bar .cb6b-r a:hover{background:#eef1fb}' +
    '#cb6bar .cb6b-r .t{font-weight:600;font-size:14px}' +
    '#cb6bar .cb6b-r .d{font-size:12px;color:#4b5563;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
    '#cb6bar .cb6b-r .k{display:inline-block;font-size:11px;font-weight:700;color:#f47920;text-transform:uppercase;letter-spacing:.04em;margin-right:6px}' +
    '#cb6bar .cb6b-r .more{text-align:center;font-weight:600;color:#f47920}' +
    '#cb6bar .cb6b-r .note{padding:10px;font-size:13px;color:#4b5563}' +
    '#cb6bar .cb6b-r .addr{background:#fff4ea}' +
    '@media(max-width:640px){#cb6bar .cb6b-wm,#cb6bar .cb6b-home{display:none}#cb6bar .cb6b-in{gap:8px;padding:8px 10px}#cb6bar .cb6b-sec{padding:5px 9px;font-size:12px}#cb6bar .cb6b-app img{height:26px}#cb6bar .cb6b-r{position:fixed;left:8px;right:8px;top:58px}}' +
    '@media(max-width:400px){#cb6bar .cb6b-sec small{display:none}}';

  var title = (document.title || '').replace(/\s*[|—–-]\s*(bkcb6\.app|BKCB6|CB6 & Beyond|Brooklyn CB6)\s*$/i, '');
  var descEl = document.querySelector('meta[name="description"]');
  var sec = sectionOf(location.pathname, title, descEl ? descEl.getAttribute('content') : '');
  var isHome = /^\/(index\.html)?$/.test(location.pathname);

  var st = document.createElement('style'); st.textContent = CSS;
  var bar = document.createElement('div'); bar.id = 'cb6bar';
  bar.innerHTML =
    '<div class="cb6b-in">' +
      '<a class="cb6b-logo" href="/" aria-label="bkcb6.app home"><img src="/cb6-logo.png" alt="" width="34" height="34"><span class="cb6b-wm">bkcb6.app</span></a>' +
      (sec && !isHome ? '<a class="cb6b-sec" href="' + sec[1] + '" title="All ' + sec[0] + ' pages"><small>in</small>' + sec[0] + ' ›</a>' : '') +
      '<form class="cb6b-s" role="search" action="/search/" method="get" autocomplete="off">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2.4" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>' +
        '<input type="search" name="q" placeholder="Search, or an address" aria-label="Search bkcb6.app" enterkeyhint="search">' +
        '<div class="cb6b-r" role="listbox"></div>' +
      '</form>' +
      (isHome ? '' : '<a class="cb6b-home" href="/">Home</a>') +
      '<a class="cb6b-app" href="https://apps.apple.com/us/app/bkcb6/id6813967208" target="_blank" rel="noopener"><img src="/appstore-badge.png" alt="Download BKCB6 on the App Store"></a>' +
    '</div>';

  function mount() {
    var old = document.getElementById('asb'); if (old) old.style.display = 'none';
    document.head.appendChild(st);
    document.body.insertBefore(bar, document.body.firstChild);
    if (!svPart && !document.getElementById('cb6sv')) { svCss(); bar.parentNode.insertBefore(svStrip(), bar.nextSibling); }
    wire();
  }

  // ---- search ----
  var INDEX = null, loading = null;
  function load() {
    if (INDEX) return Promise.resolve(INDEX);
    if (loading) return loading;
    loading = fetch('/data/site-index.json', { cache: 'force-cache' }).then(function (r) { return r.json(); }).then(function (d) {
      var names = d.sections.map(function (s) { return s[0]; });
      INDEX = { names: names, hubs: d.sections.map(function (s) { return s[1]; }), pages: d.pages.map(function (p) {
        return { u: p[0], t: p[1], s: names[p[2]], d: p[3] || '', x: (p[1] + ' ' + (p[3] || '') + ' ' + p[0].replace(/[-_\/\.]/g, ' ')).toLowerCase() };
      }) };
      return INDEX;
    }).catch(function () { loading = null; return null; });
    return loading;
  }
  var YEAR = new Date().getFullYear(), HUBS = {};
  SECTIONS.forEach(function (s) { HUBS[s[1]] = 1; });
  ['/elections.html', '/early-vote-map.html', '/throughtime/', '/blocks/', '/address.html', '/citywide-search.html', '/calendar.html', '/search/'].forEach(function (u) { HUBS[u] = 1; });
  function isAddress(s) { return /^\d+[a-z\-]*\s+\S/i.test(s.trim()); }
  function search(query, limit, boost, dedupe) {
    var qs = query.toLowerCase().trim(); if (!qs || !INDEX) return [];
    var toks = qs.split(/\s+/).filter(Boolean), out = [], i, p, j, ok, sc, depth;
    for (i = 0; i < INDEX.pages.length; i++) {
      p = INDEX.pages[i]; ok = true;
      for (j = 0; j < toks.length; j++) if (p.x.indexOf(toks[j]) < 0) { ok = false; break; }
      if (!ok) continue;
      var tl = p.t.toLowerCase(); sc = 0;
      if (tl === qs) sc += 40; else if (tl.indexOf(qs) === 0) sc += 12; else if (tl.indexOf(qs) >= 0) sc += 8;
      for (j = 0; j < toks.length; j++) {
        if (tl.indexOf(toks[j]) >= 0) sc += 4;
        if (new RegExp('(^|[^a-z0-9])' + toks[j].replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '([^a-z0-9]|$)').test(tl)) sc += 2;
      }
      if (p.d && p.d.toLowerCase().indexOf(qs) >= 0) sc += 5;
      depth = (p.u.match(/\//g) || []).length;
      sc += depth === 1 ? 6 : (depth === 2 ? 0 : -1);
      if (HUBS[p.u]) sc += 8;
      var dm = /^\/(e|news)\/(\d{4})-/.exec(p.u);
      if (dm) { sc -= dm[1] === 'e' ? 6 : 3; if (+dm[2] < YEAR - 1) sc -= 4; }
      sc -= Math.min(4, p.t.length / 40);
      if (boost && p.s === boost) sc += 1.5;
      out.push([sc, p]);
    }
    out.sort(function (a, b) { return b[0] - a[0] || a[1].t.length - b[1].t.length; });
    var res = [], seen = {};
    for (i = 0; i < out.length && res.length < (limit || 10); i++) {
      p = out[i][1];
      if (dedupe) { var k = p.s + '|' + p.t.toLowerCase(); if (seen[k]) continue; seen[k] = 1; }
      res.push(p);
    }
    return res;
  }
  window.CB6Search = { load: load, search: search, isAddress: isAddress, sectionOf: sectionOf, hubOf: hubOf };
  // The District Needs Survey pill: under the bar on every page; on its own at the top of every page inside the apps.
  // Not inside frames or ?embed= parts (the page or app screen around them carries it).
  var SURVEY = 'https://docs.google.com/forms/d/e/1FAIpQLSeogV51Py43b3dYDwfgQnDpHADqS60TG0WXGFNcmB6PKduV6w/viewform?usp=header';
  var SVCSS = '#cb6sv{display:flex;justify-content:center;padding:7px 10px;background:#0d1b4b;border-top:1px solid rgba(255,255,255,.12);border-bottom:3px solid #f47920;position:relative;z-index:8999}' +
    '#cb6sv a{display:inline-flex;align-items:center;gap:8px;background:#f47920;color:#fff;text-decoration:none;border-radius:999px;padding:7px 16px;font:700 14px/1.15 "DM Sans",system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased;-webkit-tap-highlight-color:transparent;max-width:100%;box-sizing:border-box;text-align:center}' +
    '#cb6sv a:hover{background:#d4631a}#cb6sv a span{font-weight:500;opacity:.9}' +
    '@media(max-width:400px){#cb6sv a{font-size:13px;padding:7px 13px}}';
  function svStrip(inApp) {
    var d = document.createElement('div'); d.id = 'cb6sv';
    // in the apps it is a button to the app's own survey screen, not a link out
    d.innerHTML = inApp ? '<a href="/budgetsurvey/index.html?app=1" role="button">Take our District Needs Survey <span>›</span></a>'
      : '<a href="' + SURVEY + '" target="_blank" rel="noopener">Take our District Needs Survey <span>›</span></a>';
    return d;
  }
  function svCss() { var t = document.createElement('style'); t.textContent = SVCSS; document.head.appendChild(t); }
  var svPart = true;
  try { svPart = self !== top || /[?&]embed=/.test(location.search || '') || document.documentElement.classList.contains('embed') || /^\/budgetsurvey\//.test(location.pathname); } catch (e) { svPart = true; }
  if (hidden() || document.getElementById('cb6bar')) {
    if (!svPart && !document.getElementById('cb6sv')) {
      var svMount = function () { svCss(); document.body.insertBefore(svStrip(true), document.body.firstChild); };
      if (document.body) svMount(); else document.addEventListener('DOMContentLoaded', svMount);
    }
    return;
  }

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function wire() {
    var form = bar.querySelector('form'), inp = form.querySelector('input'), box = form.querySelector('.cb6b-r'), selIdx = -1, cur = '';
    function render() {
      var v = inp.value; cur = v;
      if (!v.trim()) { box.className = 'cb6b-r'; box.innerHTML = ''; return; }
      if (!INDEX) { box.className = 'cb6b-r on'; box.innerHTML = '<div class="note">Loading the site index…</div>'; load().then(function () { if (inp.value === cur) render(); }); return; }
      var res = search(v, 8, sec ? sec[0] : null, true), h = '';
      if (isAddress(v)) h += '<a class="addr" href="/citywide-search.html?address=' + encodeURIComponent(v.trim()) + '"><span class="t"><span class="k">Address</span>' + esc(v.trim()) + '</span><div class="d">Districts, zoning, who represents it, what is nearby</div></a>';
      res.forEach(function (p) { h += '<a href="' + esc(p.u) + '"><span class="t"><span class="k">' + esc(p.s) + '</span>' + esc(p.t) + '</span>' + (p.d ? '<div class="d">' + esc(p.d) + '</div>' : '') + '</a>'; });
      if (!res.length && !isAddress(v)) h += '<div class="note">No page matches. Try a shorter word, or an address like 250 Baltic Street.</div>';
      h += '<a class="more" href="/search/?q=' + encodeURIComponent(v.trim()) + '">All results for “' + esc(v.trim()) + '” ›</a>';
      box.innerHTML = h; box.className = 'cb6b-r on'; selIdx = -1;
    }
    inp.addEventListener('focus', function () { load(); if (inp.value) render(); });
    inp.addEventListener('input', render);
    inp.addEventListener('keydown', function (e) {
      var items = box.querySelectorAll('a'); if (!items.length) return;
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault(); selIdx = (selIdx + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
        items.forEach(function (a, i) { a.className = a.className.replace(' sel', '') + (i === selIdx ? ' sel' : ''); });
        items[selIdx].scrollIntoView({ block: 'nearest' });
      } else if (e.key === 'Enter' && selIdx >= 0) { e.preventDefault(); location.href = items[selIdx].href; }
      else if (e.key === 'Escape') { box.className = 'cb6b-r'; inp.blur(); }
    });
    form.addEventListener('submit', function (e) {
      var v = inp.value.trim(); if (!v) { e.preventDefault(); return; }
      if (isAddress(v)) { e.preventDefault(); location.href = '/citywide-search.html?address=' + encodeURIComponent(v); }
    });
    document.addEventListener('click', function (e) { if (!form.contains(e.target)) box.className = 'cb6b-r'; });
  }

  if (document.body) mount(); else document.addEventListener('DOMContentLoaded', mount);
})();
