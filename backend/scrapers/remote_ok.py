"""
Scraper Remote OK — API JSON publique (pas de navigateur)
Endpoint : https://remoteok.com/api

Aucune dépendance externe : urllib (stdlib) suffit.
À déposer dans scrapers/remoteok.py, à côté de indeed.py.
"""
import json
import re
import html
import urllib.request
import urllib.error

API_URL = "https://remoteok.com/api"

# RemoteOK renvoie 403 sur un User-Agent "python par défaut" → on imite un navigateur
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

TAG_MAP = {
    "devops":     ["dev","devops", "ops", "sys-admin", "cloud", "kubernetes"],
    "ops":        ["dev","ops", "devops", "sys-admin"],
    "automation": ["dev","devops", "ops", "python", "api"],
    "python":     ["dev","python", "backend", "api"],
    "security":   ["dev","security", "infosec"],
    "infosec":    ["dev","infosec", "security"],
    "qa":         ["dev","testing"],
    "test":       ["dev","testing"],
    "cloud":      ["dev","cloud", "aws", "devops"],
    "data":       ["dev","data-science", "analytics", "sql"],
    "backend":    ["dev","backend", "api", "python"],
    "frontend":   ["dev","front-end", "react", "javascript", "typescript"],
    "ai":         ["dev","ai", "machine-learning"],
}

def tags_for(poste: str) -> list[str] | None:
    """Dérive les tags RemoteOK depuis le poste tapé.
    None si aucun mapping → on retombe sur le filtrage texte."""
    p = (poste or "").lower()
    matched = []
    for key, slugs in TAG_MAP.items():
        if key in p:
            matched.extend(slugs)
    # dédoublonne en gardant l'ordre
    seen = set()
    out = [t for t in matched if not (t in seen or seen.add(t))]
    return out or None

def _strip_html(raw: str) -> str:
    """Enlève les balises HTML d'une description et nettoie les espaces."""
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)      # retire les balises
    text = html.unescape(text)               # &amp; → &, &eacute; → é, etc.
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def _format_salary(item: dict) -> str:
    lo = item.get("salary_min") or 0
    hi = item.get("salary_max") or 0
    if lo and hi:
        return f"${lo:,} – ${hi:,} / an (USD)"
    if hi:
        return f"Jusqu'à ${hi:,} / an (USD)"
    if lo:
        return f"À partir de ${lo:,} / an (USD)"
    return ""


class RemoteOKScraper:
    source_name = "remoteok"

    def __init__(self, query: str, city: str = "", limit: int = 20, tags=None):
        self.query = query
        self.city  = city
        self.limit = limit
        # ensemble de slugs-cibles ; None → on retombe sur le filtrage texte
        self.tags = {t.lower() for t in tags} if tags else None

    def _matches(self, item: dict, terms: list[str]) -> bool:
        # Filtrage par tag structuré (prioritaire, robuste)
        if self.tags:
            job_tags = {t.lower() for t in (item.get("tags") or [])}
            if job_tags & self.tags:        # intersection non vide → match
                return True
            # si pas de tag commun, on tente quand même le texte (titre explicite)

    # Repli : filtrage par mots-clés de la requête
        if not terms:
            return self.tags is None        # pas de tags ET pas de query → tout passe
        hay = (
            (item.get("position") or "") + " "
            + " ".join(item.get("tags") or []) + " "
            + (item.get("company") or "")
        ).lower()
        return all(t in hay for t in terms)
    

    def scrape(self) -> list[dict]:
        """Version synchrone — utilisable par le CLI et l'executor FastAPI."""
        raw_jobs = self._fetch()
        if not raw_jobs:
            return []

        terms = [t for t in self.query.lower().split() if t]
        jobs = []
        for item in raw_jobs:
            # Le 1er élément de l'API est une mention légale, pas une offre → on saute
            if not item.get("id") or not item.get("position"):
                continue
            if not self._matches(item, terms):
                continue
            jobs.append(self._to_job(item))
            if len(jobs) >= self.limit:
                break

        print(f"✅ {len(jobs)} offres récupérées (Remote OK)")
        print(jobs[0] if jobs else "Aucune offre à afficher")
        return jobs

    async def scrape_async(self) -> list[dict]:
        """Délègue à scrape() — pas de navigateur, donc pas besoin d'executor."""
        return self.scrape()

    # ── HTTP ────────────────────────────────────────────────────────────────────

    def _fetch(self) -> list[dict]:
        req = urllib.request.Request(API_URL, headers=_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            print(f"❌ Remote OK HTTP {e.code} : {e.reason}")
            return []
        except Exception as e:
            print(f"❌ Remote OK erreur : {type(e).__name__}: {e}")
            return []
        return data if isinstance(data, list) else []


    def _to_job(self, item: dict) -> dict:
        title    = (item.get("position") or "").strip()
        company  = (item.get("company") or "").strip()
        location = (item.get("location") or "").strip() or "Remote"
        url       = item.get("url") or f"https://remoteok.com/remote-jobs/{item.get('id')}"
        apply_url = item.get("apply_url") or url

        print(f"    Remote OK — {title} @ {company} ({location})")

        return {
            "source":        "remoteok",
            "title":         title,
            "url":           url,
            "apply_url":     apply_url,
            "company":       company,
            "city":          location,
            "salary":        _format_salary(item),
            "education":     "",
            # "remote" présent → l'embed du bot affichera automatiquement "Télétravail"
            "contract_type": "Remote",
            "easily_apply":  bool(item.get("apply_url")),
            "description":   _strip_html(item.get("description"))[:600],
        }


if __name__ == "__main__":
    print("🔍 Lancement du scraper Remote OK...")
    scraper = RemoteOKScraper(
    query="automation",
    limit=20,
    tags=["python", "devops", "ops", "security", "infosec",
          "sys-admin", "cloud", "aws", "api", "testing", "ai", "junior"],
    )
    jobs = scraper.scrape()
    print(f"\n📦 {len(jobs)} offres trouvées :")
    for job in jobs:
        print(f"  - {job['title']} @ {job['company']} ({job['city']})")
        print(f"    💰 {job['salary'] or 'non précisé'}")
        print(f"    🔗 {job['url']}")