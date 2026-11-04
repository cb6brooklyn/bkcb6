/* Apple Map (MapKit JS) for an election district page: bkcb6.app/ed/<AADDD>/
   <div id="edmap" data-ed="52046" data-nb="52034,52045"></div> plus a toggle row #edtg.
   Draws the ED, its neighbors (tap to open their page) and, on request, the districts it is part of. */
(function(){
var TOKEN='eyJraWQiOiI0SjZVQlRDRFpEIiwidHlwIjoiSldUIiwiYWxnIjoiRVMyNTYifQ.eyJpc3MiOiJGN0hGR1Y1UVIyIiwiaWF0IjoxNzkzNzQ5OTEyLCJvcmlnaW4iOiJia2NiNi5hcHAiLCJzY29wZSI6Im1hcGtpdF9qcyJ9.LpYs4ZPhfyWiHXBTv_qniPsZ-ciCJhQ-aCjQOuWsfIpQ6HFKgQGNGYlFEoci3dSys9c4oh5Te8dbp3N1R9vMyw';
var el=document.getElementById('edmap');if(!el||!window.mapkit)return;
var ED=el.dataset.ed,NB=(el.dataset.nb||'').split(',').filter(Boolean);
var LCOL={ad:'#2e7d32',sd:'#6a1b9a',cd:'#c62828',cc:'#00796b',mc:'#8d4b2b',cb:'#0d1b4b',bo:'#1a3e8c'};
mapkit.init({authorizationCallback:function(done){done(TOKEN)},language:'en'});
var map=new mapkit.Map(el,{showsCompass:mapkit.FeatureVisibility.Hidden,showsZoomControl:true,showsMapTypeControl:true,isRotationEnabled:false,showsPointsOfInterest:false});
function C(c){return new mapkit.Coordinate(c[1],c[0])}
function rings(g){var o=[];(g.type==='Polygon'?[g.coordinates]:g.coordinates).forEach(function(p){p.forEach(function(r){o.push(r.map(C))})});return o}
function S(o){return new mapkit.Style({fillColor:o.f||'#000',fillOpacity:o.fo||0,strokeColor:o.s,strokeOpacity:o.so==null?1:o.so,lineWidth:o.w||1,fillRule:'evenodd'})}
var P=null,main=null,nbo={},LAY={},LD=null;
function inRing(x,y,r){var ins=false;for(var i=0,j=r.length-1;i<r.length;j=i++){var xi=r[i][0],yi=r[i][1],xj=r[j][0],yj=r[j][1];if(((yi>y)!==(yj>y))&&(x<(xj-xi)*(y-yi)/(yj-yi)+xi))ins=!ins}return ins}
function hit(g,x,y){var ps=g.type==='Polygon'?[g.coordinates]:g.coordinates;for(var i=0;i<ps.length;i++){if(inRing(x,y,ps[i][0])){var h=false;for(var k=1;k<ps[i].length;k++)if(inRing(x,y,ps[i][k]))h=true;if(!h)return true}}return false}
var NBF=[];
fetch('/electionexplainer/map/eds.geojson').then(function(r){return r.json()}).then(function(d){
  d.features.forEach(function(f){var id=f.properties.id;
    if(id===ED){P=f.properties;main=new mapkit.PolygonOverlay(rings(f.geometry),{style:S({s:'#f47920',w:4,f:'#f47920',fo:.22}),enabled:false})}
    else if(NB.indexOf(id)>=0){NBF.push(f);nbo[id]=new mapkit.PolygonOverlay(rings(f.geometry),{style:S({s:'#3d4a72',w:1.5,so:.85,f:'#9aa3b8',fo:.08}),enabled:false})}});
  var ov=Object.keys(nbo).map(function(k){return nbo[k]});map.addOverlays(ov);if(main){map.addOverlay(main);map.showItems([main],{animate:false,padding:new mapkit.Padding(110,110,110,110)})}
  NBF.forEach(function(f){var g=f.geometry,ps=g.type==='Polygon'?[g.coordinates]:g.coordinates,sx=0,sy=0,n=0;ps[0][0].forEach(function(c){sx+=c[0];sy+=c[1];n++});
    var a=new mapkit.Annotation(new mapkit.Coordinate(sy/n,sx/n),function(){var x=document.createElement('a');x.href='/ed/'+f.properties.id+'/';x.textContent='ED '+parseInt(f.properties.id.slice(2),10);x.style.cssText='font:700 11px DM Sans,sans-serif;color:#0d1b4b;background:rgba(255,255,255,.9);border:1px solid #c9ccd6;border-radius:999px;padding:2px 7px;text-decoration:none;white-space:nowrap';return x},{displayPriority:mapkit.Annotation.DisplayPriority.Low,anchorOffset:new DOMPoint(0,0)});map.addAnnotation(a)});
}).catch(function(){});
map.addEventListener('single-tap',function(ev){var c=map.convertPointOnPageToCoordinate(ev.pointOnPage);for(var i=0;i<NBF.length;i++)if(hit(NBF[i].geometry,c.longitude,c.latitude)){location.href='/ed/'+NBF[i].properties.id+'/';return}});
function part(k){if(!P)return null;if(k==='ad')return String(parseInt(ED.slice(0,2),10));if(k==='cb'||k==='bo'||k==='mc')return P[k];return P[k]?String(parseInt(P[k],10)):null}
function layer(k,on){if(!on){if(LAY[k])map.removeOverlays(LAY[k]);return}
  if(LAY[k]){map.addOverlays(LAY[k]);return}
  var go=function(){var mine=part(k);LAY[k]=LD[k].features.map(function(f){var me=String(f.properties.id)===String(mine);return new mapkit.PolygonOverlay(rings(f.geometry),{style:S({s:LCOL[k],w:me?4:1.6,so:me?1:.7,f:LCOL[k],fo:me?.07:0}),enabled:false})});map.addOverlays(LAY[k]);if(main){map.removeOverlay(main);map.addOverlay(main)}};
  if(LD)go();else fetch('/electionexplainer/map/layers.json').then(function(r){return r.json()}).then(function(d){LD=d;go()})}
[].forEach.call(document.querySelectorAll('#edtg button'),function(b){b.onclick=function(){var on=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',on);var k=b.dataset.l;
  if(k==='nb'){var ov=Object.keys(nbo).map(function(x){return nbo[x]});if(on)map.addOverlays(ov);else map.removeOverlays(ov)}else layer(k,on)}});
})();
