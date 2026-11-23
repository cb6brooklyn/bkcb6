/* link-logos.js: the logo of whatever a link opens, beside the link, on every page (loaded by site-bar.js).
   Pages: assets/link-logos/<first path part>.json (the Directory tile of that place, org, official or district, or the
   picture the site already shows for that page). Outside websites: assets/link-logos/_web.json (each listing's own site),
   else the website's own icon. Links that already show a picture are left alone. Written by tools/build_link_logos.py. */
(function () {
  'use strict';
  var SKIP = '#cb6bar,#cb6sv,#bk-credit,#cb6appnav,.leaflet-container,.mk-map-view,[data-nologo],svg';
  var cache = {}, ICON = '/app/data/civic/icons/';
  function get(name) {
    if (!cache[name]) cache[name] = fetch('/assets/link-logos/' + encodeURIComponent(name) + '.json').then(function (r) { return r.ok ? r.json() : {}; }).catch(function () { return {}; });
    return cache[name];
  }
  function norm(p) { p = p.split('#')[0].split('?')[0].replace(/\/index\.html$/, '/').replace(/\.html$/, '').replace(/\/+$/, ''); return p || '/'; }
  function shard(p) { var s = p.replace(/^\/+|\/+$/g, '').split('/'); return s.length > 1 ? s[0] : '_root'; }
  var GOV = /^(nyc\.gov|ny\.gov|council\.nyc\.gov|nysenate\.gov|assembly\.state\.ny\.us|nyassembly\.gov|house\.gov|senate\.gov|linktr\.ee|facebook\.com|instagram\.com|sites\.google\.com)$/;
  function webkey(u) {
    var host = u.hostname.toLowerCase().replace(/^www\./, ''), seg = u.pathname.toLowerCase().split('/').filter(Boolean);
    if (GOV.test(host)) return host + '/' + seg.slice(0, seg[0] === 'site' ? 2 : 1).join('/');
    return host;
  }
  function src(v) { return v.charAt(0) === '/' ? v : ICON + v; }
  function css() {
    if (document.getElementById('ll-css')) return;
    var s = document.createElement('style'); s.id = 'll-css';
    s.textContent = 'img.ll{width:1.25em;height:1.25em;object-fit:contain;border-radius:4px;vertical-align:-.28em;margin-right:.38em;background:#fff;box-shadow:0 0 0 1px rgba(13,27,75,.12);display:inline-block}';
    document.head.appendChild(s);
  }
  function put(a, url) {
    if (!url || a.querySelector('img.ll')) return;
    var i = document.createElement('img'); i.className = 'll'; i.alt = ''; i.loading = 'lazy'; i.decoding = 'async'; i.src = url;
    i.onerror = function () { i.remove(); };
    a.insertBefore(i, a.firstChild);
  }
  function run() {
    var as = document.querySelectorAll('a[href]'), need = {}, todo = [];
    for (var k = 0; k < as.length; k++) {
      var a = as[k];
      if (a.dataset.ll || a.querySelector('img,svg,picture,canvas') || a.closest(SKIP) || !a.textContent.trim()) continue;
      var h = a.getAttribute('href'); if (!h || /^(#|mailto:|tel:|javascript:|sms:)/i.test(h)) continue;
      var u; try { u = new URL(h, location.href); } catch (e) { continue; }
      a.dataset.ll = '1';
      if (u.origin === location.origin) { var p = norm(u.pathname); if (p === norm(location.pathname)) continue; todo.push([a, 'in', p]); need[shard(p)] = 1; }
      else if (/^https?:$/.test(u.protocol)) { todo.push([a, 'out', u]); need._web = 1; }
    }
    if (!todo.length) return;
    css();
    var names = Object.keys(need);
    Promise.all(names.map(get)).then(function (maps) {
      var M = {}; names.forEach(function (n, i) { M[n] = maps[i]; });
      todo.forEach(function (t) {
        if (t[1] === 'in') {
          var v = (M[shard(t[2])] || {})[t[2]];
          put(t[0], v ? src(v) : '/app/data/Logos/cb306.png');
        } else {
          var w = (M._web || {})[webkey(t[2])] || (M._web || {})[t[2].hostname.toLowerCase().replace(/^www\./, '')];
          put(t[0], w ? src(w) : 'https://icons.duckduckgo.com/ip3/' + t[2].hostname + '.ico');
        }
      });
    });
  }
  function start() { run(); setTimeout(run, 1500); setTimeout(run, 4000); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
