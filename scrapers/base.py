import asyncio
import random
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright, Page, Browser


DESKTOP_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


class BaseScraper(ABC):
    source_name: str = ""

    def __init__(self, query: str, city: str, limit: int = 20):
        self.query = query
        self.city = city
        self.limit = limit

    async def _make_browser(self, playwright):
        browser = await playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=random.choice(DESKTOP_UAS),
            viewport={"width": 1280, "height": 800},
            locale="fr-FR",
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        return browser, context

    async def _random_delay(self, min_s: float = 1.5, max_s: float = 3.5):
        await asyncio.sleep(random.uniform(min_s, max_s))

    @abstractmethod
    async def scrape(self) -> list[dict]:
        """Return list of job dicts matching the db schema."""
        ...

    def _normalize(self, job: dict) -> dict:
        defaults = {
            "source": self.source_name,
            "external_id": None,
            "title": "",
            "company": "",
            "city": "",
            "salary": "",
            "education": "",
            "contract_type": "",
            "description": "",
            "url": "",
        }
        return {**defaults, **job, "source": self.source_name}
