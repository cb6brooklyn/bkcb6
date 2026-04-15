# 311 Complaints Search Visibility Fix

## Problem confirmed

The new Location and Complaint Type search fields had been added to the page source, but they were placed inside the `c311FeltMap` container. That container is hidden when no embedded Felt map is available, so the search controls did not appear for users on the live Monthly complaints view.

## Fix applied

The search and table section was moved into an always-visible monthly complaints wrapper so the search controls render regardless of whether any separate embedded map content exists.

## Local verification

| Check | Result |
| --- | --- |
| Search fields visible in Monthly view | Yes |
| Combined test `Smith` + `Illegal Parking` | 5 complaints |
| Map subtitle after filter | `5 of 5 complaints plotted` |
| Clear reset | Restored `1,864 complaints` and `1,836 of 1,864 complaints plotted` |
