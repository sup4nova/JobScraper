"""
Les 4 outils du chatbot :
  scrape_jobs      → lance les scrapers existants
  generate_letter  → lettre de motivation via LLM
  analyze_gap      → comparaison profil vs offre via LLM
  translate_text   → traduction via LLM
"""
import asyncio
import sys
import os

# S'assure que backend/ est dans le path pour importer les scrapers
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from chat.ollama_client import call


# ── Scraping ──────────────────────────────────────────────────────────────────

def scrape_jobs(query: str, sites: list[str], limit: int = 10) -> list[dict]:
    from scrapers.indeed import IndeedScraper
    from scrapers.linkedin import LinkedInScraper
    from scrapers.WIP.wttj import WTTJScraper
    from scrapers.remote_ok import RemoteOKScraper
    from scrapers.wellfound import WellfoundScraper

    offres: list[dict] = []

    if "indeed" in sites:
        try:
            print("  → Indeed...")
            jobs = IndeedScraper(query=query, city="", limit=limit).scrape()
            offres.extend(jobs)
            print(f"     {len(jobs)} offres")
        except Exception as e:
            print(f"     ⚠️ Indeed : {e}")

    if "remoteok" in sites:
        try:
            print("  → Remote OK...")
            jobs = RemoteOKScraper(query=query, limit=limit).scrape()
            offres.extend(jobs)
            print(f"     {len(jobs)} offres")
        except Exception as e:
            print(f"     ⚠️ Remote OK : {e}")

    if "linkedin" in sites:
        try:
            print("  → LinkedIn...")
            jobs = LinkedInScraper(query=query, city="", limit=limit).scrape()
            offres.extend(jobs)
            print(f"     {len(jobs)} offres")
        except Exception as e:
            print(f"     ⚠️ LinkedIn : {e}")


    if "wellfound" in sites:
        try:
            print("  → Wellfound...")
            jobs = WellfoundScraper(query=query, city="", limit=limit).scrape()
            offres.extend(jobs)
            print(f"     {len(jobs)} offres")
        except Exception as e:
            print(f"     ⚠️ Wellfound : {e}")

    async def _async_scrapers():
        results = []
        if "wttj" in sites:
            try:
                print("  → WTTJ...")
                jobs = await WTTJScraper(query=query, city="", limit=limit).scrape()
                results.extend(jobs)
                print(f"     {len(jobs)} offres")
            except Exception as e:
                print(f"     ⚠️ WTTJ : {e}")
        return results

    if "wttj" in sites:
        offres.extend(asyncio.run(_async_scrapers()))

    return offres


def format_jobs_list(offres: list[dict]) -> str:
    """Formate la liste des offres pour l'affichage dans le terminal."""
    lines = []
    for i, o in enumerate(offres, 1):
        sal = f"  💶 {o['salary']}" if o.get("salary") else ""
        src = (o.get("source") or "?").upper()
        lines.append(f"  {i}. {o.get('title', '?')} — {o.get('company', '?')} [{src}]{sal}")
        lines.append(f"     📍 {o.get('city', '?')}   🔗 {(o.get('url') or '')[:70]}")
        if o.get("description"):
            snippet = o["description"].splitlines()[0][:100]
            lines.append(f"     📝 {snippet}")
        lines.append("")
    return "\n".join(lines)


# ── Lettre de motivation ───────────────────────────────────────────────────────

def generate_letter(job: dict, profil: dict, model: str) -> str:
    job_block = (
        f"Poste : {job.get('title')}\n"
        f"Entreprise : {job.get('company')}\n"
        f"Lieu : {job.get('city')}\n"
        f"Description :\n{(job.get('description') or 'non précisée')[:2000]}"
    )
    profil_block = (
        f"Nom : {profil.get('name')}\n"
        f"Titre visé : {profil.get('title')}\n"
        f"Compétences : {profil.get('skills')}\n"
        f"Résumé : {profil.get('summary')}\n"
        f"Expérience : {profil.get('experience') or 'non précisée'}\n"
        f"Formation : {profil.get('education_text') or 'non précisée'}"
    )
    messages = [
        {
            "role": "system",
            "content": (
                "Tu es expert en rédaction de lettres de motivation professionnelles. "
                "Rédige des lettres personnalisées, convaincantes et adaptées au poste, en français."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Rédige une lettre de motivation pour ce poste.\n\n"
                f"OFFRE :\n{job_block}\n\n"
                f"MON PROFIL :\n{profil_block}\n\n"
                "La lettre doit :\n"
                "- Mentionner explicitement l'entreprise et le poste\n"
                "- S'appuyer sur les compétences du profil en lien avec l'offre\n"
                "- Tenir en 3 paragraphes : accroche → compétences pertinentes → conclusion\n"
                "- Faire environ 250-300 mots\n"
                "- Commencer par 'Madame, Monsieur,' et finir par une formule de politesse"
            ),
        },
    ]
    return call(messages, model)


# ── Analyse du gap ─────────────────────────────────────────────────────────────

def analyze_gap(job: dict, profil: dict, model: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "Tu es un expert RH. Compare un profil candidat à une offre d'emploi. "
                "Sois direct, précis et structuré. Réponds en français."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Compare mon profil à cette offre et donne :\n"
                f"1. ✅ Ce qui MATCHE (compétences présentes des deux côtés)\n"
                f"2. ❌ Ce qui MANQUE dans mon profil (exigences non couvertes)\n"
                f"3. Score de match estimé /10 avec justification\n\n"
                f"OFFRE : {job.get('title')} @ {job.get('company')}\n"
                f"Description : {(job.get('description') or 'non disponible')[:2500]}\n\n"
                f"MON PROFIL :\n"
                f"- Titre : {profil.get('title')}\n"
                f"- Compétences : {profil.get('skills')}\n"
                f"- Résumé : {profil.get('summary')}\n"
                f"- Expérience : {profil.get('experience') or 'non précisée'}\n"
                f"- Formation : {profil.get('education_text') or 'non précisée'}"
            ),
        },
    ]
    return call(messages, model)


# ── Traduction ─────────────────────────────────────────────────────────────────

_LANG_NAMES = {
    "en": "anglais",
    "fr": "français",
    "de": "allemand",
    "es": "espagnol",
    "it": "italien",
}


def translate_text(text: str, target: str, model: str) -> str:
    lang = _LANG_NAMES.get(target, target)
    messages = [
        {
            "role": "system",
            "content": (
                f"Tu es traducteur professionnel. "
                f"Traduis fidèlement en {lang} en conservant le ton, la mise en forme et le registre."
            ),
        },
        {
            "role": "user",
            "content": f"Traduis ce texte en {lang} :\n\n{text}",
        },
    ]
    return call(messages, model)
