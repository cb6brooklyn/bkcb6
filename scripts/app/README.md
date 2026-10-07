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
