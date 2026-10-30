"""Append interactive tool embeds + graphics to news archive pages that link to bkcb6.app tools."""
import os,re,html
R=os.path.join(os.path.dirname(__file__),'..','news')+'/'
T='https://bkcb6.app/press/newsletter/'
TOOLS={ # key: (path, title, graphic)
'blockbyblock':('blockbyblock/','Block by Block','https://bkcb6.app/tiles/blockbyblock.png'),
'useofland':('useofland/','The Use of Land Hub','https://bkcb6.app/og-useofland.png'),
'elections':('elections/','The Elections Hub','https://bkcb6.app/og-cb6-votes.png'),
'poll-finder-bk':('poll-finder-bk.html','Where Do I Vote?',None),
'spookycb6':('spookycb6/','Spooky CB6',T+'tile-spookycb6-2026.png'),
'spooky':('spookycb6/','Spooky CB6',T+'tile-spookycb6-2026.png'),
'rents':('rents/','Rents, Then and Now','https://bkcb6.app/tiles/rents.png'),
'landusemap':('landusemap/','Land Use & Zoning Map','https://bkcb6.app/tiles/landusemap.png'),
'gowanus':('gowanus.html','Gowanus Rezoning','https://bkcb6.app/tiles/gowanus.png'),
'bergndeanblvd':('bergndeanblvd/','Dean & Bergen Bike Boulevard',T+'tile-bergndeanblvd.png'),
'sammyslaw':('sammyslaw/','Sammy’s Law, daylighting and low traffic neighborhoods','https://bkcb6.app/sammyslaw/og.jpg'),
'housecostavail':('housecostavail/','Housing, costs & availability in CB6, BK & NYC',T+'tile-housecostavail.png'),
'cooldown':('cooldown.html','CB6 Weather & Safety','https://bkcb6.app/og-cb6-cooldown.png'),
'cobble-hill-health-center':('cobble-hill-health-center/','Cobble Hill Health Center',None),
'marathon':('marathon/','2026 TCS NYC Marathon in CB6',T+'tile-marathon-2026.png'),
'knicks':('knicks/','Knicks Parade Route','https://bkcb6.app/knicks-og.png'),
'friends-of-fort-defiance':('friends-of-fort-defiance/','Friends of Fort Defiance',None),
'fhgs':('fhgs/','Fair Housing Growth Strategy',T+'tile-fhgs.png'),
'electionexplainer':('electionexplainer/','An Attempt to Explain Your Ballot',T+'tile-electionexplainer-2026.png'),
'november2026':('electionexplainer/','An Attempt to Explain Your Ballot',T+'tile-electionexplainer-2026.png'),
'early-vote-map':('early-vote-map.html','Early Voting by Election District','https://bkcb6.app/og-early-vote.png'),
'budgetsurvey':('budgetsurvey/','District Needs Survey',T+'tile-survey.png'),
'bkcompplan':('bkcompplan/','The 2025 Comprehensive Plan for Brooklyn',T+'tile-bkcompplan.png'),
'250baltic':('250baltic/','250 Baltic Street','https://bkcb6.app/og-250baltic.jpg'),
'2026primary':('2026primary.html','2026 Votes in CB6','https://bkcb6.app/og-cb6-votes.png'),
'zoninghistory':('zoninghistory/','CB6 Zoning, 1961 to Today',T+'tile-zoninghistory.png'),
'calendar':('calendar.html','Community Calendar',T+'tile-calendar.png'),
'jobs':('jobs/','Jobs',T+'tile-jobs.png'),
}
LINK=re.compile(r'href="https?://(?:www\.)?bkcb6\.app/([a-z0-9_-]+)(?:\.html)?/?(?:index\.html)?["#?]')
KW=[ # (regex on article text, tool key)
 (r'gowanus[^.]{0,80}rezon|rezon[^.]{0,80}gowanus','gowanus'),
 (r'\b(early voting|election day|polls are open|primary election|general election|ballot)\b','elections'),
 (r'halloween|trick-or-treat|spooky','spookycb6'),
 (r'\bmarathon\b','marathon'),
 (r'comprehensive plan','bkcompplan'),
 (r'fair housing','fhgs'),
 (r'bike boulevard|bergen street[^.]{0,60}dean|dean street[^.]{0,60}bergen','bergndeanblvd'),
 (r'cobble hill health center','cobble-hill-health-center'),
 (r"sammy.s law|daylighting",'sammyslaw'),
 (r'cooling cent|heat advisory|heat emergency','cooldown'),
 (r'fort defiance','friends-of-fort-defiance'),
 (r'district needs|budget survey|needs survey','budgetsurvey'),
 (r'\bzoning\b|land use','landusemap'),
 (r'\brent(s|al)?\b[^.]{0,40}(median|asking|afford|stabiliz)','rents'),
]
import json
EXTRA=json.load(open(R+'extra_tools.json')) if os.path.exists(R+'extra_tools.json') else {} # page -> tool keys from the email's Happenings tiles
START='<section class="tools-embed"';END='</section><!--/tools-embed-->'
def section(keys,related=()):
    out=['<section class="tools-embed" style="margin:34px 0 10px;border-top:1px solid #e5dcc8;padding-top:18px">',
         '<h2 style="font-size:1.15rem;margin:0 0 12px">%s</h2>'%('Interactive in this issue' if keys else 'Related tools')]
    allk=list(keys)+[k for k in related]
    for i,k in enumerate(allk):
        if i==len(keys) and keys and related: out.append('<h2 style="font-size:1.05rem;margin:20px 0 12px">Related tools</h2>')
        p,t,g=TOOLS[k];u='https://bkcb6.app/'+p
        out.append('<figure style="margin:0 0 26px">'
          +('<a href="%s"><img src="%s" alt="%s" loading="lazy" style="display:block;width:100%%;max-width:560px;height:auto;margin:0 auto 10px;border-radius:8px"></a>'%(u,html.escape(g),html.escape(t)) if g else '')+
          '<iframe src="%s" title="%s" loading="lazy" style="width:100%%;height:640px;border:1px solid #e5dcc8;border-radius:10px;background:#fff" allowfullscreen></iframe>'
          '<figcaption style="font-size:.9rem;margin-top:6px"><a href="%s">Open %s full screen &rarr;</a></figcaption></figure>'%(u,html.escape(t),u,html.escape(t)))
    out.append(END)
    return '\n'.join(out)
n=0
for f in sorted(os.listdir(R)):
    if not re.match(r'\d{4}-\d\d-\d\d-.*\.html$',f): continue
    s=open(R+f).read()
    s=re.sub(re.escape(START)+r'.*?'+re.escape(END)+r'\n?','',s,flags=re.S)
    a=s.find('<article>');b=s.find('</article>')
    keys=[]
    for k in LINK.findall(s[a:b]):
        if k in TOOLS and TOOLS[k][0] not in [TOOLS[x][0] for x in keys]: keys.append(k)
    for k in EXTRA.get(f,[]):
        if k in TOOLS and TOOLS[k][0] not in [TOOLS[x][0] for x in keys]: keys.append(k)
    txt=re.sub(r'<[^>]+>',' ',s[a:b]).lower()
    have={TOOLS[k][0] for k in keys};rel=[]
    for rx,k in KW:
        if len(rel)>=3: break
        if TOOLS[k][0] not in have and re.search(rx,txt): rel.append(k);have.add(TOOLS[k][0])
    if keys or rel:
        art=s[a:b]
        pos=art.find('<div class="signoff">')
        if pos<0: pos=art.find('<p class="source-note"')
        if pos<0: pos=len(art)
        art=art[:pos]+section(keys,rel)+'\n\n    '+art[pos:]
        s=s[:a]+art+s[b:];n+=1
    open(R+f,'w').write(s)
print('pages with embeds',n)
