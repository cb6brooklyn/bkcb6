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
    senate: { label: 'Senate districts', folder: 'senate', color: '#0f766e', count: 28 }
  };
  var ZONE_FILL = {
    R: '#56B4E9', C: '#E69F00', M: '#D55E00', P: '#009E73', X: '#CC79A7', O: '#999999'
  };

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

  function init(el) {
    if (typeof L === 'undefined' || !el || el.dataset.profileMapReady === 'true') return;
    el.dataset.profileMapReady = 'true';

    var chamber = el.getAttribute('data-chamber') || 'council';
    var district = String(el.getAttribute('data-district') || '');
    var self = CHAMBERS[chamber];
    if (!self) return;

    var map = L.map(el, { scrollWheelZoom: false, zoomControl: true });
    // CARTO now watermarks unkeyed tiles, so use Esri's keyless light canvas
    L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19, attribution: 'Esri, HERE, Garmin, &copy; OpenStreetMap contributors'
    }).addTo(map);
    L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19, opacity: 0.9
    }).addTo(map);

    var homeBounds = null;
    var pin = null;
    var layers = {};
    var status = el.parentNode.querySelector('[data-map-status]');

    function say(msg) { if (status) status.textContent = msg || ''; }

    // ---- the member's own district ----
    getJSON('/data/districts/' + self.folder + '-' + district + '.geojson').then(function (g) {
      var own = L.geoJSON(g, {
        style: { color: self.color, weight: 2.5, fillColor: '#f47920', fillOpacity: 0.14 }
      }).addTo(map);
      homeBounds = own.getBounds();
      map.fitBounds(homeBounds, { padding: [14, 14] });
      own.bringToBack();
    }).catch(function () { map.setView([40.70, -73.95], 11); });

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
          for (var i = 1; i <= c.count; i++) {
            jobs.push(getJSON('/data/districts/' + c.folder + '-' + i + '.geojson')
              .catch(function () { return null; }));
          }
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
              lyr.bindTooltip(c.label.replace(' districts', '') + ' District ' + num, { sticky: true });
              group.addLayer(lyr);
            });
            say('');
          });
        }
      };
    }

    ['council', 'assembly', 'senate'].forEach(function (k) {
      if (k === chamber) return;
      layers['overlap-' + k] = overlapLayer(k);
    });

    // ---- zoning, live from City Planning ----
    layers.zoning = (function () {
      var group = L.layerGroup();
      var done = false;
      return {
        group: group,
        load: function () {
          if (done) return Promise.resolve();
          done = true;
          say('Loading zoning\u2026');
          return arcQuery('nyzd', 'ZONEDIST', map.getBounds(), 2000).then(function (g) {
            L.geoJSON(g, {
              style: function (f) {
                var fam = zoneFamily(f.properties.ZONEDIST);
                return { color: ZONE_FILL[fam], weight: 0.6, fillColor: ZONE_FILL[fam], fillOpacity: 0.42 };
              },
              onEachFeature: function (f, l) { l.bindTooltip(f.properties.ZONEDIST || 'Zoning', { sticky: true }); }
            }).addTo(group);
            say('');
          }).catch(function () { say('Zoning did not load at this zoom.'); });
        }
      };
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

    // ---- toggles ----
    var toggleWrap = el.parentNode.querySelector('[data-map-toggles]');
    function addToggle(key, label) {
      if (!toggleWrap || !layers[key]) return;
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'mtog';
      b.textContent = label;
      b.addEventListener('click', function () {
        var on = b.classList.toggle('on');
        if (on) {
          Promise.resolve(layers[key].load()).then(function () {
            if (b.classList.contains('on')) layers[key].group.addTo(map);
          });
        } else {
          map.removeLayer(layers[key].group);
        }
      });
      toggleWrap.appendChild(b);
    }
    ['council', 'assembly', 'senate'].forEach(function (k) {
      if (k === chamber) return;
      addToggle('overlap-' + k, 'Overlapping ' + CHAMBERS[k].label.toLowerCase());
    });
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

    setTimeout(function () { map.invalidateSize(); }, 300);
  }

  function boot() {
    Array.prototype.forEach.call(document.querySelectorAll('[data-profile-map]'), init);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
