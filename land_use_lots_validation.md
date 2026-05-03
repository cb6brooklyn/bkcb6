# CB6 Land Use Lots Overlay Validation

Local validation was completed against `http://127.0.0.1:8080/research.html?landuse_lots_local=1`.

The Research map now includes a **Land Use Lots** overlay button. Enabling the overlay loads `data/cb6-land-use-lots.geojson`, creates **13,741** Leaflet circle markers, colors each lot by land-use category, and displays a category legend using the same palette as the existing CB6 land-use map.

Sample records rendered successfully in the browser included:

| Name | Land Use | Code | Zone | BBL |
|---|---|---:|---|---:|
| 235 Sackett Street | Multi-Family Walk-Up Buildings | 2 | R6B | 3003320041 |
| 381 Clinton Street | One & Two Family Buildings | 1 | R6A | 3003330001 |
| 379 Clinton Street | Multi-Family Walk-Up Buildings | 2 | R6A | 3003330002 |
| Van Brunt Street | Parking Facilities | 10 | M1-1 | 3003410001 |
| 61A Summit Street | One & Two Family Buildings | 1 | R6B | 3003520049 |

The local browser check confirmed that the overlay is present on the map, the marker layer is active, the legend entries are rendered, and the research page inline JavaScript passes `node --check`.
