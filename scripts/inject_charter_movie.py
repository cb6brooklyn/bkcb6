"""Put the charter org chart movie (assets/charter-movie.js) under the NYC org chart header:
govhub.html loads the script; the app copy (app/data/civic/orgchart/orgchart.html) gets the script and the officeholder data inline so it works offline."""
import json, re
V = '20261018a'
A, B = '<!--chartermovie-->', '<!--/chartermovie-->'
ANCHOR = re.compile(r'(<h2>🏛️ How NYC Government Is Organized</h2>.*?<p>Tap any section to expand\. Tap an agency to see what it does\.</p>\s*</div>)', re.S)
def put(path, block):
    s = open(path, encoding='utf-8').read()
    while A in s:
        i = s.index(A); j = s.index(B, i) + len(B); s = s[:i] + s[j:]
    s, n = ANCHOR.subn(lambda m: m.group(1) + '\n' + A + block + B, s, count=1)
    assert n == 1, path
    open(path, 'w', encoding='utf-8').write(s)
wrap = '<div style="padding:12px 12px 0"><div data-charter-movie></div></div>'
put('govhub.html', wrap + '<script src="/assets/charter-movie.js?v=' + V + '"></script>')
al = json.load(open('data/districthistory/at-large.json'))
keep = {'mayor', 'comptroller', 'pa', 'speaker', 'bp'}
sub = {'offices': [o for o in al['offices'] if o['key'] in keep]}
js = open('assets/charter-movie.js', encoding='utf-8').read()
put('app/data/civic/orgchart/orgchart.html', wrap + '<script>window.CHARTER_AL=' + json.dumps(sub, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + ';</script><script>' + js.replace('</script', '<\\/script') + '</script>')
print('ok')
