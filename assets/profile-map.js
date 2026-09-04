/* Interactive district map for elected official profile pages.
   Reads data-chamber and data-district from the map element. Layers are lazy:
   nothing is fetched until the person switches it on. */
(function () {
  'use strict';

  var GEO = 'https://geosearch.planninglabs.nyc/v2';
  var ARC = 'https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services';
  var CHAMBERS = {
    council: { label: 'Council districts', folder: 'council', color: '#0d1b4b', count: 51 },
    assembly: { label: 'Assembly districts', folder: 'assembly', color: '#7c3aed', count: 65 },
    senate: { label: 'Senate districts', folder: 'senate', color: '#0f766e', count: 28 },
    congress: { label: 'Congressional districts', folder: 'congress', color: '#b45309', count: 13 },
    cb: { label: 'Community boards', folder: 'cb', color: '#be185d', count: 0, codes: ["101", "102", "103", "104", "105", "106", "107", "108", "109", "110", "111", "112", "201", "202", "203", "204", "205", "206", "207", "208", "209", "210", "211", "212", "301", "302", "303", "304", "305", "306", "307", "308", "309", "310", "311", "312", "313", "314", "315", "316", "317", "318", "401", "402", "403", "404", "405", "406", "407", "408", "409", "410", "411", "412", "413", "414", "501", "502", "503"] },
    borough: { label: 'Borough', folder: 'borough', color: '#0d1b4b', count: 1 }
  };
  // the chambers offered as overlays on any district page
  var OVERLAPS = ['council', 'assembly', 'senate', 'congress', 'cb'];
  var ZONE_FILL = {
    R: '#56B4E9', C: '#E69F00', M: '#D55E00', P: '#009E73', X: '#CC79A7', O: '#999999'
  };
  // same order the lot search uses, so the two maps read the same way
  var ZONE_LEGEND = [
    ['R', 'Residential'], ['C', 'Commercial'], ['P', 'Park / open space'],
    ['M', 'Manufacturing'], ['X', 'Mixed use']
  ];
  // near-black sits outside the zoning palette entirely, so the boundary can
  // never be mistaken for a zoning category underneath it
  var BID_LINE = '#111827';

  function zoneFamily(z) {
    z = String(z || '').toUpperCase().trim();
    if (!z) return 'O';
    if (z.indexOf('PARK') >= 0 || z.indexOf('PLAYGROUND') >= 0) return 'P';
    if (z.indexOf('/') >= 0 && z.indexOf('M') >= 0 && z.indexOf('R') >= 0) return 'X';
    if (z.charAt(0) === 'R') return 'R';
    if (z.charAt(0) === 'C') return 'C';
    if (z.charAt(0) === 'M') return 'M';
    return 'O';
  }

  function getJSON(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    });
  }

  function boundsToEnvelope(b) {
    return JSON.stringify({
      xmin: b.getWest(), ymin: b.getSouth(), xmax: b.getEast(), ymax: b.getNorth(),
      spatialReference: { wkid: 4326 }
    });
  }

  function arcQuery(service, fields, bounds, max) {
    var u = ARC + '/' + service + '/FeatureServer/0/query'
      + '?f=geojson&outFields=' + encodeURIComponent(fields)
      + '&geometryType=esriGeometryEnvelope&inSR=4326&outSR=4326'
      + '&spatialRel=esriSpatialRelIntersects&where=1%3D1'
      + '&resultRecordCount=' + (max || 1200)
      + '&geometry=' + encodeURIComponent(boundsToEnvelope(bounds));
    return getJSON(u);
  }

  var STYLE_ID = 'pmap-legend-css';
  function injectCss() {
    if (document.getElementById(STYLE_ID)) return;
    var s = document.createElement('style');
    s.id = STYLE_ID;
    s.textContent =
      '.pmap-legend{background:rgba(255,255,255,.94);border:1px solid #d6d3d1;border-radius:9px;'
      + 'padding:8px 10px;font-family:"DM Sans",sans-serif;color:#0d1b4b;'
      + 'box-shadow:0 2px 8px rgba(0,0,0,.14);line-height:1.35;max-width:170px}'
      + '.pmap-legend .lt{font-family:"DM Mono",monospace;font-size:.55rem;text-transform:uppercase;'
      + 'letter-spacing:.09em;color:#6b6760;font-weight:700;margin-bottom:5px}'
      + '.pmap-legend .li{display:flex;align-items:center;gap:6px;font-size:.7rem;font-weight:600;margin-top:3px}'
      + '.pmap-legend .sw{width:13px;height:13px;border-radius:3px;flex:none;border:1px solid rgba(0,0,0,.18)}'
      + '.pmap-legend .ln{width:13px;height:0;flex:none;border-top:3px solid ' + BID_LINE + ';'
      + 'box-shadow:0 0 0 1px #fff}'
      + '.leaflet-tooltip.pmap-corridor{background:rgba(255,255,255,.92);border:1.5px solid '
      + BID_LINE + ';border-radius:5px;padding:1px 6px;font-family:"DM Sans",sans-serif;'
      + 'font-size:.6rem;font-weight:800;color:' + BID_LINE + ';white-space:nowrap;'
      + 'box-shadow:0 1px 4px rgba(0,0,0,.22)}'
      + '.leaflet-tooltip.pmap-corridor:before{display:none}'
      + '.leaflet-tooltip.pmap-place{background:#0d1b4b;border:0;border-radius:5px;'
      + 'padding:3px 8px;font-family:"DM Sans",sans-serif;font-size:.63rem;font-weight:800;'
      + 'color:#fff;white-space:nowrap;box-shadow:0 2px 7px rgba(13,27,75,.35)}'
      + '.leaflet-tooltip.pmap-place:before{border-top-color:#0d1b4b}'
      + '@media(max-width:480px){.pmap-legend{padding:6px 8px;max-width:138px}'
      + '.pmap-legend .li{font-size:.63rem}}';
    document.head.appendChild(s);
  }

  // The bounding box centre of a long diagonal ribbon is not on the ribbon, so
  // a label placed there floats a few blocks off the street it is naming. Take
  // the mean of the vertices and snap to the nearest real one.
  function corridorPoint(g) {
    var pts = [];
    function walk(c) {
      if (!c || !c.length) return;
      if (typeof c[0] === 'number') { pts.push(c); return; }
      for (var i = 0; i < c.length; i++) walk(c[i]);
    }
    ((g && g.features) || []).forEach(function (f) {
      if (f.geometry && f.geometry.coordinates) walk(f.geometry.coordinates);
    });
    if (!pts.length) return null;
    var sx = 0, sy = 0;
    pts.forEach(function (q) { sx += q[0]; sy += q[1]; });
    var mx = sx / pts.length, my = sy / pts.length;
    var best = null, bd = Infinity;
    pts.forEach(function (q) {
      var d = (q[0] - mx) * (q[0] - mx) + (q[1] - my) * (q[1] - my);
      if (d < bd) { bd = d; best = q; }
    });
    return best ? [best[1], best[0]] : null;
  }

  function withLabels(fn) {
    if (window.MapLabels) return fn(window.MapLabels);
    var s = document.querySelector('script[data-maplabels]');
    if (!s) { s = document.createElement('script'); s.src = '/assets/map-labels.js?v=20260829a'; s.setAttribute('data-maplabels', '1'); document.head.appendChild(s); }
    s.addEventListener('load', function () { if (window.MapLabels) fn(window.MapLabels); });
  }
  function init(el) {
    if (typeof L === 'undefined' || !el || el.dataset.profileMapReady === 'true') return;
    var fold = el.closest('details:not([open])');
    if (fold) {
      if (!el.dataset.profileMapWait) { el.dataset.profileMapWait = '1'; fold.addEventListener('toggle', function () { if (fold.open) init(el); }); }
      return;
    }
    el.dataset.profileMapReady = 'true';

    var chamber = el.getAttribute('data-chamber') || 'council';
    var district = String(el.getAttribute('data-district') || '');
    // a BID is not a chamber, so it names its own file and skips the sibling toggles
    var bidSlug = el.getAttribute('data-bid-slug') || '';
    // a place profile is not a BID, but it wants the same zoning-on opening view
    var startZoning = el.getAttribute('data-start-zoning') === '1';
    var self = bidSlug ? { label: 'BID', folder: 'bid', color: BID_LINE } : CHAMBERS[chamber];
    if (!self) return;
    // an address profile pins its own front door and opens on it, so the map
    // reads as a place rather than as a district that happens to contain one
    var ptLat = parseFloat(el.getAttribute('data-point-lat'));
    var ptLng = parseFloat(el.getAttribute('data-point-lng'));
    var ptZoom = parseInt(el.getAttribute('data-point-zoom') || '17', 10);
    var ptLabel = el.getAttribute('data-point-label') || '';
    var ptIcon = el.getAttribute('data-point-icon') || '';
    var ptIconW = parseInt(el.getAttribute('data-point-icon-w') || '200', 10);
    var ptIconH = parseInt(el.getAttribute('data-point-icon-h') || '200', 10);
    var hasPoint = isFinite(ptLat) && isFinite(ptLng);
    injectCss();

    var map = L.map(el, { scrollWheelZoom: false, zoomControl: true });
    // CARTO now watermarks unkeyed tiles, so use Esri's keyless light canvas
    // The light grey canvas has no cached tiles past z16, and past it Esri
    // serves a "Map data not yet available" placeholder rather than nothing.
    // maxNativeZoom stops at the last real tile and scales it up instead.
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e', {
      maxZoom: 19, maxNativeZoom: 16,
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    }).addTo(map);

    // A flat grey basemap under a single shape reads as nothing. Zoning and land
    // use go in their own pane below the street labels, so the colour tells you
    // what the blocks are while the street names stay readable on top of it.
    function pane(name, z, noClick) {
      if (!map.createPane) return null;
      map.createPane(name);
      var p = map.getPane(name);
      if (p && p.style) {
        p.style.zIndex = z;
        if (noClick) p.style.pointerEvents = 'none';
      }
      return name;
    }
    var FILL_PANE = pane('pmapFills', 410);
    // the boundary goes above the fills but below the street names, so the name
    // of the street the district runs along is not hidden by the district
    var LINE_PANE = pane('pmapLine', 440);
    var LABEL_PANE = pane('pmapLabels', 450, true);

    // Esri's light grey reference carries almost no street names at the zoom a
    // long thin corridor fits at, which left people no way to place the shape.
    // World_Transportation labels the grid at that zoom, so BID pages use it.
    // Chamber districts are borough-scale, where those labels are just noise.
    var refTiles = bidSlug
      ? 'https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e'
      : 'https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e';
    L.tileLayer(refTiles, {
      maxZoom: 19, opacity: bidSlug ? 0.6 : 0.9, pane: LABEL_PANE || undefined
    }).addTo(map);

    if (hasPoint) {
      var place;
      if (ptIcon && L.divIcon) {
        // the logo in a white plate on a navy tail, the same pin the lot card
        // drops, so a place reads as itself rather than as a generic dot
        var iw = 58, ih = Math.round(iw * (ptIconH / ptIconW)) || 58;
        place = L.marker([ptLat, ptLng], {
          pane: LINE_PANE || undefined,
          icon: L.divIcon({
            className: '', iconSize: [iw, ih + 10], iconAnchor: [iw / 2, ih + 10],
            html: '<div style="text-align:center">'
              + '<img src="' + ptIcon + '" alt="" style="width:' + iw + 'px;height:' + ih
              + 'px;display:block;background:#fff;border:2px solid #0d1b4b;border-radius:7px;'
              + 'box-shadow:0 2px 6px rgba(0,0,0,.28)">'
              + '<div style="width:0;height:0;margin:0 auto;border-left:6px solid transparent;'
              + 'border-right:6px solid transparent;border-top:9px solid #0d1b4b"></div></div>'
          })
        }).addTo(map);
      } else {
        place = L.circleMarker([ptLat, ptLng], {
          pane: LINE_PANE || undefined,
          radius: 9, color: '#ffffff', weight: 3, opacity: 1,
          fillColor: '#f47920', fillOpacity: 1
        }).addTo(map);
      }
      if (ptLabel && place.bindTooltip) {
        place.bindTooltip(ptLabel, {
          permanent: true, direction: 'top',
          offset: ptIcon ? [0, -6] : [0, -8], className: 'pmap-place'
        });
      }
    }

    var homeBounds = null;
    var pin = null;
    var layers = {};
    var status = el.parentNode.querySelector('[data-map-status]');

    function say(msg) { if (status) status.textContent = msg || ''; }

    // ---- the member's own district ----
    var ownFile = bidSlug ? ('/data/districts/bid-' + bidSlug + '.geojson')
                          : ('/data/districts/' + self.folder + '-' + district + '.geojson');
    getJSON(ownFile).then(function (g) {
      // The BID is a thin ribbon of frontage. A fill would hide the zoning
      // underneath it, so it gets a white casing and a dark line instead.
      if (bidSlug) {
        L.geoJSON(g, {
          pane: LINE_PANE || undefined,
          style: { color: '#ffffff', weight: 4, opacity: 1, fill: false }
        }).addTo(map);
      }
      var own = L.geoJSON(g, {
        pane: bidSlug ? (LINE_PANE || undefined) : undefined,
        style: bidSlug
          ? { color: BID_LINE, weight: 1.3, opacity: 1, fill: false }
          : { color: self.color, weight: 2.5, fillColor: '#f47920', fillOpacity: 0.14 }
      }).addTo(map);
      homeBounds = own.getBounds();
      // neighborhoods, the district and the borough, so the map reads at a glance
      var dl = bidSlug ? '' : chamber === 'council' ? 'Council District ' + district : chamber === 'assembly' ? 'Assembly District ' + district
        : chamber === 'senate' ? 'Senate District ' + district : chamber === 'congress' ? 'NY-' + district : chamber === 'cb' ? (district.length === 3 ? ({ '1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island' })[district.charAt(0)] + ' CB' + parseInt(district.slice(1), 10) : 'Brooklyn CB' + district) : chamber === 'borough' ? '' : '';
      withLabels(function (ML) { ML.add(map, { bounds: homeBounds, district: dl, boroughs: chamber === 'borough' ? ['Brooklyn'] : undefined }); });
      // a BID is a small shape in a small frame, so it can sit tighter
      if (hasPoint) map.setView([ptLat, ptLng], ptZoom);
      else map.fitBounds(homeBounds, { padding: bidSlug ? [8, 8] : [14, 14] });
      if (!bidSlug) own.bringToBack();
      if (bidSlug) {
        var nm = (g.features && g.features[0] && g.features[0].properties
          && g.features[0].properties.name) || '';
        var mid = corridorPoint(g);
        if (nm && mid) {
          own.bindTooltip(nm + ' BID', {
            permanent: true, direction: 'center', className: 'pmap-corridor'
          });
          var tt = own.getTooltip && own.getTooltip();
          if (tt && tt.setLatLng) tt.setLatLng(mid);
        }
        startDefaults();
      }
    }).catch(function () {
      map.setView(hasPoint ? [ptLat, ptLng] : [40.70, -73.95], hasPoint ? ptZoom : 11);
      startDefaults();
    });

    // ---- overlapping districts from the other two chambers, faint ----
    function overlapLayer(kind) {
      var c = CHAMBERS[kind];
      var group = L.layerGroup();
      var loaded = false;
      return {
        group: group,
        load: function () {
          if (loaded) return Promise.resolve();
          loaded = true;
          if (!homeBounds) return Promise.resolve();
          var jobs = [];
          (c.codes || (function () { var r = []; for (var i = 1; i <= c.count; i++) r.push(i); return r; })()).forEach(function (i) {
            jobs.push(getJSON('/data/districts/' + c.folder + '-' + i + '.geojson')
              .catch(function () { return null; }));
          });
          say('Loading ' + c.label.toLowerCase() + '\u2026');
          return Promise.all(jobs).then(function (all) {
            all.forEach(function (g) {
              if (!g || !g.features || !g.features[0]) return;
              var lyr = L.geoJSON(g, {
                style: { color: c.color, weight: 1, opacity: 0.55, fillColor: c.color, fillOpacity: 0.05 }
              });
              // only draw the ones that actually overlap this member's district
              try {
                if (homeBounds && !homeBounds.intersects(lyr.getBounds())) return;
              } catch (e) { return; }
              var num = g.features[0].properties.district;
              var BN = { '1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island' };
              lyr.bindTooltip(k === 'cb' ? (String(num).length === 3 ? BN[String(num).charAt(0)] + ' CB' + parseInt(String(num).slice(1), 10) : 'Brooklyn CB' + num) : k === 'congress' ? 'NY-' + num : c.label.replace(' districts', '') + ' District ' + num, { sticky: true });
              group.addLayer(lyr);
            });
            say('');
          });
        }
      };
    }

    OVERLAPS.forEach(function (k) {
      if (!bidSlug && k === chamber) return;
      layers['overlap-' + k] = overlapLayer(k);
    });

    // ---- zoning, live from City Planning ----
    // It queries whatever is in view, so once it is on it has to redraw as the
    // map moves or it silently goes stale the first time somebody pans.
    layers.zoning = (function () {
      var group = L.layerGroup();
      var busy = false;
      function draw() {
        if (busy) return Promise.resolve();
        if (map.getZoom() < 13) {
          group.clearLayers();
          say('Zoom in to see zoning.');
          return Promise.resolve();
        }
        busy = true;
        say('Loading zoning\u2026');
        return arcQuery('nyzd', 'ZONEDIST', map.getBounds(), 2000).then(function (g) {
          group.clearLayers();
          L.geoJSON(g, {
            pane: FILL_PANE || undefined,
            style: function (f) {
              var fam = zoneFamily(f.properties.ZONEDIST);
              return {
                color: ZONE_FILL[fam],
                weight: bidSlug ? 0.4 : 0.6,
                opacity: bidSlug ? 0.5 : 1,
                fillColor: ZONE_FILL[fam],
                fillOpacity: bidSlug ? 0.26 : 0.42
              };
            },
            onEachFeature: function (f, l) { l.bindTooltip(f.properties.ZONEDIST || 'Zoning', { sticky: true }); }
          }).addTo(group);
          say('');
        }).catch(function () {
          say('Zoning did not load at this zoom.');
        }).then(function () { busy = false; });
      }
      return { group: group, load: draw, refresh: draw, legend: true };
    })();

    // ---- land use, live from MapPLUTO ----
    var LU_HEX = {
      '01': '#FEFFA8', '02': '#FCB842', '03': '#B16E00', '04': '#ff8341', '05': '#fc2929',
      '06': '#E362FB', '07': '#E0BEEB', '08': '#44A3D5', '09': '#78D271', '10': '#BAB8B6', '11': '#555555'
    };
    var LU_LABEL = {
      '01': 'One & two family', '02': 'Multi-family walk-up', '03': 'Multi-family elevator',
      '04': 'Mixed residential & commercial', '05': 'Commercial & office', '06': 'Industrial & manufacturing',
      '07': 'Transportation & utility', '08': 'Public facilities & institutions',
      '09': 'Open space & recreation', '10': 'Parking', '11': 'Vacant land'
    };
    layers.landuse = (function () {
      var group = L.layerGroup();
      var done = false;
      return {
        group: group,
        load: function () {
          if (done) return Promise.resolve();
          done = true;
          if (map.getZoom() < 15) { say('Zoom in to see land use lot by lot.'); done = false; return Promise.resolve(); }
          say('Loading land use\u2026');
          return arcQuery('MAPPLUTO', 'LandUse,Address,ZoneDist1', map.getBounds(), 1500).then(function (g) {
            L.geoJSON(g, {
              pane: FILL_PANE || undefined,
              style: function (f) {
                var k = String(f.properties.LandUse || '').padStart(2, '0');
                var c = LU_HEX[k] || '#d9d6cf';
                return { color: c, weight: 0.4, fillColor: c, fillOpacity: 0.6 };
              },
              onEachFeature: function (f, l) {
                var k = String(f.properties.LandUse || '').padStart(2, '0');
                l.bindTooltip((f.properties.Address || 'Lot') + '<br>' + (LU_LABEL[k] || 'Land use ' + k), { sticky: true });
              }
            }).addTo(group);
            say('');
          }).catch(function () { say('Land use did not load. Try zooming in.'); });
        }
      };
    })();

    // ---- landmarks: historic districts ----
    layers.landmarks = (function () {
      var group = L.layerGroup();
      var done = false;
      return {
        group: group,
        load: function () {
          if (done) return Promise.resolve();
          done = true;
          say('Loading historic districts\u2026');
          return getJSON('/data/historic-districts.geojson').then(function (g) {
            L.geoJSON(g, {
              style: { color: '#7a5c2e', weight: 1.2, fillColor: '#c8a24a', fillOpacity: 0.3 },
              onEachFeature: function (f, l) {
                l.bindTooltip((f.properties.area_name || 'Historic district')
                  + (f.properties.desdate ? '<br>Designated ' + String(f.properties.desdate).slice(0, 10) : ''), { sticky: true });
              }
            }).addTo(group);
            say('');
          }).catch(function () { say('Historic districts did not load.'); });
        }
      };
    })();

    // ---- business improvement districts ----
    layers.bids = (function () {
      var group = L.layerGroup();
      var done = false;
      var districtNum = parseInt(district, 10);
      function isOwn(p) {
        return chamber === 'council' && p && p.councils && p.councils.indexOf(districtNum) > -1;
      }
      function popup(p) {
        var html = '<b>' + p.name + '</b><br>' + p.borough
          + (p.year ? ' &middot; established ' + p.year : '');
        if (p.councils && p.councils.length) {
          html += '<br>Council district' + (p.councils.length > 1 ? 's ' : ' ') + p.councils.join(', ');
        }
        if (p.url) html += '<br><a href="' + p.url + '" target="_blank" rel="noopener">Visit the BID &#8599;</a>';
        html += '<br><a href="/bids">All 76 BIDs &rarr;</a>';
        return html;
      }
      return {
        group: group,
        load: function () {
          if (done) return Promise.resolve();
          done = true;
          say('Loading business improvement districts\u2026');
          return getJSON('/data/bids.geojson').then(function (g) {
            var drawn = 0;
            (g.features || []).forEach(function (f) {
              var p = f.properties || {};
              var own = isOwn(p);
              var lyr = L.geoJSON(f, {
                style: own
                  ? { color: '#ea580c', weight: 2.2, fillColor: '#ea580c', fillOpacity: 0.4 }
                  : { color: '#0d1b4b', weight: 1, opacity: 0.5, fillColor: '#0d1b4b', fillOpacity: 0.12 }
              });
              try {
                if (homeBounds && !homeBounds.intersects(lyr.getBounds())) return;
              } catch (e) { return; }
              lyr.bindTooltip(p.name + (own ? ' \u00b7 in this district' : ''), { sticky: true });
              lyr.bindPopup(popup(p));
              group.addLayer(lyr);
              drawn++;
            });
            say(drawn ? '' : 'No business improvement districts fall in this district.');
          }).catch(function () { say('Business improvement districts did not load.'); });
        }
      };
    })();

    // ---- transportation: subway, bus stops, bike routes for the boroughs in view ----
    layers.transport = (function () {
      var group = L.layerGroup();
      var done = false;
      return {
        group: group,
        load: function () {
          if (done) return Promise.resolve();
          done = true;
          say('Loading transportation\u2026');
          var boros = ['brooklyn', 'manhattan', 'queens', 'bronx', 'statenisland'];
          return Promise.all(boros.map(function (b) {
            return getJSON('/transport-data/' + b + '.json').catch(function () { return null; });
          })).then(function (all) {
            var b = map.getBounds();
            all.forEach(function (t) {
              if (!t) return;
              (t.subway && t.subway.features ? t.subway.features : []).forEach(function (f) {
                if (!f.geometry || f.geometry.type !== 'Point') return;
                var c = f.geometry.coordinates;
                if (!b.contains([c[1], c[0]])) return;
                L.circleMarker([c[1], c[0]], { radius: 4, color: '#0d1b4b', weight: 1.5, fillColor: '#fff', fillOpacity: 1 })
                  .bindTooltip((f.properties.stop_name || f.properties.name || 'Subway'), { sticky: true })
                  .addTo(group);
              });
              (t.bike && t.bike.features ? t.bike.features : []).forEach(function (f) {
                if (!f.geometry) return;
                var lyr = L.geoJSON(f, { style: { color: '#009E73', weight: 2, opacity: 0.75 } });
                try { if (!b.intersects(lyr.getBounds())) return; } catch (e) { return; }
                lyr.addTo(group);
              });
            });
            say('');
          }).catch(function () { say('Transportation did not load.'); });
        }
      };
    })();

    // ---- legend, shown only while a layer that needs one is on ----
    var legend = null;
    function legendHtml() {
      var h = '<div class="lt">Zoning</div>';
      ZONE_LEGEND.forEach(function (z) {
        h += '<div class="li"><span class="sw" style="background:' + ZONE_FILL[z[0]] + '"></span>' + z[1] + '</div>';
      });
      if (bidSlug) h += '<div class="li"><span class="ln"></span>BID boundary</div>';
      return h;
    }
    function showLegend(on) {
      if (!L.control || !L.DomUtil) return;
      if (on && !legend) {
        legend = L.control({ position: 'topright' });
        legend.onAdd = function () {
          var d = L.DomUtil.create('div', 'pmap-legend');
          d.innerHTML = legendHtml();
          return d;
        };
        legend.addTo(map);
      } else if (!on && legend) {
        try { map.removeControl(legend); } catch (e) {}
        legend = null;
      }
    }

    // ---- toggles ----
    var toggleWrap = el.parentNode.querySelector('[data-map-toggles]');
    var toggleBtn = {};
    function setLayer(key, on) {
      var b = toggleBtn[key];
      if (b) b.classList.toggle('on', on);
      if (on) {
        return Promise.resolve(layers[key].load()).then(function () {
          if (!b || b.classList.contains('on')) {
            layers[key].group.addTo(map);
            if (layers[key].legend) showLegend(true);
          }
        });
      }
      map.removeLayer(layers[key].group);
      if (layers[key].legend) showLegend(false);
      return Promise.resolve();
    }
    function addToggle(key, label) {
      if (!toggleWrap || !layers[key]) return;
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'mtog';
      b.textContent = label;
      toggleBtn[key] = b;
      b.addEventListener('click', function () {
        setLayer(key, !b.classList.contains('on'));
      });
      toggleWrap.appendChild(b);
    }

    // a view-scoped layer goes stale the moment the map moves
    var moveTimer = null;
    map.on('moveend', function () {
      clearTimeout(moveTimer);
      moveTimer = setTimeout(function () {
        Object.keys(layers).forEach(function (k) {
          if (layers[k].refresh && map.hasLayer(layers[k].group)) layers[k].refresh();
        });
      }, 400);
    });

    // On a BID page the boundary is a thin ribbon of frontage. Alone on a grey
    // basemap it says nothing, so the zoning underneath it starts switched on.
    function startDefaults() {
      if ((!bidSlug && !startZoning) || startDefaults.done) return;
      startDefaults.done = true;
      setLayer('zoning', true);
    }
    OVERLAPS.forEach(function (k) {
      if (!bidSlug && k === chamber) return;
      addToggle('overlap-' + k, 'Overlapping ' + CHAMBERS[k].label.toLowerCase());
    });

    // the toggle strip starts closed so it does not swallow the page
    var togBtn = el.parentNode.querySelector('[data-map-toggle-btn]');
    if (togBtn && toggleWrap) {
      togBtn.addEventListener('click', function () {
        var on = toggleWrap.hidden;
        toggleWrap.hidden = !on;
        togBtn.setAttribute('aria-expanded', on ? 'true' : 'false');
      });
    }
    addToggle('zoning', 'Zoning');
    addToggle('landuse', 'Land use');
    addToggle('landmarks', 'Landmarks');
    addToggle('bids', 'Business improvement districts');
    addToggle('transport', 'Transportation');

    // ---- address search and pin drop ----
    var form = el.parentNode.querySelector('[data-map-search]') || el.parentNode.querySelector('.msearch');
    if (form) {
      var input = form.querySelector('input');
      var btn = form.querySelector('button:not([data-map-reset])');
      function drop(lat, lng, label) {
        if (pin) map.removeLayer(pin);
        pin = L.marker([lat, lng]).addTo(map);
        pin.bindPopup('<b>' + label + '</b><br>'
          + '<a href="/citywide-search.html?address=' + encodeURIComponent(label) + '">Open the full lot record &rarr;</a>').openPopup();
        map.setView([lat, lng], Math.max(map.getZoom(), 16));
      }
      function run() {
        var q = (input.value || '').trim();
        if (!q) return;
        say('Searching\u2026');
        getJSON(GEO + '/search?size=1&text=' + encodeURIComponent(q)).then(function (d) {
          var f = d.features && d.features[0];
          if (!f) { say('No match for that address.'); return; }
          say('');
          drop(f.geometry.coordinates[1], f.geometry.coordinates[0], f.properties.label.replace(', USA', ''));
        }).catch(function () { say('Address search did not respond.'); });
      }
      if (btn) btn.addEventListener('click', function (e) { e.preventDefault(); run(); });
      if (input) input.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); run(); } });
    }

    // click anywhere to drop a pin
    map.on('click', function (ev) {
      say('Looking up that spot\u2026');
      getJSON(GEO + '/reverse?point.lat=' + ev.latlng.lat + '&point.lon=' + ev.latlng.lng + '&size=1')
        .then(function (d) {
          var f = d.features && d.features[0];
          var label = f ? f.properties.label.replace(', USA', '') : 'This spot';
          say('');
          if (pin) map.removeLayer(pin);
          pin = L.marker(ev.latlng).addTo(map);
          pin.bindPopup('<b>' + label + '</b><br>'
            + '<a href="/citywide-search.html?address=' + encodeURIComponent(label) + '">Open the full lot record &rarr;</a>').openPopup();
        }).catch(function () { say(''); });
    });

    var reset = el.parentNode.querySelector('[data-map-reset]');
    if (reset) reset.addEventListener('click', function () {
      if (pin) { map.removeLayer(pin); pin = null; }
      if (homeBounds) map.fitBounds(homeBounds, { padding: [14, 14] });
    });

    // Hand the page a handle on the map so a directory alongside it can put its
    // own pins up. Read only as far as this file is concerned.
    el._pmap = {
      map: map,
      homeBounds: function () { return homeBounds; },
      pane: LINE_PANE
    };
    try {
      el.dispatchEvent(new CustomEvent('profile-map-ready', { bubbles: true }));
    } catch (e) {}

    setTimeout(function () { map.invalidateSize(); }, 300);

    // inside a collapsed <details> the map has no size until it is opened
    var fold = el.closest ? el.closest('details') : null;
    if (fold) {
      fold.addEventListener('toggle', function () {
        if (!fold.open) return;
        setTimeout(function () {
          map.invalidateSize();
          if (hasPoint) map.setView([ptLat, ptLng], ptZoom);
          else if (homeBounds) map.fitBounds(homeBounds, { padding: [14, 14] });
        }, 60);
      });
    }
  }

  function boot() {
    Array.prototype.forEach.call(document.querySelectorAll('[data-profile-map]'), init);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
