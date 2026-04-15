# CB6 permit feature handoff package

**Author:** Manus AI  
**Date:** April 15, 2026
**Target repository:** `cb6brooklyn/bkcb6`  
**Repository URL:** <https://github.com/cb6brooklyn/bkcb6>

## Executive summary

This handoff package contains the completed static-site implementation for a new **CB6 permit search** feature. The work was built for GitHub Pages compatibility and tested locally against official NYC Open Data permit sources. The feature is centered on a new `permits.html` page and a visible entry link added to `elections.html` so the current site can route users into the permit experience without restructuring the rest of the BKCB6 site.

The implementation queries both the legacy **DOB Permit Issuance** dataset and the current **DOB NOW: Build – Approved Permits** dataset because the legacy BIS source does not fully cover current permits, while DOB NOW does not fully cover older permit activity.[1] [2] That combined approach is what allows the page to return meaningful results across both recent and older dates.

## Files included in this handoff

| File | Status | Purpose |
| --- | --- | --- |
| `permits.html` | New | Main permit-search page for Brooklyn Community Board 6. |
| `elections.html` | Updated | Adds a visible **Find Permits** call-to-action linking to `permits.html`. |
| `permit_feature_implementation_summary_20260415.md` | New | Short implementation summary with data-source rationale and test results. |
| `notes/permit_dataset_notes_20260415.md` | Updated | Working notes from data selection and browser validation. |

## What the feature does

The new page supports a **daily district-wide search for Brooklyn Community Board 6**, with the selected date defaulting to the current day. It also includes an optional text filter so users can narrow results by address fragments or street names after the dataset query completes.

The interface includes a date picker, a source filter, summary counts, a results table, and a Leaflet map for records with coordinates. Internally, the page normalizes records from the two permit systems into one consistent result model so users can review permits in a single interface even when the underlying records come from different city systems.

## Implemented data logic

The feature uses the community-board identifiers that matched live dataset behavior during implementation and testing.

| Source | Dataset | Board filter used | Reason |
| --- | --- | --- | --- |
| BIS permit issuance | DOB Permit Issuance | `community_board='306'` | Matches Brooklyn Community Board 6 in the BIS-style dataset.[1] |
| DOB NOW approved permits | DOB NOW: Build – Approved Permits | `c_b_no='306'` | Matches Brooklyn Community Board 6 in the DOB NOW dataset.[2] |

The page merges both result sets, normalizes the field names, sorts the combined results, and renders them through a common UI. This is why the page can show a no-results state, a DOB NOW-only state, or a combined BIS-plus-DOB-NOW state depending on the selected date.

## Local test results already completed

The page was validated locally after implementation with representative dates that exercised the major pathways.

| Test date | Result | Interpretation |
| --- | --- | --- |
| `2026-04-15` | `0` records | Confirms the empty-state handling is working. |
| `2025-05-06` | `22` records | Confirms DOB NOW retrieval and map plotting for current-era permits. |
| `2022-05-10` | `17` records | Confirms the combined-source path, including both BIS and DOB NOW records. |

These tests indicate that the page is functioning as intended in local preview and is ready for repository publication.

## Exact publish steps

The fastest clean publication path is to copy the modified files into a fresh checkout of the live repository and then commit and push them to `main`.

| Step | Action |
| --- | --- |
| 1 | Clone the live repo: `git clone https://github.com/cb6brooklyn/bkcb6.git` |
| 2 | Copy in the new page: `cp /path/to/permits.html /path/to/bkcb6/permits.html` |
| 3 | Copy in the updated site entry page: `cp /path/to/elections.html /path/to/bkcb6/elections.html` |
| 4 | Optionally copy the documentation files into the repo if you want the notes preserved there. |
| 5 | Review the diff: `git diff -- permits.html elections.html` |
| 6 | Commit: `git add permits.html elections.html && git commit -m "Add CB6 permit search page"` |
| 7 | Push: `git push origin main` |
| 8 | Wait for GitHub Pages to redeploy, then verify the live pages. |

If you want the documentation inside the repository, add these as well before the commit:

```bash
git add permit_feature_implementation_summary_20260415.md notes/permit_dataset_notes_20260415.md
```

## Recommended commit message

```text
Add CB6 permit search page
```

If you want a more descriptive commit, this also fits the implementation cleanly:

```text
Add CB6 permit search and link from elections page
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
| Historical validation date | Searching `2022-05-10` returns combined-source results. |
| Recent validation date | Searching `2025-05-06` returns DOB NOW records and map points. |

## Known limitations and notes

This implementation was built as a static GitHub Pages page, so all data access happens client-side against the city datasets. That keeps deployment simple, but it also means the page depends on the availability and response behavior of the NYC Open Data endpoints at runtime.[1] [2]

The feature is currently scoped to **Brooklyn Community Board 6**. However, the page structure and normalization logic were organized so that additional community boards could be added later by extending the board configuration and keeping the same fetch pipeline.

## References

[1]: https://data.cityofnewyork.us/Housing-Development/DOB-Permit-Issuance/ipu4-2q9a/about_data "DOB Permit Issuance | NYC Open Data"
[2]: https://data.cityofnewyork.us/Housing-Development/DOB-NOW-Build-Approved-Permits/rbx6-tga4/about_data "DOB NOW: Build – Approved Permits | NYC Open Data"
