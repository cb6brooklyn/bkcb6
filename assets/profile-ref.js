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
      '.pref-more a{color:' + NAVY + ';border-bottom:2px solid ' + ORANGE + ';text-decoration:none}'
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
      var set = d[kind]; if (!set) return;
      var keys = Object.keys(set);
      if (kind === 'council') keys.sort(function (a, b) { return (+a) - (+b); });
      var wrap = document.createElement('div');
      wrap.className = 'sec pref-peers';
      wrap.id = 'sec-others';
      var title = kind === 'council' ? 'The other 50 council members' : 'The other borough presidents';
      var sub = kind === 'council'
        ? 'Every district, in order. Each one has the same page.'
        : 'Each borough, with the same page.';
      wrap.innerHTML = '<h2>' + title + '</h2><div class="sub">' + sub + '</div>' +
        '<div class="pref-row">' + keys.map(function (k) {
          var p = set[k], self = String(k) === String(me);
          return '<a class="pref-p' + (self ? ' self' : '') + '" href="/' + esc(p.slug) + '/">' +
            (p.icon ? '<img src="' + esc(p.icon) + '" alt="" loading="lazy">' : '') +
            '<span class="n">' + esc(p.name) + '</span>' +
            '<span class="d">' + esc(kind === 'council' ? 'District ' + k : k) + '</span></a>';
        }).join('') + '</div>' +
        '<div class="pref-more"><a href="/govhub.html">The Government Hub</a> &middot; ' +
        '<a href="/directory">The Address Directory</a></div>';
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
