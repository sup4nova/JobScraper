import os
import re
import json
from datetime import datetime, timezone
import hashlib
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, quote_plus

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

SEEN_JOBS_FILE = "seen_jobs.json"

# ── Habillage par source ───────────────────────────────────────────────────
SOURCE_STYLE = {
    "indeed":   {"label": "Indeed",   "color": 0x2557A7},
    "linkedin": {"label": "LinkedIn", "color": 0x0A66C2},
    "wellfound": {"label": "Wellfound", "color": 0x00A2E8},
    "wttj":     {"label": "Welcome to the Jungle", "color": 0xFFCD00},
}
DEFAULT_COLOR = 0x5865F2  # blurple

# Icônes (emojis Unicode — pas besoin d'emojis serveur)
EMO_SALARY   = "💰"
EMO_MODE     = "📍"
EMO_CONTRACT = "📄"
EMO_APPLY    = "⚡"
EMO_LINK     = "🔗"
EMO_HIDE     = "🙈"


# ── Persistance des offres vues ────────────────────────────────────────────
def load_seen_jobs(current_profile: dict) -> set:
    if not os.path.exists(SEEN_JOBS_FILE):
        return set()

    with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Ancien format (liste simple) → migration
    if isinstance(data, list):
        return set(data)

    # Si le profil a changé → reset
    saved_profile = data.get("profile", {})
    if saved_profile.get("title") != current_profile.get("title") or \
       saved_profile.get("location") != current_profile.get("location"):
        print(f"🔄 Profil changé ({saved_profile.get('title')} → {current_profile.get('title')}) — reset des offres vues")
        return set()
    print("URL:", repr(data.get("url")))

    return set(data.get("seen", []))


def save_seen_jobs(seen: set, profile: dict):
    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump({"profile": {"title": profile.get("title"), "location": profile.get("location")}, "seen": list(seen)}, f, indent=2)


def extract_job_key(url: str) -> str | None:
    """Identifiant stable d'une offre. Repli sur un hash de l'URL si pas de jk."""
    if not url:
        return None
    m = re.search(r"[?&]jk=([0-9A-Za-z]+)", url)
    if m:
        return m.group(1)
    # pagead ou format inconnu → clé de repli (dédup imparfaite mais on n'éjecte plus)
    return "url:" + hashlib.md5(url.encode("utf-8")).hexdigest()


# ── Helpers d'affichage ────────────────────────────────────────────────────
def _truncate(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _clean_description(desc: str) -> str:
    """Met la description en forme : 1er paragraphe + puces, tronqué."""
    if not desc:
        return "_Pas de description fournie._"
    # Normalise les puces en •, limite le bruit
    lines = [l.strip() for l in desc.splitlines() if l.strip()]
    out = []
    for l in lines:
        if l.startswith(("-", "*", "•")):
            out.append("• " + l.lstrip("-*• ").strip())
        else:
            out.append(l)
    return _truncate("\n".join(out), 600)  # max embed desc = 4096, on garde lisible


def _is_http(url: str) -> bool:
    return isinstance(url, str) and url.startswith(("http://", "https://"))


def build_job_embed(job: dict) -> discord.Embed:
    """Construit la carte (Embed) à partir d'une offre du scraper."""
    source = (job.get("source") or "").lower()
    style = SOURCE_STYLE.get(source, {"label": source.title() or "Offre", "color": DEFAULT_COLOR})

    title = _truncate(job.get("title") or "Offre sans titre", 256)
    url = job.get("url") if _is_http(job.get("url")) else None

    embed = discord.Embed(
        title=title,
        url=url,                       # titre cliquable
        description=_clean_description(job.get("description")),
        color=style["color"],
        timestamp=datetime.now(timezone.utc),
    )

    # En-tête : entreprise · ville
    company = job.get("company") or "Entreprise inconnue"
    city = job.get("city")
    author_name = f"{company} · {city}" if city else company
    embed.set_author(name=_truncate(author_name, 256))

    # Champs en colonnes (inline) : Salaire | Mode | Contrat
    embed.add_field(
        name=f"{EMO_SALARY} Salaire",
        value=job.get("salary") or "Non précisé",
        inline=True,
    )

    # "Mode" : on déduit présentiel/remote depuis contract_type ou city
    contract_type = job.get("contract_type") or ""
    mode = "Présentiel"
    lc = contract_type.lower() + " " + (city or "").lower()
    if "télétravail" in lc or "remote" in lc or "distance" in lc:
        mode = "Télétravail"
    elif "hybride" in lc:
        mode = "Hybride"
    embed.add_field(name=f"{EMO_MODE} Mode", value=mode, inline=True)

    # Contrat (CDI/CDD…) — on retire la partie remote déjà affichée
    contract_clean = re.sub(r"·?\s*(full remote|remote|hybride.*|télétravail.*|présentiel)",
                            "", contract_type, flags=re.I).strip(" ·") or "Non précisé"
    embed.add_field(name=f"{EMO_CONTRACT} Contrat", value=_truncate(contract_clean, 100), inline=True)

    # Pied : source + (easy apply)
    footer = style["label"]
    if job.get("easily_apply"):
        footer += "  •  ⚡ Candidature simplifiée"
    embed.set_footer(text=footer)

    return embed


# ── Vue avec les boutons ───────────────────────────────────────────────────
class JobCardView(discord.ui.View):
    """Rangée de boutons sous chaque carte. timeout=None → persiste."""

    def __init__(self, job: dict):
        super().__init__(timeout=None)

        def _valid_btn_url(u):
            return _is_http(u) and len(u) <= 512

        url = job.get("url") if _valid_btn_url(job.get("url")) else None
        apply_url = job.get("apply_url") or url
        if not _valid_btn_url(apply_url):
            apply_url = None

        # ⚡ Postuler
        if apply_url:
            self.add_item(discord.ui.Button(
                label="Postuler",
                emoji=EMO_APPLY,
                style=discord.ButtonStyle.link,
                url=apply_url,
            ))

        # 🔗 Voir l'offre
        if url:
            self.add_item(discord.ui.Button(
                label="Voir l'offre",
                emoji=EMO_LINK,
                style=discord.ButtonStyle.link,
                url=url,
            ))

    # 🙈 Cacher — bouton d'interaction (callback)
    @discord.ui.button(label="Cacher", emoji=EMO_HIDE, style=discord.ButtonStyle.secondary)
    async def hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Option A — supprimer complètement le message :
        await interaction.message.delete()

        # Option B — au lieu de supprimer, réduire à une ligne discrète :
        # (commente la ligne ci-dessus et décommente le bloc suivant)
        #
        # job_title = interaction.message.embeds[0].title if interaction.message.embeds else "Offre"
        # await interaction.response.edit_message(
        #     content=f"🙈 *Offre masquée — {job_title}*",
        #     embed=None,
        #     view=None,
        # )


# ── Récupération profil + offres (inchangé) ────────────────────────────────
async def get_profile() -> dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/profile") as resp:
                if resp.status != 200:
                    return {}
                return await resp.json()
    except Exception as e:
        print(f"Impossible de récupérer le profil: {e}")
        return {}


async def get_jobs() -> list[dict]:
    profile = await get_profile()
    query = profile.get("title", "developpeur python")
    city = profile.get("location", "Paris")
    print(f'Recherche: "{query}" à "{city}"')

    try:
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "http://localhost:8000/api/scrape",
                json={"poste": query, "ville": city, "limite": 5},
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(f"Erreur serveur HTTP {resp.status}: {text[:300]}")
                    return []
                data = await resp.json()
                return data.get("jobs", [])
    except aiohttp.ClientConnectorError:
        print("Impossible de joindre localhost:8000 — FastAPI est-il lancé ?")
        return []
    except Exception as e:
        print(f"Erreur get_jobs: {type(e).__name__}: {e}")
        return []


# ── on_ready : envoie une carte par offre ──────────────────────────────────
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    channel = bot.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
    if not channel:
        print("Channel introuvable")
        return

    profile = await get_profile()
    seen = load_seen_jobs(profile)
    print(f"Offres déjà vues : {len(seen)}")

    print("Lancement du scraper...")
    jobs = await get_jobs()
    print(f"Offres trouvées : {len(jobs)}")

    if not jobs:
        print("Aucune offre retournée par le scraper")
        return

    new_count = 0
    for job in jobs:
        if not job.get("title"):
            continue

        # Nettoyage URL : reconstruit une URL courte depuis le jk
        url = job.get("url")
        if url:
            jk = parse_qs(urlparse(url).query).get("jk", [None])[0]
            if jk:
                job["url"] = f"https://fr.indeed.com/viewjob?jk={jk}"   # ← on écrit dans job

        job_id = extract_job_key(job.get("url", ""))
        if not job_id:
            continue

        if job_id in seen:
            print(f'Déjà vue : {job["title"]}')
            continue

        print(f'Envoi : {job["title"]} @ {job["company"]}')
        await channel.send(embed=build_job_embed(job), view=JobCardView(job))
        seen.add(job_id)
        new_count += 1

    save_seen_jobs(seen, profile)
    print(f"Terminé — {new_count} nouvelle(s) offre(s) envoyée(s)")


if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
