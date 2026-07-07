"""
Welcome to the Jungle scraper — httpx (Algolia API) + Playwright (job pages)
"""
import random
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from fake_useragent import UserAgent


# ── Constants ─────────────────────────────────────────────────────────────────

ALGOLIA_URL = "https://csekhvms53-dsn.algolia.net/1/indexes/*/queries"
ALGOLIA_HEADERS = {
    "x-algolia-application-id": "CSEKHVMS53",
    "x-algolia-api-key":        "4bd8f6215d0cc52b26430765769e65a0",
    "content-type":             "application/json",
}

_SALARY_KEYWORDS = ["€", "k€", "eur", "salaire", "rémunération", "par an", "par mois"]
_EDU_KEYWORDS    = ["bac", "bts", "dut", "licence", "master", "ingénieur",
                    "doctorat", "cap", "bep", "niveau"]


class WTTJScraper:
    source_name = "wttj"

    def __init__(self, query: str, city: str, limit: int = 20):
        self.query = query
        self.city  = city
        self.limit = limit

    # ── Entry point ──────────────────────────────────────────────────────────

    async def scrape(self) -> list[dict]:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            ua = UserAgent()
            context = await browser.new_context(
                user_agent=ua.random,
                viewport={"width": 1920, "height": 1080},
                locale="fr-FR",
            )
            page = await context.new_page()

            try:
                job_urls = await self._get_job_urls_api()
                jobs     = await self._scrape_jobs(page, job_urls)
            finally:
                await browser.close()

        return jobs

    # ── Fetch job URLs via the Algolia API ───────────────────────────────────

    async def _get_job_urls_api(self) -> list[str]:
        payload = {
            "requests": [{
                "indexName": "wttj_jobs_production_fr",
                "params":    f"query={quote_plus(self.query)}&aroundQuery={quote_plus(self.city)}&hitsPerPage={self.limit}",
            }]
        }

        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(ALGOLIA_URL, headers=ALGOLIA_HEADERS, json=payload, timeout=10)
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            print(f"    WTTJ — Algolia API error: {e}")
            return []

        hits = data.get("results", [{}])[0].get("hits", [])
        print(f"    WTTJ — {len(hits)} jobs found via Algolia")

        urls = []
        for h in hits:
            org_slug = h.get("organization", {}).get("slug", "")
            job_slug = h.get("slug", "")
            if org_slug and job_slug:
                urls.append(
                    f"https://www.welcometothejungle.com/fr/companies/{org_slug}/jobs/{job_slug}"
                )

        return urls

    # ── Scraping each job ────────────────────────────────────────────────────

    async def _scrape_jobs(self, page, job_urls: list[str]) -> list[dict]:
        jobs = []
        for url in job_urls:
            job = await self._scrape_one(page, url)
            if job:
                jobs.append(job)
            await page.wait_for_timeout(random.randint(1500, 3000))
        return jobs

    async def _scrape_one(self, page, job_url: str) -> dict | None:
        try:
            await page.goto(job_url, timeout=15_000, wait_until="domcontentloaded")
            await page.wait_for_timeout(random.randint(1000, 2000))
        except PlaywrightTimeout:
            print(f"    WTTJ — timeout on {job_url[:60]}...")
            return None

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Title
        title_el = soup.select_one("h1")
        if not title_el:
            return None
        title = title_el.get_text(strip=True)

        # Company
        company_el = soup.select_one("[data-testid='organization-title']")
        if not company_el:
            company_el = soup.select_one("a[href*='/fr/companies/'] span")
        company = company_el.get_text(strip=True) if company_el else ""

        # City
        city_el = soup.select_one("[data-testid='job-location']")
        if not city_el:
            city_el = soup.select_one("[name='map-pin'] ~ span")
        city = city_el.get_text(strip=True) if city_el else ""

        # Salary
        salary = ""
        salary_el = soup.select_one("[data-testid='job-salary']")
        if not salary_el:
            for tag in soup.select("[data-testid='job-tag']"):
                text = tag.get_text(strip=True)
                if any(kw in text.lower() for kw in _SALARY_KEYWORDS):
                    salary = text
                    break
        else:
            salary = salary_el.get_text(strip=True)

        # Contract type
        contract_type = ""
        contract_el = soup.select_one("[data-testid='contract-type']")
        if not contract_el:
            contract_el = soup.select_one("[data-testid='job-contract']")
        if contract_el:
            contract_type = contract_el.get_text(strip=True)

        # Education level
        education = ""
        for tag in soup.select("[data-testid='job-tag'], [data-testid='job-education']"):
            text = tag.get_text(strip=True)
            if any(kw in text.lower() for kw in _EDU_KEYWORDS):
                education = text
                break

        # Remote work
        remote = ""
        remote_el = soup.select_one("[data-testid='job-remote']")
        if remote_el:
            remote = remote_el.get_text(strip=True)

        # Description
        desc_el = soup.select_one("[data-testid='job-description']")
        if not desc_el:
            desc_el = soup.select_one(".job-description")
        description = desc_el.get_text(strip=True)[:1000] if desc_el else ""

        return {
            "source":        "wttj",
            "title":         title,
            "url":           job_url,
            "company":       company,
            "city":          f"{city} {remote}".strip(),
            "salary":        salary,
            "education":     education,
            "contract_type": contract_type,
            "easily_apply":  True,
            "description":   description,
        }