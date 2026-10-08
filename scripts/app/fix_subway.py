"""The strip's subway tile opens the app's Weather screen, whose MTA service card already lists the lines' delays and changes
in detail. The tile is a button the file can re-aim (screens.json buttons "HomeStatus.subway"). fix_subway.py <app dir>"""
import sys, os
p = os.path.join(sys.argv[1], 'App/Views/HomeStatus.swift'); s = open(p).read()
if 'FileAction("HomeStatus.subway")' in s: print('already'); sys.exit()
old = '                tile(.org("mta.png"), subwayTitle, transit.isEmpty ? Copy.t("HomeStatus.97876b83", "Checking") : transit, transit == "Good service")\n'
old6 = '                tile(.org("mta.png"), Copy.t("HomeStatus.318e719c", "Subway in CB6"), transit.isEmpty ? Copy.t("HomeStatus.97876b83", "Checking") : transit, transit == "Good service")\n'
def link(title):
    return f'''                FileAction("HomeStatus.subway") {{
                NavigationLink {{ ScreenRouter.view("weather") }} label: {{
                    tile(.org("mta.png"), {title}, transit.isEmpty ? Copy.t("HomeStatus.97876b83", "Checking") : transit, transit == "Good service")
                }}
                .buttonStyle(.plain)
                }}
'''
if old in s: s = s.replace(old, link('subwayTitle'), 1)
elif old6 in s: s = s.replace(old6, link('Copy.t("HomeStatus.318e719c", "Subway in CB6")'), 1)
else: raise SystemExit('tile NOT FOUND')
open(p, 'w').write(s); print('subway tile ok')
