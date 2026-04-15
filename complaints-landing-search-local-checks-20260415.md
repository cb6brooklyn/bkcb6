# 311 Landing Search Local Verification

The complaints page now includes a duplicate search block in the landing section, positioned below the follow-up complaint callout and above the tab controls.

| Check | Result |
| --- | --- |
| Landing search visible on first page load | Yes |
| Landing fields shown | Location, Date, Complaint Type |
| Search button behavior | Switches to the Monthly tab and loads Monthly complaint results |
| Search value sync | Landing values copy into the Monthly search inputs |

A local end-to-end test used the landing search values `Smith`, `2026-04-07`, and `Noise`.

| Output | Result |
| --- | --- |
| Active tab after landing search | `monthly` |
| Filtered complaint count | `1 complaints` |
| Map subtitle | `1 of 1 complaints plotted` |
| Sample match | `2026-04-07` · `Noise - Street/Sidewalk` · `253 SMITH STREET` |
