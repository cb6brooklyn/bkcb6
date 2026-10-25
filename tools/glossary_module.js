// Glossary + guide to regulations. Data: /data/glossary.json (tools/build_glossary.py)
(function(){
  var G=null, st={q:'',kind:'all',area:'',agency:''}, showAll={};
  var $=function(id){return document.getElementById(id)};
  function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function hi(s){s=esc(s);if(!st.q)return s;var q=st.q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');try{return s.replace(new RegExp('('+q+')','ig'),'<mark>$1</mark>')}catch(e){return s}}
  function areaName(k){for(var i=0;i<G.areas.length;i++)if(G.areas[i].key===k)return G.areas[i].name;return k}
  function agBadge(a){var x=G.agencies[a]||{name:a};return '<button class="gx-ag'+(x.logo?'':' noimg')+'" data-ag="'+esc(a)+'" title="'+esc(x.name)+'">'+(x.logo?'<img src="'+esc(x.logo)+'" alt="" loading="lazy">':'')+esc(a)+'</button>'}
  function srcLink(refs){return (refs||[]).map(function(r){var s=G.sources[r.src]||{name:r.src};var u=r.url||s.url;var t=s.name+(r.page?', p. '+r.page:'');return u?'<a class="gx-src" href="'+esc(u)+'" target="_blank" rel="noopener">'+esc(t)+' ↗</a>':'<span class="gx-src">'+esc(t)+'</span>'}).join(' · ')}
  function hay(x){return (x.term||x.rule||'')+' '+(x.aka||[]).join(' ')+' '+(x.def||x.what||'')+' '+(x.who||'')+' '+(x.penalty||'')+' '+(x.tags||'')+' '+x.agencies.map(function(a){return a+' '+((G.agencies[a]||{}).name||'')}).join(' ')}
  var _qr=null,_qk=null;
  function qres(){if(_qk!==st.q){_qk=st.q;_qr=st.q.toLowerCase().split(/\s+/).filter(Boolean).map(function(w){return new RegExp('(^|[^a-z0-9])'+w.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'))})}return _qr}
  function score(x){if(!st.q)return 0;var n=(x.term||x.rule||'').toLowerCase()+' '+(x.aka||[]).join(' ').toLowerCase(),q=st.q.toLowerCase();if(n.indexOf(q)===0)return 3;var re=qres(),all=true;for(var i=0;i<re.length;i++)if(!re[i].test(n))all=false;return all?2:0}
  function match(x){
    if(st.area&&x.area!==st.area)return false;
    if(st.agency&&x.agencies.indexOf(st.agency)<0)return false;
    if(st.q){var re=qres();for(var i=0;i<re.length;i++)if(!re[i].test(x._h))return false}
    return true;
  }
  function termHTML(t){
    return '<div class="gx-e" id="'+esc(t.id)+'"><div class="h"><div><div class="term">'+hi(t.term)+(t.zr?' <span title="Legally defined in the Zoning Resolution" style="color:var(--orange)">*</span>':'')+'</div>'
      +(t.aka&&t.aka.length?'<div class="aka">Also: '+hi(t.aka.join(', '))+'</div>':'')+'</div>'
      +'<button class="gx-copy" data-link="'+esc(t.id)+'" title="Copy a link to this term">🔗</button></div>'
      +'<div class="d">'+hi(t.def)+'</div><div class="m">'+(st.area?'':'<button class="gx-area" data-area="'+t.area+'">'+esc(areaName(t.area))+'</button>')+t.agencies.map(agBadge).join('')+' '+srcLink(t.refs)+'</div></div>';
  }
  function ruleHTML(r){
    return '<div class="gx-e gx-r" id="'+esc(r.id)+'"><div class="h"><div class="term">'+hi(r.rule)+'</div><div style="display:flex;gap:6px;align-items:center">'+(r.who?'<span class="who">'+esc(r.who)+'</span>':'')
      +'<button class="gx-copy" data-link="'+esc(r.id)+'" title="Copy a link to this rule">🔗</button></div></div>'
      +'<div class="d">'+hi(r.what)+'</div>'+(r.penalty?'<div class="pen"><b>If not followed:</b> '+hi(r.penalty)+'</div>':'')
      +'<div class="m">'+(st.area?'':'<button class="gx-area" data-area="'+r.area+'">'+esc(areaName(r.area))+'</button>')+r.agencies.map(agBadge).join('')+' '+srcLink(r.refs)+'</div></div>';
  }
  function chips(){
    var pool=[].concat(st.kind!=='rules'?G.terms:[],st.kind!=='terms'?G.rules:[]);
    var ac={},gc={};
    pool.forEach(function(x){
      var okQ=!st.q||(function(){var re=qres();for(var i=0;i<re.length;i++)if(!re[i].test(x._h))return false;return true})();
      if(!okQ)return;
      if(!st.agency||x.agencies.indexOf(st.agency)>=0)ac[x.area]=(ac[x.area]||0)+1;
      if(!st.area||x.area===st.area)x.agencies.forEach(function(a){gc[a]=(gc[a]||0)+1});
    });
    var h='<button class="gx-chip'+(st.area?'':' on')+'" data-area="">All areas</button>';
    G.areas.forEach(function(a){if(!ac[a.key]&&st.area!==a.key)return;h+='<button class="gx-chip'+(st.area===a.key?' on':'')+'" data-area="'+a.key+'">'+esc(a.name)+' <span class="n">'+(ac[a.key]||0)+'</span></button>'});
    $('gx-areas').innerHTML=h;
    var ags=Object.keys(gc).sort(function(a,b){return gc[b]-gc[a]||a.localeCompare(b)});
    if(st.agency&&ags.indexOf(st.agency)<0)ags.unshift(st.agency);
    h='<button class="gx-chip'+(st.agency?'':' on')+'" data-agency="">All agencies</button>';
    ags.forEach(function(a){var x=G.agencies[a]||{name:a};h+='<button class="gx-chip'+(st.agency===a?' on':'')+'" data-agency="'+esc(a)+'" title="'+esc(x.name)+'">'+(x.logo?'<img src="'+esc(x.logo)+'" alt="">':'')+esc(a)+' <span class="n">'+(gc[a]||0)+'</span></button>'});
    $('gx-agencies').innerHTML=h;
    setTimeout(function(){document.querySelectorAll('.gx-row .gx-chip.on').forEach(function(c){var r=c.parentNode;r.scrollLeft=c.offsetLeft-r.offsetLeft-16})},0);
    document.querySelectorAll('#gx-kind button').forEach(function(b){b.classList.toggle('on',b.dataset.k===st.kind)});
  }
  function render(){
    chips();
    var filtering=!!(st.q||st.area||st.agency);
    var T=st.kind==='rules'?[]:G.terms.filter(match), R=st.kind==='terms'?[]:G.rules.filter(match);
    if(st.q){var by=function(a,b){return score(b)-score(a)};T=T.slice().sort(by);R=R.slice().sort(by)}
    $('gloss-count').textContent=T.length+' term'+(T.length===1?'':'s')+' · '+R.length+' rule'+(R.length===1?'':'s')+(st.q?' matching “'+st.q+'”':'')+(st.agency?' · '+((G.agencies[st.agency]||{}).name||st.agency):'')+(st.area?' · '+areaName(st.area):'');
    $('gx-reset').hidden=!filtering&&st.kind==='all';
    if(!T.length&&!R.length){$('gloss-list').innerHTML='<div class="gx-empty">Nothing matches. Try another word or clear the filters.</div>';return}
    var h='';
    var areas=G.areas.slice();if(st.q){var best={};T.concat(R).forEach(function(x){var v=score(x);if(!(x.area in best)||v>best[x.area])best[x.area]=v});areas.sort(function(a,b){return (best[b.key]||0)-(best[a.key]||0)})}
    areas.forEach(function(a){
      var t=T.filter(function(x){return x.area===a.key}), r=R.filter(function(x){return x.area===a.key});
      if(!t.length&&!r.length)return;
      var lg={};t.concat(r).forEach(function(x){x.agencies.forEach(function(g){lg[g]=(lg[g]||0)+1})});
      var top=Object.keys(lg).sort(function(x,y){return lg[y]-lg[x]}).filter(function(g){return (G.agencies[g]||{}).logo}).slice(0,4);
      h+='<details class="gx-grp" data-g="'+a.key+'"'+(filtering?' open':'')+'><summary><span class="t">'+esc(a.name)+'</span><span class="gx-logos">'+top.map(function(g){return '<img src="'+esc(G.agencies[g].logo)+'" alt="'+esc(g)+'" title="'+esc(G.agencies[g].name)+'" loading="lazy">'}).join('')+'</span><span class="c">'+[t.length?t.length+' term'+(t.length===1?'':'s'):'',r.length?r.length+' rule'+(r.length===1?'':'s'):''].filter(Boolean).join(' · ')+'</span><span class="ch">›</span></summary>';
      [['rules',r,ruleHTML,'Rules & regulations'],['terms',t,termHTML,'Terms']].forEach(function(p){
        var list=p[1];if(!list.length)return;var key=a.key+':'+p[0];var lim=showAll[key]||filtering&&list.length<=60?list.length:12;
        if(r.length&&t.length)h+='<div class="gx-sub">'+p[3]+'</div>';
        h+=list.slice(0,lim).map(p[2]).join('');
        if(list.length>lim)h+='<button class="gx-more" data-more="'+key+'">Show all '+list.length+' '+(p[0]==='rules'?'rules':'terms')+'</button>';
      });
      h+='</details>';
    });
    $('gloss-list').innerHTML=h;
    var u=new URL(location.href);['q','area','agency','kind'].forEach(function(k){var v=st[k];if(v&&!(k==='kind'&&v==='all'))u.searchParams.set(k,v);else u.searchParams.delete(k)});
    history.replaceState(null,'',u.pathname+(u.search||'')+location.hash);
  }
  function openTarget(){
    var id=decodeURIComponent((location.hash||'').slice(1));if(!id)return;
    var x=G.terms.concat(G.rules).filter(function(e){return e.id===id})[0];if(!x)return;
    if(!document.getElementById(id)){st={q:'',kind:'all',area:x.area,agency:''};showAll[x.area+':'+(x.rule?'rules':'terms')]=1;render()}
    var el=document.getElementById(id);if(!el)return;var g=el.closest('details');if(g)g.open=true;setTimeout(function(){el.scrollIntoView({block:'start'})},60);
  }
  document.addEventListener('click',function(e){
    var b=e.target.closest('[data-area],[data-agency],[data-ag],[data-more],[data-k],[data-link],#gx-reset');if(!b)return;
    if(b.id==='gx-reset'){st={q:'',kind:'all',area:'',agency:''};$('gloss-search').value='';render();return}
    if(b.dataset.more){showAll[b.dataset.more]=1;render();var g=document.querySelector('[data-g="'+b.dataset.more.split(':')[0]+'"]');if(g)g.open=true;return}
    if(b.dataset.k){st.kind=b.dataset.k;render();return}
    if(b.dataset.link){var u=location.origin+location.pathname+'#'+b.dataset.link;(navigator.clipboard?navigator.clipboard.writeText(u):Promise.reject()).then(function(){b.textContent='✓';setTimeout(function(){b.textContent='🔗'},1200)},function(){location.hash=b.dataset.link});return}
    if('area' in b.dataset){st.area=st.area===b.dataset.area?'':b.dataset.area;render();$('gloss-top').scrollIntoView({block:'start'});return}
    var a=b.dataset.agency!=null?b.dataset.agency:b.dataset.ag;
    if(a!=null){st.agency=(st.agency===a&&b.dataset.ag==null)?'':a;render();$('gloss-top').scrollIntoView({block:'start'})}
  });
  var tmr;$('gloss-search').addEventListener('input',function(e){clearTimeout(tmr);tmr=setTimeout(function(){st.q=e.target.value.trim();render()},120)});
  window.addEventListener('hashchange',openTarget);
  fetch('/data/glossary.json').then(function(r){return r.json()}).then(function(d){
    G=d;G.terms.concat(G.rules).forEach(function(x){x._h=hay(x).toLowerCase()});
    var p=new URLSearchParams(location.search);['q','area','agency','kind'].forEach(function(k){if(p.get(k))st[k]=p.get(k)});
    $('gloss-search').value=st.q;render();openTarget();
  }).catch(function(){$('gloss-count').textContent='The glossary could not load. Check your connection and refresh.'});
  window.glossFilter=function(){};window.setGlossFilter=function(f){st.area=f==='all'?'':f;render()};
})();
