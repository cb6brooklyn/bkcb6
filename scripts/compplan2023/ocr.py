import json,subprocess,collections
from PIL import Image
L=json.load(open('lines.json'))
P=collections.defaultdict(list)
for x in L: P[x[0]].append(x)
out={}
for p in list(range(14,126))+list(range(150,161)):
    body=sum(1 for x in P[p] if x[5].startswith('Garamond') and x[2]<725)
    if body>3: continue
    im=Image.open(f'png/p{p:03d}.png')
    W,H=im.size
    im.crop((0,0,W,int(H*.30))).save('/tmp/ocr.png')
    t=subprocess.run(['tesseract','/tmp/ocr.png','-','--psm','11'],capture_output=True,text=True).stdout
    out[p]=[s.strip() for s in t.split('\n') if s.strip()]
json.dump(out,open('ocr.json','w'),indent=0)
for p,v in out.items(): print(p,' | '.join(v[:6])[:150])
