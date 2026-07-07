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
| Discord bot — job cards with Apply / Hide buttons | ✅ Local only |
| WTTJ scraper | 🚧 WIP |
| AI assistant (Ollama) | 🚧 Local only |
| Tailored CV generator (Typst) | 🚧 Local only |

---

## Architecture

```
JobScrapper/
├── main.py                    ← CLI entry point (scrape → pick → generate CV)
├── docker-compose.yml
├── backend/
│   ├── main.py                ← FastAPI app + scraping orchestration
│   ├── models.py              ← Job data model
│   ├── bot.py                 ← Discord bot
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── scrapers/
│   │   ├── indeed.py          ← undetected-chromedriver
│   │   ├── linkedin.py        ← guest HTTP API (no browser)
│   │   ├── wellfound.py       ← undetected-chromedriver + __NEXT_DATA__ JSON
│   │   ├── remote_ok.py       ← public JSON API (no browser)
│   │   └── WIP/
│   │       └── wttj.py        ← Playwright + Algolia (in progress)
│   └── api/
│       └── routes.py
└── frontend/
    ├── index.html             ← Vue.js 3 (CDN, no build step)
    ├── public/
    │   ├── app.js
    │   └── data.js
    ├── Dockerfile
    └── nginx.conf
```

**Not in the repo** (local-only, gitignored):
- `backend/chat/` — Ollama LLM agent
- `backend/cv/` — Typst CV generator
- `profil.json`, `liked_jobs.json`, `seen_jobs.json` — runtime user data
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

Run the scraper interactively from the terminal:

```bash
python main.py
```

You'll be asked for a job title, city, max results per site, and which sites to use. Results are saved to `scraped_jobs.csv`.

---

## Discord bot

The bot polls the FastAPI backend on startup, then posts new job listings as embed cards with **Apply**, **View listing**, and **Hide** buttons.

Create a `.env` file in the `backend/` folder:

```env
DISCORD_TOKEN=your_bot_token
DISCORD_CHANNEL_ID=your_channel_id
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
| WTTJ | Playwright + Algolia API | WIP |

Chrome-based scrapers (Indeed, Wellfound) run in a subprocess via `multiprocessing.Pool` to avoid driver conflicts.

---

## Dependencies

See `backend/requirements.txt`. Key packages:

| Package | Usage |
|---|---|
| `fastapi` + `uvicorn` | REST API server |
| `undetected-chromedriver` | Anti-bot Chrome driver |
| `beautifulsoup4` | HTML parsing (LinkedIn) |
| `playwright` | WTTJ scraper (WIP) |
| `discord.py` | Discord bot |
| `python-dotenv` | `.env` loading |

---

## Notes

- **Indeed and LinkedIn block scrapers** — if results are empty, the site may have detected the request. Adding delays and rotating user agents helps.
- **Indeed and Wellfound** auto-detect the Chrome binary and version (`backend/scrapers/_chrome.py`) — works out of the box on both Windows and the Docker image. To pin a specific install, set `CHROME_BINARY` / `CHROME_VERSION_MAIN` in `.env`.
- **Remote OK** is the most reliable source — public API, no auth, no browser.
- CSS selectors and JSON structures may break if sites update their frontend — that's the nature of scraping.
