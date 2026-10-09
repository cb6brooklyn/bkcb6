# The apps' code-to-file patches

The three iOS apps (BKCB6 `~/bkcb6app`, BKCB `~/bkcivics`, CBNYC `~/cb6beyond` on the Mac) read everything that can be
changed from the pack (`app/data/civic/...`), with the code's own value as the fallback when the file has no entry:

| What | File | Keys |
|---|---|---|
| Tables (categories, labels, aliases, routes, colors, lookups, tuples, structs) | `civic/lists.json` | `<File>.<name>` |
| Every screen's parts (order, folds, hidden, inserted text, pages, buttons, tools), screen replacement, the tab bar | `civic/ui/<app>/screens.json` | `screens.<key>`, `replace`, `tabs` |
| The code's tunable numbers (list caps, day windows, radii) | `civic/mapstyle.json` `numbers` | `<File>.n.<name>` |
| Every NYC Open Data dataset a screen reads | `civic/lists.json` | `<File>.ds.<id>` |
| Every button: where it goes, or hidden; anything made a button | `civic/ui/<app>/screens.json` `buttons`, parts' `dest` | `<File>.<id>` |
| The day's strip on Home | `civic/lists.json` `HomeStatus.tiles` | |
| The home-screen widget's words, colors, date formats | `civic/widget.json` | |
| Every SF symbol (icons on rows, buttons, tabs, chevrons) | `civic/mapstyle.json` `symbols` | `<File>.s.<id>` |
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
`fix_bkhome.py` (BKCB) and `fix_beyondhome.py` (CBNYC) (the top of Home as home.json sections), `fix_mapfold.py`
`fix_strip.py` `fix_pinned.py` `fix_home2.py` `fix_foldicon.py` `fix_web.py` `fix_blocksources.py` `fix_nearby.py`
`fix_blockbuttons.py` `fix_ballot.py` `fix_rows.py` `fix_place.py` (Home sections: folds, the map strip, pinned, `home@2`, fold icons, web pages and text
folds; the block card's sources, buttons, hidden rows, and every row of the card from lists.json `MyBlock.rows`, data rows, buttons, text and site
pages in any order; site pages in the app get the saved address, `{ADDRESS} {SLUG} {CD}`... in the path and `window.__bkcbPlace`), then `audit_strings.py`
(every visible string → `Copy.t` / `Copy.f`, enum raw values shown as `<File>.<Enum>.<case>`). `Shared/` is left alone
because the widget extension compiles it without `Copy`. `audit_symbols.py` then `audit_symbols2.py` (every SF symbol name →
`MapStyle.symbol("<File>.s.<id>", "name")`, overridden by mapstyle.json `symbols`; registries `symbols-<app>.json` here). Last,
`fix_screens.py <app> screens-<app>.json` (builds from 118): every `ScrollView { VStack { ... } }` screen becomes `FileParts("<screen>", [parts])`,
one named part per statement, drawn in the order `civic/ui/<app>/screens.json` lists them, with folds, text, site pages, buttons and tool grids
inserted anywhere; every screen key goes through `ScreenRouter` (the file's `replace` table); the tab bar reads `tabs`; registries `screens-<app>.json`. The registries each step writes (`lists-*.json`,
`style-keys-<app>.json`, `copy-audit-<app>.json`) go through `scripts/merge_app_keys.py <dir>`.

What stays in code: layout and logic, keys and identifiers (dataset ids, symbol names, file names, settings keys), date
formats, and anything compared or matched rather than shown.

Then (builds from 120 and 121): `fix_tiles.py` (the strip and parts' `dest`), `audit_numbers.py <app> numbers-<app>.json`, `audit_datasets.py <app> datasets-<app>.json`,
`fix_widget.py ~/bkcb6app` (the widget reads civic/widget.json), `fix_boardmeeting.py`, `fix_bknext.py`, `fix_subway.py`. `today.sh` runs the whole chain in order.
