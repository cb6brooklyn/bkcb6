# Permit dataset notes for CB6 permit search

## Official NYC data sources reviewed

### 1. DOB Permit Issuance (`ipu4-2q9a`)
This NYC Open Data dataset covers permit issuance records in the legacy BIS system. The official dataset description states that each record represents the life cycle of one permit for one work type and that the dataset is updated daily. The page also notes that this dataset only includes permits issued in BIS and that most current permits are now issued in DOB NOW.

Relevant fields visible on the dataset page include:
- `borough`
- `house__`
- `street_name`
- `community_board`
- `zip_code`
- other permit/job fields

### 2. DOB NOW: Build – Approved Permits (`rbx6-tga4`)
This NYC Open Data dataset covers permits issued through DOB NOW since 2016 and is updated daily. It is described as a list of all approved construction permits in DOB NOW except Electrical, Elevator, and Limited Alteration Application (LAA), which have their own datasets.

Relevant fields visible on the dataset page include:
- `house_no`
- `street_name`
- `borough`
- `c_b_no`
- `work_type`
- other permit/job fields

## Implementation implication
A district-wide daily permit search for CB6 should likely combine BIS permit issuance records with DOB NOW approved permits to avoid missing current records. Both official datasets expose address and community-board style fields, which makes them suitable for:
1. district-wide daily permit lookup for CB6
2. address-based permit search inside CB6

## Existing site pattern
The current `elections.html` page already contains:
- an address-search pattern using Geoclient
- a district-wide 311 monthly search pattern using direct Socrata fetches

This means a permits feature can likely reuse the same client-side design approach and query pattern.

## Live page implementation test

A new `permits.html` page was created in the BKCB6 project and tested locally in the browser.

### Browser test results
- The page loaded successfully with the default date set to the current day.
- For `2026-04-15`, the page correctly returned zero records and displayed a clear empty-state message.
- For `2025-05-06`, the page successfully loaded live CB6 permit results from the combined permit pipeline.
- The browser test showed **22 permit records**, all from **DOB NOW**, for `2025-05-06` in CB6.
- The page rendered both the permit table and the Leaflet map, with **22 mapped pins** visible for that test date.
- The existing `elections.html` page now shows a visible **Find Permits** call-to-action near the top of the page, and that button successfully navigates into `permits.html` during local browser testing.
- For `2022-05-10`, the live page returned **17 permit records** in CB6, including **11 DOB NOW** rows and **6 BIS** rows, confirming that both permit-source pipelines are working in the browser.

### Current V1 behavior
- District filter is fixed to CB6 through configuration values rather than hard-coded UI text only.
- Data fetches are client-side and GitHub Pages compatible.
- Address filtering and source filtering are currently handled on the client after the district/date query returns.
- The page is structured so additional community boards and datasets can be added later.
