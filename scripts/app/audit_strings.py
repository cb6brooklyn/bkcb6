#!/usr/bin/env python3
"""Every string literal a screen can show, routed through civic/copy.json. audit_strings.py <app dir> [--dry]
Finds string literals with words in the views (and Shared/Services) that are not already read through Copy.t / Copy.f /
T() / MapStyle / Lists / UIConfig and are not code keys (identifiers, symbol names, file names, URLs, dictionary keys,
switch cases, string-matching arguments), and wraps them: "text" -> Copy.t("<File>.<id>", "text"), with interpolations
as Copy.f(... "{0}" ...). Writes copy-audit-<app>.json with the new keys and what was left as a key."""
import re, sys, os, glob, json, hashlib

ROOT = sys.argv[1]; DRY = '--dry' in sys.argv
app = os.path.basename(os.path.dirname(os.path.abspath(ROOT)))
# Shared/ is left alone: the widget extension compiles it too, without Copy.
FILES = sorted(glob.glob(os.path.join(ROOT, 'App/Views/*.swift')) + glob.glob(os.path.join(ROOT, 'App/Services/*.swift')) + glob.glob(os.path.join(ROOT, 'App/Theme.swift')))
def h8(t): return hashlib.sha1(t.encode()).hexdigest()[:8]

# contexts whose string argument is a key, a name, a pattern, not words on the screen
KEY_CTX = re.compile(r'\b(systemName|forKey|key|id|named|forResource|withExtension|subdirectory|rawValue|string|of|separator|separatedBy|with|prefix|suffix|identifier|tag|format|dateFormat|locale|scheme|host|path|anchor|pattern|font|family|url|href|slug|layer|screen|section|cal|file|image|logo|icon|symbol|cover|tile|route|dest|destination|content|when|cd|boro|ad|ed|sd|op|target|source|src|base|ext|dir|folder|by|as|to|from|into|at|for|in|where|select|order|query|q|filter|sql|fields|sortBy|group|groupBy)\s*:\s*$|\b(dateFormat|format|pattern|select|order|where|query|regex)\s*=\s*$')
KEY_FN = re.compile(r'(AppStorage|SceneStorage|\.id|\.tag|accessibilityIdentifier|NSLog|hasPrefix|hasSuffix|contains|replacingOccurrences|components|split|firstIndex|lastIndex|trimmingCharacters|starts|range|index|Notification\.Name|UserDefaults|URL|Hook\.value|Hook\.flag|DK\.json|DK\.str|DK\.num|DataPack\.url|DataPack\.has|Bundle\.main\.url|NSPredicate|String\(format|Image|UIImage|Color\(|Font\.custom|\.custom|Date\(|DateFormatter|ISO8601|Calendar|TimeZone|Locale|CharacterSet|NSLocalizedString|print|fatalError|assert|precondition|os_log|Logger|NSRegularExpression|NSSortDescriptor|exists|matches|lowercased\(\) ==|uppercased\(\) ==|== |!= |case |import |@objc|#selector|init\(rawValue|coder|Swift\.print|UIApplication\.shared\.open|openURL)\s*\(?\s*$')
WRAPPED = re.compile(r'(Copy\.[tf]|\bT|UIConfig\.shared\.(string|text|label)|MapStyle\.(label|icon|color)|Lists\.\w+|DKMarkers\.icon)\(\s*$|(Copy\.[tf]|T)\("[^"]*",\s*$')
VISIBLE_HINT = re.compile(r'[A-Za-z]{2,}')

def visible(t):
    """A literal that reads as words on the screen rather than a code key."""
    if not VISIBLE_HINT.search(t): return False
    if '\\(' in t and len(t.replace('\\(', '')) < 4: return False
    if re.fullmatch(r'[a-z0-9_.:/\-\\()$?&=#%+,{}]*', t): return False         # keys, slugs, routes, paths, "map-{0}"
    if re.fullmatch(r'[A-Za-z0-9_]+', t) and not t[0].isupper(): return False   # camelCase identifiers
    if ' ' not in t and re.fullmatch(r'[\w{}.:/\-]+', t) and '{' in t: return False  # key templates "{0}Header"
    if re.fullmatch(r'[a-z]+(\.[a-z]+)+', t): return False                       # SF Symbols "house.fill"
    if re.fullmatch(r'[a-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+', t): return False      # dotted keys "cb6map.setupSeen"
    if t.startswith('http') or t.startswith('mailto:') or t.startswith('tel:'): return False
    if re.fullmatch(r'[A-Z][a-zA-Z0-9]*', t) and len(t) < 4: return False        # "CD", "AD", "BK"
    if re.fullmatch(r'#[0-9A-Fa-f]{6,8}', t): return False
    if re.fullmatch(r'[\d\s.,:%$+\-/]+', t): return False
    if re.fullmatch(r'[A-Za-z0-9]+\.(png|jpg|jpeg|webp|json|geojson|gz|html|svg|pdf|csv|txt)', t): return False
    return True

def scan_literal(s, i):
    j = i + 1; out = ''; args = []
    while j < len(s):
        c = s[j]
        if c == '\\':
            if j + 1 < len(s) and s[j + 1] == '(':
                k = j + 2; depth = 1; instr = False
                while k < len(s) and depth > 0:
                    ch = s[k]
                    if instr:
                        if ch == '\\': k += 1
                        elif ch == '"': instr = False
                    else:
                        if ch == '"': instr = True
                        elif ch == '(': depth += 1
                        elif ch == ')': depth -= 1
                    k += 1
                out += '{%d}' % len(args); args.append(s[j + 2:k - 1]); j = k; continue
            out += s[j:j + 2]; j += 2; continue
        if c == '"': return j + 1, out, args
        if c == '\n': return None
        out += c; j += 1
    return None

reg = {}; left = []; stats = {}
for fn in FILES:
    stem = os.path.basename(fn)[:-6]
    s = open(fn).read(); out = ''; i = 0; n = 0; kept = 0
    while i < len(s):
        c = s[i]
        if c == '/' and s.startswith('//', i):          # a comment: copy through
            j = s.find('\n', i); j = len(s) if j < 0 else j; out += s[i:j]; i = j; continue
        if c != '"': out += c; i += 1; continue
        if i > 0 and s[i - 1] == '#':                      # a raw string #"..."#: copy through
            j = s.find('"#', i + 1); j = len(s) if j < 0 else j + 2; out += s[i:j]; i = j; continue
        if s.startswith('"""', i):                       # multi-line text: wrap whole
            j = s.find('"""', i + 3); body = s[i + 3:j]
            before = s[max(0, i - 60):i]
            if WRAPPED.search(before) or '\\(' in body or not visible(body): out += s[i:j + 3]; i = j + 3; continue
            k = f'{stem}.{h8(body)}'; reg[k] = body
            out += f'Copy.t("{k}", """{body}""")'; i = j + 3; n += 1; continue
        r = scan_literal(s, i)
        if r is None: out += c; i += 1; continue
        end, tpl, args = r
        before = s[max(0, i - 70):i]
        line_start = s.rfind('\n', 0, i) + 1; line = s[line_start:s.find('\n', i) if s.find('\n', i) > 0 else len(s)]
        if WRAPPED.search(before): out += s[i:end]; i = end; continue
        if re.search(r'(Copy\.[tf]|T)\("$', before): out += s[i:end]; i = end; continue
        one_line_enum = re.match(r'\s*(?:\w+\s+)*enum\s+\w+\s*:\s*String', line) is not None and re.search(r'=\s*$', s[line_start:i]) is not None
        sofar = s[line_start:i]
        # on a "case" line only the pattern (before the colon that ends it) is a key; what follows the colon is shown
        case_pattern = line.strip().startswith('case ') and not re.search(r'(?<!\?):(?!:)', sofar.split('case ', 1)[1] if 'case ' in sofar else '')
        key_name = re.search(r'static (let|var) \w*(key|Key|id|ID|Id|name|Name|slug|Slug|url|URL|path|Path|file|File|prefix|Prefix|suffix|Suffix|scheme|host|format|Format)\w* *(: *String)? *= *$', sofar) is not None
        if KEY_CTX.search(before) or KEY_FN.search(before) or case_pattern or one_line_enum or key_name or re.search(r'(enum |case )[^"]*=\s*$', sofar):
            if visible(tpl): left.append((stem, tpl[:60], 'key context')); kept += 1
            out += s[i:end]; i = end; continue
        if 'Lists.' in line or 'DK.json(' in line or 'Hook.' in line or 'UserDefaults' in line or 'Notification.Name' in line or 'print(' in line or 'assert' in line or 'fatalError' in line:
            if visible(tpl): left.append((stem, tpl[:60], 'line context')); kept += 1
            out += s[i:end]; i = end; continue
        if not visible(tpl): out += s[i:end]; i = end; continue
        if 'specifier:' in ''.join(args) or 'Image(' in ''.join(args) or 'Text(' in ''.join(args): left.append((stem, tpl[:60], 'formatted')); kept += 1; out += s[i:end]; i = end; continue
        k = f'{stem}.{h8(tpl)}'; reg[k] = tpl.replace('\\"', '"')
        isText = re.search(r'Text\(\s*$', before) is not None and re.match(r'\s*\)', s[end:end + 4]) is not None
        if args:
            call = f'Copy.f("{k}", "{tpl}", {", ".join(args)})'
            if isText: call = 'verbatim: ' + call
        else:
            call = f'Copy.t("{k}", "{tpl}")'
            if isText: call = 'LocalizedStringKey(' + call + ')'
        out += call; i = end; n += 1
    # enum raw values shown as they are: chips, titles, labels read the file by <File>.<Enum>.<case>
    RAW = re.compile(r'(DKChip\(text: |Text\(|Button\(|menuChrome\(|legendEntry\(|title: |text: |label: |subtitle: |name: |caption: )(\$0|[a-zA-Z_][\w.]*)\.rawValue(\.uppercased\(\))?')
    def raw_sub(m):
        v = m.group(2)
        return f'{m.group(1)}Copy.t("{stem}.\\(type(of: {v})).\\({v})", {v}.rawValue){m.group(3) or ""}'
    out2, nr = RAW.subn(raw_sub, out)
    # the same on Copy.f arguments, interpolations and tuple cells, on lines that show the value rather than key on it
    SKIP_RAW = re.compile(r'==|!=|<|>|sorted|signature|sig =|key|id:|\.tag\(|init\(rawValue|hasPrefix|hasSuffix|contains\(|UserDefaults|AppStorage|Hook\.|DK\.json|Lists\.|joined|map\(\\\.rawValue\)|\+ |\.lowercased|replacingOccurrences|split|components|filter')
    RAW2 = re.compile(r'(Copy\.f\([^\n]*?, |\\\(|\(|, )(\$0|[a-zA-Z_][\w]*)\.rawValue(\.uppercased\(\))?(?=[,)\s])')
    lines2 = out2.split('\n'); n2 = 0
    for li, ln in enumerate(lines2):
        if '.rawValue' not in ln or 'type(of:' in ln and ln.count('.rawValue') == ln.count('type(of:') or SKIP_RAW.search(ln): continue
        new_ln, k2 = RAW2.subn(lambda m: f'{m.group(1)}Copy.t("{stem}.\\(type(of: {m.group(2)})).\\({m.group(2)})", {m.group(2)}.rawValue){m.group(3) or ""}', ln)
        if k2: lines2[li] = new_ln; n2 += k2
    if n2: out2 = '\n'.join(lines2); nr += n2
    if nr:
        out = out2; n += nr
        for em in re.finditer(r'enum (\w+)\s*:\s*String[^{]*\{', out):
            k = em.end(); depth = 1
            while k < len(out) and depth: depth += (out[k] == '{') - (out[k] == '}'); k += 1
            body = out[em.end():k]
            for cm in re.finditer(r'\bcase ([^\n]+)', body):
                for item in cm.group(1).split(','):
                    item = item.strip()
                    mm = re.match(r'(\w+)(?:\s*=\s*"([^"]*)")?$', item)
                    if mm and mm.group(1) not in ('let', 'var'): reg[f'{stem}.{em.group(1)}.{mm.group(1)}'] = mm.group(2) if mm.group(2) is not None else mm.group(1)
    stats[stem] = (n, kept)
    if n and not DRY: open(fn, 'w').write(out)
json.dump({'strings': reg, 'left': left}, open(os.path.join(ROOT, '..', f'copy-audit-{app}.json'), 'w'), ensure_ascii=False, indent=1)
print(app, 'wrapped', sum(a for a, _ in stats.values()), '| left as keys/patterns', len(left))
for st, (a, b) in sorted(stats.items(), key=lambda x: -x[1][0])[:14]:
    if a: print('  ', st, a)
