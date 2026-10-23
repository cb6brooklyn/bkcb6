/* Election records on the look-back page: who got the most votes, who was on the most ballots, the closest
   contests, for New York City, a borough or a community district. Reads /data/ballots/records/<scope>.json,
   built by tools/build_election_records.py from the ballots and results on this site; every line links to the
   ballot it comes from and to the Board of Elections or Wikipedia record behind it. */
(function(){
  var box=document.getElementById('recBox');if(!box)return;
  function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(m){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m];});}
  function j(u){return fetch(u).then(function(r){if(!r.ok)throw new Error(u);return r.json();});}
  var BA={'1':'MN','2':'BX','3':'BK','4':'QN','5':'SI'},BN={'1':'Manhattan','2':'Bronx','3':'Brooklyn','4':'Queens','5':'Staten Island'};
  function label(sc){if(sc==='nyc')return 'New York City';if(/^[a-z]{2}$/.test(sc))return {bk:'Brooklyn',mn:'Manhattan',qn:'Queens',bx:'Bronx',si:'Staten Island'}[sc];return BA[sc[0]]+'CB'+(+sc.slice(1));}
  function longLabel(sc){if(/^\d{3}$/.test(sc))return BN[sc[0]]+' Community District '+(+sc.slice(1))+' ('+label(sc)+')';return label(sc);}
  var q=new URLSearchParams(location.search),cb=q.get('cb'),sc0=q.get('scope');
  var home=cb&&/^[1-5]\d\d$/.test(cb)?cb:(sc0==='bk'||sc0==='nyc'?sc0:'306');
  var scopes=[];if(/^\d{3}$/.test(home)){scopes.push(home);var b={'1':'mn','2':'bx','3':'bk','4':'qn','5':'si'}[home[0]];if(b)scopes.push(b);}else if(home==='bk')scopes.push('bk');scopes.push('nyc');
  if(scopes.indexOf('306')<0&&scopes[0]!=='bk'&&home!=='bk'&&home!=='nyc')scopes.splice(1,0,'306');
  var PER=[['all','All time'],['2000','Since 2000'],['2012','Since 2012'],['2020','Since 2020']];
  var cur={scope:scopes[0],per:'all'},DATA={},IDX=null,rnd=null;
  function nice(d){var m=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];var p=d.split('-');return m[+p[1]-1]+' '+(+p[2])+', '+p[0];}
  function n(x){return x==null?'':Number(x).toLocaleString();}
  function eb(e){return e&&e.est?' <span class="est" title="Estimated from Assembly district results">est.</span>':'';}
  function party(p){return (p||[]).join(' · ');}
  function dist(e){var d=e.d||'';if(!d||d==='NYC')return '';if(/^\d+$/.test(d)){var o=(e.o||'');if(/Congress/i.test(o))return 'District '+d;if(/Senat/i.test(o))return 'District '+d;if(/Assembly/i.test(o))return 'District '+d;if(/Council/i.test(o))return 'District '+d;return d;}return d;}
  function where(e){var o=esc(e.o);var d=dist(e);var pp=e.pp?esc(e.pp)+' primary':'';return o+(d?', '+esc(d):'')+(pp?' ('+pp+')':'');}
  function lnk(e,txt){return '<a href="#" class="rb" data-d="'+e.date+'" title="Open this ballot, with the results">'+(txt||'ballot')+'</a>'+(e.src?' · <a href="'+esc(e.src.u)+'" target="_blank" rel="noopener" title="'+esc(e.src.t)+'">source</a>':'');}
  function line(main,sub,e){return '<div class="rl"><div class="rm">'+main+'</div><div class="rs">'+sub+(e?' · '+lnk(e):'')+'</div></div>';}
  var TYPES=[
    {k:'mostOne',t:'Most votes in one contest',d:'One candidate, one contest, the votes cast in {A}.',
      row:function(e){return line('<b>'+esc(e.n)+'</b> <span class="rv">'+n(e.v)+'</span>'+eb(e)+(e.pct!=null?' <small>('+e.pct+'%)</small>':''),where(e)+', '+nice(e.date),e);},
      big:function(e){return {v:n(e.v)+eb(e),s:esc(e.n)+', '+where(e)+', '+nice(e.date),e:e};}},
    {k:'career',t:'Most votes, all contests combined',d:'Every vote cast for the name in {A}, in vote-for-one public offices.',
      row:function(c){return line('<b>'+esc(c.n)+'</b> <span class="rv">'+n(c.v)+'</span>'+(c.best&&c.best.est?eb(c.best):''),c.contests+' contest'+(c.contests===1?'':'s')+', '+c.first.slice(0,4)+' to '+c.last.slice(0,4)+': '+esc(c.offices.join(', '))+(c.best?' · best '+n(c.best.v)+eb(c.best)+' as '+where(c.best)+', '+nice(c.best.date):''),c.best);},
      big:function(c){return {v:n(c.v),s:esc(c.n)+', '+c.contests+' contests, '+c.first.slice(0,4)+' to '+c.last.slice(0,4),e:c.best};}},
    {k:'ballots',t:'On the most ballots',d:'Election days on which the name appeared on a ballot in {A}, any office.',
      row:function(c){return line('<b>'+esc(c.n)+'</b> <span class="rv">'+c.elections+'</span> <small>elections</small>',c.first.slice(0,4)+' to '+c.last.slice(0,4)+': '+esc(c.offices.join(', ')),{date:c.last,src:null});},
      big:function(c){return {v:c.elections+' ballots',s:esc(c.n)+', '+c.first.slice(0,4)+' to '+c.last.slice(0,4)+', '+esc(c.offices.join(', ')),e:{date:c.last}};}},
    {k:'offices',t:'Most different offices sought',d:'Distinct offices the name ran for in {A}.',
      row:function(c){return line('<b>'+esc(c.n)+'</b> <span class="rv">'+c.offices.length+'</span> <small>offices</small>',esc(c.offices.join(', '))+' · '+c.elections+' elections, '+c.first.slice(0,4)+' to '+c.last.slice(0,4),{date:c.last,src:null});},
      big:function(c){return {v:c.offices.length+' offices',s:esc(c.n)+': '+esc(c.offices.join(', ')),e:{date:c.last}};}},
    {k:'wins',t:'{W}',d:'Contests in which the name had the most votes in {A} (vote-for-one public offices; ranked-choice primaries not counted).',
      row:function(c){return line('<b>'+esc(c.n)+'</b> <span class="rv">'+c.wins+'</span> <small>contests</small>'+(c.ex&&c.ex.est?eb(c.ex):''),c.first.slice(0,4)+' to '+c.last.slice(0,4)+': '+esc(c.offices.join(', ')),c.ex);},
      big:function(c){return {v:c.wins+' contests',s:esc(c.n)+', '+c.first.slice(0,4)+' to '+c.last.slice(0,4)+', '+esc(c.offices.join(', ')),e:c.ex};}},
    {k:'share',t:'Largest share',d:'Highest share of the vote in {A} in a contest with at least two candidates and {M} votes.',
      row:function(e){return line('<b>'+esc(e.n)+'</b> <span class="rv">'+e.pct+'%</span>'+eb(e)+' <small>('+n(e.v)+' of '+n(e.tot)+')</small>',where(e)+', '+nice(e.date)+' · runner-up '+esc(e.runner)+', '+n(e.runnerV),e);},
      big:function(e){return {v:e.pct+'%'+eb(e),s:esc(e.n)+', '+where(e)+', '+nice(e.date)+' ('+n(e.v)+' of '+n(e.tot)+')',e:e};}},
    {k:'closest',t:'Closest contest',d:'Smallest margin between first and second in {A}, in a contest with {M} votes.',
      row:function(e){return line('<b>'+esc(e.n)+'</b> by <span class="rv">'+n(e.margin)+'</span> <small>vote'+(e.margin===1?'':'s')+'</small>'+eb(e),where(e)+', '+nice(e.date)+' · '+n(e.v)+' to '+n(e.runnerV)+' over '+esc(e.runner),e);},
      big:function(e){return {v:n(e.margin)+' vote'+(e.margin===1?'':'s')+eb(e),s:esc(e.n)+' over '+esc(e.runner)+', '+where(e)+', '+nice(e.date)+' ('+n(e.v)+' to '+n(e.runnerV)+')',e:e};}},
    {k:'turnout',t:'Most votes cast in one contest',d:'Votes cast for all candidates in {A} in a single vote-for-one contest.',
      row:function(e){return line('<span class="rv">'+n(e.tot)+'</span> <small>votes</small>'+eb(e)+' · '+where(e),nice(e.date)+' · led by '+esc(e.n)+', '+n(e.v)+(e.pct!=null?' ('+e.pct+'%)':''),e);},
      big:function(e){return {v:n(e.tot)+' votes'+eb(e),s:where(e)+', '+nice(e.date)+', led by '+esc(e.n)+' with '+n(e.v),e:e};}}
  ];
  function winsTitle(sc){return sc==='nyc'?'Most contests won':'Carried '+label(sc)+' the most times';}
  function load(sc){if(DATA[sc])return Promise.resolve(DATA[sc]);return j('/data/ballots/records/'+sc+'.json').then(function(d){DATA[sc]=d;return d;}).catch(function(){return null;});}
  function render(){
    var h='<div class="rt">'+scopes.map(function(s){return '<button type="button" data-s="'+s+'"'+(s===cur.scope?' class="on"':'')+'>'+esc(label(s))+'</button>';}).join('')+
      '<select id="recPer" aria-label="Period">'+PER.map(function(p){return '<option value="'+p[0]+'"'+(p[0]===cur.per?' selected':'')+'>'+p[1]+'</option>';}).join('')+'</select></div><div id="recBody"><p class="note">Loading&hellip;</p></div>';
    box.innerHTML=h;
    box.querySelector('.rt').addEventListener('click',function(ev){var b=ev.target.closest('button[data-s]');if(!b)return;cur.scope=b.getAttribute('data-s');rnd=null;render();});
    document.getElementById('recPer').onchange=function(){cur.per=this.value;rnd=null;body();};
    body();
  }
  function body(){
    var el=document.getElementById('recBody');
    Promise.all([load(cur.scope),IDX?Promise.resolve(IDX):j('/data/ballots/records/index.json').then(function(x){IDX=x;return x;}).catch(function(){return null;})]).then(function(a){var d=a[0];
      if(!d||!d.periods[cur.per]){el.innerHTML='<p class="note">No records on file for '+esc(longLabel(cur.scope))+' in this period.</p>';return;}
      var P=d.periods[cur.per],A=label(cur.scope),M=n((IDX||{}).minVotes||1000);
      var avail=TYPES.filter(function(T){return (P[T.k]||[]).length;});
      if(rnd==null||!avail[rnd])rnd=Math.floor(Math.random()*avail.length);
      var T=avail[rnd],top=P[T.k][0],bg=T.big(top);
      var h='<div class="rbig"><div class="rk">Random record · '+esc(A)+' · '+esc(PER.filter(function(p){return p[0]===cur.per;})[0][1].toLowerCase())+'</div><div class="rbt">'+esc(T.t.replace('{W}',winsTitle(cur.scope)))+'</div><div class="rbv">'+bg.v+'</div><div class="rbs">'+bg.s+'</div>'+
        '<div class="rba">'+(bg.e&&bg.e.date?'<a href="#" class="rb cbbtn" data-d="'+bg.e.date+'">See that ballot</a> ':'')+(bg.e&&bg.e.src?'<a class="cbbtn alt" href="'+esc(bg.e.src.u)+'" target="_blank" rel="noopener">Source: '+esc(bg.e.src.t)+'</a> ':'')+'<button type="button" class="cbbtn alt" id="recAnother">Another</button></div></div>';
      h+='<p class="note" style="margin:8px 0 10px">'+esc(longLabel(cur.scope))+': '+n(P.elections)+' elections and '+n(P.contests)+' contests on file, '+nice(P.from)+' to '+nice(P.to)+(P.estimatedContests?', of which '+n(P.estimatedContests)+' (2000 to 2013) are estimates from Assembly district results, marked est.':'')+'. Every line links to the ballot it comes from (with the results) and to the record behind it.</p>';
      h+='<div class="bgrid">'+TYPES.map(function(T){var L=P[T.k]||[];if(!L.length)return '';
        return '<div class="gc"><div class="gh" style="cursor:default"><div><div class="go">'+esc(T.t.replace('{W}',winsTitle(cur.scope)))+'</div><div class="gd">'+esc(T.d.replace('{A}',A).replace('{M}',M))+'</div></div></div><div class="rlist">'+L.map(T.row).join('')+'</div></div>';}).join('')+'</div>';
      if(IDX&&IDX.notes)h+='<div class="note" style="margin-top:12px"><b>How these are counted.</b> '+IDX.notes.map(esc).join(' ')+' Built from the ballots and results on this site; the data files are at <a href="/data/ballots/records/'+cur.scope+'.json">/data/ballots/records/'+cur.scope+'.json</a>.</div>';
      el.innerHTML=h;
      document.getElementById('recAnother').onclick=function(){rnd=(rnd+1+Math.floor(Math.random()*Math.max(1,avail.length-1)))%avail.length;body();};
      [].forEach.call(el.querySelectorAll('a.rb'),function(a){a.addEventListener('click',function(ev){ev.preventDefault();var d=a.getAttribute('data-d');if(window.ttGo)window.ttGo(d);});});
    });
  }
  var css=document.createElement('style');css.textContent=
    '.rt{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:4px 0 10px}.rt button,.rt select{font:700 .8rem "DM Sans",sans-serif;border:1.5px solid var(--border);background:#fff;color:var(--navy);border-radius:8px;padding:7px 10px;cursor:pointer}.rt button.on{background:var(--navy);color:#fff;border-color:var(--navy)}'+
    '.rbig{border:2px solid var(--navy);border-radius:12px;padding:14px 16px;background:#fff}.rk{font:500 .6rem "DM Mono",monospace;text-transform:uppercase;letter-spacing:.08em;color:var(--orange)}.rbt{font:800 1rem "DM Sans",sans-serif;color:var(--navy);margin-top:2px}'+
    '.rbv{font:900 2.2rem/1.05 "DM Sans",sans-serif;color:var(--navy);margin:6px 0 2px;letter-spacing:-.02em}.rbs{font-size:.84rem;color:#333;line-height:1.45}.rba{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}.rba .cbbtn{text-decoration:none;display:inline-block}.cbbtn.alt{background:#fff;color:var(--navy);border:1.5px solid var(--navy)}'+
    '.est{display:inline-block;font:700 .58rem "DM Mono",monospace;text-transform:uppercase;letter-spacing:.06em;color:#b45309;border:1px solid #b45309;border-radius:4px;padding:1px 4px;vertical-align:middle}'+
    '.rlist{padding:4px 12px 8px}.rl{padding:8px 0;border-top:1px solid var(--border)}.rl:first-child{border-top:0}.rm{font-size:.9rem;color:var(--navy)}.rv{font:800 .95rem "DM Mono",monospace;color:var(--orange)}.rs{font-size:.72rem;color:var(--muted);line-height:1.45;margin-top:2px}.rs a{color:var(--navy)}';
  document.head.appendChild(css);
  render();
})();
