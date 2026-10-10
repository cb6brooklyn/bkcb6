import re,sys,os,glob,json,hashlib
H='/Users/user301938'
app=sys.argv[1]; P=f'{H}/{app}/BKCB6/App/Views/'
reg={}
def key(stem,text):
    return f'{stem}.{hashlib.sha1(text.encode()).hexdigest()[:8]}'
STR=r'"((?:[^"\\\n]|\\[^(])*)"'   # a one-line string literal with no \( interpolation
def ok(text):
    if len(text)<2 or not re.search(r'[A-Za-z]',text) or text.startswith('http'): return False
    if re.fullmatch(r'[a-z0-9_.:/-]+',text): return False      # a key, a symbol name, a slug
    return True
def wrap(stem,text):
    k=key(stem,text); reg[k]=text.replace('\\"','"')
    return f'Copy.t("{k}", "{text}")'
total=0
for fn in sorted(glob.glob(P+'*.swift')):
    stem=os.path.basename(fn)[:-6]
    if stem in ('DistrictKit',) and False: pass
    s=open(fn).read(); o=s
    def sub(pattern, s, group=1, lsk=False):
        def rep(m):
            text=m.group(group)
            if not ok(text): return m.group(0)
            w=wrap(stem,text)
            if lsk: w='LocalizedStringKey('+w+')'
            return m.group(0)[:m.start(group)-m.start()-1]+w+m.group(0)[m.end(group)-m.start()+1:]
        return re.sub(pattern,rep,s)
    s=sub(r'(?<![\w.])Text\('+STR+r'\)',s,lsk=True)
    s=sub(r'\.navigationTitle\('+STR+r'\)',s)
    s=sub(r'\.cb6Page\((?:[^,\n]+), '+STR,s)
    s=sub(r'\.cb6Page\('+STR,s)
    s=sub(r'SectionHeader\(text: '+STR,s)
    s=sub(r'DKHeader\(text: '+STR,s)
    s=sub(r'(?<![\w.])Label\('+STR+r',',s)
    s=sub(r'(?<![\w.])Button\('+STR+r'[,)]',s)
    s=sub(r'TextField\('+STR+r',',s)
    s=sub(r'\.alert\('+STR+r',',s)
    s=sub(r'\.confirmationDialog\('+STR+r',',s)
    s=sub(r'DKChip\(text: '+STR,s)
    s=sub(r'DKLegendDot\(color: [^,\n]+, text: '+STR+r'\)',s)
    if s!=o:
        open(fn,'w').write(s); total+=s.count('Copy.t(')-o.count('Copy.t(')
# Copy itself
dk=P+'DistrictKit.swift'; s=open(dk).read()
if 'enum Copy ' not in s and 'enum Copy{' not in s: s+=open(H+'/copy.swift').read(); open(dk,'w').write(s)
json.dump(reg,open(f'{H}/copy-{app}.json','w'),ensure_ascii=False,indent=0)
print(app,'strings wrapped',total,'registry',len(reg))
