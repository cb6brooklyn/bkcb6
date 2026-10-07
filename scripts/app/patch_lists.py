import re,sys,os,glob,json
H='/Users/user301938'
app=sys.argv[1]; P=f'{H}/{app}/BKCB6/App/'
reg={}
LISTS='''

// MARK: - Lists from a file

/// Every table written in the code (categories, labels, aliases, route lists, lookup tables) can be replaced from
/// civic/lists.json on bkcb6.app, by name. The table in the code is the fallback when the file has no entry.
enum Lists {
    private static var cache: [String: Any]?
    private static let lock = NSLock()
    private static var observing = false
    private static func entry(_ key: String) -> Any? {
        lock.lock(); defer { lock.unlock() }
        if !observing {
            observing = true
            NotificationCenter.default.addObserver(forName: DataPack.notification, object: nil, queue: nil) { _ in
                lock.lock(); cache = nil; lock.unlock()
            }
        }
        if cache == nil { cache = ((DK.json("lists") as? [String: Any])?["lists"] as? [String: Any]) ?? [:] }
        return cache?[key]
    }
    static func dict(_ key: String, _ fallback: [String: String]) -> [String: String] { (entry(key) as? [String: String]) ?? fallback }
    static func dictList(_ key: String, _ fallback: [String: [String]]) -> [String: [String]] { (entry(key) as? [String: [String]]) ?? fallback }
    static func strings(_ key: String, _ fallback: [String]) -> [String] { (entry(key) as? [String]) ?? fallback }
    static func pairs(_ key: String, _ fallback: [(String, String)]) -> [(String, String)] {
        guard let rows = entry(key) as? [[String]] else { return fallback }
        return rows.filter { $0.count == 2 }.map { ($0[0], $0[1]) }
    }
}
'''
STRLIT=r'"(?:[^"\\]|\\.)*"'
def literal_only(body):
    # the table holds only string literals, commas, colons, brackets, parens and whitespace: exportable as JSON
    return re.fullmatch(r'(?:\s|,|:|\(|\)|\[|\]|'+STRLIT+r')*', body) is not None
def parse_body(kind, body):
    strs=[json.loads(m.group(0).replace("\\'", "'")) if True else None for m in re.finditer(STRLIT, body)]
    if kind=='dict': return {strs[i]:strs[i+1] for i in range(0,len(strs),2)}
    if kind=='pairs': return [[strs[i],strs[i+1]] for i in range(0,len(strs),2)]
    if kind=='strings': return strs
    if kind=='dictList':
        out={};
        for m in re.finditer(r'('+STRLIT+r')\s*:\s*\[((?:\s|,|'+STRLIT+r')*)\]', body):
            out[json.loads(m.group(1))]=[json.loads(x.group(0)) for x in re.finditer(STRLIT, m.group(2))]
        return out
pat=re.compile(r'^(?P<ind>[ \t]*)(?P<priv>private )?static let (?P<name>\w+): (?P<type>\[String: String\]|\[String: \[String\]\]|\[String\]|\[\(String, String\)\]) = \[', re.M)
total=0
for fn in sorted(glob.glob(P+'Views/*.swift')+glob.glob(P+'Services/*.swift')):
    stem=os.path.basename(fn)[:-6]
    s=open(fn).read(); out=''; i=0; n=0
    for m in pat.finditer(s):
        if m.start()<i: continue
        # find the end of the literal: balanced brackets, skipping strings
        k=m.end(); depth=1; instr=False
        while k<len(s) and depth>0:
            c=s[k]
            if instr:
                if c=='\\': k+=1
                elif c=='"': instr=False
            else:
                if c=='"': instr=True
                elif c=='[': depth+=1
                elif c==']': depth-=1
            k+=1
        body=s[m.end():k-1]
        kind={'[String: String]':'dict','[String: [String]]':'dictList','[String]':'strings','[(String, String)]':'pairs'}[m.group('type')]
        key=f'{stem}.{m.group("name")}'
        if literal_only(body):
            try: reg[key]=parse_body(kind, body)
            except Exception as e: pass
        decl=f'{m.group("ind")}{m.group("priv") or ""}static var {m.group("name")}: {m.group("type")} {{ Lists.{kind}("{key}", ['
        out+=s[i:m.start()]+decl+body+']) }'
        i=k; n+=1
    out+=s[i:]
    if n: open(fn,'w').write(out); total+=n
dk=P+'Views/DistrictKit.swift'; s=open(dk).read()
if 'enum Lists ' not in s and 'enum Lists{' not in s: open(dk,'w').write(s+LISTS)
json.dump(reg,open(f'{H}/lists-{app}.json','w'),ensure_ascii=False,indent=1)
print(app,'tables rerouted',total,'exported',len(reg))
