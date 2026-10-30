import os,re,html,datetime,email.utils
import os
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','news')+'/'
items=[]
for f in sorted(os.listdir(R)):
    if not re.match(r'\d{4}-\d\d-\d\d-.*\.html$',f): continue
    s=open(R+f).read()
    a=re.search(r'<article>(.*?)</article>',s,re.S)
    if not a: print('noart',f); continue
    a=a.group(1)
    t=re.search(r'<h1>(.*?)</h1>',a,re.S).group(1).strip()
    m=re.search(r"<time datetime=\"([^\"]+)\"",a)
    dt=m.group(1) if m else f[:10]+'T09:00:00-04:00'
    i=a.find('</div>',a.find('class="byline"'))+6
    j=a.find('<div class="signoff">')
    if j<0:
        j=a.find('<p class="source-note"');j=len(a) if j<0 else j
        sign=''
    else:
        k=a.find('</div>',j)+6;sign=a[j:k]
    body=a[i:j].strip()
    body=re.sub(r'<iframe[^>]*></iframe>','',body)
    body=re.sub(r'href="/',r'href="https://bkcb6.app/',body)
    body=re.sub(r'src="/',r'src="https://bkcb6.app/',body)
    content=body+(('\n<p>'+re.sub(r'<div class="signoff">|</div>','',sign).strip()+'</p>') if sign else '')
    desc=re.search(r'<meta name="description" content="([^"]*)"',s)
    d=datetime.datetime.fromisoformat(dt)
    items.append((d,t,f,desc.group(1) if desc else '',content))
items.sort(reverse=True)
out=['<?xml version="1.0" encoding="UTF-8"?>','<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/"><channel>','<title>The CB6 Newsletter</title><link>https://bkcb6.app/news/</link><description>District Manager Mike Racioppo\'s newsletter for Brooklyn Community Board 6.</description><language>en-us</language>']
for d,t,f,desc,c in items:
    url='https://bkcb6.app/news/'+f
    out.append('<item><title>%s</title><link>%s</link><guid isPermaLink="true">%s</guid><dc:creator>Mike Racioppo</dc:creator><pubDate>%s</pubDate><description>%s</description><content:encoded><![CDATA[%s]]></content:encoded></item>'%(t,url,url,email.utils.format_datetime(d),desc,c.replace(']]>',']]&gt;')))
out.append('</channel></rss>')
open(R+'feed-full.xml','w').write('\n'.join(out))
print(len(items), os.path.getsize(R+'feed-full.xml')//1024,'KB')
