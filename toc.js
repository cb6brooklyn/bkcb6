(function(){
  const TOC = window.PAGE_TOC;
  if (!TOC || !TOC.length) return;

  const btn = document.createElement('button');
  btn.id = 'toc-btn';
  btn.innerHTML = '☰ Contents';
  btn.style.cssText = 'position:fixed;bottom:20px;right:16px;z-index:8000;background:#0d1b4b;color:#fff;border:2px solid #f47920;border-radius:24px;padding:9px 16px;font-family:"DM Sans",sans-serif;font-size:.78rem;font-weight:700;cursor:pointer;box-shadow:0 3px 12px rgba(0,0,0,.25);transition:transform .15s';

  const backdrop = document.createElement('div');
  backdrop.style.cssText = 'display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:8001';

  const panel = document.createElement('div');
  panel.style.cssText = 'display:none;position:fixed;bottom:0;left:0;right:0;z-index:8002;background:#fff;border-radius:16px 16px 0 0;box-shadow:0 -4px 24px rgba(0,0,0,.18);max-height:75vh;overflow-y:auto;font-family:"DM Sans",sans-serif';

  panel.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;padding:14px 20px 10px;border-bottom:1px solid #e5e2db;position:sticky;top:0;background:#fff;z-index:1">
      <div style="font-size:.7rem;font-family:'DM Mono',monospace;text-transform:uppercase;letter-spacing:.08em;color:#0d1b4b;font-weight:700">On This Page</div>
      <button id="toc-close" style="background:none;border:none;font-size:1.2rem;cursor:pointer;color:#9ca3af;padding:4px;line-height:1">✕</button>
    </div>
    <div style="padding:8px 0 24px">
      ${TOC.map(item => `
        <a href="${item.href}" onclick="closeTOC()" style="display:flex;align-items:center;gap:12px;padding:12px 20px;text-decoration:none;border-bottom:1px solid #f3f0eb">
          <span style="font-size:1rem;flex-shrink:0">${item.icon}</span>
          <div>
            <div style="font-size:.88rem;font-weight:700;color:#0d1b4b">${item.label}</div>
            ${item.sub ? `<div style="font-size:.72rem;color:#6b6760;margin-top:1px">${item.sub}</div>` : ''}
          </div>
          <span style="margin-left:auto;color:#f47920;font-size:.8rem;font-weight:700">↓</span>
        </a>`).join('')}
    </div>
  `;

  document.body.appendChild(backdrop);
  document.body.appendChild(panel);
  document.body.appendChild(btn);

  function openTOC() {
    panel.style.display = 'block';
    backdrop.style.display = 'block';
    btn.style.transform = 'scale(.95)';
  }
  window.closeTOC = function() {
    panel.style.display = 'none';
    backdrop.style.display = 'none';
    btn.style.transform = 'scale(1)';
  };

  btn.onclick = openTOC;
  backdrop.onclick = closeTOC;
  document.addEventListener('DOMContentLoaded', () => {
    const cl = document.getElementById('toc-close');
    if (cl) cl.onclick = closeTOC;
  });
})();
