/* CB6 Beyond - Find My Community Board (GPS) */
(function(){
  var GEOCLIENT_KEY = "b913bdfb9c47466589d0f08c99c75b21";
  var btn = document.getElementById("find-cb-btn");
  var status = document.getElementById("find-cb-status");
  if (!btn || !status) return;

  var BORO_BY_FIRST_DIGIT = {
    "1": { slug: "manhattan",     name: "Manhattan" },
    "2": { slug: "bronx",         name: "The Bronx" },
    "3": { slug: "brooklyn",      name: "Brooklyn" },
    "4": { slug: "queens",        name: "Queens" },
    "5": { slug: "statenisland",  name: "Staten Island" }
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
    if (!communityDistrict || communityDistrict.length !== 3) {
      setStatus("Could not determine your Community Board.", true);
      return;
    }
    var boro = BORO_BY_FIRST_DIGIT[communityDistrict[0]];
    var cbNum = parseInt(communityDistrict.substring(1), 10).toString();
    if (!boro || !cbNum) {
      setStatus("Could not determine your Community Board.", true);
      return;
    }
    var slugMap = { manhattan:"mn", bronx:"bx", brooklyn:"bk", queens:"qn", statenisland:"si" };
    var page = "cb-" + slugMap[boro.slug] + "-" + cbNum + ".html";
    setStatusHTML("Found you in <strong>" + boro.name + " CB " + cbNum + "</strong> - loading...");
    setTimeout(function(){ window.location.href = page; }, 500);
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

      var url = "https://api.cityofnewyork.us/geoclient/v2/search.json?input=" +
                encodeURIComponent(lat + "," + lng) +
                "&app_key=" + GEOCLIENT_KEY;

      fetch(url).then(function(r){ return r.json(); }).then(function(j){
        var result = j && j.results && j.results[0] && j.results[0].response;
        var cd = result && (result.communityDistrict || result.cd);
        if (!cd) {
          setStatus("Could not find a Community Board for your location. Try entering an address instead.", true);
          btn.classList.remove("is-loading");
          btn.disabled = false;
          return;
        }
        routeToCB(cd);
      }).catch(function(){
        setStatus("Lookup failed. Check your connection and try again.", true);
        btn.classList.remove("is-loading");
        btn.disabled = false;
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
