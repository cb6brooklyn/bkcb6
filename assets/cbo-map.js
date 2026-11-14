/* cbo-map.js: the map on a Council-funded organization's profile: its address, with its community district outlined.
   <div data-cbo-map data-lat data-lng data-cd="306" data-label="..." data-logo="/cbo/logos/x.png"></div> */
(function () {
  function init(el) {
    if (!window.L || el.dataset.ready) return; el.dataset.ready = '1';
    var lat = +el.getAttribute('data-lat'), lng = +el.getAttribute('data-lng'), cd = el.getAttribute('data-cd');
    var map = L.map(el, { scrollWheelZoom: false, zoomControl: true }).setView([lat, lng], 16);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e', {
      maxZoom: 19, maxNativeZoom: 18, attribution: '&copy; OpenStreetMap contributors &copy; CARTO' }).addTo(map);
    var icon = L.icon({ iconUrl: el.getAttribute('data-logo'), iconSize: [40, 40], iconAnchor: [20, 20], className: 'cbo-pin' });
    L.marker([lat, lng], { icon: icon, title: el.getAttribute('data-label') }).addTo(map);
    if (cd) fetch('/data/districts/cb-' + cd + '.geojson').then(function (r) { return r.json(); }).then(function (g) {
      L.geoJSON(g, { style: { color: '#f47920', weight: 3, fill: false } }).addTo(map);
    }).catch(function () {});
  }
  var css = document.createElement('style'); css.textContent = '.cbo-pin{border-radius:8px;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.35);background:#fff}'; document.head.appendChild(css);
  function all() { Array.prototype.forEach.call(document.querySelectorAll('[data-cbo-map]'), init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', all); else all();
})();
