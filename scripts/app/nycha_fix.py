import sys, os, json
R = sys.argv[1]; OUT = sys.argv[2]
p = os.path.join(R, 'BKCB6/App/Views/NYCHAView.swift'); s = open(p).read()
if 'FileParts("nycha"' in s: print('nycha already'); sys.exit()
names = ['mapSection', 'directorySection', 'applySection', 'sourceNote']; ids = ['map', 'directory', 'apply', 'source']
old = '                    if model.loaded {\n' + ''.join(f'                        {n}\n' for n in names) + '                    } else {'
assert old in s, 'nycha'
ind = ' ' * 24
cases = ''.join(f'{ind}    case "{i}": AnyView(Group {{\n{ind}{n}\n{ind}    }})\n' for i, n in zip(ids, names))
body = f'FileParts("nycha", {json.dumps(ids)}) {{ part in\n{ind}    switch part {{\n{cases}{ind}    default: AnyView(EmptyView())\n{ind}    }}\n{ind}}}'
s = s.replace(old, '                    if model.loaded {\n' + ind + body + '\n                    } else {', 1); open(p, 'w').write(s)
r = OUT; reg = json.load(open(r)) if os.path.exists(r) else {}; reg['nycha'] = [{'id': i} for i in ids]; json.dump(reg, open(r, 'w'), indent=1, sort_keys=True)
print('nycha ok')
