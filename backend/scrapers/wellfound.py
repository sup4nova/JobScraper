"""
Wellfound scraper — undetected-chromedriver (bypasses Cloudflare) + JSON __NEXT_DATA__
"""
import time
import json
import html
import random
import tempfile
import os
from urllib.parse import quote

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapers._chrome import chrome_binary_location, chrome_version_main
from selenium.common.exceptions import TimeoutException
from fake_useragent import UserAgent

BASE = "https://wellfound.com"


class WellfoundScraper:
    source_name = "wellfound"

    @staticmethod
    def _extract_locations(raw) -> list[str]:
        """locationNames can be a list, a dict with a 'json' key, or None."""
        if isinstance(raw, list):
            return [str(x) for x in raw if x]
        if isinstance(raw, dict):
            return [str(x) for x in raw.get("json", []) if x]
        return []

    def __init__(self, query: str, city: str = "", limit: int = 20):
        self.query = query
        self.city  = city
        self.limit = limit

    def _make_driver(self):
        options = uc.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={UserAgent().random}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        binary = chrome_binary_location()
        if binary:
            options.binary_location = binary

        # Temp profile outside OneDrive to avoid sync lock conflicts
        profile_dir = os.path.join(tempfile.gettempdir(), "uc_wellfound")
        options.add_argument(f"--user-data-dir={profile_dir}")

        return uc.Chrome(options=options, version_main=chrome_version_main())

    def _build_url(self) -> str:
        role = quote(self.query.strip().lower().replace(" ", "-"))
        if self.city:
            loc = quote(self.city.strip().lower().replace(" ", "-"))
            return f"{BASE}/role/l/{role}/{loc}"
        return f"{BASE}/role/{role}"

    def scrape(self) -> list[dict]:
        driver = self._make_driver()
        try:
            url = self._build_url()
            print(f"Wellfound: {url}")
            driver.get(url)
            time.sleep(random.uniform(3, 6))  # wait for Cloudflare challenge and JS to resolve

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "script#__NEXT_DATA__"))
                )
            except TimeoutException:
                print("⛔ __NEXT_DATA__ not found — likely blocked by Cloudflare")
                return []

            raw = driver.find_element(
                By.CSS_SELECTOR, "script#__NEXT_DATA__"
            ).get_attribute("textContent")

            return self._parse(raw)
        finally:
            driver.quit()

    async def scrape_async(self) -> list[dict]:
        return self.scrape()

    def _parse(self, raw: str) -> list[dict]:
        try:
            data = json.loads(raw)
            graph = data["props"]["pageProps"]["apolloState"]["data"]
        except (KeyError, json.JSONDecodeError, TypeError):
            print("⚠️  could not parse __NEXT_DATA__ JSON")
            return []

        jobs = []
        for key, node in graph.items():
            if not key.startswith("JobListingSearchResult"):
                continue
            slug = node.get("slug") or ""
            jid  = node.get("id") or key.split(":")[-1]
            locs = self._extract_locations(node.get("locationNames"))
            comp = node.get("compensation")
            if isinstance(comp, dict):
                comp = comp.get("text") or comp.get("json") or ""
            salary = comp if isinstance(comp, str) else ""
            jobs.append({
                "source":        "wellfound",
                "title":         html.unescape(node.get("title") or ""),
                "url":           f"{BASE}/jobs/{jid}-{slug}",
                "company":       "",
                "city":          ", ".join(locs) or "Remote",
                "salary":        salary,
                "education":     "",
                "contract_type": "Remote" if node.get("remote") else (node.get("jobType") or ""),
                "easily_apply":  False,
                "description":   "",
            })
            if len(jobs) >= self.limit:
                break

        print(f"Wellfound — {len(jobs)} jobs found")
        return jobs


if __name__ == "__main__":
    scraper = WellfoundScraper(query="devops", city="france", limit=10)
    jobs = scraper.scrape()
    print(f"\n{len(jobs)} jobs:")
    for job in jobs:
        print(f"  - {job['title']} ({job['city']})  💰 {job['salary'] or 'n/a'}")
        print(f"    🔗 {job['url']}")
