/* Page guide for the rent and for-sale map pages: the map stays first; under it, a short "what is on
   this page" menu, and the long parts below fold closed until opened, so the page is not overwhelming.
     - every existing collapsible section (details.sect) is listed, as it is;
     - the housing-costs section (.inchist) and the affordable housing section (.emb-le) become
       collapsible chapters, closed at first, and each part inside the housing-costs section folds too;
     - on the CB6 page, each titled group (At a glance, Trends, ...) becomes a chapter as well;
     - a "Sections" button stays at the bottom of the screen and brings the menu back.
   Opening a chapter fires a resize so maps and charts inside it draw at their full size. */
(function () {
  'use strict';
  var CSS =
    '.pg-guide{background:#fff;border-top:3px solid #f47920;border-bottom:1px solid #e5e2db;font-family:"DM Sans",sans-serif;color:#132D65}' +
    '.pg-guide .pg-h{background:#0d1b4b;color:#fff;padding:12px 16px}' +
    '.pg-guide .pg-t{font-size:1.02rem;font-weight:800}.pg-guide .pg-s{font-size:.78rem;color:rgba(255,255,255,.78);margin-top:3px;line-height:1.45}' +
    '.pg-guide ol{list-style:none;margin:0;padding:0}' +
    '.pg-guide li{border-top:1px solid #eeebe5}' +
    '.pg-guide a{display:flex;gap:10px;align-items:center;padding:9px 16px;text-decoration:none;color:inherit}' +
    '.pg-guide .tx{min-width:0;flex:1}.pg-guide .dd{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
    '.pg-guide a.on{background:#fff1e5}.pg-guide a.on .n{background:#0d1b4b}' +
    '.pg-guide .go:before{content:"\\203A";font-size:1.1rem;color:#f47920}.pg-guide a.on .go:before{content:"\\2304"}' +
    '.pg-note{margin:10px 12px 4px;padding:12px 15px;background:#fff;border-left:3px solid #f47920;border-radius:4px;font:400 .9rem/1.55 "DM Sans",sans-serif;color:#132D65;max-width:78ch}.pg-note p{margin:0}.pg-note .pg-sig{margin-top:6px;font:500 .66rem "DM Mono",monospace;color:#6b7280}' +
    '#nowbar,#bed-controls,.unitbar,#legend,.legend-sticky,.timebar,#tmScale,.tmscale,.tmlead{position:relative!important;top:auto!important}' +
    '.pg-how{border-top:1px solid #e5e2db}.pg-how>summary{cursor:pointer;padding:9px 15px;font:700 .62rem "DM Mono",monospace;text-transform:uppercase;letter-spacing:.08em;color:#f47920;list-style:none}' +
    '.pg-how>summary::-webkit-details-marker{display:none}.pg-how>summary:after{content:" \\25BE"}.pg-how[open]>summary:after{content:" \\25B4"}' +
    '.pg-guide a:hover,.pg-guide a:focus{background:#fff6ee;outline:none}' +
    '.pg-guide .n{flex:none;width:22px;height:22px;border-radius:50%;background:#f47920;color:#fff;font:700 .66rem/22px "DM Mono",monospace;text-align:center}' +
    '.pg-guide .tt{font-weight:800;font-size:.86rem;line-height:1.3}.pg-guide .dd{font-size:.72rem;color:#7a7f8c;line-height:1.4;margin-top:1px}' +
    '.pg-guide .go{margin-left:auto;flex:none}' +
    'details.pg-ch{background:#fff;border-top:1px solid #e5e2db}' +
    'details.pg-ch>summary{list-style:none;cursor:pointer;display:flex;gap:11px;align-items:center;padding:14px 16px;background:#f8f7f4;border-left:4px solid #f47920}' +
    'details.pg-ch>summary::-webkit-details-marker{display:none}' +
    'details.pg-ch>summary .ct{font-weight:800;font-size:.98rem;color:#0d1b4b}details.pg-ch>summary .cd{font-size:.76rem;color:#5c6170;margin-top:2px;line-height:1.4}' +
    'details.pg-ch>summary .cv{margin-left:auto;flex:none;font:700 .62rem "DM Mono",monospace;color:#f47920;text-transform:uppercase}' +
    'details.pg-ch>summary .cv:before{content:"open \\25BE"}details.pg-ch[open]>summary .cv:before{content:"close \\25B4"}' +
    '.inchist .ih-h.pg-fold{cursor:pointer;user-select:none}' +
    '.inchist .ih-h.pg-fold:after{content:"show \\25BE";margin-left:auto;font:700 .6rem "DM Mono",monospace;color:#f47920;text-transform:uppercase}' +
    '.inchist .ih-h.pg-fold.pg-on:after{content:"hide \\25B4"}' +
    '.pg-hide{display:none!important}' +
    /* the orange "could you qualify" link duplicates the Affordable housing section built into these pages */
    'a.afford-cta{display:none!important}' +
    '#pgFab{position:fixed;left:14px;bottom:16px;z-index:9500;display:inline-flex;align-items:center;gap:7px;padding:10px 15px;border:0;border-radius:999px;background:#0d1b4b;color:#fff;font:700 .82rem "DM Sans",sans-serif;box-shadow:0 3px 12px rgba(0,0,0,.28);cursor:pointer}' +
    '#pgFab span{color:#f47920}';

  var DESC = {
    inchist: ['Costs, income and context',
      'Household income and wages over time, rent burden, owners and renters, homes built, the down payment and monthly cost to buy, property tax rates, rent stabilization, the City’s housing budget, and HUD. One switch adjusts older years for inflation.'],
    'emb-le': ['Affordable housing',
      'What you may qualify for, every open City housing lottery, income limits, what has been built, State housing, and the free neighborhood groups that help you apply (in CB6, FAC and CGA).']
  };

  function fire() { try { window.dispatchEvent(new Event('resize')); } catch (e) {} setTimeout(function () { try { window.dispatchEvent(new Event('resize')); } catch (e) {} }, 300); }

  function chapter(nodes, title, desc, id) {
    var first = nodes[0], d = document.createElement('details');
    d.className = 'pg-ch'; d.id = id;
    d.innerHTML = '<summary><span><span class="ct"></span><span class="cd" style="display:block"></span></span><span class="cv"></span></summary>';
    d.querySelector('.ct').textContent = title; d.querySelector('.cd').textContent = desc;
    first.parentNode.insertBefore(d, first);
    nodes.forEach(function (n) { d.appendChild(n); });
    d.addEventListener('toggle', function () { if (d.open) fire(); });
    return d;
  }

  function foldParts(box) {          /* inside the housing-costs section: each titled part folds; the first stays open */
    var hs = Array.prototype.slice.call(box.querySelectorAll(':scope > .ih-h'));
    hs.forEach(function (h, i) {
      var parts = [], n = h.nextElementSibling;
      while (n && !n.classList.contains('ih-h')) { parts.push(n); n = n.nextElementSibling; }
      if (!parts.length) return;
      h.classList.add('pg-fold');
      var set = function (on) { h.classList.toggle('pg-on', on); parts.forEach(function (p) { p.classList.toggle('pg-hide', !on); }); if (on) fire(); };
      set(i === 0);
      h.addEventListener('click', function () { set(!h.classList.contains('pg-on')); });
    });
  }

  function build() {
    if (document.getElementById('pgGuide')) return;
    var st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
    var items = [], k = 0;

    /* CB6 page: each titled group in the CB6 sections */
    document.querySelectorAll('.cb6x .wrap').forEach(function (w) {
      if (w.closest('.emb-le') || w.closest('[class^="emb-"]')) return;   /* not the affordable housing copy's own layout */
      var kids = Array.prototype.slice.call(w.children), cur = null;
      kids.forEach(function (el) {
        if (el.classList.contains('eyebrow')) {
          var h2 = el.nextElementSibling, sub = h2 && h2.nextElementSibling;
          cur = { nodes: [el], title: (h2 && h2.classList.contains('h2') ? h2.textContent : el.textContent).trim(),
                  desc: sub && sub.classList.contains('sub') ? sub.textContent.trim() : '' };
          items.push({ kind: 'group', g: cur });
        } else if (el.classList.contains('inchist') || el.classList.contains('emb-le')) {
          cur = null;
        } else if (cur) { cur.nodes.push(el); }
      });
    });
    items.forEach(function (it) { if (it.kind === 'group') { it.el = chapter(it.g.nodes, it.g.title, it.g.desc, 'pg-' + (++k)); it.title = it.g.title; it.desc = it.g.desc; } });

    /* the housing-costs and affordable housing sections */
    ['inchist', 'emb-le'].forEach(function (cls) {
      var el = document.querySelector('.' + cls);
      if (!el) return;
      if (cls === 'inchist') {      /* its parts are drawn after the data loads; fold them once they exist */
        var done = false, tryFold = function () { if (!done && el.querySelector(':scope > .ih-h')) { done = true; foldParts(el); } };
        tryFold();
        if (!done) { var mo = new MutationObserver(function () { tryFold(); if (done) mo.disconnect(); }); mo.observe(el, { childList: true }); }
      }
      var c = chapter([el], DESC[cls][0], DESC[cls][1], 'pg-' + cls);
      items.push({ el: c, title: DESC[cls][0], desc: DESC[cls][1] });
    });

    /* the sections that already fold */
    document.querySelectorAll('details.sect').forEach(function (d) {
      if (d.closest('.emb-le') || d.closest('.inchist')) return;
      var t = d.querySelector('.sect-t'), s = d.querySelector('.sect-d');
      if (!t) return;
      if (!d.id) d.id = 'pg-s' + (++k);
      d.addEventListener('toggle', function () { if (d.open) fire(); });
      items.push({ el: d, title: t.textContent.trim(), desc: s ? s.textContent.trim() : '' });
    });

    /* in page order */
    items = items.filter(function (it) { return it.el; });
    items.sort(function (a, b) { return a.el.compareDocumentPosition(b.el) & 4 ? -1 : 1; });
    if (!items.length) return;

    /* quiet by default: only the menu shows; one section at a time opens under it */
    var shown = null;
    function hideAll() { items.forEach(function (it) { it.el.classList.add('pg-hide'); if (it.el.open) it.el.open = false; }); }
    function show(it) {
      if (shown && shown !== it) { shown.el.open = false; shown.el.classList.add('pg-hide'); shown.a.classList.remove('on'); }
      shown = it; it.a.classList.add('on');
      it.el.classList.remove('pg-hide'); it.el.open = true; fire();
      setTimeout(function () { it.el.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 60);
    }
    items.forEach(function (it) {
      it.el.addEventListener('toggle', function () {          /* closing a section puts it away again */
        if (!it.el.open && shown === it) { it.el.classList.add('pg-hide'); it.a.classList.remove('on'); shown = null; g.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
      });
    });

    var g = document.createElement('nav'); g.className = 'pg-guide'; g.id = 'pgGuide'; g.setAttribute('aria-label', 'On this page');
    g.innerHTML = '<div class="pg-h"><div class="pg-t">On this page</div><div class="pg-s">Pick a section and it opens below this list, one at a time.</div></div><ol></ol>';
    var ol = g.querySelector('ol');
    items.forEach(function (it, i) {
      var li = document.createElement('li'), a = document.createElement('a');
      a.href = '#' + it.el.id;
      a.innerHTML = '<span class="n">' + (i + 1) + '</span><span class="tx"><span class="tt"></span><span class="dd"></span></span><span class="go"></span>';
      a.querySelector('.tt').textContent = it.title; a.querySelector('.dd').textContent = it.desc;
      a.addEventListener('click', function (e) { e.preventDefault(); if (shown === it) { it.el.open = false; return; } show(it); });
      it.a = a; li.appendChild(a); ol.appendChild(li);
    });
    hideAll();
    var cap = document.querySelector('.map-caption');
    var anchor = cap || document.getElementById('map');
    if (!anchor) return;
    anchor.parentNode.insertBefore(g, anchor.nextSibling);
    /* the page's own explanation: its first sentence above the menu, the rest folded */
    var intro = Array.prototype.filter.call(document.querySelectorAll('.pgintro'), function (x) { return !x.closest('[class^="emb-"]'); })[0];
    if (intro) {
      g.parentNode.insertBefore(intro, g);
      var rest = Array.prototype.slice.call(intro.children).filter(function (c) { return !c.classList.contains('pgi-lead'); });
      if (rest.length) {
        var how = document.createElement('details'); how.className = 'pg-how';
        how.innerHTML = '<summary>How to read the map</summary>';
        rest.forEach(function (c) { how.appendChild(c); });
        intro.appendChild(how);
      }
    }
    /* a short note at the top, in Mike's words */
    var P = location.pathname, sale = /sales/.test(P);
    var where = /cb6/.test(P) ? ['Brooklyn CB6', 'neighborhood'] : /^\/bk/.test(P) ? ['Brooklyn', 'community board'] : /boroughs/.test(P) ? ['New York City', 'borough'] : ['New York City', 'community district'];
    var tg = document.querySelector('.rs-toggle');
    if (tg && !document.getElementById('pgNote')) {
      var nt = document.createElement('div'); nt.id = 'pgNote'; nt.className = 'pg-note';
      nt.innerHTML = '<p>Asking ' + (sale ? 'prices for homes for sale' : 'rents for apartments') + ' on the market in ' + where[0] + ', by ' + where[1] + ', since 2010. ' +
        'Press play to see them change. More in the menu under the map.</p>' +
        '<p class="pg-sig">Mike Racioppo, District Manager, Brooklyn Community Board 6</p>';
      tg.parentNode.insertBefore(nt, tg);
      if (intro) { var ld = intro.querySelector('.pgi-lead'); if (ld) ld.style.display = 'none'; }
    }
    var fab = document.createElement('button'); fab.id = 'pgFab'; fab.type = 'button';
    fab.innerHTML = '<span>&#9776;</span> Sections';
    fab.addEventListener('click', function () { g.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
    document.body.appendChild(fab);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build); else build();
})();
