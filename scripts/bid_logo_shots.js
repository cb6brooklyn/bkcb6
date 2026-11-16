// For each business in the logo queue that has a website: open the site in a browser, find the logo on the page
// (in the header or marked as the logo) and screenshot it; with no logo on the page, keep the site's own share image
// (og:image, usually a storefront or dish photo). Writes <out>/<slug>.png and <out>/results.json.
// Run: node scripts/bid_logo_shots.js <queue.json> <outdir>
const {chromium} = require('playwright');
const fs = require('fs'), path = require('path');
const [, , QF, OUT] = process.argv;
const Q = JSON.parse(fs.readFileSync(QF, 'utf8')).filter(q => q[3]);
fs.mkdirSync(OUT, {recursive: true});
const RES = fs.existsSync(path.join(OUT, 'results.json')) ? JSON.parse(fs.readFileSync(path.join(OUT, 'results.json'))) : {};
const SKIP = /facebook|instagram|yelp|google|linktr|toasttab|grubhub|doordash|seamless|ubereats|bkcb6\.app|nyc\.gov|ny\.gov/i;
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({viewport: {width: 1280, height: 900}, deviceScaleFactor: 2, locale: 'en-US',
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'});
  const todo = Q.filter(q => !RES[q[0]] && !SKIP.test(q[3]));
  let i = 0;
  async function one(q) {
    const [slug, name, addr, url0] = q;
    const url = /^https?:/.test(url0) ? url0 : 'https://' + url0;
    const p = await ctx.newPage();
    try {
      await p.goto(url, {waitUntil: 'domcontentloaded', timeout: 30000});
      await p.waitForTimeout(2500);
      const title = await p.title();
      if (/parked|for sale|domain|wix\.com|server is down|just a moment|attention required|not found|404|suspended|coming soon|godaddy|squarespace - claim/i.test(title + ' ' + (await p.evaluate(() => document.body ? document.body.innerText.slice(0, 400) : '')))) {
        RES[slug] = {kind: 'none', why: 'the site is parked, down or behind a bot check', url}; await p.close(); if (++i % 10 === 0) fs.writeFileSync(path.join(OUT, 'results.json'), JSON.stringify(RES, null, 0)); return }
      const box = await p.evaluate(() => {
        const bad = e => !!e.closest('[href*="cart" i],[href*="bag" i],[href*="account" i],[href*="search" i],[class*="cart" i],[class*="menu-toggle" i],[aria-label*="cart" i],[aria-label*="menu" i],[class*="accessib" i],[id*="accessib" i],[class*="userway" i]');
        const vis = e => { if (bad(e)) return null; if (e.tagName === 'svg' && e.getBoundingClientRect().width < 60) return null; const r = e.getBoundingClientRect(), s = getComputedStyle(e);
          return r.width >= 36 && r.height >= 18 && r.top < 450 && r.top > -5 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity !== 0 ? r : null };
        const sels = ['[class*="logo" i] img', '[id*="logo" i] img', 'img[class*="logo" i]', 'img[id*="logo" i]', 'img[alt*="logo" i]', 'img[src*="logo" i]',
          '[class*="logo" i] svg', 'svg[class*="logo" i]', '.navbar-brand img', '.site-title img', '.custom-logo', 'header a[href="/"] img', 'header a[href="/"] svg',
          'a[href="/"] img', 'header img', 'nav img', 'header svg'];
        for (const s of sels) for (const e of document.querySelectorAll(s)) { const r = vis(e); if (r && r.width < 900) return {x: r.left, y: r.top, w: r.width, h: r.height, how: s} }
        // a text logo: the site title in the header
        for (const s of ['[class*="logo" i]', '.site-title', '.navbar-brand', 'header h1']) for (const e of document.querySelectorAll(s)) { const r = vis(e); if (r && r.width < 700 && r.height < 220 && e.textContent.trim().length > 1) return {x: r.left, y: r.top, w: r.width, h: r.height, how: s} }
        return null });
      if (box) {
        const pad = 10;
        await p.screenshot({path: path.join(OUT, slug + '.png'), clip: {x: Math.max(0, box.x - pad), y: Math.max(0, box.y - pad), width: box.w + 2 * pad, height: box.h + 2 * pad}});
        RES[slug] = {kind: 'logo', how: box.how, url};
      } else {
        const og = await p.evaluate(() => { const m = document.querySelector('meta[property="og:image"], meta[name="og:image"], meta[name="twitter:image"]'); return m ? m.content : '' });
        if (og) {
          const r = await ctx.request.get(new URL(og, url).href, {timeout: 20000});
          if (r.ok()) { fs.writeFileSync(path.join(OUT, slug + '.og'), await r.body()); RES[slug] = {kind: 'photo', how: 'og:image', url} }
          else RES[slug] = {kind: 'none', why: 'share image would not load', url};
        } else RES[slug] = {kind: 'none', why: 'no logo or share image on the page', url};
      }
    } catch (e) { RES[slug] = {kind: 'none', why: String(e.message).slice(0, 80), url} }
    await p.close();
    if (++i % 10 === 0) fs.writeFileSync(path.join(OUT, 'results.json'), JSON.stringify(RES, null, 0));
  }
  const N = 6; const queue = todo.slice();
  await Promise.all(Array.from({length: N}, async () => { while (queue.length) await one(queue.shift()) }));
  fs.writeFileSync(path.join(OUT, 'results.json'), JSON.stringify(RES, null, 0));
  await b.close();
  const c = {}; for (const k in RES) c[RES[k].kind] = (c[RES[k].kind] || 0) + 1; console.log('done', todo.length, JSON.stringify(c));
})();
