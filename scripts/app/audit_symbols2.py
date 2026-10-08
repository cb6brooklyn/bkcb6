"""The rest of the SF symbol names in the code (tab icons, hub rows, tool rows, tuples, chevrons picked by a condition,
"symbol:" and "sym:" arguments, enum icon properties) read from the file the same way: MapStyle.symbol("<File>.s.<id>", "name").
A dotted lowercase literal whose first word is an SF symbol family (house, chevron, map, person, ...) is one, unless it
is a file name, a key, a case pattern or a comparison. Single words are wrapped only in enum icon properties
("case .home: return "calendar""). Adds to the registry audit_symbols.py wrote. audit_symbols2.py <app dir> <registry>"""
import re, sys, os, glob, json, hashlib
R = sys.argv[1]; out = sys.argv[2]
def h8(t): return hashlib.sha1(t.encode()).hexdigest()[:8]
reg = json.load(open(out)) if os.path.exists(out) else {}
ROOTS = set('''chevron arrow arrowshape arrowtriangle house building person figure map mappin location pin tram bus car bicycle scooter ferry
airplane tree leaf trash phone envelope paperplane link globe info questionmark exclamationmark checkmark xmark plus minus gear list line text
doc book bookmark newspaper photo camera video play pause square rectangle circle capsule shield wrench hammer paintbrush drop flame sun moon
cloud wind snowflake thermometer chart dollarsign number hand eye ear mic speaker bell flag star heart magnifyingglass clock calendar timer
lock key tag cart bag gift crown graduationcap books ticket film tv display printer wifi bolt battery power lightbulb bed chair table cup fork
wineglass takeoutbag carrot fish pawprint bird dog cat sailboat parkingsign fuelpump road signpost megaphone music sparkles wand network point
scalemass water waves mountain safari storefront briefcase seal checkerboard ellipsis slash bubble quote message creditcard banknote sportscourt
basketball football baseball soccerball tennis medal trophy rosette umbrella tornado hurricane smoke aqi humidity rainbow sparkle gamecontroller
puzzlepiece folder tray archivebox server desktopcomputer laptopcomputer iphone ipad keyboard cursorarrow externaldrive opticaldisc waveform
headphones hifispeaker antenna binoculars scissors paperclip pencil highlighter eraser lasso crop rotate slider dial switch toggle alarm stopwatch
hourglass repeat shuffle forward backward gobackward goforward return multiply divide equal lessthan greaterthan percent function sum textformat
bold italic underline strikethrough note ruler personalhotspot touchid faceid screwdriver memorychip cpu sdcard simcard airplayaudio airplayvideo
cable powerplug mouse trackpad scanner tropicalstorm dust theatermasks paintpalette pianokeys guitars dumbbell lamp birthday tortoise hare ant
ladybug lizard swift app oval scribble checklist rectangle square squares star doc questionmark globe fossil atom brain lungs heart cross pills
bandage stethoscope syringe testtube microbe allergens ladybug leaf tree camera bolt'''.split())
NOT_LAST = {'json', 'js', 'css', 'html', 'png', 'jpg', 'jpeg', 'gz', 'geojson', 'ttf', 'txt', 'md', 'plist', 'pdf', 'svg', 'mp4', 'm4a', 'swift', 'py', 'app', 'com', 'nyc', 'org', 'gov', 'us', 'io', 'net'}
SINGLE = set('''calendar circle clock gear bell star heart flag globe link trash pencil magnifyingglass bookmark book doc folder camera photo play
pause plus minus xmark checkmark info wrench hammer tram car bus bicycle leaf tree sun moon cloud wind drop flame bolt wifi lock key tag cart
gift crown trophy medal ticket film tv printer envelope paperplane megaphone music mic speaker eye ear ferry airplane scooter signpost square
shield newspaper briefcase dollarsign safari storefront wineglass sparkles lightbulb thermometer snowflake umbrella map location mappin pin timer
stopwatch hourglass ellipsis capsule questionmark exclamationmark building house person figure'''.split())
BAD_BEFORE = re.compile(r'(case |== |!= |forKey: |withExtension: |forResource: |subdirectory: |appendingPathComponent\(|Copy\.[tf]\(|MapStyle\.\w+\(|Lists\.\w+\(|\bT\(|string: |hasPrefix\(|hasSuffix\(|contains\(|of: |with: |separator: |identifier: |named: |name: |key: |id: |slug: |dataset: |route: |dest: |NSLog\(|print\(|accessibilityIdentifier\(|\.tag\(|\.id\(|AppStorage\(|SceneStorage\()\s*$')
DOTTED = re.compile(r'"([a-z0-9]+(?:\.[a-z0-9]+)+)"')
SINGLE_RET = re.compile(r'(case \.\w+: return )"([a-z]+)"')
n = 0
for f in sorted(glob.glob(os.path.join(R, 'App', '**', '*.swift'), recursive=True)):
    name = os.path.splitext(os.path.basename(f))[0]
    s = open(f).read(); o = s
    def rep(m):
        global n
        lit = m.group(1); parts = lit.split('.')
        if parts[0] not in ROOTS or parts[-1] in NOT_LAST: return m.group(0)
        before = s[max(0, m.start() - 40):m.start()]
        if BAD_BEFORE.search(before): return m.group(0)
        if 'symbol("' in before[-10:]: return m.group(0)
        key = f'{name}.s.{h8(lit)}'; reg[key] = lit; n += 1
        return f'MapStyle.symbol("{key}", "{lit}")'
    s = DOTTED.sub(rep, s)
    def rep2(m):
        global n
        if m.group(2) not in SINGLE: return m.group(0)
        key = f'{name}.s.{h8(m.group(2))}'; reg[key] = m.group(2); n += 1
        return f'{m.group(1)}MapStyle.symbol("{key}", "{m.group(2)}")'
    s = SINGLE_RET.sub(rep2, s)
    if s != o: open(f, 'w').write(s)
json.dump(reg, open(out, 'w'), indent=1, sort_keys=True)
print('symbols2', n, 'more replaced,', len(reg), 'keys')
