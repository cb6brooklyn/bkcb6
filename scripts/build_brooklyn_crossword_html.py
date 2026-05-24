#!/usr/bin/env python3
"""Build crossword-brooklyn-history.html by transforming crossword.html template:
   - replace PUZZLES data (both script blocks) with Brooklyn history puzzles (sourced)
   - replace showDefinition() to link to per-entry source instead of glossary
   - update title/meta/header/footer text
"""
import json, re, os

ROOT = os.path.join(os.path.dirname(__file__), '..')
tmpl = open(os.path.join(ROOT,'crossword.html')).read()
puzzles = json.load(open(os.path.join(os.path.dirname(__file__),'brooklyn_crossword_puzzles_sourced.json')))
PUZ_JSON = json.dumps(puzzles, ensure_ascii=False)

# 1) Replace both `const PUZZLES = [...];` occurrences.
#    The data is a single-line array literal ending in `}];`
pat = re.compile(r'const PUZZLES = \[.*?\}\];', re.DOTALL)
n_before = len(pat.findall(tmpl))
tmpl = pat.sub('const PUZZLES = ' + PUZ_JSON.replace('\\','\\\\') + ';', tmpl)
print("PUZZLES blocks replaced:", n_before)

# 2) Replace showDefinition to use entry.src_url / entry.src_title.
old_def = '''function showDefinition(entry) {
  document.getElementById('defRevealWord').textContent = '\u2705 ' + entry.word;
  document.getElementById('defRevealText').textContent = entry.clue;
  document.getElementById('defRevealLink').href = GLOSSARY_BASE + (SLUG_MAP[entry.word] || entry.word.toLowerCase());
  document.getElementById('defReveal').classList.add('visible');
}'''
new_def = '''function showDefinition(entry) {
  document.getElementById('defRevealWord').textContent = '\u2705 ' + entry.word;
  document.getElementById('defRevealText').textContent = entry.clue;
  var link = document.getElementById('defRevealLink');
  link.href = entry.src_url || (GLOSSARY_BASE + (SLUG_MAP[entry.word] || entry.word.toLowerCase()));
  var label = link.querySelector('.def-link-label');
  if (label) label.textContent = entry.src_title ? ('Source: ' + entry.src_title) : 'View in Glossary';
  var appLink = document.getElementById('defAppLink');
  if (appLink) {
    if (entry.app_url) {
      appLink.href = entry.app_url;
      appLink.querySelector('.def-app-label').textContent = entry.app_title || 'View on the app';
      appLink.style.display = 'inline-flex';
    } else {
      appLink.style.display = 'none';
    }
  }
  document.getElementById('defReveal').classList.add('visible');
}'''
c = tmpl.count(old_def)
tmpl = tmpl.replace(old_def, new_def)
print("showDefinition replaced:", c)

# 3) Wrap the link label text in a span so JS can update it. Original link inner text is "View in Glossary".
old_link = '''<line x1="10" y1="14" x2="21" y2="3"/></svg>
          View in Glossary
        </a>'''
new_link = '''<line x1="10" y1="14" x2="21" y2="3"/></svg>
          <span class="def-link-label">View source</span>
        </a>
        <a class="def-reveal-link" id="defAppLink" href="#" target="_blank" rel="noopener" style="display:none;margin-left:12px">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
          <span class="def-app-label">View on the app</span>
        </a>'''
print("link label wrap:", tmpl.count(old_link))
tmpl = tmpl.replace(old_link, new_link)

# 4) Title / meta / header text swaps (Brooklyn borough history; no em dashes).
repls = [
    # --- Share / OG image (branded crossword preview) ---
    ('<meta property="og:image" content="https://bkcb6.app/icon-quizzes.png">',
     '<meta property="og:image" content="https://bkcb6.app/crossword-brooklyn-history-og.png">\n<meta property="og:image:width" content="500">\n<meta property="og:image:height" content="500">'),
    ('<meta name="twitter:card" content="summary_large_image">',
     '<meta name="twitter:card" content="summary">'),
    ('<meta name="twitter:image" content="https://cb6brooklyn.github.io/bkcb6/icon-crossword.png">',
     '<meta name="twitter:image" content="https://bkcb6.app/crossword-brooklyn-history-og.png">'),
    # --- Fonts: Inter + Playfair -> DM Sans (match Jeopardy / app brand) ---
    ('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">',
     '<link rel="preconnect" href="https://fonts.googleapis.com">\n<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">'),
    ("font-family:'Inter',sans-serif", "font-family:'DM Sans',sans-serif"),
    ("font-family:'Playfair Display',serif", "font-family:'DM Sans',sans-serif"),
    # --- Palette: shift to Brooklyn seal colors (keep light, readable grid) ---
    ('--navy:  #1a2744;', '--navy:  #0d3a66;'),
    ('--blue:  #2563eb;', '--blue:  #005a9c;'),
    ('--gold:  #f59e0b;', '--gold:  #c79a1e;'),
    ('<meta property="og:title" content="CB6 Crossword Puzzle">',
     '<meta property="og:title" content="Brooklyn History Crossword">'),
    # --- Top bar: match Jeopardy (show bkcb6.app, not "Community Board 6") ---
    ('<span style="color:#fff;font-size:.85rem;font-weight:700">Brooklyn <span style="color:#f47920">Community Board 6</span></span>',
     '<a href="https://bkcb6.app" style="text-decoration:none;color:#fff;font-size:1.1rem;font-weight:800;letter-spacing:.5px">bkcb6<span style="color:#f47920">.app</span></a>'),
    ('<meta property="og:description" content="Test your knowledge of NYC land use, zoning, and civic process with the CB6 Crossword.">',
     '<meta property="og:description" content="A crossword covering the history of all 18 Brooklyn community board districts, with a source link for every clue.">'),
    ('<meta property="og:url" content="https://bkcb6.app/crossword.html">',
     '<meta property="og:url" content="https://bkcb6.app/crossword-brooklyn-history.html">'),
    ('<meta name="twitter:title" content="CB6 Crossword Puzzle">',
     '<meta name="twitter:title" content="Brooklyn Borough History Crossword">'),
    ('<meta name="twitter:description" content="Test your knowledge of NYC land use, zoning, and civic process.">',
     '<meta name="twitter:description" content="A crossword covering all 18 Brooklyn community board districts, with sources.">'),
    ('<title>CB6 Crossword Puzzle</title>',
     '<title>Brooklyn Borough History Crossword</title>'),
    ('<div style="font-size:.72rem;color:rgba(255,255,255,.55)">Based on <a href="https://bkcb6.app/glossary.html#crossword-accordion" style="color:#f47920;text-decoration:none;font-weight:600">the glossary</a></div>',
     '<div style="font-size:.72rem;color:rgba(255,255,255,.55)">One clue for each of Brooklyn&#39;s 18 community districts</div>'),
    ('<div style="color:rgba(255,255,255,.5);font-size:.6rem;font-family:\'DM Mono\',monospace;text-transform:uppercase;letter-spacing:.1em;margin-bottom:2px">Crossword</div>',
     '<div style="color:rgba(255,255,255,.5);font-size:.6rem;font-family:\'DM Mono\',monospace;text-transform:uppercase;letter-spacing:.1em;margin-bottom:2px">Borough History Crossword</div>'),
    ('<div class="puzzle-header">\n        <div class="puzzle-eyebrow">Brooklyn Community Board 6</div>\n        <div class="puzzle-title">CB6 <span>Crossword</span></div>',
     '<div class="puzzle-header" style="text-align:center">\n        <img src="brooklyn-seal-v2.png" alt="Borough of Brooklyn seal" style="width:96px;height:96px;border-radius:50%;box-shadow:0 4px 14px rgba(0,0,0,0.15);margin:0 auto 10px;display:block;">\n        <div class="puzzle-title" style="font-size:2rem;text-transform:uppercase;letter-spacing:.5px;color:var(--blue)">Brooklyn History <span style="color:var(--gold)">Crossword</span></div>\n        <div style="font-size:0.85rem;color:var(--gold);font-weight:700;letter-spacing:.5px;margin-top:6px">Designed by Mike Racioppo</div>\n        <div style="font-size:0.92rem;color:var(--muted);font-style:italic;margin-top:4px">Fill the grid, one clue per Brooklyn district.</div>'),
    ('<div class="page-footer">Terms sourced from <a href="https://bkcb6.app/glossary.html" target="_blank">bkcb6.app/glossary.html</a></div>',
     '<div class="page-footer">A civic history game covering all 18 Brooklyn community board districts, from <a href="https://bkcb6.app" target="_blank">bkcb6.app</a></div>'),
    # play counter localStorage key, keep separate from the land-use crossword
    ("const PLAY_KEY = 'cb6_xw_plays';", "const PLAY_KEY = 'cb6_xw_bk_history_plays';"),
    ("let playCount = 0; try { playCount = parseInt(localStorage.getItem('cb6_xw_plays') || '0', 10); } catch(e) {}",
     "let playCount = 0; try { playCount = parseInt(localStorage.getItem('cb6_xw_bk_history_plays') || '0', 10); } catch(e) {}"),
    # Single puzzle now: remove the Puzzle 2 and Puzzle 3 tab buttons
    ('\n    <button class="btn btn-outline" id="tab1" onclick="loadPuzzle(1)" style="font-size:.75rem;padding:5px 14px;color:rgba(255,255,255,.6);border-color:rgba(255,255,255,.2)">Puzzle 2</button>',
     ''),
    ('\n    <button class="btn btn-outline" id="tab2" onclick="loadPuzzle(2)" style="font-size:.75rem;padding:5px 14px;color:rgba(255,255,255,.6);border-color:rgba(255,255,255,.2)">Puzzle 3</button>',
     ''),
    # The lone remaining "Puzzle 1" tab is redundant with one puzzle; hide it
    ('<button class="btn btn-outline active" id="tab0" onclick="loadPuzzle(0)" style="font-size:.75rem;padding:5px 14px;color:#fff;border-color:rgba(255,255,255,.3)">Puzzle 1</button>',
     '<button class="btn btn-outline active" id="tab0" onclick="loadPuzzle(0)" style="display:none">Puzzle 1</button>'),
    # Make tab-highlight loop dynamic over all puzzles
    ('[0,1,2].forEach(i => {\n    document.getElementById(\'tab\'+i).classList.toggle(\'active\', i === idx);\n  });',
     'PUZZLES.forEach((_, i) => {\n    var t = document.getElementById(\'tab\'+i);\n    if (t) t.classList.toggle(\'active\', i === idx);\n  });'),
    ('? \'See all answers — giving up!\'', '? \'See all answers, giving up!\''),
    ('`${puzzle.title} — all ${puzzle.across.length + puzzle.down.length} answers`;',
     '`${puzzle.title}, all ${puzzle.across.length + puzzle.down.length} answers`;'),
]
for a,b in repls:
    cnt = tmpl.count(a)
    if cnt == 0:
        print("  [!] NOT FOUND:", a[:60])
    tmpl = tmpl.replace(a,b)

out = os.path.join(ROOT,'crossword-brooklyn-history.html')
open(out,'w').write(tmpl)
print("Wrote", os.path.abspath(out), "(", len(tmpl), "bytes )")
