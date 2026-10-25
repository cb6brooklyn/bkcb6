#!/usr/bin/env python3
"""One-time patch: swap the glossary list in glossary.html and bk/glossary.html for the
policy-area / agency module (tools/glossary_module.html + .js). Safe to re-run."""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
markup = open(os.path.join(ROOT, "tools/glossary_module.html")).read()
js = open(os.path.join(ROOT, "tools/glossary_module.js")).read()
for rel in ("glossary.html", "bk/glossary.html"):
    p = os.path.join(ROOT, rel)
    t = open(p).read()
    if "gx-bar" in t:
        # already patched: refresh module contents
        t = re.sub(r"  <!-- GLOSSARY \+ GUIDE TO REGULATIONS.*?<div id=\"gloss-list\"></div>\n", lambda m: markup, t, count=1, flags=re.S)
        t = re.sub(r"// Glossary \+ guide to regulations\. Data:.*?\n\}\)\(\);\n", lambda m: js, t, count=1, flags=re.S)
    else:
        a = t.index("  <!-- SEARCH + FILTER -->")
        b = t.index('<div id="gloss-list"></div>', a) + len('<div id="gloss-list"></div>')
        t = t[:a] + markup.rstrip("\n") + t[b:]
        a = t.index("const TERMS = [")
        b = t.index("renderGloss();\n", t.index("function setGlossFilter", a)) + len("renderGloss();\n")
        t = t[:a] + js + t[b:]
    t = t.replace("Searchable terms by topic", "Terms and rules by policy area and agency")
    t = t.replace("Search by word, filter by topic area, or browse. Each entry defines a concept once in plain language.",
                  "Search by word, or narrow by policy area and by agency. Each term is defined once in plain language, and the rules (heat season, trash setout, permits and the rest) say who has to do what, with the agency that enforces it and a link to the source.")
    open(p, "w").write(t)
    print(rel, "ok", len(t))
