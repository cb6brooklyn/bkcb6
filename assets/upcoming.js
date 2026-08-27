/* Upcoming event banner.
   Any profile page can opt in by carrying an element with data-upcoming set to
   its calendar type, e.g. <div data-upcoming="barkslope"></div>. The banner
   renders only when that type has something coming up, so the page stays clean
   the rest of the year. */
(function () {
  'use strict';

  var CSS_ID = 'upcoming-css';
  function css() {
    if (document.getElementById(CSS_ID)) return;
    var s = document.createElement('style');
    s.id = CSS_ID;
    s.textContent =
      '.upcoming{display:block;background:#fff;border:2px solid #f47920;border-radius:12px;'
      + 'padding:12px 14px;margin:0 0 14px;text-decoration:none;color:#0d1b4b}'
      + '.upcoming:hover{background:#fff7ed}'
      + '.upcoming .ul{font-family:"DM Mono",monospace;font-size:.57rem;font-weight:700;'
      + 'text-transform:uppercase;letter-spacing:.11em;color:#f47920;display:block;margin-bottom:5px}'
      + '.upcoming .un{font-size:.95rem;font-weight:800;line-height:1.3;display:block}'
      + '.upcoming .ud{font-family:"DM Mono",monospace;font-size:.63rem;color:#6b6760;'
      + 'display:block;margin-top:5px;line-height:1.55}'
      + '.upcoming .ug{font-size:.72rem;font-weight:800;color:#f47920;display:block;margin-top:7px}'
      + '.upcoming + .upcoming{margin-top:-6px}'
      + '.upflyer{display:block;margin:12px 0 4px;text-decoration:none}'
      + '.upflyer .fl{font-family:"DM Mono",monospace;font-size:.66rem;font-weight:700;'
      + 'text-transform:uppercase;letter-spacing:.1em;color:#0d1b4b;display:block;margin-bottom:7px}'
      + '.upflyer img{display:block;width:100%;max-width:420px;height:auto;border-radius:10px;'
      + 'border:1.5px solid #e5e2db}'
      + '.upflyer:hover img{border-color:#f47920}';
    document.head.appendChild(s);
  }

  var MONTH = ['January','February','March','April','May','June','July',
               'August','September','October','November','December'];
  var DAYNM = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];

  function when(iso, time) {
    var p = String(iso).split('-');
    // build in local time; new Date('2026-09-19') is parsed as UTC and can
    // land on the previous evening once it is rendered
    var d = new Date(+p[0], +p[1] - 1, +p[2]);
    var today = new Date();
    today = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    var days = Math.round((d - today) / 86400000);
    var label = DAYNM[d.getDay()] + ', ' + MONTH[d.getMonth()] + ' ' + d.getDate();
    if (days === 0) label = 'Today';
    else if (days === 1) label = 'Tomorrow';
    if (time) label += ' \u00b7 ' + time;
    if (days > 1 && days <= 30) label += ' \u00b7 in ' + days + ' days';
    return label;
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
  }

  var slots = [].slice.call(document.querySelectorAll('[data-upcoming]'));
  if (!slots.length) return;

  fetch('/data/business-events.json').then(function (r) {
    if (!r.ok) throw new Error(r.status);
    return r.json();
  }).then(function (d) {
    var owners = (d && d.owners) || {};
    slots.forEach(function (slot) {
      var key = slot.getAttribute('data-upcoming');
      var o = owners[key];
      if (!o || !o.events || !o.events.length) return;
      css();
      var n = parseInt(slot.getAttribute('data-upcoming-max') || '1', 10);
      o.events.slice(0, n).forEach(function (e) {
        var a = document.createElement('a');
        a.className = 'upcoming';
        a.href = e.url;
        a.innerHTML =
          '<span class="ul">Upcoming</span>'
          + '<span class="un">' + esc(e.label) + '</span>'
          + '<span class="ud">' + esc(when(e.date, e.time))
          + (e.location ? ' &middot; ' + esc(e.location) : '') + '</span>'
          + '<span class="ug">See the event &rarr;</span>';
        slot.appendChild(a);
      });
    });
    placeFlyers(owners);
  }).catch(function () { /* no banner rather than a broken one */ });

  /* The flyer belongs under the business card inside the lot record, which the
     citywide search renders after its own fetch. That card is not ours to
     change, so watch for it and insert once it appears. */
  function placeFlyers(owners) {
    var hosts = [].slice.call(document.querySelectorAll('[data-flyer-after-biz]'));
    if (!hosts.length) return;
    hosts.forEach(function (host) {
      var o = owners[host.getAttribute('data-flyer-after-biz')];
      if (!o || !o.events) return;
      var ev = null;
      for (var i = 0; i < o.events.length; i++) {
        if (o.events[i].flyer) { ev = o.events[i]; break; }
      }
      if (!ev) return;
      var tries = 0;
      (function wait() {
        var card = bizCard();
        if (card) { insert(card, ev); return; }
        if (tries++ > 100) return;
        setTimeout(wait, 150);
      })();
    });
  }

  function bizCard() {
    var res = document.getElementById('citywide-borough-address-search-result');
    if (!res || res.hidden) return null;
    var divs = res.querySelectorAll('div'), best = null;
    for (var i = 0; i < divs.length; i++) {
      var t = (divs[i].firstChild && divs[i].firstChild.textContent || '').trim();
      if (!/^(business(es)?\s+in\s+this\s+building|in\s+this\s+building)$/i.test(t)) continue;
      // an outer wrapper matches this text too, so take the tightest one:
      // the block that holds only the heading and the business rows
      var block = divs[i].parentNode;
      if (!best || block.children.length < best.children.length) best = block;
    }
    return best;
  }

  function insert(block, ev) {
    if (document.querySelector('.upflyer')) return;
    css();
    var a = document.createElement('a');
    a.className = 'upflyer';
    a.href = ev.url;
    a.innerHTML = '<span class="fl">' + esc(ev.label) + '</span>'
      + '<img src="' + esc(ev.flyer) + '" alt="Flyer for ' + esc(ev.label) + '" loading="lazy">';
    // straight after the business block, not at the end of the whole card
    block.parentNode.insertBefore(a, block.nextSibling);
  }
})();
