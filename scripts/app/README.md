# The apps' code-to-file patches

The three iOS apps (BKCB6 `~/bkcb6app`, BKCB `~/bkcivics`, CBNYC `~/cb6beyond` on the Mac) read everything that can be
changed from the pack (`app/data/civic/...`), with the code's own value as the fallback when the file has no entry:

| What | File | Keys |
|---|---|---|
| Tables (categories, labels, aliases, routes, colors, lookups, tuples, structs) | `civic/lists.json` | `<File>.<name>` |
| Colors, theme colors, map badges, type scale, font names | `civic/mapstyle.json` (colors, icons, numbers, labels; `where` says the file and line) | `<File>.c.<id>`, `theme.<name>`, `<File>.i.<id>`, `theme.textScale`, `theme.font.*` |
| Screen text | `civic/copy.json` | `<File>.<id>` |
| New badge layers on any map | `civic/markers.json` | per layer |
| Map colors, line widths, fills, legend labels, layer styles | `civic/mapstyle.json` | as documented in its `about` |
| Organizations tab headings and order | `civic/orgs/orgs-profiles.json` (`groups`, `group`, `topic`, `sort`) | |

The scripts here were run on the Mac against each app's `BKCB6/App` tree (`patch_*.py <app>`), then `export_lists.py`
and `scripts/merge_app_keys.py` wrote every key with its default into the pack files. Re-run them after new code is written.

## Order, as run on Oct 7, 2026 (each against `~/<app>/BKCB6`)

`patch_tables2.py` (tables), `fix1.py` `fix2.py` `fix3.py` (coordinate tables, string-keyed dictionaries), `patch_style2.py`
(colors, badges, theme, type scale), `fix_blockhead3.py` (Home's block card: the block is the headline), `fix_blockwork.py`
(the block card lists DOT street construction permits, the same dataset the Permits tab maps), `fix_landmarks.py`,
`fix_bkhome.py` (BKCB) and `fix_beyondhome.py` (CBNYC) (the top of Home as home.json sections), then `audit_strings.py`
(every visible string → `Copy.t` / `Copy.f`, enum raw values shown as `<File>.<Enum>.<case>`). `Shared/` is left alone
because the widget extension compiles it without `Copy`. The registries each step writes (`lists-*.json`,
`style-keys-<app>.json`, `copy-audit-<app>.json`) go through `scripts/merge_app_keys.py <dir>`.

What stays in code: layout and logic, keys and identifiers (dataset ids, symbol names, file names, settings keys), date
formats, and anything compared or matched rather than shown.
