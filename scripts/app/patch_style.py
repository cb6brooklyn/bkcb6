import re,sys,os,glob
H='/Users/user301938'
app=sys.argv[1]; P=f'{H}/{app}/BKCB6/App/Views/'
report=[]
def rd(f): return open(P+f).read()
def wr(f,s): open(P+f,'w').write(s)
def slug(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')

# ---- 1. MapStyle itself, DKDot.color as var, DKLayerMap applies the file
s=rd('DistrictKit.swift')
if 'enum MapStyle' not in s: s+=open(H+'/mapstyle.swift').read()
s=s.replace('struct DKDot: Hashable {\n    let coord: CLLocationCoordinate2D\n    let title: String\n    let subtitle: String\n    let color: UIColor','struct DKDot: Hashable {\n    let coord: CLLocationCoordinate2D\n    let title: String\n    let subtitle: String\n    var color: UIColor')
assert 'var color: UIColor\n    var size: CGFloat = 10' in s, 'DKDot'
if 'var style: String = ""' not in s:
    s=s.replace('struct DKLayerMap: UIViewRepresentable {\n    let layers: [DKLayer]\n','struct DKLayerMap: UIViewRepresentable {\n    let layers: [DKLayer]\n    /// Which screen this map is on, for civic/mapstyle.json ("boards", "profile", "cb6map"...).\n    var style: String = ""\n',1)
    s=s.replace('        m.removeOverlays(m.overlays)\n        m.removeAnnotations(m.annotations)\n        for l in layers {','        m.removeOverlays(m.overlays)\n        m.removeAnnotations(m.annotations)\n        for l in layers.map({ MapStyle.apply($0, screen: style) }) {',1)
assert 'MapStyle.apply($0, screen: style)' in s, 'DKLayerMap apply'
wr('DistrictKit.swift',s); report.append('DKLayerMap applies mapstyle')

# ---- 2. style: on every DKLayerMap call
slugs={'BKBoards.swift':'boards','CB6MapView.swift':'cb6map','ProfileMap.swift':'profile','DistrictKit.swift':'district','Feeds.swift':'feeds','BlockCards.swift':'blocks','AddressCardCity.swift':'address','ExploreViews.swift':'explore','LandmarksSection.swift':'landmarks','LiquorApplicants.swift':'liquor','UOLHousing.swift':'housing','UOLZoning.swift':'uolzoning','UseOfLand.swift':'useofland','WeatherView.swift':'weather'}
n=0
for fn in sorted(glob.glob(P+'*.swift')):
    s=open(fn).read()
    if 'DKLayerMap(layers:' not in s: continue
    sl=slugs.get(os.path.basename(fn), slug(os.path.basename(fn)[:-6]))
    out=''; i=0
    while True:
        j=s.find('DKLayerMap(layers:',i)
        if j<0: out+=s[i:]; break
        k=j+len('DKLayerMap(layers:'); depth=0
        # scan to the end of the layers argument at depth 0
        while k<len(s):
            ch=s[k]
            if ch in '([{': depth+=1
            elif ch in ')]}':
                if depth==0: break
                depth-=1
            elif ch==',' and depth==0: break
            k+=1
        seg=s[j:k]
        if 'style:' in s[j:k+40]: out+=s[i:k]; i=k; continue
        out+=s[i:k]+f', style: "{sl}"'; i=k; n+=1
    open(fn,'w').write(out)
report.append(f'DKLayerMap call sites given a screen: {n}')

# ---- 3. Palette (zoning families, land use table)
if os.path.exists(P+'LandUseView.swift'):
    s=rd('LandUseView.swift')
    for name in ['residential','commercial','manufacturing','park','special','otherZone']:
        s=re.sub(r'static let %s\s*=\s*(rgb\(0x[0-9a-fA-F]+\))'%name, lambda m: f'static var {name}: Color {{ MapStyle.color("zoning.{name}", {m.group(1)}) }}', s)
    assert 'static var residential: Color' in s, 'palette'
    def lu(m):
        code,label,col=m.group(1),m.group(2),m.group(3)
        return f'("{code}", MapStyle.label("landuse.{code}", "{label}"), MapStyle.color("landuse.{code}", {col}))'
    s2=re.sub(r'\("(\d\d)",\s*"([^"]+)",\s*(rgb\(0x[0-9a-fA-F]+\))\)', lu, s)
    s2=s2.replace('static let landUseTable: [(code: String, label: String, color: Color)] = [','static var landUseTable: [(code: String, label: String, color: Color)] { [',1)
    # close the computed property: the table ends with "]\n" followed by a blank line or comment; find the first "\n    ]\n" after the declaration
    idx=s2.index('static var landUseTable'); end=s2.index('\n    ]\n',idx)
    s2=s2[:end]+'\n    ] }\n'+s2[end+len('\n    ]\n'):]
    assert s2.count('MapStyle.label("landuse.')==11, 'landuse table'
    wr('LandUseView.swift',s2); report.append('Palette: zoning families and land use table from mapstyle')
    # MapScreens: landUseColors is a static let of the table -> computed
    if os.path.exists(P+'MapScreens.swift'):
        s=rd('MapScreens.swift')
        s=s.replace('static let landUseColors: [(String, Color)] = Palette.landUseTable.map { ($0.label, $0.color) }','static var landUseColors: [(String, Color)] { Palette.landUseTable.map { ($0.label, $0.color) } }')
        wr('MapScreens.swift',s)

# ---- 4. DKLandUse colors/labels (cd-landuse.json) with mapstyle laid over
s=rd('DistrictKit.swift')
s=s.replace('static var labels: [String: String] { root["landuse_labels"] as? [String: String] ?? [:] }','static var labels: [String: String] { MapStyle.merge("landuse.", root["landuse_labels"] as? [String: String] ?? [:], labels: true) }')
s=s.replace('static var colors: [String: String] { root["landuse_colors"] as? [String: String] ?? [:] }','static var colors: [String: String] { MapStyle.merge("landuse.", root["landuse_colors"] as? [String: String] ?? [:]) }')
s=s.replace('static var famColors: [String: String] { root["zone_family_colors"] as? [String: String] ?? [:] }','static var famColors: [String: String] { MapStyle.merge("zoning.", root["zone_family_colors"] as? [String: String] ?? [:]) }')
assert 'MapStyle.merge("landuse.", root["landuse_colors"]' in s, 'dklanduse'

# ---- 5. DKTransport bike/truck colors and labels
def wrap_cases(s, func_sig, keyfmt, kind):
    i=s.index(func_sig); j=s.index('\n    }\n',i)
    body=s[i:j]
    def rep(m):
        case=m.group(1).strip('"'); expr=m.group(2)
        return f'case {m.group(1)}: return MapStyle.{kind}("{keyfmt%case}", {expr})'
    body2=re.sub(r'case ("[^"]+"): return (.+)$', rep, body, flags=re.M)
    return s[:i]+body2+s[j:]
s=wrap_cases(s,'static func bikeColor(_ c: String) -> UIColor {','bike-%s','color')
s=wrap_cases(s,'static func bikeLabel(_ c: String) -> String {','bike-%s','label')
s=wrap_cases(s,'static func truckColor(_ t: String) -> UIColor {','truck-%s','color')
if 'static func truckLabel(_ t: String) -> String {' in s: s=wrap_cases(s,'static func truckLabel(_ t: String) -> String {','truck-%s','label')
assert 'MapStyle.color("bike-I"' in s and 'MapStyle.color("truck-Through"' in s, 'transport colors'
# the truck legend text
s=s.replace('DKLegendDot(color: Color(uiColor: DKTransport.truckColor(t)), text: "\\(t) truck route")','DKLegendDot(color: Color(uiColor: DKTransport.truckColor(t)), text: MapStyle.label("truck-\\(t)", "\\(t) truck route"))')
# BoardTransportView colors and chip titles
if 'private func color(_ l: Layer) -> Color {' in s:
    i=s.index('private func color(_ l: Layer) -> Color {'); j=s.index('\n    }\n',i); body=s[i:j]
    body=re.sub(r'case \.(\w+): return (.+)$', lambda m: f'case .{m.group(1)}: return MapStyle.color("transport.{m.group(1)}", {m.group(2)})', body, flags=re.M)
    s=s[:i]+body+s[j:]
    s=s.replace('DKChip(text: l.rawValue, color: color(l), on: on.contains(l))','DKChip(text: MapStyle.label("transport.\\(l)", l.rawValue), color: color(l), on: on.contains(l))')
    assert 'MapStyle.color("transport.bike"' in s and 'MapStyle.label("transport.\\(l)"' in s, 'transport chips'
# DKSpeed takes mapstyle colors over transit.json
s=s.replace('static func colors(_ c: [String: Any]) -> [String: String] { fallback.merging((c["colors"] as? [String: String]) ?? [:]) { _, new in new } }',
            'static func colors(_ c: [String: Any]) -> [String: String] { MapStyle.merge("speed-", fallback.merging((c["colors"] as? [String: String]) ?? [:]) { _, new in new }) }')
s=s.replace('static func zoneHex(_ c: [String: Any]) -> String { (c["zone"] as? String) ?? "#DC2626" }','static func zoneHex(_ c: [String: Any]) -> String { (MapStyle.section("colors")["speed-zone"] as? String) ?? (c["zone"] as? String) ?? "#DC2626" }')
s=s.replace('static let zoneLabel = "Sammy\'s Law 15 mph school zones"','static var zoneLabel: String { MapStyle.label("speed-zone", "Sammy\'s Law 15 mph school zones") }')
s=s.replace('static func label(_ s: String) -> String { s == "0" ? "No posted limit in DOT data" : "\\(s) mph" }','static func label(_ s: String) -> String { MapStyle.label("speed-" + s, s == "0" ? "No posted limit in DOT data" : "\\(s) mph") }')
assert 'MapStyle.merge("speed-"' in s, 'speed merge'
s=s.replace('    private static func section(_ name: String) -> [String: Any] { file[name] as? [String: Any] ?? [:] }','    static func section(_ name: String) -> [String: Any] { file[name] as? [String: Any] ?? [:] }')
wr('DistrictKit.swift',s); report.append('DKTransport bike/truck/speed colors and labels from mapstyle')

# ---- 6. CB6MapView: every enum color switch and the chip titles
s=rd('CB6MapView.swift')
def wrap_enum_colors(s):
    out=''; i=0
    for m in re.finditer(r'enum (\w+): String, CaseIterable', s):
        name=m.group(1).lower()
        ci=s.find('var color: Color {', m.end()); nxt=s.find('\n    enum ', m.end())
        if ci<0 or (nxt>0 and ci>nxt): continue
        cj=s.index('\n        }\n',ci)
        body=s[ci:cj]
        body2=re.sub(r'case \.(\w+)((?:, \.\w+)*): return (.+)$', lambda mm: f'case .{mm.group(1)}{mm.group(2)}: return MapStyle.color("cb6map.{name}.{mm.group(1)}", {mm.group(3)})', body, flags=re.M)
        out+=s[i:ci]+body2; i=cj
    return out+s[i:]
s=wrap_enum_colors(s)
s=s.replace('Text(t.rawValue).font(DM.sans(13, .medium)).foregroundStyle(on ? .white : Color.cb6Navy)','Text(MapStyle.label("cb6map.topic.\\(t)", t.rawValue)).font(DM.sans(13, .medium)).foregroundStyle(on ? .white : Color.cb6Navy)')
assert 'MapStyle.color("cb6map.overlay.nypd"' in s and 'MapStyle.color("cb6map.district.council"' in s, 'cb6map enums'
# legend labels in the CB6 map key
s=s.replace('zoneKeys.append((f + " zoning", Palette.zoning(z.name)))','zoneKeys.append((MapStyle.label("cb6map.zoning." + f.lowercased().replacingOccurrences(of: " ", with: "-"), f + " zoning"), Palette.zoning(z.name)))')
wr('CB6MapView.swift',s); report.append('CB6 map overlay, district and topic colors and chip titles from mapstyle')

# ---- 7. BKBoards chips and district kinds
if os.path.exists(P+'BKBoards.swift'):
    s=rd('BKBoards.swift')
    def chip(m):
        title=m.group(2); sym=m.group(3); col=m.group(4); rest=m.group(5)
        key=slug(re.sub(r'^wide \? "([^"]+)" : "([^"]+)"$', r'\2', title).strip('"')) if title.startswith('wide') else slug(title.strip('"'))
        return f'{m.group(1)}chip(MapStyle.label("boards.chip.{key}", {title}), {sym}, MapStyle.color("boards.chip.{key}", {col}), {rest}'
    s2=re.sub(r'(\s)chip\((wide \? "[^"]+" : "[^"]+"|"[^"]+"), ("[^"]+"), (Color\.\w+|Color\(red: [^)]+\)), ([^\n]+)', chip, s)
    assert s2.count('MapStyle.label("boards.chip.')>=8, 'boards chips'
    s2=s2.replace('static let districtKinds: [DistrictKind] = [','static var districtKinds: [DistrictKind] { [',1)
    s2=re.sub(r'DistrictKind\(key: "(\w+)", title: "([^"]+)", logo: "([^"]+)", color: (Color\(red: [^)]+\)), level: (\.\w+)\)',
              lambda m: f'DistrictKind(key: "{m.group(1)}", title: MapStyle.label("districts.{m.group(1)}", "{m.group(2)}"), logo: "{m.group(3)}", color: MapStyle.color("districts.{m.group(1)}", {m.group(4)}), level: {m.group(5)})', s2)
    i=s2.index('static var districtKinds'); j=s2.index('\n    ]\n',i); s2=s2[:j]+'\n    ] }\n'+s2[j+len('\n    ]\n'):]
    assert 'MapStyle.label("districts.council"' in s2, 'district kinds'
    wr('BKBoards.swift',s2); report.append('Board map chips and legislature toggles from mapstyle')

# ---- 8. ProfileMap toggles
s=rd('ProfileMap.swift')
s=re.sub(r'\("(\w+)", "([^"]+)", "(office-\w+)", (Color\(red: [^)]+\))\)', lambda m: f'("{m.group(1)}", MapStyle.label("districts.{m.group(1)}", "{m.group(2)}"), "{m.group(3)}", MapStyle.color("districts.{m.group(1)}", {m.group(4)}))', s)
s=re.sub(r'Toggle\(id: "(\w+)", title: "([^"]+)", logo: ([^,]+), symbol: "([^"]*)", color: (Color\.\w+|Color\(red: [^)]+\))\)', lambda m: f'Toggle(id: "{m.group(1)}", title: MapStyle.label("profile.{m.group(1)}", "{m.group(2)}"), logo: {m.group(3)}, symbol: "{m.group(4)}", color: MapStyle.color("profile.{m.group(1)}", {m.group(5)}))', s)
assert 'MapStyle.label("profile.zoning"' in s and 'MapStyle.label("districts.assembly"' in s, 'profile toggles'
wr('ProfileMap.swift',s); report.append('Profile map toggles from mapstyle')

# ---- 9. CivicMap: drawn colors, fill, width and legend swatches by layer id
if os.path.exists(P+'CivicMap.swift'):
    s=rd('CivicMap.swift')
    s=s.replace('poly.fill = UIColor(layer.color(f.colorKey)).withAlphaComponent(0.95)','poly.fill = MapStyle.color("civicmap.\\(layer.id).\\(f.colorKey)", UIColor(layer.color(f.colorKey))).withAlphaComponent(0.95)')
    s=s.replace('let dotColor: UIColor = isSel ? UIColor(Color.cb6Navy) : UIColor(layer.color(f.colorKey))','let dotColor: UIColor = isSel ? UIColor(Color.cb6Navy) : MapStyle.color("civicmap.\\(layer.id).\\(f.colorKey)", UIColor(layer.color(f.colorKey)))')
    s=s.replace('''                    let c = UIColor(layer.color(key))
                    let multi = StyledMultiPolygon(groups[key]!)
                    multi.fill = c.withAlphaComponent(layer.fillOpacity)
                    multi.stroke = c.withAlphaComponent(0.9)
                    multi.width = layer.lineWidth''','''                    let c = MapStyle.color("civicmap.\\(layer.id).\\(key)", UIColor(layer.color(key)))
                    let multi = StyledMultiPolygon(groups[key]!)
                    multi.fill = c.withAlphaComponent(MapStyle.number("civicmap.\\(layer.id).fill", layer.fillOpacity))
                    multi.stroke = c.withAlphaComponent(0.9)
                    multi.width = MapStyle.number("civicmap.\\(layer.id).width", layer.lineWidth)''')
    assert s.count('MapStyle.color("civicmap.')==3, 'civicmap draw'
    s=s.replace('RoundedRectangle(cornerRadius: 3).fill(layer.color(f.colorKey)).frame(width: 12, height: 12).padding(.top, 4)','RoundedRectangle(cornerRadius: 3).fill(MapStyle.color("civicmap.\\(layer.id).\\(f.colorKey)", layer.color(f.colorKey))).frame(width: 12, height: 12).padding(.top, 4)')
    s=s.replace('Text(l.name).font(DM.sans(13, .medium))','Text(MapStyle.label("civicmap.\\(l.id)", l.name)).font(DM.sans(13, .medium))')
    assert 'MapStyle.label("civicmap.\\(l.id)"' in s, 'civicmap chips'
    wr('CivicMap.swift',s); report.append('Civic maps (land use, zoning, elections, rents, permits, poll sites): colors, fills, widths, chip titles from mapstyle')
    # MapScreens: the literal colors behind each civic layer
    s=rd('MapScreens.swift')
    s=s.replace('legend: [("Historic district", Color(red: 0.55, green: 0.27, blue: 0.07))],\n                 color: { _ in Color(red: 0.55, green: 0.27, blue: 0.07) }','legend: [(MapStyle.label("civicmap.historic.legend", "Historic district"), MapStyle.color("civicmap.historic.0", Color(red: 0.55, green: 0.27, blue: 0.07)))],\n                 color: { _ in MapStyle.color("civicmap.historic.0", Color(red: 0.55, green: 0.27, blue: 0.07)) }')
    s=s.replace('legend: [("Gowanus rezoning area", Color.cb6Orange)],\n                 color: { _ in Color.cb6Orange }','legend: [(MapStyle.label("civicmap.gowanus.legend", "Gowanus rezoning area"), MapStyle.color("civicmap.gowanus.0", Color.cb6Orange))],\n                 color: { _ in MapStyle.color("civicmap.gowanus.0", Color.cb6Orange) }')
    s=s.replace('let school = Color(red: 0.16, green: 0.42, blue: 0.85), care = Color(red: 0.75, green: 0.30, blue: 0.60)','let school = MapStyle.color("civicmap.schools2.0", Color(red: 0.16, green: 0.42, blue: 0.85)), care = MapStyle.color("civicmap.childcare.0", Color(red: 0.75, green: 0.30, blue: 0.60))')
    s=s.replace('let c = Color.cb6Navy\n        return MapLayer(id: "pollsites"','let c = MapStyle.color("civicmap.pollsites.0", Color.cb6Navy)\n        return MapLayer(id: "pollsites"')
    s=s.replace('places(s, .nycha, color: Color(red: 0.13, green: 0.40, blue: 0.55))','places(s, .nycha, color: MapStyle.color("civicmap.pl-nycha.0", Color(red: 0.13, green: 0.40, blue: 0.55)))')
    s=re.sub(r'MapLayer\(id: "([a-z0-9]+)", name: "([^"]+)",', lambda m: f'MapLayer(id: "{m.group(1)}", name: MapStyle.label("civicmap.{m.group(1)}", "{m.group(2)}"),', s)
    wr('MapScreens.swift',s)

# ---- 10. FindMap renderer, keyed by the overlay's own key
if os.path.exists(P+'FindMap.swift'):
    s=rd('FindMap.swift')
    s=s.replace('''                let r = MKPolygonRenderer(polygon: p)
                r.fillColor = p.color.withAlphaComponent(p.fillAlpha)
                r.strokeColor = p.color
                r.lineWidth = 1.6''','''                let r = MKPolygonRenderer(polygon: p)
                let c = MapStyle.color("findmap." + p.key, p.color)
                r.fillColor = c.withAlphaComponent(MapStyle.number("findmap." + p.key + ".fill", p.fillAlpha))
                r.strokeColor = c
                r.lineWidth = MapStyle.number("findmap." + p.key + ".width", 1.6)''')
    s=s.replace('''                let r = MKPolylineRenderer(polyline: l)
                r.strokeColor = l.color; r.lineWidth = l.width; r.lineCap = .round''','''                let r = MKPolylineRenderer(polyline: l)
                r.strokeColor = MapStyle.color("findmap." + l.key, l.color); r.lineWidth = MapStyle.number("findmap." + l.key + ".width", l.width); r.lineCap = .round''')
    assert s.count('MapStyle.color("findmap."')==2, 'findmap'
    wr('FindMap.swift',s); report.append('Address finder map colors from mapstyle')

# ---- 11. WeatherView: every hex color remappable, outline and fills by map key
s=rd('WeatherView.swift')
s=re.sub(r'Color\(hex: "(#[0-9a-fA-F]{6})"\)', lambda m: f'MapStyle.color("weather.{m.group(1).lower()}", Color(hex: "{m.group(1)}"))', s)
s=s.replace('mp.fill = f.fill; mp.alpha = f.alpha; mp.stroke = f.stroke; mp.lineWidth = f.lineWidth','mp.fill = f.fill; mp.alpha = MapStyle.number("weather.\\(key).alpha", f.alpha); mp.stroke = f.stroke; mp.lineWidth = MapStyle.number("weather.\\(key).width", f.lineWidth)')
s=s.replace('l.color = outlineColor; l.width = 2.5; l.dashed = outlineDashed','l.color = MapStyle.color("weather.\\(key).outline", outlineColor); l.width = MapStyle.number("weather.\\(key).outlineWidth", 2.5); l.dashed = outlineDashed')
assert 'MapStyle.number("weather.\\(key).alpha"' in s, 'weather'
wr('WeatherView.swift',s); report.append('Weather maps: every color, fill alpha, outline from mapstyle')

print('\n'.join(report))
