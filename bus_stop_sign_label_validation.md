# Bus Stop Sign Label Validation

## Scope

This validation covers the `research.html` Bus Stops overlay after updating each stop to use an MTA-style bus stop sign marker. The marker is styled after the provided reference: blue MTA bus-stop sign treatment with the MTA roundel, bus icon, route number chips, and stop name.

## Local validation

Local URL: `http://127.0.0.1:8080/research.html?busstop_sign_validation=1`

The local page loaded successfully from the BKCB6 repository. The Bus Stops overlay was enabled on the research map and rendered **155** bus stop sign markers, matching the previously validated clipped CB6 stop count.

| Zoom level | Route labels visible | Stop-name labels visible | Expected behavior |
|---:|---:|---:|---|
| 14 | 0 | 0 | Compact MTA bus-stop sign only |
| 15 | 155 | 0 | Bus route number chips appear |
| 16 | 155 | 155 | Bus route number chips and stop names appear |

## Sample marker content

| Marker title | Route chips | Stop label |
|---|---|---|
| `B63 · 5 AV / 9 ST` | `B63` | `5 AV / 9 ST` |
| `B67, B69 · 7 AV / 9 ST` | `B67, B69` | `7 AV / 9 ST` |
| `B61 · BEARD ST / VAN BRUNT ST` | `B61` | `BEARD ST / VAN BRUNT ST` |
| `B57, B61 · COURT ST / LORRAINE ST` | `B57, B61` | `COURT ST / LORRAINE ST` |

## Implementation notes

The overlay remains clipped through the existing `filteredBySelectedDistricts(stopData.features || [], false)` path. The marker now uses a Leaflet `DivIcon` with `.bus-stop-sign` markup rather than the former circular bus emoji marker. Zoom-dependent detail is controlled through map container classes:

| Class | Trigger | Effect |
|---|---|---|
| `.bus-stop-labels-routes` | `zoom >= 15` | Shows route number chips for each stop |
| `.bus-stop-labels-full` | `zoom >= 16` | Shows both route number chips and the stop name |

A Node syntax check was run against extracted inline JavaScript from `research.html`; no syntax errors were reported.
