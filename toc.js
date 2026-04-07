// Shared TOC: renders inline toggle after intro + back-to-top after sections
(function(){
  const TOC = window.PAGE_TOC;
  if (!TOC || !TOC.length) return;

  // ── INLINE TOC TOGGLE ────────────────────────────────────────────────
  const anchor = document.getElementById('toc-insert');
  if (anchor) {
    const wrap = document.createElement('div');
    wrap.style.cssText = 'border-top:1px solid #e5e2db;background:#f8f7f4';

    const btn = document.createElement('button');
    btn.style.cssText = 'width:100%;padding:11px 20px;background:none;border:none;text-align:left;cursor:pointer;font-family:"DM Sans",sans-serif;display:flex;align-items:center;justify-content:space-between;font-size:.82rem;font-weight:700;color:#0d1b4b';
    btn.innerHTML = '📋 Table of Contents <span style="font-size:.72rem;color:#6b6760;font-weight:400">▼</span>';

    const list = document.createElement('div');
    list.style.cssText = 'display:none;padding:4px 0 12px';

    TOC.forEach(item => {
      const a = document.createElement('a');
      a.href = item.href;
      a.style.cssText = 'display:flex;align-items:center;gap:10px;padding:9px 20px;text-decoration:none;border-bottom:1px solid #f0ede8';
      a.innerHTML = `<span style="font-size:.9rem;flex-shrink:0">${item.icon}</span>
        <div style="flex:1">
          <div style="font-size:.82rem;font-weight:700;color:#0d1b4b">${item.label}</div>
          ${item.sub ? `<div style="font-size:.7rem;color:#6b6760">${item.sub}</div>` : ''}
        </div>
        <span style="color:#f47920;font-size:.75rem;font-weight:700">↓</span>`;
      a.onclick = () => { list.style.display='none'; btn.querySelector('span').textContent='▼'; };
      list.appendChild(a);
    });

    btn.onclick = () => {
      const open = list.style.display === 'block';
      list.style.display = open ? 'none' : 'block';
      btn.querySelector('span').textContent = open ? '▼' : '▲';
    };

    wrap.appendChild(btn);
    wrap.appendChild(list);
    anchor.parentNode.insertBefore(wrap, anchor.nextSibling);
  }

  // ── BACK TO TOP ──────────────────────────────────────────────────────
  document.querySelectorAll('[data-back-top]').forEach(el => {
    const div = document.createElement('div');
    div.style.cssText = 'padding:8px 20px;background:#f8f7f4;border-top:1px solid #e5e2db;text-align:right';
    div.innerHTML = '<a href="#" onclick="window.scrollTo({top:0,behavior:\'smooth\'});return false" style="font-size:.72rem;font-family:\'DM Mono\',monospace;color:#9ca3af;text-decoration:none;font-weight:600">↑ Back to top</a>';
    el.parentNode.insertBefore(div, el.nextSibling);
  });
})();
