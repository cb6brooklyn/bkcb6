/* The top of a Directory profile page: Mike's guide to what it does and why you may need to know it
   (profiles/glance.json, built by scripts/profile_glance.py). Loaded by site-bar.js on every page. */
(function () {
  var path = location.pathname.replace(/index\.html$/, '');
  if (document.getElementById('glance')) return;
  fetch('/profiles/glance.json', { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : {}; }).then(function (G) {
    var rows = G[path] || G[path + '/'] || G[path.replace(/\/$/, '')];
    if (!rows || document.getElementById('glance')) return;
    var esc = function (s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); };
    var st = document.createElement('style');
    st.textContent = '#glance{margin:14px 0 16px;border:2px solid #0d1b4b;border-left:8px solid #f47920;border-radius:12px;background:#fff;padding:12px 14px;font-family:"DM Sans",-apple-system,system-ui,sans-serif;box-shadow:0 3px 12px rgba(13,27,75,.12);text-align:left}'
      + '#glance .gr+.gr{margin-top:10px;padding-top:10px;border-top:1px solid #e5e2db}'
      + '#glance .gl{font-family:"DM Mono",ui-monospace,monospace;font-size:.68rem;letter-spacing:.09em;text-transform:uppercase;color:#c2410c;font-weight:500;margin-bottom:3px}'
      + '#glance .gv{font-size:1.02rem;line-height:1.45;font-weight:700;color:#0d1b4b}';
    document.head.appendChild(st);
    var box = document.createElement('div'); box.id = 'glance';
    box.innerHTML = rows.map(function (r) { return '<div class="gr"><div class="gl">' + esc(r[0]) + '</div><div class="gv">' + esc(r[1]) + '</div></div>'; }).join('');
    var a = document.querySelector('.phead') || document.querySelector('.cb-hero');
    if (a) { a.parentNode.insertBefore(box, a.nextSibling); return; }
    a = document.querySelector('header');
    if (a && a.parentNode) { a.parentNode.insertBefore(box, a.nextSibling); return; }
    var h = document.querySelector('h1');
    if (h) { var b = h.closest('header,section,div') || h; b.parentNode.insertBefore(box, b.nextSibling); }
  }).catch(function () {});
})();
