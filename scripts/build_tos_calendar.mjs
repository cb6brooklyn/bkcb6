// Writes data/trick-or-streets/calendar.json: for every street on the Spooky CB6 map that is also on
// bkcb6.app/calendar, the calendar entry's deep link, flyer and organization logo, keyed by the map's event id.
// Reads calendar.html (EVENTS, ORG_ICONS) the same way scripts/build_app_calendar.mjs does.
import fs from 'fs';
import path from 'path';
import vm from 'vm';

const ROOT = process.cwd();
const html = fs.readFileSync(path.join(ROOT, 'calendar.html'), 'utf8');
const OUT = path.join(ROOT, 'data/trick-or-streets/calendar.json');

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
const ent = s => String(s || '').replace(/&amp;/g, '&').replace(/&#39;|&rsquo;/g, '’').replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
const TYPE_NAMES = {};
for (const m of html.matchAll(/<option value="([^"]+)">([^<]+)<\/option>/g)) if (!(m[1] in TYPE_NAMES)) TYPE_NAMES[m[1]] = ent(m[2]).trim();
for (const m of html.matchAll(/<div class="leg" data-type="([^"]+)"[^>]*>(?:<img[^>]*>)?([^<]+)<\/div>/g)) if (!(m[1] in TYPE_NAMES)) TYPE_NAMES[m[1]] = ent(m[2]).trim();

// the same slug the calendar's ?event= deep link uses
const slugify = s => String(s || '').toLowerCase().replace(/[‘’']/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 80);

function iconPath(type) {
  const f = ORG_ICONS[type];
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

const out = {};
for (const date of Object.keys(EVENTS).sort()) {
  for (const e of EVENTS[date]) {
    const m = String(e.href || '').match(/trickorstreets\/\?e=([A-Za-z0-9]+)/);
    if (!m) continue;
    const id = m[1];
    if (out[id]) continue; // first calendar entry wins (the CB6 entry for a closure that crosses a board line)
    const row = { event: date + '-' + slugify(e.label), label: ent(e.label), type: e.type, org: TYPE_NAMES[e.type] || e.type };
    const fl = flyerPath(e.flyer); if (fl) row.flyer = fl;
    const ic = iconPath(e.type); if (ic) row.icon = ic;
    out[id] = row;
  }
}
fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(out, null, 1) + '\n');
console.log(JSON.stringify({ linked: Object.keys(out).length, flyers: Object.values(out).filter(r => r.flyer).length, icons: Object.values(out).filter(r => r.icon).length }));
