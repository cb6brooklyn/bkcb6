/* The charter org chart as a movie: pick any date from 1898 to today (or press play) and the chart redraws
   with who held each office, whether the Board of Estimate existed, what the legislature was called and how many seats it had.
   <div data-charter-movie></div>
   Names: data/districthistory/at-large.json (each holder's Wikipedia article). Legislature sizes: the sources listed in ERAS. */
(function () {
  var W = 'https://en.wikipedia.org/wiki/';
  var BORO = [['1', 'Manhattan'], ['2', 'The Bronx'], ['3', 'Brooklyn'], ['4', 'Queens'], ['5', 'Staten Island']];
  var BOEND = '1990-08-31';
  // the city's legislature, period by period. n = seats; null = the sources used do not give a number.
  var ERAS = [
    { from: '1898-01-01', to: '1901-12-31', name: 'Municipal Assembly', sub: 'Two houses: the Council (upper) and the Board of Aldermen (lower)', n: null,
      how: 'Council members from special districts (three each; two for Queens and Staten Island); aldermen one per Assembly district.',
      gap: 'The sources used do not give the size of either house.', src: [['Board of Aldermen', W + 'New_York_City_Board_of_Aldermen']] },
    { from: '1902-01-01', to: '1937-12-31', name: 'Board of Aldermen', sub: 'One house, one alderman per district', n: 73, later: 65,
      how: 'There were initially 73 districts; in later years this was reduced to 65.',
      gap: 'The year it went from 73 to 65 is not in the sources used, so the last 8 seats are shown striped.', src: [['Board of Aldermen', W + 'New_York_City_Board_of_Aldermen'], ['1937 Council election', W + '1937_New_York_City_Council_election']] },
    { from: '1938-01-01', to: '1939-12-31', name: 'City Council', sub: 'Proportional representation by borough, 75,000-vote quota', n: 26, boro: { '3': 9, '1': 6, '4': 5, '2': 5, '5': 1 },
      how: '26 members: Brooklyn 9, Manhattan 6, Queens 5, the Bronx 5 (Staten Island’s 1 is the remainder). The size changed with turnout.',
      src: [['1937 Council election', W + '1937_New_York_City_Council_election'], ['New York City Council', W + 'New_York_City_Council']] },
    { from: '1940-01-01', to: '1941-12-31', name: 'City Council', sub: 'Proportional representation by borough', n: 21,
      how: '21 members (the seats won in the 1939 election). Lower turnout shrank the Council from 26.', src: [['1939 Council election', W + '1939_New_York_City_Council_election']] },
    { from: '1942-01-01', to: '1943-12-31', name: 'City Council', sub: 'Proportional representation by borough', n: 26,
      how: '26 members after the 1941 election (“New City Council Has 26 Members, One a Communist,” The New York Times, Nov. 13, 1941).', src: [['Peter Cacchione', W + 'Peter_Cacchione']] },
    { from: '1944-01-01', to: '1945-12-31', name: 'City Council', sub: 'Proportional representation by borough', n: null,
      how: 'Elected in 1943.', gap: 'The sources used do not give the number elected in 1943; under proportional representation the Council ranged from 17 to 26 seats.',
      src: [['The Tally Room', 'https://www.tallyroom.com.au/39419']] },
    { from: '1946-01-01', to: '1949-12-31', name: 'City Council', sub: 'Proportional representation by borough; first four-year term', n: 23,
      how: '23 members (the seats won in the 1945 election). The term was extended to four years in 1945.', src: [['1945 Council election', W + '1945_New_York_City_Council_election'], ['New York City Council', W + 'New_York_City_Council']] },
    { from: '1950-01-01', to: '1963-12-31', name: 'City Council', sub: 'One member per State Senate district', n: 25,
      how: 'Proportional representation was abolished in 1947. In 1949 Democrats won 24 of the 25 seats.', src: [['FairVote', 'https://fairvote.org/wp-content/uploads/2024/03/Proportional-Representation-in-NYC.pdf'], ['New York City Council', W + 'New_York_City_Council']] },
    { from: '1964-01-01', to: '1983-06-30', name: 'City Council', sub: 'District members plus two elected borough-wide in each borough', n: 35, atl: 10,
      how: 'The 1963 charter revision raised the Council from 25 to 35, adding two at-large members from each borough (10).', src: [['New York City Charter', W + 'New_York_City_Charter'], ['New York City Council', W + 'New_York_City_Council']] },
    { from: '1983-07-01', to: '1991-12-31', name: 'City Council', sub: 'At-large seats struck down, June 1983', n: 35,
      how: 'A federal court ruled in June 1983 that the 10 at-large seats violated one person, one vote. The Council had 35 members when the Board of Estimate fell in 1989.',
      gap: 'The sources used do not say how the 35 seats were split after June 1983.', src: [['New York City Council', W + 'New_York_City_Council'], ['Maximum New York', 'https://www.maximumnewyork.com/p/1989-new-york-citys-new-government']] },
    { from: '1992-01-01', to: '9999-12-31', name: 'City Council', sub: '51 districts', n: 51,
      how: 'The 1989 charter raised the Council from 35 to 51 and gave it most of the Board of Estimate’s powers. Members of the new districts took office January 1, 1992 (Una Clarke, 40th district).',
      src: [['New York City Council', W + 'New_York_City_Council'], ['Una Clarke', W + 'Una_S._T._Clarke']] }
  ];
  // the changes the movie stops on
  var EVENTS = [
    ['1898-01-01', 'Greater New York consolidated: five boroughs, five Borough Presidents, a two-house Municipal Assembly and a Board of Estimate and Apportionment.'],
    ['1951-01-01', 'The Manhattan Borough President names 12 Community Planning Councils, the city\u2019s first community boards.', '1951'],
    ['1901-01-01', 'The Board of Estimate becomes eight members: Mayor, Comptroller and Council President with 3 votes each; Manhattan and Brooklyn BPs 2; Bronx, Queens and Richmond BPs 1.'],
    ['1902-01-01', 'The Municipal Assembly’s Council is removed. The Board of Aldermen becomes the only house, and its President is elected citywide.'],
    ['1938-01-01', 'The 1938 charter replaces the Board of Aldermen with the City Council, elected by proportional representation.'],
    ['1940-01-01', 'Turnout drops: the Council shrinks from 26 to 21 seats.'],
    ['1942-01-01', 'The Council is back to 26 seats.'],
    ['1946-01-01', 'Council terms go to four years.'],
    ['1950-01-01', 'Proportional representation is gone: 25 members, one per State Senate district.'],
    ['1957-01-01', 'The Board of Estimate goes to 22 votes: 4 for each citywide official, 2 for each Borough President.'],
    ['1963-01-01', 'The 1961 charter takes effect: community planning boards for every district. The Bronx (14) and Brooklyn (7) get interim boards in 1963, Queens (13) and Richmond (4) in 1966.', '1963'],
    ['1964-01-01', 'The Council grows from 25 to 35: 10 seats elected borough-wide, two per borough.'],
    ['1975-01-01', 'Richmond is renamed Staten Island.'],
    ['1968-03-01', 'The City Planning Commission adopts the first official community district map: 62 Community Planning Districts.'],
    ['1975-01-01', 'The charter revision creates today\u2019s 59 community districts and community boards.', '1975'],
    ['1983-07-01', 'A federal court strikes down the 10 at-large seats (June 1983).'],
    ['1989-03-22', 'The U.S. Supreme Court rules the Board of Estimate unconstitutional (Board of Estimate v. Morris).'],
    ['1990-09-01', 'The Board of Estimate is dissolved (August 31, 1990). Borough Presidents lose their votes on the budget and land use.'],
    ['1992-01-01', 'The Council grows from 35 to 51 seats.'],
    ['1994-01-01', 'The President of the City Council is renamed Public Advocate.'],
    ['2002-01-01', 'A charter change makes the Speaker, not the Public Advocate, the Council’s presiding officer.']
  ];
  EVENTS.sort(function (a, b) { return a[0] < b[0] ? -1 : 1; });
  function evLab(e) { return e[2] || nice(e[0]); }
  // community boards on a date: CPC, Community Planning Districts (March 1968); NYC Community Boards history (1975)
  function boards(dt) {
    if (dt < '1951-01-01') return 'Community boards: none yet.';
    if (dt < '1963-01-01') return 'Community boards: 12 Community Planning Councils in Manhattan only.';
    if (dt < '1966-01-01') return 'Community boards: interim boards named by Borough Presidents (Manhattan 12, the Bronx 14, Brooklyn 7).';
    if (dt < '1968-03-01') return 'Community boards: interim boards named by Borough Presidents (Manhattan 12, the Bronx 14, Brooklyn 7, Queens 13, Richmond 4).';
    if (dt < '1975-01-01') return 'Community boards: 62 Community Planning Districts on the official map adopted March 1, 1968; Borough Presidents appoint the boards.';
    return 'Community boards: 59, one for each community district.';
  }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (m) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m]; }); }
  var M = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function nice(d) { var p = d.split('-'); return M[+p[1] - 1] + ' ' + (+p[2]) + ', ' + p[0]; }
  function today() { var t = new Date(); return t.getFullYear() + '-' + ('0' + (t.getMonth() + 1)).slice(-2) + '-' + ('0' + t.getDate()).slice(-2); }
  function pick(hs, dt) { var h = null; (hs || []).forEach(function (x) { if (x.from <= dt) h = x; }); if (!h || (h.to && dt > h.to)) return null; return h; }
  function labelOn(o, dt) { var l = o.label; (o.labels || []).forEach(function (x) { if (x[0] <= dt) l = x[1]; }); return l; }
  // dates <-> month index for the slider
  var START = 1898 * 12;
  function toIdx(d) { var p = d.split('-'); return (+p[0]) * 12 + (+p[1] - 1) - START; }
  function toDate(i) { var y = Math.floor((i + START) / 12), m = (i + START) % 12 + 1; return y + '-' + ('0' + m).slice(-2) + '-01'; }

  function css() {
    if (document.getElementById('cm-css')) return;
    var s = document.createElement('style'); s.id = 'cm-css';
    s.textContent = '.cm{border:2px solid #0d1b4b;border-radius:12px;overflow:hidden;background:#fff;font-family:"DM Sans",sans-serif;color:#1a1a1a;margin:0 0 14px}' +
      '.cm-top{background:#0d1b4b;color:#fff;padding:12px 14px}.cm-h{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:8px}' +
      '.cm-t{font-weight:800;font-size:1rem}.cm-date{font-family:"DM Mono",monospace;font-size:1.5rem;font-weight:700;color:#f47920}' +
      '.cm-ctl{display:flex;gap:8px;align-items:center;margin-top:10px;flex-wrap:wrap}.cm-ctl button{font:700 .8rem "DM Sans",sans-serif;border:0;border-radius:6px;padding:7px 12px;background:#f47920;color:#fff;cursor:pointer}' +
      '.cm-ctl button.g{background:rgba(255,255,255,.15)}.cm-ctl input[type=date]{font-family:"DM Mono",monospace;font-size:.8rem;padding:6px;border-radius:6px;border:0}' +
      '.cm-ctl select{font-size:.8rem;padding:6px;border-radius:6px;border:0}.cm-rng{width:100%;margin-top:10px;accent-color:#f47920}' +
      '.cm-tl{position:relative;height:16px;margin:2px 7px 0}.cm-tl b{position:absolute;top:2px;width:3px;height:12px;background:#f47920;border-radius:2px;cursor:pointer;transform:translateX(-1px)}.cm-tl b.on{background:#fff}' +
      '.cm-yrs{display:flex;justify-content:space-between;font-family:"DM Mono",monospace;font-size:.6rem;opacity:.7;margin:2px 4px 0}' +
      '.cm-ev{background:#fff7f0;border-bottom:1px solid #f3dcc7;padding:10px 14px;font-size:.84rem;min-height:2.6em;transition:background .4s}.cm-ev.flash{background:#ffe2c6}.cm-ev small{font-family:"DM Mono",monospace;color:#b45309;font-size:.66rem;display:block;text-transform:uppercase;letter-spacing:.06em}' +
      '.cm-b{padding:12px 14px}.cm-people{border:2px solid #0d1b4b;border-radius:10px;text-align:center;padding:8px;font-weight:700;font-size:.82rem;color:#0d1b4b}' +
      '.cm-arrow{text-align:center;color:#9ca3af;font-size:.9rem;line-height:1.1;margin:3px 0}' +
      '.cm-row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.cm-row5{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:6px}' +
      '.cm-c{border:1.5px solid #e5e2db;border-left:4px solid #0d1b4b;border-radius:8px;padding:8px;background:#fff;transition:all .35s}.cm-c .o{font-family:"DM Mono",monospace;font-size:.6rem;text-transform:uppercase;letter-spacing:.06em;color:#6b6b6b}' +
      '.cm-c .n{font-weight:700;color:#0d1b4b;font-size:.86rem;margin-top:2px}.cm-c .s{font-size:.7rem;color:#6b6b6b;margin-top:2px}.cm-c.chg{box-shadow:0 0 0 3px #f4792066}' +
      '.cm-boe{border:2px dashed #b45309;border-radius:10px;padding:10px;margin-top:8px;background:#fffbeb;transition:opacity .5s,max-height .6s;overflow:hidden}.cm-boe.off{opacity:.45;background:#f8f7f4;border-color:#c9c5bd}' +
      '.cm-boe h4,.cm-leg h4,.cm-bps h4{margin:0 0 6px;font-size:.86rem;color:#0d1b4b}.cm-boe h4 span,.cm-leg h4 span{font-weight:400;color:#6b6b6b;font-size:.74rem}' +
      '.cm-vote{display:grid;grid-template-columns:minmax(0,1fr) 120px;gap:6px;align-items:center;font-size:.76rem;padding:2px 0}.cm-vote i{display:inline-block;width:12px;height:12px;border-radius:3px;background:#b45309;margin-right:2px;transition:all .3s}' +
      '.cm-leg{border:2px solid #0d7490;border-radius:10px;padding:10px;margin-top:8px;background:#f0f9ff}.cm-leg .sub{font-size:.74rem;color:#0d7490;margin-bottom:6px}' +
      '.cm-dots{display:flex;flex-wrap:wrap;gap:4px;margin:6px 0;min-height:16px}.cm-dot{width:13px;height:13px;border-radius:50%;background:#0d7490;transition:transform .45s,opacity .45s,background .45s}.cm-dot.off{transform:scale(0);opacity:0;width:0;margin-right:-4px}' +
      '.cm-dot.atl{background:#f47920}.cm-dot.str{background:repeating-linear-gradient(45deg,#0d7490 0 2px,#bae6fd 2px 4px)}.cm-dot.unk{background:#e5e2db}' +
      '.cm-count{font-family:"DM Mono",monospace;font-size:1.6rem;font-weight:700;color:#0d7490;transition:color .3s}.cm-leg .how{font-size:.78rem;line-height:1.45}.cm-gap{font-size:.74rem;color:#92400e;margin-top:4px}' +
      '.cm-bylist{display:flex;flex-wrap:wrap;gap:10px;font-size:.72rem;color:#0d7490;margin-top:2px}' +
      '.cm-bps{margin-top:8px}.cm-bps .cm-c{border-left-color:#6b21a8}.cm-role{font-size:.74rem;color:#4b5563;margin-top:6px;line-height:1.45}' +
      '.cm-fold>summary{cursor:pointer;font-weight:800;color:#0d1b4b;padding:10px 14px;font-size:.9rem;border-bottom:1px solid #e5e2db;background:#f8f7f4}' +
      '.cm-bar{position:sticky;top:0;z-index:1000}.cm-bar .cm-top{border-radius:0 0 10px 10px;box-shadow:0 6px 18px rgba(13,27,75,.18)}' +
      '.cm-src{font-size:.7rem;color:#6b6b6b;padding:0 14px 12px}.cm-src a{color:#0d1b4b}' +
      '@media(max-width:620px){.cm-row{grid-template-columns:1fr}.cm-row5{grid-template-columns:repeat(2,minmax(0,1fr))}.cm-vote{grid-template-columns:minmax(0,1fr) 90px}}';
    document.head.appendChild(s);
  }

  function mount(el, AL) {
    css();
    var O = {}; AL.offices.forEach(function (o) { O[o.key] = o; });
    var max = toIdx(today()), evIdx = EVENTS.map(function (e) { return toIdx(e[0]); });
    el.innerHTML = '<div class="cm"><div class="cm-top"><div class="cm-h"><span class="cm-t">The charter org chart through time</span><span class="cm-date"></span></div>' +
      '<div class="cm-ctl"><button class="cm-play">▶ Play</button><button class="g cm-prev">⏮ Prev change</button><button class="g cm-next">Next change ⏭</button>' +
      '<select class="cm-spd" aria-label="Speed"><option value="6">Slow</option><option value="18" selected>Normal</option><option value="60">Fast</option></select>' +
      '<input type="date" class="cm-in" min="1898-01-01" aria-label="Date"><button class="g cm-now">Today</button></div>' +
      '<input type="range" class="cm-rng" min="0" max="' + max + '" step="1" aria-label="Date slider"><div class="cm-tl">' +
      evIdx.map(function (x, i) { return '<b data-i="' + i + '" style="left:' + (x / max * 100).toFixed(2) + '%" title="' + esc(evLab(EVENTS[i]) + ': ' + EVENTS[i][1]) + '"></b>'; }).join('') +
      '</div><div class="cm-yrs"><span>1898</span><span>1938</span><span>1964</span><span>1990</span><span>' + today().slice(0, 4) + '</span></div></div>' +
      (el.hasAttribute('data-cm-fold') ? '<details class="cm-fold" open><summary>The org chart on this date</summary>' : '') +
      '<div class="cm-ev"></div><div class="cm-b"></div><div class="cm-src"></div>' + (el.hasAttribute('data-cm-fold') ? '</details>' : '') + '</div>';
    var bar = el.getAttribute('data-cm-bar') && document.querySelector(el.getAttribute('data-cm-bar'));
    var top = el.querySelector('.cm-top');
    if (bar) { bar.classList.add('cm-bar'); bar.appendChild(top); }
    var q = function (c) { return el.querySelector(c) || top.querySelector(c); };
    var rng = q('.cm-rng'), inp = q('.cm-in'), body = q('.cm-b'), ev = q('.cm-ev'), timer = null, lastEv = -1, prev = {};
    inp.max = today();
    // fixed skeleton so changes animate in place
    body.innerHTML = '<div class="cm-people">The People of the City of New York</div><div class="cm-arrow">▼ elect ▼</div>' +
      '<div class="cm-row"><div class="cm-c" data-k="mayor"></div><div class="cm-c" data-k="comptroller"></div><div class="cm-c" data-k="pa"></div></div>' +
      '<div class="cm-boe"></div><div class="cm-leg"><h4></h4><div class="sub"></div><div style="display:flex;align-items:center;gap:10px"><span class="cm-count"></span><div class="cm-dots">' +
      Array.apply(null, Array(73)).map(function () { return '<span class="cm-dot off"></span>'; }).join('') + '</div></div><div class="cm-bylist"></div><div class="how"></div><div class="cm-gap"></div><div class="cm-pres cm-role"></div></div>' +
      '<div class="cm-bps"><h4>Borough Presidents</h4><div class="cm-row5">' + BORO.map(function (b) { return '<div class="cm-c" data-b="' + b[0] + '"></div>'; }).join('') + '</div><div class="cm-role"></div><div class="cm-role cm-cbs"></div></div>';
    var dots = [].slice.call(el.querySelectorAll('.cm-dot'));
    function card(node, office, name, sub, key) {
      var html = '<div class="o">' + esc(office) + '</div><div class="n">' + esc(name || 'Vacant') + '</div>' + (sub ? '<div class="s">' + esc(sub) + '</div>' : '');
      if (node.innerHTML !== html) { node.innerHTML = html; if (prev[key] !== undefined) { node.classList.add('chg'); setTimeout(function () { node.classList.remove('chg'); }, 900); } prev[key] = 1; }
    }
    function who(o, hs, dt) { var x = pick(hs, dt); return x ? x.name + (x.note ? ' (' + x.note + ')' : '') : null; }
    function since(o, hs, dt) { var x = pick(hs, dt); return x ? (x.years ? 'since ' + x.from.slice(0, 4) : 'since ' + nice(x.from)) : ''; }
    function render(dt) {
      q('.cm-date').textContent = nice(dt);
      inp.value = dt; rng.value = toIdx(dt);
      // citywide officials
      card(q('[data-k=mayor]'), 'Mayor', who(O.mayor, O.mayor.holders, dt), since(O.mayor, O.mayor.holders, dt), 'mayor');
      card(q('[data-k=comptroller]'), 'Comptroller', who(O.comptroller, O.comptroller.holders, dt), since(O.comptroller, O.comptroller.holders, dt), 'comptroller');
      card(q('[data-k=pa]'), labelOn(O.pa, dt), who(O.pa, O.pa.holders, dt), since(O.pa, O.pa.holders, dt), 'pa');
      // Board of Estimate
      var boe = q('.cm-boe');
      if (dt <= BOEND) {
        boe.classList.remove('off');
        var votes = dt < '1901-01-01' ? null : dt < '1957-01-01' ? [3, { '1': 2, '3': 2, '2': 1, '4': 1, '5': 1 }] : [4, { '1': 2, '2': 2, '3': 2, '4': 2, '5': 2 }];
        var row = function (lab, n) { return '<div class="cm-vote"><span>' + esc(lab) + '</span><span>' + (n ? Array.apply(null, Array(n)).map(function () { return '<i></i>'; }).join('') + ' <small>' + n + '</small>' : '') + '</span></div>'; };
        var h = '<h4>Board of Estimate <span>' + (votes ? (votes[0] * 3 + [1, 2, 3, 4, 5].reduce(function (a, b) { return a + votes[1][b]; }, 0)) + ' votes · budget, land use, contracts, franchises' : 'Board of Estimate and Apportionment, 1898–1900') + '</span></h4>';
        if (!votes) h += '<div class="cm-role">From 1898 to 1900 a five-member board; the eight-member board with weighted votes starts in 1901.</div>';
        else {
          h += row('Mayor ' + (who(O.mayor, O.mayor.holders, dt) || 'vacant'), votes[0]) + row('Comptroller ' + (who(O.comptroller, O.comptroller.holders, dt) || 'vacant'), votes[0]) + row(labelOn(O.pa, dt) + ' ' + (who(O.pa, O.pa.holders, dt) || 'vacant'), votes[0]);
          BORO.forEach(function (b) { h += row((b[0] === '5' && dt < '1975-01-01' ? 'Richmond' : b[1]) + ' BP ' + (who(O.bp, O.bp.holders[b[0]], dt) || 'vacant'), votes[1][b[0]]); });
        }
        boe.innerHTML = h;
      } else {
        boe.classList.add('off');
        boe.innerHTML = '<h4>Board of Estimate <span>abolished</span></h4><div class="cm-role">Dissolved August 31, 1990, after the Supreme Court ruled it unconstitutional in 1989. Its budget and land-use powers went to the City Council and the Mayor.</div>';
      }
      // legislature
      var E = ERAS.filter(function (e) { return e.from <= dt && dt <= e.to; })[0];
      q('.cm-leg h4').innerHTML = esc(E.name) + ' <span>' + esc(nice(E.from)) + (E.to < '9999' ? ' – ' + esc(nice(E.to)) : ' – today') + '</span>';
      q('.cm-leg .sub').textContent = E.sub;
      q('.cm-count').textContent = E.n == null ? '?' : E.n;
      dots.forEach(function (d, i) {
        var on = E.n == null ? i < 17 : i < E.n;
        d.className = 'cm-dot' + (on ? '' : ' off') + (E.n == null && on ? ' unk' : '') + (E.later && i >= E.later && on ? ' str' : '') + (E.atl && on && i >= E.n - E.atl ? ' atl' : '');
      });
      q('.cm-bylist').innerHTML = E.boro ? BORO.map(function (b) { return b[1] + ' ' + E.boro[b[0]]; }).join(' · ') : E.atl ? '<span style="color:#0d7490">● district</span> <span style="color:#f47920">● elected borough-wide</span>' : '';
      q('.cm-leg .how').textContent = E.how;
      q('.cm-gap').textContent = E.gap || '';
      var spk = pick(O.speaker.holders, dt);
      q('.cm-pres').textContent = dt < '2002-01-01' ? 'Presiding officer: the ' + labelOn(O.pa, dt) + (spk ? '. Council leader: ' + spk.name + ' (Speaker' + (spk.years ? ' from ' + spk.from.slice(0, 4) : '') + ')' : '') + '.' :
        'Presiding officer: Speaker ' + (spk ? spk.name : '(vacant)') + ', elected by the members.';
      // borough presidents
      BORO.forEach(function (b) { card(q('[data-b="' + b[0] + '"]'), (b[0] === '5' && dt < '1975-01-01' ? 'Richmond' : b[1]), who(O.bp, O.bp.holders[b[0]], dt), since(O.bp, O.bp.holders[b[0]], dt), 'bp' + b[0]); });
      q('.cm-cbs').textContent = boards(dt);
      q('.cm-bps .cm-role').textContent = dt <= BOEND ? 'Then: each Borough President ran much of the borough’s government and voted on the Board of Estimate.' :
        'Now: Borough Presidents appoint community board members, advise on land use (ULURP) and the budget, and advocate for their borough. No Board of Estimate vote.';
      // the latest change
      var k = -1; EVENTS.forEach(function (e, i) { if (e[0] <= dt) k = i; });
      if (k !== lastEv) { ev.innerHTML = k < 0 ? '' : '<small>' + esc(evLab(EVENTS[k])) + '</small>' + esc(EVENTS[k][1]); ev.classList.add('flash'); setTimeout(function () { ev.classList.remove('flash'); }, 500); lastEv = k; }
      [].forEach.call(top.querySelectorAll('.cm-tl b'), function (b) { b.classList.toggle('on', +b.dataset.i === k); });
      q('.cm-src').innerHTML = 'Legislature sources: ' + E.src.map(function (s) { return '<a href="' + s[1] + '" target="_blank" rel="noopener">' + esc(s[0]) + '</a>'; }).join(', ') +
        '. Officeholders: each person’s Wikipedia article (<a href="/electionhistory/">Election history</a>).';
      el.cmDate = dt;
      try { el.dispatchEvent(new CustomEvent('cmdate', { detail: dt })); } catch (e) {}
    }
    el.cmGo = function (dt) { stop(); render(dt > today() ? today() : dt < '1898-01-01' ? '1898-01-01' : dt); };
    function go(i) { i = Math.max(0, Math.min(max, i)); render(i === max ? today() : toDate(i)); }
    function stop() { if (timer) { clearInterval(timer); timer = null; } q('.cm-play').textContent = '▶ Play'; }
    function play() {
      if (timer) return stop();
      if (+rng.value >= max) go(0);
      q('.cm-play').textContent = '⏸ Pause';
      var hold = 0;
      timer = setInterval(function () {
        if (hold > 0) { hold--; return; }
        var i = +rng.value + 1;
        if (i > max) return stop();
        if (evIdx.indexOf(i) >= 0) hold = 12; // linger on each change
        go(i);
      }, 1000 / +q('.cm-spd').value);
    }
    q('.cm-play').onclick = play;
    q('.cm-spd').onchange = function () { if (timer) { stop(); play(); } };
    rng.oninput = function () { stop(); go(+rng.value); };
    inp.onchange = function () { if (/^\d{4}-\d\d-\d\d$/.test(inp.value) && inp.value >= '1898-01-01') { stop(); render(inp.value > today() ? today() : inp.value); } };
    q('.cm-now').onclick = function () { stop(); render(today()); };
    q('.cm-next').onclick = function () { stop(); var c = +rng.value, n = evIdx.filter(function (x) { return x > c; })[0]; if (n != null) render(EVENTS[evIdx.indexOf(n)][0]); };
    q('.cm-prev').onclick = function () { stop(); var c = +rng.value, p = evIdx.filter(function (x) { return x < c; }).pop(); if (p != null) render(EVENTS[evIdx.indexOf(p)][0]); };
    [].forEach.call(top.querySelectorAll('.cm-tl b'), function (b) { b.onclick = function () { stop(); render(EVENTS[+b.dataset.i][0]); }; });
    var m = /[?&#](?:date|on)=(\d{4}-\d\d-\d\d)/.exec(location.href);
    var st = el.getAttribute('data-cm-start') === 'today' ? today() : '1898-01-01';
    render(m ? (m[1] > today() ? today() : m[1] < '1898-01-01' ? '1898-01-01' : m[1]) : st);
  }
  function boot() {
    var els = document.querySelectorAll('[data-charter-movie]'); if (!els.length) return;
    var p = window.CHARTER_AL ? Promise.resolve(window.CHARTER_AL) : fetch('/data/districthistory/at-large.json').then(function (r) { return r.json(); });
    p.then(function (AL) { [].forEach.call(els, function (el) { mount(el, AL); }); }).catch(function () { [].forEach.call(els, function (el) { el.textContent = 'The timeline could not load.'; }); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
