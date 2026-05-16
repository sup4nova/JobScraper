import re
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from .base import BaseScraper


class LinkedInScraper(BaseScraper):
    source_name = "linkedin"
    BASE = "https://www.linkedin.com"

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
        # Public job search — no account needed
        url = (
            f"{self.BASE}/jobs/search/"
            f"?keywords={query_enc}&location={city_enc}&f_TPR=r2592000&position=1&pageNum=0"
        )

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await self._random_delay(2, 4)

        jobs = []
        seen_urls = set()
        offset = 0

        while len(jobs) < self.limit:
            # scroll to load more cards
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self._random_delay(1.5, 2.5)

            try:
                await page.wait_for_selector(
                    ".jobs-search__results-list li, .base-card, [class*='job-search-card']",
                    timeout=8000,
                )
            except Exception:
                break

            content = await page.content()
            soup = BeautifulSoup(content, "lxml")

            cards = soup.select(".jobs-search__results-list li, .base-card")
            if not cards:
                break

            for card in cards:
                if len(jobs) >= self.limit:
                    break
                job = self._parse_card(card)
                if job and job["url"] not in seen_urls:
                    seen_urls.add(job["url"])
                    jobs.append(self._normalize(job))

            # load more button
            load_more = await page.query_selector("button[aria-label*='more jobs'], .infinite-scroller__show-more-button")
            if load_more and len(jobs) < self.limit:
                await load_more.click()
                await self._random_delay(2, 3)
            else:
                break

        return jobs

    def _parse_card(self, card) -> dict | None:
        title_el = card.select_one(
            "h3.base-search-card__title, .job-search-card__title, h3[class*='title']"
        )
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            return None

        link_el = card.select_one("a.base-card__full-link, a[class*='job-card-list__title']")
        if not link_el:
            link_el = card.select_one("a[href*='/jobs/view/']")
        url = ""
        if link_el:
            href = link_el.get("href", "").split("?")[0]
            url = href if href.startswith("http") else self.BASE + href
        if not url:
            return None

        company_el = card.select_one(
            "h4.base-search-card__subtitle, .job-search-card__company-name, a[class*='company']"
        )
        company = company_el.get_text(strip=True) if company_el else ""

        city_el = card.select_one(
            ".job-search-card__location, [class*='location']"
        )
        city = city_el.get_text(strip=True) if city_el else ""

        contract_el = card.select_one("[class*='workplace-type'], [class*='contract']")
        contract = contract_el.get_text(strip=True) if contract_el else ""

        return {
            "title": title,
            "company": company,
            "city": city,
            "contract_type": contract,
            "url": url,
        }
