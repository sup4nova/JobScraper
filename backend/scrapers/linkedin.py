"""
Scraper LinkedIn — undetected-chromedriver + Selenium
Même stack qu'Indeed pour éviter les conflits asyncio/Playwright sur Windows.
"""
import time
import random
import asyncio
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus

import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


BASE_SEARCH = "https://www.linkedin.com/jobs/search"

_SALARY_KEYWORDS = ["€", "k€", "eur", "salaire", "rémunération", "par an", "par mois", "$"]
_EDU_KEYWORDS    = ["bac", "bts", "dut", "licence", "master", "ingénieur",
                    "doctorat", "cap", "bep", "niveau"]


class LinkedInScraper:
    source_name = "linkedin"

    def __init__(self, query: str, city: str, limit: int = 20):
        self.query = query
        self.city  = city
        self.limit = limit

    # ── Driver ────────────────────────────────────────────────────────────────

    def _make_driver(self):
        options = uc.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=0")  # ← port aléatoire pour éviter le conflit
        options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        options.add_argument(f"user-agent={UserAgent().random}")

        driver = uc.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
            version_main=None,
        )
        return driver
    # ── Points d'entrée ───────────────────────────────────────────────────────

    def scrape(self) -> list[dict]:
        """Version synchrone — utilisée par le CLI."""
        driver = self._make_driver()
        try:
            return self._search(driver)
        finally:
            driver.quit()

    async def scrape_async(self) -> list[dict]:
        """Version async — appelée par FastAPI."""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, self.scrape)

    # ── Recherche ─────────────────────────────────────────────────────────────

    def _search(self, driver) -> list[dict]:
        url = (
            f"{BASE_SEARCH}"
            f"?keywords={quote_plus(self.query)}"
            f"&location={quote_plus(self.city)}"
        )
        driver.get(url)
        time.sleep(random.uniform(2, 4))

        # Scroll pour déclencher le lazy loading
        for _ in range(4):
            driver.execute_script("window.scrollBy(0, window.innerHeight * 0.8)")
            time.sleep(random.uniform(0.7, 1.2))

        soup = BeautifulSoup(driver.page_source, "html.parser")

        cards = (
            soup.select("ul.jobs-search__results-list li")
            or soup.select("div.base-card")
            or soup.select("li.result-card")
        )

        print(f"    [debug] LinkedIn — {len(cards)} cartes trouvées")

        jobs      = []
        seen_urls = set()

        for card in cards:
            if len(jobs) >= self.limit:
                break
            job = self._parse_card(card)
            if job and job["url"] not in seen_urls:
                seen_urls.add(job["url"])
                jobs.append(job)
                print(f"    LinkedIn — {job['title']} @ {job['company']}")

        return jobs

    # ── Parsing d'une carte ───────────────────────────────────────────────────

    def _parse_card(self, card) -> dict | None:
        title_el = (
            card.select_one("h3.base-search-card__title")
            or card.select_one("h3")
        )
        link_el = (
            card.select_one("a.base-card__full-link")
            or card.select_one("a[href*='/jobs/view/']")
        )
        if not title_el or not link_el:
            return None

        title = title_el.get_text(strip=True)
        url   = link_el.get("href", "").split("?")[0]
        if not url:
            return None

        company_el = (
            card.select_one("h4.base-search-card__subtitle")
            or card.select_one("a.hidden-nested-link")
        )
        company = company_el.get_text(strip=True) if company_el else ""

        location_el = card.select_one(".job-search-card__location")
        city = location_el.get_text(strip=True) if location_el else ""

        meta_el = card.select_one(".job-search-card__listdate")
        contract_type = meta_el.get_text(strip=True) if meta_el else ""

        salary    = ""
        education = ""
        for tag_el in card.select(".job-search-card__benefits span"):
            tag = tag_el.get_text(strip=True)
            tag_lower = tag.lower()
            if any(kw in tag_lower for kw in _SALARY_KEYWORDS):
                salary = tag
            elif any(kw in tag_lower for kw in _EDU_KEYWORDS):
                education = tag

        easily_apply = bool(card.select_one(".job-search-card__easy-apply-label"))

        return {
            "source":        "linkedin",
            "title":         title,
            "url":           url,
            "company":       company,
            "city":          city,
            "salary":        salary,
            "education":     education,
            "contract_type": contract_type,
            "easily_apply":  easily_apply,
            "description":   "",
        }