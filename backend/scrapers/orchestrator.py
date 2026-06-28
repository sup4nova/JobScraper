"""
Runs all scrapers and merges the results.
"""
import json
import os
from datetime import datetime
from models import Offre

from scrapers.indeed import scrape_indeed
from scrapers.linkedin import scrape_linkedin
from scrapers.wttj import scrape_wttj


SCRAPERS = {
    "indeed": scrape_indeed,
    "linkedin": scrape_linkedin,
    "wttj": scrape_wttj,
}


def run_scraping(poste: str, ville: str, limite: int, sites: list) -> list[Offre]:
    offres = []

    for site in sites:
        scraper = SCRAPERS.get(site)
        if not scraper:
            continue
        try:
            print(f"  → Scraping {site}...")
            resultats = scraper(poste=poste, ville=ville, limite=limite)
            print(f"     {len(resultats)} jobs found on {site}")
            offres.extend(resultats)
        except Exception as e:
            print(f"  ⚠️  Error on {site}: {e}")

    # Save raw results to JSON for later reuse
    _save(offres, poste, ville)

    return offres


def _save(offres: list[Offre], poste: str, ville: str):
    """Save offers to /data/ as JSON."""
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"data/offres_{poste.replace(' ', '_')}_{timestamp}.json"

    data = [vars(o) for o in offres]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n  Saved to {path}")
