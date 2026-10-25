// The day map's past days: every event on calendar.html dated before today (the app calendar file starts today),
// with its time, place, flyer and the calendar's own logo for its type. Printed as JSON for scripts/build_daymap.py.
import fs from 'fs'; import path from 'path'; import vm from 'vm';
const ROOT = path.dirname(path.dirname(new URL(import.meta.url).pathname));
const html = fs.readFileSync(path.join(ROOT, 'calendar.html'), 'utf8');
function grab(name) {
  const marker = 'const ' + name + ' = ';
  const i = html.indexOf(marker);
  let j = i + marker.length, depth = 0, started = false, q = null;
  for (; j < html.length; j++) {
    const c = html[j], n = html[j + 1];
    if (q) { if (c === '\\') { j++; continue; } if (c === q) q = null; continue; }
    if (c === '/' && n === '/') { j = html.indexOf('\n', j); continue; }
    if (c === '/' && n === '*') { j = html.indexOf('*/', j) + 1; continue; }
    if (c === '"' || c === "'" || c === '`') { q = c; continue; }
    if (c === '{' || c === '[' || c === '(') { depth++; started = true; }
    else if (c === '}' || c === ']' || c === ')') { depth--; if (started && depth === 0) { j++; break; } }
  }
  return vm.runInNewContext('(' + html.slice(i + marker.length, j) + ')', {});
}
const EVENTS = grab('EVENTS'), ORG_ICONS = grab('ORG_ICONS');
const ent = s => String(s || '').replace(/&amp;/g, '&').replace(/&#39;|&rsquo;/g, '’').replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
const NAMES = {};
for (const m of html.matchAll(/<option value="([^"]+)">([^<]+)<\/option>/g)) if (!(m[1] in NAMES)) NAMES[m[1]] = ent(m[2]).trim();
for (const m of html.matchAll(/<div class="leg" data-type="([^"]+)"[^>]*>(?:<img[^>]*>)?([^<]+)<\/div>/g)) if (!(m[1] in NAMES)) NAMES[m[1]] = ent(m[2]).trim();
function endTime(ev) {
  const txt = [ev.desc, ev.time, ev.label].filter(Boolean).join(' ');
  let m = txt.match(/\bEnds?\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*([AaPp])\.?[Mm]\.?/);
  if (!m) m = txt.match(/\d{1,2}(?::\d{2})?\s*(?:[AaPp]\.?[Mm]\.?)?\s*(?:–|—|-|to)\s*(\d{1,2})(?::(\d{2}))?\s*([AaPp])\.?[Mm]\.?/);
  return m ? `${parseInt(m[1], 10)}:${m[2] || '00'} ${m[3].toUpperCase()}M` : '';
}
const local = u => { const m = String(u || '').match(/^(?:https?:\/\/(?:www\.)?bkcb6\.app)?\/?([^?#]+\.(?:jpg|jpeg|png|webp))$/i); return m && !/^https?:/i.test(m[1]) && fs.existsSync(path.join(ROOT, m[1])) ? '/' + m[1] : null; };
const today = process.argv[2];
const out = [];
for (const [d, list] of Object.entries(EVENTS)) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(d) || d >= today) continue;
  for (const e of list || []) {
    if (!e || !e.label) continue;
    if (Array.isArray(e.cds) && e.cds.length && !e.cds.includes('306')) continue;
    const t = e.type || '';
    const ic = ORG_ICONS[t] || (t === 'bpl' || String(t).startsWith('lib-') ? 'bpl.png' : null);
    const time = (String(e.time || '').match(/\d{1,2}(?::\d{2})?\s*[AaPp]\.?[Mm]/) || [''])[0].replace(/\./g, '').toUpperCase().replace(/^(\d+)\s*([AP]M)$/, '$1:00 $2').replace(/(\d)([AP]M)/, '$1 $2');
    out.push({ d, l: ent(e.label), t: time, e: endTime(e), loc: ent(e.location || ''), org: NAMES[t] || (t === 'board' || t === 'committee' ? 'Brooklyn Community Board 6' : ''), k: t,
      fl: local(e.flyer), ic: ic ? local(ic) : null, h: /^https?:/.test(e.href || '') ? e.href : '' });
  }
}
process.stdout.write(JSON.stringify(out));
