# 311 Complaints Date Search Local Checks

The Monthly complaints search was extended to include a visible **Date** field alongside **Location** and **Complaint Type**.

| Test | Result |
| --- | --- |
| Date field visible | Yes |
| Date-only search `2026-04-14` | `5 complaints` |
| Location-only search `Smith` | `22 complaints` |
| Location + Date search `Smith` + `2026-04-07` | `3 complaints` |
| Location + Date + Complaint Type search `Smith` + `2026-04-07` + `Noise` | `1 complaints` |
| Clear reset | Restored `1,864 complaints` and `1,836 of 1,864 complaints plotted` |

Sample positive combined match:

| Date | Complaint Type | Address |
| --- | --- | --- |
| 2026-04-07 | Noise - Street/Sidewalk | 253 SMITH STREET |
