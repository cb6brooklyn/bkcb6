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
function tileMap(lat,lng,zoom,tw,th,lines,labels){return new Promise(function(res){
  var n=Math.pow(2,zoom),xf=(lng+180)/360*n,yf=(1-Math.log(Math.tan(lat*Math.PI/180)+1/Math.cos(lat*Math.PI/180))/Math.PI)/2*n;
  var SC=1;if(labels&&labels.line){var l0=labels.line,pa=[(l0[0][0]+180)/360*n,(1-Math.log(Math.tan(l0[0][1]*Math.PI/180)+1/Math.cos(l0[0][1]*Math.PI/180))/Math.PI)/2*n],pb=[(l0[l0.length-1][0]+180)/360*n,(1-Math.log(Math.tan(l0[l0.length-1][1]*Math.PI/180)+1/Math.cos(l0[l0.length-1][1]*Math.PI/180))/Math.PI)/2*n];var bl=Math.hypot(pb[0]-pa[0],pb[1]-pa[1])*256;SC=Math.max(1,Math.min(3,(Math.min(tw,th)*0.62)/Math.max(bl,40)));}
  var TS=256*SC;
  var c=document.createElement('canvas');c.width=tw;c.height=th;var ctx=c.getContext('2d');ctx.fillStyle='#eef2f7';ctx.fillRect(0,0,tw,th);
  var cx=tw/2,cy=th/2,pending=0,fin=false;var x0=Math.floor(xf-cx/TS)-1,x1=Math.floor(xf+cx/TS)+1,y0=Math.floor(yf-cy/TS)-1,y1=Math.floor(yf+cy/TS)+1;
  function px(p){var X=(p[0]+180)/360*n,Y=(1-Math.log(Math.tan(p[1]*Math.PI/180)+1/Math.cos(p[1]*Math.PI/180))/Math.PI)/2*n;return [cx+(X-xf)*TS,cy+(Y-yf)*TS];}
  function done(){if(fin)return;fin=true;ctx.lineCap='round';ctx.lineJoin='round';[[26,'rgba(244,121,32,.28)'],[9,ORANGE]].forEach(function(st){ctx.lineWidth=st[0];ctx.strokeStyle=st[1];lines.forEach(function(ln){ctx.beginPath();ln.forEach(function(p,i){var q=px(p);if(i)ctx.lineTo(q[0],q[1]);else ctx.moveTo(q[0],q[1]);});ctx.stroke();});});
    if(labels){var ln=labels.line;var A=px(ln[0]),B=px(ln[ln.length-1]),mid=px(ln[Math.floor(ln.length/2)]);var ang=Math.atan2(B[1]-A[1],B[0]-A[0]);if(ang>Math.PI/2)ang-=Math.PI;if(ang<-Math.PI/2)ang+=Math.PI;
      function tag(t,x0,y0,sz,fill,col){ctx.font='bold '+sz+'px DM Sans, Helvetica, Arial';var w=ctx.measureText(t).width+18;ctx.fillStyle=fill;ctx.beginPath();ctx.roundRect?ctx.roundRect(x0-w/2,y0-sz*0.75-6,w,sz+12,7):ctx.rect(x0-w/2,y0-sz*0.75-6,w,sz+12);ctx.fill();ctx.fillStyle=col;ctx.textAlign='center';ctx.fillText(t,x0,y0);}
      if(Math.abs(ang)>Math.PI/3){tag(labels.st,mid[0]+(mid[0]<tw/2?120:-120),mid[1]+8,26,'#0d1b4b','#ffffff');}else{ctx.save();ctx.translate(mid[0],mid[1]);ctx.rotate(ang);tag(labels.st,0,-34,26,'#0d1b4b','#ffffff');ctx.restore();}
      var dx=B[0]-A[0],dy=B[1]-A[1],L=Math.hypot(dx,dy)||1;function cl(v,lo,hi){return Math.max(lo,Math.min(hi,v));}function tag2(t,x0,y0){tag(t,x0,y0,24,'#ffffff','#0d1b4b');ctx.strokeStyle='#0d1b4b';ctx.lineWidth=3;var w=ctx.measureText(t).width+18;ctx.beginPath();ctx.roundRect?ctx.roundRect(x0-w/2,y0-24*0.75-6,w,36,7):ctx.rect(x0-w/2,y0-24*0.75-6,w,36);ctx.stroke();}
      tag2(labels.from,cl(A[0]-dx/L*30,100,tw-100),cl(A[1]-dy/L*30+8,30,th-14));tag2(labels.to,cl(B[0]+dx/L*30,100,tw-100),cl(B[1]+dy/L*30+8,30,th-14));}
    var u=null;try{u=c.toDataURL('image/jpeg',.88);}catch(e){}res(u?{data:u,w:tw,h:th}:null);}
  var timer=setTimeout(done,3000);
  for(var x=x0;x<=x1;x++)for(var y=y0;y<=y1;y++){if(y<0||y>=n)continue;pending++;(function(tx,ty){var im=new Image();im.crossOrigin='anonymous';im.onload=function(){ctx.imageSmoothingEnabled=true;ctx.drawImage(im,cx+(tx-xf)*TS,cy+(ty-yf)*TS,TS+0.5,TS+0.5);if(--pending===0){clearTimeout(timer);done();}};im.onerror=function(){if(--pending===0){clearTimeout(timer);done();}};im.src='https://a.basemaps.cartocdn.com/light_all/'+zoom+'/'+(((tx%n)+n)%n)+'/'+ty+'.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e';})(x,y);}
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
    img('/cb6-logo-card.png'),img('/block/'+D.slug+'/qr.png'),tileMap(D.mid[0],D.mid[1],18,900,558,D.lines,{st:D.st,from:D.from,to:D.to,line:D.lines.reduce(function(a,b){return b.length>a.length?b:a;},D.lines[0])}),img('/assets/blocks/asp-symbol.png'),img('/cb6-logo-square.png'),
    Promise.all(D.reps.map(function(o){return o.icon?img(o.icon):Promise.resolve(null);})),
    Promise.all(['dsny-trash','dsny-recycle','dsny-compost','dsny-truck','lpc-seal'].map(function(n){return img('/assets/blocks/'+n+'.png');}))
  ]).then(function(r){
    var logo=r[2],qr=r[3],map=r[4],sym=r[5],cbsq=r[6],icons=r[7],ic=r[8];var RED='#95262e',GREEN='#1c3d3a';var jsPDF=window.jspdf.jsPDF;var doc=new jsPDF({unit:'pt',format:'letter'});
    var W=612,H=792,M=30;var haveF=false;
    try{if(fonts){doc.addFileToVFS('DMSans-Bold.ttf',fonts['DMSans-Bold']);doc.addFont('DMSans-Bold.ttf','DMSans','bold');doc.addFileToVFS('DMMono-Medium.ttf',fonts['DMMono-Medium']);doc.addFont('DMMono-Medium.ttf','DMMono','normal');haveF=true;}}catch(e){}
    function sans(sz,col,bold){doc.setFont(haveF?'DMSans':'helvetica',haveF?'bold':(bold?'bold':'normal'));doc.setFontSize(sz);doc.setTextColor(col||NAVY);}
    function mono(sz,col){doc.setFont(haveF?'DMMono':'courier',haveF?'normal':'normal');doc.setFontSize(sz);doc.setTextColor(col||MUTED);}
    function body(sz,col){doc.setFont('helvetica','normal');doc.setFontSize(sz);doc.setTextColor(col||NAVY);}
    function label(t,x,y,o){mono(6.5,MUTED);doc.text(String(t).toUpperCase(),x,y,o||{});}
    function wrap(t,w){return doc.splitTextToSize(String(t||''),w);}
    // header band
    doc.setFillColor(NAVY);doc.rect(0,0,W,110,'F');doc.setFillColor(ORANGE);doc.rect(0,110,W,3,'F');
    if(logo)doc.addImage(logo.data,'PNG',M,18,74,74);
    var tx=logo?M+88:M;
    mono(7,'#ffffff');doc.text('BKCB6.APP  \u00b7  BLOCK CARD  \u00b7  BROOKLYN COMMUNITY BOARD 6',tx,30);
    var tsz=D.st.length>22?24:30;sans(tsz,'#ffffff');doc.text(D.st,tx,tsz>24?61:58);
    sans(15,'#ffd9b8');doc.text('between '+D.from+' and '+D.to,tx,82);
    mono(7.5,'#c9cfe0');doc.text((D.hn?D.hn+'  \u00b7  ':'')+(D.zones.length?'Zoning '+D.zones.join(', ')+'  \u00b7  ':'')+'bkcb6.app/block/'+D.slug,tx,99);
    // big points row: two tiles, then the two parking signs
    var y=126,tot=W-2*M-9,tw=tot*0.21,sw=tot*0.29,th=sw*376/573+18;
    var dsn=D.dsny[0]||{};
    var dt=[{k:'Trash',v:dsn.refuse||'n/a',n:dsn.refuse_d,im:ic[0]},{k:'Recycling',v:dsn.recycling||'n/a',n:dsn.recycling_d,im:ic[1]},{k:'Compost',v:dsn.organics||'n/a',n:dsn.organics_d||dsn.recycling_d,im:ic[2]},{k:'Bulk items',v:dsn.bulk||'none',n:'',im:ic[3]}];
    var gw=tw,gh=(th-3)/2;
    dt.forEach(function(t,i){var x=M+(i%2)*(gw+3),yy=y+Math.floor(i/2)*(gh+3);doc.setFillColor('#ffffff');doc.setDrawColor('#e5e2db');doc.roundedRect(x,yy,gw,gh,4,4,'FD');
      var isz=gh-14;if(t.im)doc.addImage(t.im.data,'PNG',x+6,yy+7,isz,isz);
      label(t.k,x+isz+12,yy+15);sans(9,NAVY);wrap(t.v,gw-isz-18).slice(0,2).forEach(function(l,j){doc.text(l,x+isz+12,yy+27+j*10);});
      if(t.n){body(6.5,'#444');doc.text(wrap('next '+nextOf(t.n).replace(/^(\w{3})\w*,/,'$1'),gw-isz-18)[0]||'',x+isz+12,yy+gh-6);}});
    function sign(x,yy,w,a){
      var h=w*376/573;doc.setFillColor('#ffffff');doc.setDrawColor(RED);doc.setLineWidth(2.2);doc.roundedRect(x,yy,w,h,3,3,'FD');doc.setLineWidth(1);
      var ss=h*0.66;if(sym)doc.addImage(sym.data,'PNG',x+6,yy+(h-ss)/2-2,ss,ss);
      var m=(a.sched||'').match(/^(.*?),\s*(.*)$/);var day=(m?m[1]:a.sched||'').toUpperCase(),time=(m?m[2]:'').replace(/\s+to\s+/,' - ').replace(/:00/g,'').replace(/ (AM|PM)/g,'$1');
      var tx0=x+ss+9,tw0=w-ss-15;sans(8.2,RED);doc.text(time,tx0+tw0/2,yy+h*0.28,{align:'center'});
      var dsz=day.length>8?10:(day.length>6?12:14);sans(dsz,RED);doc.text(day,tx0+tw0/2,yy+h*0.58,{align:'center'});
      var ax=tx0+tw0/2,ay=yy+h*0.80;doc.setDrawColor(RED);doc.setFillColor(RED);doc.setLineWidth(3);doc.line(ax-14,ay,ax+16,ay);doc.triangle(ax-22,ay,ax-12,ay-6,ax-12,ay+6,'F');doc.setLineWidth(1);
      mono(4.2,RED);doc.text('DEPT OF TRANSPORTATION',x+w/2,yy+h-6,{align:'center'});
      doc.setFillColor(RED);doc.roundedRect(x+w-52,yy+3,49,11,2,2,'F');sans(6.5,'#ffffff');doc.text(String(a.side||'').toUpperCase(),x+w-27.5,yy+11,{align:'center'});
    }
    D.asp.slice(0,2).forEach(function(a,i){var x=M+2*(tw+3)+i*(sw+3);sign(x,y,sw,a);body(7.2,'#333');doc.text(wrap(a.side+' \u00b7 next '+nextOf(a.days,a.susp),sw)[0]||'',x+1,y+sw*376/573+13);});
    if(!D.asp.length){var x=M+2*(tw+3);doc.setFillColor('#ffffff');doc.setDrawColor('#e5e2db');doc.roundedRect(x,y,sw*2+3,th,4,4,'FD');label('Alternate side parking',x+9,y+14);sans(11,NAVY);doc.text('No rules on file for this block',x+9,y+36);}
    y+=th+12;
    // two columns
    var colL=M,colW=(W-2*M-14)/2,colR=M+colW+14;
    // left: map + voting
    var mh=colW*0.62;if(map)doc.addImage(map.data,'JPEG',colL,y,colW,mh,undefined,'FAST');doc.setDrawColor(NAVY);doc.setLineWidth(1.2);doc.rect(colL,y,colW,mh);
    var ly=y+mh+10;var cx0=colL;
    function chip(t,col,icon){mono(8,col);var cw=doc.getTextWidth(t)+18+(icon?18:0);if(cx0+cw>colL+colW){cx0=colL;ly+=23;}doc.setDrawColor(col);doc.setFillColor('#ffffff');doc.setLineWidth(1.2);doc.roundedRect(cx0,ly,cw,18,9,9,'FD');if(icon)doc.addImage(icon.data,'PNG',cx0+2,ly+1,16,16);doc.setTextColor(col);doc.text(t,cx0+(icon?21:9),ly+12);cx0+=cw+5;}
    if(D.zones.length)chip('ZONING '+D.zones.join(' \u00b7 '),NAVY);
    D.precinct.forEach(function(pc){chip(pc.toUpperCase()+' PRECINCT'+(D.sector.length?' \u00b7 SECTOR '+D.sector.join(', '):''),NAVY);});
    D.school.forEach(function(sd){chip('SCHOOL DISTRICT '+sd,NAVY);});
    D.hist.forEach(function(hd,i){var t=hd.toUpperCase()+(D.hist_side&&D.hist_side[i]?' \u00b7 '+D.hist_side[i].toUpperCase():'');mono(8,'#8b1a1a');var cw=doc.getTextWidth(t)+36;if(cw>colW){t=hd.toUpperCase();}chip(t,'#8b1a1a',ic[4]);});
    doc.setLineWidth(1);ly+=18+12;
    sans(9,ORANGE);doc.text('VOTING',colL,ly);ly+=12;
    sans(11,NAVY);doc.text('Next election: Tuesday, November 3, 2026',colL,ly);ly+=11;
    body(8,'#333');wrap('Early voting Oct 24 to Nov 1. Election Day polls open 6 AM to 9 PM. On this block\u2019s ballot: '+D.ballot26.map(function(x){return x.replace(/\s*\(.*\)/,'');}).join('; ')+', plus Governor, Lt. Governor, Attorney General and State Comptroller. City Council, Mayor, Comptroller, Public Advocate and Borough President are next on the ballot in 2029.',colW).forEach(function(l){doc.text(l,colL,ly);ly+=9.5;});
    D.eds.slice(0,3).forEach(function(e,i){ly+=4;label('Election district AD '+e.ad+', ED '+e.ed+(D.eds.length>1?' (this block spans '+D.eds.length+')':''),colL,ly);ly+=10;
      if(i===0){if(e.site){sans(9,NAVY);doc.text('Election Day: '+e.site[0],colL,ly);ly+=10;body(8,'#333');doc.text(e.site[1]+(e.site[4]?' \u00b7 '+e.site[4]:''),colL,ly);ly+=10;}
        if(e.early){sans(9,NAVY);doc.text('Early voting: '+e.early[0],colL,ly);ly+=10;body(8,'#333');doc.text(e.early[1],colL,ly);ly+=10;}}
      else{body(8,'#333');if(e.site)wrap('Election Day: '+e.site[0]+', '+e.site[1].replace(/, Brooklyn.*$/,''),colW).forEach(function(l){doc.text(l,colL,ly);ly+=9.5;});if(e.early)wrap('Early voting: '+e.early[0],colW).forEach(function(l){doc.text(l,colL,ly);ly+=9.5;});}});
    // right: reps
    var ry=y;sans(9,ORANGE);doc.text('WHO REPRESENTS THIS BLOCK',colR,ry);ry+=6;
    var all=D.reps.map(function(o,i){o=Object.assign({},o);o.img=icons[i];return o;});
    var prim=all.filter(function(o){return /Council/.test(o.title);}).concat([{name:D.cb6.name,title:D.cb6.title,office:D.cb6.office,phone:D.cb6.phone,email:D.cb6.email,img:cbsq}]);
    var rest=all.filter(function(o){return !/Council/.test(o.title);});
    var reps=prim;
    var IC=27,IX=colR,TX=colR+IC+7,TW=colW-IC-7;
    reps.forEach(function(o){ry+=6;doc.setDrawColor('#e5e2db');doc.line(colR,ry-3,colR+colW,ry-3);var top=ry-1;
      if(o.img){doc.addImage(o.img.data,'PNG',IX,top+1,IC,IC,undefined,'FAST');doc.setDrawColor(NAVY);doc.setLineWidth(.6);doc.rect(IX,top+1,IC,IC);doc.setLineWidth(1);}
      label(o.title,TX,ry+3);ry+=11;sans(9.5,NAVY);doc.text(o.name,TX,ry);ry+=8.5;
      var cw=/Mayor|Comptroller|Public Advocate/.test(o.title);
      body(7,'#444');var ct=cw?[[o.office,o.phone,o.email].filter(Boolean).join('  \u00b7  ')]:[o.office,[o.phone,o.email].filter(Boolean).join('  \u00b7  ')].filter(Boolean);ct.forEach(function(l){wrap(l,TW).slice(0,2).forEach(function(w){doc.text(w,TX,ry);ry+=8;});});
      if(ry<top+IC+3)ry=top+IC+3;});
    ry+=10;sans(9,ORANGE);doc.text('ALSO REPRESENTS THIS BLOCK',colR,ry);ry+=4;
    rest.forEach(function(o){ry+=9;if(o.img){doc.addImage(o.img.data,'PNG',colR,ry-7,14,14,undefined,'FAST');}sans(8.5,NAVY);doc.text(o.name,colR+19,ry+3);mono(5.8,MUTED);doc.text(o.title.toUpperCase(),colR+19,ry+11);body(6.8,'#444');doc.text((o.phone||'')+(o.email?'  \u00b7  '+o.email:''),colR+19,ry+19);ry+=18;});
    // services line under reps
    ry+=12;body(7.6,'#333');doc.text('311 for noise, sanitation, streets, heat and hot water.',colR,ry);
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
