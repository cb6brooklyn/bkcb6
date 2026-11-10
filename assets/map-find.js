/* Address / street and cross street finder for a MapKit map, with a pin.
   MapFind.attach({host, map: () => mapkitMap, onPoint(lon, lat, label), tap: 'single-tap' | 'long-press', hint}) */
(function () {
  'use strict';
  var CSS = '.mfx{margin:0 0 10px}.mfx .seg{display:flex;background:#f1efea;border-radius:999px;padding:4px;margin-bottom:8px}' +
    '.mfx .seg button{flex:1;border:0;background:transparent;font:600 14px "DM Sans",sans-serif;color:#0d1b4b;padding:8px 6px;border-radius:999px;cursor:pointer}' +
    '.mfx .seg button.on{background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.12)}' +
    '.mfx .box{display:flex;align-items:center;gap:8px;height:46px;border:1.5px solid #e6e1d8;border-radius:14px;padding:0 12px;background:#fff}' +
    '.mfx .box input{flex:1;min-width:0;border:0;outline:0;font:400 16px "DM Sans",sans-serif;color:#0d1b4b;background:transparent}' +
    '.mfx .drop{position:relative}.mfx ul{display:none;position:absolute;left:0;right:0;top:4px;z-index:20;margin:0;padding:4px;list-style:none;background:#fff;border:1px solid #e5e2db;border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,.14);max-height:260px;overflow:auto}' +
    '.mfx li{padding:9px 10px;border-radius:8px;font:400 14px "DM Sans",sans-serif;color:#1f2937;cursor:pointer}.mfx li:hover{background:#f4f6fb}' +
    '.mfx .corner{display:none;gap:8px}.mfx .corner select{flex:1;min-width:0;height:46px;border:1.5px solid #e6e1d8;border-radius:14px;padding:0 8px;font:400 15px "DM Sans",sans-serif;color:#0d1b4b;background:#fff}' +
    '.mfx .corner button{flex:none;height:46px;border:0;border-radius:14px;padding:0 16px;background:#f47920;color:#fff;font:700 15px "DM Sans",sans-serif;cursor:pointer}' +
    '.mfx .msg{font:400 13px "DM Sans",sans-serif;color:#4b5563;margin-top:6px;min-height:0}';
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function attach(o) {
    if (!document.getElementById('mfx-css')) { var st = document.createElement('style'); st.id = 'mfx-css'; st.textContent = CSS; document.head.appendChild(st); }
    var h = o.host; h.className = (h.className ? h.className + ' ' : '') + 'mfx';
    h.innerHTML = '<div class="seg"><button type="button" class="on" data-m="a">Address</button><button type="button" data-m="c">Street and cross street</button></div>' +
      '<div data-a><form autocomplete="off"><div class="box"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0d1b4b" stroke-width="2.6" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/></svg><input type="search" placeholder="Address, e.g. 250 Baltic Street" aria-label="Address"></div></form><div class="drop"><ul></ul></div></div>' +
      '<div class="corner" data-c><select aria-label="Street"><option value="">Loading streets</option></select><select aria-label="Cross street"><option value="">Cross street</option></select><button type="button">Go</button></div>' +
      '<div class="msg">' + esc(o.hint || '') + '</div>';
    var q = h.querySelector('input'), ul = h.querySelector('ul'), msg = h.querySelector('.msg'), A = h.querySelector('[data-a]'), C = h.querySelector('[data-c]'),
      sel = C.querySelectorAll('select'), AC = [], t = null, STREETS = null, pin = null;
    function say(s) { msg.textContent = s || ''; }
    function place(lon, lat, label, move) {
      var m = o.map && o.map(); if (m && window.mapkit) {
        if (pin) m.removeAnnotation(pin);
        pin = new mapkit.MarkerAnnotation(new mapkit.Coordinate(lat, lon), { color: '#f47920', title: label || '', calloutEnabled: false });
        m.addAnnotation(pin);
        if (move) m.setRegionAnimated(new mapkit.CoordinateRegion(new mapkit.Coordinate(lat, lon), new mapkit.CoordinateSpan(.012, .012)));
      }
      say(''); if (o.onPoint) o.onPoint(lon, lat, label || 'The pin');
    }
    function geocode(text, label) {
      say('Searching…'); ul.style.display = 'none';
      fetch('https://geosearch.planninglabs.nyc/v2/search?size=1&text=' + encodeURIComponent(text)).then(function (r) { return r.json(); }).then(function (j) {
        var f = j.features && j.features[0];
        if (!f) { say(label ? 'That corner was not found. Try the other cross street.' : 'No match for that address.'); return; }
        place(f.geometry.coordinates[0], f.geometry.coordinates[1], label || f.properties.label, true);
      }).catch(function () { say('Address search did not respond. Try again.'); });
    }
    q.addEventListener('input', function () {
      clearTimeout(t); var v = q.value.trim(); if (v.length < 3) { ul.style.display = 'none'; return; }
      t = setTimeout(function () {
        fetch('https://geosearch.planninglabs.nyc/v2/autocomplete?size=6&text=' + encodeURIComponent(v)).then(function (r) { return r.json(); }).then(function (j) {
          AC = j.features || []; ul.innerHTML = AC.map(function (f, i) { return '<li data-i="' + i + '">' + esc(f.properties.label) + '</li>'; }).join(''); ul.style.display = AC.length ? 'block' : 'none';
        }).catch(function () { });
      }, 220);
    });
    ul.addEventListener('click', function (e) { var li = e.target.closest('li'); if (!li) return; var f = AC[+li.dataset.i]; q.value = f.properties.label; ul.style.display = 'none'; place(f.geometry.coordinates[0], f.geometry.coordinates[1], f.properties.label, true); });
    h.querySelector('form').addEventListener('submit', function (e) { e.preventDefault(); var v = q.value.trim(); if (v) geocode(v); });
    h.querySelector('.seg').addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return; var c = b.dataset.m === 'c';
      h.querySelectorAll('.seg button').forEach(function (x) { x.classList.toggle('on', x === b); });
      A.style.display = c ? 'none' : 'block'; C.style.display = c ? 'flex' : 'none';
      if (c && !STREETS) fetch('/bk/data/bk-streets.json').then(function (r) { return r.json(); }).then(function (j) { STREETS = j; sel[0].innerHTML = '<option value="">Street (Brooklyn)</option>' + j.streets.map(function (n) { return '<option>' + esc(n) + '</option>'; }).join(''); }).catch(function () { sel[0].innerHTML = '<option value="">Street list unavailable</option>'; });
    });
    sel[0].addEventListener('change', function () { var l = ((STREETS || {}).cross || {})[sel[0].value] || []; sel[1].innerHTML = '<option value="">Cross street</option>' + l.map(function (n) { return '<option>' + esc(n) + '</option>'; }).join(''); });
    C.querySelector('button').addEventListener('click', function () { var a = sel[0].value, b = sel[1].value; if (!a || !b) { say('Pick a street and a cross street.'); return; } geocode(a + ' and ' + b + ', Brooklyn, NY', a + ' and ' + b); });
    var hooked = null;
    function hook() { var m = o.map && o.map(); if (!m || m === hooked || !o.tap) return; hooked = m; m.addEventListener(o.tap, function (e) { try { var c = m.convertPointOnPageToCoordinate(e.pointOnPage); place(c.longitude, c.latitude, 'The pin', false); } catch (x) { } }); }
    return { hook: hook, place: place, say: say };
  }
  window.MapFind = { attach: attach };
})();
