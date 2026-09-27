/* Map point icons for the BQE pages: each point looks like what it is (311, NYPD, crash, DOT count), sized by count. */
(function(){
var CR=function(c){return '<svg viewBox="0 0 32 32" width="100%" height="100%" aria-hidden="true"><circle cx="16" cy="16" r="15" fill="#fff" stroke="'+c+'" stroke-width="2"/><path d="M16 4l2.6 5.4 5.6-2.2-2.3 5.6 5.7 2.4-5.7 2.3 2.3 5.7-5.7-2.3L16 28l-2.5-5.4-5.7 2.3 2.3-5.7L4.4 17l5.7-2.4-2.3-5.6 5.6 2.2z" fill="'+c+'"/><circle cx="16" cy="16" r="3.1" fill="#fff"/></svg>';};
var PK='<svg viewBox="0 0 32 32" width="100%" height="100%" aria-hidden="true"><circle cx="16" cy="16" r="14" fill="#fff" stroke="#475569" stroke-width="3"/><text x="16" y="22.5" text-anchor="middle" font-family="DM Sans,sans-serif" font-size="18" font-weight="700" fill="#475569">P</text><path d="M6 26L26 6" stroke="#475569" stroke-width="3.4" stroke-linecap="round"/></svg>';
var RING=function(img,c,sq){return '<span class="kmk-in'+(sq?' sq':'')+'" style="--rc:'+c+'"><img src="'+img+'" alt=""></span>';};
var KI={
  c311:{h:RING('/assets/agency-logos/311.png','#b91c1c',1),t:'311 truck route complaint'},
  t413:{h:RING('/assets/map-icons/nypd-patch.png','#1d4ed8'),t:'NYPD truck route ticket'},
  t385:{h:RING('/assets/map-icons/nypd-patch.png','#a16207'),t:'NYPD size and weight ticket'},
  crk:{h:CR('#7f1d1d'),svg:1},cri:{h:CR('#ea580c'),svg:1},crn:{h:CR('#94a3b8'),svg:1},crh:{h:CR('#6b7280'),svg:1},
  cpk:{h:PK,svg:1},
  cntr:{h:RING('/assets/permit-icons/dot-logo.png','#be123c'),t:'DOT count'},
  cntn:{h:RING('/assets/permit-icons/dot-logo.png','#0d1b4b'),t:'DOT count'},
  cnts:{h:RING('/assets/permit-icons/dot-logo.png','#64748b'),t:'DOT count'},
  citi:{h:'<span class="kmk-in sq" style="--rc:#0369a1"><img src="/assets/map-icons/citibike.png" alt="" style="width:100%;height:100%"></span>'}
};
window.KICONS=KI;
function kind(o){var c=String(o.fillColor||'').toLowerCase(),s=String(o.color||'').toLowerCase();
  if(c==='#b91c1c')return 'c311';if(c==='#1d4ed8')return 't413';if(c==='#a16207')return 't385';
  if(c==='#7f1d1d')return 'crk';if(c==='#ea580c')return 'cri';if(c==='#94a3b8')return 'crn';if(c==='#9ca3af')return 'crh';
  if(c==='#475569')return 'cpk';
  if(c==='#fff'||c==='#ffffff'){if(s==='#be123c')return 'cntr';if(s==='#0d1b4b')return 'cntn';if(s==='#64748b')return 'cnts';}
  return null;}
window.kIcon=function(k,px){var d=KI[k];return L.divIcon({className:'kmk',html:d.svg?'<span class="kmk-svg">'+d.h+'</span>':d.h,iconSize:[px,px],iconAnchor:[px/2,px/2],popupAnchor:[0,-px/2],tooltipAnchor:[px/2,0]});};
window.kMark=function(ll,o){o=o||{};var k=kind(o);if(!k)return L.circleMarker(ll,o);
  var r=o.radius||5,px=Math.max(18,Math.min(46,Math.round(r*2.3)+8));if(k.indexOf('cnt')===0)px=Math.max(14,Math.round(r*2)+6);
  return L.marker(ll,{pane:o.pane||'markerPane',icon:kIcon(k,px),keyboard:false,riseOnHover:true});};
/* legend and toggle swatches: the same icons */
var SW={'#b91c1c':'c311','#1d4ed8':'t413','#a16207':'t385','#7f1d1d':'crk','#9ca3af':'crh','#475569':'cpk','#0369a1':'citi'};
function hex(bg){bg=String(bg||'').trim().toLowerCase();var m=bg.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);if(m)return '#'+[1,2,3].map(function(i){return ('0'+(+m[i]).toString(16)).slice(-2);}).join('');return bg;}
window.kSwapSwatches=function(root){(root||document).querySelectorAll('i.sw.dot,span.ld').forEach(function(el){if(el.dataset.kic)return;var k=SW[hex(el.style.background||el.style.backgroundColor)];if(!k)return;var d=KI[k];
  var s=document.createElement('span');s.className='kmk kmk-sw';s.dataset.kic=k;s.innerHTML=d.svg?'<span class="kmk-svg">'+d.h+'</span>':d.h;el.replaceWith(s);});};
/* neighborhood labels that would sit on top of each other: keep the first */
var NBB=[];
window.kNbReset=function(){NBB=[];try{if(typeof boundFeatures!=='undefined'&&boundFeatures['306']&&typeof map!=='undefined'){var p=boundFeatures['306'].properties,pt=map.latLngToContainerPoint([p.ly,p.lx]);NBB.push([pt.x-40,pt.y-40,pt.x+40,pt.y+40]);}}catch(e){}};
window.kNbOk=function(ll,txt){if(typeof map==='undefined')return true;var p=map.latLngToContainerPoint(ll),w=String(txt||'').length*6.4+10,h=18,b=[p.x-w/2,p.y-h/2,p.x+w/2,p.y+h/2];
  for(var i=0;i<NBB.length;i++){var o=NBB[i];if(b[0]<o[2]&&b[2]>o[0]&&b[1]<o[3]&&b[3]>o[1])return false;}NBB.push(b);return true;};
/* community board labels with their logos */
window.kCdLab=function(lbl){var m=String(lbl||'').match(/^BKCB(\d+)$/);if(!m||+m[1]>18)return String(lbl||'').replace(/[&<>]/g,'');return '<span class="kcdl"><img src="/elected/CB'+m[1]+'_540.png" alt="">'+lbl+'</span>';};
})();
