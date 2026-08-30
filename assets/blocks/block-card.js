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
    var pl=L.polyline(ll,{color:'#f47920',weight:8,opacity:.95,lineCap:'round'}).addTo(map);
    map.fitBounds(pl.getBounds().pad(.45),{maxZoom:18});
    var lg=ll.reduce(function(a,b){return b.length>a.length?b:a;},ll[0]);var A=lg[0],B=lg[lg.length-1];var mid=[(A[0]+B[0])/2,(A[1]+B[1])/2];
    (function(){
      function box(t){var r=t.getElement();return r?r.getBoundingClientRect():null;}
      function hit(a,b){return a&&b&&!(a.right<b.left-4||b.right<a.left-4||a.bottom<b.top-4||b.bottom<a.top-4);}
      var t1=L.tooltip({permanent:true,direction:'center',className:'xst',interactive:false}).setLatLng(A).setContent(el.getAttribute('data-from')).addTo(map);
      var t2=L.tooltip({permanent:true,direction:'center',className:'xst',interactive:false}).setLatLng(B).setContent(el.getAttribute('data-to')).addTo(map);
      var steep=Math.abs(A[1]-B[1])<Math.abs(A[0]-B[0])*0.6;
      var dirs=steep?[['right',[18,0]],['left',[-18,0]],['top',[0,-16]],['bottom',[0,16]]]:[['top',[0,-16]],['bottom',[0,16]],['right',[18,0]],['left',[-18,0]]];
      var t3=null;
      for(var i=0;i<dirs.length;i++){
        if(t3)map.removeLayer(t3);
        t3=L.tooltip({permanent:true,direction:dirs[i][0],className:'blk',offset:dirs[i][1],interactive:false}).setLatLng(mid).setContent(el.getAttribute('data-st')).addTo(map);
        var b3=box(t3);
        if(!hit(b3,box(t1))&&!hit(b3,box(t2)))break;
      }
    })();
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
(function(){var ORD=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],DNF=['MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY','SUNDAY'];window.__compactDays=function(txt){var ds=(txt||'').split(/[,\/]/).map(function(x){return x.trim();}).filter(function(x){return ORD.indexOf(x)>=0;});ds=ORD.filter(function(x){return ds.indexOf(x)>=0;});if(!ds.length)return '';if(ds.length===1)return DNF[ORD.indexOf(ds[0])];if(ds.length===2)return ds.map(function(x){return x.toUpperCase();}).join(' ');var ix=ds.map(function(x){return ORD.indexOf(x);});var run=ix.every(function(v,i){return i===0||v===ix[i-1]+1;});if(run)return ds[0].toUpperCase()+' - '+ds[ds.length-1].toUpperCase();if(ds.length===6)return 'EXCEPT '+ORD.filter(function(x){return ds.indexOf(x)<0;})[0].toUpperCase();return ds.map(function(x){return x.toUpperCase();}).join(' ');};})();
(function(){
'use strict';
var btn=document.getElementById('pdfBtn'),dataEl=document.getElementById('blockdata');
if(!btn)return;
var D=dataEl?JSON.parse(dataEl.textContent):window.BLOCK;if(!D)return;
var NAVY='#0d1b4b',ORANGE='#f47920',MUTED='#6b6760',CREAM='#f8f7f4';
function load(src){return new Promise(function(res,rej){var s=document.createElement('script');s.src=src;s.onload=res;s.onerror=rej;document.head.appendChild(s);});}
function img(src){return new Promise(function(res){var i=new Image();i.crossOrigin='anonymous';i.onload=function(){try{var c=document.createElement('canvas');c.width=i.naturalWidth;c.height=i.naturalHeight;c.getContext('2d').drawImage(i,0,0);res({data:c.toDataURL('image/png'),w:i.naturalWidth,h:i.naturalHeight});}catch(e){res(null);}};i.onerror=function(){res(null);};i.src=src;});}
function qrImg(url){return load('https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.4.4/qrcode.min.js').then(function(){var q=window.qrcode(0,'M');q.addData(url);q.make();var n=q.getModuleCount(),sz=6,c=document.createElement('canvas');c.width=c.height=n*sz+2*sz;var ctx=c.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle='#0d1b4b';for(var r=0;r<n;r++)for(var cc=0;cc<n;cc++)if(q.isDark(r,cc))ctx.fillRect(sz+cc*sz,sz+r*sz,sz,sz);return {data:c.toDataURL('image/png'),w:c.width,h:c.height};}).catch(function(){return null;});}
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
    img('/cb6-logo-card.png'),qrImg('https://bkcb6.app/block/'+D.slug+'/'),tileMap(D.mid[0],D.mid[1],18,900,558,D.lines,{st:D.st,from:D.from,to:D.to,line:D.lines.reduce(function(a,b){return b.length>a.length?b:a;},D.lines[0])}),img('/assets/blocks/asp-symbol.png'),img('/cb6-logo-square.png'),
    Promise.all((D.ents||[]).map(function(o){return o.logo?img(o.logo):Promise.resolve(null);})),
    Promise.all(['dsny-trash','dsny-recycle','dsny-compost','dsny-truck','lpc-seal'].map(function(n){return img('/assets/blocks/'+n+'.png');})),
    Promise.all(['dcp','nycps','boe','dsny','311','lpc'].map(function(n){return img('/site-icons/agencies/'+n+'.png');})),
    Promise.all(D.precinct.map(function(pc){return img('/elected/precinct/'+parseInt(pc,10)+'.png');}))
  ]).then(function(r){
    var logo=r[2],qr=r[3],map=r[4],sym=r[5],cbsq=r[6],icons=r[7],ic=r[8],ag=r[9],pcl=r[10];var RED='#95262e',GREEN='#1c3d3a';var jsPDF=window.jspdf.jsPDF;var doc=new jsPDF({unit:'pt',format:'letter'});
    var W=612,H=792,M=30;var haveF=false;
    try{if(fonts){doc.addFileToVFS('DMSans-Bold.ttf',fonts['DMSans-Bold']);doc.addFont('DMSans-Bold.ttf','DMSans','bold');doc.addFileToVFS('DMMono-Medium.ttf',fonts['DMMono-Medium']);doc.addFont('DMMono-Medium.ttf','DMMono','normal');haveF=true;}}catch(e){}
    function sans(sz,col,bold){doc.setFont(haveF?'DMSans':'helvetica',haveF?'bold':(bold?'bold':'normal'));doc.setFontSize(sz);doc.setTextColor(col||NAVY);}
    function mono(sz,col){doc.setFont(haveF?'DMMono':'courier',haveF?'normal':'normal');doc.setFontSize(sz);doc.setTextColor(col||MUTED);}
    function body(sz,col){doc.setFont('helvetica','normal');doc.setFontSize(sz);doc.setTextColor(col||NAVY);}
    function label(t,x,y,o){mono(6.5,MUTED);doc.text(String(t).toUpperCase(),x,y,o||{});}

    function wrap(t,w){return doc.splitTextToSize(String(t||''),w);}
    // header band
    doc.setFillColor(NAVY);doc.rect(0,0,W,110,'F');doc.setFillColor(ORANGE);doc.rect(0,110,W,3,'F');
    var tx=M;
    mono(7,'#ffffff');doc.text('BKCB6.APP  \u00b7  BLOCK CARD',tx,30);
    var tsz=D.st.length>22?24:30;sans(tsz,'#ffffff');doc.text(D.st,tx,tsz>24?61:58);
    sans(15,'#ffd9b8');doc.text('between '+D.from+' and '+D.to,tx,82);
    mono(7.5,'#c9cfe0');doc.text((D.hn?D.hn+'  \u00b7  ':'')+(D.zones.length?'Zoning '+D.zones.join(', ')+'  \u00b7  ':'')+'bkcb6.app/block/'+D.slug,tx,99);
    // ---- grid: two columns of equal width, everything snapped to it ----
    var G=12,colW=(W-2*M-G)/2,colL=M,colR=M+colW+G;
    var y=126,rowH=132;
    // left half: 2x2 pickup tiles
    var dsn=D.dsny[0]||{};
    var dt=[{k:'Trash',v:dsn.refuse||'n/a',im:ic[0]},{k:'Recycling',v:dsn.recycling||'n/a',im:ic[1]},{k:'Compost',v:dsn.organics||'n/a',im:ic[2]},{k:'Bulk items',v:dsn.bulk||'none',im:ic[3]}];
    var gw=(colW-4)/2,gh=(rowH-4)/2;
    dt.forEach(function(t,i){var x=colL+(i%2)*(gw+4),yy=y+Math.floor(i/2)*(gh+4);doc.setFillColor('#ffffff');doc.setDrawColor('#e5e2db');doc.setLineWidth(.8);doc.roundedRect(x,yy,gw,gh,4,4,'FD');
      var isz=44;if(t.im)doc.addImage(t.im.data,'PNG',x+8,yy+(gh-isz)/2,isz,isz);
      var tx0=x+isz+16;label(t.k,tx0,yy+20);var vl=wrap(t.v,gw-isz-24);var fs=vl.length>2?8.5:(vl.length>1?10:11.5);sans(fs,NAVY);vl=wrap(t.v,gw-isz-24).slice(0,3);vl.forEach(function(l,j){doc.text(l,tx0,yy+34+j*(fs+2));});});
    // right half: parking signs, one per side, in matching tiles
    function sign(x,yy,w,a){
      var h=w*376/573;doc.setFillColor('#ffffff');doc.setDrawColor(RED);doc.setLineWidth(2);doc.roundedRect(x,yy,w,h,3,3,'FD');doc.setLineWidth(1);
      var ss=h*0.64;if(sym)doc.addImage(sym.data,'PNG',x+7,yy+(h-ss)/2-1,ss,ss);
      var m=(a.sched||'').match(/^(.*?),\s*(.*)$/);var day=(window.__compactDays?window.__compactDays(a.days):'')||(m?m[1]:a.sched||'').toUpperCase(),time=(m?m[2]:'').replace(/\s+to\s+/,' - ').replace(/:00/g,'').replace(/ (AM|PM)/g,'$1');
      var tx0=x+ss+10,tw0=w-ss-16,cx=tx0+tw0/2;sans(8,RED);doc.text(time,cx,yy+h*0.30,{align:'center'});
      var dsz=day.length>8?9.5:(day.length>6?11.5:13.5);sans(dsz,RED);doc.text(day,cx,yy+h*0.58,{align:'center'});
      var ay=yy+h*0.79;doc.setDrawColor(RED);doc.setFillColor(RED);doc.setLineWidth(2.6);doc.line(cx-12,ay,cx+15,ay);doc.triangle(cx-20,ay,cx-10,ay-5.5,cx-10,ay+5.5,'F');doc.setLineWidth(1);
      mono(4,RED);doc.text('DEPT OF TRANSPORTATION',x+w/2,yy+h-5,{align:'center'});
      doc.setFillColor(RED);doc.roundedRect(x+w-50,yy+3,47,10,2,2,'F');sans(6,'#ffffff');doc.text(String(a.side||'').toUpperCase(),x+w-26.5,yy+10.3,{align:'center'});
    }
    var sw=(colW-4)/2;
    if(D.asp.length){var sides=D.asp.slice(0,2);var have=sides.map(function(a){return a.side;});
      var pairs={'North side':'South side','South side':'North side','East side':'West side','West side':'East side'};
      if(sides.length===1)sides.push({missing:true,side:pairs[sides[0].side]||'Other side'});
      sides.forEach(function(a,i){var x=colR+i*(sw+4);doc.setFillColor('#ffffff');doc.setDrawColor('#e5e2db');doc.setLineWidth(.8);doc.roundedRect(x,y,sw,rowH,4,4,'FD');
      var iw=sw-12,ih=iw*376/573;
      if(a.missing){doc.setDrawColor('#c9c5bc');doc.setLineWidth(1.2);doc.roundedRect(x+6,y+6,iw,ih,3,3,'D');mono(6,MUTED);doc.text(String(a.side).toUpperCase(),x+6+iw/2,y+6+ih*0.4,{align:'center'});body(6.8,'#444');wrap('No alternate side rule on file for this side. Check the posted signs.',iw-8).forEach(function(l,j){doc.text(l,x+6+iw/2,y+6+ih*0.58+j*8,{align:'center'});});label('Alternate side, '+a.side.toLowerCase(),x+6,y+ih+18);return;}
      sign(x+6,y+6,iw,a);label('Alternate side, '+a.side.toLowerCase(),x+6,y+ih+18);body(6.8,'#444');doc.text('next '+nextOf(a.days,a.susp),x+6,y+ih+27);});}
    else{doc.setFillColor('#ffffff');doc.setDrawColor('#e5e2db');doc.roundedRect(colR,y,colW,rowH,4,4,'FD');label('Alternate side parking',colR+9,y+16);sans(10,NAVY);doc.text('No rules on file for this block',colR+9,y+34);}
    y+=rowH+G;
    // ---- second row: block diagram on the left; zoning, LPC and poll site on the right ----
    var mh=colW*0.42;
    doc.setFillColor('#fbfaf7');doc.setDrawColor(NAVY);doc.setLineWidth(1.2);doc.rect(colL,y,colW,mh,'FD');
    (function(){
      var MLAT=111320,MLON=84400;function tm(p){return [(p[0]-D.mid[1])*MLON,(p[1]-D.mid[0])*MLAT];}
      var lg=D.lines.reduce(function(a2,b2){return b2.length>a2.length?b2:a2;},D.lines[0]);
      var bl=0;D.lines.forEach(function(ln){for(var i=0;i<ln.length-1;i++){var p1=tm(ln[i]),p2=tm(ln[i+1]);bl+=Math.hypot(p2[0]-p1[0],p2[1]-p1[1]);}});bl=bl||80;var sc=Math.min(colW,mh)*0.5/bl;sc=Math.max(0.2,Math.min(sc,0.55));
      var cx=colL+colW/2,cy=y+mh/2;function px(p){var m=tm(p);return [cx+m[0]*sc,cy-m[1]*sc];}
      function clipSeg(a2,b2){var x0=colL+1,y0=y+1,x1=colL+colW-1,y1=y+mh-1;var t0=0,t1=1,dx=b2[0]-a2[0],dy=b2[1]-a2[1];var p=[-dx,dx,-dy,dy],q=[a2[0]-x0,x1-a2[0],a2[1]-y0,y1-a2[1]];for(var i=0;i<4;i++){if(p[i]===0){if(q[i]<0)return null;}else{var t=q[i]/p[i];if(p[i]<0){if(t>t1)return null;if(t>t0)t0=t;}else{if(t<t0)return null;if(t<t1)t1=t;}}}return [[a2[0]+t0*dx,a2[1]+t0*dy],[a2[0]+t1*dx,a2[1]+t1*dy]];}
      function drawLines(pts){for(var i=0;i<pts.length-1;i++){var c=clipSeg(pts[i],pts[i+1]);if(c)doc.line(c[0][0],c[0][1],c[1][0],c[1][1]);}}
      doc.setDrawColor('#c9c5bc');doc.setLineWidth(2.2);(D.near||[]).forEach(function(seg){drawLines(seg[1].map(px));});
      doc.setDrawColor(ORANGE);doc.setLineWidth(7);D.lines.forEach(function(ln){drawLines(ln.map(px));});
      var done={};(D.near||[]).forEach(function(seg){var n=seg[0];if(n===D.st||done[n]||D.from.indexOf(n)>=0||D.to.indexOf(n)>=0)return;var g=seg[1];var m=px(g[Math.floor(g.length/2)]);if(m[0]<colL+30||m[0]>colL+colW-30||m[1]<y+10||m[1]>y+mh-10)return;var a2=px(g[0]),b2=px(g[g.length-1]);var ang=-Math.atan2(b2[1]-a2[1],b2[0]-a2[0])*180/Math.PI;if(ang>90)ang-=180;if(ang<-90)ang+=180;mono(5.5,'#8a867d');doc.text(n,m[0],m[1]-2,{align:'center',angle:ang});done[n]=1;});
      function tagBox(t,x0,y0,fill,col,sz){sans(sz,col);var w=doc.getTextWidth(t)+10,h=sz+6;x0=Math.max(colL+w/2+2,Math.min(colL+colW-w/2-2,x0));y0=Math.max(y+h/2+2,Math.min(y+mh-h/2-2,y0));doc.setFillColor(fill);doc.setDrawColor(col);doc.setLineWidth(1);doc.roundedRect(x0-w/2,y0-h/2,w,h,3,3,'FD');doc.setTextColor(col);doc.text(t,x0,y0+sz*0.35,{align:'center'});}
      var pa=px(lg[0]),pb=px(lg[lg.length-1]),pm=[(pa[0]+pb[0])/2,(pa[1]+pb[1])/2];var dx=pb[0]-pa[0],dy=pb[1]-pa[1],L=Math.hypot(dx,dy)||1;var nx=-dy/L,ny=dx/L;
      tagBox(D.st,pm[0]+nx*24,pm[1]+ny*24,NAVY,'#ffffff',8);
      tagBox(D.from.split(' & ')[0],pa[0]-dx/L*14,pa[1]-dy/L*14,'#ffffff',NAVY,7);tagBox(D.to.split(' & ')[0],pb[0]+dx/L*14,pb[1]+dy/L*14,'#ffffff',NAVY,7);
    })();
    var ry=y;
    function btn(x,yy,w,h,t){doc.setFillColor('#ffffff');doc.setDrawColor(t.col);doc.setLineWidth(1.3);doc.roundedRect(x,yy,w,h,6,6,'FD');if(t.im)doc.addImage(t.im.data,'PNG',x+4,yy+4,h-8,h-8,undefined,'FAST');var tx0=x+h+2,tw0=w-h-8;mono(5.8,MUTED);doc.text(wrap(t.k.toUpperCase(),tw0)[0],tx0,yy+11);sans(9.5,t.col);doc.text(wrap(t.v,tw0)[0],tx0,yy+23);if(t.s){body(6.8,'#444');doc.text(wrap(t.s,tw0)[0],tx0,yy+33);}}
    var bh=40;
    if(D.zones.length){btn(colR,ry,colW,bh,{k:'Zoning',v:D.zones.join(' \u00b7 '),s:(D.zfam||[]).join(', '),im:ag[0],col:NAVY});ry+=bh+4;}
    D.hist.forEach(function(hd,i){btn(colR,ry,colW,bh,{k:'Historic district'+(D.hist_side&&D.hist_side[i]?', '+D.hist_side[i]:''),v:hd,s:'Exterior work needs an LPC permit',im:ic[4],col:'#8b1a1a'});ry+=bh+4;});
    ry+=4;if(ag[2])doc.addImage(ag[2].data,'PNG',colR,ry,26,26,undefined,'FAST');sans(8.5,ORANGE);doc.text('THIS BLOCK\u2019S POLL SITE',colR+32,ry+9);sans(9,NAVY);doc.text('Tue, Nov 3, 2026 \u00b7 early voting Oct 24 to Nov 1',colR+32,ry+21);ry+=32;
    var e0=D.eds[0];if(e0){label('Election district AD '+e0.ad+', ED '+e0.ed+(D.eds.length>1?' (spans '+D.eds.length+'; all on the web card)':''),colR,ry);ry+=10;
      if(e0.site){sans(9,NAVY);doc.text('Election Day: '+e0.site[0],colR,ry);ry+=9.5;body(7.5,'#333');doc.text(wrap(e0.site[1]+(e0.site[4]?' \u00b7 '+e0.site[4]:''),colW)[0],colR,ry);ry+=9.5;}
      if(e0.early){sans(9,NAVY);doc.text('Early voting: '+e0.early[0],colR,ry);ry+=9.5;body(7.5,'#333');doc.text(e0.early[1],colR,ry);ry+=9.5;}}
    y+=Math.max(mh,ry-y)+G;
    // ---- entity tiles: label above, big square logo, contact below ----
    var ents=D.ents||[];var per=4,gap=8,tw2=(W-2*M-(per-1)*gap)/per,lw=tw2-16;
    var avail=(H-92)-8-y;var rows=Math.ceil(ents.length/per);var th2=Math.min(160,(avail-(rows-1)*gap)/rows);var lsz=Math.min(lw,th2-62);
    ents.forEach(function(e,i){var x=M+(i%per)*(tw2+gap),yy=y+Math.floor(i/per)*(th2+gap);doc.setFillColor('#ffffff');doc.setDrawColor(NAVY);doc.setLineWidth(1.2);doc.roundedRect(x,yy,tw2,th2,6,6,'FD');
      mono(5.6,ORANGE);var kl=wrap(e.k.toUpperCase(),tw2-12);doc.text(kl[0],x+6,yy+10);if(kl[1])doc.text(kl[1],x+6,yy+17);
      var lo=icons[i];var ly0=yy+(kl[1]?21:14);if(lo)doc.addImage(lo.data,'PNG',x+(tw2-lsz)/2,ly0,lsz,lsz,undefined,'FAST');
      var ty=ly0+lsz+10;sans(8.2,NAVY);var nl=wrap(e.name,tw2-12);doc.text(nl[0],x+6,ty);ty+=9;if(nl[1]){doc.text(nl[1],x+6,ty);ty+=9;}
      body(5.9,'#444');e.lines.filter(Boolean).forEach(function(l){wrap(l,tw2-12).slice(0,2).forEach(function(w){if(ty<yy+th2-3){doc.text(w,x+6,ty);ty+=7;}});});});
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
