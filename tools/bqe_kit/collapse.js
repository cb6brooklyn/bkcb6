// collapse the long sections below the story: each becomes a closed <details> with its heading as the summary (same as the Carroll Gardens page)
(function(){
  function mk(title,nodes,id){var d=document.createElement('details');d.className='cx';if(id)d.id=id;var s=document.createElement('summary');s.appendChild(title);d.appendChild(s);var b=document.createElement('div');b.className='cxb';nodes.forEach(function(n){b.appendChild(n);});d.appendChild(b);return d;}
  function head(el,txt){var h=el&&el.querySelector('h2');if(h){h.parentNode.removeChild(h);return h;}var x=document.createElement('h2');x.textContent=txt;return x;}
  ['boundaries','dashboard'].forEach(function(id){var el=document.getElementById(id);if(!el||el.closest('details.cx'))return;var p=el.parentNode,nx=el.nextSibling;el.removeAttribute('id');var d=mk(head(el,id==='dashboard'?'At a glance':'What this page means by CB6'),[el],id);p.insertBefore(d,nx);});
  var wrap=document.querySelector('.wrap');if(!wrap||wrap.querySelector('details.cx>.cxb section.sec'))return;
  var kids=Array.prototype.slice.call(wrap.childNodes),groups=[],cur=null;
  kids.forEach(function(n){if(n.nodeType===1&&n.tagName==='NAV'){cur=null;groups.push({keep:n});return;}
    if(n.nodeType===1&&n.tagName==='SECTION'&&n.classList.contains('sec')){cur={sec:n,nodes:[n]};groups.push(cur);return;}
    if(n.nodeType===1&&n.classList&&n.classList.contains('cb6head')){var h=n.querySelector('h2');cur={sec:n,nodes:[n],h:h};groups.push(cur);return;}
    if(!cur){cur={sec:null,nodes:[]};groups.push(cur);}cur.nodes.push(n);});
  groups.forEach(function(g){if(g.keep){wrap.appendChild(g.keep);return;}if(!g.sec){g.nodes.forEach(function(n){wrap.appendChild(n);});return;}var id=g.sec.id||'';var title=head(g.sec,'');g.sec.removeAttribute('id');wrap.appendChild(mk(title,g.nodes,id));});
  function openTo(hash){if(!hash||hash.length<2)return;var t=document.getElementById(decodeURIComponent(hash.slice(1)));if(!t)return;var p=t;while(p){if(p.tagName==='DETAILS')p.open=true;p=p.parentElement;}setTimeout(function(){t.scrollIntoView({behavior:'smooth',block:'start'});},30);}
  document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href^="#"]');if(!a)return;var h=a.getAttribute('href');if(h.length<2)return;var t=document.getElementById(decodeURIComponent(h.slice(1)));if(!t)return;var inClosed=false,p=t;while(p){if(p.tagName==='DETAILS'&&!p.open)inClosed=true;p=p.parentElement;}if(inClosed){e.preventDefault();history.replaceState(null,'',h);openTo(h);}});
  window.addEventListener('hashchange',function(){openTo(location.hash);});openTo(location.hash);
})();
