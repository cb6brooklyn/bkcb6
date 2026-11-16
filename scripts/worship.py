"""Houses of worship: which Directory profiles are one (churches, synagogues, mosques, temples, meeting houses).
is_worship(p) -> bool. Used by cb6_worship_profiles.py and app_directory_tiles.py."""
import re
RX = re.compile(r"\bchurch\b|\bchapel\b|\btemple\b|congregation|\bcong\b|synagogue|\bshul\b|mosque|masjid|iglesia|\bparish\b|cathedral|ministr|tabernacle|chabad|"
                r"\bbaptist|methodist|lutheran|presbyterian church|episcopal|pentecostal|roman catholic|catholic church|kingdom hall|meeting house|friends meeting|"
                r"buddhist|vedanta|gurdwara|hindu temple|islamic center|assembly of god|asamblea de dios|seventh.day adventist|jewish center|unitarian|kolot chayeinu|"
                r"\bfellowship\b|ethical culture|\bsangha\b|zen center", re.I)
NOT = re.compile(r"hospital|newyork-presbyterian|new york presbyterian|medical|infusion|compost|drop-off|daycare|day care|academy|\bschool\b|pre-?k|senior|historic district|"
                 r"publishing|charities|ecc$|poll site|administration building|robotic|truth society|citizens bank", re.I)
GROUPS = ('Local businesses', 'Schools, parks and facilities', 'Community groups')
def is_worship(p):
    if p.get('group') not in GROUPS or p.get('topic') in ('Historic places', 'Food pantries', 'Compost and textile drop-off sites', 'Poll sites', 'Hospitals and health care', 'Schools', 'Child care and pre-K'): return False
    if NOT.search(p.get('name') or ''): return False
    if any((k[0] == 'Nonprofit' and 'a church' in k[1]) or (k[0] == 'Kind' and k[1] == 'Place of worship') for k in p.get('kv', [])): return True
    if (p.get('topic') or '') in ('Religious Organizations', 'Faith organizations', 'Houses of worship'): return True
    return bool(RX.search(p.get('name') or ''))
