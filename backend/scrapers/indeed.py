"""
Indeed scraper - undetected-chromedriver
"""
import time
import random
import asyncio
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus

import undetected_chromedriver as uc
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

    # ── Browser setup ────────────────────────────────────────────────────────

    def _make_driver(self):
        options = uc.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"user-agent={UserAgent().random}")
        binary = chrome_binary_location()
        if binary:
            options.binary_location = binary

        driver = uc.Chrome(
            options=options,
            version_main=chrome_version_main(),
        )
        return driver

    # ── Entry points ──────────────────────────────────────────────────────────

    def scrape(self) -> list[dict]:
        """Synchronous version, used by the CLI."""
        driver = self._make_driver()
        try:
            return self._search(driver)
        finally:
            driver.quit()

    async def scrape_async(self) -> list[dict]:
        """Async wrapper, called by FastAPI."""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, self.scrape)

    # ── Search + pagination ───────────────────────────────────────────────────

    def _search(self, driver) -> list[dict]:
        query_enc = quote_plus(self.query)
        city_enc  = quote_plus(self.city)
        driver.get(f"{self.BASE}/jobs?q={query_enc}&l={city_enc}")
        time.sleep(random.uniform(2, 4))

        # dismiss cookie banner
        try:
            btn = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            btn.click()
            time.sleep(1)
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
                print(f"    ⚠️  job list never appeared — url={driver.current_url!r} title={driver.title!r}")
                break

            container    = driver.find_element(By.CSS_SELECTOR, "#mosaic-provider-jobcards")
            job_elements = container.find_elements(
                By.CSS_SELECTOR, "[data-testid='slider_item']"
            )

            if not job_elements:
                job_elements = container.find_elements(By.CSS_SELECTOR, "li.css-5lfssm")
            if not job_elements:
                print("    ⚠️  no job cards found - selectors may be outdated")
                break

            for job_el in job_elements:
                if len(jobs) >= self.limit:
                    break
                job = self._parse_element(job_el)
                if job and job["url"] not in seen_urls:
                    seen_urls.add(job["url"])
                    jobs.append(job)

            # next page
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

        return jobs

    # ── Card parsing ─────────────────────────────────────────────────────────

    def _parse_element(self, job_el) -> dict | None:
        try:
            title_el = job_el.find_element(By.CSS_SELECTOR, "h2.jobTitle")
            title    = title_el.text
            url      = title_el.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
        except NoSuchElementException:
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

        print(f"    Indeed - {title} @ {company} ({city})")

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