/* CB6 Beyond - Find My Community Board (GPS + local PIP) */
(function(){
  var btn = document.getElementById("find-cb-btn");
  var status = document.getElementById("find-cb-status");
  if (!btn || !status) return;

  var BORO_BY_FIRST_DIGIT = {
    "1": { slug: "manhattan",    name: "Manhattan" },
    "2": { slug: "bronx",        name: "The Bronx" },
    "3": { slug: "brooklyn",     name: "Brooklyn" },
    "4": { slug: "queens",       name: "Queens" },
    "5": { slug: "statenisland", name: "Staten Island" }
  };

  function setStatus(text, isError){
    status.textContent = text;
    status.classList.toggle("is-error", !!isError);
  }
  function setStatusHTML(html){
    status.innerHTML = html;
    status.classList.remove("is-error");
  }

  function routeToCB(communityDistrict){
    if (!communityDistrict || String(communityDistrict).length !== 3) {
      setStatus("Could not determine your Community Board.", true);
      return;
    }
    var cd = String(communityDistrict);
    var boro = BORO_BY_FIRST_DIGIT[cd[0]];
    var cbNum = parseInt(cd.substring(1), 10).toString();
    if (!boro || !cbNum) {
      setStatus("Could not determine your Community Board.", true);
      return;
    }
    var slugMap = { manhattan:"mn", bronx:"bx", brooklyn:"bk", queens:"qn", statenisland:"si" };
    var page = "cb-" + slugMap[boro.slug] + "-" + cbNum + ".html";
    setStatusHTML("Found you in <strong>" + boro.name + " CB " + cbNum + "</strong> \u2014 loading...");
    setTimeout(function(){ window.location.href = page; }, 500);
  }

  /* Ray-casting point-in-polygon for a single ring (array of [lng, lat]) */
  function pointInRing(px, py, ring){
    var inside = false;
    for (var i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      var xi = ring[i][0], yi = ring[i][1];
      var xj = ring[j][0], yj = ring[j][1];
      if (((yi > py) !== (yj > py)) && (px < (xj - xi) * (py - yi) / (yj - yi) + xi)) {
        inside = !inside;
      }
    }
    return inside;
  }

  /* Works for Polygon and MultiPolygon */
  function pointInFeature(px, py, feature){
    var geom = feature.geometry;
    if (!geom) return false;
    var polys = geom.type === "MultiPolygon" ? geom.coordinates : [geom.coordinates];
    for (var p = 0; p < polys.length; p++) {
      var rings = polys[p];
      if (pointInRing(px, py, rings[0])) {
        var inHole = false;
        for (var h = 1; h < rings.length; h++) {
          if (pointInRing(px, py, rings[h])) { inHole = true; break; }
        }
        if (!inHole) return true;
      }
    }
    return false;
  }

  function findCDFromGeoJSON(lng, lat, features){
    for (var i = 0; i < features.length; i++) {
      if (pointInFeature(lng, lat, features[i])) {
        return features[i].properties.boro_cd;
      }
    }
    return null;
  }

  btn.addEventListener("click", function(){
    if (!("geolocation" in navigator)) {
      setStatus("Location services are not supported on this device.", true);
      return;
    }
    btn.classList.add("is-loading");
    btn.disabled = true;
    setStatus("Getting your location...");

    navigator.geolocation.getCurrentPosition(function(pos){
      var lat = pos.coords.latitude;
      var lng = pos.coords.longitude;
      setStatus("Looking up your Community Board...");

      fetch("community-district-boundaries.geojson")
        .then(function(r){ return r.json(); })
        .then(function(j){
          var cd = findCDFromGeoJSON(lng, lat, j.features || []);
          btn.classList.remove("is-loading");
          btn.disabled = false;
          if (!cd) {
            setStatus("Could not find a Community Board for your location. Try entering an address instead.", true);
            return;
          }
          routeToCB(cd);
        })
        .catch(function(){
          btn.classList.remove("is-loading");
          btn.disabled = false;
          setStatus("Lookup failed. Check your connection and try again.", true);
        });

    }, function(err){
      btn.classList.remove("is-loading");
      btn.disabled = false;
      if (err.code === 1) {
        setStatus("Location permission denied. Enable it in Settings to use this feature.", true);
      } else if (err.code === 2) {
        setStatus("Could not determine your location. Try again outdoors or with better signal.", true);
      } else if (err.code === 3) {
        setStatus("Location request timed out. Try again.", true);
      } else {
        setStatus("Could not get your location.", true);
      }
    }, {
      enableHighAccuracy: true,
      timeout: 15000,
      maximumAge: 0
    });
  });
})();
