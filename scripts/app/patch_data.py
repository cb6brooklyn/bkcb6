import re,sys,os,glob
H='/Users/user301938'
app=sys.argv[1]; P=f'{H}/{app}/BKCB6/App/'
# 1. DataPack
open(P+'Services/DataPack.swift','w').write(open(H+'/DataPack.swift').read()); print('DataPack written')
# 2. Every Bundle.main.url(forResource: ...) read of data or images goes through the cache first.
n=0
for fn in glob.glob(P+'Views/*.swift')+glob.glob(P+'*.swift')+glob.glob(P+'Services/*.swift'):
    if fn.endswith('Services/DataPack.swift'): continue
    s=open(fn).read(); o=s
    # keep fonts and the tile folders on the bundle; those are handled on their own
    def rep(m):
        inner=m.group(1)
        if 'subdirectory: "Fonts"' in inner: return m.group(0)
        if 'withExtension: nil, subdirectory: "civic"' in inner and '"tiles"' in inner: return m.group(0)
        if 'withExtension: nil, subdirectory: "civic/lotstiles"' in inner: return m.group(0)
        return 'DataPack.url(forResource:'+inner+')'
    s=re.sub(r'Bundle\.main\.url\(forResource:((?:[^()]|\([^()]*\))*)\)',rep,s)
    if s!=o:
        open(fn,'w').write(s); n+=s.count('DataPack.url(forResource:')-o.count('DataPack.url(forResource:')
print('bundle reads rerouted',n)
# 3. Tiles: a downloaded tile wins over the bundled one.
fn=P+'Views/CB6Base.swift'; s=open(fn).read()
if 'let rel: String' not in s:
    if 'init(lots layer: String)' in s:
        s=s.replace("""    /// The folder of z/x/y.png tiles this overlay draws: the base map, or a lot layer under civic/lotstiles.
    let dir: URL?""","""    /// The folder of z/x/y.png tiles this overlay draws: the base map, or a lot layer under civic/lotstiles.
    let dir: URL?
    /// The same folder as a bundle-relative path, so a tile downloaded from bkcb6.app is read before the shipped one.
    let rel: String
    private func tile(_ z: Int, _ x: Int, _ y: Int) -> URL {
        DataPack.url("\\(rel)/\\(z)/\\(x)/\\(y).png") ?? (dir ?? URL(fileURLWithPath: "/")).appendingPathComponent("\\(z)/\\(x)/\\(y).png")
    }""")
        s=s.replace('        dir = Self.dir; upscale = 3\n','        dir = Self.dir; upscale = 3; rel = "civic/tiles"\n')
        s=s.replace('        dir = Bundle.main.url(forResource: layer, withExtension: nil, subdirectory: "civic/lotstiles"); upscale = 4\n','        dir = Bundle.main.url(forResource: layer, withExtension: nil, subdirectory: "civic/lotstiles"); upscale = 4; rel = "civic/lotstiles/" + layer\n')
        s=s.replace("""    override func url(forTilePath p: MKTileOverlayPath) -> URL {
        (dir ?? URL(fileURLWithPath: "/")).appendingPathComponent("\\(p.z)/\\(p.x)/\\(p.y).png")
    }""","""    override func url(forTilePath p: MKTileOverlayPath) -> URL { tile(p.z, p.x, p.y) }""")
        s=s.replace("""            let u = (dir ?? URL(fileURLWithPath: "/")).appendingPathComponent("\\(z)/\\(x)/\\(y).png")""","""            let u = tile(z, x, y)""")
    else:
        s=s.replace("""    static let dir: URL? = Bundle.main.url(forResource: "tiles", withExtension: nil, subdirectory: "civic")""","""    static let dir: URL? = Bundle.main.url(forResource: "tiles", withExtension: nil, subdirectory: "civic")
    /// A tile downloaded from bkcb6.app is read before the shipped one.
    private func tile(_ z: Int, _ x: Int, _ y: Int) -> URL {
        DataPack.url("civic/tiles/\\(z)/\\(x)/\\(y).png") ?? (Self.dir ?? URL(fileURLWithPath: "/")).appendingPathComponent("\\(z)/\\(x)/\\(y).png")
    }""")
        s=s.replace("""    override func url(forTilePath p: MKTileOverlayPath) -> URL {
        (Self.dir ?? URL(fileURLWithPath: "/")).appendingPathComponent("\\(p.z)/\\(p.x)/\\(p.y).png")
    }""","""    override func url(forTilePath p: MKTileOverlayPath) -> URL { tile(p.z, p.x, p.y) }""")
        s=s.replace("""            let u = (Self.dir ?? URL(fileURLWithPath: "/")).appendingPathComponent("\\(z)/\\(x)/\\(y).png")""","""            let u = tile(z, x, y)""")
assert s.count('tile(z, x, y)')==1 and 'tile(p.z, p.x, p.y)' in s, 'CB6Base patch'
open(fn,'w').write(s); print('tiles ok')
# 4. The embedded site page reads its bundled files through the cache too.
fn=P+'Views/SiteCard.swift'; s=open(fn).read()
assert 'DataPack.url(forResource: "site/" + rel, withExtension: nil)' in s, 'sitecard'
print('sitecard ok')
