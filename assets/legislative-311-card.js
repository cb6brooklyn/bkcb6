/* 311 card for state legislator profile pages, both chambers.
   Renders into [data-leg311] with data-chamber="senate|assembly" and
   data-district="26". Shades every district in that chamber by its own 311
   count for the latest year on file, outlines the one in view, and links
   through to the full 311 page. Counts come from the chamber's rank file,
   which totals reports by the location the City mapped each one to. */
(function () {
  'use strict';

  var host = document.querySelector('[data-sen311], [data-leg311]');
  if (!host || typeof L === 'undefined') return;

  var SD = String(host.getAttribute('data-district') || '').replace(/^0+/, '');
  if (!SD) return;

  var CHAMBER = host.getAttribute('data-chamber') === 'assembly' ? 'assembly' : 'senate';
  var CFG = {
    senate: { key: 'sd', word: 'Senate', rank: '/data/senate-311-rank.json',
              geo: '/data/senate-districts.geojson', page: '/311-senate.html',
              stops: [90000, 110000, 130000, 150000, 175000],
              labels: ['under 90k', '90k to 110k', '110k to 130k', '130k to 150k', '150k to 175k', '175k and up'],
              own: { '26': '/sengounardes/311' } },
    assembly: { key: 'ad', word: 'Assembly', rank: '/data/assembly-311-rank.json',
              geo: '/data/assembly-districts.geojson', page: '/311-assembly.html',
              stops: [40000, 47000, 54000, 68000, 90000],
              labels: ['under 40k', '40k to 47k', '47k to 54k', '54k to 68k', '68k to 90k', '90k and up'],
              own: {} }
  }[CHAMBER];

  var STOPS = CFG.stops;
  var FILL = ['#fdf3c8', '#fbe07a', '#f7c948', '#e8a020', '#c2410c', '#8a1c05'];
  var LABELS = CFG.labels;

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

  Promise.all([get(CFG.rank), get(CFG.geo)])
    .then(function (res) { build(res[0], res[1]); })
    .catch(function () { host.remove(); });

  /* Districts with their own shareable page get linked to it, so a shared link
     carries that district's card rather than the generic one. */
  function linkTo(d){ return CFG.own[d] || (CFG.page + '?' + CFG.key + '=' + d); }
  function selfLink(){ return linkTo(SD); }

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
        '<span>Every ' + CFG.word.toLowerCase() + ' district shaded by its own count, ' + period + '</span></div>' +
      '<div class="s3nums">' +
        '<div class="s3n"><b>' + fmt(mine) + '</b><span>Reports ' + period + '</span></div>' +
        '<div class="s3n"><b>' + place + ' of ' + order.length + '</b><span>Busiest ' + CFG.word.toLowerCase() + ' district</span></div>' +
      '</div>' +
      '<div class="s3legend">' + legend + '</div>' +
      '<div class="s3map" id="sen311map"></div>' +
      '<a class="zoninglink" href="' + selfLink() + '">' +
        'Open the 311 page for ' + CFG.word + ' District ' + SD +
        '<span>Every report mapped and searchable, by month and category, back to 2020</span></a>';

    var map = L.map('sen311map', {
      scrollWheelZoom: false, zoomControl: true, attributionControl: true
    });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
      { maxZoom: 19, attribution: '&copy; OpenStreetMap &copy; CARTO' }).addTo(map);

    L.geoJSON(geo, {
      style: function (f) {
        var n = totals[String((f.properties || {})[CFG.key])];
        return { color: '#ffffff', weight: 1, opacity: .8,
                 fillColor: colorFor(n), fillOpacity: n == null ? .2 : .68 };
      },
      onEachFeature: function (f, layer) {
        var sd = String((f.properties || {})[CFG.key]), n = totals[sd];
        if (!sd) return;
        layer.bindTooltip(CFG.key.toUpperCase() + ' ' + sd + (n != null ? ' \u00b7 ' + fmt(n) + ' reports' : ''), { sticky: true });
        layer.on('click', function () { location.href = linkTo(sd); });
      }
    }).addTo(map);

    var here = {
      type: 'FeatureCollection',
      features: geo.features.filter(function (f) { return String((f.properties || {})[CFG.key]) === SD; })
    };
    var outline = L.geoJSON(here, { style: { color: '#111110', weight: 3, fill: false } }).addTo(map);
    map.fitBounds(outline.getBounds(), { padding: [14, 14] });
  }
})();
