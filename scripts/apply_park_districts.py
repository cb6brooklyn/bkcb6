"""Write the computed districts onto every park page. Nothing is parsed from the
agency's fields; every value here came from geometry."""
import json, re, glob, os

R='/home/claude/repo/'
D=json.load(open('/home/claude/park_all_districts.json'))
BORO={'1':'Manhattan','2':'The Bronx','3':'Brooklyn','4':'Queens','5':'Staten Island'}
ORDER=['1','2','3','4','5']
JIA={'164':'Central Park','226':'Van Cortlandt Park','227':'Bronx Park','228':'Pelham Bay Park',
     '355':'Prospect Park','356':'Brooklyn Gateway National Recreation Area',
     '480':'LaGuardia Airport','481':'Flushing Meadows Corona Park','482':'Forest Park',
     '483':'JFK International Airport','484':'Queens Gateway National Recreation Area',
     '595':'Staten Island Gateway National Recreation Area'}

def join(parts):
    if not parts: return ''
    if len(parts)==1: return parts[0]
    return ', '.join(parts[:-1]) + ' and ' + parts[-1]

def cd_phrase(codes):
    boards=sorted([c for c in codes if c not in JIA],
                  key=lambda c:(ORDER.index(c[0]), int(c[1:])))
    jias=sorted([c for c in codes if c in JIA], key=lambda c: JIA[c])
    parts=[]; byboro={}
    for c in boards: byboro.setdefault(c[0],[]).append(int(c[1:]))
    for b in ORDER:
        if b not in byboro: continue
        ns=sorted(byboro[b])
        parts.append(f"{BORO[b]} Community Board{'s' if len(ns)>1 else ''} "+join([str(n) for n in ns]))
    parts += [f"{JIA[c]} ({BORO[c[0]]} joint interest area)" for c in jias]
    return join(parts)

def nums(codes):
    return join([str(n) for n in sorted(int(c) for c in codes)])

def ordinal(n):
    n=int(n)
    if 10 <= n % 100 <= 20: suf='th'
    else: suf={1:'st',2:'nd',3:'rd'}.get(n%10,'th')
    return f'{n}{suf}'

def pct_phrase(codes):
    # the row is already labelled Precinct, so do not repeat the word
    return join([ordinal(c) for c in sorted(codes, key=int)])

FIELD=[('District','cd',cd_phrase),
       ('Council','cc',nums),
       ('Assembly','ad',nums),
       ('Senate','sd',nums),
       ('Precinct','pct',pct_phrase)]

changed=collections_changed=0
per=dict(District=0,Council=0,Assembly=0,Senate=0,Precinct=0)
skipped=[]
for f in sorted(glob.glob(R+'park/*.html')):
    s=open(f,encoding='utf-8').read()
    gm=re.search(r'Parks ID</span><span class="v">([^<]*)</span>', s)
    if not gm: skipped.append((os.path.basename(f),'no parks id')); continue
    gid=gm.group(1).strip()
    rec=D.get(gid)
    if not rec: skipped.append((os.path.basename(f),'no assignment')); continue
    touched=False
    for label,key,fn in FIELD:
        codes=rec.get(key)
        if not codes: continue
        new=fn(codes)
        m=re.search(r'(<li><span class="k">'+label+r'</span><span class="v">)([^<]*)(</span></li>)', s)
        if not m: continue
        if m.group(2)!=new:
            s=s[:m.start()]+m.group(1)+new+m.group(3)+s[m.end():]
            per[label]+=1; touched=True
    if touched:
        open(f,'w',encoding='utf-8').write(s); changed+=1
print('pages changed:', changed)
for k,v in per.items(): print(f'   {k:9} {v:5} pages')
print('skipped:', len(skipped), skipped[:5])
