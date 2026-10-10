import re,sys,os
P=os.path.expanduser('~/'+sys.argv[1]+'/BKCB6/App/Views/')
add=open(os.path.expanduser('~/dkspeed.swift')).read()
def sub(fn,old,new,count=1,regex=False):
    p=P+fn; s=open(p).read()
    if regex:
        s2,n=re.subn(old,new,s,count=count)
    else:
        n=s.count(old); s2=s.replace(old,new)
    if n<1: print('MISS',fn,old[:70]); sys.exit(1)
    open(p,'w').write(s2); print('ok',fn,n)
# data
sub('DistrictKit.swift','var speed: [(limit: String, street: String, line: [[CLLocationCoordinate2D]])] = []','var speed: [DKSpeed.Seg] = []')
sub('DistrictKit.swift','b.speed = feats("speed").map { f in (s(p(f), 0), s(p(f), 1), lines(f)) }','b.speed = feats("speed").map { f in (s(p(f), 0), s(p(f), 1), lines(f), s(p(f), 2) == "1") }')
blk=r'(?P<i>[ \t]*)for \(lim, items\) in Dictionary\(grouping: (?P<src>[\w.]+), by: \{ \$0\.limit \}\) \{\n[ \t]*out\.append\(DKLayer\(id: "speed-\\\(lim\)", lines: items\.flatMap \{ \$0\.line \}, color: DKTransport\.speedColor\(lim\), width: 3\)\)\n[ \t]*\}'
sub('DistrictKit.swift',blk,r'\g<i>out += DKSpeed.layers(\g<src>)',regex=True)
sub('CB6MapView.swift',blk,r'\g<i>out += DKSpeed.layers(\g<src>)',regex=True)
# DKMap legend
sub('DistrictKit.swift',r'ForEach\(\["20", "25", "30", "35", "45", "0"\], id: \\\.self\) \{ s in\n[ \t]*DKLegendDot\(color: Color\(uiColor: DKTransport\.speedColor\(s\)\), text: [^\n]*\n[ \t]*\}',
    'ForEach(Array(DKSpeed.key(b.speed).enumerated()), id: \\.offset) { _, it in DKLegendDot(color: it.1, text: it.0) }',regex=True)
# BKBoards and ProfileMap: their own 3-color version
bk=r'(?P<i>[ \t]*)for \(limit, group\) in Dictionary\(grouping: (?P<src>[\w.\\()]+), by: \\\.limit\) \{\n(?:[ \t]*let [^\n]*\n)?[ \t]*out\.append\(DKLayer\(id: "speed-\\\(limit\)"[^\n]*\n[ \t]*\}'
if os.path.exists(P+'BKBoards.swift'):
    sub('BKBoards.swift',bk,r'\g<i>out += DKSpeed.layers(\g<src>)',regex=True)
sub('ProfileMap.swift',bk,r'\g<i>out += DKSpeed.layers(\g<src>)',regex=True)
# keys
p=P+'CB6MapView.swift'; s=open(p).read()
old='        let items: [(String, Color)] = zoneKeys + luKeys.map { ($0, Palette.landUse($0)) }'
assert s.count(old)==1, 'cb6 key'
s=s.replace(old,'        let speedKeys: [(String, Color)] = overlays.contains(.speed) ? DKSpeed.key(DKTransport.board(cd).speed) : []\n'+old.replace('zoneKeys + ','zoneKeys + speedKeys + '))
open(p,'w').write(s); print('ok cb6 key')
if os.path.exists(P+'BKBoards.swift'):
    p=P+'BKBoards.swift'; s=open(p).read()
    i=s.index('    private var key: some View {'); j=s.index('        return Group {',i)
    s=s[:j]+('        if showSpeed { items += DKSpeed.key(transit.speed) }\n' if 'private var transit:' in s else '        if showSpeed { items += DKSpeed.key(DKTransport.board(cd).speed) }\n')+s[j:]
    open(p,'w').write(s); print('ok bk key')
p=P+'ProfileMap.swift'; s=open(p).read()
old='            Text("Turn layers on and off below. Tap an official\'s logo or a board\'s seal for its profile.")'
assert s.count(old)==1,'pm'
s=s.replace(old,'            if layers.contains("speed") { DKSpeedKey(segs: cds.flatMap { DKTransport.board($0).speed }).padding(.top, 8) }\n'+old)
open(p,'w').write(s); print('ok pm key')
p=P+'DistrictKit.swift'; s=open(p).read()
if 'enum DKSpeed' not in s: open(p,'a').write(add); print('ok appended')
