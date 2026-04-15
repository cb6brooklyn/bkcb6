# CB6 permit feature handoff package

**Author:** Manus AI  
**Date:** April 15, 2026
**Target repository:** `cb6brooklyn/bkcb6`  
**Repository URL:** <https://github.com/cb6brooklyn/bkcb6>

## Executive summary

This handoff package contains the completed static-site implementation for a new **CB6 permit search** feature. The work was built for GitHub Pages compatibility and tested locally against official NYC Open Data permit sources. The feature is centered on a new `permits.html` page and a visible entry link added to `elections.html` so the current site can route users into the permit experience without restructuring the rest of the BKCB6 site.

The final implementation does **not** rely only on DOB datasets. It now combines the legacy **DOB Permit Issuance** dataset, the current **DOB NOW: Build – Approved Permits** dataset, and the official NYC DOT **Street Construction Permits** datasets used by the NYC Streets permit ecosystem.[1] [2] [3] [4] DOB building records are filtered by their published community-board fields, while NYC DOT street permits are filtered to **Brooklyn Community Board 6** by intersecting permit geometry with an official CB6 boundary file prepared for the static site.

## Files included in this handoff

| File | Status | Purpose |
| --- | --- | --- |
| `permits.html` | New | Main permit-search page for Brooklyn Community Board 6. |
| `elections.html` | Updated | Adds a visible **Find Permits** call-to-action linking to `permits.html`. |
| `data/cb6_boundary.geojson` | New | Official CB6 boundary asset used to filter and map NYC DOT street permits inside the district. |
| `permit_feature_implementation_summary_20260415.md` | Updated | Implementation summary with data-source rationale and final validation results. |
| `notes/permit_dataset_notes_20260415.md` | Updated | Working notes from DOB source selection and browser validation. |
| `notes/dot_street_permit_source_notes_20260415.md` | New | NYC DOT street-permit source notes, geometry findings, and validation notes. |

## What the feature does

The new page supports a **daily district-wide search for Brooklyn Community Board 6**, with the selected date defaulting to the current day. It also includes an optional text filter so users can narrow results by address fragments or street names after the dataset query completes.

The interface includes a date picker, a source filter, summary counts, a results table, and a Leaflet map for records with coordinates or permit geometry. Internally, the page normalizes records from the three permit systems into one consistent result model so users can review building and street permits in a single interface even when the underlying records come from different city systems.

## Implemented data logic

The feature uses the community-board identifiers and source split that matched live dataset behavior during implementation and testing.

| Source | Dataset | CB6 filter used | Reason |
| --- | --- | --- | --- |
| BIS permit issuance | DOB Permit Issuance | `community_board='306'` | Matches Brooklyn Community Board 6 in the BIS-style dataset.[1] |
| DOB NOW approved permits | DOB NOW: Build – Approved Permits | `c_b_no='306'` | Matches Brooklyn Community Board 6 in the DOB NOW dataset.[2] |
| NYC DOT street permits, 2022-present | Street Construction Permits 2022–Present | `boroughname='BROOKLYN'` plus CB6 boundary intersection | Current NYC DOT street-permit source used for recent permit dates.[3] |
| NYC DOT street permits, 2013-2021 | Street Construction Permits 2013–2021 | `boroughname='BROOKLYN'` plus CB6 boundary intersection | Historical NYC DOT street-permit source used for pre-2022 permit dates.[4] |

The page switches between the two NYC DOT datasets according to the selected date, parses the DOT `wkt` geometry, converts those coordinates from New York State Plane to WGS84, intersects the resulting geometry with the CB6 boundary, and then merges the accepted DOT rows with the DOB results for display. That correction was necessary because the NYC DOT `wkt` geometry is not published in plain latitude and longitude, so direct comparison against the boundary would otherwise undercount or exclude valid street permits.

## Local test results already completed

The page was validated locally after implementation with representative dates that exercised the major pathways.

| Test date | Result | Interpretation |
| --- | --- | --- |
| `2026-04-15` | `0` records | Confirms the empty-state handling is working across BIS, DOB NOW, and NYC DOT sources. |
| `2025-05-06` | `85` records | Confirms recent-date combined retrieval, including `22` DOB NOW records and `63` NYC Streets / DOT records, with mapped locations rendering correctly. |
| `2022-05-10` | `54` records | Confirms the mixed-source path with `11` DOB NOW records, `6` BIS records, and `37` NYC Streets / DOT records. |

These tests indicate that the page is functioning as intended in local preview and is ready for repository publication once a fresh GitHub credential is provided.

## Exact publish steps

The fastest clean publication path is to copy the modified files into a fresh checkout of the live repository and then commit and push them to `main`.

| Step | Action |
| --- | --- |
| 1 | Clone the live repo: `git clone https://github.com/cb6brooklyn/bkcb6.git` |
| 2 | Copy in the new page: `cp /path/to/permits.html /path/to/bkcb6/permits.html` |
| 3 | Copy in the updated site entry page: `cp /path/to/elections.html /path/to/bkcb6/elections.html` |
| 4 | Copy in the CB6 boundary asset: `cp /path/to/data/cb6_boundary.geojson /path/to/bkcb6/data/cb6_boundary.geojson` |
| 5 | Optionally copy the documentation files into the repo if you want the notes preserved there. |
| 6 | Review the diff: `git diff -- permits.html elections.html data/cb6_boundary.geojson` |
| 7 | Commit: `git add permits.html elections.html data/cb6_boundary.geojson && git commit -m "Add CB6 permit search with DOT street permits"` |
| 8 | Push: `git push origin main` |
| 9 | Wait for GitHub Pages to redeploy, then verify the live pages. |

If you want the documentation inside the repository, add these as well before the commit:

```bash
git add permit_feature_implementation_summary_20260415.md \
  notes/permit_dataset_notes_20260415.md \
  notes/dot_street_permit_source_notes_20260415.md
```

## Recommended commit message

```text
Add CB6 permit search with DOB and DOT sources
```

If you want a more descriptive commit, this also fits the implementation cleanly:

```text
Add CB6 permit search and NYC DOT street permit integration
```

## Expected live URLs after publication

Because the repository is `cb6brooklyn/bkcb6`, the published pages should typically resolve under the repository-backed GitHub Pages site path.

| Page | Expected URL |
| --- | --- |
| Elections page with entry link | <https://cb6brooklyn.github.io/bkcb6/elections.html> |
| New permit search page | <https://cb6brooklyn.github.io/bkcb6/permits.html> |

If the repository uses a custom domain or a nonstandard Pages configuration, the file paths above still remain the correct repository targets even if the public domain differs.

## Quick verification checklist after push

After publication, verify the site using the following checks.

| Check | Expected result |
| --- | --- |
| `elections.html` loads | The page shows a visible **Find Permits** link or button. |
| Permit link works | Clicking the entry opens `permits.html`. |
| Current date search | The page loads and returns either live results or an empty-state message without errors. |
| Historical validation date | Searching `2022-05-10` returns BIS, DOB NOW, and NYC Streets / DOT results. |
| Recent validation date | Searching `2025-05-06` returns DOB NOW and NYC Streets / DOT results with mapped points. |
| DOT-only filter | Switching the source filter to **NYC Streets / DOT only** limits the table and cards to street permits. |

## Known limitations and notes

This implementation was built as a static GitHub Pages page, so all data access happens client-side against city datasets at runtime. That keeps deployment simple, but it also means the page depends on the availability and response behavior of the NYC Open Data endpoints.[1] [2] [3] [4]

The feature is currently scoped to **Brooklyn Community Board 6**. However, the page structure and normalization logic were organized so that additional community boards could be added later by extending the board configuration, preparing the corresponding district boundary files, and keeping the same fetch pipeline.

## References

[1]: https://data.cityofnewyork.us/Housing-Development/DOB-Permit-Issuance/ipu4-2q9a/about_data "DOB Permit Issuance | NYC Open Data"
[2]: https://data.cityofnewyork.us/Housing-Development/DOB-NOW-Build-Approved-Permits/rbx6-tga4/about_data "DOB NOW: Build – Approved Permits | NYC Open Data"
[3]: https://data.cityofnewyork.us/Transportation/Street-Construction-Permits-2022-Present-/tqtj-sjs8/about_data "Street Construction Permits 2022–Present | NYC Open Data"
[4]: https://data.cityofnewyork.us/Transportation/Street-Construction-Permits-2013-2021-/c9sj-fmsg/about_data "Street Construction Permits 2013–2021 | NYC Open Data"
