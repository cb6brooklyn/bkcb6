(function(){
'use strict';
var root=document.getElementById('card');if(!root)return;
var slug=root.getAttribute('data-slug'),cd=root.getAttribute('data-cd'),pfx=root.getAttribute('data-pfx')||'bk';
var BNAMES={mn:'Manhattan',bx:'Bronx',bk:'Brooklyn',qn:'Queens',si:'Staten Island'};
var BPATH=(pfx==='bk'?'/block/':'/block/'+pfx+'/');
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
var DAY={Sun:0,Mon:1,Tue:2,Wed:3,Thu:4,Fri:5,Sat:6},DN=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],MO=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function nextDay(daysTxt){var days=(daysTxt||'').split(/[,\/]/).map(function(x){return x.trim();}).filter(function(x){return DAY[x]!=null;});if(!days.length)return '';var t=new Date();t.setHours(0,0,0,0);
  for(var i=0;i<14;i++){var d=new Date(t.getFullYear(),t.getMonth(),t.getDate()+i);if(days.indexOf(DN[d.getDay()].slice(0,3))<0)continue;return i===0?'today':(i===1?'tomorrow':DN[d.getDay()]+', '+MO[d.getMonth()]+' '+d.getDate());}return '';}
function render(D){
  window.BLOCK=D;document.title=D.title+' \u2014 Block Card \u2014 bkcb6.app';
  var cbn=D.cd%100;var BNM=BNAMES[pfx];var h='';
  h+='<div class="top"><div class="crumb"><a href="/">CB6 &amp; Beyond</a> &rsaquo; <a href="/block/">Block cards</a> &rsaquo; <a href="/block/?cd='+D.cd+'">'+BNM+' CB'+cbn+'</a></div><h1>'+esc(D.st)+' <span>between '+esc(D.from)+' and '+esc(D.to)+'</span></h1><div class="nbs">Block card &middot; '+BNM+' Community Board '+cbn+(D.hn?' &middot; '+esc(D.hn):'')+'</div></div>';
  h+='<div class="share"><button type="button" class="sb" id="shareBtn">Share this block</button><button type="button" class="sb alt" id="pdfBtn">One-page PDF</button><button type="button" class="sb alt" id="fridgeBtn">Fridge card</button>'+(D.cd===306?'<a class="sb alt" href="/blocks/#st='+encodeURIComponent(D.st)+'&from='+encodeURIComponent(D.from.split(' & ')[0])+'&to='+encodeURIComponent(D.to.split(' & ')[0])+'&r=75">Everything on this block &rarr;</a>':'')+'</div>';
  h+='<div id="map" data-lines=\''+JSON.stringify(D.lines).replace(/'/g,'&#39;')+'\' data-mid="'+D.mid[0]+','+D.mid[1]+'" data-st="'+esc(D.st)+'" data-from="'+esc(D.from)+'" data-to="'+esc(D.to)+'"></div>';
  // zoning + LPC
  h+='<section class="card"><h2>This block</h2><div class="btns">';
  D.zones.forEach(function(z){h+='<a class="lb" href="/landuse-zoning.html#'+esc(z)+'"><img src="/site-icons/agencies/dcp.png" alt=""><span><i>Zoning</i><b>'+esc(z)+'</b></span></a>';});
  D.hist.forEach(function(hd,i){h+='<a class="lb lpc" href="/landmarks-cb6.html"><img src="/assets/blocks/lpc-seal.png" alt=""><span><i>Historic district, '+esc(D.hist_side[i]||'')+'</i><b>'+esc(hd)+'</b><em>Exterior work on those buildings needs a Landmarks Preservation Commission permit before a DOB permit.</em></span></a>';});
  if(!D.zones.length&&!D.hist.length)h+='<span class="chip muted2">No zoning district on file</span>';
  h+='</div></section>';
  // ASP
  h+='<section class="card"><h2>Alternate side parking</h2>';
  if(!D.asp.length)h+='<p class="muted">No alternate side parking rule in the DOT sign data for this block.</p>';
  else{h+='<div class="signs">';
    var ORD=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];function compact(txt){var ds=(txt||'').split(/[,\/]/).map(function(x){return x.trim();}).filter(function(x){return ORD.indexOf(x)>=0;});ds=ORD.filter(function(x){return ds.indexOf(x)>=0;});if(!ds.length)return '';if(ds.length===1)return DN[(ORD.indexOf(ds[0])+1)%7].toUpperCase();if(ds.length===2)return ds.map(function(x){return x.toUpperCase();}).join(' ');var ix=ds.map(function(x){return ORD.indexOf(x);});var run=ix.every(function(v,i){return i===0||v===ix[i-1]+1;});if(run)return ds[0].toUpperCase()+' - '+ds[ds.length-1].toUpperCase();if(ds.length===6)return 'EXCEPT '+ORD.filter(function(x){return ds.indexOf(x)<0;})[0].toUpperCase();return ds.map(function(x){return x.toUpperCase();}).join(' ');}
  D.asp.forEach(function(a){var m=(a.sched||'').match(/^(.*?),\s*(.*)$/);var day=compact(a.days)||(m?m[1]:a.sched).toUpperCase(),tm=(m?m[2]:'').replace(' to ',' - ');
      h+='<div class="signwrap"><div class="sign"><img src="/assets/blocks/asp-symbol.png" alt=""><div class="st"><div class="tm">'+esc(tm)+'</div><div class="dy">'+esc(day)+'</div><div class="ar">&larr;</div><div class="dept">DEPT OF TRANSPORTATION</div></div><div class="sidetag">'+esc(a.side.toUpperCase())+'</div></div><div class="scap"><b>'+esc(a.side)+'</b> &middot; next '+esc(nextDay(a.days)||'see signs')+'</div></div>';});
    if(D.asp.length===1){var pairs={'North side':'South side','South side':'North side','East side':'West side','West side':'East side'};var o=pairs[D.asp[0].side]||'Other side';
      h+='<div class="signwrap"><div class="sign nosign"><div class="st"><div class="tm">'+esc(o.toUpperCase())+'</div><div class="dy">No rule on file</div><div class="dept">CHECK THE POSTED SIGNS</div></div></div><div class="scap"><b>'+esc(o)+'</b> &middot; no alternate side rule in the DOT sign data for this side</div></div>';}
    h+='</div><p class="muted">From the DOT parking sign database. Confirm on 311 before you move the car.</p>';}
  h+='</section>';
  // pickup
  h+='<section class="card"><h2><img class="h2i" src="/site-icons/agencies/dsny.png" alt="">Trash and recycling</h2>';
  if(!D.dsny.length)h+='<p class="muted">No DSNY residential schedule on file here.</p>';
  if(D.byday.length){h+='<div class="byday">';D.byday.forEach(function(r){h+='<div class="bd"><b>'+esc(r[0])+'</b><span>'+esc(r[1].join(', '))+'</span></div>';});h+='</div>';}
  D.dsny.forEach(function(d,i){h+='<div class="pick">';
    [['dsny-trash','Trash',d.refuse,d.refuse_d],['dsny-recycle','Recycling',d.recycling,d.recycling_d],['dsny-compost','Compost',d.organics,d.organics_d],['dsny-truck','Bulk items',d.bulk,'']].forEach(function(t){h+='<div class="pk"><img src="/assets/blocks/'+t[0]+'.png" alt=""><i>'+t[1]+'</i><b>'+esc(t[2])+'</b>'+(t[3]?'<em>next '+esc(nextDay(t[3]))+'</em>':'')+'</div>';});
    h+='</div><p class="muted">DSNY section '+esc(d.section)+'. Set out after 6 PM the evening before, or 8 PM in a bin. Bins are required for trash.'+(D.dsny.length>1&&i===0?' This block crosses two sanitation sections; the second schedule follows.':'')+'</p>';});
  h+='</section>';
  // voting
  h+='<section class="card"><h2><img class="h2i" src="/site-icons/agencies/boe.png" alt="">Voting</h2>';
  h+='<div class="row"><div class="k">Next election</div><div class="v"><b>Tuesday, November 3, 2026</b><div class="sm">Early voting October 24 to November 1. Election Day polls open 6 AM to 9 PM.</div></div></div>';
  h+='<div class="row"><div class="k">On that ballot for this block</div><div class="v"><div class="sm">'+esc(D.ballot26.join('; '))+'. Plus statewide: Governor, Lieutenant Governor, Attorney General, State Comptroller.</div></div></div>';
  D.eds.forEach(function(e){h+='<div class="row"><div class="k">Election district</div><div class="v"><b>AD '+e.ad+', ED '+e.ed+'</b>'+(D.eds.length>1?' <span class="sm">(this block spans more than one)</span>':'')+'</div></div>';
    if(e.site)h+='<div class="row"><div class="k">Election Day poll site</div><div class="v"><b>'+esc(e.site[0])+'</b><div class="sm">'+esc(e.site[1])+(e.site[4]?' &middot; '+esc(e.site[4]):'')+'</div></div></div>';
    if(e.early)h+='<div class="row"><div class="k">Early voting site</div><div class="v"><b>'+esc(e.early[0])+'</b><div class="sm">'+esc(e.early[1])+'</div></div></div>';});
  h+='<p class="muted">Poll sites from the NYC Board of Elections. Confirm at <a href="https://findmypollsite.vote.nyc" target="_blank" rel="noopener">findmypollsite.vote.nyc</a>.</p></section>';
  // tiles
  h+='<section class="card"><h2>Who this block turns to</h2><div class="tiles">';
  D.ents.forEach(function(e){h+='<a class="tile" href="'+esc(e.url)+'"'+(/^http/.test(e.url)?' target="_blank" rel="noopener"':'')+'><i>'+esc(e.k)+'</i><img src="'+esc(e.logo)+'" alt="" onerror="this.style.visibility=\'hidden\'"><b>'+esc(e.name)+'</b><em>'+e.lines.filter(Boolean).map(esc).join('<br>')+'</em></a>';});
  h+='</div></section>';
  h+='<section class="card"><a class="lb" href="https://portal.311.nyc.gov" target="_blank" rel="noopener"><img src="/site-icons/agencies/311.png" alt=""><span><i>Report it</i><b>Call 311</b><em>Noise, sanitation, street conditions, heat and hot water, and anything else the city handles.</em></span></a></section>';
  h+='<div class="foot">Built from the DOT street centerline, DOT parking signs, DSNY collection frequencies, NYC Board of Elections poll sites, PLUTO zoning, and the district boundary files on this site. Every fact here is placed by this block\u2019s own coordinates. Rebuilt '+esc(D.built)+'. Questions or a correction: <a href="mailto:Mike@bkcb6.org">Mike Racioppo</a></div>';
  h+='<div class="nav"><a href="/block/">&#128203; All block cards</a><a href="/november2026.html">&#128499; Where do I vote</a><a href="/sanitation-hub.html">&#128465; Sanitation</a>'+(D.cd===306?'<a href="/blocks/">&#128205; Block Finder</a>':'')+'</div>';
  root.innerHTML=h;
  ['/assets/blocks/block-card.js','/assets/blocks/block-pdf.js'].forEach(function(src){var s=document.createElement('script');s.src=src;document.body.appendChild(s);});
}
fetch('/assets/blocks/'+pfx+'/'+cd+'.json').then(function(r){return r.json();}).then(function(j){var D=j.blocks[slug];if(!D){root.innerHTML='<div class="empty">No card for this block.</div>';return;}D.near=(D.near||[]).map(function(i){return j.segs[i];});render(D);}).catch(function(){root.innerHTML='<div class="empty">Could not load this block.</div>';});
})();
