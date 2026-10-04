import re
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from .base import BaseScraper


class WTTJScraper(BaseScraper):
    source_name = "wttj"
    BASE = "https://www.welcometothejungle.com"

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
        url = f"{self.BASE}/fr/jobs?query={query_enc}&aroundQuery={city_enc}&page=1"

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await self._random_delay(2, 4)

        jobs = []
        page_num = 1

        while len(jobs) < self.limit:
            await page.wait_for_selector("[data-testid='job-card'], article, [class*='JobCard']", timeout=10000)
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")

            cards = (
                soup.select("[data-testid='job-card']")
                or soup.select("article[class*='sc-']")
                or soup.select("li[class*='ais-Hits']")
            )

            for card in cards:
                if len(jobs) >= self.limit:
                    break
                job = self._parse_card(card)
                if job:
                    jobs.append(self._normalize(job))

            # next page
            next_btn = await page.query_selector("a[data-testid='pagination-next'], [aria-label='Page suivante']")
            if not next_btn or len(jobs) >= self.limit:
                break
            page_num += 1
            await next_btn.click()
            await self._random_delay(2, 3)

        return jobs

    def _parse_card(self, card) -> dict | None:
        # title
        title_el = card.select_one("h3, h4, [class*='title'], [data-testid='job-title']")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            return None

        # link
        link_el = card.select_one("a[href]")
        url = ""
        if link_el:
            href = link_el.get("href", "")
            url = href if href.startswith("http") else self.BASE + href

        # company
        company_el = card.select_one("[class*='company'], [data-testid='company-name']")
        company = company_el.get_text(strip=True) if company_el else ""

        # location
        city_el = card.select_one("[class*='location'], [data-testid='job-location']")
        city = city_el.get_text(strip=True) if city_el else ""

        # contract type
        contract_el = card.select_one("[class*='contract'], [data-testid='contract-type']")
        contract = contract_el.get_text(strip=True) if contract_el else ""

        return {
            "title": title,
            "company": company,
            "city": city,
            "contract_type": contract,
            "url": url,
        }

    async def _get_description(self, page, url: str) -> dict:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await self._random_delay(1, 2)
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")

            desc_el = soup.select_one(
                "[data-testid='job-description'], [class*='description'], "
                "section[class*='sc-'] div[class*='sc-']"
            )
            description = desc_el.get_text(separator="\n", strip=True)[:2000] if desc_el else ""

            salary_el = soup.select_one("[data-testid='job-salary'], [class*='salary']")
            salary = salary_el.get_text(strip=True) if salary_el else ""

            edu_el = soup.select_one("[data-testid='job-education'], [class*='education']")
            education = edu_el.get_text(strip=True) if edu_el else ""

            return {"description": description, "salary": salary, "education": education}
        except Exception:
            return {}
