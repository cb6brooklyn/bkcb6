# Monthly rent update

StreetEasy posts new figures in the first week of each month. This is the whole process.

## What to download

From the StreetEasy data page, eight files. Each arrives as a zip, sometimes with
other zips nested inside, which is fine.

**Median asking rent:** Studio, One Bedroom, Two Bedroom, Three Plus Bedroom, All
**Rental inventory:** Studio, One Bedroom, Two Bedroom, Three Plus Bedroom

All eight must cover the same months. If one is a month behind, the script stops
and says which one, because a partial update would put a July map over June rankings.

## Running it

Put the zips in a folder and run:

    python3 scripts/update_rents.py /path/to/that/folder

It is safe to leave old downloads in the folder. Where two files share a name the
script keeps whichever covers the later month, and it refuses to run at all if the
files would move the site backwards.

The script rebuilds twenty files, verifies roughly 181,000 values against the source
CSVs, and writes nothing unless every check passes.

Then bump the cache version in `sw.js`, commit, and deploy.

## What it rebuilds

    rent-explorer.json          the main series, 241 areas
    inventory-by-bed.json       listings per bedroom count
    cc-rents.json               all 51 council districts, from January 2023
    rent-subranges.json         cheapest and dearest area within each parent
    rent-ranges-rollup.json     current figures per borough and citywide
    cb6-rent-trends.json        CB6 against Brooklyn and the city
    cb6-nbhd-history.json       the six CB6 neighborhoods
    rent-trends-all.json        the borough comparison pages
    eight *-rank-history.json   ranking charts on the borough pages
    four *-rents.geojson        current figures shown on the maps

## Things that were learned the hard way

**Values belong in their own month.** An earlier build stripped the blanks out of
sparse neighborhood series and packed the values to the front, which put 2022 rents
at 2010 for roughly half of them. Dense areas like Park Slope looked fine, which is
why it went unnoticed. The script never compacts.

**Community district rent** is the median of its member neighborhoods; inventory is
their sum. The membership list is `data/rent-cd-crosswalk.json`.

**Staten Island** has no StreetEasy neighborhoods at all. Its community districts and
council districts 49 and 51 fall back to the borough figure.

**Council districts** begin January 2023, when the current boundaries took effect.

**Name mismatch:** StreetEasy writes "Columbia St Waterfront District" where some of
our GeoJSON says "Columbia Street Waterfront District". The alias map in the script
handles it. Watch for others.

**The date shown on the pages** comes from `assets/datastamp.js`, which reads the month
out of `rent-explorer.json`. Nothing needs editing by hand. Any page can display it by
including that script and an empty `<div class="datastamp"></div>`.

## If something goes wrong

The script writes nothing when a check fails, so a failed run leaves the site as it was.
Read what it says, fix the input, run it again.
