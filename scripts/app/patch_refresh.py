import sys,os,re
H='/Users/user301938'; app=sys.argv[1]; P=f'{H}/{app}/BKCB6/App/Views/'
dk=P+'DistrictKit.swift'; s=open(dk).read()
if 'struct DataRefreshRow' not in s: s+=open(H+'/refreshrow.swift').read(); open(dk,'w').write(s)
n=0
for fn in ['BKHome.swift','HomeView.swift']:
    p=P+fn
    if not os.path.exists(p): continue
    s=open(p).read()
    s2=re.sub(r'if let d = store\.dataUpdated \{\n\s*Text\((?:LocalizedStringKey\()?"Data checked [^\n]*\n\s*\.font\(DM\.mono\(11\)\)\.foregroundStyle\(Color\.cb6Muted\)\.padding\(\.top, (\d+)\)\n\s*\}',
             lambda m: f'DataRefreshRow().padding(.top, {m.group(1)})', s)
    if s2!=s: open(p,'w').write(s2); n+=1
print(app,'home screens patched',n)
