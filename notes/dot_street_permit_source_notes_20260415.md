# NYC DOT Street Permit Source Notes

On April 15, 2026, the official NYC Open Data pages were checked for the street-permit datasets used by NYC DOT and the NYC Streets ecosystem.

| Coverage | Dataset title | Dataset ID | Agency | Notes |
| --- | --- | --- | --- | --- |
| 2022-present | Street Construction Permits (2022 - Present) | `tqtj-sjs8` | NYC DOT | Official NYC Open Data dataset. The about page states that DOT issues over 150 permit types for sidewalk and roadway work, and that the dataset includes core permit data such as permittee, permit type, date issued, and location. |
| 2013-2021 | Street Construction Permits (2013-2021) | `c9sj-fmsg` | NYC DOT | Official NYC Open Data historical companion dataset. The about page presents it as the pre-2022 archive for the same street construction permit program and shows the same 39-column structure. |

The official Open Data pages showed the same core field family for both datasets, including fields such as `permitnumber`, `applicationtrackingid`, `permitstatusshortdesc`, `permittypedesc`, `permitissuedate`, `boroughname`, `permithousenumber`, `onstreetname`, `fromstreetname`, `tostreetname`, and `permitteename`. The pages also reference the NYC Streets / OCMC context in their tags and dataset description.

## Initial local browser test

The updated `permits.html` page loaded locally at `http://127.0.0.1:8000/permits.html?date=2025-05-06`, and the interface correctly showed the new NYC Streets / DOT source in the copy, filter dropdown, summary cards, and badges. However, the initial auto-run search remained in the loading state, so the next step is runtime diagnosis using the browser console and direct dataset queries.

## Local validation progress

A local browser retest after converting DOT WKT coordinates from New York State Plane to WGS84 confirmed that the NYC Streets / DOT integration is working on `2025-05-06`. The page returned 85 combined records for CB6 on that date, consisting of 22 DOB NOW records and 63 NYC Streets / DOT records.

The next validation step is the historical test date `2022-05-10`, which was still in the loading state at the moment this note was written and needs a follow-up check after the API calls finish.

The historical validation date `2022-05-10` was confirmed in the browser after a fresh rerun. The page returned 54 combined CB6 records on that date, consisting of 11 DOB NOW records, 6 BIS records, and 37 NYC Streets / DOT records.

The empty-state validation date `2026-04-15` has been opened locally and is in progress; the next check will confirm that the page settles into a clean no-results state after the multi-source queries complete.

The empty-state validation date `2026-04-15` also completed successfully in the browser. The page showed a clean no-results state with 0 combined records, 0 DOB NOW records, 0 BIS records, and 0 NYC Streets / DOT records.
