/* Who represented a community board on any date, and who has held a seat, from the district history
   (data/districthistory/overlap.json: every Council, Assembly, State Senate and Congressional district that covered
   each of the 59 boards, term by term, with its members) and data/districthistory/at-large.json (borough, city, state
   and federal offices).
   <div data-rep-board="306"></div>                         who represented the board on a date (today by default)
   <div data-rep-seat="council" data-district="39"></div>    everyone who has held a district seat, with the boards it covered
   <div data-rep-seat="mayor"></div>  data-rep-seat="bp" data-boro="3"   data-rep-seat="ussenate" data-seat="1"  */
(function () {
  var OV = null, AL = null;
  var BORO = { '1': 'MN', '2': 'BX', '3': 'BK', '4': 'QN', '5': 'SI' };
  var BORON = { '1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island' };
  var NAME = { council: 'Council District', assembly: 'Assembly District', senate: 'State Senate District', congress: 'Congressional District' };
  function code(c) { c = String(c); return BORO[c[0]] + 'CB' + (+c.slice(1)); }
  function lab(o, d) { return o === 'congress' ? 'NY-' + d : ({ council: 'CD', assembly: 'AD', senate: 'SD' })[o] + ' ' + d; }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (m) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m]; }); }
  function p1(x) { return (x * 100).toFixed(1).replace(/\.0$/, '') + '%'; }
  var M = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  function nice(d) { var p = d.split('-'); return M[+p[1] - 1] + ' ' + (+p[2]) + ', ' + p[0]; }
  function today() { var t = new Date(); return t.getFullYear() + '-' + ('0' + (t.getMonth() + 1)).slice(-2) + '-' + ('0' + t.getDate()).slice(-2); }
  function j(u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(u); return r.json(); }); }
  function data() {
    return Promise.all([OV || j('/data/districthistory/overlap.json').then(function (d) { OV = d; }), AL || j('/data/districthistory/at-large.json').then(function (d) { AL = d; })]);
  }
  function css() {
    if (document.getElementById('rep-history-css')) return;
    var s = document.createElement('style'); s.id = 'rep-history-css';
    s.textContent = '.rh{border:1.5px solid #0d1b4b;border-radius:10px;overflow:hidden;background:#fff;font-family:"DM Sans",sans-serif;color:#1a1a1a}' +
      '.rh-head{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;background:#0d1b4b;color:#fff;padding:10px 14px}' +
      '.rh-t{font-weight:700;font-size:.95rem}.rh-ctl{display:flex;gap:6px;align-items:center}' +
      '.rh-ctl input{font-family:"DM Mono",monospace;font-size:.82rem;padding:6px 8px;border-radius:6px;border:0}' +
      '.rh-ctl button,.rh-go{font-family:"DM Sans",sans-serif;font-size:.78rem;font-weight:700;padding:6px 10px;border-radius:6px;border:0;background:#f47920;color:#fff;cursor:pointer;text-decoration:none;display:inline-block}' +
      '.rh-g{padding:10px 14px 4px}.rh-gh{font-family:"DM Mono",monospace;font-size:.62rem;text-transform:uppercase;letter-spacing:.08em;color:#6b6b6b;margin:6px 0 4px}' +
      '.rh-r{display:grid;grid-template-columns:150px minmax(0,1fr);gap:8px;padding:6px 0;border-bottom:1px solid #f0ede7;font-size:.84rem;align-items:baseline}.rh-r:last-child{border-bottom:0}' +
      '.rh-o{font-weight:700;color:#0d1b4b;font-size:.78rem}.rh-n div{margin:1px 0}.rh-n b{color:#0d1b4b}.rh-n small{color:#6b6b6b;font-family:"DM Mono",monospace;font-size:.68rem;margin-left:4px}' +
      '.rh-foot{padding:10px 14px;border-top:1px solid #f0ede7}' +
      '.rh-tbl{width:100%;border-collapse:collapse;font-size:.82rem}.rh-tbl th{text-align:left;font-family:"DM Mono",monospace;font-size:.6rem;text-transform:uppercase;letter-spacing:.06em;color:#6b6b6b;padding:6px 8px;border-bottom:1px solid #e5e2db}' +
      '.rh-tbl td{padding:7px 8px;border-bottom:1px solid #f0ede7;vertical-align:top}.rh-tbl td b{color:#0d1b4b}.rh-tbl small{color:#6b6b6b;font-family:"DM Mono",monospace;font-size:.66rem}' +
      '.rh-x{margin:0 14px 12px;border:1px solid #e5e2db;border-radius:8px}.rh-x summary{cursor:pointer;font-weight:700;color:#0d1b4b;padding:9px 12px;font-size:.86rem}.rh-xb{padding:0 12px 10px;font-size:.82rem;line-height:1.55}.rh-xb p{margin:0 0 8px}.rh-src{color:#6b6b6b;font-size:.74rem}.rh-src a{color:#0d1b4b}' +
      '@media(max-width:560px){.rh-r{grid-template-columns:1fr;gap:2px}}';
    document.head.appendChild(s);
  }
  var P = { g: 'rh-g', gh: 'rh-gh', r: 'rh-r', o: 'rh-o', n: 'rh-n', d: 'rh-x', db: 'rh-xb', src: 'rh-src' };
  function pick(hs, dt) { var h = null; (hs || []).forEach(function (x) { if (x.from <= dt) h = x; }); if (!h || (h.to && dt > h.to)) return null; return h; }
  function stateHolders(row, ms) {
    return ms.map(function (m) { return { name: m.name, from: m.type === 'special' ? m.elected : row.served.slice(0, 4) + '-01-01', special: m.type === 'special' ? m.elected : null }; });
  }


  // ---- borough, city, state and federal offices on a date (shared with /electionhistory/) ----
  var BOEND = '1990-08-31';
  function since(x) { return x.years ? 'since ' + x.from.slice(0, 4) : 'since ' + nice(x.from); }
  function labelOn(o, dt) { var l = o.label; (o.labels || []).forEach(function (x) { if (x[0] <= dt) l = x[1]; }); return l; }
  function atLargeHTML(AL, cb, dt, P) {
    var grp = { boro: ({ '2': 'The Bronx' }[cb[0]] || BORON[cb[0]]), city: 'New York City', state: 'New York State', us: 'United States' }, last = null, h = '', mute = '<span style="color:#6b6b6b">';
    var cur = {};
    AL.offices.forEach(function (o) {
      if (o.from && dt < o.from) return;
      if (o.until && dt > o.until) return;
      if (o.eras && !o.eras.some(function (e) { return e[0] <= dt && dt <= e[1]; })) return;
      if (o.scope !== last) { h += (last ? '</div>' : '') + '<div class="' + P.g + '"><div class="' + P.gh + '">' + esc(grp[o.scope]) + '</div>'; last = o.scope; }
      var cell;
      if (o.multi) {
        var hs = (o.holders[cb[0]] || []).filter(function (x) { return x.from <= dt && dt <= (x.to || '9999'); });
        cell = hs.length ? hs.map(function (x) { return '<div><b>' + esc(x.name) + '</b><small>' + esc(since(x)) + '</small></div>'; }).join('') : '<div>' + mute + 'None on record for this date</span></div>';
        cell += '<div><small style="margin:0">Only members whose own Wikipedia article gives their term; the list is incomplete.</small></div>';
      } else {
        var lists = o.seats ? o.seats : [o.scope === 'boro' ? o.holders[cb[0]] : o.holders];
        cell = lists.map(function (hs) { var x = pick(hs, dt); if (x && !o.seats) cur[o.key] = x;
          return '<div>' + (x ? '<b>' + esc(x.name) + '</b>' + (x.note ? ' <small style="margin:0">(' + esc(x.note) + ')</small>' : '') + '<small>' + esc(since(x)) + '</small>' : mute + 'Vacant</span>') + '</div>'; }).join('');
      }
      h += '<div class="' + P.r + '"><span class="' + P.o + '">' + esc(labelOn(o, dt)) + '</span><span class="' + P.n + '">' + cell + '</span></div>';
      if (o.key === 'comptroller' && dt <= BOEND && dt >= '1898-01-01') h += boeRow(AL, dt, P, cur);
    });
    return h + (last ? '</div>' : '');
  }
  // the Board of Estimate on a date: who sat on it and how its votes were split (Wikipedia, New York City Board of Estimate)
  function boeRow(AL, dt, P, cur) {
    var bp = AL.offices.filter(function (o) { return o.key === 'bp'; })[0], pa = AL.offices.filter(function (o) { return o.key === 'pa'; })[0];
    var who = function (o, hs) { var x = pick(hs, dt); return x ? esc(x.name) : 'vacant'; };
    var votes = dt < '1901-01-01' ? null : dt < '1957-01-01' ? [3, { '1': 2, '3': 2, '2': 1, '4': 1, '5': 1 }] : [4, { '1': 2, '2': 2, '3': 2, '4': 2, '5': 2 }];
    var v = function (n) { return votes ? ' <small style="margin:0">' + n + (n === 1 ? ' vote' : ' votes') + '</small>' : ''; };
    var m = AL.offices.filter(function (o) { return o.key === 'mayor'; })[0], c = AL.offices.filter(function (o) { return o.key === 'comptroller'; })[0];
    var rows = '<div>Mayor ' + who(m, m.holders) + v(votes && votes[0]) + '</div><div>Comptroller ' + who(c, c.holders) + v(votes && votes[0]) + '</div><div>' + esc(labelOn(pa, dt)) + ' ' + who(pa, pa.holders) + v(votes && votes[0]) + '</div>';
    ['1', '2', '3', '4', '5'].forEach(function (b) { rows += '<div>' + ({ '2': 'The Bronx' }[b] || (b === '5' && dt < '1975-01-01' ? 'Richmond (Staten Island)' : BORON[b])) + ' Borough President ' + who(bp, bp.holders[b]) + v(votes && votes[1][b]) + '</div>'; });
    return '<div class="' + P.r + '"><span class="' + P.o + '">Board of Estimate</span><span class="' + P.n + '">' +
      (votes ? '' : '<div><small style="margin:0">From 1898 to 1900 a five-member Board of Estimate and Apportionment; from 1901 the eight members below.</small></div>') + rows +
      '<div><small style="margin:0">The city budget, land use, contracts and franchises went through this board until August 31, 1990.</small></div></span></div>';
  }
  // how these offices changed: sourced from the Wikipedia articles linked at the end
  function explainer(P) {
    var W = 'https://en.wikipedia.org/wiki/';
    return '<details class="' + P.d + '"><summary>How these offices changed since 1898</summary><div class="' + P.db + '">' +
      '<p><b>Board of Estimate (1898 to 1990).</b> Until 1990 the city budget, land use, contracts, franchises and water rates went through the Board of Estimate. From 1901 its eight members were the Mayor, the Comptroller and the President of the Board of Aldermen, with three votes each; the Manhattan and Brooklyn Borough Presidents, with two each; and the Bronx, Queens and Richmond (Staten Island) Borough Presidents, with one each. In 1957 the board went to 22 votes: four each for the three citywide officials and two for each Borough President. On March 22, 1989, the U.S. Supreme Court ruled unanimously in <i>Board of Estimate of City of New York v. Morris</i> that the board was unconstitutional, because Brooklyn, the most populous borough, had no more say than Staten Island, the least populous. Voters approved a new charter that November, 55% to 45%; it gave most of the board&rsquo;s work to an enlarged City Council, and the board was dissolved on August 31, 1990.</p>' +
      '<p><b>Borough President.</b> The five offices were created on January 1, 1898, when the city was consolidated, to take over work of the former mayors of Brooklyn and Long Island City, the towns of Queens and Richmond, and county offices. For most of the city&rsquo;s history the Borough Presidents ran much of their borough&rsquo;s government and sat on the Board of Estimate. Since 1990 the office mostly advises: Borough Presidents appoint community board members, one member of the City Planning Commission and two of the Panel for Educational Policy, make recommendations on land use (ULURP) and the budget, and advocate for their borough.</p>' +
      '<p><b>From President of the Council to Public Advocate.</b> The third citywide office, elected with the Mayor and Comptroller, has had four titles: President of the Council (1898 to 1901), President of the Board of Aldermen (1902 to 1937), President of the City Council (1938 to 1993) and Public Advocate (renamed by the Council in 1993, first held in 1994). The officer presided over the city&rsquo;s legislature until a 2002 charter change gave that role to a Speaker elected by the Council, and becomes acting mayor if the Mayor&rsquo;s office is vacant.</p>' +
      '<p><b>Board of Aldermen.</b> The city&rsquo;s legislature was the Board of Aldermen until 1937 (from 1898 to 1901 it shared the Municipal Assembly with a body called the Council). The 1938 charter replaced it with the New York City Council.</p>' +
      '<p><b>Council members elected borough-wide.</b> From 1938 to 1949 every Council member was elected by proportional representation (single transferable vote) across a whole borough, with a quota of 75,000 votes, so the Council&rsquo;s size changed with turnout. Later, at-large seats elected borough-wide sat alongside the district members until they were abolished in June 1983.</p>' +
      '<p><b>Council Speaker.</b> Chosen by the Council members from among themselves; the list here starts with Peter Vallone Sr. in 1992. Since the 2002 change the Speaker also presides over the Council.</p>' +
      '<p class="' + P.src + '">Sources: <a href="' + W + 'New_York_City_Board_of_Estimate">Board of Estimate</a>, <a href="' + W + 'Government_of_New_York_City#Borough_presidents">Borough presidents</a>, <a href="' + W + 'New_York_City_Public_Advocate">Public Advocate</a>, <a href="' + W + 'New_York_City_Council">New York City Council</a>, <a href="' + W + 'New_York_City_Board_of_Aldermen">Board of Aldermen</a>, <a href="' + W + 'Aileen_B._Ryan">Aileen B. Ryan (at-large seats abolished, 1983)</a>.</p></div></details>';
  }
  window.RepHistory = { atLargeHTML: atLargeHTML, explainer: explainer, pick: pick };
  // ---- a board on a date ----
  function renderBoard(el) {
    var cb = String(el.getAttribute('data-rep-board')), c = code(cb), y0 = AL && AL.since || '1898-01-01';
    el.innerHTML = '<div class="rh"><div class="rh-head"><span class="rh-t"></span><span class="rh-ctl"><input type="date" min="' + y0 + '" max="' + today() + '" value="' + today() + '"><button type="button">Today</button></span></div><div class="rh-body"></div>' +
      '<div class="rh-foot" style="display:flex;flex-wrap:wrap;gap:8px"><a class="rh-go" href="/electionhistory/?cb=' + cb + '">Every election since 2000 in ' + esc(c) + ', by election district &rarr;</a><a class="rh-go" style="background:#0d1b4b" href="/atlas/?cb=' + cb + '">' + esc(c) + ' in the Census Atlas: mapped, ranked and compared &rarr;</a></div></div>';
    var inp = el.querySelector('input'), body = el.querySelector('.rh-body'), ttl = el.querySelector('.rh-t');
    function draw() {
      var dt = inp.value || today(), y = +dt.slice(0, 4);
      ttl.textContent = 'Who represented ' + c + ' on ' + nice(dt);
      var h = '<div class="rh-g"><div class="rh-gh">Districts covering ' + esc(c) + ' (share of the board’s residents)</div>';
      OV.offices.forEach(function (o) {
        var r = o.rows.filter(function (x) { return +x.served.slice(0, 4) <= y && y <= +x.served.slice(-4); })[0], cell;
        if (!r) cell = '<span style="color:#6b6b6b">District lines in this record start in ' + o.rows[0].served.slice(0, 4) + '</span>';
        else cell = (r.cbs[cb] || []).map(function (x) {
          var ms = r.members[String(x[0])] || [], who = [];
          if (o.key === 'council') ms.forEach(function (m) { if (m.from <= dt && dt <= m.to) who.push(m); });
          else { var cur = null; stateHolders(r, ms).forEach(function (m) { if (m.from <= dt) cur = m; }); if (cur) who.push(cur); }
          var nm = who.length ? who.map(function (m) { return '<b>' + esc(m.name) + '</b>' + (m.special ? '<small>won special election ' + esc(nice(m.special)) + '</small>' : ''); }).join(', ') : '<span style="color:#6b6b6b">Vacant</span>';
          return '<div>' + esc(lab(o.key, x[0])) + ': ' + nm + '<small>' + p1(x[1]) + '</small></div>';
        }).join('');
        h += '<div class="rh-r"><span class="rh-o">' + esc(o.label) + '</span><span class="rh-n">' + cell + '</span></div>';
      });
      h += '</div>';
      h += atLargeHTML(AL, cb, dt, P);
      body.innerHTML = h + explainer(P);
    }
    inp.addEventListener('change', draw);
    el.querySelector('.rh-ctl button').addEventListener('click', function () { inp.value = today(); draw(); });
    draw();
  }

  // ---- a seat over time ----
  function renderSeat(el) {
    var kind = el.getAttribute('data-rep-seat'), d = el.getAttribute('data-district'), h = '';
    var o = OV.offices.filter(function (x) { return x.key === kind; })[0];
    if (o) {
      var title = NAME[kind] + ' ' + d;
      h = '<div class="rh"><div class="rh-head"><span class="rh-t">Who has held ' + esc(kind === 'congress' ? 'NY-' + d : title) + '</span></div><div class="rh-g" style="overflow-x:auto"><table class="rh-tbl"><thead><tr><th>Term</th><th>Held by</th><th>Boards in the district</th></tr></thead><tbody>';
      o.rows.slice().reverse().forEach(function (r) {
        var ms = r.members[String(d)];
        var boards = [], tot = 0;
        Object.keys(r.cbs).forEach(function (cb) { (r.cbs[cb] || []).forEach(function (x) { if (String(x[0]) === String(d)) { boards.push([cb, x[2]]); tot += x[2]; } }); });
        if (!ms && !boards.length) return;
        boards.sort(function (a, b) { return b[1] - a[1]; });
        var who = (ms || []).map(function (m) {
          if (kind === 'council') return '<b>' + esc(m.name) + '</b> <small>' + esc(nice(m.from)) + ' to ' + esc(m.to > today() ? 'today' : nice(m.to)) + '</small>';
          return '<b>' + esc(m.name) + '</b>' + (m.type === 'special' ? ' <small>won special election ' + esc(nice(m.elected)) + '</small>' : '');
        }).join('<br>') || '<span style="color:#6b6b6b">No member in this record</span>';
        h += '<tr><td style="white-space:nowrap"><b>' + esc(r.served) + '</b><br><small>elected ' + r.election + ' &middot; lines: ' + esc(r.release) + '</small></td><td>' + who + '</td><td>' +
          boards.map(function (b) { return '<a href="/electionhistory/?cb=' + b[0] + '" style="color:#0d1b4b">' + esc(code(b[0])) + '</a> <small>' + (tot ? p1(b[1] / tot) : '') + '</small>'; }).join(', ') + '</td></tr>';
      });
      var go = kind === 'assembly' ? '/electionhistory/?cmp=ad:' + d : '/electionhistory/';
      h += '</tbody></table></div><div class="rh-foot"><a class="rh-go" href="' + go + '">Every election since 2000, by election district and community board &rarr;</a></div></div>';
    } else {
      var a = AL.offices.filter(function (x) { return x.key === kind; })[0];
      if (!a) return;
      var hs = a.seats ? a.seats[+(el.getAttribute('data-seat') || 0)] : (a.scope === 'boro' ? a.holders[el.getAttribute('data-boro')] : a.holders);
      var where = a.scope === 'boro' ? ' of ' + ({ '2': 'the Bronx' }[el.getAttribute('data-boro')] || BORON[el.getAttribute('data-boro')]) : '';
      h = '<div class="rh"><div class="rh-head"><span class="rh-t">Who has held this office: ' + esc(a.label + where) + '</span></div><div class="rh-g"><table class="rh-tbl"><thead><tr><th>Held by</th><th>From</th><th>To</th></tr></thead><tbody>' +
        (hs || []).slice().reverse().map(function (x) { var f = function (d) { return x.years ? d.slice(0, 4) : nice(d); }; return '<tr><td><b>' + esc(x.name) + '</b>' + (x.title && x.title !== a.label ? ' <small>' + esc(x.title) + '</small>' : '') + (x.note ? ' <small>' + esc(x.note) + '</small>' : '') + '</td><td><small>' + esc(f(x.from)) + '</small></td><td><small>' + (x.to ? esc(f(x.to)) : 'today') + '</small></td></tr>'; }).join('') +
        '</tbody></table></div><div class="rh-foot"><a class="rh-go" href="/electionhistory/">Every election since 2000, by election district and community board &rarr;</a></div></div>';
    }
    el.innerHTML = h;
  }

  function boot() {
    var bs = document.querySelectorAll('[data-rep-board],[data-rep-seat]');
    if (!bs.length) return;
    css();
    data().then(function () {
      Array.prototype.forEach.call(document.querySelectorAll('[data-rep-board]'), renderBoard);
      Array.prototype.forEach.call(document.querySelectorAll('[data-rep-seat]'), renderSeat);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
