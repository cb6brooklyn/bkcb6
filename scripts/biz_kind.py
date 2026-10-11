"""Supermarkets and smoke, vape and cannabis shops, split out of the directory's food stores (used by biz_profiles.py and bid_profiles.py)."""
import re
SUPERMARKET = re.compile(r"\bc-?town\b|\bkey food\b|^(smith )?union market\b|^food bazaar$|whole foods|trader jo|park slope food coop|\bfoodtown\b|"
                         r"associated supermarket|royal supermarket|^lidl$|^met (fresh|foods?)\b|fairway|brooklyn fare", re.I)
SMOKE = re.compile(r"vape|smoke shop|cannabis|dispensar|\bcbd\b|tobacco|hookah", re.I)
SMOKE_KINDS = {'Tobacco', 'Cannabis', 'E-cigarette'}

def special(name, cat, kind):
    """(heading, label) for a supermarket or a smoke, vape or cannabis shop; None for anything else."""
    if kind in SMOKE_KINDS or SMOKE.search(name):
        return 'Smoke, vape and cannabis shops', {'Cannabis': 'Cannabis dispensary', 'E-cigarette': 'Vape shop'}.get(kind, 'Vape shop' if 'vape' in name.lower() else 'Smoke shop')
    if (SUPERMARKET.search(name.strip()) and '@' not in name) or kind == 'Supermarket':
        return 'Supermarkets', 'Supermarket'
    return None
