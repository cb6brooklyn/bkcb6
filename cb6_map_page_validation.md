# BKCB6-only map page validation

Local URL tested: `http://127.0.0.1:8080/cb6-map.html?cb6_only_local=1`

Validation completed on 2026-05-03.

## Results

The duplicated page renders with the title and heading `BKCB6 Map`, uses the existing research-map layout and controls, and shows only one focus button: `🏛 BKCB6`. The page remains scoped to the existing CB6 defaults with `activeMain = cb6` and `activeBoroFilter = 306`.

The page links back to `cb-bk-6.html` from the top bar and includes the existing footer-style navigation. The new `cb6-map.html` link was confirmed in both `index.html` and `cb-bk-6.html`, matching the existing CB6 navigation-card pattern.

A sample overlay load was tested by enabling Land Use Lots. The page successfully loaded `13,755` land-use lot features from the existing data source, confirming that the duplicated map can load the current overlays exactly as the research map does.

## Programmatic checks

| Check | Result |
|---|---:|
| Page title | `BKCB6 Map` |
| Heading | `BKCB6 Map` |
| Back link | `cb-bk-6.html` |
| Focus buttons | `🏛 BKCB6` only |
| Active main state | `cb6` |
| Active borough filter | `306` |
| Land Use Lots feature count | `13,755` |
| Index navigation link present | Yes |
| CB6 hub navigation link present | Yes |
