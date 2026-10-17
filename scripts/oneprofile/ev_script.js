<script>
/* The next few events, read live out of calendar.html and data/calendar-events.json,
   the same two sources the calendar itself uses. Each one is checked against the
   clock and not just the date, so an event that started earlier today has
   already dropped off by the evening and the next one has taken its place. */
(function(){
  var ORG=__ORG__, HREF=__HREF__, NAME=__NAME__, LOGO=__LOGO__, ALSO=[], LOC="";
  var slot=document.getElementById('orgEvents'), more=document.getElementById('orgMore');
  if(!slot) return;
  var MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var DAY=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  var AHEAD=4;
  var bust='?_='+Math.floor(Date.now()/60000);
  function esc(v){ return String(v==null?'':v).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  function literal(src, opener, closer){
    var i=src.indexOf(opener); if(i===-1) return null;
    var j=src.indexOf(closer,i); if(j===-1) return null;
    try { return (new Function('return '+src.slice(i+opener.length-1, j+closer.length)))(); } catch(e){ return null; }
  }
  function starts(e){
    var p=String(e.date||'').split('-');
    if(p.length!==3) return null;
    var d=new Date(+p[0], +p[1]-1, +p[2]);
    if(isNaN(d)) return null;
    var m=/^\s*(\d{1,2}):(\d{2})\s*([AaPp])/.exec(e.time||'');
    if(m){ var h=+m[1]%12; if(/[Pp]/.test(m[3])) h+=12; d.setHours(h, +m[2], 0, 0); }
    else { d.setHours(23,59,59,999); }
    return d;
  }
  function label(d, time){
    var t=new Date(); t.setHours(0,0,0,0);
    var days=Math.round((new Date(d.getFullYear(),d.getMonth(),d.getDate())-t)/86400000);
    var w = days===0 ? 'Today' : days===1 ? 'Tomorrow' : DAY[d.getDay()]+', '+MON[d.getMonth()]+' '+d.getDate();
    return w + (time ? ' \u00b7 '+esc(time) : '');
  }
  function empty(msg){
    slot.innerHTML='<div class="evcard"><div class="evkick">Coming up</div><div class="evline">'+msg+' <a href="'+HREF+'" style="color:#fff;font-weight:700">See their calendar</a>.</div></div>';
    more.innerHTML='<a class="evall" href="'+HREF+'">'+esc(NAME)+'</a>';
  }
  Promise.all([
    fetch('/calendar.html'+bust).then(function(r){ return r.ok ? r.text() : ''; }).catch(function(){ return ''; }),
    fetch('/data/calendar-events.json'+bust).then(function(r){ return r.ok ? r.json() : null; }).catch(function(){ return null; })
  ]).then(function(res){
    var src=res[0], live=res[1];
    var EVENTS = src ? literal(src, 'const EVENTS = {', '\n};') : null;
    if(!EVENTS){ empty('The calendar did not load.'); return; }
    var rows=[], seen={};
    function add(date, ev){
      if(!ev || !ev.label) return;
      if(ev.type!==ORG && !ALSO.some(function(a){ return String(ev.label).toLowerCase().indexOf(a.toLowerCase())!==-1; })) return;
      if(LOC && String(ev.location||'').toLowerCase().indexOf(LOC.toLowerCase())===-1) return;
      var k=date+'|'+String(ev.label).replace(/\s+/g,' ').trim().toLowerCase();
      if(seen[k]) return; seen[k]=1;
      rows.push({date:date, title:ev.label, time:ev.time||'', loc:ev.location||'', href:ev.href||'', link:ev.linkText||'', desc:ev.desc||'', flyer:ev.flyer||''});
    }
    Object.keys(EVENTS).forEach(function(d){ (EVENTS[d]||[]).forEach(function(ev){ add(d, ev); }); });
    if(live && Array.isArray(live.events)) live.events.forEach(function(ev){ if(ev && ev.date) add(ev.date, ev); });
    var now=new Date();
    var prog=rows.map(function(e){ e.__at=starts(e); return e; })
      .filter(function(e){ return e.__at && e.__at>now; })
      .sort(function(a,b){ return a.__at-b.__at; });
    if(!prog.length){ empty('Nothing on the calendar right now.'); return; }
    var e=prog[0];
    // The next flyer on their calendar, above the intro, linked to that event (pages that place one by hand keep theirs).
    if(!document.getElementById('orgFlyer')){ var fe=prog.slice(0,AHEAD).filter(function(x){ return x.flyer; })[0]; var intro=document.querySelector('.introsec');
      if(fe && intro){ var slugify=function(s){ return String(s||'').toLowerCase().replace(/[\u2018\u2019']/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,80); };
        var fd=document.createElement('div'); fd.className='sec flyersec'; fd.id='orgFlyer';
        fd.innerHTML='<a href="/calendar.html?event='+esc(fe.date+'-'+slugify(fe.title))+'" style="display:block"><img src="'+esc(fe.flyer)+'" alt="'+esc(fe.title)+'" style="display:block;width:100%;max-width:560px;margin:0 auto;border-radius:10px;box-shadow:0 3px 14px rgba(0,0,0,.18)"></a>';
        intro.parentNode.insertBefore(fd, intro); } }
    var html='<div class="evcard"><div class="evkick">Next up</div>'
      +'<div class="evhead"><span class="evlogo"><img src="'+LOGO+'" alt=""></span><span class="evttl">'+esc(e.title)+'</span></div>'
      +'<div class="evline">\uD83D\uDD52 '+label(e.__at, e.time)+'</div>'
      +(e.loc?'<div class="evline">\uD83D\uDCCD '+esc(e.loc)+'</div>':'')
      +(e.desc?'<div class="evdesc">'+esc(e.desc)+'</div>':'')
      +'<div class="evbtns">'
      +(e.href?'<a class="evbtn" href="'+esc(e.href)+'" target="_blank" rel="noopener">'+esc(e.link||'Details \u2197')+'</a>':'')
      +'<a class="evbtn" href="'+HREF+'">Their full calendar</a></div></div>';
    var rest=prog.slice(1, AHEAD);
    if(rest.length){
      html+='<ul class="evthen">';
      rest.forEach(function(x){
        var row='<span class="ed"><span class="em">'+MON[x.__at.getMonth()]+'</span><span class="en">'+x.__at.getDate()+'</span></span>'
          +'<span class="eb"><span class="et">'+esc(x.title)+'</span><span class="ew">'+label(x.__at, x.time)+'</span></span>';
        html+='<li>'+(x.href ? '<a href="'+esc(x.href)+'" target="_blank" rel="noopener">'+row+'</a>' : row)+'</li>';
      });
      html+='</ul>';
    }
    slot.innerHTML=html;
    var left=prog.length-Math.min(prog.length,AHEAD);
    more.innerHTML = left>0
      ? '<a class="evall" href="'+HREF+'">'+left+' more event'+(left===1?'':'s')+' on their CB6 calendar &rarr;</a>'
      : '<a class="evall" href="'+HREF+'">'+esc(NAME)+' &rarr;</a>';
  }).catch(function(){ empty('The calendar did not load.'); });
})();
</script>