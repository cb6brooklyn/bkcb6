(function(){
'use strict';
var D=window.BLOCK;if(!D)return;
var pfx=(document.getElementById('card')||{}).getAttribute?document.getElementById('card').getAttribute('data-pfx')||'bk':'bk';
var PAL={mn:['#0c549c','#8fb8e0','Manhattan'],bx:['#3054a8','#f06c0c','Bronx'],bk:['#003060','#f2c94c','Brooklyn'],qn:['#7a6636','#e8d9a8','Queens'],si:['#2f5a4c','#a6c4b8','Staten Island']};
var C0=PAL[pfx][0],C1=PAL[pfx][1],BNM=PAL[pfx][2];
var NAVY='#0d1b4b',ORANGE='#f47920',MUTED='#6b6760',CREAM='#f8f7f4',RED='#95262e';
var ORD=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],DNF=['MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY','SUNDAY'],DN=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],MO=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function load(src){return new Promise(function(res,rej){if(document.querySelector('script[src="'+src+'"]')){res();return;}var s=document.createElement('script');s.src=src;s.onload=res;s.onerror=rej;document.head.appendChild(s);});}
function img(src){return new Promise(function(res){if(!src){res(null);return;}var i=new Image();i.crossOrigin='anonymous';i.onload=function(){try{var c=document.createElement('canvas');c.width=i.naturalWidth;c.height=i.naturalHeight;c.getContext('2d').drawImage(i,0,0);res({data:c.toDataURL('image/png'),w:i.naturalWidth,h:i.naturalHeight});}catch(e){res(null);}};i.onerror=function(){res(null);};i.src=src;});}
function qrImg(url){return load('https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.4.4/qrcode.min.js').then(function(){var q=window.qrcode(0,'M');q.addData(url);q.make();var n=q.getModuleCount(),sz=6,c=document.createElement('canvas');c.width=c.height=n*sz+2*sz;var x=c.getContext('2d');x.fillStyle='#fff';x.fillRect(0,0,c.width,c.height);x.fillStyle=C0;for(var r=0;r<n;r++)for(var k=0;k<n;k++)if(q.isDark(r,k))x.fillRect(sz+k*sz,sz+r*sz,sz,sz);return {data:c.toDataURL('image/png'),w:c.width,h:c.height};}).catch(function(){return null;});}
function compactDays(txt){var ds=(txt||'').split(/[,\/]/).map(function(x){return x.trim();}).filter(function(x){return ORD.indexOf(x)>=0;});ds=ORD.filter(function(x){return ds.indexOf(x)>=0;});if(!ds.length)return '';if(ds.length===1)return DNF[ORD.indexOf(ds[0])];if(ds.length===2)return ds.map(function(x){return x.toUpperCase();}).join(' ');var ix=ds.map(function(x){return ORD.indexOf(x);});var run=ix.every(function(v,i){return i===0||v===ix[i-1]+1;});if(run)return ds[0].toUpperCase()+' - '+ds[ds.length-1].toUpperCase();if(ds.length===6)return 'EXCEPT '+ORD.filter(function(x){return ds.indexOf(x)<0;})[0].toUpperCase();return ds.map(function(x){return x.toUpperCase();}).join(' ');}
function nextOf(txt){var days=(txt||'').split(/[,\/]/).map(function(x){return x.trim();}).filter(function(x){return ORD.indexOf(x)>=0;});if(!days.length)return '';var t=new Date();t.setHours(0,0,0,0);for(var i=0;i<21;i++){var d=new Date(t.getFullYear(),t.getMonth(),t.getDate()+i);if(days.indexOf(DN[d.getDay()].slice(0,3))<0)continue;return i===0?'today':(i===1?'tomorrow':DN[d.getDay()]+', '+MO[d.getMonth()]+' '+d.getDate());}return '';}
function stripCity(t){return String(t||'').replace(/,\s*(Brooklyn|New York|Bronx|Queens|Staten Island),?\s*NY/,'');}

function makeDoc(jsPDF,fonts,W,H){
  var doc=new jsPDF({unit:'pt',format:[W,H]});var haveF=false;
  try{if(fonts){doc.addFileToVFS('DMSans-Bold.ttf',fonts['DMSans-Bold']);doc.addFont('DMSans-Bold.ttf','DMSans','bold');doc.addFileToVFS('DMMono-Medium.ttf',fonts['DMMono-Medium']);doc.addFont('DMMono-Medium.ttf','DMMono','normal');haveF=true;}}catch(e){}
  var d={doc:doc,W:W,H:H};
  d.sans=function(sz,col){doc.setFont(haveF?'DMSans':'helvetica','bold');doc.setFontSize(sz);doc.setTextColor(col||NAVY);};
  d.mono=function(sz,col){doc.setFont(haveF?'DMMono':'courier','normal');doc.setFontSize(sz);doc.setTextColor(col||MUTED);};
  d.body=function(sz,col){doc.setFont('helvetica','normal');doc.setFontSize(sz);doc.setTextColor(col||NAVY);};
  d.text=function(t,x,y,a){doc.text(String(t==null?'':t),x,y,a?{align:a}:undefined);};
  d.w=function(t){return doc.getTextWidth(String(t==null?'':t));};
  d.wrap=function(t,w){return doc.splitTextToSize(String(t==null?'':t),w);};
  d.rect=function(x,y,w,h,fill,stroke,lw,r){if(fill)doc.setFillColor(fill);if(stroke){doc.setDrawColor(stroke);doc.setLineWidth(lw||1);}var m=fill&&stroke?'FD':(fill?'F':'D');if(r)doc.roundedRect(x,y,w,h,r,r,m);else doc.rect(x,y,w,h,m);};
  d.img=function(im,x,y,w,h){if(im)try{doc.addImage(im.data,'PNG',x,y,w,h,undefined,'FAST');}catch(e){}};
  d.fit=function(im,x,y,bw,bh,pad){if(!im)return;pad=pad||0;var r=Math.min((bw-2*pad)/im.w,(bh-2*pad)/im.h);d.img(im,x+(bw-im.w*r)/2,y+(bh-im.h*r)/2,im.w*r,im.h*r);};
  d.line=function(x1,y1,x2,y2,col,lw){doc.setDrawColor(col);doc.setLineWidth(lw);doc.line(x1,y1,x2,y2);};
  return d;
}
function sign(d,x,y,w,a,sym){
  var h=w*376/573;
  d.rect(x,y,w,h,'#ffffff',RED,2,3);
  var ss=h*0.58;d.img(sym,x+w*0.035,y+(h-ss)/2-1,ss,ss);
  var m=(a.sched||'').match(/^(.*?),\s*(.*)$/);
  var day=compactDays(a.days)||(m?m[1]:a.sched||'').toUpperCase();
  var tm=(m?m[2]:'').replace(/\s+to\s+/,' - ').replace(/:00/g,'').replace(/ (AM|PM)/g,'$1');
  var tx=x+w*0.035+ss+w*0.03,tw=x+w-tx-w*0.04,cx=tx+tw/2;
  var ts=8;d.sans(ts,RED);while(d.w(tm)>tw&&ts>4){ts-=.25;d.sans(ts,RED);}d.text(tm,cx,y+h*0.30,'center');
  var ds=day.length>8?9.5:(day.length>6?11.5:13.5);d.sans(ds,RED);while(d.w(day)>tw&&ds>4){ds-=.25;d.sans(ds,RED);}d.text(day,cx,y+h*0.58,'center');
  var ay=y+h*0.79,al=Math.min(27,tw*0.75),ah=al*0.2;
  d.line(cx-al/2+ah,ay,cx+al/2,ay,RED,Math.max(1.4,al*0.1));
  d.doc.setFillColor(RED);d.doc.triangle(cx-al/2,ay,cx-al/2+ah*1.8,ay-ah,cx-al/2+ah*1.8,ay+ah,'F');
  var fs=Math.max(2.6,Math.min(4,w/143));d.mono(fs,RED);d.text('DEPT OF TRANSPORTATION',x+w/2,y+h-4.5,'center');
  var tg=Math.min(47,w*0.46),t3=Math.max(4,Math.min(6,tg/8));
  d.rect(x+w-tg-3,y+3,tg,t3+4,RED,null,0,2);d.sans(t3,'#ffffff');d.text((a.side||'').toUpperCase(),x+w-tg/2-3,y+t3+4.3,'center');
  return h;
}
function drawMap(d,x,y,w,h,small){
  d.rect(x,y,w,h,'#fbfaf7',C0,1.2);
  var MLAT=111320,MLON=84400;
  function tm(p){return [(p[0]-D.mid[1])*MLON,(p[1]-D.mid[0])*MLAT];}
  var lg=D.lines.reduce(function(a,b){return b.length>a.length?b:a;},D.lines[0]);
  var bl=0;D.lines.forEach(function(ln){for(var i=0;i<ln.length-1;i++){var p1=tm(ln[i]),p2=tm(ln[i+1]);bl+=Math.hypot(p2[0]-p1[0],p2[1]-p1[1]);}});bl=bl||80;
  var sc=Math.max(.12,Math.min(Math.min(w,h)*0.46/bl,.55));
  var cx=x+w/2,cy=y+h/2;
  function px(p){var m=tm(p);return [cx+m[0]*sc,cy-m[1]*sc];}
  function clip(a,b){var x0=x+1,y0=y+1,x1=x+w-1,y1=y+h-1,t0=0,t1=1,dx=b[0]-a[0],dy=b[1]-a[1];var P=[-dx,dx,-dy,dy],Q=[a[0]-x0,x1-a[0],a[1]-y0,y1-a[1]];
    for(var i=0;i<4;i++){if(P[i]===0){if(Q[i]<0)return null;}else{var t=Q[i]/P[i];if(P[i]<0){if(t>t1)return null;if(t>t0)t0=t;}else{if(t<t0)return null;if(t<t1)t1=t;}}}
    return [[a[0]+t0*dx,a[1]+t0*dy],[a[0]+t1*dx,a[1]+t1*dy]];}
  (D.near||[]).forEach(function(sg){var pts=sg[1].map(px);for(var i=0;i<pts.length-1;i++){var c=clip(pts[i],pts[i+1]);if(c)d.line(c[0][0],c[0][1],c[1][0],c[1][1],'#c9c5bc',small?1.6:2.2);}});
  D.lines.forEach(function(ln){var pts=ln.map(px);for(var i=0;i<pts.length-1;i++){var c=clip(pts[i],pts[i+1]);if(c)d.line(c[0][0],c[0][1],c[1][0],c[1][1],ORANGE,small?4.5:7);}});
  var placed=[];
  function hit(a,b){return !(a[2]<b[0]-3||b[2]<a[0]-3||a[3]<b[1]-3||b[3]<a[1]-3);}
  function tag(t,p,fill,col,sz){
    d.sans(sz,col);var tw=d.w(t)+9,th=sz+5;
    var rads=[0,16,28,42,58,76],dirs=[[0,0],[0,-1],[0,1],[1,0],[-1,0],[-.75,-.75],[.75,-.75],[-.75,.75],[.75,.75]];
    var best=null,bs=1e9,bo=[0,0];
    for(var ri=0;ri<rads.length;ri++)for(var di=0;di<dirs.length;di++){
      if(rads[ri]===0&&di>0)continue;
      var c=[p[0]+dirs[di][0]*rads[ri],p[1]+dirs[di][1]*rads[ri]];
      var r=[c[0]-tw/2,c[1]-th/2,c[0]+tw/2,c[1]+th/2];
      var s=(r[0]>=x+2&&r[1]>=y+2&&r[2]<=x+w-2&&r[3]<=y+h-2)?0:60;
      for(var k=0;k<placed.length;k++)if(hit(r,placed[k]))s+=40;
      s+=rads[ri]*0.02;
      if(s<bs){bs=s;best=r;bo=c;}
      if(bs<0.5)break;
    }
    placed.push(best);
    d.rect(bo[0]-tw/2,bo[1]-th/2,tw,th,fill,col,1,3);d.sans(sz,col);d.text(t,bo[0],bo[1]+sz*0.35,'center');
  }
  var pa=px(lg[0]),pb=px(lg[lg.length-1]),pm=[(pa[0]+pb[0])/2,(pa[1]+pb[1])/2];
  tag(D.from.split(' & ')[0],pa,'#ffffff',C0,small?6:7);
  tag(D.to.split(' & ')[0],pb,'#ffffff',C0,small?6:7);
  tag(D.st,pm,C0,'#ffffff',small?7:8);
}
function assets(){
  return Promise.all([
    load('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'),
    fetch('/assets/pdf-fonts.json').then(function(r){return r.json();}).catch(function(){return null;}),
    img('/assets/blocks/sealtile-'+pfx+'.png'),
    img('/assets/blocks/asp-symbol.png'),
    Promise.all(['dsny-trash','dsny-recycle','dsny-compost','dsny-truck','lpc-seal','mailbox'].map(function(n){return img('/assets/blocks/'+n+'.png');})),
    Promise.all(['dcp','boe','bpl','nypl','qpl','311'].map(function(n){return img('/site-icons/agencies/'+n+'.png');})),
    Promise.all((D.ents||[]).map(function(e){return img(e.logo);})),
    qrImg('https://bkcb6.app'+(pfx==='bk'?'/block/':'/block/'+pfx+'/')+D.slug+'/')
  ]);
}
function libIcon(ag,lb){return lb?({BPL:ag[2],NYPL:ag[3],QPL:ag[4]})[lb.sys]||ag[1]:ag[1];}

function buildFull(){
  return assets().then(function(r){
    var fonts=r[1],seal=r[2],sym=r[3],ic=r[4],ag=r[5],logos=r[6],qr=r[7];
    var W=612,H=792,M=30,d=makeDoc(window.jspdf.jsPDF,fonts,W,H);
    var HB=108;
    d.rect(0,0,W,HB,C0);d.rect(0,HB,W,4,C1);
    var sz=84,words=['MY',BNM.toUpperCase(),'BLOCK'];
    d.sans(14);var wmw=Math.max(d.w(words[0]),d.w(words[1]),d.w(words[2]));
    var sx=W-M-(sz+10+wmw);
    d.img(seal,sx,(HB-sz)/2,sz,sz);
    d.sans(14,'#ffffff');words.forEach(function(w,i){d.text(w,sx+sz+10,(HB-3*16)/2+12+i*16);});
    var avail=sx-M-16,st=D.st,ts=32;d.sans(ts);while(d.w(st)>avail&&ts>14){ts-=1;d.sans(ts);}
    d.sans(ts,'#ffffff');d.text(st,M,42);
    var cross='between '+D.from+' and '+D.to,cs=15;d.sans(cs);while(d.w(cross)>avail&&cs>9){cs-=.5;d.sans(cs);}
    d.sans(cs,C1);var ly=42+ts*0.74;d.wrap(cross,avail).slice(0,2).forEach(function(l){d.text(l,M,ly);ly+=cs+3;});
    d.mono(6.8,'#c9cfe0');d.text(d.wrap(BNM.toUpperCase()+' COMMUNITY BOARD '+(D.cd%100)+(D.hn?'  \u00b7  '+D.hn.toUpperCase():''),avail)[0],M,Math.min(ly+12,HB-8));
    var G=12,colW=(W-2*M-G)/2,colL=M,colR=M+colW+G,y=HB+16,rowH=132;
    var dsn=(D.dsny||[])[0]||{};
    var dt=[['Trash',dsn.refuse||'n/a',ic[0]],['Recycling',dsn.recycling||'n/a',ic[1]],['Compost',dsn.organics||'not on this route yet',ic[2]],['Bulk items',dsn.bulk||'none scheduled',ic[3]]];
    var gw=(colW-4)/2,gh=(rowH-4)/2;
    dt.forEach(function(t,i){var x=colL+(i%2)*(gw+4),yy=y+Math.floor(i/2)*(gh+4);
      d.rect(x,yy,gw,gh,'#ffffff','#e5e2db',.8,4);
      var isz=48;d.fit(t[2],x+8,yy+(gh-isz)/2,isz,isz);
      var tx=x+isz+15;d.mono(7,MUTED);d.text(t[0].toUpperCase(),tx,yy+20);
      var vl=d.wrap(t[1],gw-isz-22),fs=vl.length>2?9.5:(vl.length>1?11.5:13.5);
      d.sans(fs,NAVY);d.wrap(t[1],gw-isz-22).slice(0,3).forEach(function(l,j){d.text(l,tx,yy+36+j*(fs+2));});});
    var sw=(colW-4)/2,asp=(D.asp||[]).slice(0,2);
    if(asp.length){
      if(asp.length===1){var pr={'North side':'South side','South side':'North side','East side':'West side','West side':'East side'};asp=asp.concat([{missing:true,side:pr[asp[0].side]||'Other side'}]);}
      asp.forEach(function(a,i){var x=colR+i*(sw+4);d.rect(x,y,sw,rowH,'#ffffff','#e5e2db',.8,4);
        var iw=sw-12,ih=iw*376/573;
        if(a.missing){d.rect(x+6,y+6,iw,ih,null,'#c9c5bc',1.2,3);d.mono(6,MUTED);d.text(a.side.toUpperCase(),x+6+iw/2,y+6+ih*0.4,'center');
          d.body(6.8,'#444444');d.wrap('No alternate side rule on file for this side. Check the posted signs.',iw-8).forEach(function(l,j){d.text(l,x+6+iw/2,y+6+ih*0.58+j*8,'center');});
          d.mono(6.5,MUTED);d.text(('Alternate side, '+a.side).toUpperCase(),x+6,y+ih+18);return;}
        sign(d,x+6,y+6,iw,a,sym);d.mono(6.5,MUTED);d.text(('Alternate side, '+a.side).toUpperCase(),x+6,y+ih+18);
        d.body(6.8,'#444444');d.text('next '+nextOf(a.days),x+6,y+ih+27);});
    } else {d.rect(colR,y,colW,rowH,'#ffffff','#e5e2db',.8,4);d.mono(6.5,MUTED);d.text('ALTERNATE SIDE PARKING',colR+9,y+16);d.sans(10,NAVY);d.text('No rules on file for this block',colR+9,y+34);}
    y+=rowH+G;
    var mh=112;drawMap(d,colL,y,colW,mh,false);
    var fw=(colW-4)/2,ry=y,fh=44;
    function fact(x,yy,w,h,k,v,s2,im,col){
      d.rect(x,yy,w,h,'#ffffff',col,1.2,5);
      var isz=h-10;d.fit(im,x+5,yy+5,isz,isz,1);
      var tx=x+isz+10,tw=w-isz-15;
      d.mono(5.4,MUTED);d.text(d.wrap(k.toUpperCase(),tw)[0],tx,yy+10);
      d.sans(8.4,col);d.text(d.wrap(v,tw)[0],tx,yy+21);
      if(s2){d.body(6.2,'#444444');d.wrap(s2,tw).slice(0,2).forEach(function(l,j){d.text(l,tx,yy+30+j*7.5);});}
    }
    fact(colR,ry,fw,fh,'Zoning',(D.zones||[]).join(' \u00b7 ')||'Not on file','',ag[0],C0);
    if((D.hist||[]).length)fact(colR+fw+4,ry,fw,fh,'Historic district, '+((D.hist_side||[])[0]||''),D.hist[0].replace(' Historic District',''),'Exterior work needs an LPC permit',ic[4],'#8b1a1a');
    else fact(colR+fw+4,ry,fw,fh,'Report a problem','Call 311','Noise, sanitation, streets, heat',ag[5],C0);
    ry+=fh+4;
    var mb=D.mail,lb=D.lib;
    fact(colR,ry,fw,fh,'Closest mail box',mb?mb.addr:'None found',mb?((mb.m<=40?'On this block. ':(mb.m+' m away. '))+(mb.times?'Pickup '+mb.times:'')):'',ic[5],C0);
    fact(colR+fw+4,ry,fw,fh,'Closest library',lb?lb.name:'None found',lb?(lb.addr.split(',')[0]+' \u00b7 '+lb.phone):'',libIcon(ag,lb),C0);
    ry+=fh+4;
    var e0=(D.eds||[])[0];
    d.rect(colR,ry,colW,46,'#ffffff',C0,1.2,5);
    d.fit(ag[1],colR+5,ry+8,30,30,1);
    d.mono(5.4,MUTED);d.text('VOTE TUESDAY, NOVEMBER 3, 2026',colR+42,ry+12);
    if(e0&&e0.site){d.sans(6.6,C0);d.text('ELECTION DAY',colR+42,ry+24);var w1=d.w('ELECTION DAY')+8;d.sans(8.4,NAVY);d.text(d.wrap(e0.site[0],(colW-52-w1)*0.6)[0],colR+42+w1,ry+24);
      d.body(6,'#555555');d.text(d.wrap(stripCity(e0.site[1]),colW-52)[0],colR+42,ry+33);}
    if(e0&&e0.early){d.sans(6.6,'#8b1a1a');d.text('EARLY VOTING',colR+42,ry+42);var w2=d.w('EARLY VOTING')+8;d.sans(8.4,NAVY);d.text(d.wrap(e0.early[0],(colW-52-w2)*0.75)[0],colR+42+w2,ry+42);}
    ry+=50;
    y+=Math.max(mh,ry-y)+G;
    var ents=D.ents||[],per=4,gap=8,tw2=(W-2*M-(per-1)*gap)/per;
    var rows=Math.ceil(ents.length/per),avail2=(H-92)-8-y,txth=34;
    var lsz=Math.min(tw2,(avail2-(rows-1)*gap)/rows-txth-11),th2=lsz+txth+11;
    ents.forEach(function(e,i){var x=M+(i%per)*(tw2+gap),yy=y+Math.floor(i/per)*(th2+gap);
      d.mono(5.4,C0);d.text(d.wrap(e.k.toUpperCase(),tw2)[0],x+1,yy+7);
      d.rect(x,yy+11,tw2,lsz,'#ffffff','#d6d3d1',1,8);
      d.fit(logos[i],x,yy+11,tw2,lsz,5);
      var ty=yy+11+lsz+9;d.sans(7.6,NAVY);var nl=d.wrap(e.name,tw2);
      d.text(nl[0],x+1,ty);ty+=8;if(nl[1]){d.text(nl[1],x+1,ty);ty+=8;}
      d.body(5.7,'#444444');(e.lines||[]).filter(Boolean).forEach(function(l){var w=d.wrap(l,tw2)[0];if(ty<yy+th2+2){d.text(w,x+1,ty);ty+=6.6;}});});
    var fy=H-92;d.rect(0,fy,W,92,CREAM);d.rect(0,fy,W,3,C1);d.rect(0,fy+3,W,1.2,C0);
    d.img(qr,M,fy+11,70,70);
    d.sans(11,C0);d.text('Scan for the live version of this card',M+82,fy+28);
    d.mono(8,C0);d.text('bkcb6.app'+(pfx==='bk'?'/block/':'/block/'+pfx+'/')+D.slug+'/',M+82,fy+42);
    d.body(7.5,'#444444');d.wrap('Next dates, suspensions and permits update live on the web card. Sources: DOT street centerline and parking signs, DSNY collection frequencies, NYC Board of Elections poll sites, PLUTO zoning, USPS collection boxes, NYC district boundary files. Confirm alternate side suspensions on 311.',W-M-(M+82)).forEach(function(l,i){d.text(l,M+82,fy+56+i*9);});
    d.mono(6.5,MUTED);d.text('BROOKLYN COMMUNITY BOARD 6  \u00b7  250 BALTIC STREET  \u00b7  (718) 643-3027  \u00b7  INFO@BKCB6.ORG  \u00b7  GENERATED '+new Date().toISOString().slice(0,10),M,H-8);
    d.doc.save('block-card-'+D.slug+'.pdf');
  });
}

function buildFridge(){
  return assets().then(function(r){
    var fonts=r[1],seal=r[2],sym=r[3],ic=r[4],ag=r[5],logos=r[6],qr=r[7];
    var W=288,H=432,M=10,d=makeDoc(window.jspdf.jsPDF,fonts,W,H);
    var HB=58;
    d.rect(0,0,W,HB,C0);d.rect(0,HB,W,3,C1);
    var sz=42;d.img(seal,W-M-sz,(HB-sz)/2,sz,sz);
    var avail=W-2*M-sz-52,st=D.st,ts=19;d.sans(ts);while(d.w(st)>avail&&ts>10){ts-=1;d.sans(ts);}
    d.sans(ts,'#ffffff');d.text(st,M,24);
    var cross='between '+D.from+' and '+D.to,cs=9;d.sans(cs);while(d.w(cross)>avail&&cs>6.5){cs-=.5;d.sans(cs);}
    d.sans(cs,C1);d.text(d.wrap(cross,avail)[0],M,24+ts*0.78);
    d.mono(5,'#c9cfe0');d.text(BNM.toUpperCase()+' CB'+(D.cd%100)+(D.hn?'  \u00b7  '+D.hn.toUpperCase():''),M,HB-6);
    d.sans(6,'#ffffff');['MY',BNM.toUpperCase(),'BLOCK'].forEach(function(w,i){d.text(w,W-M-sz-6,20+i*7,'right');});
    var y=HB+9,cw=W-2*M;
    var sw=(cw-8)/3*0.92,ih=sw*376/573;
    var asp=(D.asp||[]).slice(0,2);
    if(asp.length){
      if(asp.length===1){var pr={'North side':'South side','South side':'North side','East side':'West side','West side':'East side'};asp=asp.concat([{missing:true,side:pr[asp[0].side]||'Other side'}]);}
      asp.forEach(function(a,i){var x=M+i*(sw+4);
        if(a.missing){d.rect(x,y,sw,ih,null,'#c9c5bc',1,3);d.mono(4.6,MUTED);d.text(a.side.toUpperCase(),x+sw/2,y+ih*0.42,'center');
          d.body(4.6,'#444444');d.wrap('No rule on file. Check signs.',sw-6).forEach(function(l,j){d.text(l,x+sw/2,y+ih*0.62+j*6,'center');});}
        else sign(d,x,y,sw,a,sym);
        d.body(5,'#333333');d.text(d.wrap(a.side+(a.missing?'':' \u00b7 next '+nextOf(a.days)),sw)[0],x+1,y+ih+7);});
    } else {d.rect(M,y,2*sw+4,ih,'#ffffff','#e5e2db',.8,4);d.mono(4.8,MUTED);d.text('ALTERNATE SIDE PARKING',M+6,y+13);d.sans(8,NAVY);d.wrap('No rules on file for this block',2*sw-8).slice(0,2).forEach(function(l,j){d.text(l,M+6,y+26+j*10);});}
    drawMap(d,M+2*(sw+4),y,cw-2*(sw+4),ih,true);
    y+=ih+13;
    var dsn=(D.dsny||[])[0]||{};
    var dt=[['Trash',dsn.refuse||'n/a',ic[0]],['Recycling',dsn.recycling||'n/a',ic[1]],['Compost',dsn.organics||'not on route yet',ic[2]],['Bulk',dsn.bulk||'none',ic[3]]];
    var gw=(cw-5)/2,gh=40;
    dt.forEach(function(t,i){var x=M+(i%2)*(gw+5),yy=y+Math.floor(i/2)*(gh+4);
      d.rect(x,yy,gw,gh,'#ffffff','#e5e2db',.8,4);
      var isz=gh-10;d.fit(t[2],x+5,yy+5,isz,isz);
      var tx=x+isz+10;d.mono(5.4,MUTED);d.text(t[0].toUpperCase(),tx,yy+13);
      var fs=12;d.sans(fs,NAVY);var vl=d.wrap(t[1],gw-isz-14);while(vl.length>1&&fs>8){fs-=.5;d.sans(fs,NAVY);vl=d.wrap(t[1],gw-isz-14);}
      vl.slice(0,2).forEach(function(l,j){d.text(l,tx,yy+(vl.length>1?22:27)+j*(fs+1));});});
    y+=2*(gh+4)+4;
    var fh=30,fw=(cw-5)/2,mb=D.mail,lb=D.lib;
    function fact(x,yy,w,k,v,s2,im){
      d.rect(x,yy,w,fh,'#ffffff',C0,1,4);
      d.fit(im,x+4,yy+4,fh-8,fh-8,1);
      d.mono(4.6,MUTED);d.text(d.wrap(k.toUpperCase(),w-fh-6)[0],x+fh+3,yy+10);
      d.sans(7.6,C0);d.text(d.wrap(v,w-fh-6)[0],x+fh+3,yy+20);
      if(s2){d.body(5,'#444444');d.text(d.wrap(s2,w-fh-6)[0],x+fh+3,yy+28);}
    }
    fact(M,y,fw,'Closest mail box',mb?mb.addr:'None',mb?(mb.m<=40?'on this block':(mb.m+' m away')):'',ic[5]);
    fact(M+fw+5,y,fw,'Closest library',lb?lb.name:'None',lb?lb.phone:'',libIcon(ag,lb));
    y+=fh+4;
    var e0=(D.eds||[])[0],vh=44;
    d.rect(M,y,cw,vh,'#ffffff',C0,1,4);
    d.fit(ag[1],M+5,y+(vh-24)/2,24,24,1);
    var tx0=M+34,tw0=cw-38;
    d.mono(4.6,MUTED);d.text('VOTE TUESDAY, NOVEMBER 3, 2026',tx0,y+9);
    d.rect(tx0,y+13,3,11,C0);d.sans(6,C0);d.text('ELECTION DAY',tx0+7,y+18);
    var dlw=d.w('ELECTION DAY')+13;
    d.sans(8,NAVY);var nm=d.wrap(e0&&e0.site?e0.site[0]:'See BOE',(tw0-dlw)*0.42)[0];d.text(nm,tx0+dlw,y+21);var nw=d.w(nm);
    if(e0&&e0.site){d.body(5.2,'#555555');d.text(d.wrap(stripCity(e0.site[1]),tw0-dlw-nw-8)[0],tx0+dlw+nw+8,y+21);}
    d.rect(tx0,y+27,3,11,'#8b1a1a');d.sans(6,'#8b1a1a');d.text('EARLY VOTING',tx0+7,y+32);
    d.mono(4.4,'#8b1a1a');d.text('OCT 24 - NOV 1',tx0+7,y+38.5);
    var elw=Math.max(d.w('OCT 24 - NOV 1'),0)+17;
    d.sans(8,NAVY);var evn=d.wrap(e0&&e0.early?e0.early[0]:'see BOE',(tw0-elw)*0.55)[0];d.text(evn,tx0+elw,y+35);var ew=d.w(evn);
    if(e0&&e0.early){d.body(5.2,'#555555');d.text(d.wrap(stripCity(e0.early[1]),tw0-elw-ew-8)[0],tx0+elw+ew+8,y+35);}
    y+=vh+6;
    var ents=(D.ents||[]).slice(0,8),per=4,gap=4,tw=(cw-(per-1)*gap)/per,qrs=42,bottom=H-M-qrs-14;
    var rows=Math.ceil(ents.length/per),lsz=Math.min(tw,(bottom-y-rows*8)/rows);
    d.mono(5,C0);d.text('WHO REPRESENTS THIS BLOCK',M,y+3);y+=7;
    ents.forEach(function(e,i){var x=M+(i%per)*(tw+gap),yy=y+Math.floor(i/per)*(lsz+8);
      d.rect(x,yy,tw,lsz,'#ffffff','#d6d3d1',.8,4);
      d.fit(logos[i],x,yy,tw,lsz,2.5);
      d.mono(3.9,MUTED);d.text(d.wrap(e.name.replace('Community School District','CSD').replace(/(Brooklyn|Manhattan|Queens|Bronx|Staten Island) Community Board/,'CB'),tw)[0],x+tw/2,yy+lsz+6,'center');});
    var qy=H-M-qrs;
    d.rect(0,qy-4,W,H-(qy-4),CREAM);d.rect(0,qy-4,W,1.5,C1);
    d.img(qr,M,qy,qrs,qrs);
    d.sans(7.5,C0);d.text('Scan for the live card',M+qrs+7,qy+11);
    d.body(5,'#444444');d.wrap('Contacts, poll site details, permits and 311 reports for this block, updated daily at bkcb6.app'+(pfx==='bk'?'/block/':'/block/'+pfx+'/')+D.slug,W-M-(M+qrs+7)).slice(0,4).forEach(function(l,i){d.text(l,M+qrs+7,qy+20+i*5.6);});
    d.mono(4.2,MUTED);d.text('BROOKLYN COMMUNITY BOARD 6  \u00b7  250 BALTIC ST  \u00b7  INFO@BKCB6.ORG',M,H-4);
    d.doc.save('fridge-card-'+D.slug+'.pdf');
  });
}
function wire(id,fn,label){
  var b=document.getElementById(id);if(!b)return;
  b.addEventListener('click',function(){
    b.textContent='Building\u2026';b.disabled=true;
    fn().catch(function(e){console.error(e);}).then(function(){b.textContent=label;b.disabled=false;});
  });
}
wire('pdfBtn',buildFull,'One-page PDF');
wire('fridgeBtn',buildFridge,'Fridge card');
})();
