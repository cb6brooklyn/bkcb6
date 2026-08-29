/* Sports-Reference style navigation for profile pages.
   Adds a sticky "on this page" jump bar built from the page's own sections,
   and a peer strip so you can move sideways to any comparable official.
   Opt in with <body data-profile-ref="council:39"> or "bp:Brooklyn". */
(function () {
  'use strict';
  var NAVY = '#0d1b4b', ORANGE = '#f47920', BORDER = '#e5e2db';

  function esc(v) {
    return String(v == null ? '' : v).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function slugify(t) {
    return 'sec-' + t.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  }
  function style() {
    if (document.getElementById('pref-css')) return;
    var s = document.createElement('style');
    s.id = 'pref-css';
    s.textContent = [
      '.pref-jump{position:sticky;top:0;z-index:600;background:' + NAVY + ';',
      'border-bottom:2px solid ' + ORANGE + ';overflow-x:auto;-webkit-overflow-scrolling:touch}',
      '.pref-jump::-webkit-scrollbar{display:none}',
      '.pref-jump ul{display:flex;gap:0;margin:0;padding:0;list-style:none;white-space:nowrap}',
      '.pref-jump a{display:block;padding:9px 13px;font-family:"DM Mono",monospace;font-size:.68rem;',
      'text-transform:uppercase;letter-spacing:.06em;color:rgba(255,255,255,.72);text-decoration:none}',
      '.pref-jump a.on{color:#fff;font-weight:700;box-shadow:inset 0 -3px 0 ' + ORANGE + '}',
      '.pref-peers{border-top:1px solid ' + BORDER + ';padding:16px 18px 22px}',
      '.pref-peers h2{font-size:1rem;font-weight:900;color:' + NAVY + ';margin:0 0 3px}',
      '.pref-peers .sub{font-size:.8rem;color:#666;margin-bottom:10px}',
      '.pref-row{display:grid;grid-template-columns:repeat(auto-fill,minmax(104px,1fr));gap:7px}',
      '.pref-p{display:flex;flex-direction:column;align-items:center;gap:5px;text-align:center;',
      'text-decoration:none;border:1px solid ' + BORDER + ';border-radius:10px;padding:9px 6px;background:#fff}',
      '.pref-p:hover{border-color:' + ORANGE + '}',
      '.pref-p.self{border-color:' + NAVY + ';background:#f4f6fc}',
      '.pref-p img{width:34px;height:34px;object-fit:contain}',
      '.pref-p .n{font-size:.7rem;font-weight:800;color:' + NAVY + ';line-height:1.2}',
      '.pref-p .d{font-family:"DM Mono",monospace;font-size:.58rem;color:#888}',
      '.pref-more{margin-top:10px;font-family:"DM Mono",monospace;font-size:.68rem}',
      '.pref-more a{color:' + NAVY + ';border-bottom:2px solid ' + ORANGE + ';text-decoration:none}',
      '.pref-h2{margin-top:20px}',
      '.pref-find input{width:100%;padding:9px 11px;border:1px solid ' + BORDER + ';border-radius:9px;',
      'font-family:inherit;font-size:.85rem;background:#faf9f6;box-sizing:border-box}',
      '.pref-res{margin-top:9px}',
      '.pref-none{font-family:"DM Mono",monospace;font-size:.7rem;color:#888;padding:6px 0}'
    ].join('');
    document.head.appendChild(s);
  }

  function jumpBar() {
    var heads = Array.prototype.slice.call(document.querySelectorAll('.pwrap .sec > h2'));
    if (heads.length < 3) return;
    heads.forEach(function (h) { if (!h.parentNode.id) h.parentNode.id = slugify(h.textContent); });
    var nav = document.createElement('nav');
    nav.className = 'pref-jump';
    nav.innerHTML = '<ul>' + heads.map(function (h) {
      return '<li><a href="#' + h.parentNode.id + '">' + esc(h.textContent) + '</a></li>';
    }).join('') + '</ul>';
    var head = document.querySelector('.pwrap .phead');
    if (head && head.nextSibling) head.parentNode.insertBefore(nav, head.nextSibling);
    else document.querySelector('.pwrap').insertBefore(nav, document.querySelector('.pwrap').firstChild);

    var links = Array.prototype.slice.call(nav.querySelectorAll('a'));
    if (!window.IntersectionObserver) return;
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        links.forEach(function (a) {
          var on = a.getAttribute('href') === '#' + e.target.id;
          a.classList.toggle('on', on);
          if (on && a.scrollIntoView) {
            nav.scrollTo({ left: a.offsetLeft - 40, behavior: 'smooth' });
          }
        });
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    heads.forEach(function (h) { io.observe(h.parentNode); });
  }

  function peers(spec) {
    var bits = spec.split(':'), kind = bits[0], me = bits.slice(1).join(':');
    fetch('/data/officials-roster.json').then(function (r) { return r.json(); }).then(function (d) {
      var mine = (d[kind] || {})[me];
      var myBoros = mine ? (mine.boro || []) : (kind === 'boroughs' ? [me] : []);

      /* Who actually shares this ground, read off the page's own overlap
         section, so the list is the real neighbours and not a directory. */
      var rel = [], seen = {};
      function add(fam, key, why) {
        var set = d[fam]; if (!set || !set[key]) return;
        var id = fam + ':' + key;
        if (seen[id] || (fam === kind && String(key) === String(me))) return;
        seen[id] = 1;
        rel.push({ p: set[key], fam: fam, key: key, why: why });
      }
      /* The overlaps are stamped on the page from the election district data:
         every other district sharing an ED, with the count, and every board. */
      var stamp = document.querySelector('[data-profile-tiles]');
      var slugOf = {};
      ['council', 'assembly', 'senate'].forEach(function (fam) { Object.keys(d[fam] || {}).forEach(function (k) { slugOf['/' + d[fam][k].slug + '/'] = [fam, k]; }); });
      var extra = [];
      (stamp ? stamp.getAttribute('data-dists') || '' : '').split('|').filter(Boolean).forEach(function (x) {
        var p = x.split(';'), hit = slugOf[p[1]];
        if (hit) { add(hit[0], hit[1], p[3] + ' EDs'); }
        else extra.push({ name: p[2], sub: p[0] + ' \u00b7 ' + p[3] + ' EDs', href: p[1], icon: (p[0].indexOf('NY-') === 0 ? '/site-icons/congress/cd' + p[0].slice(3) + '.png' : '') });
      });
      if (!rel.length) Array.prototype.forEach.call(document.querySelectorAll('#overlaps a[href], #overlaps .ovcard'), function (el) {
        var h = el.getAttribute('href') || '';
        var m = h.match(/[?&]ad=(\d+)/); if (m) add('assembly', m[1], 'Assembly');
        m = h.match(/[?&]sd=(\d+)/); if (m) add('senate', m[1], 'Senate');
      });
      myBoros.forEach(function (b) { add('bp', b, 'Borough President'); });
      var BC = { 'Brooklyn': ['bk', '3'], 'Manhattan': ['mn', '1'], 'Bronx': ['bx', '2'], 'Queens': ['qn', '4'], 'Staten Island': ['si', '5'] };
      var boards = (stamp ? stamp.getAttribute('data-cbs') || '' : '').split('|').filter(Boolean).map(function (x) {
        var p = x.split(';'), bn = p[0].split(' CB'), bc = BC[bn[0]] || ['bk', '3'];
        return { name: p[0], sub: p[2] + ' EDs of this district', href: p[1], icon: '/site-icons/cb/' + bc[1] + ('0' + bn[1]).slice(-2) + '.png' };
      });

      /* A page with no overlap section still has direct peers: its own body. */
      if (!rel.length) {
        Object.keys(d[kind] || {}).forEach(function (k) { add(kind, k, ''); });
      }

      var wrap = document.createElement('div');
      wrap.className = 'sec pref-peers';
      wrap.id = 'sec-others';
      var famLabel = { council: 'District', assembly: 'AD', senate: 'SD', bp: '', boroughs: '' };

      var html = '';
      if (rel.length) {
        html += '<h2>' + (rel[0].fam === kind ? 'The other ' + d.labels[kind].toLowerCase() : 'Who else represents this ground') + '</h2>' +
          '<div class="sub">' + (rel[0].fam === kind ? 'Each has the same page.' : 'The other officials whose districts cross this one.') + '</div>' +
          '<div class="pref-row">' + rel.map(function (r) {
            var sub = (famLabel[r.fam] ? famLabel[r.fam] + ' ' + r.key : r.key) + (r.why && /EDs$/.test(r.why) ? ' \u00b7 ' + r.why : '');
            return '<a class="pref-p" href="/' + esc(r.p.slug) + '/">' +
              (r.p.icon ? '<img src="' + esc(r.p.icon) + '" alt="" loading="lazy">' : '') +
              '<span class="n">' + esc(r.p.name) + '</span>' +
              '<span class="d">' + esc(sub) + '</span></a>';
          }).join('') + extra.map(function (r) {
            return '<a class="pref-p" href="' + esc(r.href) + '">' + (r.icon ? '<img src="' + esc(r.icon) + '" alt="" loading="lazy">' : '') + '<span class="n">' + esc(r.name) + '</span><span class="d">' + esc(r.sub) + '</span></a>';
          }).join('') + '</div>';
      }
      if (boards.length) {
        html += '<h2 class="pref-h2">The community boards this district overlaps</h2><div class="sub">Each board has its own page, laid out the same way.</div><div class="pref-row">' + boards.map(function (r) {
          return '<a class="pref-p" href="' + esc(r.href) + '"><img src="' + esc(r.icon) + '" alt="" loading="lazy"><span class="n">' + esc(r.name) + '</span><span class="d">' + esc(r.sub) + '</span></a>';
        }).join('') + '</div>';
      }
      html += '<h2 class="pref-h2">Jump to any official</h2>' +
        '<div class="pref-find"><input type="search" placeholder="Name, district number, or borough" ' +
        'autocomplete="off" data-pq></div><div class="pref-res" data-pres></div>' +
        '<div class="pref-more"><a href="/electeds/">All elected officials</a> &middot; ' +
        '<a href="/govhub.html">The Government Hub</a> &middot; ' +
        '<a href="/directory">The Address Directory</a></div>';
      wrap.innerHTML = html;

      var all = [];
      ['council', 'assembly', 'senate', 'bp', 'boroughs'].forEach(function (fam) {
        Object.keys(d[fam] || {}).forEach(function (k) {
          var p = d[fam][k];
          all.push({
            fam: fam, key: k, p: p,
            sub: fam === 'boroughs' ? 'Borough' : (famLabel[fam] ? famLabel[fam] + ' ' + k : k),
            hay: (p.name + ' ' + k + ' ' + (p.boro || []).join(' ') + ' ' + fam).toLowerCase()
          });
        });
      });
      var qEl = wrap.querySelector('[data-pq]'), resEl = wrap.querySelector('[data-pres]');
      function run() {
        var q = (qEl.value || '').trim().toLowerCase();
        if (q.length < 2) { resEl.innerHTML = ''; return; }
        var hits = all.filter(function (x) { return x.hay.indexOf(q) > -1; }).slice(0, 12);
        resEl.innerHTML = hits.length ? '<div class="pref-row">' + hits.map(function (x) {
          var href = x.fam === 'boroughs' ? '/' + x.p.slug : '/' + x.p.slug + '/';
          return '<a class="pref-p" href="' + esc(href) + '">' +
            (x.p.icon ? '<img src="' + esc(x.p.icon) + '" alt="" loading="lazy">' : '') +
            '<span class="n">' + esc(x.p.name) + '</span>' +
            '<span class="d">' + esc(x.sub) + '</span></a>';
        }).join('') + '</div>' : '<div class="pref-none">Nothing matches that.</div>';
      }
      qEl.addEventListener('input', run);

      var foot = document.querySelector('.pwrap .pfoot');
      if (foot) foot.parentNode.insertBefore(wrap, foot);
      else document.querySelector('.pwrap').appendChild(wrap);
    }).catch(function () {});
  }

  function boot() {
    var spec = document.body.getAttribute('data-profile-ref');
    if (!spec || !document.querySelector('.pwrap')) return;
    style();
    jumpBar();
    peers(spec);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
