/* This week's meetings: equal squares, each one opens its event. Data: https://bkcb6.app/data/week-banner.json
   Mount: <div id="week-banner"></div><script src="https://bkcb6.app/assets/week-banner.js"></script>
   On the app page (press/week-banner.html) the squares fill the frame's height and links open in place. */
(function () {
  var framed = /[?&]web=1/.test(location.search);
  var app = !framed && (/[?&]app=1/.test(location.search) || document.documentElement.hasAttribute('data-app'));
  function mount() {
    var el = document.getElementById('week-banner');
    if (!el) { el = document.createElement('div'); el.id = 'week-banner'; var c = document.getElementById('cb6-app-calendar'); if (!c) return; c.parentNode.insertBefore(el, c); }
    if (el.dataset.done) return; el.dataset.done = '1';
    if (!document.getElementById('wb-css')) {
      var st = document.createElement('style'); st.id = 'wb-css';
      st.textContent = '#week-banner .wb{display:grid;gap:6px;margin:0 0 14px}'
        + '#week-banner a{display:block;aspect-ratio:1/1;border-radius:8px;overflow:hidden;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.18);line-height:0;min-width:0}'
        + '#week-banner img{display:block;width:100%;height:100%;object-fit:cover;border:0}'
        + 'html[data-app] #week-banner .wb{margin:0;padding:4px 10px;justify-content:center}'
        + '@media(max-width:700px){#week-banner .wb.wb-web{grid-template-columns:repeat(var(--wbm),minmax(0,1fr))!important;gap:10px}#week-banner .wb.wb-web a{border-radius:10px}}';
      document.head.appendChild(st);
    }
    fetch('https://bkcb6.app/data/week-banner.json?_=' + Math.floor(Date.now() / 600000), { cache: 'no-cache' })
      .then(function (r) { return r.json(); }).then(function (d) {
        var now = Date.now();
        d.items = (d.items || []).filter(function (x) { return !x.ends || new Date(x.ends).getTime() > now; });
        // a meeting already shown in the page's own banner is not repeated as a square
        var shown = [].map.call(document.querySelectorAll('.cb6-fb-banner a[href]'), function (x) { return x.href.replace(/\/+$/, ''); });
        d.items = d.items.filter(function (x) { return shown.indexOf(String(x.href || '').replace(/\/+$/, '')) < 0; });
        if (!d.items.length) { el.style.display = 'none'; return; }
        var n = d.items.length;
        el.innerHTML = '<div class="wb' + ((app || framed) ? '' : ' wb-web') + '" style="--wbm:' + Math.min(n, 3) + ';grid-template-columns:' + ((app || framed) ? 'repeat(' + n + ',min(calc((100vw - 20px - ' + (6 * (n - 1)) + 'px) / ' + n + '),calc(100vh - 8px)))' : 'repeat(' + n + ',minmax(0,1fr))') + '">' + d.items.map(function (x) {
          return '<a href="' + x.href + '"' + (app ? '' : ' target="_blank" rel="noopener"') + ' title="' + x.alt.replace(/"/g, '&quot;') + '"><img src="' + x.img + '" alt="' + x.alt.replace(/"/g, '&quot;') + '" loading="lazy" decoding="async"></a>';
        }).join('') + '</div>';
      }).catch(function () { el.style.display = 'none'; });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
  setTimeout(mount, 1500);
})();
