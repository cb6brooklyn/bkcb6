# Ballot Question Map Source Notes

On the NYC Board of Elections 2025 election results summary page, the General Election table includes dedicated **ED Level** links for the citywide charter amendments, including Questions 2, 3, and 4. This confirms that an authoritative election-district source exists for the ballot-question maps and should be used instead of relying on placeholder percentages embedded in some community-board HTML pages.

Observed issue during inspection: several non-Brooklyn community-board pages appear to contain placeholder ballot-question percentages, such as repeated `66.7% / 33.3%` or `100% / 0%` splits, which are not reliable enough for citywide or borough map generation.

Next step: extract the ED-level CSV URLs for Questions 2, 3, and 4 from the BOE results page HTML and aggregate them to community-board polygons using the existing geography join workflow.
