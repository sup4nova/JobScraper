"""
Indeed scraper — Selenium + undetected-chromedriver
Dependencies:
    pip install undetected-chromedriver webdriver-manager selenium fake-useragent setuptools
"""
import time
import random
import asyncio
from urllib.parse import quote_plus

import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from scrapers._chrome import chrome_binary_location, chrome_version_main
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from fake_useragent import UserAgent

_SALARY_KEYWORDS = ["€", "k€", "eur", "salaire", "rémunération", "par an", "par mois"]
_EDU_KEYWORDS    = ["bac", "bts", "dut", "licence", "master", "ingénieur",
                    "doctorat", "cap", "bep", "niveau"]

_TAG_CONTAINERS = [
    ".jobMetaDataGroup",
    "[data-testid='jobsearch-JobMetadataHeader']",
    ".metadata",
    ".job-snippet",
]
_TAG_SELECTORS = [
    "[data-testid='attribute_snippet_testid']",
    ".attribute_snippet",
    "div.metadata span",
]


class IndeedScraper:
    source_name = "indeed"
    BASE = "https://fr.indeed.com"

    def __init__(self, query: str, city: str, limit: int = 20):
        self.query = query
        self.city  = city
        self.limit = limit

    # ── Driver ───────────────────────────────────────────────────────────────

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

        driver = uc.Chrome(
            options=options,
            version_main=chrome_version_main(),
        )
        return driver

    # ── Entry points ─────────────────────────────────────────────────────────

    def scrape(self) -> list[dict]:
        """Synchronous version — used by the CLI and the FastAPI executor."""
        driver = self._make_driver()
        try:
            return self._search(driver)
        finally:
            driver.quit()

    async def scrape_async(self) -> list[dict]:
        """Delegates to scrape() — the executor in main.py handles the thread."""
        return self.scrape()

    # ── Search + pagination ──────────────────────────────────────────────────

    def _search(self, driver) -> list[dict]:
        query_enc = quote_plus(self.query)
        city_enc  = quote_plus(self.city)
        driver.get(f"{self.BASE}/jobs?q={query_enc}&l={city_enc}")
        print(f"🌐 Page loaded: {driver.current_url}")
        time.sleep(random.uniform(2, 4))

        # Cookie banner
        try:
            btn = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            btn.click()
            time.sleep(1)
            print("🍪 Cookies accepted")
        except TimeoutException:
            pass

        jobs      = []
        seen_urls = set()

        while len(jobs) < self.limit:
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "#mosaic-provider-jobcards")
                    )
                )
            except TimeoutException:
                print("⚠️  Container not found")
                break

            container    = driver.find_element(By.CSS_SELECTOR, "#mosaic-provider-jobcards")
            job_elements = container.find_elements(
                By.CSS_SELECTOR, "[data-testid='slider_item']"
            )
            if not job_elements:
                job_elements = container.find_elements(By.CSS_SELECTOR, "li.css-5lfssm")
            if not job_elements:
                print("⚠️  No cards found — selectors may be stale")
                break

            print(f"📋 {len(job_elements)} cards found on this page")

            for job_el in job_elements:
                if len(jobs) >= self.limit:
                    break
                job = self._parse_element(job_el)
                if job and job["url"] not in seen_urls:
                    seen_urls.add(job["url"])
                    jobs.append(job)

            # Next page
            try:
                next_btn = driver.find_element(
                    By.CSS_SELECTOR, "a[data-testid='pagination-page-next']"
                )
                driver.execute_script("""
                    document.getElementById('onetrust-banner-sdk')?.remove();
                    document.querySelector('.ot-sdk-row')?.remove();
                    document.querySelector('#onetrust-consent-sdk')?.remove();
                """)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(random.uniform(2, 3))
            except NoSuchElementException:
                break

        print(f"✅ {len(jobs)} jobs collected")
        print(jobs[0] if jobs else "No job to display")
        return jobs

    # ── Parsing a card ───────────────────────────────────────────────────────

    def _parse_element(self, job_el) -> dict | None:
        title_el = None
        for sel in ["h2.jobTitle", "h2[data-testid='jobTitle']", "h2", ".jobTitle"]:
            try:
                title_el = job_el.find_element(By.CSS_SELECTOR, sel)
                break
            except NoSuchElementException:
                continue

        if not title_el:
            print("    ❌ No title selector matched")
            return None

        # 2. Read the title, skip empty cards (placeholders / ads)
        title = title_el.text.strip()
        if not title:
            return None

        # 3. Extract the jk (prefer data-jk, present even on sponsored cards)
        jk = job_el.get_attribute("data-jk")
        if not jk:
            try:
                jk = job_el.find_element(By.CSS_SELECTOR, "[data-jk]").get_attribute("data-jk")
            except NoSuchElementException:
                jk = None

        # 4. Clean URL if we have the jk, else fall back to the card's href
        url = None
        if jk:
            url = f"https://fr.indeed.com/viewjob?jk={jk}"
        else:
            try:
                url = title_el.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            except NoSuchElementException:
                try:
                    url = job_el.find_element(By.CSS_SELECTOR, "a.jcs-JobTitle").get_attribute("href")
                except NoSuchElementException:
                    pass

        if not url:
            print(f"    ❌ URL not found for: {title}")
            return None

        company = self._safe_text(job_el, "[data-testid='company-name']")
        city    = self._safe_text(job_el, "[data-testid='text-location']")

        salary, education, contract_parts = self._parse_tags(job_el)

        try:
            job_el.find_element(By.CSS_SELECTOR, "[data-testid='indeedApply']")
            easily_apply = True
        except NoSuchElementException:
            easily_apply = False

        description = []
        try:
            desc_container = job_el.find_element(By.CSS_SELECTOR, "[role='presentation']")
            desc_els       = desc_container.find_elements(By.CSS_SELECTOR, "ul li")
            description    = [el.text for el in desc_els if el.text]
        except NoSuchElementException:
            pass

        print(f"    Indeed — {title} @ {company} ({city})")

        return {
            "source":        "indeed",
            "title":         title,
            "url":           url,
            "company":       company,
            "city":          city,
            "salary":        salary,
            "education":     education,
            "contract_type": "; ".join(contract_parts),
            "easily_apply":  easily_apply,
            "description":   "\n".join(description),
        }

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _safe_text(self, parent, selector: str) -> str:
        try:
            return parent.find_element(By.CSS_SELECTOR, selector).text
        except NoSuchElementException:
            return ""

    def _parse_tags(self, job_el) -> tuple[str, str, list[str]]:
        salary         = ""
        education      = ""
        contract_parts = []

        tag_els = []
        for container_sel in _TAG_CONTAINERS:
            try:
                container = job_el.find_element(By.CSS_SELECTOR, container_sel)
                for tag_sel in _TAG_SELECTORS:
                    tag_els = container.find_elements(By.CSS_SELECTOR, tag_sel)
                    if tag_els:
                        break
                if tag_els:
                    break
            except NoSuchElementException:
                continue

        raw_tags = [t.text.strip() for t in tag_els if t.text.strip()]

        for tag in raw_tags:
            tag_lower = tag.lower()
            if any(kw in tag_lower for kw in _SALARY_KEYWORDS):
                salary = tag
            elif any(kw in tag_lower for kw in _EDU_KEYWORDS):
                education = tag
            else:
                contract_parts.append(tag)

        return salary, education, contract_parts
    
if __name__ == "__main__":
    print("🔍 Starting scraper...")
    scraper = IndeedScraper(query="developpeur python", city="Paris", limit=5)
    jobs = scraper.scrape()
    print(f"\n📦 {len(jobs)} jobs found:")
    for job in jobs:
        print(f"  - {job['title']} @ {job['company']} ({job['city']})")
        print(f"    🔗 {job['url']}")