# Removes passages that repeat what another part of the same page already says. Each edit must match, or the build stops.
import re

def _one(page, s):
    n = page.count(s)
    if n != 1: raise SystemExit('dedupe: expected 1 match, got %d: %r' % (n, s[:70]))
    return page.index(s)

def drop_li(page, snip):
    i = _one(page, snip); st = page.rfind('<li', 0, i); en = page.index('</li>', i) + 5
    return page[:st] + page[en:].lstrip('\n')

def drop_all_li(page, snip):
    while snip in page:
        i = page.index(snip); st = page.rfind('<li', 0, i); en = page.index('</li>', i) + 5; page = page[:st] + page[en:].lstrip('\n')
    return page

def drop_kp(page, snip):
    i = _one(page, snip); st = page.rfind('<div class="kp">', 0, i); en = page.index('</div></div>', i) + 12
    return page[:st] + page[en:]

def drop_section(page, start):
    i = _one(page, start); en = page.index('</section>', i) + 10
    return page[:i] + page[en:]

def cut(page, old, new=''):
    _one(page, old); return page.replace(old, new)

def cut_re(page, pat, new=''):
    n = len(re.findall(pat, page, flags=re.S))
    if n != 1: raise SystemExit('dedupe: expected 1 regex match, got %d: %r' % (n, pat[:70]))
    return re.sub(pat, new, page, flags=re.S)

def run(page, scope):
    # both pages: the "Key numbers" strip repeats the "At a glance" tiles
    page = drop_section(page, '<section class="mstrip"')
    if scope == 'cb6':
        # the four big figures repeat the tiles, the story so far and the corridor section
        for s in ('>130,000</a></div><div class="k">vehicles a day', '>12.1 mi</a>', '>$4B</a>', '>$160M</a>'): page = drop_kp(page, s)
        # "In CB6" tiles that repeat the 102 complaints and the 11,729 BQE trucks
        page = drop_kp(page, '311 truck route complaints in CB6, April 2020 to September 2026</div>')
        page = drop_kp(page, 'trucks a day on the BQE at Kane St, both directions')
        page = re.sub(r'<div class="kpis">\s*</div>', '', page)
        # the 187 tickets at 1 Atlantic Avenue: kept in Enforcement
        page = cut_re(page, r' NYPD wrote 187 <span class="k2">.*?</span> size and weight tickets at one point near 1 Atlantic Avenue, where BQE Central begins\.')
        # the Expert Panel's 50 percent quote: kept in the tile
        page = drop_li(page, '<b>Where the trucks come from:</b>')
        # "Trucks" is defined once, in the neighborhood counts
        page = cut(page, ' "Trucks" means DOT\'s Medium Truck plus Heavy Truck classes.</li>', '</li>')
        # the Streetsblog cut-through quote: kept in How the BQE connects
        page = drop_li(page, '<b>Hicks Street northbound is the cut-through.</b>')
        # each neighborhood's summary line already gives its complaint count
        page = drop_all_li(page, 'fall inside this outline (calculated)')
        # outline names beyond the main six: explained once, in What this page means by CB6
        page = cut(page, ' Some CB6 blocks fall inside outlines named Greenwood Heights, South Slope, Boerum Hill, Brooklyn Heights, Prospect Heights or Prospect Park, and they are listed under those names.')
        # the link to the Carroll Gardens page: kept in Enforcement
        page = cut_re(page, r'<p class="k">For a closer look at two neighborhoods, see .*?</p>')
    if scope == 'cg':
        # How the BQE connects: the 130,000 quote and the 11,729 count are in the tiles above
        page = cut_re(page, r'The BQE is the biggest truck road next to Carroll Gardens and Gowanus\. NYC DOT says "Approximately 130,000.*?\(calculated from both directions\)\. ', 'The BQE is the biggest truck road next to Carroll Gardens and Gowanus. ')
        page = cut_re(page, r'(<li><b>Trucks with a stop nearby get off at the ramps\.</b>).*?</li>', r'\1 The exits and entrances nearby are listed under How trucks get from the highway to these streets. From a ramp, a truck must use local truck routes such as Hamilton Avenue, 3rd Avenue and 4th Avenue until it is close to its stop. These ramps and routes are labeled on the map.</li>')
        # cut-through, sensors, "hopping off": kept in The BQE next to Carroll Gardens and Gowanus and the Hicks Street section
        page = drop_li(page, '<b>Trucks that dodge BQE limits end up on local streets.</b>')
        page = drop_li(page, '<b>Where BQE trucks come from.</b>')
        page = drop_li(page, '<b>What is at stake.</b>')
        page = cut_re(page, r' DOT says "Approximately 130,000 vehicles use the BQE daily – 13,000 of them trucks, making this a vital freight corridor" \(<a [^>]*>NYC DOT</a>\)\.(</p></section>\n<ul class="pts">\n<li><b>Which part of the BQE this is)', r'\1')
        # the rule for leaving a route and the list of routes: kept in What a truck route is
        page = drop_li(page, '<b>The rules.</b>')
        page = drop_li(page, '<b>Leaving a truck route to make a delivery.</b>')
        page = drop_li(page, '<b>Truck routes inside or along Carroll Gardens:</b>')
        page = drop_li(page, '<b>Truck routes inside or along Gowanus:</b>')
        page = drop_li(page, '<b>Enforcement near the BQE.</b>')
        page = drop_li(page, '<b>Route changes this fall.</b>')
        page = drop_li(page, '<b>Carroll Gardens and Gowanus within CB6.</b>')
        page = drop_li(page, '<b>What complaints measure.</b>')
        page = cut_re(page, r' DOT\'s spokeswoman said the city is "working with the NYPD to enforce this on surrounding streets to prevent trucks from hopping off the BQE and back on again" \(<a [^>]*>FreightWaves, August 1, 2024</a>\)\.(</li>\n</ul>\n<div class="sub2"><h3>Crashes involving trucks)', r'\1')
    return page
