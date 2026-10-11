"""Supermarkets, delis and bodegas, pharmacies, breweries and smoke, vape and cannabis shops, split out of the directory's food stores (used by biz_profiles.py and bid_profiles.py)."""
import re
SUPERMARKET = re.compile(r"\bc[- ]?town\b|^save a lot$|^amazon fresh|\bkey food\b|^(smith )?union market\b|^food bazaar$|whole foods|trader jo|park slope food coop|\bfoodtown\b|"
                         r"associated supermarket|royal supermarket|^lidl$|^met (fresh|foods?)\b|fairway|brooklyn fare", re.I)
SMOKE = re.compile(r"vape|smoke shop|cannabis|dispensar|\bcbd\b|tobacco|hookah", re.I)
SMOKE_KINDS = {'Tobacco', 'Cannabis', 'E-cigarette'}

DELI = re.compile(r"\bdeli\b|\bdli\b|bodega|grocery|groceries|grcy|convenience|mini ?mart|mini ?market|quick stop|food mart|candy store|\bnews\b|7.?eleven|\bmobil\b|^shell$", re.I)
PHARMACY = re.compile(r"\bcvs\b|duane reade|walgreens|rite aid", re.I)
DRINKS = re.compile(r"brewing|brewery|distiller|winery|stillhouse", re.I)
FOODCATS = {'Food stores', 'Groceries and food shops', 'Food stores with beer or liquor license', 'Grocery beer license'}

def special(name, cat, kind):
    """(heading, label) for a supermarket or a smoke, vape or cannabis shop; None for anything else."""
    if kind in SMOKE_KINDS or SMOKE.search(name):
        return 'Smoke, vape and cannabis shops', {'Cannabis': 'Cannabis dispensary', 'E-cigarette': 'Vape shop'}.get(kind, 'Vape shop' if 'vape' in name.lower() else 'Smoke shop')
    if (SUPERMARKET.search(name.strip()) and '@' not in name) or kind == 'Supermarket':
        return 'Supermarkets', 'Supermarket'
    if cat in FOODCATS and PHARMACY.search(name):
        return 'Health and medical', 'Pharmacy'
    if cat in FOODCATS and DRINKS.search(name):
        return 'Restaurants, cafes and food', 'Brewery, distillery or winery'
    if cat in FOODCATS and (DELI.search(name) or (kind == 'Convenience' and 'bagel' not in name.lower())):
        return 'Delis and bodegas', 'Convenience store' if re.search(r"convenience|mini|7.?eleven|mobil|shell|news", name, re.I) or kind == 'Convenience' else 'Deli or bodega'
    return None
