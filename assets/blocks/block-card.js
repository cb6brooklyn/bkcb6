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
