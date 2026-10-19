"""Put the charter org chart movie (assets/charter-movie.js) under the NYC org chart header:
govhub.html loads the script; the app copy (app/data/civic/orgchart/orgchart.html) gets the script and the officeholder data inline so it works offline."""
import json, re
V = '20261018c'
A, B = '<!--chartermovie-->', '<!--/chartermovie-->'
ANCHOR = re.compile(r'(<h2>🏛️ How NYC Government Is Organized</h2>.*?<p>Tap any section to expand\. Tap an agency to see what it does\.</p>\s*</div>)', re.S)
def put(path, block):
    s = open(path, encoding='utf-8').read()
    while A in s:
        i = s.index(A); j = s.index(B, i) + len(B); s = s[:i] + s[j:]
    s, n = ANCHOR.subn(lambda m: m.group(1) + '\n' + A + block + B, s, count=1)
    assert n == 1, path
    open(path, 'w', encoding='utf-8').write(s)
def wrap(link):
    return ('<div style="padding:12px 12px 0"><details class="cmx" style="background:#fff;border:2px solid #0d1b4b;border-radius:12px;overflow:hidden">'
            '<summary style="cursor:pointer;padding:12px 14px;font-family:\'DM Sans\',sans-serif;font-weight:800;color:#0d1b4b;font-size:.92rem">Watch the org chart change since 1898'
            '<span style="display:block;font-weight:400;color:#6b6b6b;font-size:.74rem;margin-top:2px">Pick a date or press play: officeholders, the Board of Estimate, the Council&rsquo;s seats</span></summary>'
            '<div style="padding:0 10px 10px"><div data-charter-movie></div>'
            '<a href="' + link + '" style="display:inline-block;font-family:\'DM Sans\',sans-serif;font-size:.8rem;font-weight:800;background:#f47920;color:#fff;text-decoration:none;border-radius:8px;padding:9px 14px">Who held every office on any date, with maps &rarr;</a>'
            '</div></details></div>')
put('govhub.html', wrap('/throughtime/') + '<script src="/assets/charter-movie.js?v=' + V + '"></script>')
al = json.load(open('data/districthistory/at-large.json'))
keep = {'mayor', 'comptroller', 'pa', 'speaker', 'bp'}
sub = {'offices': [o for o in al['offices'] if o['key'] in keep]}
js = open('assets/charter-movie.js', encoding='utf-8').read()
put('app/data/civic/orgchart/orgchart.html', wrap('https://bkcb6.app/throughtime/') + '<script>window.CHARTER_AL=' + json.dumps(sub, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + ';</script><script>' + js.replace('</script', '<\\/script') + '</script>')
print('ok')
