"""Home's block card: in place of "N more on <street>, off your block", the button that opens 311, crime and permits
near the address (the Permits tab on the pin). Other boards keep the off-block list. fix_nearby.py <app dir>"""
import sys, os
p = os.path.join(sys.argv[1], 'App/Views/MyBlock.swift'); s = open(p).read()
if 'FeedsView(startPin: place.coord)' in s: print('already'); sys.exit()
old = '''            if !street.isEmpty, let r = ref {
                Button { withAnimation { showAll.toggle() } } label: {'''
new = '''            if place.cd == 306 {
                // CB6: the Permits tab on this address, every kind within a radius, in place of the off-block list.
                NavigationLink { FeedsView(startPin: place.coord) } label: {
                    Text(Copy.t("ExploreViews.09eee297", "311, crime and permits nearby")).font(DM.sans(13, .bold)).foregroundStyle(.white).lineLimit(1).minimumScaleFactor(0.8)
                        .padding(.horizontal, 12).padding(.vertical, 9).frame(maxWidth: .infinity).background(Color.cb6Navy, in: Capsule())
                }
                .buttonStyle(.plain)
            } else if !street.isEmpty, let r = ref {
                Button { withAnimation { showAll.toggle() } } label: {'''
assert s.count(old) == 1, 'toggle'
s = s.replace(old, new, 1); open(p, 'w').write(s); print('nearby button ok')
