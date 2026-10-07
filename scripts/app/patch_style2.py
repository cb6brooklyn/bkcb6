#!/usr/bin/env python3
"""Every color, map badge and remaining screen string written in the app's code reads from the files, with the code's
value as the fallback: colors and badges from civic/mapstyle.json (colors / icons), strings from civic/copy.json,
the type scale and font names from mapstyle numbers/labels. Run: patch_style2.py <app dir>. Writes style-keys-<app>.json."""
import re, sys, os, glob, json, hashlib

ROOT = sys.argv[1]; V = os.path.join(ROOT, 'App/Views'); THEME = os.path.join(ROOT, 'App/Theme.swift'); KIT = os.path.join(V, 'DistrictKit.swift')
app = os.path.basename(os.path.dirname(os.path.abspath(ROOT)))
reg = {'colors': {}, 'icons': {}, 'strings': {}}
def h8(t): return hashlib.sha1(t.encode()).hexdigest()[:8]

def hex_of(lit):
    m = re.match(r'(?:UI)?Color\(red: ([^,]+), green: ([^,]+), blue: ([^,)]+)(?:, (?:opacity|alpha): ([^)]+))?\)', lit)
    def num(x):
        x = x.strip()
        if '/' in x: a, b = x.split('/'); return float(a) / float(b)
        return float(x)
    if m:
        try: r, g, b = (num(m.group(i)) for i in (1, 2, 3)); a = num(m.group(4)) if m.group(4) else 1
        except ValueError: return ''
        s = '#%02x%02x%02x' % (round(r * 255), round(g * 255), round(b * 255))
        return s + ('%02x' % round(a * 255) if a != 1 else '')
    m = re.search(r'"(#[0-9A-Fa-f]{6,8})"', lit)
    return m.group(1) if m else ''

# ---- 1. colors in the views ----
COLOR = re.compile(r'(?<![\w.])(?:UIColor|Color)\(red: [^()]*?\)|(?<![\w.])Color\(hex: "#[0-9A-Fa-f]+"\)|(?<![\w])(?:DK\.hex|DK\.uiHex|Color\.fhHex|\.fhHex|\.cpHex|evHex|bidColor|c311Color|permitColor)\("#[0-9A-Fa-f]+"\)')
def wrap_colors(s, stem):
    out = ''; i = 0; n = 0
    for m in COLOR.finditer(s):
        if m.start() < i: continue
        before = s[max(0, m.start() - 80):m.start()]
        line_start = s.rfind('\n', 0, m.start()) + 1; line = s[line_start:s.find('\n', m.start())]
        # already read from a file, or a table's fallback (those are in lists.json), or a static table literal
        if re.search(r'MapStyle\.color\("[^"]*", $', before) or 'Lists.' in line or re.match(r'\s*(private |fileprivate )?(static )?var \w+: \[', line) or 'MapStyle.color(' in line and line.count('MapStyle.color(') >= line.count('Color('):
            continue
        lit = m.group(0)
        if not hex_of(lit): continue
        is_ui = lit.startswith('UIColor') or lit.startswith('DK.uiHex')
        key = f'{stem}.c.{h8(lit)}'
        reg['colors'][key] = {'hex': hex_of(lit), 'file': stem, 'line': line.strip()[:120]}
        out += s[i:m.start()] + f'MapStyle.color("{key}", {lit})'
        i = m.end(); n += 1
    return out + s[i:], n

# ---- 2. map badges ----
ICON = re.compile(r'icon: (\.image\("[^"]*"\)|\.symbol\("[^"]*", "#[0-9A-Fa-f]+"\)|\.labeled\("[^"]*", [^()]*?\)|DKIcon\.school\([^()]*\))')
def wrap_icons(s, stem):
    out = ''; i = 0; n = 0
    for m in ICON.finditer(s):
        if m.start() < i: continue
        before = s[max(0, m.start() - 60):m.start()]
        lit = m.group(1)
        if 'MapStyle.icon(' in s[m.start():m.start() + 40] or re.search(r'MapStyle\.icon\("[^"]*", $', before): continue
        key = f'{stem}.i.{h8(lit)}'
        reg['icons'][key] = {'icon': lit, 'file': stem}
        out += s[i:m.start()] + f'icon: MapStyle.icon("{key}", {lit})'
        i = m.end(); n += 1
    return out + s[i:], n

# ---- 3. strings still written in Text("...") ----
TEXT = re.compile(r'Text\("((?:[^"\\]|\\.)*)"\)')
def wrap_text(s, stem):
    out = ''; i = 0; n = 0
    for m in TEXT.finditer(s):
        if m.start() < i: continue
        t = m.group(1)
        if not re.search(r'[A-Za-z]', t) or '\\(' in t: continue
        key = f'{stem}.{h8(t)}'
        reg['strings'][key] = t
        out += s[i:m.start()] + f'Text(LocalizedStringKey(Copy.t("{key}", "{t}")))'
        i = m.end(); n += 1
    return out + s[i:], n

tc = ti = tt = 0
for fn in sorted(glob.glob(V + '/*.swift')):
    stem = os.path.basename(fn)[:-6]
    s = open(fn).read(); o = s
    s, a = wrap_colors(s, stem); s, b = wrap_icons(s, stem); s, c = wrap_text(s, stem)
    tc += a; ti += b; tt += c
    if s != o: open(fn, 'w').write(s)

# ---- 4. the theme: colors, type scale and font names ----
t = open(THEME).read(); o = t
for name in ('cb6Navy', 'cb6NavyDeep', 'cb6Orange', 'cb6Paper', 'cb6Ink', 'cb6Muted', 'cb6Rule', 'parksGreen'):
    m = re.search(r'static let %s = (Color\(red: [^)]*\))' % name, t)
    if m:
        reg['colors'][f'theme.{name}'] = {'hex': hex_of(m.group(1)), 'file': 'Theme', 'line': f'Color.{name}'}
        t = t.replace(m.group(0), f'static var {name}: Color {{ MapStyle.color("theme.{name}", {m.group(1)}) }}')
if 'theme.textScale' not in t:
    t = t.replace('''    static func sans(_ size: CGFloat, _ weight: Font.Weight = .regular) -> Font {
        switch weight {
        case .bold, .heavy, .black, .semibold: return .custom("DMSans-Bold", size: size)
        case .medium: return .custom("DMSans-Medium", size: size)
        default: return .custom("DMSans-Regular", size: size)
        }
    }
    static func mono(_ size: CGFloat, _ weight: Font.Weight = .regular) -> Font {
        weight == .regular ? .custom("DMMono-Regular", size: size) : .custom("DMMono-Medium", size: size)
    }''', '''    /// Type scale and font names from civic/mapstyle.json: numbers "theme.textScale", labels "theme.font.sansBold" etc.
    static var scale: CGFloat { MapStyle.number("theme.textScale", CGFloat(1)) }
    static func sans(_ size: CGFloat, _ weight: Font.Weight = .regular) -> Font {
        switch weight {
        case .bold, .heavy, .black, .semibold: return .custom(MapStyle.label("theme.font.sansBold", "DMSans-Bold"), size: size * scale)
        case .medium: return .custom(MapStyle.label("theme.font.sansMedium", "DMSans-Medium"), size: size * scale)
        default: return .custom(MapStyle.label("theme.font.sans", "DMSans-Regular"), size: size * scale)
        }
    }
    static func mono(_ size: CGFloat, _ weight: Font.Weight = .regular) -> Font {
        weight == .regular ? .custom(MapStyle.label("theme.font.mono", "DMMono-Regular"), size: size * scale) : .custom(MapStyle.label("theme.font.monoMedium", "DMMono-Medium"), size: size * scale)
    }''')
if t != o: open(THEME, 'w').write(t)

# ---- 5. MapStyle caches parsed colors, so theme colors cost a dictionary lookup ----
k = open(KIT).read(); ok = k
if 'colorCache' not in k:
    k = k.replace('''    static func reset() { lock.lock(); cache = nil; lock.unlock() }
    static func section(_ name: String) -> [String: Any] { file[name] as? [String: Any] ?? [:] }''', '''    static func reset() { lock.lock(); cache = nil; colorCache = [:]; colorMiss = []; lock.unlock() }
    static func section(_ name: String) -> [String: Any] { file[name] as? [String: Any] ?? [:] }
    private static var colorCache: [String: UIColor] = [:]
    private static var colorMiss: Set<String> = []
    /// The file's color for a key, parsed once.
    static func fileColor(_ key: String) -> UIColor? {
        lock.lock()
        if let c = colorCache[key] { lock.unlock(); return c }
        if colorMiss.contains(key) { lock.unlock(); return nil }
        lock.unlock()
        let c = (section("colors")[key] as? String).flatMap(hex)
        lock.lock(); if let c { colorCache[key] = c } else { colorMiss.insert(key) }; lock.unlock()
        return c
    }''', 1)
    k = k.replace('''    static func color(_ key: String, _ fallback: UIColor) -> UIColor {
        if let s = section("colors")[key] as? String, let c = hex(s) { return c }
        return fallback
    }
    static func color(_ key: String, _ fallback: Color) -> Color {
        if let s = section("colors")[key] as? String, let c = hex(s) { return Color(uiColor: c) }
        return fallback
    }''', '''    static func color(_ key: String, _ fallback: UIColor) -> UIColor { fileColor(key) ?? fallback }
    static func color(_ key: String, _ fallback: Color) -> Color { fileColor(key).map { Color(uiColor: $0) } ?? fallback }''', 1)
    assert 'fileColor(key) ?? fallback' in k, 'mapstyle color'
if k != ok: open(KIT, 'w').write(k)

json.dump(reg, open(os.path.join(ROOT, '..', f'style-keys-{app}.json'), 'w'), ensure_ascii=False, indent=1)
print(app, 'colors wrapped', tc, '| badges wrapped', ti, '| strings wrapped', tt, '| theme colors', sum(1 for x in reg['colors'] if x.startswith('theme.')))
