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
  function init(){
    var els=document.querySelectorAll('.inchist');if(!els.length)return;
    var st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
    fetch('/data/income-history.json').then(function(r){return r.json();}).then(function(D){needChart(function(){
      els.forEach(function(el){
        var boros=el.getAttribute('data-mode')==='boroughs',cd=el.getAttribute('data-cd')||'BKCB6';
        el.innerHTML='<div class="ih-h"><span class="ih-t">Median household income</span><span class="ih-s">'+(boros?'the five boroughs and the city':'district, borough and city')+', over time</span></div>'+
          (boros?'':'<div class="ih-pick"><select aria-label="Community district"></select></div>')+
          '<div class="ih-cards"></div><div class="ih-ch"><canvas></canvas></div><div class="ih-n"></div>';
        if(!boros){var sel=el.querySelector('select');
          Object.keys(D.acs.cd).sort(function(a,b){return a.slice(0,2)===b.slice(0,2)?(+a.slice(4))-(+b.slice(4)):a<b?-1:1;}).forEach(function(c){sel.add(new Option(cdName(c),c));});
          sel.value=cd;sel.onchange=function(){draw(el,D,sel.value);};}
        draw(el,D,cd);
      });
    });});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
