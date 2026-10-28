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
    '.inchist .ih-ch{position:relative;height:320px;padding:10px 12px}.inchist .ih-n{padding:4px 16px 14px;font-size:.66rem;line-height:1.55;color:#6b6760}';
  function money(v){return v==null?'—':'$'+Math.round(v).toLocaleString('en-US');}
  function k(v){return v>=1e6?'$'+(v/1e6).toFixed(1)+'M':'$'+Math.round(v/1000)+'K';}
  function cdName(c){return BORO[c.slice(0,2)]+' CB'+c.slice(4);}
  function first(o){var y=Object.keys(o).sort();return y.length?y[0]:null;}
  function last(o){var y=Object.keys(o).sort();return y.length?y[y.length-1]:null;}
  function needChart(cb){if(window.Chart)return cb();var s=document.createElement('script');s.src='https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js';s.onload=cb;document.head.appendChild(s);}
  function card(l,o){var a=first(o),b=last(o);if(!b)return '';var ch=a&&a!==b?((o[b]/o[a]-1)*100):null;
    return '<div class="ih-c"><div class="ih-l">'+l+', '+b+'</div><div class="ih-v">'+money(o[b])+'</div><div class="ih-d">'+(ch==null?'':(ch>=0?'+':'')+ch.toFixed(0)+'% since '+a+' ('+money(o[a])+')')+'</div></div>';}
  function draw(el,D,cd){
    var A=D.acs,SA=D.saipe.boro,series=[],cards='';
    if(el.getAttribute('data-mode')==='boroughs'){
      Object.keys(COLS).forEach(function(b){series.push({label:b,o:SA[b],c:COLS[b]});cards+=card(b,SA[b]);});
    }else{
      var b=BORO[cd.slice(0,2)],dist=A.cd[cd]||{};
      series.push({label:cdName(cd),o:dist,c:'#f47920',w:3});cards+=card(cdName(cd),dist);
      series.push({label:b,o:SA[b],c:'#1B5E8A'});cards+=card(b,SA[b]);
    }
    series.push({label:'New York City',o:A.nyc,c:'#0d1b4b',dash:[5,3]});cards+=card('New York City',A.nyc);
    var ys={};series.forEach(function(s){Object.keys(s.o||{}).forEach(function(y){ys[y]=1;});});ys=Object.keys(ys).sort();
    el.querySelector('.ih-cards').innerHTML=cards;
    var sh=(A.shared[cd]||{})[last(A.cd[cd]||{})];
    el.querySelector('.ih-n').innerHTML='Median household income in dollars of each year, not adjusted for inflation. '+
      (el.getAttribute('data-mode')==='boroughs'?'':'Community district: Census American Community Survey 1-year estimates, from 2012, the first year the Census labels its areas by district'+(sh?' (it shares one Census area with '+sh.map(cdName).join(', ')+')':'')+'. ')+
      'Borough: Census Small Area Income and Poverty Estimates, from 1989. New York City: American Community Survey 1-year estimates, from 2010. There are no standard 2020 1-year estimates.';
    if(el._chart)el._chart.destroy();
    el._chart=new Chart(el.querySelector('canvas'),{type:'line',data:{labels:ys,datasets:series.map(function(s){
      return {label:s.label,data:ys.map(function(y){return s.o&&s.o[y]!=null?s.o[y]:null;}),borderColor:s.c,backgroundColor:s.c,borderWidth:s.w||2,pointRadius:2,borderDash:s.dash||[],spanGaps:true};})},
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
      var iy=last(s.inc),dp=P.now!=null?P.now*.2:null;
      cards+='<div class="ih-c"><div class="ih-l">'+s.label+', '+(P.nowM?MON[+P.nowM.slice(5)-1]+' '+P.nowM.slice(0,4):'')+'</div><div class="ih-v">'+money(dp)+'</div><div class="ih-d">20% of '+money(P.now)+
        (dp!=null&&iy?' &middot; '+(dp/s.inc[iy]).toFixed(1)+' years of '+iy+' median income ('+money(s.inc[iy])+')':'')+'</div></div>';});
    ys=Object.keys(ys).sort();
    el.querySelector('.ih-dcards').innerHTML=cards;
    if(el._dchart)el._dchart.destroy();
    el._dchart=new Chart(el.querySelector('.ih-dch canvas'),{type:'line',data:{labels:ys,datasets:list.filter(function(s){return s.P;}).map(function(s){
      return {label:s.label,data:ys.map(function(y){var p=s.P.yr[y],i=s.inc[y];return p!=null&&i!=null?+(p*.2/i).toFixed(2):null;}),
        _dp:ys.map(function(y){var p=s.P.yr[y];return p!=null?p*.2:null;}),borderColor:s.c,backgroundColor:s.c,borderWidth:s.w||2,pointRadius:2,borderDash:s.dash||[],spanGaps:true};})},
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
      var r=s.P.nowM?D.mortgage.monthly[s.P.nowM]:null,m=pmt(s.P.now,r),iy=last(s.inc);
      cards+='<div class="ih-c"><div class="ih-l">'+s.label+', '+(s.P.nowM?MON[+s.P.nowM.slice(5)-1]+' '+s.P.nowM.slice(0,4):'')+'</div><div class="ih-v">'+money(m)+' a month</div><div class="ih-d">'+
        (r!=null?'at '+r.toFixed(2)+'% on '+money(s.P.now?s.P.now*.8:null):'')+(m!=null&&iy?' &middot; '+Math.round(m*12/s.inc[iy]*100)+'% of '+iy+' median income':'')+'</div></div>';});
    ys=Object.keys(ys).sort();
    el.querySelector('.ih-mcards').innerHTML=cards;
    if(el._mchart)el._mchart.destroy();
    el._mchart=new Chart(el.querySelector('.ih-mch canvas'),{type:'line',data:{labels:ys,datasets:list.filter(function(s){return s.P;}).map(function(s){
      return {label:s.label,data:ys.map(function(y){return pmt(s.P.yr[y],yrRate(D,y));}),borderColor:s.c,backgroundColor:s.c,borderWidth:s.w||2,pointRadius:2,borderDash:s.dash||[],spanGaps:true};})
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
    var o=H.budget.outlays,b=H.budget.budget_authority,ys=[],seen={};
    o.concat(b).forEach(function(r){if(!seen[r.fy]){seen[r.fy]=1;ys.push(r.fy);}});ys.sort(function(a,c){return a-c;});
    function at(arr,y){for(var i=0;i<arr.length;i++)if(arr[i].fy===y)return arr[i];return null;}
    function actual(arr){var a=arr.filter(function(r){return !r.est;});return a[a.length-1];}
    var la=actual(b),lo=actual(o),N=H.nyc.years,ln=N[N.length-1],fn=N[0];
    el.querySelector('.ih-hcards').innerHTML=
      '<div class="ih-c"><div class="ih-l">HUD budget authority, FY '+la.fy+'</div><div class="ih-v">'+bil(la.m)+'</div><div class="ih-d">'+bil(b[0].m)+' in FY '+b[0].fy+'</div></div>'+
      '<div class="ih-c"><div class="ih-l">HUD outlays, FY '+lo.fy+'</div><div class="ih-v">'+bil(lo.m)+'</div><div class="ih-d">'+bil(o[0].m)+' in FY '+o[0].fy+'</div></div>'+
      '<div class="ih-c"><div class="ih-l">HUD awards in NYC, FY '+ln.fy+'</div><div class="ih-v">'+bil(ln.total/1e6)+'</div><div class="ih-d">NYCHA '+bil(ln.nycha/1e6)+' &middot; City agencies '+bil(ln.city/1e6)+' &middot; '+bil(fn.total/1e6)+' in FY '+fn.fy+'</div></div>';
    if(el._hchart)el._hchart.destroy();
    function ds(arr,label,c){var la=actual(arr).fy;return [
      {label:label,data:ys.map(function(y){var r=at(arr,y);return r&&!r.est?r.m:null;}),borderColor:c,backgroundColor:c,borderWidth:2.5,pointRadius:0},
      {label:label+' (President\u2019s estimate)',data:ys.map(function(y){var r=at(arr,y);return r&&(r.est||y===la)?r.m:null;}),borderColor:c,backgroundColor:c,borderWidth:2,borderDash:[5,4],pointRadius:0}];}
    el._hchart=new Chart(el.querySelector('.ih-hch canvas'),{type:'line',data:{labels:ys,datasets:ds(b,'Budget authority','#0d1b4b').concat(ds(o,'Outlays','#f47920'))},
      options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},
        plugins:{legend:{labels:{boxWidth:10,font:{size:11,family:'DM Sans'}}},tooltip:{callbacks:{label:function(c){return c.parsed.y==null?null:c.dataset.label+': '+bil(c.parsed.y);}}}},
        scales:{y:{ticks:{callback:function(v){return bil(v);},font:{size:10}}},x:{ticks:{font:{size:10},maxTicksLimit:14}}}}});
    if(el._nchart)el._nchart.destroy();
    el._nchart=new Chart(el.querySelector('.ih-nch canvas'),{type:'bar',data:{labels:N.map(function(r){return 'FY '+r.fy;}),datasets:[
      {label:'NYCHA',data:N.map(function(r){return r.nycha/1e6;}),backgroundColor:'#0d1b4b'},
      {label:'City agencies',data:N.map(function(r){return r.city/1e6;}),backgroundColor:'#f47920'},
      {label:'Everyone else (private owners, nonprofits, others)',data:N.map(function(r){return r.other/1e6;}),backgroundColor:'#9ECAE1'}]},
      options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},
        plugins:{legend:{labels:{boxWidth:10,font:{size:11,family:'DM Sans'}}},tooltip:{callbacks:{label:function(c){return c.dataset.label+': '+bil(c.parsed.y);},footer:function(items){var i=items[0].dataIndex;return 'Total: '+bil(N[i].total/1e6);}}}},
        scales:{x:{stacked:true,ticks:{font:{size:10}}},y:{stacked:true,ticks:{callback:function(v){return bil(v);},font:{size:10}}}}}});
    el.querySelector('.ih-hn').innerHTML='Federal budget: '+H.budget.source+', millions of dollars by federal fiscal year (October to September); dashed lines are the President\u2019s budget estimates. <a href="'+H.budget.url+'" target="_blank" rel="noopener">OMB</a>. '+
      'NYC: '+H.nyc.source+'. '+H.nyc.note+' <a href="'+H.nyc.url+'" target="_blank" rel="noopener">USAspending.gov</a>.';
  }
  function init(){
    var els=document.querySelectorAll('.inchist');if(!els.length)return;
    var st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
    var SX=null,TX=null,HU=null;
    Promise.all([fetch('/data/income-history.json').then(function(r){return r.json();}),
      SALE?fetch('/data/sales/rent-explorer.json').then(function(r){return r.json();}):null,
      SALE?fetch('/data/nyc-property-tax-rates.json').then(function(r){return r.json();}):null,
      fetch('/data/hud-nyc.json').then(function(r){return r.json();}).catch(function(){return null;})]).then(function(res){var D=res[0];TX=res[2];HU=res[3];
      if(res[1]){SX={months:res[1].months,A:{}};res[1].areas.forEach(function(a){SX.A[a.id]=a;});}
      needChart(function(){
      els.forEach(function(el){
        var boros=el.getAttribute('data-mode')==='boroughs',cd=el.getAttribute('data-cd')||'BKCB6';
        el.innerHTML='<div class="ih-h"><span class="ih-t">Median household income</span><span class="ih-s">'+(boros?'the five boroughs and the city':'district, borough and city')+', over time</span></div>'+
          (boros?'':'<div class="ih-pick"><select aria-label="Community district"></select></div>')+
          '<div class="ih-cards"></div><div class="ih-ch"><canvas></canvas></div><div class="ih-n"></div>'+
          (SALE?'<div class="ih-h"><span class="ih-t">Down payment needed</span><span class="ih-s">20% of the median asking price, all homes, and how many years of median income that is</span></div>'+
            '<div class="ih-dcards ih-cards"></div><div class="ih-ch ih-dch"><canvas></canvas></div><div class="ih-n">Down payment is 20% of the median asking price for all homes (StreetEasy). Each year uses the median of that year\'s monthly median asking prices, set against that year\'s median household income. The latest month is set against the latest income the Census has published.</div>'+
            '<div class="ih-h"><span class="ih-t">Monthly mortgage cost</span><span class="ih-s">principal and interest on the median asking price, 20% down, 30-year fixed</span></div>'+
            '<div class="ih-mcards ih-cards"></div><div class="ih-ch ih-mch"><canvas></canvas></div><div class="ih-n">Principal and interest on 80% of the median asking price for all homes, 30-year fixed at that year\'s average rate (Freddie Mac Primary Mortgage Market Survey, via FRED); the latest month uses that month\'s rate. Property taxes, insurance and co-op maintenance or condo common charges are not included.</div>'+
            '<div class="ih-h"><span class="ih-t">NYC property tax rates</span><span class="ih-s">every year since 1981/82</span></div>'+
            '<div class="ih-tcards ih-cards"></div><div class="ih-ch ih-tch"><canvas></canvas></div><div class="ih-n ih-tn"></div>':'')+
          '<div class="ih-h"><span class="ih-t">HUD&rsquo;s budget and HUD money in NYC</span><span class="ih-s">federal budget since 1962, awards in the five boroughs since FY 2010</span></div>'+
          '<div class="ih-hcards ih-cards"></div><div class="ih-ch ih-hch"><canvas></canvas></div><div class="ih-ch ih-nch"><canvas></canvas></div><div class="ih-n ih-hn"></div>';
        if(!boros){var sel=el.querySelector('select');
          Object.keys(D.acs.cd).sort(function(a,b){return a.slice(0,2)===b.slice(0,2)?(+a.slice(4))-(+b.slice(4)):a<b?-1:1;}).forEach(function(c){sel.add(new Option(cdName(c),c));});
          sel.value=cd;sel.onchange=function(){draw(el,D,sel.value);if(SX){drawDown(el,D,SX,sel.value);drawMonthly(el,D,SX,sel.value);}};}
        draw(el,D,cd);
        if(SX){drawDown(el,D,SX,cd);drawMonthly(el,D,SX,cd);}
        if(HU)drawHud(el,HU);
        if(TX){drawTax(el,TX);el.querySelector('.ih-tn').innerHTML='Fiscal year rates, as a percentage of <b>assessed value</b>, not of the price. NYC taxes one- to three-family homes on an assessed value capped at 6% of market value (with yearly limits on increases), and co-ops and condos on a value the Department of Finance sets from comparable rental buildings, so the tax bill is far below the rate times the price. '+(TX.note.split('. ').slice(1,2).join('')||'')+'. Source: <a href="'+TX.url+'" target="_blank" rel="noopener">NYC Department of Finance</a>.';}
      });
    });});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
