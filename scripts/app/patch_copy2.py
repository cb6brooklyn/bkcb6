import re,sys,os,glob,json,hashlib
H='/Users/user301938'
app=sys.argv[1]; P=f'{H}/{app}/BKCB6/App/Views/'
reg={}
def key(stem,text): return f'{stem}.{hashlib.sha1(text.encode()).hexdigest()[:8]}'
def ok(text):
    if len(text)<2 or not re.search(r'[A-Za-z]',text) or text.startswith('http'): return False
    if re.fullmatch(r'[a-z0-9_.:/-]+',text): return False
    return True

def scan_literal(s, i):
    """s[i] == '"'. Returns (end index after closing quote, template, [interpolation exprs]) or None."""
    assert s[i]=='"'
    j=i+1; out=''; args=[]
    while j<len(s):
        c=s[j]
        if c=='\\':
            if s[j+1]=='(':
                # interpolation: find matching ) with nested parens and strings
                k=j+2; depth=1; instr=False
                while k<len(s) and depth>0:
                    ch=s[k]
                    if instr:
                        if ch=='\\': k+=1
                        elif ch=='"': instr=False
                    else:
                        if ch=='"': instr=True
                        elif ch=='(': depth+=1
                        elif ch==')': depth-=1
                    k+=1
                expr=s[j+2:k-1]
                out+='{%d}'%len(args); args.append(expr); j=k; continue
            out+=s[j:j+2]; j+=2; continue
        if c=='"': return j+1, out, args
        if c=='\n': return None
        out+=c; j+=1
    return None

LABELS=('title','subtitle','text','label','name','caption','body','hint','intro','sub','detail','note','placeholder','message','footer','header','prompt','headline','kicker','line','about','blurb','summary','description','question','answer','tagline','lead','explainer','why','what','how','tip','warning','empty','emptyText','value')
CALLS=('Text','Button','Label','TextField','NavyHeader','alertCard','placeRow','SectionHeader','DKHeader','DKChip','cb6Page','navigationTitle','alert','confirmationDialog','infoRow','row','bullet','para','p','h','h2','h3','note','callout','DKLegendDot')

def transform(s, stem):
    out=''; i=0; n=0
    while i<len(s):
        c=s[i]
        if c!='"': out+=c; i+=1; continue
        # already wrapped?
        before=s[max(0,i-40):i]
        if re.search(r'(Copy\.[tf]|MapStyle\.(label|color|number))\($', before) or re.search(r'(Copy\.[tf]|MapStyle\.(label|color|number))\("[^"]*", $', before):
            # this literal is the key or fallback of an existing wrap: copy it through
            r=scan_literal(s,i)
            if r is None: out+=c; i+=1; continue
            out+=s[i:r[0]]; i=r[0]; continue
        if s.startswith('"""',i):
            out+='"""'; i+=3; continue
        r=scan_literal(s,i)
        if r is None: out+=c; i+=1; continue
        end,tpl,args=r
        # what is this literal an argument of?
        m=re.search(r'(?:(\w+)\(|(\w+): |\.(\w+)\()\s*$', before)
        role=None
        if m:
            if m.group(2) and m.group(2) in LABELS: role='label'
            elif (m.group(1) or m.group(3)) in CALLS: role='call'
        if role is None or not ok(tpl) or 'specifier:' in ''.join(args) or 'Image(' in ''.join(args) or '{0}' in tpl and not args:
            out+=s[i:end]; i=end; continue
        if not args and len(tpl)<2: out+=s[i:end]; i=end; continue
        k=key(stem,tpl); reg[k]=tpl.replace('\\"','"')
        isText = bool(m and (m.group(1)=='Text' or m.group(3)=='Text')) and re.match(r'\s*\)', s[end:end+4]) is not None
        if args:
            call=f'Copy.f("{k}", "{tpl}", {", ".join(args)})'
            if isText: call='verbatim: '+call
        else:
            call=f'Copy.t("{k}", "{tpl}")'
            if isText: call='LocalizedStringKey('+call+')'
        out+=call; i=end; n+=1
    return out,n
total=0
for fn in sorted(glob.glob(P+'*.swift')):
    stem=os.path.basename(fn)[:-6]
    s=open(fn).read()
    s2,n=transform(s,stem)
    if n: open(fn,'w').write(s2); total+=n
dk=P+'DistrictKit.swift'; s=open(dk).read()
if 'static func f(_ key: String' not in s:
    s=s.replace('''        return cache?[key] ?? fallback
    }
}''','''        return cache?[key] ?? fallback
    }
    /// A sentence with values in it: "{0}", "{1}"... stand for the values, in order.
    static func f(_ key: String, _ fallback: String, _ args: Any...) -> String {
        var s = t(key, fallback)
        for (i, a) in args.enumerated() { s = s.replacingOccurrences(of: "{\\(i)}", with: "\\(a)") }
        return s
    }
}''',1)
    assert 'static func f(_ key: String' in s
    open(dk,'w').write(s)
json.dump(reg,open(f'{H}/copy2-{app}.json','w'),ensure_ascii=False,indent=0)
print(app,'more strings wrapped',total,'registry',len(reg))
