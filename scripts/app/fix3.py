import re, glob
H = '/Users/user301938'
for a in ('bkcb6app', 'bkcivics', 'cb6beyond'):
    n = 0
    for fn in glob.glob(f'{H}/{a}/BKCB6/App/Views/*.swift') + glob.glob(f'{H}/{a}/BKCB6/App/Services/*.swift') + glob.glob(f'{H}/{a}/BKCB6/Shared/*.swift'):
        s = open(fn).read(); o = s
        # untyped tables whose keys are strings in the code were typed with Int keys: give them String keys
        s = re.sub(r'var (\w+): \[Int: String\] \{ Lists\.intKeyed\("([^"]+)", \[\s*"', r'var \1: [String: String] { Lists.dict("\2", ["', s)
        s = re.sub(r'var (\w+): \[Int: Color\] \{ Lists\.colorDictInt\("([^"]+)", \[\s*"', r'var \1: [String: Color] { Lists.colorDict("\2", ["', s)
        if s != o: open(fn, 'w').write(s); n += len(re.findall(r'Lists\.dict\(|Lists\.colorDict\(', s)) - len(re.findall(r'Lists\.dict\(|Lists\.colorDict\(', o))
        for m in re.finditer(r'var (\w+): (\[Int: \w+\]) \{ Lists\.(\w+)\("([^"]+)", \[\s*(\S{0,12})', s):
            print(a, fn.split('/')[-1], m.group(1), m.group(2), m.group(3), 'first key', m.group(5))
    print(a, 'retyped', n)
