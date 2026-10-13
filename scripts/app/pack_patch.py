"""DataPack: show new files as they arrive. The screens redraw once the manifest's own files are in (text, screens,
lists, copy, calendar, directory), and again after each big folder (maps, logos, site), instead of only at the very end.
Usage: python3 pack_patch.py <project dir>  (idempotent)"""
import sys
P = sys.argv[1].rstrip('/') + '/BKCB6/App/Services/DataPack.swift'
s = open(P).read()
if 'static func announce()' in s:
    print('already'); raise SystemExit
old = """        for (rel, meta) in files.sorted(by: { $0.key < $1.key }) {
            listed.insert(rel)
            await take(rel, meta, &have, &changed)
        }
"""
new = """        for (rel, meta) in files.sorted(by: { $0.key < $1.key }) {
            listed.insert(rel)
            await take(rel, meta, &have, &changed)
        }
        // The screens' own files are in: save where we are and show them now, before the big folders.
        var shown = changed
        if changed > 0 { shas = have; await announce() }
"""
assert old in s; s = s.replace(old, new, 1)
old = """            if ok { dseen[prefix] = sha }
        }
"""
new = """            if ok { dseen[prefix] = sha }
            // Each folder shows as soon as it is in.
            if changed > shown { shown = changed; shas = have; dirShas = dseen; await announce() }
        }
"""
assert old in s; s = s.replace(old, new, 1)
old = """        if changed > 0 {
            await MainActor.run {
                CalData.reset()
                OrgsData.reset()
                NotificationCenter.default.post(name: notification, object: nil)
            }
        }
        return changed
    }
"""
new = """        if changed > shown { await announce() }
        return changed
    }

    /// Tells every screen that reads a pack file to read it again.
    static func announce() async {
        await MainActor.run {
            CalData.reset()
            OrgsData.reset()
            NotificationCenter.default.post(name: notification, object: nil)
        }
    }
"""
assert old in s; s = s.replace(old, new, 1)
open(P, 'w').write(s); print('patched')
