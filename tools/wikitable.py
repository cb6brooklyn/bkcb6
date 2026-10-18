import re
MON={m:i+1 for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'])}
def strip_tpl(s,names):
    out=[];i=0
    while i<len(s):
        m=re.compile(r'\{\{\s*(?:%s)\s*\|'%'|'.join(names),re.I).search(s,i)
        if not m: out.append(s[i:]);break
        out.append(s[i:m.start()]);d=0;j=m.start()
        while j<len(s):
            if s.startswith('{{',j):d+=1;j+=2;continue
            if s.startswith('}}',j):
                d-=1;j+=2
                if d==0:break
                continue
            j+=1
        i=j
    return ''.join(out)
def clean(s):
    s=strip_tpl(s,['efn','efn-ua','efn-lr','refn','sfn','Efn','NoteTag','note'])
    s=re.sub(r'<ref[^>]*/>','',s)
    s=re.sub(r'<ref[^>]*>.*?</ref>','',s,flags=re.S)
    s=re.sub(r'<!--.*?-->','',s,flags=re.S)
    return s
def dates(s):
    out=[]
    for m in re.finditer(r'\{\{(?:dts|start date|end date|date|Start date|End date|Dts)\|(\d{4})\|(\d{1,2})\|(\d{1,2})[^}]*\}\}|((?:%s))\s+(\d{1,2}),?\s+(\d{4})|(\d{1,2})\s+((?:%s))\s+(\d{4})|((?:%s))\s+(\d{4})|\b(present|incumbent|Incumbent|Present)\b'%('|'.join(MON),'|'.join(MON),'|'.join(MON)),s):
        g=m.groups()
        if g[0]:out.append('%s-%02d-%02d'%(g[0],int(g[1]),int(g[2])))
        elif g[3]:out.append('%s-%02d-%02d'%(g[5],MON[g[3]],int(g[4])))
        elif g[6]:out.append('%s-%02d-%02d'%(g[8],MON[g[7]],int(g[6])))
        elif g[9]:out.append('%s-%02d-01'%(g[10],MON[g[9]]))
        else:out.append(None)
    return out
def person(s):
    s=re.sub(r'\[\[(?:File|Image):[^\]]*\]\]','',s)
    m=re.search(r"'''\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'''",s) or re.search(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]",s)
    if not m:return None
    return (m.group(2) or m.group(1)).strip()
def rows(table):
    return [r for r in re.split(r'\n\|-[^\n]*',table)]
def tables(w):
    return re.findall(r'\{\|.*?\n\|\}',w,flags=re.S)
