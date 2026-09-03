/* Organization profile pages at /o/<slug>.html.
   Events are read live out of calendar.html plus data/calendar-events.json, the
   same two sources the calendar itself uses, so a profile page can never drift
   from the calendar. Nothing here needs regenerating when the calendar changes.
   The page sets ORG, ORG_NAME and ORG_LOGO before loading this file. */
(function(){
  var MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var DOW = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  var bust = '?_=' + Math.floor(Date.now() / 60000);

  function esc(s){
    return String(s == null ? '' : s)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;');
  }
  function slugify(str){
    return String(str||'').toLowerCase()
      .replace(/[\u2018\u2019']/g,'')
      .replace(/[^a-z0-9]+/g,'-')
      .replace(/^-+|-+$/g,'')
      .slice(0,80);
  }
  // Pull a top-level object/array literal out of calendar.html by name and
  // evaluate it. Both literals end on a line of their own, so the first
  // newline-anchored terminator after the opening is the right one.
  function literal(src, opener, closer){
    var i = src.indexOf(opener);
    if(i === -1) return null;
    var j = src.indexOf(closer, i);
    if(j === -1) return null;
    var body = src.slice(i + opener.length - 1, j + closer.length);
    try { return (new Function('return ' + body))(); } catch(e){ return null; }
  }

  function mergeLive(EVENTS, live, suppressed){
    var norm = function(s){ return (s||'').replace(/\s+/g,' ').trim().toLowerCase(); };
    live.forEach(function(ev){
      if(!ev || !ev.date) return;
      if(suppressed.has(ev.date + '|' + (ev.label||'').replace(/\s+/g,' ').trim())) return;
      if(typeof ev.label === 'string' && /^Early Voting\s+\u2014/.test(ev.label)) return;
      if(!EVENTS[ev.date]) EVENTS[ev.date] = [];
      var day = EVENTS[ev.date];
      if(day.some(function(e){ return e._hardcoded && norm(e.label) === norm(ev.label); })) return;
      var idx = day.findIndex(function(e){ return e.type === ev.type && e._hardcoded; });
      if(idx !== -1) day[idx] = ev;
      else if(!day.some(function(e){ return e.type === ev.type && !e._hardcoded; })) day.push(ev);
    });
  }

  function card(key, ev){
    var d = new Date(key + 'T00:00:00');
    var time = ev.time || ((ev.type === 'board' || ev.type === 'committee') ? '6:30 PM' : '');
    var meta = [];
    if(time) meta.push('<span>' + esc(time) + '</span>');
    if(ev.location) meta.push('<span>' + esc(ev.location) + '</span>');
    var desc = '';
    if(ev.desc){
      var t = String(ev.desc).replace(/\s+/g,' ').trim();
      if(t.length > 320) t = t.slice(0, 317).replace(/\s+\S*$/,'') + '\u2026';
      desc = '<div class="evx">' + esc(t) + '</div>';
    }
    // A civic listing only exists on the calendar once its source is switched
    // on, so the deep link carries that source with it.
    var civicKey = { nyccouncil:'council', bkcbs:'bkcbs', bpall:'bp', hearing:'hearing', deadline:'deadline' }[ev.type];
    var acts = ['<a class="hot" href="/calendar.html?' + (civicKey ? 'civic=' + civicKey + '&' : '') +
                'event=' + encodeURIComponent(key + '-' + slugify(ev.label)) +
                '">On the calendar</a>'];
    if(ev.href) acts.push('<a href="' + esc(ev.href) + '" target="_blank" rel="noopener noreferrer">' +
                          esc(ev.linkText || 'Full details') + ' \u2197</a>');
    (ev.links || []).forEach(function(l){
      if(l && l.href) acts.push('<a href="' + esc(l.href) + '" target="_blank" rel="noopener noreferrer">' + esc(l.text || 'Link') + ' \u2197</a>');
    });
    return '<li class="evc">' +
      '<div class="evd"><div class="m">' + MON[d.getMonth()] + '</div>' +
      '<div class="d">' + d.getDate() + '</div>' +
      '<div class="w">' + DOW[d.getDay()] + '</div></div>' +
      '<div class="evb"><div class="evt">' + esc(ev.label) + '</div>' +
      (meta.length ? '<div class="evm">' + meta.join('') + '</div>' : '') +
      desc +
      '<div class="eva">' + acts.join('') + '</div></div></li>';
  }

  function render(rows){
    var todayKey = (function(){
      var n = new Date(), p = function(x){ return String(x).padStart(2,'0'); };
      return n.getFullYear() + '-' + p(n.getMonth()+1) + '-' + p(n.getDate());
    })();
    var upcoming = rows.filter(function(r){ return r.key >= todayKey; });
    var past = rows.filter(function(r){ return r.key < todayKey; }).reverse();

    var up = document.getElementById('o-upcoming');
    var upN = document.getElementById('o-upcoming-n');
    if(upcoming.length){
      up.innerHTML = '<ul class="evl">' + upcoming.map(function(r){ return card(r.key, r.ev); }).join('') + '</ul>';
      upN.textContent = upcoming.length + (upcoming.length === 1 ? ' event' : ' events');
    } else {
      up.innerHTML = '<div class="oempty">No upcoming ' + esc(window.ORG_NAME) +
        ' events are on the calendar right now.' + (past.length ? ' Past events are listed below.' : '') + '</div>';
      upN.textContent = 'none scheduled';
    }

    var pastWrap = document.getElementById('o-past-sec');
    if(past.length){
      document.getElementById('o-past-sum').textContent = 'See ' + past.length + ' past ' +
        (past.length === 1 ? 'event' : 'events');
      document.getElementById('o-past').innerHTML =
        past.map(function(r){ return card(r.key, r.ev); }).join('');
    } else {
      pastWrap.style.display = 'none';
    }

    var tot = document.getElementById('o-total');
    if(tot) tot.textContent = rows.length + (rows.length === 1 ? ' listing' : ' listings') +
      ' on the CB6 community calendar';
  }

  function fail(msg){
    document.getElementById('o-upcoming').innerHTML =
      '<div class="oempty">' + esc(msg) + ' <a href="/calendar.html?org=' +
      encodeURIComponent(window.ORG) + '">Open this organization on the calendar</a>.</div>';
    document.getElementById('o-upcoming-n').textContent = '';
    document.getElementById('o-past-sec').style.display = 'none';
  }

  // The citywide civic layer is off by default on the calendar itself, but a
  // profile page for one of those bodies exists to show its meetings, so the
  // matching feed is always loaded here. Transforms mirror civicLoad() in
  // calendar.html so labels and links read identically on both pages.
  var CIVIC = {
    nyccouncil: 'council', bkcbs: 'brooklyn-cbs', bpall: 'bp',
    hearing: 'hearings', deadline: 'hearings'
  };
  function civicAdd(EVENTS, key, ev){
    if(!key) return;
    if(!EVENTS[key]) EVENTS[key] = [];
    var norm = function(t){ return (t||'').replace(/\s+/g,' ').trim().toLowerCase(); };
    if(EVENTS[key].some(function(e){ return norm(e.label) === norm(ev.label) && e.type === ev.type; })) return;
    EVENTS[key].push(ev);
  }
  function mergeCivic(EVENTS, org, data){
    if(!data) return;
    if(org === 'nyccouncil' && data.events){
      Object.keys(data.events).forEach(function(d){
        data.events[d].forEach(function(e){
          civicAdd(EVENTS, d, { type:'nyccouncil', label:'NYC Council: ' + e.label,
            time:e.time || null, location:e.location || null, href:e.href || null,
            linkText:e.href ? 'Meeting details' : null,
            desc:e.status ? ('Status: ' + e.status + '.') : null });
        });
      });
    } else if(org === 'bkcbs' && data.boards){
      Object.keys(data.boards).forEach(function(k){
        var b = data.boards[k];
        (b.events || []).forEach(function(e){
          civicAdd(EVENTS, e.date, { type:'bkcbs', label:'Brooklyn CB' + b.cb + ': ' + e.label,
            time:e.time || null, location:e.location || null, href:e.href || null,
            linkText:e.linkText || null,
            desc:e.source === 'standing'
              ? ('Standing schedule: ' + e.rule + '. Confirm with the board before attending.')
              : null });
        });
      });
    } else if(org === 'bpall' && data.boroughs){
      Object.keys(data.boroughs).forEach(function(k){
        (data.boroughs[k].events || []).forEach(function(e){
          civicAdd(EVENTS, e.date, { type:'bpall', label:e.borough + ' BP: ' + e.label,
            time:e.time || null, href:e.href || null, linkText:e.linkText || 'Notice' });
        });
      });
    } else if((org === 'hearing' || org === 'deadline') && data.events){
      var want = (org === 'hearing') ? 'hearing' : 'comment-deadline';
      Object.keys(data.events).forEach(function(d){
        data.events[d].forEach(function(e){
          if((e.kind || 'hearing') !== want) return;
          civicAdd(EVENTS, d, { type:org, label:e.agency + ': ' + e.label,
            time:e.time || null, href:e.href || null, linkText:e.linkText || 'Notice',
            desc:e.section || null });
        });
      });
    }
  }

  function boot(){
    var civicFile = CIVIC[window.ORG];
    Promise.all([
      fetch('/calendar.html' + bust).then(function(r){ return r.ok ? r.text() : ''; }).catch(function(){ return ''; }),
      fetch('/data/calendar-events.json' + bust).then(function(r){ return r.ok ? r.json() : null; }).catch(function(){ return null; }),
      civicFile
        ? fetch('/data/civic-calendar/' + civicFile + '.json' + bust).then(function(r){ return r.ok ? r.json() : null; }).catch(function(){ return null; })
        : Promise.resolve(null)
    ]).then(function(res){
      var src = res[0], live = res[1], civic = res[2];
      var EVENTS = src ? literal(src, 'const EVENTS = {', '\n};') : null;
      if(!EVENTS){ fail('The calendar could not be read from here.'); return; }
      var suppressed = (src ? literal(src, 'const SUPPRESSED_LIVE = new Set([', '\n]);') : null) || [];
      var supSet = new Set(suppressed);
      if(live && Array.isArray(live.events)) mergeLive(EVENTS, live.events, supSet);
      if(civic) mergeCivic(EVENTS, window.ORG, civic);

      var rows = [], seen = new Set();
      Object.keys(EVENTS).sort().forEach(function(key){
        (EVENTS[key] || []).forEach(function(ev){
          if(!ev || ev.type !== window.ORG || !ev.label) return;
          var k = key + '|' + ev.label.replace(/\s+/g,' ').trim().toLowerCase();
          if(seen.has(k)) return;
          seen.add(k);
          rows.push({ key: key, ev: ev });
        });
      });
      render(rows);
    }).catch(function(){ fail('The calendar could not be read from here.'); });
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
