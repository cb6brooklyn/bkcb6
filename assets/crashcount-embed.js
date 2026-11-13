/* crashcount-embed.js: CrashCount's own map and crash counter for a district, on its profile.
   <div data-crashcount data-layer="council|assembly|senate|community|borough|citywide" data-id="39"
        data-path="council-district/39/"></div>
   The counter is CrashCount's published embed (crashcountnyc.com/embed/<layer>/<id>/); the map is the district's
   page on CrashCount opened at its crash map. Both load only when the section is opened. */
(function () {
  var BASE = 'https://crashcountnyc.com/';
  function css() {
    if (document.getElementById('ccx-css')) return;
    var s = document.createElement('style'); s.id = 'ccx-css';
    s.textContent = '.ccx{border:1px solid #e5e2db;border-radius:12px;background:#fff;margin-top:10px;overflow:hidden}'
      + '.ccx>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:10px;padding:10px 12px;font:700 .9rem "DM Sans",sans-serif;color:#0d1b4b}'
      + '.ccx>summary::-webkit-details-marker{display:none}.ccx>summary img{width:34px;height:34px;border-radius:7px;flex:none}'
      + '.ccx>summary:after{content:"\\25BE";margin-left:auto;color:#f47920}.ccx[open]>summary:after{content:"\\25B4"}'
      + '.ccx .ccx-l{font:700 .62rem "DM Mono",monospace;text-transform:uppercase;letter-spacing:.08em;color:#6b6760;margin:10px 12px 4px}'
      + '.ccx iframe{display:block;width:100%;border:0}.ccx .ccx-f{font-size:.78rem;color:#6b6760;padding:8px 12px 12px}'
      + '.ccx .ccx-f a{color:#0d1b4b;font-weight:700}';
    document.head.appendChild(s);
  }
  function frame(src, h, title) {
    var f = document.createElement('iframe');
    f.src = src; f.height = h; f.title = title; f.loading = 'lazy';
    f.setAttribute('referrerpolicy', 'no-referrer-when-downgrade');
    return f;
  }
  function init(el) {
    if (el.dataset.ready) return; el.dataset.ready = '1';
    var layer = el.getAttribute('data-layer'), id = el.getAttribute('data-id'), path = el.getAttribute('data-path');
    if (!layer || !id) return;
    css();
    var d = document.createElement('details'); d.className = 'ccx';
    d.innerHTML = '<summary><img src="/site-icons/crashcount.png" alt="CrashCount">Crash map and counts from CrashCount</summary>';
    function load() {
      if (d.dataset.loaded) return; d.dataset.loaded = '1';
      var l1 = document.createElement('div'); l1.className = 'ccx-l'; l1.textContent = 'Crash map';
      d.appendChild(l1);
      if (path) d.appendChild(frame(BASE + path + '#crash-map', 700, 'CrashCount crash map'));
      var l2 = document.createElement('div'); l2.className = 'ccx-l'; l2.textContent = 'Crash counter';
      d.appendChild(l2);
      d.appendChild(frame(BASE + 'embed/' + layer + '/' + id + '/', 700, 'CrashCount crash counter'));
      var f = document.createElement('div'); f.className = 'ccx-f';
      f.innerHTML = 'From <a href="/crashcount/">CrashCount</a>, from NYPD crash reports. '
        + (path ? '<a href="https://crashcount.nyc/' + path + '?source=bkcb6.app" target="_blank" rel="noopener">This district on CrashCount &#8599;</a>' : '');
      d.appendChild(f);
    }
    d.addEventListener('toggle', function () { if (d.open) load(); });
    el.appendChild(d);
    // inside a section that is itself folded: open with it, so it takes one tap, not two
    var fold = el.parentNode && el.parentNode.closest ? el.parentNode.closest('details') : null;
    if (fold) {
      d.open = true;
      if (fold.open) load(); else fold.addEventListener('toggle', function () { if (fold.open) load(); });
    }
  }
  function all() { Array.prototype.forEach.call(document.querySelectorAll('[data-crashcount]'), init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', all); else all();
})();
