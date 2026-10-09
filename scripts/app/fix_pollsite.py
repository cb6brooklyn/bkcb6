"""The election screen's poll site card finds the site by address: "Find your poll site", an address field with the same
suggestions as Home's block card, the saved address filled in on open, the block's election district looked up from the
blocks file and the site shown; an election district number typed in still works. fix_pollsite.py <app dir>"""
import sys, os
p = os.path.join(sys.argv[1], 'App/Views/November2026View.swift'); s = open(p).read()
if 'addrQuery' in s: print('already'); sys.exit()
# 1. state: the address field and its hits
old = '    @State private var edQuery = ""\n'
new = '''    @State private var edQuery = ""
    @State private var addrQuery = ""
    @State private var addrLabel = ""
    @State private var addrLookedUp = false
    /// Addresses matching what is typed, as on Home's block card.
    private var addrHits: [AddressMatch] {
        let q = addrQuery.trimmingCharacters(in: .whitespaces)
        guard q.count > 3, q != addrLabel else { return [] }
        let exact = AddressIndex.points(q, scope: .city)
        return exact.isEmpty ? AddressIndex.search(q, scope: .city) : exact
    }
    /// The block's election district, as the lookup keys read it ("44001"), from the blocks file.
    private func pick(_ h: AddressMatch) {
        addrLabel = h.label.replacingOccurrences(of: ", Brooklyn", with: ""); addrQuery = addrLabel
        Task {
            if let blocks = await BlockStore.load(h.cd), let o = blocks[h.slug], let c = BlockCard(o), let e = c.eds.first, e.ad > 0 {
                edQuery = String(format: "%02d%03d", e.ad, e.ed)
            } else { edQuery = "" }
        }
    }
'''
assert old in s, 'state'; s = s.replace(old, new, 1)
# 2. the card: the address field first; a typed election district number still works
old2 = '''            Card {
                Text(d.pollLookupLabel.isEmpty ? Copy.t("November2026View.7ac435a3", "Your election district") : d.pollLookupLabel)
                    .font(DM.sans(16, .bold))
                    .foregroundStyle(Color.cb6Ink)

                HStack(spacing: 8) {
                    Image(systemName: MapStyle.symbol("November2026View.s.8709f7f6", "magnifyingglass"))
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(Color.cb6Muted)
                    TextField(Copy.t("November2026View.29133292", "44001, 44 1, or AD 44 ED 001"), text: $edQuery)
                        .font(DM.mono(15))
                        .foregroundStyle(Color.cb6Ink)
                        .textInputAutocapitalization(.characters)
                        .autocorrectionDisabled(true)
                        .submitLabel(.search)
                    if !edQuery.isEmpty {
                        Button {
                            edQuery = ""
                        } label: {'''
new2 = '''            Card {
                Text(d.pollLookupLabel.isEmpty ? Copy.t("November2026View.7ac435a3", "Find your poll site") : d.pollLookupLabel)
                    .font(DM.sans(16, .bold))
                    .foregroundStyle(Color.cb6Ink)

                HStack(spacing: 8) {
                    Image(systemName: MapStyle.symbol("November2026View.s.8709f7f6", "magnifyingglass"))
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(Color.cb6Muted)
                    TextField(Copy.t("November2026View.29133292", "Your address, e.g. 250 Baltic Street"), text: $addrQuery)
                        .font(DM.sans(15))
                        .foregroundStyle(Color.cb6Ink)
                        .autocorrectionDisabled(true)
                        .submitLabel(.search)
                        .onChange(of: addrQuery) { _, q in
                            // An election district number typed here works as before; a new address clears the old district.
                            if let k = novEDKey(q), q.count <= 12, q.filter(\\.isNumber).count >= 4 { edQuery = k }
                            else if q != addrLabel { edQuery = ""; addrLabel = "" }
                        }
                    if !addrQuery.isEmpty {
                        Button {
                            addrQuery = ""; addrLabel = ""; edQuery = ""
                        } label: {'''
assert old2 in s, 'card'; s = s.replace(old2, new2, 1)
# 3. the address suggestions under the field, and the saved address on open
old3 = '''                if !d.pollLookupHint.isEmpty {
                    Text(d.pollLookupHint)'''
new3 = '''                ForEach(Array(addrHits.prefix(5).enumerated()), id: \\.offset) { _, h in
                    Button { pick(h) } label: {
                        HStack(spacing: 8) {
                            Image(systemName: MapStyle.symbol("November2026View.s.f90dd65b", "mappin.circle.fill")).foregroundStyle(Color.cb6Orange)
                            Text(h.label).font(DM.sans(14)).foregroundStyle(Color.cb6Ink).multilineTextAlignment(.leading)
                            Spacer(minLength: 0)
                        }
                    }
                    .buttonStyle(.plain)
                }
                if !d.pollLookupHint.isEmpty {
                    Text(d.pollLookupHint)'''
assert old3 in s, 'hits'; s = s.replace(old3, new3, 1)
# the hint: the file's, else the code's
old3b = '''                if !d.pollLookupHint.isEmpty {
                    Text(d.pollLookupHint)
                        .font(DM.sans(12))'''
new3b = '''                let hint = d.pollLookupHint.isEmpty ? Copy.t("November2026View.pollhint", "Type your address and pick it from the list.") : d.pollLookupHint
                if !hint.isEmpty {
                    Text(hint)
                        .font(DM.sans(12))'''
assert old3b in s, 'hint'; s = s.replace(old3b, new3b, 1)
# the suggestions chips were election district numbers: only once a district is partly typed, never for an address
old4 = '''    private var suggestions: [String] {
        guard match == nil, !d.edKeys.isEmpty else { return [] }'''
new4 = '''    private var suggestions: [String] {
        return []  // election district chips are gone: people search by address
        guard match == nil, !d.edKeys.isEmpty, !edQuery.isEmpty else { return [] }'''
assert old4 in s, 'suggestions'; s = s.replace(old4, new4, 1)
# the saved address, on open
old5 = '''    private var pollSiteSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            SectionHeader(text: Copy.t("November2026View.9d482bf6", "Your poll site"))
'''
new5 = '''    private var pollSiteSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            SectionHeader(text: Copy.t("November2026View.9d482bf6", "Your poll site"))
                .onAppear {
                    // The saved address, looked up once.
                    guard !addrLookedUp, addrQuery.isEmpty, let p = MyPlace.current, !p.slug.isEmpty else { return }
                    addrLookedUp = true
                    pick(AddressMatch(label: p.label, slug: p.slug, cd: p.cd, coord: p.coord))
                }
'''
assert old5 in s, 'section'; s = s.replace(old5, new5, 1)
open(p, 'w').write(s)
print('poll site ok')
