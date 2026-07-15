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
| Discord bot — job cards with Apply / Hide buttons, standalone (no FastAPI dependency) | ✅ Needs a `.env` (not committed) |
| Discord bot — personal `/jobalert` DMs, per user | ✅ Working |

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
│   ├── bot.py                 ← Discord bot (standalone, no FastAPI dependency)
│   ├── scraping.py            ← shared scrape orchestration (used by main.py and bot.py)
│   ├── requirements.txt
│   ├── requirements-dev.txt   ← + pytest, httpx (for backend/tests/)
│   ├── Dockerfile             ← FastAPI + frontend stack
│   ├── Dockerfile.bot         ← Discord bot, standalone (for VPS deployment)
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
- `profil.json`, `liked_jobs.json`, `seen_jobs.json`, `subscribers.json`, `scraped_jobs.csv` — runtime/user data, regenerated locally
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

The bot is standalone — it scrapes directly (via `backend/scraping.py`, no HTTP call to the FastAPI backend) and posts new job listings as embed cards with **Apply**, **View listing**, and **Hide** buttons. It scrapes automatically **twice a day, Monday–Friday (08:00 and 14:00 server time)**, plus once immediately on startup.

Create a `.env` file in the `backend/` folder (see `backend/.env.example`):

```env
DISCORD_TOKEN=your_bot_token
DISCORD_CHANNEL_ID=your_channel_id

# Default search posted to the channel above
JOB_TITLE=python developer
JOB_LOCATION=Paris

# Optional — override where the bot stores dedup/subscriber state
# (useful when mounting a volume in Docker, e.g. /app/data/seen_jobs.json)
# SEEN_JOBS_FILE=seen_jobs.json
# SUBSCRIBERS_FILE=subscribers.json
```

Run it:

```bash
cd backend
python bot.py
```

Waiting until 08:00/14:00 to test isn't practical — use `/scrape-now` (server admins only) to trigger both the shared-channel scrape and the personal `/jobalert` cycle immediately.

### Personal alerts (`/jobalert`)

Anyone in the server can set up their own search, independent of the shared channel above — results are sent as a DM instead:

| Command | Effect |
|---|---|
| `/jobalert title: location:` | Subscribe/update your own job title + city |
| `/jobalert-status` | Show your current subscription |
| `/jobalert-stop` | Unsubscribe |

Subscribers with the same title+location are scraped together (one Chrome run instead of one per person), then each gets DM'd only the jobs they haven't seen yet.

**Requires the `applications.commands` OAuth2 scope** on the bot's invite link (in addition to `bot`) — if the bot was invited before this feature existed, regenerate the invite link in the Discord Developer Portal (check `applications.commands`) and re-invite it, otherwise the slash commands won't show up.

### Deploying just the bot (VPS)

`backend/Dockerfile.bot` builds a standalone bot image (same Chrome/Xvfb setup as the main `Dockerfile`, but running `python bot.py` instead of `uvicorn`) — no FastAPI, no port exposed. Useful when you want the bot running 24/7 on a server without deploying the full backend/frontend stack:

```bash
docker build -f backend/Dockerfile.bot -t jobscrapper-bot:latest backend/
docker run -d --name jobscrapper-bot --restart unless-stopped \
  --env-file backend/.env \
  -v /opt/jobscrapper/data:/app/data \
  -e SEEN_JOBS_FILE=/app/data/seen_jobs.json \
  -e SUBSCRIBERS_FILE=/app/data/subscribers.json \
  jobscrapper-bot:latest
```

The mounted volume keeps `seen_jobs.json`/`subscribers.json` across container restarts (otherwise every restart would re-send every job).

### Monitoring (VPS bot health → Discord alert)

`.github/workflows/vps-monitor.yml` runs on a schedule (08:30/14:30 UTC, Mon-Fri — ~30min after the bot's own scrape times), SSHes into the VPS, and checks:
- the `jobscrapper-bot` container is actually `running` (not crashed/restarting),
- the last 3h of logs for two levels of failure:
  - **global**: a `Traceback`, or the `ALERT: scrape cycle returned 0 jobs from all sources` line (`backend/scraping.py`'s `_print_recap` prints this whenever every source comes back empty at once — usually an anti-bot block, not a genuinely quiet job market);
  - **per-source**: the specific messages each scraper prints when it recognizes an actual block rather than just "0 results" — `Cloudflare` (Wellfound), `job list never appeared` / `selectors may be outdated` (Indeed), or a caught `X error:` exception (any source). A single source returning 0 with none of these messages is treated as a normal empty search, not an alert — otherwise a narrow search having a genuinely quiet day would trigger noisy false alarms.

If any of these match, it posts to a Discord webhook and fails the workflow (so it also shows up in the Actions tab / your GitHub notification email).

**One-time VPS setup:**

1. Generate a **dedicated** key for this — don't reuse your personal/deploy key:
   ```bash
   ssh-keygen -t ed25519 -f monitor_key -C "github-actions-monitor" -N ""
   ```
2. Copy `backend/monitoring/check_health.sh` to the VPS (e.g. `/opt/jobscrapper/check_health.sh`), `chmod +x` it.
3. In the monitoring user's `~/.ssh/authorized_keys`, add the **public** key with a forced command so it can never do anything but run this one read-only script, even if the private key leaks:
   ```
   command="/opt/jobscrapper/check_health.sh",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-ed25519 AAAA... github-actions-monitor
   ```
   (Running `docker logs`/`docker inspect` requires the user to be in the `docker` group, which is root-equivalent in practice — the `command=` restriction above is what actually enforces least privilege here, not the group membership.)
4. Add these repo secrets (**Settings → Secrets and variables → Actions**): `VPS_MONITOR_HOST`, `VPS_MONITOR_USER`, `VPS_MONITOR_SSH_KEY` (the private key from step 1), `DISCORD_ALERT_WEBHOOK` (Discord channel → Settings → Integrations → Webhooks).
5. Test it on demand from the Actions tab (`workflow_dispatch`) before waiting for the schedule.

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
- **`undetected-chromedriver` needs an older Chrome** — `uc==3.5.5` (unmaintained since Feb 2024) crashes mid-scrape (`NoSuchWindowException: target window already closed`) against a too-recent Chrome. Both Dockerfiles pin Chrome via [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/) (`121.0.6167.184`) instead of the system/apt Chrome for this reason. If you hit this locally, set `CHROME_BINARY`/`CHROME_VERSION_MAIN` in `.env` to point at the same pinned build (see `.env.example`) rather than your regular, auto-updating Chrome install.
- **Remote OK** is the most reliable source — public API, no auth, no browser.
- CSS selectors and JSON structures may break if sites update their frontend — that's the nature of scraping.

---

## Roadmap

- [ ] **Publish the AI chat assistant** (`backend/chat/`) — currently a local prototype that routes natural-language requests (scrape, write a cover letter, gap analysis, translate) to a self-hosted [Ollama](https://ollama.com/) model. Not committed yet: needs a packaged/hosted LLM story before it's something a cloned repo can actually run, rather than a 503.
- [ ] **Publish the CV generator** (`backend/cv/`) — currently a local prototype that fills a [Typst](https://github.com/typst/typst) template from a job + profile and compiles it to PDF via the `typst` CLI. Not committed yet: needs the external CLI dependency either bundled (Docker) or clearly documented as a setup step.
- [ ] WTTJ scraper (Playwright + Algolia API) — removed as an incomplete WIP; to be rebuilt and shipped complete rather than half-working
- [x] **`undetected-chromedriver==3.5.5` can't drive Chrome 150** — confirmed both in Docker and locally (`NoSuchWindowException: target window already closed`, `chrome=150.0.7871.101`). `uc` 3.5.5 (unmaintained since 2024-02-17) has hit a compatibility ceiling with newer Chrome releases. Worked around by pinning Chrome to `121.0.6167.184` via [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/) (Google's official archive of historical builds — the apt repo only ever serves current stable, so it couldn't be used to pin an older version). Tradeoff: this Chrome build only gets used for scraping and won't receive security updates; revisit if `uc` ever ships a release that supports current Chrome, or consider migrating to an actively maintained stealth driver (e.g. SeleniumBase's UC mode) instead of re-pinning indefinitely.
