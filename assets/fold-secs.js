/* Profile pages without the tiles block (schools, school districts, Community Education Councils): every section folds
   under its title by default, except the opening bio and the map. */
(function () {
  function run() {
    if (!document.getElementById('foldsecs-css')) {
      var st = document.createElement('style'); st.id = 'foldsecs-css';
      st.textContent = 'details.pfold{border-top:1px solid #e5e2db;background:#fff}details.pfold>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:8px;padding:14px 18px;font:500 .72rem/1.3 "DM Mono",monospace;letter-spacing:.1em;text-transform:uppercase;color:#0d1b4b}'
        + 'details.pfold>summary::-webkit-details-marker{display:none}details.pfold>summary .arr{margin-left:auto;font-size:.7rem;transition:transform .15s}details.pfold[open]>summary .arr{transform:rotate(180deg)}'
        + 'details.pfold>.sec{border-top:0;padding-top:4px}details.pfold>.sec>h2{display:none}';
      document.head.appendChild(st);
    }
    var all = document.querySelectorAll('.sec');
    Array.prototype.forEach.call(all, function (sec, i) {
      // the first section is the bio (an intro block, or "What it is")
      if (i === 0 || sec.closest('details.pfold') || sec.classList.contains('introsec') || sec.querySelector('[data-profile-map]')) return;
      var h = sec.querySelector(':scope > h2'); if (!h) return;
      var d = document.createElement('details'); d.className = 'pfold';
      var sm = document.createElement('summary');
      sm.textContent = h.textContent.replace(/\s+/g, ' ').trim();
      var a = document.createElement('span'); a.className = 'arr'; a.innerHTML = '&#9660;'; sm.appendChild(a);
      sec.parentNode.insertBefore(d, sec); d.appendChild(sm); d.appendChild(sec);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run); else run();
})();
