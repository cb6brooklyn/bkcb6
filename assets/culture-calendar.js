/* Calendar section on the culture profile pages at /c/.
   A culture place earns events two ways: its name matches an organization on
   the community calendar, or an event names it as the location. Both are
   resolved against the live calendar so a new event at a venue turns up on
   that venue's page without anything being regenerated here.
   The page sets window.PLACE = {name, slug} before loading this file. */
(function(){
  var bust = '?_=' + Math.floor(Date.now() / 60000);

  function norm(s){
    return String(s == null ? '' : s).toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
  }
  function literal(src, opener, closer){
    var i = src.indexOf(opener); if(i === -1) return null;
    var j = src.indexOf(closer, i); if(j === -1) return null;
    try { return (new Function('return ' + src.slice(i + opener.length - 1, j + closer.length)))(); }
    catch(e){ return null; }
  }

  function boot(){
    var host = document.getElementById('c-cal');
    if(!host || !window.PLACE) return;
    Promise.all([
      fetch('/calendar.html' + bust).then(function(r){ return r.ok ? r.text() : ''; }).catch(function(){ return ''; }),
      fetch('/data/calendar-events.json' + bust).then(function(r){ return r.ok ? r.json() : null; }).catch(function(){ return null; }),
      fetch('/data/culture-events.json' + bust).then(function(r){ return r.ok ? r.json() : null; }).catch(function(){ return null; })
    ]).then(function(res){
      var src = res[0], live = res[1], own = res[2];
      // What the venue itself publishes, scraped from its own listings page.
      var ownRows = [];
      if(own && own[window.PLACE.name]) own[window.PLACE.name].forEach(function(e){
        if(!e || !e.date || !e.title) return;
        ownRows.push({ key: e.date, ev: { label: e.title, time: e.time || '',
          location: window.PLACE.name, href: e.url || '', type: 'venue' } });
      });
      var EVENTS = src ? literal(src, 'const EVENTS = {', '\n};') : null;
      if(!EVENTS){
        window.renderProfileCalendar(host, ownRows, { name: window.PLACE.name });
        return;
      }
      // Same merge the calendar itself applies to the daily overlay.
      var supSet = new Set(literal(src, 'const SUPPRESSED_LIVE = new Set([', '\n]);') || []);
      if(live && Array.isArray(live.events)) live.events.forEach(function(ev){
        if(!ev || !ev.date) return;
        if(supSet.has(ev.date + '|' + (ev.label||'').replace(/\s+/g,' ').trim())) return;
        if(typeof ev.label === 'string' && /^Early Voting\s+\u2014/.test(ev.label)) return;
        if(!EVENTS[ev.date]) EVENTS[ev.date] = [];
        var day = EVENTS[ev.date];
        if(day.some(function(e){ return e._hardcoded && norm(e.label) === norm(ev.label); })) return;
        var idx = day.findIndex(function(e){ return e.type === ev.type && e._hardcoded; });
        if(idx !== -1) day[idx] = ev;
        else if(!day.some(function(e){ return e.type === ev.type && !e._hardcoded; })) day.push(ev);
      });

      // Does this place run its own organization on the calendar?
      var org = null;
      var sel = src.match(/id="list-org-filter"[\s\S]*?<\/select>/);
      if(sel){
        var re = /<option value="([^"]+)"[^>]*>([\s\S]*?)<\/option>/g, m, want = norm(window.PLACE.name);
        while((m = re.exec(sel[0]))) if(norm(m[2]) === want){ org = m[1]; break; }
      }

      var needle = norm(window.PLACE.name);
      var rows = [], seen = new Set();
      Object.keys(EVENTS).forEach(function(key){
        (EVENTS[key] || []).forEach(function(ev){
          if(!ev || !ev.label) return;
          var mine = org ? ev.type === org : (needle.length >= 8 && norm(ev.location).indexOf(needle) !== -1);
          if(!mine) return;
          var k = key + '|' + norm(ev.label);
          if(seen.has(k)) return;
          seen.add(k);
          rows.push({ key: key, ev: ev });
        });
      });

      ownRows.forEach(function(r){
        var k = r.key + '|' + norm(r.ev.label);
        if(seen.has(k)) return;
        seen.add(k); rows.push(r);
      });

      window.renderProfileCalendar(host, rows, {
        name: window.PLACE.name,
        calendarHref: org ? ('/calendar.html?org=' + encodeURIComponent(org)) : '/calendar.html'
      });
      if(org){
        var more = document.getElementById('c-cal-more');
        if(more) more.insertAdjacentHTML('afterbegin', '<a class="chip" href="/o/' + encodeURIComponent(org) +
          '.html">All ' + rows.length + ' listings on its page</a>');
      }
    }).catch(function(){
      window.renderProfileCalendar(host, [], { name: window.PLACE.name });
    });
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
