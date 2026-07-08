# JobScraper

Scrapes job listings from Indeed, LinkedIn, Wellfound, and Remote OK, then surfaces them through a Vue.js dashboard. A Discord bot can post new listings directly to a channel as interactive cards.

---

## Features

| Feature | Status |
|---|---|
| Scraping — Indeed, LinkedIn, Wellfound, Remote OK | ✅ Working |
| Vue.js job dashboard (search, filter, like) | ✅ Working |
| FastAPI REST backend | ✅ Working |
| Docker deployment (backend + frontend) | ✅ Working |
| Discord bot — job cards with Apply / Hide buttons | ✅ Needs a `.env` (not committed) |

An AI chat assistant and a CV generator exist as local, unpublished experiments — see [Roadmap](#roadmap).

---

## Architecture

```
JobScrapper/
├── docker-compose.yml
├── LICENSE
├── .github/workflows/ci.yml   ← syntax check, pytest, frontend build, docker build
├── backend/
│   ├── main.py                ← FastAPI app + CLI entry point (run directly: python main.py)
│   ├── bot.py                 ← Discord bot
│   ├── requirements.txt
│   ├── requirements-dev.txt   ← + pytest, httpx (for backend/tests/)
│   ├── Dockerfile
│   ├── tests/                 ← pytest: API endpoints + scraper helpers
│   └── scrapers/
│       ├── indeed.py          ← undetected-chromedriver
│       ├── linkedin.py        ← guest HTTP API (no browser)
│       ├── wellfound.py       ← undetected-chromedriver + __NEXT_DATA__ JSON
│       ├── remote_ok.py       ← public JSON API (no browser)
│       └── _chrome.py         ← cross-platform Chrome binary/version resolution
└── frontend/
    ├── index.html             ← Vue.js 3 (CDN, no build step)
    ├── public/
    │   ├── app.js
    │   └── data.js
    ├── Dockerfile
    └── nginx.conf
```

**Not in the repo** (gitignored):
- `backend/chat/`, `backend/cv/`, `chat.py` — local-only prototypes, see [Roadmap](#roadmap)
- `profil.json`, `liked_jobs.json`, `seen_jobs.json`, `scraped_jobs.csv` — runtime/user data, regenerated locally
- `.env` — secrets (Discord token, channel ID)

---

## Setup

### 1. Clone

```bash
git clone https://github.com/sup4nova/JobScraper.git
cd JobScraper
```

### 2. Create a virtual environment

```bash
cd backend
python -m venv venv
```

### 3. Activate it

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Mac / Linux:**
```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the FastAPI backend

```bash
uvicorn main:app --reload
```

The API is available at `http://localhost:8000`.

---

## Frontend

Open `frontend/index.html` directly in a browser, or serve it via the Docker setup below. No build step needed — Vue 3 is loaded from CDN.

---

## Docker

```bash
docker-compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:8001`

---

## CLI mode

`backend/main.py` doubles as a CLI when run directly (as opposed to via `uvicorn`):

```bash
cd backend
python main.py
```

You'll be asked for a job title, city, and max results per site. All four scrapers run and results are saved to `scraped_jobs.csv`.

---

## Discord bot

The bot polls the FastAPI backend on startup, then posts new job listings as embed cards with **Apply**, **View listing**, and **Hide** buttons.

Create a `.env` file in the `backend/` folder:

```env
DISCORD_TOKEN=your_bot_token
DISCORD_CHANNEL_ID=your_channel_id

# Optional — comma-separated list of allowed origins for the API's CORS policy.
# Defaults to the Docker frontend + direct file:// access.
# CORS_ORIGINS=http://localhost:8001,null
```

Run it:

```bash
cd backend
python bot.py
```

---

## Scrapers

| Source | Method | Notes |
|---|---|---|
| Indeed | undetected-chromedriver | Cloudflare bypass via UC |
| LinkedIn | Guest HTTP API | No browser needed |
| Wellfound | undetected-chromedriver + `__NEXT_DATA__` | Parses Next.js JSON blob |
| Remote OK | Public JSON API | No browser, no auth |

Chrome-based scrapers (Indeed, Wellfound) run in a subprocess via `multiprocessing.Pool` to avoid driver conflicts.

---

## Legal / Terms of Service

Scraping Indeed, LinkedIn, and Wellfound goes against their Terms of Service — this is a known, deliberate tradeoff, not an oversight. This project was built for **personal, low-volume, educational use** (searching for my own job applications), not for redistribution, resale, or bulk data collection:

- No scraped data is republished or sold; it's used locally to generate a personal shortlist and cover letters.
- Requests are rate-limited (randomized delays between pages/cards) and use rotating user agents — not to evade detection maliciously, but to avoid hammering these sites.
- Remote OK uses a public JSON API, not scraping.

If you reuse this code, you're responsible for complying with the target sites' Terms of Service in your jurisdiction. The [MIT license](LICENSE) already disclaims warranty and liability for the software itself; it does not authorize violating a third party's ToS.

---

## Dependencies

See `backend/requirements.txt`. Key packages:

| Package | Usage |
|---|---|
| `fastapi` + `uvicorn` | REST API server |
| `undetected-chromedriver` | Anti-bot Chrome driver |
| `beautifulsoup4` | HTML parsing (LinkedIn) |
| `discord.py` | Discord bot |
| `python-dotenv` | `.env` loading |

---

## Notes

- **Indeed and LinkedIn block scrapers** — if results are empty, the site may have detected the request. Adding delays and rotating user agents helps.
- **Indeed and Wellfound** auto-detect the Chrome binary and version (`backend/scrapers/_chrome.py`) — works out of the box on both Windows and the Docker image. To pin a specific install, set `CHROME_BINARY` / `CHROME_VERSION_MAIN` in `.env`.
- **Remote OK** is the most reliable source — public API, no auth, no browser.
- CSS selectors and JSON structures may break if sites update their frontend — that's the nature of scraping.

---

## Roadmap

- [ ] **Publish the AI chat assistant** (`backend/chat/`) — currently a local prototype that routes natural-language requests (scrape, write a cover letter, gap analysis, translate) to a self-hosted [Ollama](https://ollama.com/) model. Not committed yet: needs a packaged/hosted LLM story before it's something a cloned repo can actually run, rather than a 503.
- [ ] **Publish the CV generator** (`backend/cv/`) — currently a local prototype that fills a [Typst](https://github.com/typst/typst) template from a job + profile and compiles it to PDF via the `typst` CLI. Not committed yet: needs the external CLI dependency either bundled (Docker) or clearly documented as a setup step.
- [ ] WTTJ scraper (Playwright + Algolia API) — removed as an incomplete WIP; to be rebuilt and shipped complete rather than half-working
- [ ] Config-driven API base URL — replace hardcoded `http://localhost:8000` in `bot.py` and the frontend
