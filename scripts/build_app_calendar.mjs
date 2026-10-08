// Builds the BKCB6 iOS app's calendar files from the same sources bkcb6.app/calendar reads:
//   calendar.html (EVENTS, TYPES, ORG_ICONS, SUPPRESSED_LIVE, the type names in its <option> list)
//   data/calendar-events.json            (CB6 site feed, refreshed daily)
//   data/civic-calendar/council.json     (NYC Council, refreshed daily)
//   data/civic-calendar/hearings.json    (City Record hearings, refreshed daily)
//   data/civic-calendar/brooklyn-cbs.json (Brooklyn community boards, refreshed daily)
// Writes app/data/civic/cal/calendar-bk.json and calendar-city.json, copies any new flyers and icons into
// the pack, and updates app/manifest.json so installed apps download the new files.
// Only events from today (New York) onward are written.
import fs from 'fs';
import path from 'path';
import vm from 'vm';
import crypto from 'crypto';

const ROOT = process.cwd();
const PACK = path.join(ROOT, 'app/data');
const CAL = path.join(PACK, 'civic/cal');
const TYPEMAP_FILE = path.join(ROOT, 'scripts/app-calendar-types.json');
const html = fs.readFileSync(path.join(ROOT, 'calendar.html'), 'utf8');

// ---------- pull a top-level const out of calendar.html and evaluate it ----------
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
const TYPES = grab('TYPES');
const ORG_ICONS = grab('ORG_ICONS');
const SUPPRESSED_LIVE = grab('SUPPRESSED_LIVE');

const ent = s => String(s || '').replace(/&amp;/g, '&').replace(/&#39;|&rsquo;/g, '’').replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
const TYPE_NAMES = {};
for (const m of html.matchAll(/<option value="([^"]+)">([^<]+)<\/option>/g)) if (!(m[1] in TYPE_NAMES)) TYPE_NAMES[m[1]] = ent(m[2]).trim();
for (const m of html.matchAll(/<div class="leg" data-type="([^"]+)"[^>]*>(?:<img[^>]*>)?([^<]+)<\/div>/g)) if (!(m[1] in TYPE_NAMES)) TYPE_NAMES[m[1]] = ent(m[2]).trim();

// ---------- merge the live CB6 feed exactly as calendar.html's loadLiveEvents does ----------
const norm = s => (s || '').replace(/\s+/g, ' ').trim().toLowerCase();
function mergeEntry(ev) {
  if (!ev || !ev.date) return;
  if (SUPPRESSED_LIVE.has(ev.date + '|' + (ev.label || '').replace(/\s+/g, ' ').trim())) return;
  if (typeof ev.label === 'string' && /^Early Voting\s+—/.test(ev.label)) return;
  if (!EVENTS[ev.date]) EVENTS[ev.date] = [];
  if (EVENTS[ev.date].some(e => e._hardcoded && norm(e.label) === norm(ev.label))) return;
  const idx = ev.type === "community" ? -1 : EVENTS[ev.date].findIndex(e => e.type === ev.type && e._hardcoded); // same rule as calendar.html
  if (idx !== -1) EVENTS[ev.date][idx] = ev;
  else if (!EVENTS[ev.date].some(e => e.type === ev.type && !e._hardcoded)) EVENTS[ev.date].push(ev);
}
const readJSON = (p, fallback) => { try { return JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8')); } catch { return fallback; } };
const live = readJSON('data/calendar-events.json', { events: [] });
(live.events || []).forEach(mergeEntry);

// ---------- dates ----------
const nyDate = d => new Intl.DateTimeFormat('en-CA', { timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit' }).format(d);
const TODAY = nyDate(new Date());
const LAST = nyDate(new Date(Date.now() + 400 * 86400000));
const inWindow = d => /^\d{4}-\d{2}-\d{2}$/.test(d) && d >= TODAY && d <= LAST;

// End time when the event states one: "Ends 8:00 PM", "6:00–8:00 PM", "2:00 to 4:00 pm".
function endTime(ev) {
  const txt = [ev.desc, ev.time, ev.label].filter(Boolean).join(' ');
  let m = txt.match(/\bEnds?\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*([AaPp])\.?[Mm]\.?/);
  if (!m) m = txt.match(/\d{1,2}(?::\d{2})?\s*(?:[AaPp]\.?[Mm]\.?)?\s*(?:–|—|-|to)\s*(\d{1,2})(?::(\d{2}))?\s*([AaPp])\.?[Mm]\.?/);
  if (!m) return null;
  return `${parseInt(m[1], 10)}:${m[2] || '00'} ${m[3].toUpperCase()}M`;
}

// ---------- type key -> app type slug, kept stable across runs ----------
const slug = s => String(s || '').toLowerCase().replace(/[‘’']/g, '').replace(/&/g, 'and').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
const oldBk = readJSON('app/data/civic/cal/calendar-bk.json', { types: {}, events: [] });
const oldCity = readJSON('app/data/civic/cal/calendar-city.json', { types: {}, events: [] });
const typeMap = readJSON('scripts/app-calendar-types.json', {});
// Learn the mapping the existing app file already uses, by matching events on date and label.
// Generic site types (community, principles) cover many organizations, so they are resolved per event.
const GENERIC = new Set(['community', 'principles', 'board', 'committee']);
const oldIndex = new Map(oldBk.events.map(e => [e.d + '|' + norm(ent(e.l)), e]));
const votes = {};
for (const [d, list] of Object.entries(EVENTS)) for (const e of list || []) {
  if (!e || !e.label || GENERIC.has(e.type) || typeMap[e.type]) continue;
  const o = oldIndex.get(d + '|' + norm(ent(e.label)));
  if (!o || o.g !== 'cb6') continue;
  const v = (votes[e.type] ||= {}); const k = o.ty + '\u0000' + o.org; v[k] = (v[k] || 0) + 1;
}
for (const [t, v] of Object.entries(votes)) {
  const [ty, org] = Object.entries(v).sort((a, b) => b[1] - a[1])[0][0].split('\u0000');
  typeMap[t] = { ty, org };
}
const classify = vm.runInNewContext('(' + (() => {
  const i = html.indexOf('function classifyICSEvent(');
  let j = html.indexOf('{', i), depth = 0;
  for (; j < html.length; j++) { if (html[j] === '{') depth++; else if (html[j] === '}') { depth--; if (depth === 0) { j++; break; } } }
  return html.slice(i, j);
})() + ')', {});
const CB6 = { ty: 'brooklyn-community-board-6', org: 'Brooklyn Community Board 6' };
const COMMUNITY = { ty: 'community-event', org: 'Community event' };
// One event's organization: the app's existing assignment when this event was already in it, otherwise the site type.
function orgFor(d, e) {
  if (e.type === 'board' || e.type === 'committee') return { ...CB6, k: e.type };
  let t = e.type;
  if (GENERIC.has(t)) {
    const k = classify(e.label, '', [e.href, e.location].filter(Boolean).join(' '));
    if (k && !['board', 'committee', 'ulurp', 'budget', 'altside', 'community'].includes(k)) t = k;
  }
  const o = oldIndex.get(d + '|' + norm(ent(e.label)));
  if (o && o.g === 'cb6' && o.ty) return { ty: o.ty, org: o.org, k: t };
  if (t === 'community') return { ...COMMUNITY, k: t };
  return { ...typeFor(t), k: t };
}
function typeFor(t) {
  if (t === 'board' || t === 'committee') return CB6;
  if (!typeMap[t]) {
    const name = TYPE_NAMES[t] || (t.charAt(0).toUpperCase() + t.slice(1));
    typeMap[t] = { ty: slug(name) || t, org: name };
  }
  return typeMap[t];
}

// ---------- files the pack carries ----------
const copied = [];
function packFile(dirRel, file) {
  if (!file || /[\/\\]/.test(file)) return false;
  const dest = path.join(PACK, dirRel, file);
  if (fs.existsSync(dest)) return true;
  const src = path.join(ROOT, file);
  if (!fs.existsSync(src)) return false;
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
  copied.push(dirRel + '/' + file);
  return true;
}
const flyerName = u => {
  if (!u) return null;
  const m = String(u).match(/^(?:https?:\/\/(?:www\.)?bkcb6\.app\/)?([^\/?#]+\.(?:jpg|jpeg|png|webp))$/i);
  return m ? m[1] : null;
};

// ---------- CB6 calendar events ----------
const types = { ...oldBk.types };
const out = [];
// Calendar events tagged with other boards (cds) belong to those boards: BKCB's citywide file only, not CB6's.
const elsewhere = [];
for (const [d, list] of Object.entries(EVENTS)) {
  if (!inWindow(d)) continue;
  for (const e of list || []) {
    if (!e || !e.label) continue;
    const tm = orgFor(d, e);
    const row = { d, l: ent(e.label), g: 'cb6', ty: tm.ty, k: tm.k };
    if (e.time) row.t = e.time;
    const end = endTime(e); if (end) row.e = end;
    if (e.location) row.loc = ent(e.location);
    if (e.desc) row.desc = ent(e.desc);
    if (e.href) { row.h = e.href; row.lt = 'Details'; }
    const fl = flyerName(e.flyer);
    if (fl && packFile('civic/cal/flyers', fl)) row.f = fl;
    if (tm.ty === CB6.ty) row.cd = '306';
    row.org = tm.org;
    if (Array.isArray(e.cds) && e.cds.length && !e.cds.includes('306')) {
      row.cd = String(e.cds[0]);
      if (e.cds.length > 1) row.cds = e.cds.map(String);
      // A community event in another board's district is not that board's meeting: its group is "community", not "cb6".
      row.g = 'community';
      elsewhere.push(row);
    } else out.push(row);
    if (!types[tm.ty]) {
      const t = { name: tm.org };
      const icon = ORG_ICONS[e.type];
      if (icon && packFile('civic/cal/icons', icon)) t.icon = icon;
      if (TYPES[e.type] && TYPES[e.type].bg) t.bg = TYPES[e.type].bg;
      types[tm.ty] = t;
    } else if (!types[tm.ty].icon && ORG_ICONS[e.type] && packFile('civic/cal/icons', ORG_ICONS[e.type])) {
      types[tm.ty].icon = ORG_ICONS[e.type];
    }
  }
}

// ---------- NYC Council and City Record hearings ----------
const civic = [];
const council = readJSON('data/civic-calendar/council.json', { events: {} });
for (const [d, list] of Object.entries(council.events || {})) {
  if (!inWindow(d)) continue;
  for (const e of list || []) {
    if (!e || !e.label) continue;
    const row = { d, l: e.label, g: 'council', ty: 'new-york-city-council' };
    if (e.time) row.t = e.time;
    if (e.location) row.loc = e.location.replace(/\s+/g, ' ').trim();
    if (e.href) { row.h = e.href; row.lt = 'Details'; }
    row.org = 'New York City Council';
    civic.push(row);
  }
}
const hearings = readJSON('data/civic-calendar/hearings.json', { events: {} });
for (const [d, list] of Object.entries(hearings.events || {})) {
  if (!inWindow(d)) continue;
  for (const e of list || []) {
    if (!e || !e.label) continue;
    const row = { d, l: e.label, g: 'hearing', ty: 'public-hearing' };
    if (e.time) row.t = e.time;
    if (e.agency) row.loc = e.agency;
    if (e.href) { row.h = e.href; row.lt = 'Details'; }
    row.org = 'Public hearing';
    civic.push(row);
  }
}
if (!types['new-york-city-council']) types['new-york-city-council'] = { name: 'New York City Council' };
if (!types['community-event']) types['community-event'] = { name: 'Community event' };
if (!types['public-hearing']) types['public-hearing'] = { name: 'Public hearing' };

const order = (a, b) => (a.d + (a.g === 'cb6' ? '0' : '1')).localeCompare(b.d + (b.g === 'cb6' ? '0' : '1'));
const bk = [...out, ...civic].sort(order);

// ---------- citywide file: the same CB6, Council and hearing events, plus every community board ----------
const cityTypes = { ...oldCity.types };
for (const [k, v] of Object.entries(types)) {
  if (!cityTypes[k]) cityTypes[k] = v;
  else if (v.icon && !cityTypes[k].icon) cityTypes[k].icon = v.icon;
}
const boards = [];
const bkcbs = readJSON('data/civic-calendar/brooklyn-cbs.json', { boards: {} });
const bkBoardsHaveData = Object.keys(bkcbs.boards || {}).length > 0;
for (const b of Object.values(bkcbs.boards || {})) {
  if (!b || b.cb === 6) continue;
  const cd = String(300 + Number(b.cb));
  const org = 'Brooklyn Community Board ' + b.cb;
  for (const e of b.events || []) {
    if (!e || !e.label || !inWindow(e.date)) continue;
    const standing = e.source === 'standing';
    const row = { d: e.date, l: e.label, g: 'board', ty: standing ? 'cbmeeting' : slug(org) };
    if (e.time) row.t = e.time;
    if (e.location) row.loc = e.location;
    if (e.href) { row.h = e.href; row.lt = standing ? 'Board website' : 'Details'; }
    row.cd = cd; row.org = org;
    boards.push(row);
    if (!standing && !cityTypes[row.ty]) cityTypes[row.ty] = { name: org };
  }
}
// Boards in the other four boroughs have no daily source here yet: keep their dated entries that are still ahead.
for (const e of oldCity.events || []) {
  if (e.g !== 'board' || !inWindow(e.d)) continue;
  if (bkBoardsHaveData && String(e.cd || '').startsWith('3')) continue;
  boards.push(e);
}
const city = [...bk, ...boards, ...elsewhere].sort(order);

// ---------- write only when something changed ----------
const write = (rel, obj) => {
  const p = path.join(PACK, rel);
  const s = JSON.stringify(obj);
  if (fs.existsSync(p) && fs.readFileSync(p, 'utf8') === s) return false;
  fs.writeFileSync(p, s);
  return true;
};
const changed = [];
if (write('civic/cal/calendar-bk.json', { types, events: bk })) changed.push('civic/cal/calendar-bk.json');
if (write('civic/cal/calendar-city.json', { types: cityTypes, events: city })) changed.push('civic/cal/calendar-city.json');
fs.writeFileSync(TYPEMAP_FILE, JSON.stringify(Object.fromEntries(Object.entries(typeMap).filter(([k]) => !GENERIC.has(k)).sort()), null, 1) + '\n');

const touched = [...changed, ...copied];
if (touched.length) {
  const mp = path.join(ROOT, 'app/manifest.json');
  const man = JSON.parse(fs.readFileSync(mp, 'utf8'));
  for (const rel of touched) {
    const buf = fs.readFileSync(path.join(PACK, rel));
    man.files[rel] = { sha: crypto.createHash('sha256').update(buf).digest('hex'), size: buf.length };
  }
  man.generated = new Date().toISOString().replace(/\.\d+Z$/, '+00:00');
  fs.writeFileSync(mp, JSON.stringify(man, null, 1).split('\n').map(l => l.replace(/^ +/, '')).join('\n'));
}
console.log(JSON.stringify({ today: TODAY, bk: bk.length, cb6: out.length, council_hearings: civic.length, city: city.length, boards: boards.length, changed, copied }));
