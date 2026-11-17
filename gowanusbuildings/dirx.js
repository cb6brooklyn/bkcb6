(function(){try{
var css=".dxn{max-width:900px;margin:12px auto 0;padding:0 14px}.dxn p{margin:0 0 10px;font-size:.95rem;line-height:1.5;color:#33405f}.dxq{width:100%;box-sizing:border-box;font:400 1rem 'DM Sans',sans-serif;padding:11px 14px;border:1.5px solid #0d1b4b;border-radius:999px;background:#fff;color:#0d1b4b}"+
".dxc{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0 0}.dxc a{font:700 .84rem 'DM Sans',sans-serif;border-radius:999px;padding:8px 13px;text-decoration:none;border:1.5px solid #0d1b4b;color:#0d1b4b;background:#fff}.dxc a.m{background:#f47920;border-color:#f47920;color:#fff}.dxn .dxk{font-size:.82rem;color:#4a5578;margin-top:8px;min-height:1em}"+
".dxtop{position:fixed;right:14px;bottom:18px;z-index:3000;background:#06024D;color:#fff;font:700 .92rem 'DM Sans',sans-serif;border:0;border-radius:999px;padding:12px 18px;box-shadow:0 3px 12px rgba(0,0,0,.35);cursor:pointer;display:none}";
var st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
var secs=[].slice.call(document.querySelectorAll('section.sec'));if(!secs.length)return;
var anchor=document.getElementById('evw')||document.querySelector('.top-bar');
var box=document.createElement('div');box.className='dxn';
var chips=secs.map(function(s){var h=s.querySelector('h2'),l=s.querySelector('.lede');return '<a href="#'+s.id+'">'+h.textContent+(l?' · '+l.textContent.split(',')[0]:'')+'</a>'}).join('');
box.innerHTML='<p>Every new building filed since the 2021 Gowanus rezoning: what it is, how many apartments, and what the zoning allows. Search a name or address, or jump to a group.</p><input class="dxq" type="search" placeholder="Search by building name or address" autocomplete="off"><div class="dxc">'+chips+'<a class="m" href="/gowanusbuildings/">The map</a><a class="m" href="/gowanusrezoning/">Rezoning map</a><a class="m" href="/gowanusbid/">BID map</a></div><div class="dxk"></div>';
anchor.parentNode.insertBefore(box,anchor.nextSibling);
var cards=[].slice.call(document.querySelectorAll('.dc'));
function grid(s){var g=s.nextElementSibling;return g&&g.classList.contains('dgrid')?g:null}
box.querySelector('.dxq').addEventListener('input',function(e){var t=e.target.value.trim().toLowerCase(),n=0;
  cards.forEach(function(c){var ok=!t||c.textContent.toLowerCase().indexOf(t)>=0;c.style.display=ok?'':'none';if(ok)n++});
  secs.forEach(function(s){var g=grid(s);var any=g&&[].some.call(g.querySelectorAll('.dc'),function(c){return c.style.display!=='none'});s.style.display=any?'':'none';if(g)g.style.display=any?'':'none'});
  box.querySelector('.dxk').textContent=t?n+(n===1?' building':' buildings'):''});
var top=document.createElement('button');top.className='dxtop';top.type='button';top.textContent='↑ Search';document.body.appendChild(top);
top.addEventListener('click',function(){box.scrollIntoView({behavior:'smooth'})});
window.addEventListener('scroll',function(){top.style.display=box.getBoundingClientRect().bottom<0?'block':'none'},{passive:true});
}catch(x){}})();
