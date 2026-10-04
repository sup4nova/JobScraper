"""
Wellfound scraper — undetected-chromedriver (bypasses Cloudflare) + JSON __NEXT_DATA__
"""
import time
import json
import html
import random
from urllib.parse import quote

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapers._chrome import (
    chrome_binary_location,
    chrome_version_main,
    chrome_profile_dir,
    looks_like_cloudflare_challenge,
)
from selenium.common.exceptions import TimeoutException

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
        # No manual user-agent override: uc already keeps the UA consistent
        # with the actual patched Chrome binary. A random UA here would say
        # e.g. "Chrome 131" while the JS engine/TLS fingerprint says "121" —
        # exactly the kind of mismatch Cloudflare's bot check looks for.
        options.add_argument("--disable-blink-features=AutomationControlled")
        binary = chrome_binary_location()
        if binary:
            options.binary_location = binary

        # Persistent profile: keeps the `cf_clearance` cookie (and other
        # session state) across scrape cycles so we don't re-trigger
        # Cloudflare's JS challenge on every single run.
        profile_dir = chrome_profile_dir("wellfound")
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
            # Warm-up: land on the homepage first like a real visitor, rather
            # than jumping straight to a deep search URL — gives Cloudflare a
            # normal-looking navigation history before the page that matters.
            print("Wellfound: warm-up visit to homepage")
            driver.get(BASE)
            time.sleep(random.uniform(2, 4))

            url = self._build_url()
            for attempt in range(1, 3):
                print(f"Wellfound: {url} (attempt {attempt}/2)")
                driver.get(url)
                time.sleep(random.uniform(3, 6))  # let the Cloudflare/JS challenge resolve

                try:
                    WebDriverWait(driver, 35).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "script#__NEXT_DATA__"))
                    )
                    raw = driver.find_element(
                        By.CSS_SELECTOR, "script#__NEXT_DATA__"
                    ).get_attribute("textContent")
                    return self._parse(raw)
                except TimeoutException:
                    if looks_like_cloudflare_challenge(driver.page_source):
                        print(f"⛔ still on Cloudflare challenge after {attempt} attempt(s)")
                    else:
                        print("⚠️  __NEXT_DATA__ not found and no Cloudflare markers — "
                              "page markup may have changed")
                        break  # not a Cloudflare issue, retrying won't help
                    time.sleep(random.uniform(4, 8))

            return []
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
