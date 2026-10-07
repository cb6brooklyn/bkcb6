#!/usr/bin/env python3
"""Every table still written in the app's code becomes a file entry (civic/lists.json), with the code's own
table as the fallback. Covers typed and untyped static tables, instance-level literal tables, colors, tuples,
dictionaries of tuples and simple structs. Run: patch_tables2.py <app dir> [--dry]. Writes lists-<app>-2.json."""
import re, sys, os, glob, json

import sys as _sys
ROOTDIR = _sys.argv[1] if len(_sys.argv) > 1 else ''; DRY = '--dry' in _sys.argv
LISTS2 = r'''

// MARK: - More table shapes from civic/lists.json

extension Lists {
    static func any(_ key: String) -> Any? { entry(key) }
    static func hexColor(_ s: String) -> Color { DK.hex(s) }
    static func colors(_ key: String, _ fallback: [Color]) -> [Color] { (entry(key) as? [String]).map { $0.map(hexColor) } ?? fallback }
    static func uiColors(_ key: String, _ fallback: [UIColor]) -> [UIColor] { (entry(key) as? [String]).map { $0.map { DK.uiHex($0) } } ?? fallback }
    static func colorDict(_ key: String, _ fallback: [String: Color]) -> [String: Color] { (entry(key) as? [String: String]).map { $0.mapValues(hexColor) } ?? fallback }
    static func uiColorDict(_ key: String, _ fallback: [String: UIColor]) -> [String: UIColor] { (entry(key) as? [String: String]).map { $0.mapValues { DK.uiHex($0) } } ?? fallback }
    static func colorDictInt(_ key: String, _ fallback: [Int: Color]) -> [Int: Color] {
        guard let d = entry(key) as? [String: String] else { return fallback }
        var out: [Int: Color] = [:]; for (k, v) in d { if let i = Int(k) { out[i] = hexColor(v) } }; return out
    }
    static func colorPairs(_ key: String, _ fallback: [String: (Color, Color)]) -> [String: (Color, Color)] {
        guard let d = entry(key) as? [String: [String]] else { return fallback }
        var out: [String: (Color, Color)] = [:]; for (k, v) in d where v.count >= 2 { out[k] = (hexColor(v[0]), hexColor(v[1])) }; return out
    }
    static func numberLists(_ key: String, _ fallback: [String: [CGFloat]]) -> [String: [CGFloat]] { (entry(key) as? [String: [NSNumber]]).map { $0.mapValues { $0.map { CGFloat($0.doubleValue) } } } ?? fallback }
    static func numberLists2(_ key: String, _ fallback: [String: [Double]]) -> [String: [Double]] { (entry(key) as? [String: [NSNumber]]).map { $0.mapValues { $0.map(\.doubleValue) } } ?? fallback }
    static func numberDict(_ key: String, _ fallback: [String: Double]) -> [String: Double] { (entry(key) as? [String: NSNumber]).map { $0.mapValues(\.doubleValue) } ?? fallback }
    static func intDict(_ key: String, _ fallback: [String: Int]) -> [String: Int] { (entry(key) as? [String: NSNumber]).map { $0.mapValues(\.intValue) } ?? fallback }
    static func intKeyed(_ key: String, _ fallback: [Int: String]) -> [Int: String] {
        guard let d = entry(key) as? [String: String] else { return fallback }
        var out: [Int: String] = [:]; for (k, v) in d { if let i = Int(k) { out[i] = v } }; return out
    }
    static func charDict(_ key: String, _ fallback: [Character: String]) -> [Character: String] {
        guard let d = entry(key) as? [String: String] else { return fallback }
        var out: [Character: String] = [:]; for (k, v) in d { if let c = k.first { out[c] = v } }; return out
    }
    static func stringSets(_ key: String, _ fallback: [String: Set<String>]) -> [String: Set<String>] { (entry(key) as? [String: [String]]).map { $0.mapValues(Set.init) } ?? fallback }
    static func stringSet(_ key: String, _ fallback: Set<String>) -> Set<String> { (entry(key) as? [String]).map(Set.init) ?? fallback }
    static func numbers(_ key: String, _ fallback: [Double]) -> [Double] { (entry(key) as? [NSNumber]).map { $0.map(\.doubleValue) } ?? fallback }
    static func ints(_ key: String, _ fallback: [Int]) -> [Int] { (entry(key) as? [NSNumber]).map { $0.map(\.intValue) } ?? fallback }
    /// Rows of cells, for tables of tuples; nil when the file has no entry.
    static func rows(_ key: String) -> [[Any]]? { entry(key) as? [[Any]] }
    static func dictRows(_ key: String) -> [String: [[Any]]]? { entry(key) as? [String: [[Any]]] }
    static func dictRow(_ key: String) -> [String: [Any]]? { entry(key) as? [String: [Any]] }
    static func s(_ r: [Any], _ i: Int) -> String { i < r.count ? ((r[i] as? String) ?? (r[i] as? NSNumber)?.stringValue ?? "") : "" }
    static func i(_ r: [Any], _ i: Int) -> Int { i < r.count ? ((r[i] as? NSNumber)?.intValue ?? Int((r[i] as? String) ?? "") ?? 0) : 0 }
    static func d(_ r: [Any], _ i: Int) -> Double { i < r.count ? ((r[i] as? NSNumber)?.doubleValue ?? Double((r[i] as? String) ?? "") ?? 0) : 0 }
    static func b(_ r: [Any], _ i: Int) -> Bool { i < r.count ? ((r[i] as? Bool) ?? ((r[i] as? NSNumber)?.boolValue ?? false)) : false }
    static func c(_ r: [Any], _ i: Int) -> Color { hexColor(s(r, i)) }
    static func uc(_ r: [Any], _ i: Int) -> UIColor { DK.uiHex(s(r, i)) }
    static func u32(_ r: [Any], _ i: Int) -> UInt32 {
        if i < r.count, let n = r[i] as? NSNumber { return n.uint32Value }
        return UInt32(s(r, i).trimmingCharacters(in: CharacterSet(charactersIn: "#")), radix: 16) ?? 0
    }
    static func l(_ r: [Any], _ i: Int) -> [String] { i < r.count ? ((r[i] as? [String]) ?? []) : [] }
    static func ld(_ r: [Any], _ i: Int) -> [Double] { i < r.count ? ((r[i] as? [NSNumber])?.map(\.doubleValue) ?? []) : [] }
    static func coords(_ key: String, _ fallback: [CLLocationCoordinate2D]) -> [CLLocationCoordinate2D] {
        guard let rows = entry(key) as? [[String: NSNumber]] else { return fallback }
        return rows.compactMap { r in
            guard let la = r["latitude"], let ln = r["longitude"] else { return nil }
            return CLLocationCoordinate2D(latitude: la.doubleValue, longitude: ln.doubleValue)
        }
    }
    /// Rows of simple structs, decoded from the file's JSON; the code's table when the file has none.
    static func decode<T: Decodable>(_ key: String, _ fallback: [T]) -> [T] {
        guard let v = entry(key), JSONSerialization.isValidJSONObject(v), let d = try? JSONSerialization.data(withJSONObject: v),
              let out = try? JSONDecoder().decode([T].self, from: d) else { return fallback }
        return out
    }
    static func decodeDict<T: Decodable>(_ key: String, _ fallback: [String: T]) -> [String: T] {
        guard let v = entry(key), JSONSerialization.isValidJSONObject(v), let d = try? JSONSerialization.data(withJSONObject: v),
              let out = try? JSONDecoder().decode([String: T].self, from: d) else { return fallback }
        return out
    }
    /// [["Group title", [items...]], ...]
    static func decodeGroups<T: Decodable>(_ key: String, _ fallback: [(String, [T])]) -> [(String, [T])] {
        guard let rows = entry(key) as? [[Any]] else { return fallback }
        var out: [(String, [T])] = []
        for r in rows where r.count >= 2 {
            guard let title = r[0] as? String, JSONSerialization.isValidJSONObject(r[1]), let d = try? JSONSerialization.data(withJSONObject: r[1]),
                  let items = try? JSONDecoder().decode([T].self, from: d) else { return fallback }
            out.append((title, items))
        }
        return out
    }
}
'''
V = os.path.join(ROOTDIR, 'App/Views'); S = os.path.join(ROOTDIR, 'App/Services'); SH = os.path.join(ROOTDIR, 'Shared')
THEME = {'cb6Navy': '#06024D', 'cb6NavyDeep': '#0d1b4b', 'cb6Orange': '#f47920', 'cb6Paper': '#f8f7f4', 'cb6Ink': '#14141c',
         'cb6Muted': '#626470', 'cb6Rule': '#e1dfd8', 'parksGreen': '#203D27', 'white': '#ffffff', 'black': '#000000',
         'clear': '#00000000', 'gray': '#8e8e93', 'red': '#ff3b30', 'blue': '#007aff', 'green': '#34c759', 'orange': '#ff9500',
         'yellow': '#ffcc00', 'purple': '#af52de', 'pink': '#ff2d55', 'primary': '#000000', 'secondary': '#3c3c4399'}
HEXFN = ('DK.hex', 'Color.fhHex', '.fhHex', 'Color.hex', 'DK.uiHex')

# ---------- tokenizer / parser for Swift literals ----------
class Tok:
    def __init__(self, k, v): self.k, self.v = k, v
    def __repr__(self): return f'{self.k}:{self.v}'

def tokenize(s):
    out = []; i = 0; n = len(s)
    while i < n:
        c = s[i]
        if c.isspace(): i += 1; continue
        if s.startswith('//', i):
            j = s.find('\n', i); i = n if j < 0 else j; continue
        if s.startswith('/*', i):
            j = s.find('*/', i); i = n if j < 0 else j + 2; continue
        if c == '"':
            if s.startswith('"""', i):
                j = s.find('"""', i + 3); out.append(Tok('S', s[i + 3:j])); i = j + 3; continue
            j = i + 1; buf = ''
            while j < n and s[j] != '"':
                if s[j] == '\\':
                    nxt = s[j + 1]
                    if nxt == 'n': buf += '\n'
                    elif nxt == 't': buf += '\t'
                    elif nxt == 'u':
                        m = re.match(r'u\{([0-9A-Fa-f]+)\}', s[j + 1:]); buf += chr(int(m.group(1), 16)); j += 1 + len(m.group(0)); continue
                    elif nxt == '(':  # interpolation: give up on this literal
                        raise ValueError('interpolation')
                    else: buf += nxt
                    j += 2; continue
                buf += s[j]; j += 1
            out.append(Tok('S', buf)); i = j + 1; continue
        if c.isdigit() or (c == '-' and i + 1 < n and s[i + 1].isdigit()) or (c == '.' and i + 1 < n and s[i + 1].isdigit()):
            m = re.match(r'-?(0x[0-9A-Fa-f_]+|\d[\d_]*(\.\d+)?([eE][-+]?\d+)?|\.\d+)', s[i:])
            t = m.group(0).replace('_', '')
            out.append(Tok('N', t)); i += len(m.group(0)); continue
        if c.isalpha() or c == '_' or (c == '.' and i + 1 < n and (s[i + 1].isalpha() or s[i + 1] == '_')):
            m = re.match(r'\.?[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*', s[i:])
            out.append(Tok('I', m.group(0))); i += len(m.group(0)); continue
        if c in '[](),:!?': out.append(Tok('P', c)); i += 1; continue
        if c == '/': out.append(Tok('P', '/')); i += 1; continue
        if c == '*': out.append(Tok('P', '*')); i += 1; continue
        if c == '+': out.append(Tok('P', '+')); i += 1; continue
        if c == '<' or c == '>':  # generic args like Set<String>(...)
            out.append(Tok('P', c)); i += 1; continue
        raise ValueError('char ' + c)
    return out

class P:
    def __init__(self, toks): self.t = toks; self.i = 0
    def peek(self, k=0): return self.t[self.i + k] if self.i + k < len(self.t) else Tok('E', '')
    def take(self):
        t = self.peek(); self.i += 1; return t
    def expect(self, v):
        t = self.take()
        if t.v != v: raise ValueError(f'expected {v} got {t}')
    def number(self):
        t = self.take()
        if t.k != 'N': raise ValueError('number')
        v = int(t.v, 16) if t.v.lower().startswith('0x') or t.v.lower().startswith('-0x') else (float(t.v) if ('.' in t.v or 'e' in t.v.lower()) else int(t.v))
        while self.peek().v in ('/', '*'):
            op = self.take().v; r = self.number()
            v = v / r if op == '/' else v * r
        return v
    def value(self):
        t = self.peek()
        if t.k == 'S': self.take(); return t.v
        if t.k == 'N': return self.number()
        if t.v == '[': return self.collection()
        if t.v == '(': return self.tuple()
        if t.k == 'I': return self.ident()
        raise ValueError('value ' + repr(t))
    def collection(self):
        self.expect('[')
        if self.peek().v == ']': self.take(); return []
        if self.peek().v == ':' and self.peek(1).v == ']': self.take(); self.take(); return {}
        items = []; isdict = False
        while True:
            if self.peek().v == ']': self.take(); break
            v = self.value()
            if self.peek().v == ':':
                self.take(); isdict = True; items.append((v, self.value()))
            else: items.append(v)
            if self.peek().v == ',': self.take()
            elif self.peek().v == ']': self.take(); break
            else: raise ValueError('collection sep ' + repr(self.peek()))
        if isdict:
            d = {}
            for k, v in items: d[k if isinstance(k, int) else str(k)] = v
            return d
        return items
    def args(self):
        """( label: value, value, ... ) -> (labels or None, values)"""
        self.expect('(')
        labels = []; vals = []
        while True:
            if self.peek().v == ')': self.take(); break
            if self.peek().k == 'I' and self.peek(1).v == ':' :
                labels.append(self.take().v); self.take()
            else: labels.append(None)
            vals.append(self.value())
            if self.peek().v == ',': self.take()
            elif self.peek().v == ')': self.take(); break
            else: raise ValueError('args sep ' + repr(self.peek()))
        return labels, vals
    def tuple(self):
        labels, vals = self.args()
        return vals
    def ident(self):
        name = self.take().v
        # generic suffix: Set<String>(...)
        if self.peek().v == '<':
            while self.take().v != '>': pass
        if self.peek().v == '(':
            labels, vals = self.args()
            while self.peek().v in ('!', '?'): self.take()
            return self.call(name, labels, vals)
        while self.peek().v in ('!', '?'): self.take()
        return self.member(name)
    def call(self, name, labels, vals):
        if name in HEXFN: return vals[0]
        if name in ('Copy.t',) and len(vals) >= 2: return vals[1]
        if name in ('MapStyle.color', 'MapStyle.label') and len(vals) == 2: return vals[1]
        if (name.endswith('Hex') or name.endswith('Color') or name.endswith('hex')) and len(vals) == 1 and isinstance(vals[0], str) and vals[0].startswith('#'): return vals[0]
        if name.endswith('Color') and len(vals) == 1 and isinstance(vals[0], int): return '#%06x' % vals[0]
        if name in ('Color', 'UIColor') and labels and labels[0] == 'hex': return vals[0]
        if name in ('Color', 'UIColor') and labels and labels[0] == 'red':
            d = dict(zip(labels, vals)); r, g, b = d['red'], d['green'], d['blue']; a = d.get('opacity', d.get('alpha'))
            h = '#%02x%02x%02x' % (round(r * 255), round(g * 255), round(b * 255))
            if a is not None and a != 1: h += '%02x' % round(a * 255)
            return h
        if name in ('Color', 'UIColor') and labels and labels[0] in ('white', 'gray') :
            d = dict(zip(labels, vals)); w = d.get('white', d.get('gray')); a = d.get('opacity', d.get('alpha'))
            h = '#%02x%02x%02x' % ((round(w * 255),) * 3)
            if a is not None and a != 1: h += '%02x' % round(a * 255)
            return h
        if name in ('Set', 'Array'): return vals[0]
        if name in ('CGFloat', 'Double', 'Int', 'Float'): return vals[0]
        if name == 'URL' and labels and labels[0] == 'string': return vals[0]
        if name == 'Character': return vals[0]
        if name.endswith('.init') : name = name[:-5]
        if labels and all(labels):  # a struct literal with labels: an object
            return {'__type': name, **dict(zip(labels, vals))}
        raise ValueError('call ' + name)
    def member(self, name):
        if name == 'true': return True
        if name == 'false': return False
        if name == 'nil': return None
        n = name.split('.')[-1]
        if n in THEME: return THEME[n]
        raise ValueError('ident ' + name)

def parse_literal(body):
    p = P(tokenize(body)); v = p.value()
    if p.i != len(p.t): raise ValueError('trailing ' + repr(p.peek()))
    return v

# ---------- find the literal's end ----------
def literal_end(s, i):
    """s[i] is '[' ; returns index after the matching ']' (strings and comments skipped)."""
    depth = 0; k = i; n = len(s)
    while k < n:
        c = s[k]
        if c == '"':
            if s.startswith('"""', k):
                k = s.find('"""', k + 3) + 3; continue
            k += 1
            while k < n and s[k] != '"':
                if s[k] == '\\': k += 1
                k += 1
            k += 1; continue
        if s.startswith('//', k): k = s.find('\n', k); continue
        if c == '[': depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0: return k + 1
        k += 1
    raise ValueError('unbalanced')

# ---------- type handling ----------
PRIM = {'String': 's', 'Int': 'i', 'Double': 'd', 'CGFloat': 'f', 'Color': 'c', 'UIColor': 'uc', 'UInt32': 'u', 'Bool': 'b',
        'Set<String>': 'set', '[String]': 'l', '[Double]': 'ld', '[CGFloat]': 'lf', '[Int]': 'li', 'Character': 'ch', 'URL': 'url'}
CELL = {'s': 'Lists.s(r, %d)', 'i': 'Lists.i(r, %d)', 'd': 'Lists.d(r, %d)', 'f': 'CGFloat(Lists.d(r, %d))', 'c': 'Lists.c(r, %d)',
        'uc': 'Lists.uc(r, %d)', 'u': 'Lists.u32(r, %d)', 'b': 'Lists.b(r, %d)', 'set': 'Set(Lists.l(r, %d))', 'l': 'Lists.l(r, %d)',
        'ld': 'Lists.ld(r, %d)', 'lf': 'Lists.ld(r, %d).map { CGFloat($0) }', 'li': 'Lists.ld(r, %d).map { Int($0) }',
        'ch': 'Character(Lists.s(r, %d))', 'url': 'URL(string: Lists.s(r, %d))!'}

def split_top(s, sep=','):
    out = []; depth = 0; cur = ''
    for ch in s:
        if ch in '([<': depth += 1
        if ch in ')]>': depth -= 1
        if ch == sep and depth == 0: out.append(cur); cur = ''
        else: cur += ch
    if cur.strip(): out.append(cur)
    return [x.strip() for x in out]

def tuple_parts(t):
    """'(key: String, name: String)' -> [(label or None, type)]"""
    inner = t.strip()[1:-1]
    parts = []
    for p in split_top(inner):
        if ':' in p and not p.startswith('['):
            lab, ty = p.split(':', 1); parts.append((lab.strip(), ty.strip()))
        else: parts.append((None, p.strip()))
    return parts

def tuple_expr(parts):
    cells = []
    for idx, (lab, ty) in enumerate(parts):
        if ty not in PRIM: raise ValueError('tuple type ' + ty)
        e = CELL[PRIM[ty]] % idx
        cells.append((lab + ': ' + e) if lab else e)
    return '(' + ', '.join(cells) + ')'

def infer_type(v):
    """A Swift type for an untyped literal, from its parsed value."""
    def kind(x):
        if isinstance(x, bool): return 'Bool'
        if isinstance(x, int): return 'Int'
        if isinstance(x, float): return 'Double'
        if isinstance(x, str): return 'String'
        if isinstance(x, list):
            ks = {kind(y) for y in x}
            if len(ks) == 1: return '[' + ks.pop() + ']'
            if ks <= {'Int', 'Double'}: return '[Double]'
            raise ValueError('mixed list')
        if isinstance(x, dict):
            if '__type' in x: raise ValueError('struct')
            vk = {kind(y) for y in x.values()}
            if len(vk) != 1:
                if vk <= {'Int', 'Double'}: vk = {'Double'}
                else: raise ValueError('mixed dict')
            kk = 'Int' if x and all(isinstance(k, int) for k in x) else 'String'
            return '[' + kk + ': ' + vk.pop() + ']'
        raise ValueError('kind')
    return kind(v)

def expr_for(ty, key, lit, value):
    """The Swift expression that reads key from the file with lit as the fallback, for a declared type."""
    ty = re.sub(r'\s+', ' ', ty.strip())
    simple = {'[String: String]': 'Lists.dict', '[String: [String]]': 'Lists.dictList', '[String]': 'Lists.strings', '[(String, String)]': 'Lists.pairs',
              '[Color]': 'Lists.colors', '[String: Color]': 'Lists.colorDict', '[Int: Color]': 'Lists.colorDictInt', '[String: (Color, Color)]': 'Lists.colorPairs',
              '[String: [CGFloat]]': 'Lists.numberLists', '[String: Set<String>]': 'Lists.stringSets', '[String: Int]': 'Lists.intDict',
              '[Int: String]': 'Lists.intKeyed', '[Character: String]': 'Lists.charDict', '[Double]': 'Lists.numbers', '[Int]': 'Lists.ints',
              '[String: Double]': 'Lists.numberDict', '[String: [Double]]': 'Lists.numberLists2', '[UIColor]': 'Lists.uiColors', '[String: UIColor]': 'Lists.uiColorDict'}
    if ty == 'Set<String>': return f'Lists.stringSet("{key}", {lit})'
    if ty == '[CLLocationCoordinate2D]': return f'Lists.coords("{key}", {lit})'
    if ty == '[String: CLLocationCoordinate2D]': return f'Lists.coordDict("{key}", {lit})'
    if ty in simple: return f'{simple[ty]}("{key}", {lit})'
    m = re.fullmatch(r'\[\(String, \[([A-Za-z_][A-Za-z0-9_.]*)\]\)\]', ty)
    if m and m.group(1) not in PRIM: return f'Lists.decodeGroups("{key}", {lit})', m.group(1)
    m = re.fullmatch(r'\[(\(.*\))\]', ty)
    if m: return f'Lists.rows("{key}")?.map {{ r in {tuple_expr(tuple_parts(m.group(1)))} }} ?? {lit}'
    m = re.fullmatch(r'\[String: \[(\(.*\))\]\]', ty)
    if m: return f'Lists.dictRows("{key}")?.mapValues {{ $0.map {{ r in {tuple_expr(tuple_parts(m.group(1)))} }} }} ?? {lit}'
    m = re.fullmatch(r'\[String: (\(.*\))\]', ty)
    if m: return f'Lists.dictRow("{key}")?.mapValues {{ r in {tuple_expr(tuple_parts(m.group(1)))} }} ?? {lit}'
    m = re.fullmatch(r'\[([A-Za-z_][A-Za-z0-9_.]*)\]', ty)
    if m and m.group(1) not in PRIM: return f'Lists.decode("{key}", {lit})', m.group(1)
    m = re.fullmatch(r'\[String: ([A-Za-z_][A-Za-z0-9_.]*)\]', ty)
    if m and m.group(1) not in PRIM: return f'Lists.decodeDict("{key}", {lit})', m.group(1)
    raise ValueError('type ' + ty)


def main():
    global ROOTDIR, DRY, V, S, SH
    DECL = re.compile(r'^(?P<ind>[ \t]*)(?P<mods>(?:private |fileprivate |public )?(?:static )?)let (?P<name>[A-Za-z_][A-Za-z0-9_]*)(?P<ty>: [^=\n]+?)? = \[', re.M)
    SKIP_NAMES = {'columns', 'roots', 'defaultItems', 'defaultSections', 'defaultBanners', 'defaultSteps', 'defaultGroups', 'baseDefaults',
                  'default_projects', 'default_around', 'default_services', 'default_government', 'default_elections', 'neighborhoods'}
    def clean_json(v):
        if isinstance(v, dict): return {str(k): clean_json(x) for k, x in v.items() if k != '__type'}
        if isinstance(v, list): return [clean_json(x) for x in v]
        return v

    reg = {}; structs = {}; report = []
    files = sorted(glob.glob(V + '/*.swift') + glob.glob(S + '/*.swift') + glob.glob(SH + '/*.swift'))
    total = 0
    for fn in files:
        stem = os.path.basename(fn)[:-6]
        s = open(fn).read(); out = ''; i = 0; n = 0
        for m in DECL.finditer(s):
            if m.start() < i: continue
            name = m.group('name')
            if name in SKIP_NAMES: continue
            # instance-level tables only at type scope (4 spaces); statics anywhere
            if 'static' not in m.group('mods') and m.group('ind') != '    ': continue
            try: end = literal_end(s, m.end() - 1)
            except ValueError: continue
            lit = s[m.end() - 1:end]
            # a closure / trailing call after the literal (e.g. ].map {...}) is not a plain table
            rest = s[end:end + 2]
            if rest.startswith('.') : continue
            try: value = parse_literal(lit)
            except ValueError as e:
                report.append(('unparsed', stem, name, str(e)[:60])); continue
            ty = m.group('ty')[2:].strip() if m.group('ty') else None
            if ty is None:
                try: ty = infer_type(value)
                except ValueError as e: report.append(('untyped', stem, name, str(e))); continue
            key = f'{stem}.{name}'
            if key in reg: key = f'{stem}.{name}.{s.count(chr(10), 0, m.start()) + 1}'
            try: r = expr_for(ty, key, lit, value)
            except ValueError as e: report.append(('type', stem, name, str(e)[:70])); continue
            if isinstance(r, tuple): expr, st = r; structs.setdefault(st, []).append(key)
            else: expr = r
            def hexify(v, t):
                t = re.sub(r'\s+', ' ', t.strip())
                mm = re.fullmatch(r'\[(\(.*\))\]', t)
                if mm and isinstance(v, list):
                    cols = [ty2 for _, ty2 in tuple_parts(mm.group(1))]
                    return [[('#%06x' % c if cols[j] == 'UInt32' and isinstance(c, int) else c) for j, c in enumerate(row)] if isinstance(row, list) else row for row in v]
                return v
            reg[key] = clean_json(hexify(value, ty))
            mods = m.group('mods')
            decl = f'{m.group("ind")}{mods}var {name}: {ty} {{ {expr} }}'
            out += s[i:m.start()] + decl
            i = end; n += 1
        out += s[i:]
        if n and not DRY: open(fn, 'w').write(out)
        total += n
    CONFORM = [('JobsView.swift', 'private struct Source: Identifiable {', 'private struct Source: Identifiable, Decodable {'),
               ('NYCHAView.swift', 'private struct NYCHAStep: Identifiable {', 'private struct NYCHAStep: Identifiable, Decodable {'),
               ('NYCHAView.swift', 'private struct NYCHACode: Identifiable {', 'private struct NYCHACode: Identifiable, Decodable {'),
               ('ReviewProcessView.swift', 'struct Stage: Identifiable {', 'struct Stage: Identifiable, Decodable {'),
               ('BidsOrgsView.swift', '''    init(title: String, steps: [String] = [], body: String = "") {''',
                '''    private enum K: String, CodingKey { case title, steps, body }
        init(from d: Decoder) throws {
            let c = try d.container(keyedBy: K.self)
            self.init(title: try c.decode(String.self, forKey: .title), steps: try c.decodeIfPresent([String].self, forKey: .steps) ?? [], body: try c.decodeIfPresent(String.self, forKey: .body) ?? "")
        }
        init(title: String, steps: [String] = [], body: String = "") {'''),
               ('BidsOrgsView.swift', 'private struct BidExplainer: Identifiable {', 'private struct BidExplainer: Identifiable, Decodable {'),
               ('BKBoards.swift', 'Lists.decode("BKBoards.labelSpots"', 'Lists.coords("BKBoards.labelSpots"'),
               ('HelpView.swift', 'struct Item: Identifiable { let id = UUID(); let symbol: String; let title: String; let lines: [String]', 'struct Item: Identifiable, Decodable { let id = UUID(); let symbol: String; let title: String; let lines: [String]'),
               ('HelpView.swift', '''        init(symbol: String, title: String, lines: [String]) { self.symbol = symbol; self.title = title; self.lines = lines }''',
                '''        init(symbol: String, title: String, lines: [String]) { self.symbol = symbol; self.title = title; self.lines = lines }
            private enum K: String, CodingKey { case symbol, title, lines }
            init(from d: Decoder) throws {
                let c = try d.container(keyedBy: K.self)
                self.init(symbol: (try? c.decode(String.self, forKey: .symbol)) ?? "circle", title: try c.decode(String.self, forKey: .title), lines: (try? c.decode([String].self, forKey: .lines)) ?? [])
            }'''),
               ('UseOfLand.swift', 'struct Item: Identifiable { let title: String; let sub: String; let symbol: String; let route: String; var cover: String? = nil;', 'struct Item: Identifiable, Decodable { let title: String; let sub: String; let symbol: String; let route: String; var cover: String? = nil;')]
    if not DRY:
        dk = os.path.join(V, 'DistrictKit.swift'); t = open(dk).read()
        if 'extension Lists {' not in t: open(dk, 'w').write(t + LISTS2)
        for fn, old, new in CONFORM:
            p = os.path.join(V, fn)
            if os.path.exists(p):
                t = open(p).read()
                if old in t and new not in t: open(p, 'w').write(t.replace(old, new, 1))
    json.dump({'lists': reg, 'structs': structs}, open(os.path.join(ROOTDIR, '..', f'lists-{os.path.basename(os.path.abspath(ROOTDIR))}-2.json'), 'w'), ensure_ascii=False, indent=1)
    print('tables rerouted', total, '| struct types needing Decodable:', {k: len(v) for k, v in structs.items()})
    for r in report: print('  SKIP', r)


if __name__ == '__main__':
    main()
