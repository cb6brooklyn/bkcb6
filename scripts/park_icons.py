#!/usr/bin/env python3
"""NYC Parks icons on every map page that draws the parks layer, the way schools and libraries carry theirs:
one logo badge per named park property at the center of its shape (strips, malls, parkways, undeveloped lots and
unnamed properties get none), with the park's name, type and acres on tap. The badge toggles with the parks layer.
Re-runnable: pages already carrying parkIconMarker are left alone."""
import glob, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = ('.resource-marker-icon.resource-marker-parks{width:36px;height:36px;border-radius:10px;padding:2px;box-sizing:border-box;background:rgba(255,255,255,.98);'
       'border:2px solid rgba(255,255,255,.98);box-shadow:0 3px 11px rgba(15,23,42,.24)}\n'
       '.resource-marker-icon.resource-marker-parks img{max-width:30px;max-height:30px;width:100%;height:100%;object-fit:contain;border-radius:7px}\n')
JS = '''var PARK_ICON_SKIP = {'Strip':1,'Undeveloped':1,'Lot':1,'Parkway':1,'Mall':1,'Managed Sites':1,'Operations':1,'Retired N/A':1};
function parkIconMarker(f, l, seen){
  var p = f.properties || {}; if(p._supplemental_park) return null;
  var name = parkTooltipName(p); if(!name || name === 'Park' || PARK_ICON_SKIP[p.typecategory]) return null;
  if(seen[name]) return null; seen[name] = 1;
  var c; try { c = l.getBounds().getCenter(); } catch(e) { return null; }
  var icon = L.divIcon({className:'resource-icon-wrap', html:'<div class="resource-marker-icon resource-marker-parks" title="'+escH(name)+'"><img src="assets/map-icons/nyc-parks-logo.png" alt="NYC Parks"></div>', iconSize:[36,36], iconAnchor:[18,18], popupAnchor:[0,-16], tooltipAnchor:[0,-16]});
  var m = L.marker(c, {icon:icon, riseOnHover:true});
  m.bindTooltip('<strong>'+escH(name)+'</strong><br>'+escH(p.typecategory||'NYC Parks'), {sticky:true});
  m.bindPopup('<h4>'+escH(name)+'</h4><p>'+escH(p.address||p.location||'NYC Parks property')+'</p><div class="small">'+escH((p.typecategory||'Park')+(p.acres?' · '+(Math.round(Number(p.acres)*10)/10)+' acres':''))+'</div>');
  return m;
}
'''
TOOLTIP = '''function parkTooltipName(p){
  p = p || {};
  return p.signname || p.name || p.name311 || p.Name || 'Park';
}
'''
PAT = re.compile(r"  parksLayer = L\.geoJSON\(\{type:'FeatureCollection',features:pkFeatures\},\{\n    style:(?P<style>[^\n]*),\n    onEachFeature:\(f,l\)=>l\.bindTooltip\((?P<tip>[^\n]*?),\{sticky:true\}\)\n  \}\);\n  if\(subState\.parks\) parksLayer\.addTo\(map\);")

done = skipped = 0
for path in sorted(glob.glob(os.path.join(ROOT, '*.html')) + glob.glob(os.path.join(ROOT, '*/*.html'))):
    s = open(path, errors='surrogateescape').read()
    if 'function buildParks(d){' not in s: continue
    if 'function parkIconMarker' in s: skipped += 1; continue
    m = PAT.search(s)
    if not m or 'function escH' not in s and 'escH=' not in s and 'escH =' not in s:
        print('NOT PATCHED', os.path.relpath(path, ROOT)); continue
    tip = m.group('tip')
    if 'parkTooltipName' not in tip: tip = 'parkTooltipName(f.properties)'
    new = ("  var parkIcons = L.layerGroup(), parkIconNames = {};\n"
           "  var parkPolys = L.geoJSON({type:'FeatureCollection',features:pkFeatures},{\n"
           "    style:%s,\n"
           "    onEachFeature:(f,l)=>{ l.bindTooltip(%s,{sticky:true}); var pm = parkIconMarker(f, l, parkIconNames); if(pm) parkIcons.addLayer(pm); }\n"
           "  });\n"
           "  parksLayer = L.featureGroup([parkPolys, parkIcons]);\n"
           "  if(subState.parks) parksLayer.addTo(map);") % (m.group('style'), tip)
    s = s[:m.start()] + new + s[m.end():]
    pre = ('' if 'function parkTooltipName' in s else TOOLTIP) + JS
    s = s.replace('function buildParks(d){', pre + 'function buildParks(d){', 1)
    if '.resource-marker-parks' not in s:
        i = s.find('.resource-marker-icon.resource-marker-custom-school img')
        if i < 0: i = s.find('.resource-marker-icon img')
        if i >= 0:
            j = s.find('\n', i) + 1
            s = s[:j] + CSS + s[j:]
        else:
            s = s.replace('</style>', '<style>' + CSS + '</style></style>', 1).replace('</style></style>', '</style>', 1)
    open(path, 'w', errors='surrogateescape').write(s); done += 1
print('patched', done, 'already', skipped)
