#!/usr/bin/env python3
"""Every elected official named on the government org chart links to their profile: on the site (govhub.html,
links to /<slug>) and in the apps' copy (app/data/civic/orgchart/orgchart.html, links to <slug>, relative, which
is what the apps' web view can open in-app: a root link such as /cmmarte is a file URL outside the page's folder
and WebKit drops it before the app sees it). Also repairs the Bronx/Queens State Senate cells that were collapsed,
and makes the address-lookup results link the council member, senator and assembly member they name."""
import base64, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
officials = json.load(open(os.path.join(ROOT, 'app/data/civic/officials.json')))
by_type = {}
for o in officials:
    if o.get('district') is not None: by_type.setdefault(o['type'], {})[o['district']] = o['slug']
slugs = {o['slug'] for o in officials}

BROKEN = re.compile(r'(<div class="leg-cell"><div class="dist">SD 35</div><div class="name">)<a href="/sensanders"[^>]*>Andrea Stewart-Cousins ↗ D\s*SD 36Jamaal T\. Bailey ↗ D\s*Queens\s*SD 10James Sanders Jr\.</a>( <span style="font-size:\.6rem;color:#1d4ed8">D</span></div></div>)')
STYLE = 'style="color:var(--navy);text-decoration:none;font-weight:600"'

def fix(path, pfx):
    s = open(path).read()
    L = lambda slug, text, style=STYLE: '<a href="%s%s" %s>%s</a>' % (pfx, slug, style, text)
    # 1. the collapsed Senate cells
    s, n = BROKEN.subn(lambda m: m.group(1) + '<a href="https://www.nysenate.gov/senators/andrea-stewart-cousins" target="_blank" ' + STYLE + '>Andrea Stewart-Cousins</a>' + m.group(2)
                        + '\n        <div class="leg-cell"><div class="dist">SD 36</div><div class="name">' + L('senbailey', 'Jamaal T. Bailey') + ' <span style="font-size:.6rem;color:#1d4ed8">D</span></div></div>'
                        + '\n      </div>\n      <div class="leg-section-header"><div>Queens</div></div>\n      <div class="leg-grid">'
                        + '\n        <div class="leg-cell"><div class="dist">SD 10</div><div class="name">' + L('sensanders', 'James Sanders Jr.') + m.group(2), s)
    assert n == 1 or 'SD 36</div>' in s, path
    # 2. the apps' copy: root links become relative, so the app's web view can open them, and the two seals are
    #    inlined, because the page is served from the app's cache once it has been updated, where no logo file sits.
    if pfx == '':
        s = re.sub(r'href="/([a-z0-9-]+)"', r'href="\1"', s)
        for f in ('nyc-logo.jpg', 'nys-logo.png'):
            raw = open(os.path.join(ROOT, 'assets/govhub', f), 'rb').read()
            mime = 'image/png' if raw[:8] == b'\x89PNG\r\n\x1a\n' else 'image/jpeg'   # the type by the bytes, not the name
            b = base64.b64encode(raw).decode()
            inl = 'src="data:%s;base64,%s" data-src="%s"' % (mime, b, f)
            s = re.sub(r'src="data:[^"]+" data-src="%s"' % re.escape(f), inl, s)   # already inlined on an earlier run
            s = re.sub(r'(?<![-\w])src="%s"' % re.escape(f), lambda m: inl, s)
    # 3. names that were plain text
    plain = {'Eric Gonzalez': 'dagonzalez', 'Alvin Bragg': 'dabragg', 'Melinda Katz': 'dakatz', 'Darcel Clark': 'daclark', 'Michael McMahon': 'damcmahon'}
    for name, slug in plain.items():
        s = s.replace('font-weight:700;color:var(--navy)">%s</div>' % name, 'font-weight:700;color:var(--navy)">%s</div>' % L(slug, name, 'style="color:var(--navy);text-decoration:none"'))
    for name, slug in {'Kathy Hochul': 'governor', 'Antonio Delgado': 'lieutenantgovernor', 'Letitia James': 'attorneygeneral', 'Thomas DiNapoli': 'statecomptroller'}.items():
        s = re.sub(r'(<h3 [^>]*>[^<]*— )%s(</h3>)' % re.escape(name), lambda m: m.group(1) + L(slug, name, 'style="color:inherit;text-decoration:underline;text-underline-offset:3px"') + m.group(2), s)
    s = s.replace('Speaker: Julie Menin (CD 5, Manhattan)', 'Speaker: ' + L('cmmenin', 'Julie Menin', 'style="color:inherit;text-decoration:underline"') + ' (CD 5, Manhattan)')
    s = s.replace('Speaker: Carl Heastie.', 'Speaker: ' + L('amheastie', 'Carl Heastie', 'style="color:inherit;text-decoration:underline"') + '.')
    # 4. the address-lookup results name the official as a link to their profile
    maps = 'const OC_SLUG = ' + json.dumps({'cc': by_type.get('council', {}), 'ss': by_type.get('senate', {}), 'sa': by_type.get('assembly', {})}, separators=(',', ':')) + ';\n'
    maps += 'const OC_PFX = %s;\nfunction ocName(kind, n, name) { const s = OC_SLUG[kind][n]; return s ? `<a href="${OC_PFX}${s}" style="color:#0d1b4b;text-decoration:underline;text-underline-offset:3px">${name}</a>` : name; }\n' % json.dumps(pfx)
    s = re.sub(r'const OC_SLUG = .*?\nfunction ocName[^\n]*\n', '', s, flags=re.S)
    s = s.replace('const OC_COUNCIL = {', maps + 'const OC_COUNCIL = {', 1)
    s = s.replace("${cm ? cm[0] : '—'}", "${cm ? ocName('cc', cdNum, cm[0]) : '—'}")
    s = s.replace("State Senate District ${ssNum}</div>\n    <div style=\"font-size:.95rem;font-weight:700;color:#0d1b4b;margin-bottom:6px\">${info ? info[0] : ''}</div>",
                  "State Senate District ${ssNum}</div>\n    <div style=\"font-size:.95rem;font-weight:700;color:#0d1b4b;margin-bottom:6px\">${info ? ocName('ss', ssNum, info[0]) : ''}</div>")
    s = s.replace("Assembly District ${saNum}</div>\n    <div style=\"font-size:.95rem;font-weight:700;color:#0d1b4b;margin-bottom:6px\">${info ? info[0] : ''}</div>",
                  "Assembly District ${saNum}</div>\n    <div style=\"font-size:.95rem;font-weight:700;color:#0d1b4b;margin-bottom:6px\">${info ? ocName('sa', saNum, info[0]) : ''}</div>")
    open(path, 'w').write(s)
    linked = set(re.findall(r'href="%s([a-z0-9-]+)"' % re.escape(pfx), s))
    print(os.path.relpath(path, ROOT), 'official links', len(linked & slugs), '| ocName hooks', s.count('ocName('), '| root links left', len(re.findall(r'href="/[a-z0-9-]+"', s)) if pfx == '' else '-')

fix(os.path.join(ROOT, 'govhub.html'), '/')
fix(os.path.join(ROOT, 'app/data/civic/orgchart/orgchart.html'), '')
