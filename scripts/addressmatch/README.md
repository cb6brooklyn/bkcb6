Helper block files for the apps' Your block card (civic/blocks/zz-geo.json, zb-geo.json, zy-geo.json, zw-geo.json).
The card picks the closest block centre; these files add a point at addresses that rule gets wrong, tied to the block on the address's own street.
Run from the repo root, in order: 1 (CB6 area, dense), 2 (each address's own-street block), 3 <cell metres> (which addresses need a point), 4 (zy citywide, zb Brooklyn), 5 (zw, BKCB6 fix-ups), 6 (street names on the blocks split between two boards). Scripts 2 to 5 pass data through /tmp/city*.pkl.
Each app lists the files it reads in its lists.json BlockCards.boroughs: BKCB6 zz, zb, zw; BKCB zb; CBNYC zy.
