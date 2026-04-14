# Land-Use Rollout Deployment Notes

The attached files are the completed sitewide **land-use tax lot map rollout** prepared for the `bkcb6` site.

## Current state

| Item | Status |
| --- | --- |
| Local completed commit | `b64e0ca` |
| Commit message | `Add land-use tax lot maps across all pages` |
| Live site baseline | The live site at `https://bkcb6.app` still reflects the earlier published zoning rollout and does **not** yet include this land-use commit. |
| Publication blocker | GitHub authentication was unavailable in both the terminal and the controllable browser session, so automated push could not be completed from this environment. |

## What changed

This rollout updates the five borough pages and all affected community-board district pages, and adds the shared script:

| File group | Count |
| --- | --- |
| Borough HTML pages | 5 |
| Community-board HTML pages | 59 |
| Shared script | 1 |

The shared script file is `landuse-rollout.js`.

## Manual deployment

Upload these attached files into the repository working tree, replacing the existing versions, then commit and push to the repository default branch.

A simple deployment flow is:

1. Replace the existing files with the attached versions.
2. Commit with the message `Add land-use tax lot maps across all pages`.
3. Push to `main`.
4. Wait for GitHub Pages to redeploy `https://bkcb6.app`.

## Modified files

| File |
| --- |
| `bronx.html` |
| `brooklyn.html` |
| `cb-bk-1.html` |
| `cb-bk-10.html` |
| `cb-bk-11.html` |
| `cb-bk-12.html` |
| `cb-bk-13.html` |
| `cb-bk-14.html` |
| `cb-bk-15.html` |
| `cb-bk-16.html` |
| `cb-bk-17.html` |
| `cb-bk-18.html` |
| `cb-bk-2.html` |
| `cb-bk-3.html` |
| `cb-bk-4.html` |
| `cb-bk-5.html` |
| `cb-bk-6.html` |
| `cb-bk-7.html` |
| `cb-bk-8.html` |
| `cb-bk-9.html` |
| `cb-bx-1.html` |
| `cb-bx-10.html` |
| `cb-bx-11.html` |
| `cb-bx-12.html` |
| `cb-bx-2.html` |
| `cb-bx-3.html` |
| `cb-bx-4.html` |
| `cb-bx-5.html` |
| `cb-bx-6.html` |
| `cb-bx-7.html` |
| `cb-bx-8.html` |
| `cb-bx-9.html` |
| `cb-mn-1.html` |
| `cb-mn-10.html` |
| `cb-mn-11.html` |
| `cb-mn-12.html` |
| `cb-mn-2.html` |
| `cb-mn-3.html` |
| `cb-mn-4.html` |
| `cb-mn-5.html` |
| `cb-mn-6.html` |
| `cb-mn-7.html` |
| `cb-mn-8.html` |
| `cb-mn-9.html` |
| `cb-qn-1.html` |
| `cb-qn-10.html` |
| `cb-qn-11.html` |
| `cb-qn-12.html` |
| `cb-qn-13.html` |
| `cb-qn-14.html` |
| `cb-qn-2.html` |
| `cb-qn-3.html` |
| `cb-qn-4.html` |
| `cb-qn-5.html` |
| `cb-qn-6.html` |
| `cb-qn-7.html` |
| `cb-qn-8.html` |
| `cb-qn-9.html` |
| `cb-si-1.html` |
| `cb-si-2.html` |
| `cb-si-3.html` |
| `landuse-rollout.js` |
| `manhattan.html` |
| `queens.html` |
| `statenisland.html` |
