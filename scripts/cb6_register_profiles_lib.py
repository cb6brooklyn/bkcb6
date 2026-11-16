"""Name and address casing shared by the BKCB6 register and facility profile scripts."""
import re
SMALL = {'of', 'and', 'the', 'for', 'at', 'in', 'on', 'a', 'de', 'la', 'el', 'by'}
def tc(s):
    s = re.sub(r'\s+', ' ', re.sub(r'\s*#+\s*', ' ', s or '')).strip()
    if s != s.upper(): return s
    out = []
    for i, w in enumerate(s.split(' ')):
        lw = w.lower()
        if re.fullmatch(r'(llc|inc|nyc|ny|bbq|ii|iii|iv|usa|cvs|bk|dba|j\.?t\.?c\.?)\.?,?', lw): out.append(w.upper() if lw.rstrip('.,') not in ('inc',) else 'Inc.')
        elif i and lw in SMALL: out.append(lw)
        else: out.append(re.sub(r"(^|[-/(.&+])([a-z])", lambda m: m.group(1) + m.group(2).upper(), lw))
    return ' '.join(out).replace("'S", "'s").replace("’S", "’s")
def addr_tc(a): return re.sub(r'\b(\d+)(St|Nd|Rd|Th)\b', lambda m: m.group(1) + m.group(2).lower(), tc(a))
