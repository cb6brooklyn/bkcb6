"""The Home block card shows the saved address's sample ballot: the block's "ballot26" lines from the blocks file
(the same lines the full address card shows), one row under "Who represents you", with the statewide line after them.
Off by file with "ballot" in lists.json "MyBlock.hide"; the heading and the statewide line are copy.json strings
(ExploreViews.b2a7c3e1, ExploreViews.637639ad). fix_ballot.py <app dir>"""
import sys, os
p = os.path.join(sys.argv[1], 'App/Views/ExploreViews.swift'); s = open(p).read()
if 'ExploreViews.b2a7c3e1' in s: print('already'); sys.exit()
old = '''                if !s.reps.isEmpty {
                    fact("person.2.fill", Color.cb6Orange, Copy.t("ExploreViews.9e73a044", "Who represents you"), s.reps.map { "\\($0.title): \\($0.name)" }.joined(separator: "\\n"))
                }
'''
new = '''                if !s.reps.isEmpty {
                    fact("person.2.fill", Color.cb6Orange, Copy.t("ExploreViews.9e73a044", "Who represents you"), s.reps.map { "\\($0.title): \\($0.name)" }.joined(separator: "\\n"))
                }
                // The sample ballot for this block, from the blocks file; "ballot" in lists.json MyBlock.hide leaves it out.
                if let card = s.card, !card.ballot26.isEmpty, !Set(Lists.strings("MyBlock.hide", ["offblock"])).contains("ballot") {
                    let statewide = Copy.t("ExploreViews.637639ad", "Plus statewide: Governor, Lieutenant Governor, Attorney General, State Comptroller.")
                    fact("checkmark.seal.fill", MapStyle.color("ExploreViews.c.069b4658", Color(red: 0.75, green: 0.13, blue: 0.24)), Copy.t("ExploreViews.b2a7c3e1", "On your ballot, Tuesday, November 3"),
                         (card.ballot26 + (statewide.isEmpty ? [] : [statewide])).joined(separator: "\\n"))
                }
'''
assert s.count(old) == 1, 'reps fact'
s = s.replace(old, new, 1)
open(p, 'w').write(s)
print('ballot row ok')
