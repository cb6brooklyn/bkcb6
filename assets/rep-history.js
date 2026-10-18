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
      '@media(max-width:560px){.rh-r{grid-template-columns:1fr;gap:2px}}';
    document.head.appendChild(s);
  }
  function pick(hs, dt) { var h = null; (hs || []).forEach(function (x) { if (x.from <= dt) h = x; }); if (!h || (h.to && dt > h.to)) return null; return h; }
  function stateHolders(row, ms) {
    return ms.map(function (m) { return { name: m.name, from: m.type === 'special' ? m.elected : row.served.slice(0, 4) + '-01-01', special: m.type === 'special' ? m.elected : null }; });
  }

  // ---- a board on a date ----
  function renderBoard(el) {
    var cb = String(el.getAttribute('data-rep-board')), c = code(cb), y0 = '2000-01-01';
    el.innerHTML = '<div class="rh"><div class="rh-head"><span class="rh-t"></span><span class="rh-ctl"><input type="date" min="' + y0 + '" max="' + today() + '" value="' + today() + '"><button type="button">Today</button></span></div><div class="rh-body"></div>' +
      '<div class="rh-foot"><a class="rh-go" href="/electionhistory/?cb=' + cb + '">Every election since 2000 in ' + esc(c) + ', by election district &rarr;</a></div></div>';
    var inp = el.querySelector('input'), body = el.querySelector('.rh-body'), ttl = el.querySelector('.rh-t');
    function draw() {
      var dt = inp.value || today(), y = +dt.slice(0, 4);
      ttl.textContent = 'Who represented ' + c + ' on ' + nice(dt);
      var h = '<div class="rh-g"><div class="rh-gh">Districts covering ' + esc(c) + ' (share of the board’s residents)</div>';
      OV.offices.forEach(function (o) {
        var r = o.rows.filter(function (x) { return +x.served.slice(0, 4) <= y && y <= +x.served.slice(-4); })[0], cell;
        if (!r) cell = '<span style="color:#6b6b6b">Not in this record before ' + o.rows[0].served.slice(0, 4) + '</span>';
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
      var grp = { boro: BORON[cb[0]], city: 'New York City', state: 'New York State', us: 'United States' }, last = null;
      AL.offices.forEach(function (o) {
        if (o.scope !== last) { h += (last ? '</div>' : '') + '<div class="rh-g"><div class="rh-gh">' + esc(grp[o.scope]) + '</div>'; last = o.scope; }
        var lists = o.seats ? o.seats : [o.scope === 'boro' ? o.holders[cb[0]] : o.holders];
        h += '<div class="rh-r"><span class="rh-o">' + esc(o.label) + '</span><span class="rh-n">' + lists.map(function (hs) {
          var x = pick(hs, dt); return '<div>' + (x ? '<b>' + esc(x.name) + '</b><small>since ' + esc(nice(x.from)) + '</small>' : '<span style="color:#6b6b6b">Vacant</span>') + '</div>';
        }).join('') + '</span></div>';
      });
      body.innerHTML = h + '</div>';
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
        (hs || []).slice().reverse().map(function (x) { return '<tr><td><b>' + esc(x.name) + '</b></td><td><small>' + esc(nice(x.from)) + '</small></td><td><small>' + (x.to ? esc(nice(x.to)) : 'today') + '</small></td></tr>'; }).join('') +
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
