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
  // Categories, as on the bkcb6.app calendar. The calendar data carries which calendar types fall in each (cats).
  var MODES = [
    { id: 'all', label: 'All' },
    { id: 'cb6', label: 'CB6 meetings' },
    { id: 'civic', label: 'Civic' },
    { id: 'community', label: 'Community' },
    { id: 'parks', label: 'Parks' },
    { id: 'food', label: 'Food & Markets' },
    { id: 'arts', label: 'Arts' }
  ];
  var VIEWS = [{ id: 'today', label: 'Today' }, { id: 'day', label: 'Day' }, { id: 'week', label: 'Week' }, { id: 'month', label: 'Month' }];
  var GROUP_LIMIT = 3;
  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  var DOWS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  var root = document.getElementById('cb6-app-calendar');
  if (!root) return;

  function loadPrefs() { try { return JSON.parse(localStorage.getItem(PREF_KEY)) || {}; } catch (e) { return {}; } }
  function savePrefs() { try { localStorage.setItem(PREF_KEY, JSON.stringify({ mode: S.mode, view: S.view, hidden: Object.keys(S.hidden), q: S.q })); } catch (e) {} }
  var P = loadPrefs();
  var OLDMODE = { events: 'all', council: 'civic', hearing: 'civic' };
  var S = { mode: OLDMODE[P.mode] || P.mode || 'all', view: P.view || 'today', hidden: {}, q: P.q || '', org: null, ym: null, sel: null, types: {}, cats: {}, events: [], byDate: {}, exp: {}, orgsOpen: false };
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

  function catsOf(e) {
    if (e._c) return e._c;
    var c = {}, k = e.k || '';
    if (e.ty === CB6) c.cb6 = 1;
    if (e.g === 'council' || e.g === 'hearing') c.civic = 1;
    if (/^park-/.test(k)) c.parks = 1;
    if (/^lib-/.test(k)) c.community = 1;
    Object.keys(S.cats).forEach(function (cat) { if (S.cats[cat][k]) c[cat] = 1; });
    return (e._c = c);
  }
  function inMode(e, id) { return id === 'all' || !!catsOf(e)[id]; }
  function visible(e) {
    if (!inMode(e, S.mode)) return false;
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
    '.cc-views{display:flex;background:#fff;border:1.5px solid #e2dccd;border-radius:999px;padding:3px;margin:0 0 12px;gap:2px}' +
    '.cc-view{flex:1;border:0;background:none;border-radius:999px;padding:9px 6px;font-size:15px;font-weight:700;color:' + NAVY + '}' +
    '.cc-view.on{background:' + NAVY + ';color:#fff}' +
    '.cc-chip .n{font-family:"DM Mono",monospace;font-size:12px;color:#8a8a99;font-weight:500}.cc-chip.on .n{color:#c9cee0}' +
    '.cc-orgwrap{margin:-2px 0 6px}' +
    '.cc-orgtoggle{border:0;background:none;color:' + NAVY + ';font-size:14px;font-weight:600;padding:4px 2px 8px;text-decoration:underline;text-underline-offset:3px}' +
    '.cc-orgtoggle.on{color:' + ORANGE + '}' +
    '.cc-orgs[hidden]{display:none}' +
    '.cc-day.wk{background:#eef0f7}.cc-day.wk.sel{background:' + NAVY + '}' +
    '.cc-day .dw{font-family:"DM Mono",monospace;font-size:11px;text-transform:uppercase;color:#6b6b80}.cc-day.sel .dw{color:#c9cee0}' +
    '.cc-gh{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:' + NAVY + ';margin:16px 4px 8px}' +
    '.cc-gh span{font-family:"DM Mono",monospace;font-weight:500;color:#8a8a99;letter-spacing:0}' +
    '.cc-dh.sel{color:' + NAVY + '}' +
    '.cc-more{display:block;width:100%;border:1.5px dashed #d8d0bf;background:none;border-radius:12px;padding:9px;font-size:14px;font-weight:600;color:' + NAVY + ';margin:-2px 0 10px}' +
    '.cc-list .cc-card{padding:10px 12px;gap:12px;border-radius:12px;margin-bottom:8px}' +
    '.cc-list .cc-card .lg{width:40px;height:40px;border-radius:8px}' +
    '.cc-list .cc-card .tt{font-size:16px}' +
    '.cc-list .cc-card .mt{font-size:13px}' +
    '.cc-list .cc-thumb{width:40px;height:40px}' +
    '.cc-umb{background:#fff;border:1.5px solid #ece6d8;border-radius:12px;margin-bottom:8px}' +
    '.cc-umbh{display:flex;gap:12px;align-items:center;padding:10px 12px;cursor:pointer;color:' + NAVY + '}' +
    '.cc-umbh .lg{width:40px;height:40px;flex:none;border-radius:8px;object-fit:contain;background:#fff}' +
    '.cc-umbh .lg.ph{display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700}' +
    '.cc-umbh .b{flex:1;min-width:0}.cc-umbh .tt{display:block;font-size:16px;font-weight:700}' +
    '.cc-umbh .cnt{font-family:"DM Mono",monospace;font-size:12px;font-weight:500;color:#fff;background:' + NAVY + ';border-radius:999px;padding:2px 8px;margin-left:4px;vertical-align:2px}' +
    '.cc-umbh .mt{display:block;font-size:13px;color:#5a5a6e;margin-top:2px}' +
    '.cc-umbh .pv{display:block;font-size:13px;color:#3d3d52;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
    '.cc-umbh .ch{flex:none;color:' + ORANGE + ';font-size:24px;font-weight:700;transition:transform .15s}.cc-umb.open .cc-umbh .ch{transform:rotate(90deg)}' +
    '.cc-umbb{padding:0 10px 4px 22px;border-top:1px solid #f0ebe0}.cc-umbb .cc-card{border:0;border-bottom:1px solid #f0ebe0;border-radius:0;margin:0;background:none}.cc-umbb .cc-card:last-child{border-bottom:0}.cc-umbb .cc-card .lg{display:none}' +
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
    '<div class="cc-views" role="tablist"></div>' +
    '<div class="cc-row cc-modes"></div>' +
    '<div class="cc-orgwrap"><button type="button" class="cc-orgtoggle"></button><div class="cc-row cc-orgs" hidden></div></div>' +
    '<div class="cc-cal"><div class="cc-mh"><button type="button" data-n="-1" aria-label="Previous">&lsaquo;</button><h3></h3><button type="button" data-n="1" aria-label="Next">&rsaquo;</button></div><div class="cc-grid"></div></div>' +
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

  function addDays(d, n) { var x = parse(d); x.setDate(x.getDate() + n); return ds(x.getFullYear(), x.getMonth(), x.getDate()); }
  function weekStart(d) { var x = parse(d); return addDays(d, -x.getDay()); }
  function shortDate(d) { var x = parse(d); return MONTHS[x.getMonth()].slice(0, 3) + ' ' + x.getDate(); }
  function view() { return S.view === 'today' ? 'day' : S.view; }
  function dayEvents(d) { return (S.byDate[d] || []).filter(visible).sort(sortDay); }

  function renderViews() {
    var today = nyToday();
    $('.cc-views').innerHTML = VIEWS.map(function (v) {
      var on = v.id === 'today' ? (S.view === 'today' || (S.view === 'day' && S.sel === today)) : (S.view === v.id && !(v.id === 'day' && S.sel === today));
      return '<button type="button" class="cc-view' + (on ? ' on' : '') + '" data-view="' + v.id + '" role="tab" aria-selected="' + on + '">' + v.label + '</button>';
    }).join('');
  }
  function renderModes() {
    $('.cc-modes').innerHTML = MODES.map(function (m) {
      var n = periodEvents(m.id).length;
      if (m.id !== 'all' && m.id !== S.mode && !n) return '';
      return '<button type="button" class="cc-chip' + (S.mode === m.id ? ' on' : '') + '" data-mode="' + m.id + '">' + esc(m.label) + ' <span class="n">' + n + '</span></button>';
    }).join('');
  }
  // The events in what is on screen (the day, the week or the month), for the counts on the filters.
  function periodEvents(mode) {
    var from, to, v = view();
    if (v === 'month') { from = S.ym.y + '-' + String(S.ym.m + 1).padStart(2, '0') + '-01'; to = from.slice(0, 8) + '31'; }
    else if (v === 'week') { from = weekStart(S.sel); to = addDays(from, 6); }
    else { from = to = S.sel; }
    return S.events.filter(function (e) { return e.d >= from && e.d <= to && inMode(e, mode) && !S.hidden[e.ty]; });
  }

  function renderOrgs() {
    var counts = {};
    periodEvents(S.mode).forEach(function (e) { counts[e.ty] = (counts[e.ty] || 0) + 1; });
    var tys = Object.keys(counts).sort(function (a, b) { return (b === CB6) - (a === CB6) || counts[b] - counts[a]; });
    var hid = Object.keys(S.hidden).length;
    $('.cc-orgtoggle').innerHTML = (S.org ? 'Organization: ' + esc((S.types[S.org] && S.types[S.org].name) || S.org) : 'Filter by organization') + (hid ? ' &middot; ' + hid + ' hidden' : '') + ' <span>' + (S.orgsOpen ? '&#9652;' : '&#9662;') + '</span>';
    $('.cc-orgtoggle').classList.toggle('on', !!S.org);
    $('.cc-orgs').hidden = !S.orgsOpen;
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

  function dayButton(key, label, cls) {
    var evs = dayEvents(key), today = nyToday();
    var cols = [], seen = {};
    evs.forEach(function (e) { var c = color(e.ty); if (!seen[c]) { seen[c] = 1; cols.push(c); } });
    var isCb6 = evs.some(function (e) { return e.ty === CB6; });
    var c = 'cc-day' + (cls || '') + (isCb6 ? ' cb6' : '') + (key === today ? ' today' : '') + (key === S.sel ? ' sel' : '') + (key < today ? ' past' : '');
    return '<button type="button" class="' + c + '" data-d="' + key + '" aria-label="' + longDate(key) + ', ' + evs.length + ' events">' + label +
      '<span class="dots">' + cols.slice(0, 3).map(function (x) { return '<i style="background:' + x + '"></i>'; }).join('') + '</span>' +
      '<span class="more">' + (evs.length ? evs.length : '') + '</span></button>';
  }
  // The month calendar is always there; the view (Today, Day, Week, Month) sets what the list below it shows.
  function renderGrid() {
    var v = view(), y = S.ym.y, m = S.ym.m, w0 = weekStart(S.sel), w6 = addDays(w0, 6);
    $('.cc-cal').className = 'cc-cal v-' + v;
    $('.cc-mh h3').textContent = MONTHS[m] + ' ' + y;
    var first = new Date(y, m, 1).getDay(), days = new Date(y, m + 1, 0).getDate();
    var html = ['S', 'M', 'T', 'W', 'T', 'F', 'S'].map(function (d) { return '<div class="cc-dow">' + d + '</div>'; }).join('');
    for (var i = 0; i < first; i++) html += '<div class="cc-day blank"></div>';
    for (var d = 1; d <= days; d++) { var key = ds(y, m, d); html += dayButton(key, '<span class="dn">' + d + '</span>', v === 'week' && key >= w0 && key <= w6 ? ' wk' : ''); }
    $('.cc-grid').innerHTML = html;
  }

  // Time, organization and place, each said once: drops a place segment or comma piece that repeats the organization, the title or an earlier piece.
  function metaOf(e, isCb6) {
    var nz = function (x) { return String(x || '').toLowerCase().replace(/&amp;/g, '&').replace(/[^a-z0-9]/g, ''); };
    var org = isCb6 ? '' : orgName(e), kept = [nz(org), nz(e.l)], parts = [];
    String(cleanLoc(e.loc) || '').replace(/,\s*United States$/, '').split(/\s*\u00b7\s*/).forEach(function (seg) {
      var pieces = seg.split(/\s*,\s*/).filter(function (pc) {
        var k = nz(pc); if (!k) return false;
        for (var i = 0; i < kept.length; i++) if (kept[i] && kept[i].indexOf(k) > -1) return false;
        kept.push(k); return true;
      });
      if (pieces.length) parts.push(pieces.join(', '));
    });
    return [e.t ? e.t + (e.e && minutes(e.e) > minutes(e.t) ? ' to ' + e.e : '') : '', org].concat(parts).filter(Boolean).join(' \u00b7 ');
  }
  function card(e) {
    var isCb6 = e.ty === CB6, ic = isCb6 ? 'https://bkcb6.app/cb6-logo-square.png' : icon(e.ty);
    var meta = metaOf(e, isCb6);
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

  // One organization, one entry a day: two or more events from the same organization on a day sit under one card that opens to list them.
  function items(d, evs) {
    var by = {}, order = [];
    evs.forEach(function (e) {
      var k = e.ty === CB6 ? CB6 + '|' + order.length : e.ty;
      if (!by[k]) { by[k] = []; order.push(k); }
      by[k].push(e);
    });
    return order.map(function (k) { var list = by[k]; return { e: list[0], list: list, html: list.length > 1 ? umbrella(d, list) : card(list[0]) }; });
  }
  function umbrella(d, list) {
    var e = list[0], ty = e.ty, ic = icon(ty), key = d + '|org|' + ty, open = !!S.exp[key];
    var times = list.map(function (x) { return x.t; }).filter(Boolean);
    var span = times.length ? 'From ' + times[0] : '';
    var logo = ic ? '<img class="lg" src="' + esc(ic) + '" alt="" loading="lazy">' : '<span class="lg ph" style="background:' + color(ty) + '">' + esc(orgName(e).charAt(0)) + '</span>';
    var preview = list.slice(0, 3).map(function (x) { return esc(x.l); }).join(' &middot; ') + (list.length > 3 ? ' &middot; +' + (list.length - 3) + ' more' : '');
    return '<div class="cc-umb' + (open ? ' open' : '') + '"><div class="cc-umbh" role="button" tabindex="0" aria-expanded="' + open + '" data-umb="' + esc(key) + '">' + logo +
      '<span class="b"><span class="tt">' + esc(orgName(e)) + ' <span class="cnt">' + list.length + ' events</span></span><span class="mt">' + esc(span) + '</span>' +
      (open ? '' : '<span class="pv">' + preview + '</span>') + '</span><span class="ch">&rsaquo;</span></div>' +
      (open ? '<div class="cc-umbb">' + list.map(card).join('') + '</div>' : '') + '</div>';
  }

  // A day's events grouped by category, CB6 first, a few of each with the rest a tap away.
  var GROUPS = [['cb6', 'CB6 meetings'], ['civic', 'Civic'], ['community', 'Community'], ['parks', 'Parks'], ['food', 'Food & Markets'], ['arts', 'Arts'], ['other', 'More events']];
  function groupDay(d, evs, limit) {
    var by = {};
    items(d, evs).forEach(function (it) {
      var c = catsOf(it.e), g = 'other';
      for (var j = 0; j < GROUPS.length - 1; j++) if (c[GROUPS[j][0]]) { g = GROUPS[j][0]; break; }
      (by[g] = by[g] || []).push(it);
    });
    return GROUPS.filter(function (g) { return by[g[0]]; }).map(function (g) {
      var list = by[g[0]], key = d + '|' + g[0], open = S.exp[key], lim = g[0] === 'cb6' ? 99 : limit;
      var shown = open ? list : list.slice(0, lim), rest = list.length - shown.length;
      var n = list.reduce(function (a, it) { return a + it.list.length; }, 0);
      return '<div class="cc-gh">' + g[1] + ' <span>' + n + '</span></div>' + shown.map(function (it) { return it.html; }).join('') +
        (rest > 0 ? '<button type="button" class="cc-more" data-exp="' + esc(key) + '">Show ' + rest + ' more</button>' : '');
    }).join('');
  }
  function flatDay(d, evs, limit) {
    var its = items(d, evs), key = d + '|flat', open = S.exp[key], shown = open ? its : its.slice(0, limit), rest = its.length - shown.length;
    return shown.map(function (it) { return it.html; }).join('') + (rest > 0 ? '<button type="button" class="cc-more" data-exp="' + esc(key) + '">Show ' + rest + ' more</button>' : '');
  }

  function renderList() {
    var today = nyToday(), out = '', v = view();
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
    } else if (v === 'week' || v === 'month') {
      var w0 = v === 'week' ? weekStart(S.sel) : (S.ym.y + '-' + String(S.ym.m + 1).padStart(2, '0') + '-01'), nd = v === 'week' ? 7 : new Date(S.ym.y, S.ym.m + 1, 0).getDate();
      if (v === 'month' && today.slice(0, 7) === w0.slice(0, 7)) { nd -= +today.slice(8) - 1; w0 = today; }
      out = '<div class="cc-dh" style="color:#0d1b4b">' + (v === 'week' ? 'Week of ' + shortDate(weekStart(S.sel)) + ' to ' + shortDate(addDays(weekStart(S.sel), 6)) : MONTHS[S.ym.m] + (w0 === today ? ', from today' : '')) + '</div>';
      for (var k = 0; k < nd; k++) {
        var d = addDays(w0, k), evs = dayEvents(d);
        if (v === 'month' && !evs.length) continue;
        out += '<div class="cc-dh' + (d === S.sel ? ' sel' : '') + '">' + longDate(d) + (d === today ? ' &middot; today' : '') + '</div>';
        if (!evs.length) { out += '<div class="cc-empty">Nothing on the calendar.</div>'; continue; }
        var its = items(d, evs), ncb6 = its.filter(function (it) { return it.e.ty === CB6; }).length, top = its.slice(0, Math.max(3, ncb6));
        out += top.map(function (it) { return it.html; }).join('') + (its.length > top.length ? '<button type="button" class="cc-more" data-day="' + d + '">See all ' + evs.length + ' that day &rsaquo;</button>' : '');
      }
    } else {
      var de = dayEvents(S.sel);
      out = '<div class="cc-dh">' + (S.sel === today ? 'Today, ' : '') + longDate(S.sel) + ' &middot; ' + de.length + ' event' + (de.length === 1 ? '' : 's') + '</div>' +
        (de.length ? (S.mode === 'all' && !S.org ? groupDay(S.sel, de, GROUP_LIMIT) : flatDay(S.sel, de, 8)) : '<div class="cc-empty">Nothing on the calendar this day.</div>');
    }
    $('.cc-list').innerHTML = out;
  }

  function renderAll() { renderViews(); renderModes(); renderOrgs(); renderGrid(); renderList(); }
  function setSel(d) { S.sel = d; var x = parse(d); S.ym = { y: x.getFullYear(), m: x.getMonth() }; }

  root.addEventListener('click', function (ev) {
    var t = ev.target.closest('button,[role=button]');
    if (!t || !root.contains(t)) return;
    if (t.dataset.view) { S.view = t.dataset.view; if (S.view === 'today') setSel(nyToday()); if (S.q) { S.q = ''; input.value = ''; } savePrefs(); renderAll(); return; }
    if (t.dataset.mode) { S.mode = t.dataset.mode; S.org = null; savePrefs(); renderAll(); return; }
    if (t.classList.contains('cc-orgtoggle')) { S.orgsOpen = !S.orgsOpen; renderOrgs(); return; }
    if (t.dataset.org !== undefined && t.classList.contains('cc-chip')) {
      var ty = t.dataset.org;
      if (ev.detail === 2 && ty) { if (S.hidden[ty]) delete S.hidden[ty]; else S.hidden[ty] = 1; if (S.org === ty) S.org = null; savePrefs(); renderAll(); return; }
      if (!ty) { S.org = null; S.hidden = {}; savePrefs(); }
      else if (S.hidden[ty]) { delete S.hidden[ty]; savePrefs(); }
      else S.org = S.org === ty ? null : ty;
      renderAll(); return;
    }
    if (t.dataset.exp) { S.exp[t.dataset.exp] = 1; renderList(); return; }
    if (t.dataset.umb) { var uk = t.dataset.umb; if (S.exp[uk]) delete S.exp[uk]; else S.exp[uk] = 1; renderList(); return; }
    if (t.dataset.n) {
      var n = +t.dataset.n, v = view();
      var m = S.ym.m + n, y = S.ym.y; if (m < 0) { m = 11; y--; } if (m > 11) { m = 0; y++; } S.ym = { y: y, m: m }; S.sel = ds(y, m, 1); var td = nyToday(); if (td.slice(0, 7) === S.sel.slice(0, 7)) S.sel = td;
      if (S.view === 'today' && S.sel !== td) S.view = 'day';
      renderAll(); return;
    }
    if (t.dataset.day) { setSel(t.dataset.day); S.view = 'day'; savePrefs(); renderAll(); root.querySelector('.cc-list').scrollIntoView({ behavior: 'smooth', block: 'start' }); return; }
    if (t.dataset.d) {
      setSel(t.dataset.d); if (S.q) { S.q = ''; input.value = ''; savePrefs(); }
      if (S.view === 'today') S.view = 'day';
      renderAll(); return;
    }
    if (t.classList.contains('cc-clear')) { S.q = ''; input.value = ''; savePrefs(); renderAll(); return; }
    if (t.classList.contains('cc-card') && !ev.target.closest('a')) { t.classList.toggle('open'); t.setAttribute('aria-expanded', t.classList.contains('open')); }
  });
  root.addEventListener('keydown', function (ev) { if ((ev.key === 'Enter' || ev.key === ' ') && ev.target.classList && (ev.target.classList.contains('cc-card') || ev.target.classList.contains('cc-umbh'))) { ev.preventDefault(); ev.target.click(); } });
  var qt;
  input.addEventListener('input', function () { clearTimeout(qt); qt = setTimeout(function () { S.q = input.value.trim(); savePrefs(); renderAll(); }, 150); });

  var ARCHIVE = 'https://bkcb6.app/data/cal-archive.json';
  Promise.all([
    fetch(DATA, { cache: 'no-cache' }).then(function (r) { return r.json(); }),
    fetch(ARCHIVE, { cache: 'no-cache' }).then(function (r) { return r.json(); }).catch(function () { return { types: {}, events: [] }; })
  ]).then(function (both) {
    var d = both[0], a = both[1], today0 = nyToday();
    S.types = Object.assign({}, a.types || {}, d.types || {});
    Object.keys(d.cats || {}).forEach(function (c) { S.cats[c] = {}; d.cats[c].forEach(function (k) { S.cats[c][k] = 1; }); });
    S.events = (a.events || []).filter(function (e) { return e.d < today0; }).concat((d.events || []).filter(function (e) { return e.d >= today0; }));
    S.events.forEach(function (e) { (S.byDate[e.d] = S.byDate[e.d] || []).push(e); });
    var today = nyToday(), t = parse(today);
    S.ym = { y: t.getFullYear(), m: t.getMonth() };
    S.sel = today;
    if (S.view === 'day') S.view = 'today';
    renderLead(); renderAll();
    window.dispatchEvent(new Event('resize'));
  }).catch(function () { $('.cc-list').innerHTML = '<div class="cc-empty">The calendar could not load. Reload the page to try again.</div>'; });
})();
