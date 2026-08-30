(function(){
'use strict';
var el=document.getElementById('map');
if(el){
  var css=document.createElement('link');css.rel='stylesheet';css.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';document.head.appendChild(css);
  var js=document.createElement('script');js.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';js.onload=function(){
    var lines=JSON.parse(el.getAttribute('data-lines'));var mid=el.getAttribute('data-mid').split(',');
    var map=L.map('map',{scrollWheelZoom:false,zoomControl:false,dragging:false,touchZoom:false,doubleClickZoom:false}).setView([parseFloat(mid[0]),parseFloat(mid[1])],17);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e',{attribution:'&copy; OpenStreetMap &copy; CARTO',maxZoom:19}).addTo(map);
    var ll=lines.map(function(ln){return ln.map(function(p){return [p[1],p[0]];});});
    L.polyline(ll,{color:'#f47920',weight:16,opacity:.22,lineCap:'round'}).addTo(map);
    var pl=L.polyline(ll,{color:'#f47920',weight:6,opacity:.95,lineCap:'round'}).addTo(map);
    map.fitBounds(pl.getBounds().pad(.6));
  };document.head.appendChild(js);
}
var b=document.getElementById('shareBtn');
if(b)b.addEventListener('click',function(){
  var u=location.href.split('#')[0],t=document.title.replace(/ &mdash;.*$/,'');
  if(navigator.share){navigator.share({title:t,url:u}).catch(function(){});}
  else if(navigator.clipboard){navigator.clipboard.writeText(u).then(function(){b.textContent='Link copied';setTimeout(function(){b.textContent='Share this block';},1600);});}
});
})();
(function(){
var DAY={Sun:0,Mon:1,Tue:2,Wed:3,Thu:4,Fri:5,Sat:6},DN=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],MO=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function ymd(d){return d.getFullYear()*10000+(d.getMonth()+1)*100+d.getDate();}
var els=document.querySelectorAll('.nx');
Array.prototype.forEach.call(els,function(el){
  var days=(el.getAttribute('data-days')||'').split(/[,\/]/).map(function(x){return x.trim();}).filter(function(x){return DAY[x]!=null;});
  if(!days.length)return;
  var susp={},raw=(el.getAttribute('data-susp')||'').split('|'),today=new Date();today.setHours(0,0,0,0);
  var future=[];
  raw.forEach(function(x){var m=x.trim().match(/^\w{3}\s+(\w{3})\s+(\d{1,2})(?::\s*(.*))?/);if(!m)return;var mo=MO.indexOf(m[1]);if(mo<0)return;var d=new Date(today.getFullYear(),mo,parseInt(m[2],10));if(d<today)return;susp[ymd(d)]=1;future.push(m[1]+' '+m[2]+(m[3]?' ('+m[3]+')':''));});
  var out='';
  for(var i=0;i<21;i++){var d=new Date(today.getFullYear(),today.getMonth(),today.getDate()+i);if(days.indexOf(DN[d.getDay()].slice(0,3))<0)continue;if(susp[ymd(d)])continue;out=i===0?'today':(i===1?'tomorrow':DN[d.getDay()]+', '+MO[d.getMonth()]+' '+d.getDate());break;}
  el.textContent=out||'see signs';
  if(future.length){var s=document.createElement('span');s.textContent=' Suspended '+future.slice(0,3).join('; ')+'.';el.parentNode.appendChild(s);}
});
})();
(function(){
'use strict';
var btn=document.getElementById('pdfBtn'),dataEl=document.getElementById('blockdata');
if(!btn||!dataEl)return;
var D=JSON.parse(dataEl.textContent);
var NAVY='#0d1b4b',ORANGE='#f47920',MUTED='#6b6760',CREAM='#f8f7f4';
function load(src){return new Promise(function(res,rej){var s=document.createElement('script');s.src=src;s.onload=res;s.onerror=rej;document.head.appendChild(s);});}
function img(src){return new Promise(function(res){var i=new Image();i.crossOrigin='anonymous';i.onload=function(){try{var c=document.createElement('canvas');c.width=i.naturalWidth;c.height=i.naturalHeight;c.getContext('2d').drawImage(i,0,0);res({data:c.toDataURL('image/png'),w:i.naturalWidth,h:i.naturalHeight});}catch(e){res(null);}};i.onerror=function(){res(null);};i.src=src;});}
function tileMap(lat,lng,zoom,tw,th,lines){return new Promise(function(res){
  var n=Math.pow(2,zoom),xf=(lng+180)/360*n,yf=(1-Math.log(Math.tan(lat*Math.PI/180)+1/Math.cos(lat*Math.PI/180))/Math.PI)/2*n;
  var c=document.createElement('canvas');c.width=tw;c.height=th;var ctx=c.getContext('2d');ctx.fillStyle='#eef2f7';ctx.fillRect(0,0,tw,th);
  var cx=tw/2,cy=th/2,pending=0,fin=false;var x0=Math.floor(xf-cx/256)-1,x1=Math.floor(xf+cx/256)+1,y0=Math.floor(yf-cy/256)-1,y1=Math.floor(yf+cy/256)+1;
  function px(p){var X=(p[0]+180)/360*n,Y=(1-Math.log(Math.tan(p[1]*Math.PI/180)+1/Math.cos(p[1]*Math.PI/180))/Math.PI)/2*n;return [cx+(X-xf)*256,cy+(Y-yf)*256];}
  function done(){if(fin)return;fin=true;ctx.lineCap='round';ctx.lineJoin='round';[[18,'rgba(244,121,32,.25)'],[7,ORANGE]].forEach(function(st){ctx.lineWidth=st[0];ctx.strokeStyle=st[1];lines.forEach(function(ln){ctx.beginPath();ln.forEach(function(p,i){var q=px(p);if(i)ctx.lineTo(q[0],q[1]);else ctx.moveTo(q[0],q[1]);});ctx.stroke();});});
    var u=null;try{u=c.toDataURL('image/jpeg',.88);}catch(e){}res(u?{data:u,w:tw,h:th}:null);}
  var timer=setTimeout(done,3000);
  for(var x=x0;x<=x1;x++)for(var y=y0;y<=y1;y++){if(y<0||y>=n)continue;pending++;(function(tx,ty){var im=new Image();im.crossOrigin='anonymous';im.onload=function(){ctx.drawImage(im,cx+(tx-xf)*256,cy+(ty-yf)*256,256,256);if(--pending===0){clearTimeout(timer);done();}};im.onerror=function(){if(--pending===0){clearTimeout(timer);done();}};im.src='https://a.basemaps.cartocdn.com/light_all/'+zoom+'/'+(((tx%n)+n)%n)+'/'+ty+'.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e';})(x,y);}
  if(!pending){clearTimeout(timer);done();}
});}
var DAY={Sun:0,Mon:1,Tue:2,Wed:3,Thu:4,Fri:5,Sat:6},DN=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],MO=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function ymd(d){return d.getFullYear()*10000+(d.getMonth()+1)*100+d.getDate();}
function nextOf(daysTxt,susp){var days=(daysTxt||'').split(/[,\/]/).map(function(x){return x.trim();}).filter(function(x){return DAY[x]!=null;});if(!days.length)return '';var t=new Date();t.setHours(0,0,0,0);var sk={};(susp||[]).forEach(function(x){var m=x.match(/^\w{3}\s+(\w{3})\s+(\d{1,2})/);if(!m)return;var mo=MO.indexOf(m[1]);if(mo<0)return;var d=new Date(t.getFullYear(),mo,parseInt(m[2],10));if(d>=t)sk[ymd(d)]=1;});
  for(var i=0;i<21;i++){var d=new Date(t.getFullYear(),t.getMonth(),t.getDate()+i);if(days.indexOf(DN[d.getDay()].slice(0,3))<0||sk[ymd(d)])continue;return i===0?'today':(i===1?'tomorrow':DN[d.getDay()]+', '+MO[d.getMonth()]+' '+d.getDate());}return '';}
function build(){
  btn.textContent='Building PDF\u2026';btn.disabled=true;
  var fonts=null;
  Promise.all([
    load('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'),
    fetch('/assets/pdf-fonts.json').then(function(r){return r.json();}).then(function(j){fonts=j;}).catch(function(){}),
    img('/cb6-logo-card.png'),img('/block/'+D.slug+'/qr.png'),tileMap(D.mid[0],D.mid[1],17,900,560,D.lines)
  ]).then(function(r){
    var logo=r[2],qr=r[3],map=r[4];var jsPDF=window.jspdf.jsPDF;var doc=new jsPDF({unit:'pt',format:'letter'});
    var W=612,H=792,M=30;var haveF=false;
    try{if(fonts){doc.addFileToVFS('DMSans-Bold.ttf',fonts['DMSans-Bold']);doc.addFont('DMSans-Bold.ttf','DMSans','bold');doc.addFileToVFS('DMMono-Medium.ttf',fonts['DMMono-Medium']);doc.addFont('DMMono-Medium.ttf','DMMono','normal');haveF=true;}}catch(e){}
    function sans(sz,col,bold){doc.setFont(haveF?'DMSans':'helvetica',haveF?'bold':(bold?'bold':'normal'));doc.setFontSize(sz);doc.setTextColor(col||NAVY);}
    function mono(sz,col){doc.setFont(haveF?'DMMono':'courier',haveF?'normal':'normal');doc.setFontSize(sz);doc.setTextColor(col||MUTED);}
    function body(sz,col){doc.setFont('helvetica','normal');doc.setFontSize(sz);doc.setTextColor(col||NAVY);}
    function label(t,x,y){mono(6.5,MUTED);doc.text(String(t).toUpperCase(),x,y);}
    function wrap(t,w){return doc.splitTextToSize(String(t||''),w);}
    // header band
    doc.setFillColor(NAVY);doc.rect(0,0,W,96,'F');doc.setFillColor(ORANGE);doc.rect(0,96,W,3,'F');
    if(logo)doc.addImage(logo.data,'PNG',M,18,60,60);
    var tx=logo?M+72:M;
    mono(7,'#ffffff');doc.text('BLOCK CARD  \u00b7  BROOKLYN COMMUNITY BOARD 6',tx,32);
    sans(22,'#ffffff');doc.text(D.st,tx,56);
    sans(12,'#ffd9b8');doc.text('between '+D.from+' and '+D.to,tx,73);
    mono(7,'#c9cfe0');doc.text((D.hn?D.hn+'  \u00b7  ':'')+'Brooklyn Community Board 6  \u00b7  bkcb6.app',tx,87);
    // big points row
    var y=112,tw=(W-2*M-9)/4,th=74;
    var tiles=[];
    var dsn=D.dsny[0]||{};
    tiles.push({k:'Trash',v:dsn.refuse||'n/a',s:dsn.refuse_d?'next '+nextOf(dsn.refuse_d):''});
    tiles.push({k:'Recycling & compost',v:dsn.recycling||'n/a',s:dsn.recycling_d?'next '+nextOf(dsn.recycling_d):''});
    var a0=D.asp[0],a1=D.asp[1];
    tiles.push({k:'Alt side parking, '+(a0?a0.side.toLowerCase():''),v:a0?a0.sched.split(',')[0]:'none on file',s:a0?(a0.sched.split(',').slice(1).join(',').trim()+'  \u00b7  next '+nextOf(a0.days,a0.susp)):''});
    tiles.push({k:'Alt side parking, '+(a1?a1.side.toLowerCase():''),v:a1?a1.sched.split(',')[0]:'none on file',s:a1?(a1.sched.split(',').slice(1).join(',').trim()+'  \u00b7  next '+nextOf(a1.days,a1.susp)):''});
    tiles.forEach(function(t,i){var x=M+i*(tw+3);doc.setFillColor('#ffffff');doc.setDrawColor('#e5e2db');doc.roundedRect(x,y,tw,th,4,4,'FD');doc.setFillColor(ORANGE);doc.rect(x,y,3,th,'F');
      label(t.k,x+9,y+14);sans(15,NAVY);var vl=wrap(t.v,tw-16);doc.text(vl[0],x+9,y+35);if(vl[1]){sans(15,NAVY);doc.text(vl[1],x+9,y+52);}
      body(7.5,'#444');wrap(t.s,tw-16).slice(0,2).forEach(function(l,j){doc.text(l,x+9,y+(vl[1]?64:50)+j*9);});});
    y+=th+12;
    // two columns
    var colL=M,colW=(W-2*M-14)/2,colR=M+colW+14;
    // left: map + voting
    var mh=colW*560/900;if(map)doc.addImage(map.data,'JPEG',colL,y,colW,mh,undefined,'FAST');doc.setDrawColor(NAVY);doc.setLineWidth(1);doc.rect(colL,y,colW,mh);
    var ly=y+mh+16;
    sans(9,ORANGE);doc.text('VOTING',colL,ly);ly+=12;
    sans(11,NAVY);doc.text('Next election: Tuesday, November 3, 2026',colL,ly);ly+=11;
    body(8,'#333');wrap('Early voting Oct 24 to Nov 1. Election Day polls open 6 AM to 9 PM.',colW).forEach(function(l){doc.text(l,colL,ly);ly+=9.5;});
    ly+=3;label('On this block\u2019s ballot',colL,ly);ly+=10;
    body(8,'#333');wrap(D.ballot26.join('; ')+'. Plus Governor, Lt. Governor, Attorney General, State Comptroller.',colW).forEach(function(l){doc.text(l,colL,ly);ly+=9.5;});
    ly+=3;label('City offices next on the ballot in 2029',colL,ly);ly+=10;
    body(8,'#333');wrap(D.ballot29.join('; ')+'.',colW).forEach(function(l){doc.text(l,colL,ly);ly+=9.5;});
    D.eds.slice(0,2).forEach(function(e){ly+=4;label('Election district AD '+e.ad+', ED '+e.ed,colL,ly);ly+=10;
      if(e.site){sans(9,NAVY);doc.text('Election Day: '+e.site[0],colL,ly);ly+=10;body(8,'#333');doc.text(e.site[1]+(e.site[4]?' \u00b7 '+e.site[4]:''),colL,ly);ly+=10;}
      if(e.early){sans(9,NAVY);doc.text('Early voting: '+e.early[0],colL,ly);ly+=10;body(8,'#333');doc.text(e.early[1],colL,ly);ly+=10;}});
    if(D.eds.length>2){body(7.5,MUTED);doc.text('This block spans '+D.eds.length+' election districts; see the web card for all of them.',colL,ly);ly+=10;}
    // right: reps
    var ry=y;sans(9,ORANGE);doc.text('WHO REPRESENTS THIS BLOCK',colR,ry);ry+=6;
    var reps=D.reps.concat([{name:D.cb6.name,title:D.cb6.title,office:D.cb6.office,phone:D.cb6.phone,email:D.cb6.email}]);
    reps.forEach(function(o){ry+=7;doc.setDrawColor('#e5e2db');doc.line(colR,ry-4,colR+colW,ry-4);label(o.title,colR,ry+3);ry+=12;sans(10,NAVY);doc.text(o.name,colR,ry);ry+=9;
      body(7.2,'#444');var ct=[o.office,[o.phone,o.email].filter(Boolean).join('  \u00b7  ')].filter(Boolean);ct.forEach(function(l){wrap(l,colW).forEach(function(w){doc.text(w,colR,ry);ry+=8.3;});});});
    // services line under reps
    ry+=7;sans(9,ORANGE);doc.text('SERVICES',colR,ry);ry+=11;body(7.6,'#333');
    var sv=[];if(D.precinct.length)sv.push('Police: '+D.precinct.join(' and ')+' Precinct'+(D.sector.length?', sector '+D.sector.join(', '):''));if(D.school.length)sv.push('Community School District '+D.school.join(' and '));sv.push('311 for noise, sanitation, streets, heat and hot water');
    sv.forEach(function(l){wrap(l,colW).forEach(function(w){doc.text(w,colR,ry);ry+=9;});});
    // footer band with QR
    var fy=H-92;doc.setFillColor(CREAM);doc.rect(0,fy,W,92,'F');doc.setFillColor(ORANGE);doc.rect(0,fy,W,2,'F');
    if(qr)doc.addImage(qr.data,'PNG',M,fy+11,70,70);
    sans(11,NAVY);doc.text('Scan for the live version of this card',M+82,fy+28);
    mono(8,NAVY);doc.text('bkcb6.app/block/'+D.slug+'/',M+82,fy+42);
    body(7.5,'#444');wrap('Next dates, suspensions and permits update live on the web card. Everything on this block, from permits to 311 reports, at bkcb6.app/blocks. Sources: DOT street centerline and parking signs, DSNY collection frequencies, NYC Board of Elections poll sites, NYC district boundary files. Confirm alternate side suspensions on 311.',W-M-(M+82)).forEach(function(l,i){doc.text(l,M+82,fy+56+i*9);});
    mono(6.5,MUTED);doc.text('BROOKLYN COMMUNITY BOARD 6  \u00b7  250 BALTIC STREET  \u00b7  (718) 643-3027  \u00b7  MIKE@BKCB6.ORG  \u00b7  GENERATED '+new Date().toISOString().slice(0,10),M,H-8);
    doc.save('block-card-'+D.slug+'.pdf');
  }).catch(function(e){console.error(e);}).then(function(){btn.textContent='One-page PDF';btn.disabled=false;});
}
btn.addEventListener('click',build);
})();
