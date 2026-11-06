import json,re,sys
tpl,out=sys.argv[1],sys.argv[2]
s=open(tpl).read()
san=open('/root/bkcb6/sanitation-policy/index.html').read()
tok=re.search(r"const TOKEN='([^']+)'",san).group(1)
css=open('css.txt').read()
s=s.replace('{{CSS}}',css).replace('{{ICO}}',json.dumps(json.load(open('ico.json')),separators=(',',':'))).replace('{{TOKEN}}',tok)
assert '{{' not in s
open(out,'w').write(s); print(out,len(s))
