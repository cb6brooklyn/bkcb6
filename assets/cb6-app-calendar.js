/* CB6 calendar, built to match the BKCB6 app's calendar.
   Reads the same file the app reads: /app/data/civic/cal/calendar-bk.json (rebuilt by the App calendar workflow).
   Mount: <div id="cb6-app-calendar"></div><script src="https://bkcb6.app/assets/cb6-app-calendar.js"></script>
   Preferences (mode, hidden organizations, last search) are saved in this browser. */
(function () {
  var BASE = 'https://bkcb6.app/app/data/civic/cal/';
  var DATA = BASE + 'calendar-bk.json';
  var CB6 = 'brooklyn-community-board-6';
  var ICON_FALLBACK = { 'brooklyn-community-board-6': 'https://bkcb6.app/elected/CB6_540.png' };
  var PREF_KEY = 'cb6cal.prefs.v1';
  var NAVY = '#0d1b4b', ORANGE = '#f47920';
  var PALETTE = ['#2d6a4f', '#1a56db', '#c0392b', '#3b0764', '#e8a020', '#1a4b8c', '#6b0a14', '#3a7d44', '#7a1a1a', '#2c5f9e', '#4c6028', '#d4512a'];
  var MODES = [
    { id: 'all', label: 'Everything', test: function () { return true; } },
    { id: 'cb6', label: 'CB6 meetings', test: function (e) { return e.ty === CB6; } },
    { id: 'events', label: 'Events', test: function (e) { return e.g === 'cb6' && e.ty !== CB6; } },
    { id: 'council', label: 'City Council', test: function (e) { return e.g === 'council'; } },
    { id: 'hearing', label: 'Hearings', test: function (e) { return e.g === 'hearing'; } }
  ];
  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  var DOWS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  var root = document.getElementById('cb6-app-calendar');
  if (!root) return;

  function loadPrefs() { try { return JSON.parse(localStorage.getItem(PREF_KEY)) || {}; } catch (e) { return {}; } }
  function savePrefs() { try { localStorage.setItem(PREF_KEY, JSON.stringify({ mode: S.mode, hidden: Object.keys(S.hidden), q: S.q })); } catch (e) {} }
  var P = loadPrefs();
  var S = { mode: P.mode || 'all', hidden: {}, q: P.q || '', org: null, ym: null, sel: null, types: {}, events: [], byDate: {} };
  (P.hidden || []).forEach(function (t) { S.hidden[t] = 1; });

  var DEC = document.createElement('textarea');
  function dec(s) { s = String(s == null ? '' : s); if (s.indexOf('&') < 0) return s; DEC.innerHTML = s; return DEC.value; }
  function esc(s) { return dec(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function nyToday() {
    var p = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
    return p; // YYYY-MM-DD
  }
  function ds(y, m, d) { return y + '-' + String(m + 1).padStart(2, '0') + '-' + String(d).padStart(2, '0'); }
  function parse(d) { var a = d.split('-'); return new Date(+a[0], +a[1] - 1, +a[2]); }
  function longDate(d) { var x = parse(d); return DOWS[x.getDay()] + ', ' + MONTHS[x.getMonth()] + ' ' + x.getDate(); }
  function hash(s) { var h = 0; for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return Math.abs(h); }
  function color(ty) { if (ty === CB6) return ORANGE; var t = S.types[ty]; return (t && t.bg) || PALETTE[hash(ty) % PALETTE.length]; }
  function icon(ty) { var t = S.types[ty]; if (ICON_FALLBACK[ty]) return ICON_FALLBACK[ty]; return t && t.icon ? BASE + 'icons/' + t.icon : ''; }
  function orgName(e) { return e.org || (S.types[e.ty] && S.types[e.ty].name) || ''; }
  function minutes(t) { if (!t) return 9999; var m = /(\d{1,2}):(\d{2})\s*([AP]M)/i.exec(t); if (!m) return 9998; var h = +m[1] % 12 + (/p/i.test(m[3]) ? 12 : 0); return h * 60 + +m[2]; }
  function cleanLoc(l) { return l && l.trim() !== 'NY' ? l : ''; }
  function cb6Title(e) {
    return e.l.replace(/^CB6 Committee Meeting\s*[–—-]\s*/i, '').replace(/^CB6 Committee Meeting-\s*/i, '').replace(/\s*Committee Meeting$/i, ' Committee').replace(/\s*·\s*6:30pm$/i, '');
  }

  function modeOf(id) { for (var i = 0; i < MODES.length; i++) if (MODES[i].id === id) return MODES[i]; return MODES[0]; }
  function visible(e) {
    if (!modeOf(S.mode).test(e)) return false;
    if (S.hidden[e.ty]) return false;
    if (S.org && e.ty !== S.org && !(e.also || []).some(function (a) { return a.ty === S.org; })) return false;
    if (S.q) {
      var hay = (e.l + ' ' + orgName(e) + ' ' + (e.loc || '') + ' ' + (e.desc || '')).toLowerCase();
      var words = S.q.toLowerCase().split(/\s+/).filter(Boolean);
      for (var i = 0; i < words.length; i++) if (hay.indexOf(words[i]) < 0) return false;
    }
    return true;
  }

  var css = '' +
    '#cb6-app-calendar{font-family:"DM Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;color:' + NAVY + ';background:#f6f4ef;border-radius:18px;padding:16px;box-sizing:border-box;max-width:100%}' +
    '#cb6-app-calendar *{box-sizing:border-box}' +
    '#cb6-app-calendar button{font-family:inherit;cursor:pointer}' +
    '.cc-lead{font-family:"DM Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}.cc-lead a{display:flex;align-items:center;gap:16px;background:' + NAVY + ';color:#fff;text-decoration:none;padding:18px 20px;border-top:5px solid ' + ORANGE + ';border-bottom:5px solid ' + ORANGE + ';margin-bottom:12px;border-radius:4px}' +
    '.cc-lead img{width:60px;height:60px;border-radius:10px;background:#fff;flex:none}' +
    '.cc-lead .k{display:block;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:' + ORANGE + ';font-weight:700;margin-bottom:3px}' +
    '.cc-lead .t{display:block;font-size:20px;font-weight:700;line-height:1.2}' +
    '.cc-lead .w{display:block;font-size:15px;color:#dfe3f0;margin-top:3px}' +
    '.cc-lead .go{flex:none;width:36px;height:36px;border-radius:50%;background:' + ORANGE + ';display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:700}' +
    '.cc-search{display:flex;gap:8px;margin:6px 0 12px}' +
    '.cc-search input{flex:1;min-width:0;font:inherit;font-size:16px;padding:11px 16px;border:1.5px solid #ddd6c6;border-radius:999px;background:#fff;color:' + NAVY + ';outline:none}' +
    '.cc-search input:focus{border-color:' + NAVY + '}' +
    '.cc-search button{border:1.5px solid #ddd6c6;background:#fff;border-radius:999px;padding:0 16px;font-size:14px;font-weight:600;color:' + NAVY + '}' +
    '.cc-row{display:flex;gap:8px;overflow-x:auto;padding:2px 0 10px;scrollbar-width:thin}' +
    '.cc-chip{flex:none;display:inline-flex;align-items:center;gap:8px;border:1.5px solid #e2dccd;background:#fff;color:' + NAVY + ';border-radius:999px;padding:8px 16px;font-size:15px;font-weight:600;white-space:nowrap}' +
    '.cc-chip.on{background:' + NAVY + ';border-color:' + NAVY + ';color:#fff}' +
    '.cc-org{padding:5px 12px 5px 5px;font-size:14px}' +
    '.cc-org img,.cc-org .ph{width:26px;height:26px;border-radius:50%;object-fit:contain;background:#fff;border:1px solid #eee}' +
    '.cc-org .ph{display:inline-block}' +
    '.cc-org .n{font-family:"DM Mono",monospace;font-size:12px;color:#8a8a99}' +
    '.cc-org.on{background:' + NAVY + ';color:#fff}.cc-org.on .n{color:#c9cee0}' +
    '.cc-org.off{opacity:.45;text-decoration:line-through}' +
    '.cc-all{background:' + ORANGE + ';border-color:' + ORANGE + ';color:#fff;padding:6px 14px}' +
    '.cc-all.dim{background:#fff;color:' + NAVY + ';border-color:#e2dccd}' +
    '.cc-cal{background:#fff;border:1.5px solid #ece6d8;border-radius:18px;padding:14px 10px 10px;margin:4px 0 18px}' +
    '.cc-mh{display:flex;align-items:center;justify-content:space-between;padding:0 10px 10px}' +
    '.cc-mh h3{margin:0;font-size:24px;font-weight:700;color:' + NAVY + '}' +
    '.cc-mh button{background:none;border:0;color:' + ORANGE + ';font-size:28px;font-weight:700;line-height:1;padding:4px 10px}' +
    '.cc-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:4px;text-align:center}' +
    '.cc-dow{font-family:"DM Mono",monospace;font-size:13px;color:#6b6b80;padding:4px 0 8px}' +
    '.cc-day{border:1.5px solid transparent;background:none;border-radius:12px;padding:6px 0 4px;min-height:62px;display:flex;flex-direction:column;align-items:center;gap:3px;color:' + NAVY + '}' +
    '.cc-day .dn{font-size:19px;font-weight:600}' +
    '.cc-day .dots{display:flex;gap:3px;height:7px}' +
    '.cc-day .dots i{width:7px;height:7px;border-radius:50%;display:block}' +
    '.cc-day .more{font-family:"DM Mono",monospace;font-size:10px;color:#8a8a99;height:12px}' +
    '.cc-day.cb6{background:#fdeee2;border-color:#f6b98a}' +
    '.cc-day.today .dn{color:' + ORANGE + '}' +
    '.cc-day.sel{background:' + NAVY + ';border-color:' + NAVY + ';color:#fff}.cc-day.sel .dn{color:#fff}.cc-day.sel .more{color:#c9cee0}' +
    '.cc-day.blank{visibility:hidden}' +
    '.cc-day.past .dn{color:#8a8a99}' +
    '.cc-dh{font-family:"DM Mono",monospace;font-size:15px;letter-spacing:.12em;text-transform:uppercase;color:' + ORANGE + ';margin:18px 4px 10px}' +
    '.cc-card{display:flex;gap:14px;align-items:center;background:#fff;border:1.5px solid #ece6d8;border-radius:16px;padding:14px 16px;margin-bottom:10px;text-decoration:none;color:' + NAVY + '}' +
    '.cc-card.cb6{background:#fdeee2;border:2px solid ' + ORANGE + '}' +
    '.cc-card .lg{width:56px;height:56px;flex:none;border-radius:10px;object-fit:contain;background:#fff}' +
    '.cc-card .lg.ph{display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:20px}' +
    '.cc-card .b{flex:1;min-width:0}' +
    '.cc-card .og{display:block;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:' + ORANGE + ';font-weight:700;margin-bottom:2px}' +
    '.cc-card .tt{display:block;font-size:19px;font-weight:700;line-height:1.25}' +
    '.cc-card .mt{display:block;font-size:15px;color:#5a5a6e;margin-top:3px}' +
    '.cc-card .ds{display:none;font-size:14px;color:#3d3d52;margin-top:8px;line-height:1.45}' +
    '.cc-card.open .ds{display:block}' +
    '.cc-card .fl{display:none;max-width:100%;border-radius:10px;margin-top:10px}' +
    '.cc-card.open .fl{display:block}' +
    '.cc-card .lk{display:none;margin-top:10px}' +
    '.cc-card.open .lk{display:inline-block}' +
    '.cc-card .lk a{display:inline-block;background:' + NAVY + ';color:#fff;text-decoration:none;font-weight:700;font-size:14px;padding:8px 14px;border-radius:999px;margin-right:8px}' +
    '.cc-card .ch{flex:none;color:' + ORANGE + ';font-size:26px;font-weight:700;align-self:flex-start;margin-top:4px;transition:transform .15s}' +
    '.cc-card.open .ch{transform:rotate(90deg)}' +
    '.cc-thumb{width:56px;height:56px;flex:none;border-radius:8px;object-fit:cover}' +
    '.cc-empty{color:#6b6b80;font-size:15px;padding:12px 4px}' +
    '.cc-note{font-family:"DM Mono",monospace;font-size:12px;color:#8a8a99;margin:6px 4px 0}' +
    '@media(max-width:560px){#cb6-app-calendar{padding:10px;border-radius:12px}.cc-day{min-height:54px}.cc-day .dn{font-size:16px}.cc-mh h3{font-size:20px}.cc-card .tt{font-size:17px}.cc-lead .t{font-size:17px}.cc-lead img{width:48px;height:48px}}';

  if (!document.getElementById('cb6-app-calendar-css')) {
    var st = document.createElement('style'); st.id = 'cb6-app-calendar-css'; st.textContent = css; document.head.appendChild(st);
    if (!document.querySelector('link[href*="DM+Sans"]')) {
      var lf = document.createElement('link'); lf.rel = 'stylesheet';
      lf.href = 'https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;600;700&display=swap';
      document.head.appendChild(lf);
    }
  }

  root.innerHTML = '<div class="cc-lead"></div>' +
    '<div class="cc-search"><input type="search" placeholder="Search events, organizations, places" aria-label="Search the calendar"><button type="button" class="cc-clear">Clear</button></div>' +
    '<div class="cc-row cc-modes"></div><div class="cc-row cc-orgs"></div>' +
    '<div class="cc-cal"><div class="cc-mh"><button type="button" data-n="-1" aria-label="Previous month">&lsaquo;</button><h3></h3><button type="button" data-n="1" aria-label="Next month">&rsaquo;</button></div><div class="cc-grid"></div></div>' +
    '<div class="cc-list"><div class="cc-empty">Loading the calendar…</div></div>';
  var $ = function (s) { return root.querySelector(s); };
  var input = $('.cc-search input');
  input.value = S.q;

  function renderLead() {
    var today = nyToday(), t = parse(today);
    var sunday = new Date(t); sunday.setDate(t.getDate() + (7 - t.getDay()) % 7);
    var weekEnd = ds(sunday.getFullYear(), sunday.getMonth(), sunday.getDate());
    // A meeting earlier today that has ended (CB6 meetings run about 90 minutes; 150 minutes after the start counts as over) is no longer next.
    var nyNow = (function () { var p = {}; new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', hour: '2-digit', minute: '2-digit', hour12: false }).formatToParts(new Date()).forEach(function (x) { p[x.type] = x.value; }); return (+p.hour % 24) * 60 + (+p.minute); })();
    var over = function (e) { return e.d === today && minutes(e.t) < 9998 && nyNow > minutes(e.t) + 150; };
    var mtgs = S.events.filter(function (e) { return e.ty === CB6 && e.d >= today && !over(e); }).sort(function (a, b) { return a.d < b.d ? -1 : a.d > b.d ? 1 : minutes(a.t) - minutes(b.t); });
    var week = mtgs.filter(function (e) { return e.d <= weekEnd; });
    var show = week.length ? week : mtgs.slice(0, 1);
    var label = week.length ? 'CB6 meeting this week' : 'Next CB6 meeting';
    var leadEl = document.getElementById('cb6-app-calendar-lead') || $('.cc-lead');
    if (leadEl.id === 'cb6-app-calendar-lead') leadEl.className = 'cc-lead';
    leadEl.innerHTML = show.map(function (e) {
      var time = e.t || (/(\d{1,2}:\d{2}\s*[ap]m)/i.exec(e.l) || [])[1] || '';
      var when = longDate(e.d) + (time ? ' at ' + time.toUpperCase().replace(/(\d)([AP]M)/, '$1 $2') : '') + (cleanLoc(e.loc) ? ' · ' + cleanLoc(e.loc).replace(/, United States$/, '') : '');
      return '<a href="' + esc(e.h || '#') + '" target="_blank" rel="noopener"><img src="https://bkcb6.app/cb6-logo-square.png" alt=""><span style="flex:1;min-width:0"><span class="k">' + label + '</span><span class="t">' + esc(cb6Title(e)) + '</span><span class="w">' + esc(when) + '</span></span><span class="go">&rsaquo;</span></a>';
    }).join('');
  }

  function renderModes() {
    $('.cc-modes').innerHTML = MODES.map(function (m) {
      return '<button type="button" class="cc-chip' + (S.mode === m.id ? ' on' : '') + '" data-mode="' + m.id + '">' + m.label + '</button>';
    }).join('');
  }

  function monthEvents() {
    var pre = S.ym.y + '-' + String(S.ym.m + 1).padStart(2, '0');
    return S.events.filter(function (e) { return e.d.slice(0, 7) === pre && modeOf(S.mode).test(e); });
  }

  function renderOrgs() {
    var counts = {};
    monthEvents().forEach(function (e) { counts[e.ty] = (counts[e.ty] || 0) + 1; });
    var tys = Object.keys(counts).sort(function (a, b) { return (b === CB6) - (a === CB6) || counts[b] - counts[a]; });
    var html = '<button type="button" class="cc-chip cc-all' + (S.org ? ' dim' : '') + '" data-org="">All</button>';
    html += tys.map(function (ty) {
      var ic = icon(ty), name = (S.types[ty] && S.types[ty].name) || ty;
      var cls = 'cc-chip cc-org' + (S.org === ty ? ' on' : '') + (S.hidden[ty] ? ' off' : '');
      return '<button type="button" class="' + cls + '" data-org="' + esc(ty) + '" title="Tap to show only this organization. Double-tap to hide it.">' +
        (ic ? '<img src="' + esc(ic) + '" alt="" loading="lazy">' : '<span class="ph" style="background:' + color(ty) + '"></span>') +
        esc(name) + ' <span class="n">' + counts[ty] + '</span></button>';
    }).join('');
    $('.cc-orgs').innerHTML = html;
  }

  function renderGrid() {
    var y = S.ym.y, m = S.ym.m, today = nyToday();
    $('.cc-mh h3').textContent = MONTHS[m] + ' ' + y;
    var first = new Date(y, m, 1).getDay(), days = new Date(y, m + 1, 0).getDate();
    var html = ['S', 'M', 'T', 'W', 'T', 'F', 'S'].map(function (d) { return '<div class="cc-dow">' + d + '</div>'; }).join('');
    for (var i = 0; i < first; i++) html += '<div class="cc-day blank"></div>';
    for (var d = 1; d <= days; d++) {
      var key = ds(y, m, d);
      var evs = (S.byDate[key] || []).filter(visible);
      var cols = [], seen = {};
      evs.forEach(function (e) { var c = color(e.ty); if (!seen[c]) { seen[c] = 1; cols.push(c); } });
      var isCb6 = evs.some(function (e) { return e.ty === CB6; });
      var cls = 'cc-day' + (isCb6 ? ' cb6' : '') + (key === today ? ' today' : '') + (key === S.sel ? ' sel' : '') + (key < today ? ' past' : '');
      html += '<button type="button" class="' + cls + '" data-d="' + key + '" aria-label="' + longDate(key) + ', ' + evs.length + ' events"><span class="dn">' + d + '</span>' +
        '<span class="dots">' + cols.slice(0, 3).map(function (c) { return '<i style="background:' + c + '"></i>'; }).join('') + '</span>' +
        '<span class="more">' + (evs.length > 3 ? '+' + (evs.length - 3) : '') + '</span></button>';
    }
    $('.cc-grid').innerHTML = html;
  }

  function card(e) {
    var isCb6 = e.ty === CB6, ic = isCb6 ? 'https://bkcb6.app/cb6-logo-square.png' : icon(e.ty);
    var meta = [e.t ? e.t + (e.e ? ' to ' + e.e : '') : '', isCb6 ? '' : orgName(e), cleanLoc(e.loc)].filter(Boolean).join(' · ');
    var logo = ic ? '<img class="lg" src="' + esc(ic) + '" alt="" loading="lazy">' : '<span class="lg ph" style="background:' + color(e.ty) + '">' + esc(orgName(e).charAt(0)) + '</span>';
    var thumb = e.f ? '<img class="cc-thumb" src="' + esc(BASE + 'flyers/' + e.f) + '" alt="" loading="lazy" onerror="this.onerror=null;this.src=\'https://bkcb6.app/' + esc(e.f) + '\'">' : '';
    var links = e.h ? '<span class="lk"><a href="' + esc(e.h) + '" target="_blank" rel="noopener">' + esc(e.lt || 'Details') + ' &#8599;</a></span>' : '';
    return '<div class="cc-card' + (isCb6 ? ' cb6' : '') + '" tabindex="0" role="button" aria-expanded="false">' + logo +
      '<span class="b">' + (isCb6 ? '<span class="og">Brooklyn CB6</span>' : '') +
      '<span class="tt">' + esc(isCb6 ? cb6Title(e) : e.l) + '</span>' + (meta ? '<span class="mt">' + esc(meta) + '</span>' : '') +
      (e.desc ? '<span class="ds">' + esc(e.desc) + '</span>' : '') +
      (e.f ? '<img class="fl" src="' + esc(BASE + 'flyers/' + e.f) + '" alt="Flyer" loading="lazy" onerror="this.onerror=null;this.src=\'https://bkcb6.app/' + esc(e.f) + '\'">' : '') + links + '</span>' +
      thumb + '<span class="ch">&rsaquo;</span></div>';
  }
  function sortDay(a, b) { return (b.ty === CB6) - (a.ty === CB6) || minutes(a.t) - minutes(b.t); }

  function renderList() {
    var today = nyToday(), out = '';
    if (S.q) {
      var all = S.events.filter(visible);
      var up = all.filter(function (e) { return e.d >= today; }), past = all.filter(function (e) { return e.d < today; });
      var group = function (list, desc) {
        var dates = Object.keys(list.reduce(function (o, e) { o[e.d] = 1; return o; }, {})).sort();
        if (desc) dates.reverse();
        return dates.map(function (d) { return '<div class="cc-dh">' + longDate(d) + ', ' + d.slice(0, 4) + '</div>' + list.filter(function (e) { return e.d === d; }).sort(sortDay).map(card).join(''); }).join('');
      };
      out = '<div class="cc-note">' + up.length + ' upcoming and ' + past.length + ' past match' + (all.length === 1 ? '' : 'es') + ' for “' + esc(S.q) + '”</div>';
      if (!all.length) out += '<div class="cc-empty">Nothing on the calendar matches that search.</div>';
      if (up.length) out += '<div class="cc-dh" style="color:#0d1b4b">Upcoming</div>' + group(up, false);
      if (past.length) out += '<div class="cc-dh" style="color:#0d1b4b">Past, most recent first</div>' + group(past, true);
    } else {
      var evs = (S.byDate[S.sel] || []).filter(visible).sort(sortDay);
      out = '<div class="cc-dh">' + longDate(S.sel) + '</div>' + (evs.length ? evs.map(card).join('') : '<div class="cc-empty">Nothing on the calendar this day.</div>');
    }
    $('.cc-list').innerHTML = out;
  }

  function renderAll() { renderModes(); renderOrgs(); renderGrid(); renderList(); }

  root.addEventListener('click', function (ev) {
    var t = ev.target.closest('button,[role=button]');
    if (!t || !root.contains(t)) return;
    if (t.dataset.mode) { S.mode = t.dataset.mode; S.org = null; savePrefs(); renderAll(); return; }
    if (t.dataset.org !== undefined && t.classList.contains('cc-chip')) {
      var ty = t.dataset.org;
      if (ev.detail === 2 && ty) { if (S.hidden[ty]) delete S.hidden[ty]; else S.hidden[ty] = 1; if (S.org === ty) S.org = null; savePrefs(); renderAll(); return; }
      if (!ty) { S.org = null; S.hidden = {}; savePrefs(); }
      else if (S.hidden[ty]) { delete S.hidden[ty]; savePrefs(); }
      else S.org = S.org === ty ? null : ty;
      renderAll(); return;
    }
    if (t.dataset.n) { var m = S.ym.m + +t.dataset.n, y = S.ym.y; if (m < 0) { m = 11; y--; } if (m > 11) { m = 0; y++; } S.ym = { y: y, m: m }; S.sel = ds(y, m, 1); var td = nyToday(); if (td.slice(0, 7) === S.sel.slice(0, 7)) S.sel = td; renderAll(); return; }
    if (t.dataset.d) { S.sel = t.dataset.d; if (S.q) { S.q = ''; input.value = ''; savePrefs(); } renderGrid(); renderList(); return; }
    if (t.classList.contains('cc-clear')) { S.q = ''; input.value = ''; savePrefs(); renderAll(); return; }
    if (t.classList.contains('cc-card') && !ev.target.closest('a')) { t.classList.toggle('open'); t.setAttribute('aria-expanded', t.classList.contains('open')); }
  });
  root.addEventListener('keydown', function (ev) { if ((ev.key === 'Enter' || ev.key === ' ') && ev.target.classList && ev.target.classList.contains('cc-card')) { ev.preventDefault(); ev.target.click(); } });
  var qt;
  input.addEventListener('input', function () { clearTimeout(qt); qt = setTimeout(function () { S.q = input.value.trim(); savePrefs(); renderAll(); }, 150); });

  var ARCHIVE = 'https://bkcb6.app/data/cal-archive.json';
  Promise.all([
    fetch(DATA, { cache: 'no-cache' }).then(function (r) { return r.json(); }),
    fetch(ARCHIVE, { cache: 'no-cache' }).then(function (r) { return r.json(); }).catch(function () { return { types: {}, events: [] }; })
  ]).then(function (both) {
    var d = both[0], a = both[1], today0 = nyToday();
    S.types = Object.assign({}, a.types || {}, d.types || {});
    S.events = (a.events || []).filter(function (e) { return e.d < today0; }).concat((d.events || []).filter(function (e) { return e.d >= today0; }));
    S.events.forEach(function (e) { (S.byDate[e.d] = S.byDate[e.d] || []).push(e); });
    var today = nyToday(), t = parse(today);
    S.ym = { y: t.getFullYear(), m: t.getMonth() };
    S.sel = today;
    renderLead(); renderAll();
    window.dispatchEvent(new Event('resize'));
  }).catch(function () { $('.cc-list').innerHTML = '<div class="cc-empty">The calendar could not load. Reload the page to try again.</div>'; });
})();
