// Links the Spooky CB6 map (bkcb6.app/trickorstreets) to bkcb6.app/calendar.
// Writes:
//   data/trick-or-streets/calendar.json   for every street on the map and every Halloween event, the calendar
//                                         entry's deep link, flyer and organization logo, keyed by the map's event id
//   data/trick-or-streets/halloween.json  every Halloween event in CB6 on the calendar (October 2026 through Nov 1),
//                                         geocoded, in the map's event shape, so the map can draw it
//   data/trick-or-streets/geocache.json   geocoder results, so a location is only looked up once
// Reads calendar.html (EVENTS, ORG_ICONS, SUPPRESSED_LIVE) and data/calendar-events.json the same way
// scripts/build_app_calendar.mjs does.
import fs from 'fs';
import path from 'path';
import vm from 'vm';

const ROOT = process.cwd();
const html = fs.readFileSync(path.join(ROOT, 'calendar.html'), 'utf8');
const DIR = path.join(ROOT, 'data/trick-or-streets');
const OUT_LINKS = path.join(DIR, 'calendar.json');
const OUT_EVENTS = path.join(DIR, 'halloween.json');
const CACHE = path.join(DIR, 'geocache.json');
const SEASON_FROM = '2026-10-01', SEASON_TO = '2026-11-01';

function grab(name) {
  const marker = 'const ' + name + ' = ';
  const i = html.indexOf(marker);
  if (i < 0) throw new Error('calendar.html has no ' + marker);
  let j = i + marker.length, depth = 0, started = false, q = null;
  for (; j < html.length; j++) {
    const c = html[j], n = html[j + 1];
    if (q) {
      if (c === '\\') { j++; continue; }
      if (c === q) q = null;
      continue;
    }
    if (c === '/' && n === '/') { j = html.indexOf('\n', j); continue; }
    if (c === '/' && n === '*') { j = html.indexOf('*/', j) + 1; continue; }
    if (c === '"' || c === "'" || c === '`') { q = c; continue; }
    if (c === '{' || c === '[' || c === '(') { depth++; started = true; }
    else if (c === '}' || c === ']' || c === ')') { depth--; if (started && depth === 0) { j++; break; } }
  }
  return vm.runInNewContext('(' + html.slice(i + marker.length, j) + ')', {});
}

const EVENTS = grab('EVENTS');
const ORG_ICONS = grab('ORG_ICONS');
const SUPPRESSED_LIVE = grab('SUPPRESSED_LIVE');
const ent = s => String(s || '').replace(/&amp;/g, '&').replace(/&#39;|&rsquo;/g, '’').replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
const TYPE_NAMES = {};
for (const m of html.matchAll(/<option value="([^"]+)">([^<]+)<\/option>/g)) if (!(m[1] in TYPE_NAMES)) TYPE_NAMES[m[1]] = ent(m[2]).trim();
for (const m of html.matchAll(/<div class="leg" data-type="([^"]+)"[^>]*>(?:<img[^>]*>)?([^<]+)<\/div>/g)) if (!(m[1] in TYPE_NAMES)) TYPE_NAMES[m[1]] = ent(m[2]).trim();

// the live CB6 feed, merged exactly as calendar.html's loadLiveEvents does
const norm = s => (s || '').replace(/\s+/g, ' ').trim().toLowerCase();
const MANY_A_DAY = { has: t => ['unionhall', 'bellhouse', 'littlefield', 'powerhouse', 'prospect', 'bbp', 'dredgers', 'osh'].includes(t) || String(t).startsWith('park-') || String(t).startsWith('lib-') };
function mergeEntry(ev) {
  if (!ev || !ev.date) return;
  if (SUPPRESSED_LIVE.has(ev.date + '|' + (ev.label || '').replace(/\s+/g, ' ').trim())) return;
  if (typeof ev.label === 'string' && /^Early Voting\s+—/.test(ev.label)) return;
  if (!EVENTS[ev.date]) EVENTS[ev.date] = [];
  if (EVENTS[ev.date].some(e => e._hardcoded && norm(e.label) === norm(ev.label))) return;
  const idx = ev.type === 'community' ? -1 : EVENTS[ev.date].findIndex(e => e.type === ev.type && e._hardcoded);
  if (idx !== -1) EVENTS[ev.date][idx] = ev;
  else if (!EVENTS[ev.date].some(e => e.type === ev.type && !e._hardcoded && (!MANY_A_DAY.has(ev.type) || (e.label === ev.label && e.time === ev.time)))) EVENTS[ev.date].push(ev);
}
const readJSON = (p, fallback) => { try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return fallback; } };
(readJSON(path.join(ROOT, 'data/calendar-events.json'), { events: [] }).events || []).forEach(mergeEntry);

// the same slug the calendar's ?event= deep link uses
const slugify = s => String(s || '').toLowerCase().replace(/[‘’']/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 80);

function iconPath(type) {
  const f = ORG_ICONS[type] || (String(type).startsWith('park-') ? 'dpr.png' : String(type).startsWith('lib-') ? 'bpl.png' : null);
  if (!f) return null;
  const file = f.split('?')[0];
  if (fs.existsSync(path.join(ROOT, file))) return '/' + f;
  if (fs.existsSync(path.join(ROOT, 'app/data/civic/cal/icons', file))) return '/app/data/civic/cal/icons/' + f;
  return null;
}
function flyerPath(u) {
  if (!u) return null;
  const file = String(u).replace(/^https?:\/\/bkcb6\.app\//, '').split('?')[0];
  if (fs.existsSync(path.join(ROOT, file))) return '/' + file;
  return null;
}
function linkRow(date, e) {
  const row = { event: date + '-' + slugify(e.label), label: ent(e.label), type: e.type, org: TYPE_NAMES[e.type] || e.type };
  const fl = flyerPath(e.flyer); if (fl) row.flyer = fl;
  const ic = iconPath(e.type); if (ic) row.icon = ic;
  return row;
}

// ---------- 1. calendar entries that point at a street on the map ----------
const links = {};
for (const date of Object.keys(EVENTS).sort()) {
  for (const e of EVENTS[date]) {
    const m = String(e.href || '').match(/trickorstreets\/\?e=([A-Za-z0-9]+)/);
    if (!m || links[m[1]]) continue; // first calendar entry wins (the CB6 entry for a closure that crosses a board line)
    links[m[1]] = linkRow(date, e);
  }
}

// ---------- 2. Halloween events in CB6 ----------
const HALLOWEEN = /hallow|howl-o-ween|spooky|trick-or|pumpkin|haunt|costume|monster|creepy|ghost|witch|zombie|skeleton|day of the dead|d[ií]a de (los )?muertos|jack-o|boo bash/i;
const cb6 = readJSON(path.join(ROOT, 'data/cb6_boundary.geojson'), null);
const cb6Geom = cb6.type === 'FeatureCollection' ? cb6.features[0].geometry : (cb6.geometry || cb6);
function pip(lng, lat, g) {
  const rings = g.type === 'Polygon' ? [g.coordinates] : g.type === 'MultiPolygon' ? g.coordinates : [];
  for (const poly of rings) { const o = poly[0]; let ins = false; for (let i = 0, j = o.length - 1; i < o.length; j = i++) { const xi = o[i][0], yi = o[i][1], xj = o[j][0], yj = o[j][1]; if (((yi > lat) !== (yj > lat)) && (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi)) ins = !ins; } if (ins) return true; }
  return false;
}
// Places the geocoders do not know by name: what to look up instead (an address, or the corners a park sits between).
const PLACES = [
  { re: /^carroll park\b/i, q: ['Court Street and Carroll Street', 'Smith Street and President Street'] },
  { re: /^cobble hill park\b/i, q: ['Clinton Street and Congress Street', 'Henry Street and Congress Street'], dlat: 0.00035 },
  { re: /^thomas greene park\b/i, q: ['3 Avenue and Degraw Street', 'Nevins Street and Douglass Street'] },
  { re: /^nitehawk/i, q: ['188 Prospect Park West'] },
  { re: /^court street between pacific and union/i, q: ['Court Street and Baltic Street'] },
  { re: /^5th avenue\b.*park slope|^fifth avenue\b.*park slope/i, q: ['5 Avenue and 1 Street'] },
  { re: /^gowanus dredgers/i, q: ['165 2 Street'] },
  { re: /^old stone house/i, q: ['336 3 Street'] },
  { re: /^brooklyn public library, carroll gardens|^carroll gardens library/i, q: ['396 Clinton Street'] },
  { re: /^brooklyn public library, red hook|^red hook library/i, q: ['7 Wolcott Street'] },
  { re: /^brooklyn public library, park slope|^park slope library/i, q: ['431 6 Avenue'] },
];
const GEOCLIENT = 'https://api.nyc.gov/geoclient/v2/';
const GEOCLIENT_KEY = process.env.GEOCLIENT_KEY || 'b913bdfb9c47466589d0f08c99c75b21';
const cache = readJSON(CACHE, {});
let cacheDirty = false;
const clean = s => String(s || '').replace(/,?\s*(brooklyn|new york|ny|usa|united states|\d{5})\b.*$/i, '').replace(/\s+/g, ' ').trim();
async function geoclientOnce(kind, params) {
  const r = await fetch(GEOCLIENT + kind + '?' + new URLSearchParams({ ...params, borough: 'Brooklyn' }), { headers: { 'Ocp-Apim-Subscription-Key': GEOCLIENT_KEY } });
  if (!r.ok) throw new Error('geoclient ' + r.status);
  return (await r.json())[kind] || {};
}
async function geoclient(kind, params) {
  let d = await geoclientOnce(kind, params);
  // two streets that cross twice (a street with a median): try each compass direction until one resolves
  if (kind === 'intersection' && d.geosupportReturnCode === '02') for (const c of ['N', 'S', 'E', 'W']) { d = await geoclientOnce(kind, { ...params, compassDirection: c }); if (d.latitude) break; }
  if (!d.geosupportReturnCode) throw new Error('geoclient gave no answer'); // throttled or empty: try again next run rather than caching a miss
  return d.latitude && d.longitude ? { lat: +d.latitude, lng: +d.longitude, label: kind === 'address' ? d.houseNumber + ' ' + d.firstStreetNameNormalized : d.firstStreetNameNormalized + ' and ' + d.secondStreetNameNormalized } : null;
}
// One place name, address or corner -> a point: Geoclient for addresses and corners, geosearch for anything else.
async function geocode(text) {
  const key = clean(text);
  if (!key) return null;
  if (cache[key] !== undefined) return cache[key];
  let hit = null;
  try {
    let m = key.match(/^(.+?)\s+(?:&|and|at)\s+(.+)$/i);
    if (m) hit = await geoclient('intersection', { crossStreetOne: m[1], crossStreetTwo: m[2] });
    else if ((m = key.match(/^(\d+[A-Za-z]?)\s+(.+)$/))) hit = await geoclient('address', { houseNumber: m[1], street: m[2] });
    if (!hit) {
      const r = await fetch('https://geosearch.planninglabs.nyc/v2/search?size=1&text=' + encodeURIComponent(key + ', Brooklyn'));
      if (!r.ok) throw new Error('geosearch ' + r.status);
      const d = await r.json();
      const f = d.features && d.features[0];
      if (f && /brooklyn/i.test(f.properties.borough || f.properties.label || '')) hit = { lat: f.geometry.coordinates[1], lng: f.geometry.coordinates[0], label: f.properties.label };
    }
  } catch (err) { console.error('geocode failed, not cached:', key, err.message); return null; } // a transient failure is retried next run
  cache[key] = hit; cacheDirty = true;
  await new Promise(r => setTimeout(r, 150));
  return hit;
}
async function locate(location) {
  const loc = String(location || '').replace(/\s+/g, ' ').trim();
  if (!loc) return null;
  const place = PLACES.find(p => p.re.test(loc));
  let queries;
  if (place) queries = place.q;
  else {
    const parts = loc.split(/\s*[\u00b7|]\s*/).map(x => x.split(' (')[0].trim()).filter(Boolean);
    const addr = parts.find(x => /^\d+[A-Za-z]?\s+\S/.test(x)) || parts.find(x => /\s(?:&|and|at)\s/i.test(x)) || parts[0];
    queries = [addr];
  }
  const pts = [];
  for (const q of queries) { const h = await geocode(q); if (h) pts.push(h); }
  if (!pts.length) return null;
  const lat = pts.reduce((s, p) => s + p.lat, 0) / pts.length + (place && place.dlat || 0);
  const lng = pts.reduce((s, p) => s + p.lng, 0) / pts.length + (place && place.dlng || 0);
  return { lat: +lat.toFixed(6), lng: +lng.toFixed(6) };
}
function timeText(e) {
  const t = e.time || '';
  const txt = [e.desc, e.time, e.label].filter(Boolean).join(' ');
  let m = txt.match(/\bEnds?\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*([AaPp])\.?[Mm]\.?/);
  if (!m) m = txt.match(/\d{1,2}(?::\d{2})?\s*(?:[AaPp]\.?[Mm]\.?)?\s*(?:–|—|-|to)\s*(\d{1,2})(?::(\d{2}))?\s*([AaPp])\.?[Mm]\.?/);
  const end = m ? `${parseInt(m[1], 10)}:${m[2] || '00'} ${m[3].toUpperCase()}M` : null;
  const mins = x => { const k = /^(\d{1,2})(?::(\d{2}))?\s*([AP])M$/i.exec(x || ''); if (!k) return null; return (+k[1] % 12 + (/p/i.test(k[3]) ? 12 : 0)) * 60 + (+(k[2] || 0)); };
  if (t && end && end !== t && mins(end) !== null && mins(t) !== null && mins(end) > mins(t)) return t + ' to ' + end;
  return t || 'See the calendar for times';
}

const items = [], skipped = [];
for (const date of Object.keys(EVENTS).sort()) {
  if (date < SEASON_FROM || date > SEASON_TO) continue;
  for (const e of EVENTS[date]) {
    if (!e || !e.label || e.type === 'spookycb6') continue;
    if (/trickorstreets\/\?e=/.test(e.href || '')) continue; // already a street on the map
    if (!HALLOWEEN.test(ent(e.label))) continue;
    const pt = await locate(e.location);
    if (!pt) { skipped.push([date, ent(e.label), e.location, 'no geocode']); continue; }
    if (!pip(pt.lng, pt.lat, cb6Geom)) { skipped.push([date, ent(e.label), e.location, 'outside CB6']); continue; }
    const id = 'c' + date.replace(/-/g, '') + '-' + slugify(e.label).slice(0, 40);
    items.push({ src: 'cal', id, name: ent(e.label), kind: 'Halloween event', org: TYPE_NAMES[e.type] && e.type !== 'community' ? TYPE_NAMES[e.type] : '', date, time: timeText(e), where: ent(e.location || ''), cds: [6], lat: pt.lat, lng: pt.lng, lines: [] });
    links[id] = linkRow(date, e);
  }
}

fs.mkdirSync(DIR, { recursive: true });
fs.writeFileSync(OUT_LINKS, JSON.stringify(links, null, 1) + '\n');
fs.writeFileSync(OUT_EVENTS, JSON.stringify({ built: new Date().toISOString().slice(0, 10), items }, null, 1) + '\n');
if (cacheDirty) fs.writeFileSync(CACHE, JSON.stringify(cache, null, 1) + '\n');
console.log(JSON.stringify({ linked: Object.keys(links).length, halloween: items.length, flyers: Object.values(links).filter(r => r.flyer).length, skipped }, null, 1));
