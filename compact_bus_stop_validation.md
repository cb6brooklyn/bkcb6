# Compact Bus Stop Marker Validation

## Scope

This note validates the refinement that reduces the size of MTA-style bus stop markers on `research.html` while preserving the route and stop-name labels requested for zoomed-in map views.

## Local validation

Local URL: `http://127.0.0.1:8080/research.html?compact_bus_stops=1`

The Bus Stops overlay rendered **155** bus stop markers. The markers remain blue MTA-style stop signs, but the sign dimensions, route chips, iconography, border, padding, and shadow were reduced to lower visual clutter.

| Zoom level | Route labels visible | Stop-name labels visible | Result |
|---:|---:|---:|---|
| 14 | 0 | 0 | Compact bus stop signs only |
| 15 | 155 | 0 | Compact route chips visible |
| 16 | 155 | 155 | Compact route chips and stop names visible |

## Size check

A sample of 40 full-label markers at zoom 16 averaged approximately **84 px wide by 52 px tall**, down from the prior full-label minimum width of 118 px and maximum width of 184 px. The new full-label range is 84 px to 132 px, which materially reduces overlap while retaining legibility.

## Visual inspection

The local zoom-16 screenshot confirmed lower marker density and less map obstruction compared with the earlier full-size signs. The route and stop labels remain visible when zoomed in.
