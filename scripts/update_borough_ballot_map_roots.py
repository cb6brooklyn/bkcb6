from pathlib import Path

ROOT = Path('/home/ubuntu/bkcb6_publish_20260414_2000')
VERSION_OLD = 'winner-margin-rollout.js?v=202604150335'
VERSION_NEW = 'winner-margin-rollout.js?v=202604150530'

PAGES = [
    ('bronx.html', 'bronx', 'Bronx', 'BRONX'),
    ('brooklyn.html', 'brooklyn', 'Brooklyn', 'BROOKLYN'),
    ('manhattan.html', 'manhattan', 'Manhattan', 'MANHATTAN'),
    ('queens.html', 'queens', 'Queens', 'QUEENS'),
    ('statenisland.html', 'statenisland', 'Staten Island', 'STATEN ISLAND'),
]

TEMPLATE = '''  <div class="card" data-winner-margin-root data-borough="{slug}" data-borough-name="{name}" data-race="MAYOR">
    <div class="section-label">{upper} Winner Margin Map</div>
  </div>

  <div class="card" data-winner-margin-root data-borough="{slug}" data-borough-name="{name}" data-race="Q2">
    <div class="section-label">{upper} Question 2 Approval Margin Map</div>
  </div>

  <div class="card" data-winner-margin-root data-borough="{slug}" data-borough-name="{name}" data-race="Q3">
    <div class="section-label">{upper} Question 3 Approval Margin Map</div>
  </div>

  <div class="card" data-winner-margin-root data-borough="{slug}" data-borough-name="{name}" data-race="Q4">
    <div class="section-label">{upper} Question 4 Approval Margin Map</div>
  </div>'''

for filename, slug, name, upper in PAGES:
    path = ROOT / filename
    text = path.read_text()
    old_block = f'''  <div class="card" data-winner-margin-root data-borough="{slug}" data-borough-name="{name}">
    <div class="section-label">{upper} Winner Margin Map</div>
  </div>'''
    new_block = TEMPLATE.format(slug=slug, name=name, upper=upper)
    if old_block not in text:
        raise SystemExit(f'Map root block not found in {filename}')
    text = text.replace(old_block, new_block, 1)
    text = text.replace(VERSION_OLD, VERSION_NEW)
    path.write_text(text)
    print(f'Updated {filename}')
