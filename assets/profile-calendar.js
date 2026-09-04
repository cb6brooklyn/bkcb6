/* Month calendar for profile pages.
   Exposes window.renderProfileCalendar(host, rows, opts) where rows is
   [{key:'YYYY-MM-DD', ev:{...}}] and opts carries the subject's name and the
   calendar link to fall back to. The caller owns the data; this file only
   draws it, so the organization pages and the culture pages share one grid. */
(function(){
  var MON = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  var DOWS = ['S','M','T','W','T','F','S'];

  function esc(s){
    return String(s == null ? '' : s)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
  function pad(n){ return String(n).padStart(2,'0'); }
  function keyOf(d){ return d.getFullYear() + '-' + pad(d.getMonth()+1) + '-' + pad(d.getDate()); }
  function todayKey(){ return keyOf(new Date()); }

  function dayList(rows, key, opts){
    var day = rows.filter(function(r){ return r.key === key; });
    if(!day.length) return '';
    var d = new Date(key + 'T00:00:00');
    var head = '<div class="pcal-hint">' + esc(MON[d.getMonth()]) + ' ' + d.getDate() + ', ' + d.getFullYear() + '</div>';
    return head + '<ul class="evl">' + day.map(function(r){
      var ev = r.ev;
      var meta = [];
      if(ev.time) meta.push('<span>' + esc(ev.time) + '</span>');
      if(ev.location) meta.push('<span>' + esc(ev.location) + '</span>');
      return '<li class="evc" style="padding:9px 0">' +
        '<div class="evb"><div class="evt">' + esc(ev.label) + '</div>' +
        (meta.length ? '<div class="evm">' + meta.join('') + '</div>' : '') +
        (ev.href ? '<div class="eva"><a href="' + esc(ev.href) + '" target="_blank" rel="noopener noreferrer">' +
                   esc(ev.linkText || 'Full details') + ' \u2197</a></div>' : '') +
        '</div></li>';
    }).join('') + '</ul>';
  }

  window.renderProfileCalendar = function(host, rows, opts){
    if(!host) return;
    opts = opts || {};
    rows = (rows || []).slice().sort(function(a,b){ return a.key < b.key ? -1 : a.key > b.key ? 1 : 0; });

    var byKey = {};
    rows.forEach(function(r){ (byKey[r.key] = byKey[r.key] || []).push(r); });
    var keys = Object.keys(byKey).sort();
    var tKey = todayKey();

    // Open on the month of the next event, or the current month when there is
    // nothing ahead, so the useful month is the one on screen first.
    var anchor = keys.filter(function(k){ return k >= tKey; })[0] || keys[keys.length-1] || tKey;
    var cur = new Date(anchor + 'T00:00:00');
    cur = new Date(cur.getFullYear(), cur.getMonth(), 1);
    var first = keys.length ? new Date(keys[0] + 'T00:00:00') : new Date();
    var last  = keys.length ? new Date(keys[keys.length-1] + 'T00:00:00') : new Date();
    var minMo = new Date(Math.min(first, new Date()).valueOf());
    minMo = new Date(minMo.getFullYear(), minMo.getMonth(), 1);
    var maxMo = new Date(Math.max(last, new Date()).valueOf());
    maxMo = new Date(maxMo.getFullYear(), maxMo.getMonth(), 1);
    var selected = null;

    function draw(){
      var y = cur.getFullYear(), m = cur.getMonth();
      var start = new Date(y, m, 1).getDay();
      var days = new Date(y, m+1, 0).getDate();
      var prevDays = new Date(y, m, 0).getDate();
      var cells = '';
      for(var i = start - 1; i >= 0; i--) cells += '<span class="pcal-d pad">' + (prevDays - i) + '</span>';
      for(var d = 1; d <= days; d++){
        var k = y + '-' + pad(m+1) + '-' + pad(d);
        var has = !!byKey[k];
        var cls = 'pcal-d' + (has ? ' has' : '') + (k === tKey ? ' today' : '') + (k === selected ? ' sel' : '');
        cells += has
          ? '<button type="button" class="' + cls + '" data-k="' + k + '" aria-label="' +
            byKey[k].length + ' on ' + MON[m] + ' ' + d + '">' + d + '<span class="pcal-dot"></span></button>'
          : '<span class="' + cls + '">' + d + '</span>';
      }
      var tail = (start + days) % 7;
      if(tail) for(var t = 1; t <= 7 - tail; t++) cells += '<span class="pcal-d pad">' + t + '</span>';

      var atMin = cur <= minMo, atMax = cur >= maxMo;
      host.innerHTML = '<div class="pcal">' +
        '<div class="pcal-bar">' +
          '<button type="button" class="pcal-nav" data-mo="-1"' + (atMin ? ' disabled' : '') + ' aria-label="Previous month">\u2039</button>' +
          '<div class="pcal-mo">' + MON[m] + ' ' + y + '</div>' +
          '<button type="button" class="pcal-nav" data-mo="1"' + (atMax ? ' disabled' : '') + ' aria-label="Next month">\u203a</button>' +
        '</div>' +
        '<div class="pcal-dow">' + DOWS.map(function(x){ return '<span>' + x + '</span>'; }).join('') + '</div>' +
        '<div class="pcal-grid">' + cells + '</div>' +
        (selected
          ? '<div class="pcal-out">' + dayList(rows, selected, opts) + '</div>'
          : (rows.length
              ? '<div class="pcal-out"><div class="pcal-hint">Tap a highlighted day to see what is on.</div></div>'
              : '<div class="pcal-none">Nothing for ' + esc(opts.name || 'this place') +
                ' is on the community calendar yet. <a href="' + esc(opts.calendarHref || '/calendar.html') +
                '">See the full calendar</a>.</div>')) +
        '</div>';

      Array.prototype.forEach.call(host.querySelectorAll('.pcal-nav'), function(b){
        b.addEventListener('click', function(){
          if(b.disabled) return;
          cur = new Date(cur.getFullYear(), cur.getMonth() + Number(b.dataset.mo), 1);
          selected = null;
          draw();
        });
      });
      Array.prototype.forEach.call(host.querySelectorAll('.pcal-d.has'), function(b){
        b.addEventListener('click', function(){
          selected = (selected === b.dataset.k) ? null : b.dataset.k;
          draw();
        });
      });
    }
    draw();
  };
})();
