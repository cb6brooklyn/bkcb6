# NYC Streets source notes

**Date:** April 15, 2026

Initial findings for `https://nycstreets.net/public/permit/search`:

- The public page describes itself as the **NYCDOT NYCStreets Active Permits Finder**.
- It appears to expose **active street permits** around a location or searched address, rather than DOB building permits.
- The page description states that permit results are shown as orange dots for intersections and orange lines for blocks or stretches.
- The page supports current-location search, area search, and address search.
- In the controllable browser session, a subsequent page view failed with `ERR_CONNECTION_CLOSED`, so browser-only inspection is unreliable and command-line inspection is needed.
