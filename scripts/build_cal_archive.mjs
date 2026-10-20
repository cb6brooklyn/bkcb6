// Keeps data/cal-archive.json: every calendar event that has passed, so the CB6 calendar
// (assets/cb6-app-calendar.js) can show past months the way the app did.
// Sources, merged and de-duplicated:
//   data/cal-archive.json                 what was archived before
//   app/data/civic/cal/calendar-bk.json   the app's calendar file (events move here as they pass)
//   any extra calendar-bk.json shaped files passed on the command line (one-time seeds)
//   minutes/*.html + app/data/civic/minutes.json   every CB6 meeting with minutes, 2010 on
//   data/cb6-site-past-meetings.json      CB6 meetings listed on brooklyncb6.cityofnewyork.us
// Only events before today (New York) are written.
import fs from 'fs';
import path from 'path';

const ROOT = process.cwd();
const OUT = path.join(ROOT, 'data/cal-archive.json');
const CB6 = 'brooklyn-community-board-6';
const readJSON = (p, fb) => { try { return JSON.parse(fs.readFileSync(path.isAbsolute(p) ? p : path.join(ROOT, p), 'utf8')); } catch { return fb; } };
const TODAY = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
const norm = s => String(s || '').replace(/&#0?38;|&amp;/g, '&').replace(/\s+/g, ' ').trim().toLowerCase();

// Which CB6 body a meeting is, so the same meeting from two sources is kept once.
function body(label) {
  const s = norm(label);
  if (/full board|general board/.test(s)) return 'full';
  if (/landmark|land use/.test(s)) return 'luh';
  if (/business|licens/.test(s)) return 'bal';
  if (/transportation|public safety|public infrastructure/.test(s)) return 'tppi';
  if (/youth|human services|education|environmental sustainability/.test(s)) return 'hses';
  if (/economic|waterfront/.test(s)) return 'ewcd';
  if (/parks|recreation|environmental/.test(s)) return 'prep';
  if (/executive/.test(s)) return 'exec';
  if (/budget/.test(s)) return 'budget';
  return s;
}

const types = {};
const map = new Map();
const cb6Seen = new Map();
function add(e, prio) {
  if (!e || !/^\d{4}-\d{2}-\d{2}$/.test(e.d) || e.d >= TODAY || !e.l) return;
  if (e.ty === CB6) {
    const k = e.d + '|' + body(e.l);
    const old = cb6Seen.get(k);
    if (old && old.prio >= prio) return;
    if (old) map.delete(old.key);
    const key = 'cb6|' + k;
    cb6Seen.set(k, { prio, key });
    map.set(key, e);
    return;
  }
  const key = [e.d, norm(e.l), e.t || ''].join('|');
  if (!map.has(key)) map.set(key, e);
}
function addFile(f, prio) {
  const d = readJSON(f, null);
  if (!d) return 0;
  Object.assign(types, d.types || {});
  (d.events || []).forEach(e => add(e, prio));
  return (d.events || []).length;
}

addFile('data/cal-archive.json', 1);
addFile('app/data/civic/cal/calendar-bk.json', 1);
for (const f of process.argv.slice(2)) addFile(f, 1);

// CB6 meetings from the official site's event listings.
const site = readJSON('data/cb6-site-past-meetings.json', { events: [] });
for (const r of site.events || []) add({ d: r.d, l: r.l.replace(/&#0?38;/g, '&'), g: 'cb6', ty: CB6, k: 'board', t: r.t, loc: r.loc, h: r.h, lt: 'Details', cd: '306', org: 'Brooklyn Community Board 6' }, 2);

// Every meeting with minutes on bkcb6.app.
const NAMES = {
  'full-board': 'Full Board Meeting',
  'landmarks-land-use-housing': 'Landmarks, Land Use & Housing Committee',
  'business-affairs-licensing': 'Business Affairs & Licensing Committee',
  'transportation-parks-public-safety': 'Transportation, Parks & Public Safety Committee',
  'youth-human-services-education': 'Youth & Human Services / Education Committee',
  'economic-waterfront-cd-housing': 'Economic / Waterfront / Community Development & Housing Committee',
  'executive': 'Executive Committee',
  'parks-recreation-environmental': 'Parks / Recreation / Environmental Protection Committee'
};
const minutesDir = path.join(ROOT, 'minutes');
const records = readJSON('app/data/civic/minutes.json', []);
const recByDate = {};
for (const r of records) (recByDate[r.d] ||= []).push(r.b);
if (fs.existsSync(minutesDir)) for (const f of fs.readdirSync(minutesDir).sort()) {
  const m = /^(\d{4}-\d{2}-\d{2})-(.+)\.html$/.exec(f);
  if (!m) continue;
  let name = NAMES[m[2]];
  if (!name) { const bs = recByDate[m[1]] || []; name = bs.length === 1 ? bs[0] + ' Committee' : m[2].replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()); }
  add({ d: m[1], l: name, g: 'cb6', ty: CB6, k: 'board', h: 'https://bkcb6.app/minutes/' + f, lt: 'Minutes', cd: '306', org: 'Brooklyn Community Board 6' }, 3);
}

types[CB6] ||= { name: 'Brooklyn Community Board 6', icon: 'CB6_540.png' };
const events = [...map.values()].sort((a, b) => a.d < b.d ? -1 : a.d > b.d ? 1 : 0);
const s = JSON.stringify({ through: TODAY, types, events });
const before = fs.existsSync(OUT) ? fs.readFileSync(OUT, 'utf8') : '';
if (before !== s) fs.writeFileSync(OUT, s);
console.log(JSON.stringify({ today: TODAY, events: events.length, cb6: events.filter(e => e.ty === CB6).length, first: events[0] && events[0].d, changed: before !== s }));
