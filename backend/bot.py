import os
import re
import json
from datetime import datetime, timezone
import hashlib
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import urlparse, parse_qs

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

SEEN_JOBS_FILE = "seen_jobs.json"

# ── Source styles ─────────────────────────────────────────────────────────────
SOURCE_STYLE = {
    "indeed":    {"label": "Indeed",    "color": 0x2557A7},
    "linkedin":  {"label": "LinkedIn",  "color": 0x0A66C2},
    "wellfound": {"label": "Wellfound", "color": 0x00A2E8},
}
DEFAULT_COLOR = 0x5865F2  # Discord blurple

# Icons (unicode emojis, no custom server emojis needed)
EMO_SALARY   = "💰"
EMO_MODE     = "📍"
EMO_CONTRACT = "📄"
EMO_APPLY    = "⚡"
EMO_RESUME   = "📝"
EMO_LINK     = "🔗"
EMO_HIDE     = "🙈"


# ── Seen job persistence ──────────────────────────────────────────────────────
def load_seen_jobs(current_profile: dict) -> set:
    if not os.path.exists(SEEN_JOBS_FILE):
        return set()

    with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Legacy format (plain list) → migrate
    if isinstance(data, list):
        return set(data)

    # Profile changed → reset seen list
    saved_profile = data.get("profile", {})
    if saved_profile.get("title") != current_profile.get("title") or \
       saved_profile.get("location") != current_profile.get("location"):
        print(f"Profile changed ({saved_profile.get('title')} → {current_profile.get('title')}) — resetting seen jobs")
        return set()

    return set(data.get("seen", []))


def save_seen_jobs(seen: set, profile: dict):
    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "profile": {"title": profile.get("title"), "location": profile.get("location")},
            "seen": list(seen),
        }, f, indent=2)


def extract_job_key(url: str) -> str | None:
    """Stable job identifier. Falls back to a URL hash if no `jk` param is found."""
    if not url:
        return None
    m = re.search(r"[?&]jk=([0-9A-Za-z]+)", url)
    if m:
        return m.group(1)
    # Unknown URL format → hash-based fallback (imperfect dedup but we don't skip the job)
    return "url:" + hashlib.md5(url.encode("utf-8")).hexdigest()


# ── Display helpers ───────────────────────────────────────────────────────────
def _truncate(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _clean_description(desc: str) -> str:
    """Format description: first paragraph + bullets, truncated."""
    if not desc:
        return "_No description provided._"
    # Normalize bullets to •, strip noise
    lines = [line.strip() for line in desc.splitlines() if line.strip()]
    out = []
    for line in lines:
        if line.startswith(("-", "*", "•")):
            out.append("• " + line.lstrip("-*• ").strip())
        else:
            out.append(line)
    return _truncate("\n".join(out), 600)


def _is_http(url: str) -> bool:
    return isinstance(url, str) and url.startswith(("http://", "https://"))


def build_job_embed(job: dict) -> discord.Embed:
    """Build an embed card from a job dict."""
    source = (job.get("source") or "").lower()
    style = SOURCE_STYLE.get(source, {"label": source.title() or "Job listing", "color": DEFAULT_COLOR})

    title = _truncate(job.get("title") or "Untitled", 256)
    url = job.get("url") if _is_http(job.get("url")) else None

    embed = discord.Embed(
        title=title,
        url=url,
        description=_clean_description(job.get("description")),
        color=style["color"],
        timestamp=datetime.now(timezone.utc),
    )

    # Header: company · city
    company = job.get("company") or "Unknown company"
    city = job.get("city")
    author_name = f"{company} · {city}" if city else company
    embed.set_author(name=_truncate(author_name, 256))

    # Inline fields: Salary | Mode | Contract
    embed.add_field(
        name=f"{EMO_SALARY} Salary",
        value=job.get("salary") or "Not specified",
        inline=True,
    )

    # Infer on-site/remote from contract_type or city
    contract_type = job.get("contract_type") or ""
    mode = "On-site"
    lc = contract_type.lower() + " " + (city or "").lower()
    if "télétravail" in lc or "remote" in lc or "distance" in lc:
        mode = "Remote"
    elif "hybride" in lc or "hybrid" in lc:
        mode = "Hybrid"
    embed.add_field(name=f"{EMO_MODE} Mode", value=mode, inline=True)

    # Contract type — strip the remote part already shown above
    contract_clean = re.sub(r"·?\s*(full remote|remote|hybride.*|télétravail.*|présentiel)",
                            "", contract_type, flags=re.I).strip(" ·") or "Not specified"
    embed.add_field(name=f"{EMO_CONTRACT} Contract", value=_truncate(contract_clean, 100), inline=True)

    # Footer: source + easy apply flag
    footer = style["label"]
    if job.get("easily_apply"):
        footer += "  •  ⚡ Easy Apply"
    embed.set_footer(text=footer)

    return embed


# ── Button row ────────────────────────────────────────────────────────────────
class JobCardView(discord.ui.View):
    """Button row under each job card. timeout=None so it persists after restarts."""

    def __init__(self, job: dict, resume: str | None = None):
        super().__init__(timeout=None)

        def _valid_btn_url(u):
            return _is_http(u) and len(u) <= 512

        url = job.get("url") if _valid_btn_url(job.get("url")) else None
        apply_url = job.get("apply_url") or url
        if not _valid_btn_url(apply_url):
            apply_url = None

        # ⚡ Apply button
        if apply_url:
            self.add_item(discord.ui.Button(
                label="Apply",
                emoji=EMO_APPLY,
                style=discord.ButtonStyle.link,
                url=apply_url,
            ))

        # 🔗 View listing button
        if url:
            self.add_item(discord.ui.Button(
                label="View listing",
                emoji=EMO_LINK,
                style=discord.ButtonStyle.link,
                url=url,
            ))

        if resume and _valid_btn_url(resume):
            self.add_item(discord.ui.Button(
                label="View CV",
                emoji=EMO_RESUME,
                style=discord.ButtonStyle.link,
                url=resume,
            ))

    # 🙈 Hide button
    @discord.ui.button(label="Hide", emoji=EMO_HIDE, style=discord.ButtonStyle.secondary)
    async def hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()


# ── CV generation via API ─────────────────────────────────────────────────────
async def get_cv_url(job: dict) -> str | None:
    try:
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "http://localhost:8000/api/generate-cvs",
                json={"jobs": [job]},
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                result = (data.get("results") or [{}])[0]
                if not result.get("ok") or not result.get("path"):
                    return None
                filename = Path(result["path"]).name
                return f"http://localhost:8000/cv/{filename}"
    except Exception as e:
        print(f"CV generation error: {e}")
        return None


# ── Profile + job fetching ────────────────────────────────────────────────────
async def get_profile() -> dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/profile") as resp:
                if resp.status != 200:
                    return {}
                return await resp.json()
    except Exception as e:
        print(f"Could not fetch profile: {e}")
        return {}


async def get_jobs() -> list[dict]:
    profile = await get_profile()
    query = profile.get("title", "python developer")
    city = profile.get("location", "Paris")
    print(f'Searching: "{query}" in "{city}"')

    try:
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "http://localhost:8000/api/scrape",
                json={"poste": query, "ville": city, "limite": 5},
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(f"Server error HTTP {resp.status}: {text[:300]}")
                    return []
                data = await resp.json()
                return data.get("jobs", [])
    except aiohttp.ClientConnectorError:
        print("Cannot reach localhost:8000 — is FastAPI running?")
        return []
    except Exception as e:
        print(f"get_jobs error: {type(e).__name__}: {e}")
        return []


# ── on_ready: send a card per job ─────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    channel = bot.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
    if not channel:
        print("Channel not found")
        return

    profile = await get_profile()
    seen = load_seen_jobs(profile)
    print(f"Already seen: {len(seen)} jobs")

    print("Starting scraper...")
    jobs = await get_jobs()
    print(f"Jobs found: {len(jobs)}")

    if not jobs:
        print("No jobs returned by the scraper")
        return

    new_count = 0
    for job in jobs:
        if not job.get("title"):
            continue

        # Rebuild a clean short URL from the jk param
        url = job.get("url")
        if url:
            jk = parse_qs(urlparse(url).query).get("jk", [None])[0]
            if jk:
                job["url"] = f"https://fr.indeed.com/viewjob?jk={jk}"

        job_id = extract_job_key(job.get("url", ""))
        if not job_id:
            continue

        if job_id in seen:
            print(f'Already seen: {job["title"]}')
            continue

        print(f'Sending: {job["title"]} @ {job["company"]}')
        resume = await get_cv_url(job)
        await channel.send(embed=build_job_embed(job), view=JobCardView(job, resume=resume))
        seen.add(job_id)
        new_count += 1

    save_seen_jobs(seen, profile)
    print(f"Done — {new_count} new job(s) sent")


if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
