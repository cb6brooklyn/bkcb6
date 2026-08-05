/* Writes the data date onto any page that shows rent figures.
   Reads the month from the data itself, so it can never drift out of step
   with what is on screen. Drop <div class="datastamp"></div> anywhere on a
   page and include this script; if the element is absent nothing happens. */
(function(){
  var MONTHS=['January','February','March','April','May','June',
              'July','August','September','October','November','December'];
  function fmt(ym){
    var p=String(ym||'').split('-');
    if(p.length!==2) return '';
    var m=parseInt(p[1],10);
    return (MONTHS[m-1]||'')+' '+p[0];
  }
  function nextMonth(ym){
    var p=String(ym||'').split('-');
    if(p.length!==2) return '';
    var y=parseInt(p[0],10), m=parseInt(p[1],10);
    if(m===12){ y+=1; m=1; } else { m+=1; }
    return MONTHS[m-1]+' '+y;
  }
  function paint(last){
    var els=document.querySelectorAll('.datastamp');
    if(!els.length) return;
    var html='Latest data: <b>'+fmt(last)+'</b> &middot; updated the first week of '+
             nextMonth(last)+'. New StreetEasy figures land in the first week of each month.';
    els.forEach(function(el){ el.innerHTML=html; });
  }
  try{
    fetch('/data/rent-explorer.json',{cache:'no-store'})
      .then(function(r){return r.json();})
      .then(function(d){ paint((d.meta&&d.meta.last)||(d.months&&d.months[d.months.length-1])); })
      .catch(function(){});
  }catch(e){}
})();
