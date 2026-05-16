import re
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from .base import BaseScraper


class IndeedScraper(BaseScraper):
    source_name = "indeed"
    BASE = "https://fr.indeed.com"

    async def scrape(self) -> list[dict]:
        jobs = []
        async with async_playwright() as pw:
            browser, context = await self._make_browser(pw)
            page = await context.new_page()
            try:
                jobs = await self._search(page)
            finally:
                await browser.close()
        return jobs

    async def _search(self, page) -> list[dict]:
        query_enc = quote_plus(self.query)
        city_enc = quote_plus(self.city)
        url = f"{self.BASE}/jobs?q={query_enc}&l={city_enc}&lang=fr"

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await self._random_delay(2, 4)

        # dismiss cookie banner if present
        try:
            btn = await page.wait_for_selector("button#onetrust-accept-btn-handler", timeout=4000)
            await btn.click()
            await self._random_delay(0.5, 1)
        except Exception:
            pass

        jobs = []
        seen_urls = set()

        while len(jobs) < self.limit:
            try:
                await page.wait_for_selector(".job_seen_beacon, .tapItem, [data-jk]", timeout=10000)
            except Exception:
                break

            content = await page.content()
            soup = BeautifulSoup(content, "lxml")

            cards = soup.select(".job_seen_beacon, .tapItem")
            if not cards:
                cards = soup.select("[data-jk]")

            for card in cards:
                if len(jobs) >= self.limit:
                    break
                job = self._parse_card(card)
                if job and job["url"] not in seen_urls:
                    seen_urls.add(job["url"])
                    jobs.append(self._normalize(job))

            # next page
            next_btn = await page.query_selector("a[data-testid='pagination-page-next'], a[aria-label='Suivante']")
            if not next_btn or len(jobs) >= self.limit:
                break
            await next_btn.click()
            await self._random_delay(2, 4)

        return jobs

    def _parse_card(self, card) -> dict | None:
        title_el = card.select_one(".jobTitle span, h2.jobTitle, [class*='title']")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title or title.lower() == "new":
            return None

        jk = card.get("data-jk") or ""
        link_el = card.select_one("a[href][id*='job_'], a.jcs-JobTitle")
        if link_el:
            href = link_el.get("href", "")
            url = href if href.startswith("http") else self.BASE + href
        elif jk:
            url = f"{self.BASE}/viewjob?jk={jk}"
        else:
            return None

        company_el = card.select_one("[data-testid='company-name'], .companyName")
        company = company_el.get_text(strip=True) if company_el else ""

        city_el = card.select_one("[data-testid='job-location'], .companyLocation")
        city = city_el.get_text(strip=True) if city_el else ""

        salary_el = card.select_one(".salary-snippet-container, [class*='salary']")
        salary = salary_el.get_text(strip=True) if salary_el else ""

        desc_el = card.select_one(".job-snippet, [class*='snippet']")
        description = desc_el.get_text(separator=" ", strip=True) if desc_el else ""

        return {
            "external_id": jk,
            "title": title,
            "company": company,
            "city": city,
            "salary": salary,
            "description": description,
            "url": url,
        }
