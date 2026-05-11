/* CB6 Beyond shared script */
(function(){
  document.addEventListener('click', function(e){
    var a = e.target && e.target.closest && e.target.closest('a');
    if (!a) return;
    var href = a.getAttribute('href') || '';
    if (!href) return;
    if (/^(mailto:|tel:|sms:)/i.test(href)) return;
    try {
      var u = new URL(href, window.location.href);
      if (u.origin === window.location.origin) return;
    } catch(_) { return; }
    e.preventDefault();
    if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.Browser) {
      window.Capacitor.Plugins.Browser.open({ url: a.href });
    } else {
      window.open(a.href, '_blank', 'noopener');
    }
  });
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function(){
      navigator.serviceWorker.register('/sw.js').catch(function(){});
    });
  }
})();
