import os
import re
import sys
import json
import asyncio
from datetime import datetime, time, timezone
import hashlib
import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs

# Must run before the `scraping` import below, so this module is importable
# regardless of the current working directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraping import _run_scrape_in_process

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

SEEN_JOBS_FILE = os.getenv("SEEN_JOBS_FILE", "seen_jobs.json")
SUBSCRIBERS_FILE = os.getenv("SUBSCRIBERS_FILE", "subscribers.json")

# Weekday scraping schedule (Mon-Fri only, checked inside the task below)
SCRAPE_TIMES = [time(hour=8, minute=0), time(hour=14, minute=0)]

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


# ── Per-user subscriptions (personal /jobalert config) ────────────────────────
def load_subscribers() -> dict:
    if not os.path.exists(SUBSCRIBERS_FILE):
        return {}
    with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_subscribers(subs: dict):
    with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(subs, f, ensure_ascii=False, indent=2)


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


def _clean_job_url(job: dict):
    """Rebuild a clean short Indeed URL from the `jk` param, in place."""
    url = job.get("url")
    if url:
        jk = parse_qs(urlparse(url).query).get("jk", [None])[0]
        if jk:
            job["url"] = f"https://fr.indeed.com/viewjob?jk={jk}"


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

    def __init__(self, job: dict):
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

    # 🙈 Hide button
    @discord.ui.button(label="Hide", emoji=EMO_HIDE, style=discord.ButtonStyle.secondary)
    async def hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()


# ── Profile + job fetching ────────────────────────────────────────────────────
def get_profile() -> dict:
    """Job title / location config, set via env vars (no FastAPI backend on the VPS)."""
    return {
        "title": os.getenv("JOB_TITLE", "python developer"),
        "location": os.getenv("JOB_LOCATION", "Paris"),
    }


async def get_jobs(profile: dict) -> list[dict]:
    query = profile.get("title", "python developer")
    city = profile.get("location", "Paris")
    print(f'Searching: "{query}" in "{city}"')

    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(
            None, lambda: _run_scrape_in_process(query, city, 5)
        )
    except Exception as e:
        print(f"get_jobs error: {type(e).__name__}: {e}")
        return []


# ── Scrape cycle: fetch jobs, send a card per new one ─────────────────────────
async def run_scrape_cycle(channel):
    profile = get_profile()
    seen = load_seen_jobs(profile)
    print(f"Already seen: {len(seen)} jobs")

    print("Starting scraper...")
    jobs = await get_jobs(profile)
    print(f"Jobs found: {len(jobs)}")

    if not jobs:
        print("No jobs returned by the scraper")
        return

    new_count = 0
    for job in jobs:
        if not job.get("title"):
            continue

        _clean_job_url(job)

        job_id = extract_job_key(job.get("url", ""))
        if not job_id:
            continue

        if job_id in seen:
            print(f'Already seen: {job["title"]}')
            continue

        print(f'Sending: {job["title"]} @ {job["company"]}')
        await channel.send(embed=build_job_embed(job), view=JobCardView(job))
        seen.add(job_id)
        new_count += 1

    save_seen_jobs(seen, profile)
    print(f"Done — {new_count} new job(s) sent")


# ── Personal alerts: slash commands ───────────────────────────────────────────
@bot.tree.command(name="jobalert", description="Reçois tes propres offres d'emploi en MP")
@app_commands.describe(title="Poste recherché", location="Ville")
async def jobalert(interaction: discord.Interaction, title: str, location: str):
    subs = load_subscribers()
    uid = str(interaction.user.id)
    existing = subs.get(uid, {})
    subs[uid] = {"title": title, "location": location, "seen": existing.get("seen", [])}
    save_subscribers(subs)
    await interaction.response.send_message(
        f"C'est noté : tu recevras en MP les offres pour **{title}** à **{location}**.",
        ephemeral=True,
    )


@bot.tree.command(name="jobalert-stop", description="Arrête tes alertes personnelles")
async def jobalert_stop(interaction: discord.Interaction):
    subs = load_subscribers()
    uid = str(interaction.user.id)
    if subs.pop(uid, None) is not None:
        save_subscribers(subs)
        await interaction.response.send_message("Alertes désactivées.", ephemeral=True)
    else:
        await interaction.response.send_message("Tu n'avais pas d'alerte active.", ephemeral=True)


@bot.tree.command(name="jobalert-status", description="Affiche ta configuration actuelle")
async def jobalert_status(interaction: discord.Interaction):
    sub = load_subscribers().get(str(interaction.user.id))
    if not sub:
        await interaction.response.send_message("Aucune alerte configurée. Utilise `/jobalert`.", ephemeral=True)
    else:
        await interaction.response.send_message(
            f"Poste : **{sub['title']}** — Ville : **{sub['location']}**", ephemeral=True,
        )


async def run_subscriber_cycle():
    """Scrape once per distinct (title, location) among subscribers, DM new jobs to each."""
    subs = load_subscribers()
    if not subs:
        return

    groups: dict[tuple[str, str], list[str]] = {}
    for uid, sub in subs.items():
        key = (sub["title"].strip().lower(), sub["location"].strip().lower())
        groups.setdefault(key, []).append(uid)

    loop = asyncio.get_event_loop()
    for (title, location), uids in groups.items():
        try:
            jobs = await loop.run_in_executor(
                None, lambda t=title, l=location: _run_scrape_in_process(t, l, 5)
            )
        except Exception as e:
            print(f"run_subscriber_cycle scrape error for '{title}' / '{location}': {type(e).__name__}: {e}")
            continue

        for job in jobs:
            _clean_job_url(job)

        for uid in uids:
            sub = subs[uid]
            seen = set(sub.get("seen", []))
            try:
                user = await bot.fetch_user(int(uid))
            except discord.NotFound:
                print(f"Subscriber {uid} not found — skipping")
                continue

            new_count = 0
            for job in jobs:
                job_id = extract_job_key(job.get("url", ""))
                if not job.get("title") or not job_id or job_id in seen:
                    continue
                try:
                    await user.send(embed=build_job_embed(job), view=JobCardView(job))
                except discord.Forbidden:
                    print(f"Cannot DM user {uid} (DMs closed) — skipping")
                    break
                seen.add(job_id)
                new_count += 1

            sub["seen"] = list(seen)
            print(f"Sent {new_count} job(s) to subscriber {uid}")

    save_subscribers(subs)


def _get_channel():
    channel = bot.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
    if not channel:
        print("Channel not found")
    return channel


# ── Manual trigger (testing/admin) ────────────────────────────────────────────
@bot.tree.command(name="scrape-now", description="Force un scrape immédiat (admin only)")
async def scrape_now(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Réservé aux admins du serveur.", ephemeral=True)
        return

    # Scraping (Selenium + Chrome) takes well over Discord's 3s response window,
    # so acknowledge immediately and follow up once both cycles are done.
    await interaction.response.defer(ephemeral=True)
    channel = _get_channel()
    if channel:
        await run_scrape_cycle(channel)
    await run_subscriber_cycle()
    await interaction.followup.send("Scrape terminé — voir les logs pour le détail.", ephemeral=True)


# ── Scheduled scraping: weekdays only, twice a day ────────────────────────────
@tasks.loop(time=SCRAPE_TIMES)
async def scheduled_scrape():
    if datetime.now().weekday() >= 5:  # Saturday=5, Sunday=6
        print("Weekend — skip scheduled scrape")
        return
    channel = _get_channel()
    if channel:
        await run_scrape_cycle(channel)
    await run_subscriber_cycle()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    channel = _get_channel()
    if not channel:
        return

    if channel.guild:
        await bot.tree.sync(guild=channel.guild)

    await run_scrape_cycle(channel)
    await run_subscriber_cycle()

    if not scheduled_scrape.is_running():
        scheduled_scrape.start()


if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
