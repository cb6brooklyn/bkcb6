/* Every profile opens on a grid of tiles, one per section, so the whole page
   is visible at a glance; sections stay folded until their tile is tapped.
   A search box matches section titles and their text. Colors come from the
   borough's seal. Reads <div data-profile-tiles data-boro=".." data-elections=".."
   data-parks=".." data-zoning=".."> and builds around it. */
(function () {
  var PAL = { 'New York City': ['#0d1b4b', '#f47920'], 'Brooklyn': ['#003060', '#f2c94c'], 'Manhattan': ['#0c549c', '#0c306c'], 'Bronx': ['#3054a8', '#f06c0c'], 'Queens': ['#8a7440', '#b85040'], 'Staten Island': ['#486c60', '#a6c4b8'] };
  function esc(v) { return String(v == null ? '' : v).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }
  function css(c0, c1) {
    if (document.getElementById('ptiles-css')) return;
    var s = document.createElement('style'); s.id = 'ptiles-css';
    s.textContent = '.ptiles{padding:12px 14px 4px}.ptiles .ps{display:flex;gap:6px}.ptiles .ps input{flex:1;min-width:0;font:inherit;font-size:.9rem;padding:11px 12px;border:1.5px solid #e5e2db;border-radius:9px;background:#fff;color:#0d1b4b}' +
      '.ptiles .pg{display:grid;grid-template-columns:repeat(auto-fill,minmax(112px,1fr));gap:7px;margin-top:10px}' +
      '.ptile{aspect-ratio:1/1;display:flex;flex-direction:column;justify-content:space-between;text-align:left;font:inherit;cursor:pointer;border:1.5px solid #e5e2db;border-top:4px solid ' + c1 + ';border-radius:11px;background:#fff;padding:9px 9px 8px;color:#0d1b4b;text-decoration:none;min-width:0;overflow:hidden;transition:transform .1s}' +
      '.ptile:active{transform:scale(.98)}.ptile.hide{display:none}.ptile .t{font-size:.76rem;font-weight:900;line-height:1.15;color:' + c0 + ';display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}.ptile .d{font-size:.64rem;color:#6b6760;line-height:1.3;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}' +
      '.ptile.go{background:' + c0 + ';border-color:' + c0 + '}.ptile.go .t{color:#fff}.ptile.go .d{color:rgba(255,255,255,.75)}.ptile .k{font-family:"DM Mono",monospace;font-size:.5rem;letter-spacing:.09em;text-transform:uppercase;color:#6b6760}.ptile.go .k{color:' + c1 + '}' +
      '.ptile.cb{border-top-color:' + c0 + ';background:#f4f6fb}.ptile.cb .k{color:' + c0 + '}' +
      '.ptile.art{grid-column:span 2;aspect-ratio:auto;padding:0;background:#fff;border-color:#e5e2db;border-top-color:' + c1 + ';overflow:hidden}' +
      '.ptile.art .ai{display:block;width:100%;aspect-ratio:1/1;overflow:hidden;background:#f4f2ec}.ptile.art .ai img{width:100%;height:100%;object-fit:cover;display:block}' +
      '.ptile.art .al{display:block;padding:9px 11px 10px}.ptile.art .t{font-size:.8rem;color:' + c0 + '}.ptile.art .d{color:#6b6760;margin-top:3px}' +
      '.ptiles .pn{font-size:.76rem;color:#6b6760;margin-top:6px;min-height:1em}' +
      '.pbrief{padding:14px 18px 2px;font-size:.92rem;line-height:1.6;color:#1f2937}.pbrief p{margin:0 0 8px}.pbrief .bio p{margin:0 0 8px}.pbrief b{color:' + c0 + '}' +
      'details.pfold{border-top:1px solid #e5e2db}details.pfold>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:10px;padding:13px 18px;font-family:"DM Mono",monospace;font-size:.63rem;text-transform:uppercase;letter-spacing:.11em;color:' + c0 + ';font-weight:700}' +
      'details.pfold>summary::-webkit-details-marker{display:none}details.pfold>summary .arr{margin-left:auto;font-size:.7rem;transition:transform .15s}details.pfold[open]>summary .arr{transform:rotate(180deg)}details.pfold>summary+.sec{border-top:0;padding-top:4px}details.pfold>summary+.sec>h2{display:none}' +
      '.phead{background:' + c0 + '!important}.btn.hot{background:' + c1 + '!important;border-color:' + c1 + '!important}';
    document.head.appendChild(s);
  }
  function teaser(sec) {
    var t = (sec.textContent || '').replace(/\s+/g, ' ').trim();
    var h = sec.querySelector('h2'); if (h) t = t.replace(h.textContent.trim(), '').trim();
    var links = sec.querySelectorAll('a.btn, a.dl, a.chip, .ovcard, .dcard, tr').length;
    var maps = sec.querySelector('[data-profile-map], [data-race-map], [data-ed-results], .leaflet-container, iframe') ? 'Map. ' : '';
    return maps + (links >= 3 ? links + ' items. ' : '') + t.slice(0, 110);
  }
  function init(el) {
    var boro = el.getAttribute('data-boro') || 'Brooklyn', pal = PAL[boro] || PAL['Brooklyn'];
    css(pal[0], pal[1]);
    el.className = 'ptiles';
    el.innerHTML = '<div class="ps"><input type="search" placeholder="Search this page" autocomplete="off" data-pq></div><div class="pn" data-pn></div><div class="pg" data-pg></div>';
    var grid = el.querySelector('[data-pg]'), q = el.querySelector('[data-pq]'), note = el.querySelector('[data-pn]');
    // the short bio comes up top, under the banner and before the tiles
    var brief = null;
    Array.prototype.forEach.call(document.querySelectorAll('.sec'), function (sec) { var h = sec.querySelector('h2'); if (h && /^in brief$/i.test(h.textContent.trim())) brief = sec; });
    var bio = brief ? brief.querySelector('.bio') : null;
    if (bio) { var bx = document.createElement('div'); bx.className = 'pbrief'; bx.appendChild(bio); el.parentNode.insertBefore(bx, el); }
    var cbd = document.querySelector('.cd-description');
    if (cbd && !bio) { var ps = cbd.querySelectorAll('p'); var bx2 = document.createElement('div'); bx2.className = 'pbrief'; var txt = ''; Array.prototype.forEach.call(ps, function (pp, i) { if (i < 2) txt += '<p>' + pp.innerHTML + '</p>'; }); if (txt) { bx2.innerHTML = txt; el.parentNode.insertBefore(bx2, el); } }
    var entries = [];
    // page-specific lead tiles, first in the grid: data-own="Title;href;desc;kicker|..."
    (el.getAttribute('data-own') || '').split('|').filter(Boolean).forEach(function (x) {
      var p = x.split(';'); var a = document.createElement('a'); a.className = 'ptile go'; a.href = p[1];
      if (/^https?:/.test(p[1])) { a.target = '_blank'; a.rel = 'noopener'; }
      if (p[4]) {
        a.className = 'ptile art';
        a.innerHTML = '<span class="ai"><img src="' + esc(p[4]) + '" alt="' + esc(p[0]) + '" loading="lazy"></span><span class="al"><span class="t">' + esc(p[0]) + '</span><span class="d">' + esc(p[2] || '') + '</span></span>';
      } else {
        a.innerHTML = '<span class="k">' + esc(p[3] || 'Own page') + '</span><span class="t">' + esc(p[0]) + '</span><span class="d">' + esc(p[2] || '') + '</span>';
      }
      grid.appendChild(a); entries.push({ el: a, text: (p[0] + ' ' + (p[2] || '')).toLowerCase() });
    });
    // quick links to the district's own pages
    [['elections', 'Election results', 'Every contest since 2025, by election district'], ['parks', 'Parks and activities', 'Every park, court, field, pool and market'], ['zoning', 'Land use, zoning and housing', 'Every tax lot, and the district map']].forEach(function (x) {
      var href = el.getAttribute('data-' + x[0]); if (!href) return;
      var a = document.createElement('a'); a.className = 'ptile go'; a.href = href; a.innerHTML = '<span class="k">Own page</span><span class="t">' + esc(x[1]) + '</span><span class="d">' + esc(x[2]) + '</span>';
      grid.appendChild(a); entries.push({ el: a, text: (x[1] + ' ' + x[2]).toLowerCase() });
    });
    // the community boards this district overlaps, and for a board the districts that overlap it
    (el.getAttribute('data-cbs') || '').split('|').filter(Boolean).forEach(function (x) {
      var p = x.split(';'); var a = document.createElement('a'); a.className = 'ptile cb'; a.href = p[1];
      a.innerHTML = '<span class="k">Community board</span><span class="t">' + esc(p[0]) + '</span><span class="d">' + esc(p[2] + ' election district' + (p[2] === '1' ? '' : 's') + ' of this district') + '</span>';
      grid.appendChild(a); entries.push({ el: a, text: (p[0] + ' community board').toLowerCase() });
    });
    (el.getAttribute('data-dists') || '').split('|').filter(Boolean).forEach(function (x) {
      var p = x.split(';'); var a = document.createElement('a'); a.className = 'ptile cb'; a.href = p[1];
      a.innerHTML = '<span class="k">' + esc(p[0].indexOf('NY-') === 0 ? 'Congress' : p[0].split(' District')[0]) + '</span><span class="t">' + esc(p[2] || p[0]) + '</span><span class="d">' + esc(p[0] + ' \u00b7 ' + p[3] + ' election district' + (p[3] === '1' ? '' : 's') + ' in this board') + '</span>';
      grid.appendChild(a); entries.push({ el: a, text: (p[0] + ' ' + p[2]).toLowerCase() });
    });
    // fold every section after this block, one tile each
    var secs = [];
    var n = el.nextElementSibling;
    while (n) { var nx = n.nextElementSibling; if (n.classList && n.classList.contains('sec') && n.querySelector('h2')) secs.push(n); n = nx; }
    function foldSec(sec) {
      if (sec.dataset.ptFolded) return; sec.dataset.ptFolded = '1';
      var h = sec.querySelector('h2'), title = h.textContent.trim();
      var d = document.createElement('details'); d.className = 'pfold';
      var sm = document.createElement('summary'); sm.innerHTML = esc(title) + '<span class="arr">&#9660;</span>';
      sec.parentNode.insertBefore(d, sec); d.appendChild(sm); d.appendChild(sec);
      var tz = teaser(sec);
      var b = document.createElement('button'); b.type = 'button'; b.className = 'ptile'; b.innerHTML = '<span class="k">Section</span><span class="t">' + esc(title) + '</span><span class="d">' + esc(tz) + '</span>';
      b.addEventListener('click', function () { d.open = true; setTimeout(function () { d.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 60); });
      grid.appendChild(b); entries.push({ el: b, text: (title + ' ' + (sec.textContent || '')).replace(/\s+/g, ' ').toLowerCase(), fold: d });
    }
    secs.forEach(foldSec);
    // sections other scripts add later (the related-officials block) get folded and tiled too
    var wrap = el.closest('.pwrap') || document.body;
    if (window.MutationObserver) new MutationObserver(function (ms) {
      ms.forEach(function (m) { Array.prototype.forEach.call(m.addedNodes, function (nd) {
        if (nd.nodeType === 1 && nd.classList && nd.classList.contains('sec') && nd.querySelector('h2') && !nd.closest('details.pfold')) { foldSec(nd); search(); }
      }); });
    }).observe(wrap, { childList: true });
    // in-page anchors (the jump nav) open the fold they point at
    document.addEventListener('click', function (e) {
      var a = e.target.closest('a[href^="#"]'); if (!a) return;
      var t = document.getElementById(a.getAttribute('href').slice(1)); if (!t) return;
      var d = t.closest('details.pfold'); if (d) d.open = true;
    });
    // community board pages fold their own sections already
    Array.prototype.forEach.call(document.querySelectorAll('.drop-section'), function (ds) {
      var tg = ds.querySelector('.drop-toggle'); if (!tg) return;
      var title = tg.textContent.replace(/[\u25bc\u25be\u25b6\u2713\u{1F517}]/gu, '').replace(/^[^A-Za-z0-9]+/, '').replace(/\s+/g, ' ').trim();
      var body = ds.querySelector('.drop-body'); var t = (body ? body.textContent : '').replace(/\s+/g, ' ').trim();
      var b = document.createElement('button'); b.type = 'button'; b.className = 'ptile'; b.innerHTML = '<span class="k">Section</span><span class="t">' + esc(title) + '</span><span class="d">' + esc(t.slice(0, 110)) + '</span>';
      b.addEventListener('click', function () { if (!ds.classList.contains('open') && !(body && body.offsetParent)) tg.click(); setTimeout(function () { ds.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 60); });
      grid.appendChild(b); entries.push({ el: b, text: (title + ' ' + t).toLowerCase() });
    });
    function search() {
      var s = q.value.trim().toLowerCase(), k = 0;
      entries.forEach(function (e) { var ok = !s || e.text.indexOf(s) !== -1; e.el.classList.toggle('hide', !ok); if (ok) k++; });
      note.textContent = s ? (k + ' of ' + entries.length + ' match') : '';
    }
    q.addEventListener('input', search);
  }
  function boot() { Array.prototype.forEach.call(document.querySelectorAll('[data-profile-tiles]'), init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
