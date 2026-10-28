/* Median household income over time: a community district, its borough and New York City.
   Drop <div class="inchist" data-cd="BKCB6"></div> on a page (data-mode="boroughs" draws the five boroughs and the city).
   Data: /data/income-history.json (scripts/update_income.py).
     district: Census American Community Survey 1-year estimates (B19013), 2012 onward
     borough:  Census Small Area Income and Poverty Estimates, 1989 onward
     city:     American Community Survey 1-year estimates, 2010 onward
   Dollars of each year, not adjusted for inflation. */
(function(){
  var BORO={MN:'Manhattan',BX:'Bronx',BK:'Brooklyn',QN:'Queens',SI:'Staten Island'};
  var COLS={Manhattan:'#67000D',Brooklyn:'#f47920',Queens:'#1B5E8A',Bronx:'#82C341','Staten Island':'#8a6d3b'};
  var css='.inchist{background:#fff;border-top:3px solid #f47920;font-family:"DM Sans",sans-serif;color:#222}'+
    '.inchist .ih-h{background:#0d1b4b;color:#fff;padding:11px 16px;display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}'+
    '.inchist .ih-t{font-size:1rem;font-weight:800}.inchist .ih-s{font-family:"DM Mono",monospace;font-size:.62rem;color:rgba(255,255,255,.65);text-transform:uppercase;letter-spacing:.06em}'+
    '.inchist .ih-pick{padding:10px 16px 0}.inchist select{padding:8px 10px;font-family:"DM Sans",sans-serif;font-size:.8rem;border:2px solid #132D65;border-radius:8px;color:#132D65;font-weight:600;background:#fff;max-width:100%}'+
    '.inchist .ih-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:#e5e2db;margin:10px 0 0;border-top:1px solid #e5e2db;border-bottom:1px solid #e5e2db}'+
    '.inchist .ih-c{background:#fff;padding:10px 14px}.inchist .ih-l{font-family:"DM Mono",monospace;font-size:.56rem;text-transform:uppercase;letter-spacing:.07em;color:#6b6760}'+
    '.inchist .ih-v{font-size:1.15rem;font-weight:800;color:#0d1b4b;margin-top:2px}.inchist .ih-d{font-size:.66rem;color:#6b6760;margin-top:1px}'+
    '.inchist .ih-ctl{display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:10px 16px;background:#f8f7f4;border-bottom:1px solid #e5e2db}'+
    '.inchist .ih-ctl .lb{font-family:"DM Mono",monospace;font-size:.56rem;text-transform:uppercase;letter-spacing:.08em;color:#6b6760;font-weight:700;margin-right:4px}'+
    '.inchist .ih-ctl button{padding:6px 12px;font-family:"DM Sans",sans-serif;font-size:.76rem;font-weight:700;border:2px solid #132D65;border-radius:20px;background:#fff;color:#132D65;cursor:pointer}'+
    '.inchist .ih-ctl button.on{background:#f47920;border-color:#f47920;color:#fff}'+
    '.inchist .ih-ch{position:relative;height:320px;padding:10px 12px}.inchist .ih-n{padding:4px 16px 14px;font-size:.66rem;line-height:1.55;color:#6b6760}';
  function money(v){return v==null?'—':'$'+Math.round(v).toLocaleString('en-US');}
  function k(v){return v>=1e6?'$'+(v/1e6).toFixed(1)+'M':'$'+Math.round(v/1000)+'K';}
  var AJ=null;
  /* inflation: multiply a dollar figure of year y to express it in base-year dollars (CPI-U); 1 when "as reported" */
  function fac(el,y,which){if(!el._real||!AJ)return 1;var c=AJ['cpi_'+which],b=c[AJ.base],v=c[String(y)];return v?b/v:null;}
  function adj(el,v,y,which){if(v==null)return null;var f=fac(el,y,which);return f==null?null:v*f;}
  /* population for year y, or the latest year before it when this year's estimate is not out yet */
  function pop(which,y){if(!AJ)return null;var o=AJ['pop_'+which];for(var k=+y;k>=+y-2;k--)if(o[String(k)])return o[String(k)];return null;}
  function dlab(el){return el._real&&AJ?' (in '+AJ.base+' dollars)':'';}
  function cdName(c){return BORO[c.slice(0,2)]+' CB'+c.slice(4);}
  function first(o){var y=Object.keys(o).sort();return y.length?y[0]:null;}
  function last(o){var y=Object.keys(o).sort();return y.length?y[y.length-1]:null;}
  function needChart(cb){if(window.Chart)return cb();var s=document.createElement('script');s.src='https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js';s.onload=cb;document.head.appendChild(s);}
  function card(l,o0,el){var o={};Object.keys(o0||{}).forEach(function(y){var v=adj(el,o0[y],y,'ny');if(v!=null)o[y]=v;});var a=first(o),b=last(o);if(!b)return '';var ch=a&&a!==b?((o[b]/o[a]-1)*100):null;
    return '<div class="ih-c"><div class="ih-l">'+l+', '+b+'</div><div class="ih-v">'+money(o[b])+'</div><div class="ih-d">'+(ch==null?'':(ch>=0?'+':'')+ch.toFixed(0)+'% since '+a+' ('+money(o[a])+')')+'</div></div>';}
  function draw(el,D,cd){
    var A=D.acs,SA=D.saipe.boro,series=[],cards='';
    if(el.getAttribute('data-mode')==='boroughs'){
      Object.keys(COLS).forEach(function(b){series.push({label:b,o:SA[b],c:COLS[b]});cards+=card(b,SA[b],el);});
    }else{
      var b=BORO[cd.slice(0,2)],dist=A.cd[cd]||{};
      series.push({label:cdName(cd),o:dist,c:'#f47920',w:3});cards+=card(cdName(cd),dist,el);
      series.push({label:b,o:SA[b],c:'#1B5E8A'});cards+=card(b,SA[b],el);
    }
    series.push({label:'New York City',o:A.nyc,c:'#0d1b4b',dash:[5,3]});cards+=card('New York City',A.nyc,el);
    var ys={};series.forEach(function(s){Object.keys(s.o||{}).forEach(function(y){ys[y]=1;});});ys=Object.keys(ys).sort();
    el.querySelector('.ih-cards').innerHTML=cards;
    var sh=(A.shared[cd]||{})[last(A.cd[cd]||{})];
    el.querySelector('.ih-n').innerHTML=(el._real&&AJ?'Median household income adjusted for inflation to '+AJ.base+' dollars with the New York-area consumer price index (CPI-U, New York-Newark-Jersey City). ':'Median household income in dollars of each year, not adjusted for inflation. ')+
      (el.getAttribute('data-mode')==='boroughs'?'':'Community district: Census American Community Survey 1-year estimates, from 2012, the first year the Census labels its areas by district'+(sh?' (it shares one Census area with '+sh.map(cdName).join(', ')+')':'')+'. ')+
      'Borough: Census Small Area Income and Poverty Estimates, from 1989. New York City: American Community Survey 1-year estimates, from 2010. There are no standard 2020 1-year estimates.';
    if(el._chart)el._chart.destroy();
    el._chart=new Chart(el.querySelector('canvas'),{type:'line',data:{labels:ys,datasets:series.map(function(s){
      return {label:s.label,data:ys.map(function(y){return s.o&&s.o[y]!=null?adj(el,s.o[y],y,'ny'):null;}),borderColor:s.c,backgroundColor:s.c,borderWidth:s.w||2,pointRadius:2,borderDash:s.dash||[],spanGaps:true};})},
      options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},
        plugins:{legend:{labels:{boxWidth:10,font:{size:11,family:'DM Sans'}}},tooltip:{callbacks:{label:function(c){return c.dataset.label+': '+money(c.parsed.y);}}}},
        scales:{y:{ticks:{callback:k,font:{size:10}}},x:{ticks:{font:{size:10},maxTicksLimit:12}}}}});
  }
  /* For-sale pages: the 20% down payment on the median asking price (all homes), in dollars and in years of
     median household income. Price for a year = median of that year's monthly median asking prices
     (StreetEasy, /data/sales/rent-explorer.json, the all-homes series). */
  var SALE=true;   /* every rent and sale page carries the full section */
  var MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  function med(a){a=a.filter(function(x){return x!=null;}).sort(function(x,y){return x-y;});if(!a.length)return null;var m=a.length>>1;return a.length%2?a[m]:(a[m-1]+a[m])/2;}
  function priceSeries(SX,id){var a=SX.A[id];if(!a)return null;var v=a.s.studio[1],o=a.s.studio[0],by={},lastI=-1;
    v.forEach(function(x,i){var m=SX.months[i+o];if(x!=null){(by[m.slice(0,4)]=by[m.slice(0,4)]||[]).push(x);lastI=i+o;}});
    var yr={};Object.keys(by).forEach(function(y){yr[y]=med(by[y]);});return {yr:yr,now:lastI<0?null:a.s.studio[1][lastI-o],nowM:lastI<0?null:SX.months[lastI]};}
  function drawDown(el,D,SX,cd){
    var A=D.acs,SA=D.saipe.boro,list=[];
    if(el.getAttribute('data-mode')==='boroughs'){Object.keys(COLS).forEach(function(b){list.push({label:b,id:'b:'+b,inc:SA[b],c:COLS[b]});});}
    else{var b=BORO[cd.slice(0,2)];list.push({label:cdName(cd),id:'c:'+cd,inc:A.cd[cd]||{},c:'#f47920',w:3});list.push({label:b,id:'b:'+b,inc:SA[b],c:'#1B5E8A'});}
    list.push({label:'New York City',id:'x:NYC',inc:A.nyc,c:'#0d1b4b',dash:[5,3]});
    var cards='',ys={};
    list.forEach(function(s){var P=priceSeries(SX,s.id);s.P=P;if(!P)return;
      Object.keys(P.yr).forEach(function(y){if(s.inc[y]!=null)ys[y]=1;});
      var iy=last(s.inc),ny=P.nowM?P.nowM.slice(0,4):null,dp=P.now!=null?adj(el,P.now*.2,ny,'ny'):null;
      cards+='<div class="ih-c"><div class="ih-l">'+s.label+', '+(P.nowM?MON[+P.nowM.slice(5)-1]+' '+P.nowM.slice(0,4):'')+'</div><div class="ih-v">'+money(dp)+'</div><div class="ih-d">20% of '+money(adj(el,P.now,ny,'ny'))+dlab(el)+
        (P.now!=null&&iy?' &middot; '+(P.now*.2/s.inc[iy]).toFixed(1)+' years of '+iy+' median income ('+money(adj(el,s.inc[iy],iy,'ny'))+')':'')+'</div></div>';});
    ys=Object.keys(ys).sort();
    el.querySelector('.ih-dcards').innerHTML=cards;
    if(el._dchart)el._dchart.destroy();
    el._dchart=new Chart(el.querySelector('.ih-dch canvas'),{type:'line',data:{labels:ys,datasets:list.filter(function(s){return s.P;}).map(function(s){
      return {label:s.label,data:ys.map(function(y){var p=s.P.yr[y],i=s.inc[y];return p!=null&&i!=null?+(p*.2/i).toFixed(2):null;}),
        _dp:ys.map(function(y){var p=s.P.yr[y];return p!=null?adj(el,p*.2,y,'ny'):null;}),borderColor:s.c,backgroundColor:s.c,borderWidth:s.w||2,pointRadius:2,borderDash:s.dash||[],spanGaps:true};})},
      options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},
        plugins:{legend:{labels:{boxWidth:10,font:{size:11,family:'DM Sans'}}},tooltip:{callbacks:{label:function(c){var d=c.dataset._dp[c.dataIndex];return c.dataset.label+': '+money(d)+' down, '+c.parsed.y.toFixed(1)+' years of income';}}}},
        scales:{y:{title:{display:true,text:'Years of median household income',font:{size:10}},ticks:{font:{size:10}}},x:{ticks:{font:{size:10}}}}}});
  }
  /* Monthly cost: principal and interest on 80% of the median asking price (all homes), 30-year fixed at the
     year's average Freddie Mac rate (the latest month at that month's rate). Property tax rates: NYC DOF. */
  function yrRate(D,y){var v=[];Object.keys(D.mortgage.monthly).forEach(function(m){if(m.slice(0,4)===y)v.push(D.mortgage.monthly[m]);});
    return v.length?v.reduce(function(a,b){return a+b;},0)/v.length:null;}
  function pmt(price,rate){if(price==null||rate==null)return null;var L=price*.8,r=rate/1200;return L*r/(1-Math.pow(1+r,-360));}
  function drawMonthly(el,D,SX,cd){
    var A=D.acs,SA=D.saipe.boro,list=[];
    if(el.getAttribute('data-mode')==='boroughs'){Object.keys(COLS).forEach(function(b){list.push({label:b,id:'b:'+b,inc:SA[b],c:COLS[b]});});}
    else{var b=BORO[cd.slice(0,2)];list.push({label:cdName(cd),id:'c:'+cd,inc:A.cd[cd]||{},c:'#f47920',w:3});list.push({label:b,id:'b:'+b,inc:SA[b],c:'#1B5E8A'});}
    list.push({label:'New York City',id:'x:NYC',inc:A.nyc,c:'#0d1b4b',dash:[5,3]});
    var ys={},cards='';
    list.forEach(function(s){s.P=priceSeries(SX,s.id);if(!s.P)return;Object.keys(s.P.yr).forEach(function(y){ys[y]=1;});
      var r=s.P.nowM?D.mortgage.monthly[s.P.nowM]:null,m0=pmt(s.P.now,r),ny=s.P.nowM?s.P.nowM.slice(0,4):null,m=adj(el,m0,ny,'ny'),iy=last(s.inc);
      cards+='<div class="ih-c"><div class="ih-l">'+s.label+', '+(s.P.nowM?MON[+s.P.nowM.slice(5)-1]+' '+s.P.nowM.slice(0,4):'')+'</div><div class="ih-v">'+money(m)+' a month</div><div class="ih-d">'+
        (r!=null?'at '+r.toFixed(2)+'% on '+money(s.P.now?adj(el,s.P.now*.8,ny,'ny'):null)+dlab(el):'')+(m0!=null&&iy?' &middot; '+Math.round(m0*12/s.inc[iy]*100)+'% of '+iy+' median income':'')+'</div></div>';});
    ys=Object.keys(ys).sort();
    el.querySelector('.ih-mcards').innerHTML=cards;
    if(el._mchart)el._mchart.destroy();
    el._mchart=new Chart(el.querySelector('.ih-mch canvas'),{type:'line',data:{labels:ys,datasets:list.filter(function(s){return s.P;}).map(function(s){
      return {label:s.label,data:ys.map(function(y){return adj(el,pmt(s.P.yr[y],yrRate(D,y)),y,'ny');}),borderColor:s.c,backgroundColor:s.c,borderWidth:s.w||2,pointRadius:2,borderDash:s.dash||[],spanGaps:true};})
      .concat([{label:'30-year rate (right)',data:ys.map(function(y){var r=yrRate(D,y);return r==null?null:+r.toFixed(2);}),borderColor:'#9ca3af',backgroundColor:'#9ca3af',borderWidth:1.5,pointRadius:0,yAxisID:'r'}])},
      options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},
        plugins:{legend:{labels:{boxWidth:10,font:{size:11,family:'DM Sans'}}},tooltip:{callbacks:{label:function(c){return c.dataset.yAxisID==='r'?'30-year rate: '+c.parsed.y+'%':c.dataset.label+': '+money(c.parsed.y)+' a month';}}}},
        scales:{y:{ticks:{callback:function(v){return money(v);},font:{size:10}}},r:{position:'right',grid:{display:false},ticks:{callback:function(v){return v+'%';},font:{size:10}}},x:{ticks:{font:{size:10}}}}}});
  }
  function drawTax(el,T){
    var ys=T.years.map(function(y){return y.fy.replace(' (1st & 2nd quarters)',' H1').replace(' (3rd & 4th quarters)',' H2');});
    var lastY=T.years[T.years.length-1],firstY=T.years[0];
    el.querySelector('.ih-tcards').innerHTML=
      '<div class="ih-c"><div class="ih-l">Class 1, '+lastY.fy+'</div><div class="ih-v">'+lastY.c1.toFixed(3)+'%</div><div class="ih-d">One- to three-family homes &middot; '+firstY.c1.toFixed(3)+'% in '+firstY.fy+'</div></div>'+
      '<div class="ih-c"><div class="ih-l">Class 2, '+lastY.fy+'</div><div class="ih-v">'+lastY.c2.toFixed(3)+'%</div><div class="ih-d">Co-ops, condos and other apartment buildings &middot; '+firstY.c2.toFixed(3)+'% in '+firstY.fy+'</div></div>';
    if(el._tchart)el._tchart.destroy();
    el._tchart=new Chart(el.querySelector('.ih-tch canvas'),{type:'line',data:{labels:ys,datasets:[
      {label:'Class 1: one- to three-family homes',data:T.years.map(function(y){return y.c1;}),borderColor:'#f47920',backgroundColor:'#f47920',borderWidth:2.5,pointRadius:2},
      {label:'Class 2: co-ops, condos, apartment buildings',data:T.years.map(function(y){return y.c2;}),borderColor:'#0d1b4b',backgroundColor:'#0d1b4b',borderWidth:2.5,pointRadius:2}]},
      options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},
        plugins:{legend:{labels:{boxWidth:10,font:{size:11,family:'DM Sans'}}},tooltip:{callbacks:{label:function(c){return c.dataset.label+': '+c.parsed.y.toFixed(3)+'%';}}}},
        scales:{y:{ticks:{callback:function(v){return v+'%';},font:{size:10}}},x:{ticks:{font:{size:10},maxTicksLimit:14}}}}});
  }
  /* HUD: federal budget over time (OMB) and HUD awards in NYC (USAspending). /data/hud-nyc.json */
  function bil(v){return v==null?'\u2014':'$'+(Math.abs(v)>=1e3?(v/1e3).toFixed(1)+'B':Math.round(v)+'M');}
  function drawHud(el,H){
    var view=el._hud||'total',o=H.budget.outlays,b=H.budget.budget_authority,F=H.budget.federal_outlays,ys=[],seen={};
    o.concat(b).forEach(function(r){if(!seen[r.fy]){seen[r.fy]=1;ys.push(r.fy);}});ys.sort(function(a,c){return a-c;});
    function at(arr,y){for(var i=0;i<arr.length;i++)if(arr[i].fy===y)return arr[i];return null;}
    function actual(arr){var a=arr.filter(function(r){return !r.est;});return a[a.length-1];}
    /* one HUD budget figure (millions) in the chosen view */
    function V(m,y){if(m==null)return null;
      if(view==='share'){var f=at(F,y);return f&&f.m?m/f.m*100:null;}
      var v=adj(el,m*1e6,y,'us');if(v==null)return null;
      if(view==='person'){var p=pop('us',y);return p?v/(p*1e3):null;}
      return v;}
    function fmt(v){return v==null?'—':view==='share'?v.toFixed(2)+'%':view==='person'?'$'+v.toFixed(0):bil(v/1e6);}
    function NV(r,part){var m=r[part];if(view==='share'){var a=at(b,r.fy);return a&&a.m?m/(a.m*1e6)*100:null;}
      var v=adj(el,m,r.fy,'ny');if(v==null)return null;if(view==='person'){var p=pop('nyc',r.fy);return p?v/(p*1e3):null;}return v;}
    function nf(v){return v==null?'—':view==='share'?v.toFixed(1)+'%':view==='person'?'$'+v.toFixed(0):bil(v/1e6);}
    var la=actual(b),lo=actual(o),N=H.nyc.years,ln=N[N.length-1],fn=N[0];
    var vl={total:'',person:' per person',share:' as a share of all federal spending'}[view];
    el.querySelector('.ih-hcards').innerHTML=
      '<div class="ih-c"><div class="ih-l">HUD budget authority'+vl+', FY '+la.fy+'</div><div class="ih-v">'+fmt(V(la.m,la.fy))+'</div><div class="ih-d">'+fmt(V(b[0].m,b[0].fy))+' in FY '+b[0].fy+dlab(el)+'</div></div>'+
      '<div class="ih-c"><div class="ih-l">HUD outlays'+vl+', FY '+lo.fy+'</div><div class="ih-v">'+fmt(V(lo.m,lo.fy))+'</div><div class="ih-d">'+fmt(V(o[0].m,o[0].fy))+' in FY '+o[0].fy+dlab(el)+'</div></div>'+
      '<div class="ih-c"><div class="ih-l">HUD awards in NYC'+(view==='person'?' per New Yorker':view==='share'?' as a share of HUD budget authority':'')+', FY '+ln.fy+'</div><div class="ih-v">'+nf(NV(ln,'total'))+'</div><div class="ih-d">NYCHA '+nf(NV(ln,'nycha'))+' &middot; City agencies '+nf(NV(ln,'city'))+' &middot; '+nf(NV(fn,'total'))+' in FY '+fn.fy+'</div></div>';
    if(el._hchart)el._hchart.destroy();
    function ds(arr,label,c){var la=actual(arr).fy;return [
      {label:label,data:ys.map(function(y){var r=at(arr,y);return r&&!r.est?V(r.m,y):null;}),borderColor:c,backgroundColor:c,borderWidth:2.5,pointRadius:0},
      {label:label+' (President’s estimate)',data:ys.map(function(y){var r=at(arr,y);return r&&(r.est||y===la)?V(r.m,y):null;}),borderColor:c,backgroundColor:c,borderWidth:2,borderDash:[5,4],pointRadius:0}];}
    el._hchart=new Chart(el.querySelector('.ih-hch canvas'),{type:'line',data:{labels:ys,datasets:ds(b,'Budget authority','#0d1b4b').concat(ds(o,'Outlays','#f47920'))},
      options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},
        plugins:{legend:{labels:{boxWidth:10,font:{size:11,family:'DM Sans'}}},tooltip:{callbacks:{label:function(c){return c.parsed.y==null?null:c.dataset.label+': '+fmt(c.parsed.y);}}}},
        scales:{y:{ticks:{callback:function(v){return fmt(v);},font:{size:10}}},x:{ticks:{font:{size:10},maxTicksLimit:14}}}}});
    if(el._nchart)el._nchart.destroy();
    var nds=[
      {label:'NYCHA',data:N.map(function(r){return NV(r,'nycha');}),backgroundColor:'#0d1b4b',stack:'a'},
      {label:'City agencies',data:N.map(function(r){return NV(r,'city');}),backgroundColor:'#f47920',stack:'a'},
      {label:'Everyone else (private owners, nonprofits, others)',data:N.map(function(r){return NV(r,'other');}),backgroundColor:'#9ECAE1',stack:'a'}];
    if(view==='share'&&AJ)nds.push({type:'line',label:'NYC share of the U.S. population',data:N.map(function(r){var a=pop('nyc',r.fy),u=pop('us',r.fy);return a&&u?a/u*100:null;}),borderColor:'#67000D',backgroundColor:'#67000D',borderWidth:2,pointRadius:2});
    el._nchart=new Chart(el.querySelector('.ih-nch canvas'),{type:'bar',data:{labels:N.map(function(r){return 'FY '+r.fy;}),datasets:nds},
      options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},
        plugins:{legend:{labels:{boxWidth:10,font:{size:11,family:'DM Sans'}}},tooltip:{callbacks:{label:function(c){return c.dataset.label+': '+nf(c.parsed.y);},footer:function(items){var i=items[0].dataIndex;return 'Total: '+nf(NV(N[i],'total'));}}}},
        scales:{x:{stacked:true,ticks:{font:{size:10}}},y:{stacked:true,ticks:{callback:function(v){return nf(v);},font:{size:10}}}}}});
    el.querySelector('.ih-hn').innerHTML=
      (view==='share'?'Share view: HUD as a share of all federal outlays (same OMB table), and HUD awards in NYC as a share of HUD budget authority that year (awards are obligations, a different measure from budget authority, so read this as an approximation), with New York City’s share of the U.S. population for comparison. ':
       view==='person'?'Per person: HUD’s budget divided by the U.S. population, and HUD awards in NYC divided by New York City’s population (Census estimates for the five counties). ':'')+
      (el._real&&AJ&&view!=='share'?'Adjusted for inflation to '+AJ.base+' dollars: the federal budget with the national CPI-U, NYC awards with the New York-area CPI-U, by calendar year; years without a published index (budget estimates past this year) are left out. ':'')+
      'Federal budget: '+H.budget.source+', by federal fiscal year (October to September); dashed lines are the President’s budget estimates. <a href="'+H.budget.url+'" target="_blank" rel="noopener">OMB</a>. '+
      'NYC: '+H.nyc.source+'. '+H.nyc.note+' <a href="'+H.nyc.url+'" target="_blank" rel="noopener">USAspending.gov</a>. Prices and population: '+(AJ?AJ.source:'')+'.';
  }

  /* ---------- context blocks: ACS (earnings, rent burden, tenure, population), DCP supply, RGB, HPD ---------- */
  var AC=null,HC=null;
  function areas(el,cd){   /* district / borough / city, or five boroughs / city */
    var L=[];
    if(el.getAttribute('data-mode')==='boroughs')Object.keys(COLS).forEach(function(b){L.push({label:b,k:'boro',id:b,c:COLS[b]});});
    else{var b=BORO[cd.slice(0,2)];L.push({label:cdName(cd),k:'cd',id:cd,c:'#f47920',w:3});L.push({label:b,k:'boro',id:b,c:'#1B5E8A'});}
    L.push({label:'New York City',k:'nyc',id:'NYC',c:'#0d1b4b',dash:[5,3]});return L;}
  function acsOf(a,m){if(!AC)return {};var r=a.k==='nyc'?AC.nyc:(AC[a.k]||{})[a.id];return (r&&r[m])||{};}
  function lineChart(el,key,cv,L,get,fmt,opts){
    var ys={};L.forEach(function(a){Object.keys(get(a)).forEach(function(y){ys[y]=1;});});ys=Object.keys(ys).sort();
    if(el[key])el[key].destroy();
    el[key]=new Chart(el.querySelector(cv),{type:'line',data:{labels:ys,datasets:L.map(function(a){var o=get(a);
      return {label:a.label,data:ys.map(function(y){return o[y]!=null?o[y]:null;}),borderColor:a.c,backgroundColor:a.c,borderWidth:a.w||2,pointRadius:2,borderDash:a.dash||[],spanGaps:true};})},
      options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},
        plugins:{legend:{labels:{boxWidth:10,font:{size:11,family:'DM Sans'}}},tooltip:{callbacks:{label:function(c){return c.dataset.label+': '+fmt(c.parsed.y);}}}},
        scales:{y:Object.assign({ticks:{callback:fmt,font:{size:10}}},opts||{}),x:{ticks:{font:{size:10},maxTicksLimit:14}}}}});}
  function lastCard(l,o,fmt,extra){var a=first(o),b=last(o);if(!b)return '';return '<div class="ih-c"><div class="ih-l">'+l+', '+b+'</div><div class="ih-v">'+fmt(o[b])+'</div><div class="ih-d">'+(a&&a!==b?fmt(o[a])+' in '+a:'')+(extra||'')+'</div></div>';}
  function pct1(v){return v==null?'—':v.toFixed(1)+'%';}
  function drawWages(el,cd){
    var L=areas(el,cd),c='';
    function get(a){var o=acsOf(a,'earn'),r={};Object.keys(o).forEach(function(y){var v=adj(el,o[y],y,'ny');if(v!=null)r[y]=v;});return r;}
    L.forEach(function(a){c+=lastCard(a.label,get(a),money);});
    el.querySelector('.ih-wcards').innerHTML=c;lineChart(el,'_wchart','.ih-wch canvas',L,get,function(v){return k(v);});}
  function drawBurden(el,cd){
    var L=areas(el,cd),c='';
    L.forEach(function(a){var o=acsOf(a,'burden30'),o5=acsOf(a,'burden50'),y=last(o);c+=lastCard(a.label,o,pct1,y?' &middot; '+pct1(o5[y])+' pay half or more':'');});
    el.querySelector('.ih-bcards').innerHTML=c;
    lineChart(el,'_bchart','.ih-bch canvas',L.concat(L.map(function(a){return {label:a.label+', 50% or more',k:a.k,id:a.id,c:a.c,dash:[2,3],half:1};})),
      function(a){return acsOf(a,a.half?'burden50':'burden30');},function(v){return v==null?'':Math.round(v)+'%';},{min:0});}
  function drawTenure(el,cd){
    var L=areas(el,cd),c='';
    L.forEach(function(a){var o=acsOf(a,'owner'),y=last(o),ow=acsOf(a,'owners'),rn=acsOf(a,'renters');
      c+=lastCard(a.label+' homes lived in by owners',o,pct1,y?' &middot; '+cnt(ow[y])+' owner and '+cnt(rn[y])+' renter households':'');});
    el.querySelector('.ih-ocards').innerHTML=c;lineChart(el,'_ochart','.ih-och canvas',L,function(a){return acsOf(a,'owner');},function(v){return v==null?'':Math.round(v)+'%';},{min:0});}
  function cnt(v){return v==null?'—':Math.round(v).toLocaleString('en-US');}
  function drawSupply(el,cd){
    if(!HC)return;var S=HC.supply,boros=el.getAttribute('data-mode')==='boroughs';
    var a=boros?{label:'New York City',k:'nyc',id:'NYC'}:{label:cdName(cd),k:'cd',id:cd};
    var rec=a.k==='nyc'?S.nyc:S.cd[cd],ys=S.years.map(String),built=ys.map(function(y){return rec.comp[y]!=null?rec.comp[y]:null;});
    var pop=acsOf(a,'pop'),py=Object.keys(pop).sort(),tot=0;built.forEach(function(v){if(v)tot+=v;});
    var c='<div class="ih-c"><div class="ih-l">'+a.label+', homes added 2010 to '+S.ytd+'</div><div class="ih-v">'+cnt(tot)+'</div><div class="ih-d">net, after demolitions &middot; '+(rec.cen20?Math.round(tot/rec.cen20*100)+'% of the '+cnt(rec.cen20)+' homes counted in the 2020 Census':'')+'</div></div>'+
      '<div class="ih-c"><div class="ih-l">'+a.label+', homes added in '+(+S.ytd-1)+'</div><div class="ih-v">'+cnt(rec.comp[String(+S.ytd-1)])+'</div><div class="ih-d">'+cnt(rec.comp[S.ytd])+' so far in '+S.ytd+'</div></div>'+
      (py.length>1?'<div class="ih-c"><div class="ih-l">'+a.label+', population</div><div class="ih-v">'+cnt(pop[py[py.length-1]])+'</div><div class="ih-d">'+py[py.length-1]+' &middot; '+cnt(pop[py[0]])+' in '+py[0]+' ('+((pop[py[py.length-1]]/pop[py[0]]-1)*100>=0?'+':'')+((pop[py[py.length-1]]/pop[py[0]]-1)*100).toFixed(1)+'%)</div></div>':'');
    el.querySelector('.ih-scards').innerHTML=c;
    if(el._schart)el._schart.destroy();
    el._schart=new Chart(el.querySelector('.ih-sch canvas'),{type:'bar',data:{labels:ys,datasets:[
      {label:'Homes added (net)',data:built,backgroundColor:ys.map(function(y){return y===S.ytd?'rgba(244,121,32,.45)':'#f47920';}),yAxisID:'u'},
      {type:'line',label:'Population (Census ACS, right)',data:ys.map(function(y){return pop[y]!=null?pop[y]:null;}),borderColor:'#0d1b4b',backgroundColor:'#0d1b4b',borderWidth:2,pointRadius:2,spanGaps:true,yAxisID:'p'}]},
      options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},
        plugins:{legend:{labels:{boxWidth:10,font:{size:11,family:'DM Sans'}}},tooltip:{callbacks:{label:function(c){return c.dataset.label+': '+cnt(c.parsed.y)+(c.dataset.yAxisID==='u'&&ys[c.dataIndex]===S.ytd?' (year to date)':'');}}}},
        scales:{u:{position:'left',ticks:{callback:cnt,font:{size:10}}},p:{position:'right',grid:{display:false},ticks:{callback:cnt,font:{size:10}}},x:{ticks:{font:{size:10}}}}}});}
  function drawRgb(el){
    if(!HC)return;var R=HC.rgb.orders,st=HC.stab,lab=R.map(function(o){return o.start.slice(0,4);});
    var infl=R.map(function(o){if(!AJ)return null;var y=+o.start.slice(0,4),a=AJ.cpi_ny[String(y)],b=AJ.cpi_ny[String(y-1)];return a&&b?+((a/b-1)*100).toFixed(1):null;});
    var l=R[R.length-1],p=R[R.length-2];
    el.querySelector('.ih-rcards').innerHTML=
      '<div class="ih-c"><div class="ih-l">Order #'+l.order+', leases from '+MON[+l.start.slice(5)-1]+' '+l.start.slice(0,4)+'</div><div class="ih-v">'+l.one+'% / '+l.two+'%</div><div class="ih-d">one-year / two-year renewal &middot; #'+p.order+': '+p.one+'% / '+p.two+'%</div></div>'+
      '<div class="ih-c"><div class="ih-l">Rent stabilized homes, '+st.year+'</div><div class="ih-v">'+cnt(st.units)+'</div><div class="ih-d">'+st.share_rentals+'% of rentals, '+st.share_all+'% of all homes in NYC</div></div>'+
      '<div class="ih-c"><div class="ih-l">Vacancy in rent stabilized homes, '+st.year+'</div><div class="ih-v">'+st.vacancy+'%</div><div class="ih-d">'+st.vacancy_2021+'% in 2021</div></div>';
    if(el._rchart)el._rchart.destroy();
    el._rchart=new Chart(el.querySelector('.ih-rch canvas'),{type:'bar',data:{labels:lab,datasets:[
      {label:'One-year renewal',data:R.map(function(o){return o.one;}),backgroundColor:'#f47920'},
      {label:'Two-year renewal',data:R.map(function(o){return o.two;}),backgroundColor:'#0d1b4b'},
      {type:'line',label:'Inflation that year (New York-area CPI)',data:infl,borderColor:'#67000D',backgroundColor:'#67000D',borderWidth:2,pointRadius:1.5,spanGaps:true}]},
      options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},
        plugins:{legend:{labels:{boxWidth:10,font:{size:11,family:'DM Sans'}}},tooltip:{callbacks:{title:function(it){var o=R[it[0].dataIndex];return 'Order #'+o.order+', from '+MON[+o.start.slice(5)-1]+' '+o.start.slice(0,4);},
          label:function(c){return c.dataset.label+': '+(c.parsed.y==null?'—':c.parsed.y+'%');},footer:function(it){return R[it[0].dataIndex].note||'';}}}},
        scales:{y:{ticks:{callback:function(v){return v+'%';},font:{size:10}}},x:{ticks:{font:{size:10},maxTicksLimit:20}}}}});}
  function drawHpd(el){
    if(!HC)return;var H=HC.hpd.years,lab=H.map(function(h){return 'FY '+h.fy;});
    function A(h,f){return adj(el,h[f],h.fy,'ny');}
    var l=H[H.length-1],f0=H[0];
    el.querySelector('.ih-pcards').innerHTML=
      '<div class="ih-c"><div class="ih-l">HPD adopted expense budget, FY '+l.fy+'</div><div class="ih-v">'+bil(A(l,'total')/1e6)+'</div><div class="ih-d">City funds '+bil(A(l,'city')/1e6)+' &middot; federal '+bil((A(l,'federal')+A(l,'cd'))/1e6)+dlab(el)+'</div></div>'+
      '<div class="ih-c"><div class="ih-l">FY '+f0.fy+'</div><div class="ih-v">'+bil(A(f0,'total')/1e6)+'</div><div class="ih-d">City funds '+bil(A(f0,'city')/1e6)+' &middot; federal '+bil((A(f0,'federal')+A(f0,'cd'))/1e6)+'</div></div>';
    if(el._pchart)el._pchart.destroy();
    el._pchart=new Chart(el.querySelector('.ih-pch canvas'),{type:'bar',data:{labels:lab,datasets:[
      {label:'City funds',data:H.map(function(h){return A(h,'city')/1e6;}),backgroundColor:'#f47920'},
      {label:'Federal (HUD and other)',data:H.map(function(h){return A(h,'federal')/1e6;}),backgroundColor:'#0d1b4b'},
      {label:'Federal Community Development Block Grant',data:H.map(function(h){return A(h,'cd')/1e6;}),backgroundColor:'#1B5E8A'},
      {label:'State and other',data:H.map(function(h){return (A(h,'state')+A(h,'other'))/1e6;}),backgroundColor:'#9ECAE1'}]},
      options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},
        plugins:{legend:{labels:{boxWidth:10,font:{size:11,family:'DM Sans'}}},tooltip:{callbacks:{label:function(c){return c.dataset.label+': '+bil(c.parsed.y);},footer:function(it){return 'Total: '+bil(A(H[it[0].dataIndex],'total')/1e6);}}}},
        scales:{x:{stacked:true,ticks:{font:{size:10}}},y:{stacked:true,ticks:{callback:function(v){return bil(v);},font:{size:10}}}}}});}
  function hdr(t,s){return '<div class="ih-h"><span class="ih-t">'+t+'</span><span class="ih-s">'+s+'</span></div>';}
  function blk(cls,note,two){return '<div class="ih-'+cls+'cards ih-cards"></div><div class="ih-ch ih-'+cls+'ch"><canvas></canvas></div><div class="ih-n">'+note+'</div>';}
  function init(){
    var els=document.querySelectorAll('.inchist');if(!els.length)return;
    var st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
    var SX=null,TX=null,HU=null;
    Promise.all([fetch('/data/income-history.json').then(function(r){return r.json();}),
      SALE?fetch('/data/sales/rent-explorer.json').then(function(r){return r.json();}):null,
      SALE?fetch('/data/nyc-property-tax-rates.json').then(function(r){return r.json();}):null,
      fetch('/data/hud-nyc.json').then(function(r){return r.json();}).catch(function(){return null;}),
      fetch('/data/adjusters.json').then(function(r){return r.json();}).catch(function(){return null;}),
      fetch('/data/acs-context.json').then(function(r){return r.json();}).catch(function(){return null;}),
      fetch('/data/housing-context.json').then(function(r){return r.json();}).catch(function(){return null;})]).then(function(res){var D=res[0];TX=res[2];HU=res[3];AJ=res[4];AC=res[5];HC=res[6];
      if(res[1]){SX={months:res[1].months,A:{}};res[1].areas.forEach(function(a){SX.A[a.id]=a;});}
      needChart(function(){
      els.forEach(function(el){
        var boros=el.getAttribute('data-mode')==='boroughs',cd=el.getAttribute('data-cd')||'BKCB6';
        el.innerHTML='<div class="ih-h"><span class="ih-t">Median household income</span><span class="ih-s">'+(boros?'the five boroughs and the city':'district, borough and city')+', over time</span></div>'+
          '<div class="ih-ctl ih-dol"><span class="lb">Dollars</span><button type="button" data-r="0" class="on">As reported</button><button type="button" data-r="1">Adjusted for inflation'+(AJ?' ('+AJ.base+' dollars)':'')+'</button></div>'+
          (boros?'':'<div class="ih-pick"><select aria-label="Community district"></select></div>')+
          '<div class="ih-cards"></div><div class="ih-ch"><canvas></canvas></div><div class="ih-n"></div>'+
          hdr('Median earnings of workers','what a typical worker earns, district, borough and city')+blk('w','Median earnings in the past 12 months of people 16 and over with earnings (Census American Community Survey 1-year estimates, table B20002). Household income adds up everyone in a household; this is one worker. Dollars follow the switch above.')+
          hdr('Rent burden','share of renter households paying 30% or more of income on rent, and 50% or more')+blk('b','Gross rent (rent plus utilities) as a share of household income (Census ACS 1-year, table B25070). Paying 30% or more is the federal definition of rent burdened; 50% or more is severely burdened. Households with no income or no cash rent are left out.')+
          hdr('Owners and renters','share of homes lived in by their owners')+blk('o','Owner-occupied share of occupied homes (Census ACS 1-year, table B25003).')+
          hdr('Homes built and population','net new homes each year since 2010, against population')+blk('s','Net homes added: '+(HC?HC.supply.note+' '+HC.supply.source:'')+'. Population: Census ACS 1-year estimates (table B01003), from 2012 for districts. A district that shares a Census area with another shows the combined population.')+
          (SALE?'<div class="ih-h"><span class="ih-t">Down payment needed</span><span class="ih-s">20% of the median asking price, all homes, and how many years of median income that is</span></div>'+
            '<div class="ih-dcards ih-cards"></div><div class="ih-ch ih-dch"><canvas></canvas></div><div class="ih-n">Down payment is 20% of the median asking price for all homes (StreetEasy). Each year uses the median of that year\'s monthly median asking prices, set against that year\'s median household income. The latest month is set against the latest income the Census has published.</div>'+
            '<div class="ih-h"><span class="ih-t">Monthly mortgage cost</span><span class="ih-s">principal and interest on the median asking price, 20% down, 30-year fixed</span></div>'+
            '<div class="ih-mcards ih-cards"></div><div class="ih-ch ih-mch"><canvas></canvas></div><div class="ih-n">Principal and interest on 80% of the median asking price for all homes, 30-year fixed at that year\'s average rate (Freddie Mac Primary Mortgage Market Survey, via FRED); the latest month uses that month\'s rate. Property taxes, insurance and co-op maintenance or condo common charges are not included.</div>'+
            '<div class="ih-h"><span class="ih-t">NYC property tax rates</span><span class="ih-s">every year since 1981/82</span></div>'+
            '<div class="ih-tcards ih-cards"></div><div class="ih-ch ih-tch"><canvas></canvas></div><div class="ih-n ih-tn"></div>':'')+
          hdr('Rent stabilization','Rent Guidelines Board renewal increases every year since 1968, against inflation')+blk('r','Guidelines as printed in the '+(HC?'<a href="'+HC.rgb.url+'" target="_blank" rel="noopener">'+HC.rgb.source+'</a>':'RGB summary chart')+'. Orders from #13 on start October 1 (earlier ones July 1); where an order split a lease or set a dollar minimum, the tooltip says so. Inflation is the change in the New York-area CPI-U over the calendar year the order starts. Rent stabilized homes and vacancy: '+(HC?'<a href="'+HC.stab.url+'" target="_blank" rel="noopener">'+HC.stab.source+'</a>':'')+'.')+
          hdr('The City&rsquo;s housing agency budget','HPD adopted expense budget by where the money comes from')+blk('p',(HC?HC.hpd.note+' Source: <a href="'+HC.hpd.url+'" target="_blank" rel="noopener">'+HC.hpd.source+'</a>, fiscal years July to June. Dollars follow the switch above.':''))+
          '<div class="ih-h"><span class="ih-t">HUD&rsquo;s budget and HUD money in NYC</span><span class="ih-s">federal budget since 1962, awards in the five boroughs since FY 2010</span></div>'+
          '<div class="ih-ctl ih-hv"><span class="lb">Show</span><button type="button" data-v="total" class="on">Total</button><button type="button" data-v="person">Per person</button><button type="button" data-v="share">Share of federal spending</button></div>'+
          '<div class="ih-hcards ih-cards"></div><div class="ih-ch ih-hch"><canvas></canvas></div><div class="ih-ch ih-nch"><canvas></canvas></div><div class="ih-n ih-hn"></div>';
        if(!boros){var sel=el.querySelector('select');
          Object.keys(D.acs.cd).sort(function(a,b){return a.slice(0,2)===b.slice(0,2)?(+a.slice(4))-(+b.slice(4)):a<b?-1:1;}).forEach(function(c){sel.add(new Option(cdName(c),c));});
          sel.value=cd;sel.onchange=function(){all();};}
        function cur(){var s2=el.querySelector('.ih-pick select');return s2?s2.value:cd;}
        function all(){var c=cur();draw(el,D,c);if(AC){drawWages(el,c);drawBurden(el,c);drawTenure(el,c);}drawSupply(el,c);if(SX){drawDown(el,D,SX,c);drawMonthly(el,D,SX,c);}drawRgb(el);drawHpd(el);if(HU)drawHud(el,HU);}
        el.querySelectorAll('.ih-dol button').forEach(function(bt){bt.onclick=function(){el._real=bt.getAttribute('data-r')==='1';el.querySelectorAll('.ih-dol button').forEach(function(x){x.classList.toggle('on',x===bt);});all();};});
        el.querySelectorAll('.ih-hv button').forEach(function(bt){bt.onclick=function(){el._hud=bt.getAttribute('data-v');el.querySelectorAll('.ih-hv button').forEach(function(x){x.classList.toggle('on',x===bt);});if(HU)drawHud(el,HU);};});
        all();
        if(TX){drawTax(el,TX);el.querySelector('.ih-tn').innerHTML='Fiscal year rates, as a percentage of <b>assessed value</b>, not of the price. NYC taxes one- to three-family homes on an assessed value capped at 6% of market value (with yearly limits on increases), and co-ops and condos on a value the Department of Finance sets from comparable rental buildings, so the tax bill is far below the rate times the price. '+(TX.note.split('. ').slice(1,2).join('')||'')+'. Source: <a href="'+TX.url+'" target="_blank" rel="noopener">NYC Department of Finance</a>.';}
      });
    });});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
