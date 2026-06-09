"""
Scraper LinkedIn — endpoint guest seeMoreJobPostings (HTTP, pas de navigateur)
Dépendances : beautifulsoup4 (déjà installé)
"""
import time
import random
import urllib.request
import urllib.error
from urllib.parse import urlencode

from bs4 import BeautifulSoup

GUEST_API = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "text/html",
}


class LinkedInScraper:
    source_name = "linkedin"

    def __init__(self, query: str, city: str = "", limit: int = 20):
        self.query = query
        self.city  = city
        self.limit = limit

    def scrape(self) -> list[dict]:
        jobs = []
        seen = set()
        start = 0

        # L'endpoint pagine par tranches de 25 via le paramètre start
        while len(jobs) < self.limit and start < 200:
            cards = self._fetch_page(start)
            if not cards:
                break  # plus de résultats, ou LinkedIn a coupé

            for card in cards:
                if len(jobs) >= self.limit:
                    break
                job = self._parse_card(card)
                if job and job["url"] not in seen:
                    seen.add(job["url"])
                    jobs.append(job)
                    print(f"    LinkedIn — {job['title']} @ {job['company']}")

            start += 25
            time.sleep(random.uniform(1.5, 3))  # respire pour éviter le 999

        print(f"✅ {len(jobs)} offres récupérées (LinkedIn)")
        return jobs

    async def scrape_async(self) -> list[dict]:
        return self.scrape()

    # ── HTTP ────────────────────────────────────────────────────────────────

    def _fetch_page(self, start: int):
        params = {
            "keywords": self.query,
            "location": self.city or "France",
            "start": start,
        }
        url = f"{GUEST_API}?{urlencode(params)}"
        req = urllib.request.Request(url, headers=_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                soup = BeautifulSoup(resp.read(), "html.parser")
        except urllib.error.HTTPError as e:
            # 999 = anti-bot LinkedIn ; 400 = fin de pagination
            print(f"⚠️  LinkedIn HTTP {e.code} à start={start}")
            return []
        except Exception as e:
            print(f"❌ LinkedIn erreur : {type(e).__name__}: {e}")
            return []

        return soup.select("li") or soup.select("div.base-card")

    # ── Parsing ───────────────────────────────────────────────────────────────

    def _parse_card(self, card) -> dict | None:
        title_el = card.select_one("h3.base-search-card__title")
        link_el  = card.select_one("a.base-card__full-link") or card.select_one("a[href*='/jobs/view/']")
        if not title_el or not link_el:
            return None

        title = title_el.get_text(strip=True)
        url   = link_el.get("href", "").split("?")[0]
        if not title or not url:
            return None

        company_el = card.select_one("h4.base-search-card__subtitle")
        company    = company_el.get_text(strip=True) if company_el else ""

        loc_el = card.select_one(".job-search-card__location")
        city   = loc_el.get_text(strip=True) if loc_el else ""

        return {
            "source":        "linkedin",
            "title":         title,
            "url":           url,
            "company":       company,
            "city":          city,
            "salary":        "",
            "education":     "",
            "contract_type": "",   # pas de date ici (ne pas confondre avec le contrat)
            "easily_apply":  False,
            "description":   "",
        }


if __name__ == "__main__":
    print("🔍 Scraper LinkedIn (guest)")
    scraper = LinkedInScraper(query="devops", city="France", limit=10)
    jobs = scraper.scrape()
    print(f"\n📦 {len(jobs)} offres :")
    for job in jobs:
        print(f"  - {job['title']} @ {job['company']} ({job['city']})")
        print(f"    🔗 {job['url']}")