# 311 Complaints Search — Local Verification Notes

## Interface check

Confirmed on the locally served `complaints.html` page that the Monthly 311 panel now includes:

- A dedicated **Location** search input (`c311SearchLocation`)
- A dedicated **Complaint Type** search input (`c311SearchType`)
- A **Clear** button to reset both searches

## Functional check

Using the local page with live monthly complaint data loaded for April 2026:

| Test | Result count | Map subtitle | Sample result |
| --- | ---: | --- | --- |
| Location = `Smith` | 22 complaints | 20 of 22 complaints plotted | `253 SMITH STREET` noise complaint |
| Complaint Type = `Illegal Parking` | 599 complaints | 599 of 599 complaints plotted | Multiple Illegal Parking records returned |
| Location = `Smith` and Complaint Type = `Illegal Parking` | Combined filter worked in browser test | Map and table both narrowed together | Intersection search returned only matching rows |
| Clear button | Restored the full monthly dataset | Map and count reset | Search inputs cleared successfully |

## Implementation note

The search now filters both the complaint table and the Leaflet complaint map together, instead of only filtering a single combined search box in the table.
