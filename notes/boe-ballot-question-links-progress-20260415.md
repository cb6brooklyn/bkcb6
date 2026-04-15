# NYC BOE ballot-question link progress

On the NYC Board of Elections 2025 results summary page, the visible general-election table includes rows for the citywide charter amendment ballot questions.

Visible interactive link indices captured from the first viewport:

| Question row | PDF links | CSV links |
| --- | --- | --- |
| Q2 — Fast Track Affordable Housing | `47` = Recap, `48` = ED | `49` = Recap, `50` = ED Level |
| Q3 — Simplify Review of Modest Housing | `51` = Recap, `52` = ED Level | `53` = Recap, `54` = ED Level |

The Q4 row begins just below the visible portion of the table and needs one more downward inspection to capture its ED-level link indices.

## Direct source extraction from the page DOM

Using the NYC BOE table DOM, I confirmed that the citywide ballot-question rows expose direct ED-level source files for the charter amendments.

| Question | Direct ED-level source status |
| --- | --- |
| Q2 | Found a direct citywide ED-level PDF link and parallel recap links in the row |
| Q3 | Found the direct citywide ED-level links in the row |
| Q4 | Found the direct citywide ED-level links in the row |

The full extracted URLs from the DOM were saved by the browser console to:

`/home/ubuntu/console_outputs/exec_result_2026-04-15_05-10-57_538.txt`

Next step: turn those authoritative source links into downloaded files and rebuild the community-board aggregates from those source results rather than from placeholder values embedded in community-board pages.
