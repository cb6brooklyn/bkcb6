/* 311 card for state senator profile pages.
   Renders into [data-sen311] using data-district="26".
   Shades every senate district by its own 311 count for the latest year on
   file, outlines the one in view, and links through to the full 311 page.
   Counts come from data/senate-311-rank.json, which totals reports by the
   location the City mapped each one to. */
(function () {
  'use strict';

  var host = document.querySelector('[data-sen311]');
  if (!host || typeof L === 'undefined') return;

  var SD = String(host.getAttribute('data-district') || '').replace(/^0+/, '');
  if (!SD) return;

  var STOPS = [90000, 110000, 130000, 150000, 175000];
  var FILL = ['#fdf3c8', '#fbe07a', '#f7c948', '#e8a020', '#c2410c', '#8a1c05'];
  var LABELS = ['under 90k', '90k to 110k', '110k to 130k', '130k to 150k', '150k to 175k', '175k and up'];

  function colorFor(n) {
    if (n == null) return '#e9e7e0';
    for (var i = 0; i < STOPS.length; i++) if (n < STOPS[i]) return FILL[i];
    return FILL[FILL.length - 1];
  }
  function fmt(n) { return Number(n).toLocaleString('en-US'); }
  function get(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(url + ' returned ' + r.status);
      return r.json();
    });
  }

  Promise.all([get('/data/senate-311-rank.json'), get('/data/senate-districts.geojson')])
    .then(function (res) { build(res[0], res[1]); })
    .catch(function () { host.remove(); });

  /* Districts with their own shareable page get linked to it, so a shared link
     carries that district's card rather than the generic one. */
  var OWN_PAGE = { '26': '/sengounardes/311' };
  function selfLink(){ return OWN_PAGE[SD] || ('/311-senate.html?sd=' + SD); }

  function build(rank, geo) {
    var years = Object.keys(rank.years).sort();
    var year = years[years.length - 1];
    var totals = rank.years[year];
    var mine = totals[SD];
    if (mine == null) { host.remove(); return; }

    var order = Object.keys(totals).sort(function (a, b) { return totals[b] - totals[a]; });
    var place = order.indexOf(SD) + 1;
    var partial = String(new Date().getFullYear()) === year;
    var period = partial ? year + ' so far' : 'in ' + year;

    var legend = FILL.map(function (c, i) {
      return '<span class="s3rk"><i style="background:' + c + '"></i>' + LABELS[i] + '</span>';
    }).join('');

    host.innerHTML =
      '<div class="mapttl">311 reports in Senate District ' + SD +
        '<span>Every senate district shaded by its own count, ' + period + '</span></div>' +
      '<div class="s3nums">' +
        '<div class="s3n"><b>' + fmt(mine) + '</b><span>Reports ' + period + '</span></div>' +
        '<div class="s3n"><b>' + place + ' of ' + order.length + '</b><span>Busiest senate district</span></div>' +
      '</div>' +
      '<div class="s3legend">' + legend + '</div>' +
      '<div class="s3map" id="sen311map"></div>' +
      '<a class="zoninglink" href="' + selfLink() + '">' +
        'Open the 311 page for Senate District ' + SD +
        '<span>Every report mapped and searchable, by month and category, back to 2020</span></a>';

    var map = L.map('sen311map', {
      scrollWheelZoom: false, zoomControl: true, attributionControl: true
    });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
      { maxZoom: 19, attribution: '&copy; OpenStreetMap &copy; CARTO' }).addTo(map);

    L.geoJSON(geo, {
      style: function (f) {
        var n = totals[String((f.properties || {}).sd)];
        return { color: '#ffffff', weight: 1, opacity: .8,
                 fillColor: colorFor(n), fillOpacity: n == null ? .2 : .68 };
      },
      onEachFeature: function (f, layer) {
        var sd = String((f.properties || {}).sd), n = totals[sd];
        if (!sd) return;
        layer.bindTooltip('SD ' + sd + (n != null ? ' \u00b7 ' + fmt(n) + ' reports' : ''), { sticky: true });
        layer.on('click', function () { location.href = '/311-senate.html?sd=' + sd; });
      }
    }).addTo(map);

    var here = {
      type: 'FeatureCollection',
      features: geo.features.filter(function (f) { return String((f.properties || {}).sd) === SD; })
    };
    var outline = L.geoJSON(here, { style: { color: '#111110', weight: 3, fill: false } }).addTo(map);
    map.fitBounds(outline.getBounds(), { padding: [14, 14] });
  }
})();
