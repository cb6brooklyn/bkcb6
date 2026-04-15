# CB6 permit feature implementation summary

**Author:** Manus AI  
**Date:** April 15, 2026

## Overview

A new **Find Permits** feature was added to the BKCB6 site as a GitHub Pages–compatible static page. The implementation uses official NYC Open Data permit records from both the legacy **DOB Permit Issuance** dataset and the current **DOB NOW: Build – Approved Permits** dataset, both of which are updated daily and expose the community-board and address fields needed for a district-wide CB6 search.[1] [2]

> The DOB Permit Issuance page states that it contains permit issuance records from the BIS system and notes that most current permit records are now issued through DOB NOW.[1]
>
> The DOB NOW dataset page states that it is a list of approved construction permits in DOB NOW and that it is updated daily.[2]

## What was built

The new `permits.html` page provides a **district-wide permit lookup for one selected date**, with the date defaulting to today. It combines BIS and DOB NOW permit records for **Brooklyn Community Board 6** by querying each dataset with the official community-board filters used by those systems: `community_board='306'` for BIS and `c_b_no='306'` for DOB NOW.[1] [2]

The page includes a date picker, an optional text filter for addresses or street names, a source selector, a permit table, and a Leaflet map for records that include latitude and longitude. The JavaScript is organized around a board configuration object plus separate source-fetch and normalization functions, which means the same pattern can expand to more community boards and more permit datasets later without reworking the user interface.

## Existing site integration

The current `elections.html` page was updated to include a visible **Find Permits** call-to-action near the top of the page. That link routes users into `permits.html`, which creates a clean first-step integration inside the current site structure while keeping the permits feature modular.

## Live testing results

The page was tested locally in a browser after implementation.

| Test date | Result | Notes |
| --- | --- | --- |
| 2026-04-15 | 0 records | Empty-state message rendered correctly when no permits were returned. |
| 2025-05-06 | 22 records | All 22 records came from DOB NOW and all 22 plotted on the map. |
| 2022-05-10 | 17 records | Combined result included 11 DOB NOW records and 6 BIS records, confirming both source pipelines work in the live page. |

These tests show that the page correctly handles three important states: no results, DOB NOW-only results, and combined DOB NOW + BIS results.

## Files added or updated

| File | Status | Purpose |
| --- | --- | --- |
| `permits.html` | New | Main district-wide permit search page for CB6. |
| `elections.html` | Updated | Added a visible Find Permits button linking into the new page. |
| `notes/permit_dataset_notes_20260415.md` | Updated | Saved source-selection notes and browser test findings. |
| `scripts/inspect_dob_now_columns.py` | New | Small inspection utility used to confirm the DOB NOW field names during implementation. |

## Publication status

The feature files are ready for placement in the BKCB6 GitHub Pages repository, but **publication was not completed in this environment** because the working directory available here does not contain Git repository metadata and no active repository remote is configured in the project snapshot. In addition, you previously noted that the old GitHub token was exposed and should not be reused. A **fresh safe publishing path** is therefore still required before pushing changes.

## Recommended next publishing step

The clean next step is to copy these updated files into the live BKCB6 repository checkout and then publish using a newly created GitHub credential or another safe GitHub authentication method. Once the real repository is available, the changes can be committed and pushed normally.

## References

[1]: https://data.cityofnewyork.us/Housing-Development/DOB-Permit-Issuance/ipu4-2q9a/about_data "DOB Permit Issuance | NYC Open Data"
[2]: https://data.cityofnewyork.us/Housing-Development/DOB-NOW-Build-Approved-Permits/rbx6-tga4/about_data "DOB NOW: Build – Approved Permits | NYC Open Data"
