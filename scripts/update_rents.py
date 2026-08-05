#!/usr/bin/env python3
"""
Rebuild every rent data file on bkcb6.app from a month of StreetEasy downloads.

Usage:
    python3 scripts/update_rents.py /path/to/folder-of-zips

The folder can hold the raw .zip files exactly as StreetEasy sends them, nested
zips included. The script finds the eight CSVs it needs, rebuilds all eighteen
data files, verifies every value against the source, and refuses to write
anything if a check fails.

What it needs, per month:
    medianAskingRent_Studio / OneBd / TwoBd / ThreePlusBd / All
    rentalInventory_Studio / OneBd / TwoBd / ThreePlusBd

Notes that took a while to work out, so they are recorded here:
  * Values sit in the month they belong to. Do not compact out the blanks.
    An earlier build packed values to the front, which put 2022 rents at 2010
    for about half the neighborhoods.
  * Community district rent is the median of its member neighborhoods, and
    inventory is their sum. Staten Island districts have no StreetEasy
    neighborhoods, so they fall back to the borough figure.
  * Council districts work the same way and start January 2023, when the
    current boundaries took effect. Councils 49 and 51 are entirely Staten
    Island, so they also fall back to the borough.
  * StreetEasy writes "Columbia St Waterfront District"; some of our GeoJSON
    says "Columbia Street". The alias map below handles that.
"""
import csv, json, os, re, shutil, statistics, sys, tempfile, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')

RENT_FILES = {'studio':'medianAskingRent_Studio.csv','br1':'medianAskingRent_OneBd.csv',
              'br2':'medianAskingRent_TwoBd.csv','br3':'medianAskingRent_ThreePlusBd.csv',
              'all':'medianAskingRent_All.csv'}
INV_FILES  = {'studio':'rentalInventory_Studio.csv','br1':'rentalInventory_OneBd.csv',
              'br2':'rentalInventory_TwoBd.csv','br3':'rentalInventory_ThreePlusBd.csv'}
BEDS = ['studio','br1','br2','br3']
ALL_SERIES = BEDS + ['all']
BORO_OF = {'MN':'Manhattan','BX':'Bronx','BK':'Brooklyn','QN':'Queens','SI':'Staten Island'}
ALIAS = {'Columbia Street Waterfront District':'Columbia St Waterfront District'}

def die(msg):
    print('\nSTOPPED: '+msg)
    print('Nothing was written.')
    sys.exit(1)

def _last_month_of(path):
    """Read just the header and report the final month column."""
    try:
        with open(path, newline='') as fh:
            header = next(csv.reader(fh))
        ms = [c for c in header if re.match(r'^\d{4}-\d{2}$', c)]
        return ms[-1] if ms else ''
    except Exception:
        return ''

def unpack(src, workdir):
    """Pull every CSV out of the folder, following nested zips.

    StreetEasy downloads often contain older copies of the same file, and a
    folder may hold several months of downloads. Whenever two files share a
    name, keep the one covering the most recent month, so a stale duplicate
    can never quietly roll the site backwards.
    """
    staging = os.path.join(workdir, '_staging')
    os.makedirs(staging, exist_ok=True)
    seen = 0
    for depth in range(4):
        roots = [src] if depth == 0 else [staging]
        for root in roots:
            for dirpath, _dirs, files in os.walk(root):
                for fn in files:
                    p = os.path.join(dirpath, fn)
                    if fn.lower().endswith('.zip'):
                        try:
                            with zipfile.ZipFile(p) as z:
                                z.extractall(os.path.join(staging, 'z%d' % seen)); seen += 1
                        except Exception:
                            pass
    best = {}
    for dirpath, _dirs, files in os.walk(src):
        for fn in files:
            if fn.lower().endswith('.csv'):
                p = os.path.join(dirpath, fn)
                m = _last_month_of(p)
                if m and (fn not in best or m > best[fn][1]): best[fn] = (p, m)
    for dirpath, _dirs, files in os.walk(staging):
        for fn in files:
            if fn.lower().endswith('.csv'):
                p = os.path.join(dirpath, fn)
                m = _last_month_of(p)
                if m and (fn not in best or m > best[fn][1]): best[fn] = (p, m)
    for fn, (p, m) in best.items():
        shutil.copy(p, os.path.join(workdir, fn))
    return workdir

def load_csv(workdir, name):
    p = os.path.join(workdir, name)
    if not os.path.exists(p):
        die('missing %s. Download it from StreetEasy and include it.' % name)
    rows = list(csv.DictReader(open(p)))
    if not rows: die('%s is empty' % name)
    months = [c for c in rows[0] if re.match(r'^\d{4}-\d{2}$', c)]
    if not months: die('%s has no month columns' % name)
    return rows, months

def num(v):
    try:
        f = float(v)
        return round(f) if f == f else None
    except Exception:
        return None

def median(vals):
    v = [x for x in vals if x is not None]
    return round(statistics.median(v)) if v else None

def total(vals):
    v = [x for x in vals if x is not None]
    return sum(v) if v else None


def main(src):
    work = tempfile.mkdtemp(prefix='rents_')
    unpack(src, work)

    # ---- read and check the source files agree on the same months ----
    months = None
    for label, name in list(RENT_FILES.items()) + list(INV_FILES.items()):
        _rows, ms = load_csv(work, name)
        if months is None:
            months = ms
        elif ms != months:
            die('%s ends at %s but the others end at %s.\n'
                '       All eight files must cover the same months. Re-download the odd one out.'
                % (name, ms[-1], months[-1]))
    LAST = months[-1]
    current = json.load(open(os.path.join(DATA,'rent-explorer.json'))).get('meta',{}).get('last')
    if current and LAST < current:
        die('these files end at %s but the site already has %s.\n'
            '       That would roll the data backwards. Check you sent the newest downloads.'
            % (LAST, current))
    if current and LAST == current:
        print('Note: the site is already at %s. Rebuilding it anyway.' % LAST)
    print('Source files agree: %d months, ending %s' % (len(months), LAST))

    rent, inv, meta = {}, {}, {}
    for key, name in RENT_FILES.items():
        rows, _ = load_csv(work, name)
        for r in rows:
            nm = r['areaName']
            meta.setdefault(nm, {'t': r['areaType'], 'p': r.get('Borough') or ''})
            rent.setdefault(nm, {})[key] = [num(r.get(m)) for m in months]
    for key, name in INV_FILES.items():
        rows, _ = load_csv(work, name)
        for r in rows:
            inv.setdefault(r['areaName'], {})[key] = [num(r.get(m)) for m in months]

    blank = [None] * len(months)
    def rs(nm, k): return rent.get(nm, {}).get(k, blank)
    def iv(nm, k): return inv.get(nm, {}).get(k, blank)

    crosswalk = json.load(open(os.path.join(DATA, 'rent-cd-crosswalk.json')))

    # ---- rent-explorer.json ----
    PREFIX = {'neighborhood':'n:', 'borough':'b:', 'city':'x:'}
    areas = []
    for nm, series in rent.items():
        t = meta[nm]['t']
        if t not in PREFIX: continue
        s = {k: [0, series.get(k, blank)] for k in ALL_SERIES}
        s['inv'] = [0, [total([iv(nm,k)[i] for k in BEDS]) for i in range(len(months))]]
        areas.append({'id': PREFIX[t]+nm, 'n': nm, 't': t, 'p': meta[nm]['p'], 's': s})

    for code, members in crosswalk.items():
        si = code.startswith('SI')
        s = {}
        for k in ALL_SERIES:
            s[k] = [0, [ (rs('Staten Island',k)[i] if si else median([rs(m,k)[i] for m in members]))
                        for i in range(len(months)) ]]
        s['inv'] = [0, [ total([iv('Staten Island',k)[i] for k in BEDS]) if si
                         else total([iv(m,k)[i] for m in members for k in BEDS])
                        for i in range(len(months)) ]]
        areas.append({'id':'c:'+code, 'n':code, 't':'cd', 'p':BORO_OF[code[:2]], 's':s})

    explorer = {'months': months, 'areas': areas,
                'meta': {'source':'StreetEasy', 'last': LAST,
                         'note':'CD rent = median of member neighborhood medians; '
                                'CD inventory = sum of member listings; SI CDs use borough figures'}}
    by_name = {a['n']: a for a in areas}
    by_id   = {a['id']: a for a in areas}

    # ---- verify every value against the source before writing anything ----
    checked = bad = 0
    for key, name in RENT_FILES.items():
        rows, _ = load_csv(work, name)
        for r in rows:
            if r['areaType'] not in PREFIX: continue
            a = by_name.get(r['areaName'])
            if not a: die('area %s vanished during the rebuild' % r['areaName'])
            for i, m in enumerate(months):
                checked += 1
                if a['s'][key][1][i] != num(r.get(m)): bad += 1
    if bad: die('%d rent values did not match the source CSVs' % bad)
    print('Verified %s rent values against source, no mismatches' % format(checked,','))

    for code, members in crosswalk.items():
        a = by_id['c:'+code]; si = code.startswith('SI')
        for k in ALL_SERIES:
            for i in range(len(months)):
                want = rs('Staten Island',k)[i] if si else median([rs(m,k)[i] for m in members])
                if a['s'][k][1][i] != want:
                    die('community district %s %s went wrong at %s' % (code,k,months[i]))
    print('Verified all %d community districts' % len(crosswalk))

    # ---- inventory-by-bed.json ----
    old_ib = json.load(open(os.path.join(DATA,'inventory-by-bed.json')))
    ib = {'months': months, 'cd':{}, 'nb':{}, 'boro':{}, 'city':{}}
    for nm in inv:
        bucket = {'neighborhood':'nb','borough':'boro','city':'city'}.get(meta.get(nm,{}).get('t'))
        if not bucket: continue
        ib[bucket][nm] = {k:[0, iv(nm,k)] for k in BEDS}
    for code, members in crosswalk.items():
        if code not in old_ib['cd']: continue
        si = code.startswith('SI')
        ib['cd'][code] = {k:[0,[ (iv('Staten Island',k)[i] if si else total([iv(m,k)[i] for m in members]))
                                for i in range(len(months))]] for k in BEDS}

    # ---- cc-rents.json, council districts from January 2023 ----
    cc = json.load(open(os.path.join(DATA,'cc-rents.json')))
    cc_boro = json.load(open(os.path.join(DATA,'cc-borough.json')))
    start = cc['months'][0]
    keep = [m for m in months if m >= start]
    idx  = [months.index(m) for m in keep]
    cds = {}
    fell_back = []
    for cd, members in cc['crosswalk'].items():
        usable = [m for m in members if m in rent]
        boro = (cc_boro.get(cd) or {}).get('main')
        fallback = boro if not usable and boro in rent else None
        if fallback: fell_back.append(cd)
        rec = {}
        for k in BEDS:
            if fallback:
                rec[k]          = [rs(fallback,k)[i] for i in idx]
                rec['inv_'+k]   = [iv(fallback,k)[i] for i in idx]
            else:
                rec[k]          = [median([rs(m,k)[i] for m in usable]) for i in idx]
                rec['inv_'+k]   = [total([iv(m,k)[i] for m in usable]) for i in idx]
        cds[cd] = rec
    # any council with no StreetEasy neighborhoods, currently 49 and 51 on
    # Staten Island, is absent from cc['crosswalk'] entirely; add it here so
    # all 51 are covered, using the borough figure
    for cd in [str(i) for i in range(1, 52)]:
        if cd in cds: continue
        boro = (cc_boro.get(cd) or {}).get('main')
        if not boro or boro not in rent: continue
        cds[cd] = {}
        for k in BEDS:
            cds[cd][k]        = [rs(boro,k)[i] for i in idx]
            cds[cd]['inv_'+k] = [iv(boro,k)[i] for i in idx]
        fell_back.append(cd)
    cc['months'], cc['cds'] = keep, cds
    if fell_back:
        cc['note'] = cc.get('note','') + (' Councils %s have no StreetEasy neighborhoods and use their borough figure.'
                                          % ', '.join(sorted(set(fell_back), key=int)))

    # ---- rank-history files ----
    PRE = {v:k for k,v in BORO_OF.items()}
    RANK_KEYS = BEDS + ['inv']
    rank_out = {}
    for path in sorted(f for f in os.listdir(DATA) if f.endswith('-rank-history.json')):
        d = json.load(open(os.path.join(DATA,path)))
        selfname = d['self']['name']
        def series_for(look):
            a = by_name.get(look)
            return {k:[0, a['s'][k][1]] for k in RANK_KEYS} if a else None
        s = series_for('NYC' if selfname=='New York City' else selfname)
        if s: d['self']['s'] = s
        for e in d['cds']:
            nm = e['name']
            if nm.startswith('CD'):     look = PRE.get(selfname,'')+'CB'+nm[2:]
            elif ' CD' in nm:
                b,numpart = nm.split(' CD'); look = PRE[b]+'CB'+numpart
            else:                        look = 'NYC' if nm=='New York City' else nm
            s = series_for(look)
            if s: e['s'] = s
        for e in d['nbs']:
            s = series_for('NYC' if e['name']=='New York City' else e['name'])
            if s: e['s'] = s
        d['months'] = months
        rank_out[path] = d

    # ---- rent-subranges.json ----
    sub_old = json.load(open(os.path.join(DATA,'rent-subranges.json')))
    def members_of(aid):
        if aid.startswith('c:'): return [by_name[m]['id'] for m in crosswalk.get(aid[2:],[]) if m in by_name]
        if aid.startswith('b:'):
            b = aid[2:]
            nbs = [a['id'] for a in areas if a['t']=='neighborhood' and a['p']==b]
            return nbs or [a['id'] for a in areas if a['t']=='cd' and a['p']==b]
        if aid.startswith('x:'): return [a['id'] for a in areas if a['t']=='neighborhood']
        return []
    sub = {}
    for aid, orec in sub_old['sub'].items():
        mem = [m for m in members_of(aid) if m in by_id]
        if not mem: continue
        listN = isinstance(orec['loN'], list)
        lo, hi = [], []
        loN = [] if listN else None; hiN = [] if listN else None
        lastLo, lastHi = (None,None) if listN else (orec['loN'], orec['hiN'])
        for i in range(len(months)):
            vals = [(by_id[m]['s']['all'][1][i], m) for m in mem if by_id[m]['s']['all'][1][i] is not None]
            if vals:
                mn, mx = min(vals), max(vals)
                lo.append(mn[0]); hi.append(mx[0]); lastLo, lastHi = mn[1], mx[1]
            else:
                lo.append(None); hi.append(None)
            if listN: loN.append(lastLo); hiN.append(lastHi)
        sub[aid] = {'lo':[0,lo], 'hi':[0,hi],
                    'loN': loN if listN else (lastLo or orec['loN']),
                    'hiN': hiN if listN else (lastHi or orec['hiN'])}
    subranges = {'months': months, 'sub': sub, 'labels': sub_old['labels']}

    # ---- rent-ranges-rollup.json ----
    BEDLBL = {'studio':'studio','br1':'1BR','br2':'2BR','br3':'3+BR'}
    roll_old = json.load(open(os.path.join(DATA,'rent-ranges-rollup.json')))
    last_i = len(months)-1
    rollup = {}
    for aid, orec in roll_old.items():
        a = by_id.get(aid)
        if not a: continue
        beds = {k:a['s'][k][1][last_i] for k in BEDS}
        have = {k:v for k,v in beds.items() if v is not None}
        rec = dict(orec)
        if have:
            lo = min(have, key=have.get); hi = max(have, key=have.get)
            rec.update({'range_lo':have[lo],'range_hi':have[hi],
                        'range_lo_bed':BEDLBL[lo],'range_hi_bed':BEDLBL[hi]})
        rec.update({'rent_studio':beds['studio'],'rent_1br':beds['br1'],
                    'rent_2br':beds['br2'],'rent_3br':beds['br3'],
                    'rent_all':a['s']['all'][1][last_i]})
        kind = orec.get('sub_kind')
        kids = [x for x in areas
                if x['t'] == ('cd' if kind=='district' else 'neighborhood')
                and (aid.startswith('x:') or x['p']==aid[2:])]
        vals = [(x['s']['all'][1][last_i], x['n']) for x in kids if x['s']['all'][1][last_i] is not None]
        if vals:
            mn, mx = min(vals), max(vals)
            rec.update({'sub_lo':mn[0],'sub_lo_name':mn[1],'sub_hi':mx[0],'sub_hi_name':mx[1]})
        rollup[aid] = rec

    # ---- cb6-rent-trends.json and cb6-nbhd-history.json ----
    t_old = json.load(open(os.path.join(DATA,'cb6-rent-trends.json')))
    cb6_nbs = t_old['meta']['cb6_neighborhoods']
    cb6_trends = {
        'rent':{'months':months,
                'cb6':[median([rs(n,'all')[i] for n in cb6_nbs]) for i in range(len(months))],
                'brooklyn':rs('Brooklyn','all'), 'nyc':rs('NYC','all')},
        'inventory':{'months':months,
                'cb6':[total([by_name[n]['s']['inv'][1][i] for n in cb6_nbs if n in by_name]) for i in range(len(months))],
                'brooklyn':by_name['Brooklyn']['s']['inv'][1], 'nyc':by_name['NYC']['s']['inv'][1]},
        'meta':dict(t_old['meta'], last_month=LAST)}

    nb_old = json.load(open(os.path.join(DATA,'cb6-nbhd-history.json')))
    nbhds = {}
    for nm in nb_old['nbhds']:
        a = by_name.get(ALIAS.get(nm, nm))
        if not a: continue
        rec = {'rent':[0,a['s']['all'][1]], 'inv':[0,a['s']['inv'][1]]}
        for k in BEDS:
            rec[k] = [0, a['s'][k][1]]
            rec['inv_'+k] = [0, ib['nb'].get(ALIAS.get(nm,nm), {}).get(k, [0,blank])[1]]
        nbhds[nm] = rec
    cb6_nbhd = {'months':months, 'nbhds':nbhds}

    # ---- rent-trends-all.json ----
    ta_old = json.load(open(os.path.join(DATA,'rent-trends-all.json')))
    PAGE_AREA = {'brooklyn':'Brooklyn','manhattan':'Manhattan','queens':'Queens',
                 'bronx':'Bronx','statenisland':'Staten Island'}
    def page_series(name):
        if name == 'cb6':
            r  = {k:[median([rs(n,k)[i] for n in cb6_nbs]) for i in range(len(months))] for k in ALL_SERIES}
            i2 = {k:[total([by_name[n]['s']['inv'][1][i] for n in cb6_nbs if n in by_name]) for i in range(len(months))] for k in ALL_SERIES}
            return r, i2
        a = by_name[PAGE_AREA[name]]
        return ({k:a['s'][k][1] for k in ALL_SERIES},
                {k:a['s']['inv'][1] for k in ALL_SERIES})
    pages = {}
    for name, p in ta_old['pages'].items():
        r, i2 = page_series(name)
        cmps = []
        for c in p['cmp']:
            look = {'New York City':'NYC','NYC':'NYC'}.get(c['label'], c['label'])
            a = by_name.get(look)
            cmps.append({'label':c['label'],
                         'rent':{k:a['s'][k][1] for k in ALL_SERIES},
                         'inv':{k:a['s']['inv'][1] for k in ALL_SERIES}} if a else c)
        pages[name] = {'self':r, 'selfinv':i2, 'cmp':cmps, 'title':p['title']}
    trends_all = {'months':months, 'beds':ta_old['beds'], 'pages':pages}

    # ---- the four GeoJSON files that hold only the current month ----
    GEO_KEYS = {'rent_studio':'studio','rent_1br':'br1','rent_2br':'br2',
                'rent_3br':'br3','rent_all':'all','inv':'inv'}
    geo_writes = []
    for path, keyfn in [('citywide-rents.geojson',   lambda p: p.get('cb_code')),
                        ('neighborhood-rents.geojson',lambda p: ALIAS.get(p.get('nb'), p.get('nb'))),
                        ('borough-rents.geojson',    lambda p: p.get('boro')),
                        ('bk-rents.geojson',         lambda p: ('BK'+p['cb_code']) if str(p.get('cb_code','')).startswith('CB') else p.get('cb_code'))]:
        full = os.path.join(DATA, path)
        if not os.path.exists(full): continue
        g = json.load(open(full))
        for f in g['features']:
            p = f['properties']; a = by_name.get(keyfn(p))
            if not a: continue
            for pk, sk in GEO_KEYS.items():
                if pk in p and sk in a['s']:
                    v = a['s'][sk][1][last_i]
                    if v is not None: p[pk] = v
        geo_writes.append((full, g))

    # ---- write everything, only now that every check has passed ----
    def write(name, obj):
        with open(os.path.join(DATA, name), 'w') as fh:
            json.dump(obj, fh, separators=(',',':'))
        return name

    written = [write('rent-explorer.json', explorer),
               write('inventory-by-bed.json', ib),
               write('cc-rents.json', cc),
               write('rent-subranges.json', subranges),
               write('rent-ranges-rollup.json', rollup),
               write('cb6-rent-trends.json', cb6_trends),
               write('cb6-nbhd-history.json', cb6_nbhd),
               write('rent-trends-all.json', trends_all)]
    for path, d in rank_out.items():
        written.append(write(path, d))
    for full, g in geo_writes:
        with open(full,'w') as fh: json.dump(g, fh, separators=(',',':'))
        written.append(os.path.basename(full))

    # ---- final sweep: nothing left behind at an older month ----
    stale = []
    for fn in os.listdir(DATA):
        if not fn.endswith('.json'): continue
        if not any(t in fn for t in ('rent','rank-history','inventory-by-bed','nbhd')): continue
        try: d = json.load(open(os.path.join(DATA,fn)))
        except Exception: continue
        ms = d.get('months') if isinstance(d, dict) else None
        if isinstance(d, dict) and not ms:
            for v in list(d.values())[:5]:
                if isinstance(v, dict) and 'months' in v: ms = v['months']; break
        if ms and ms[-1] != LAST: stale.append((fn, ms[-1]))
    if stale:
        die('these files are still at an older month: %s' % stale)

    print()
    print('Wrote %d files, all at %s:' % (len(written), LAST))
    for w in sorted(set(written)): print('   ' + w)
    print()
    print('Council districts covered: %d of 51' % len(cds))
    print('Community districts: %d   Neighborhoods: %d'
          % (len([a for a in areas if a['t']=='cd']),
             len([a for a in areas if a['t']=='neighborhood'])))
    print()
    print('Next: bump the cache version in sw.js, commit, and deploy.')
    shutil.rmtree(work, ignore_errors=True)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    main(sys.argv[1])
