"""
JobScraper — FastAPI backend + CLI
"""
import csv
import json
import os
import asyncio
import sys
import json
from pathlib import Path
from pydantic import BaseModel
from scrapers.indeed import IndeedScraper
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Make backend/chat/ importable from here
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chat.agent import handle_message, Session
from chat.ollama_client import DEFAULT_MODEL

app = FastAPI()

# Single session shared across requests — holds scraped jobs, last letter, chat history
# (single-user only; swap for a per-cookie dict to support multiple users)
_session = Session()


class ChatRequest(BaseModel):
    message: str           # the user's message from the frontend
    model: str = DEFAULT_MODEL  # Ollama model to use, defaults to qwen2.5:7b


@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        # Delegate to agent: routes the intent, calls the right tool, returns a string
        reply = handle_message(req.message, _session, req.model)
        return {"reply": reply}
    except ConnectionError as e:
        # Ollama is not running — tell the frontend clearly instead of a 500
        raise HTTPException(status_code=503, detail=str(e))

LIKED_FILE = Path("liked_jobs.json")

class LikeRequest(BaseModel):
    jobs: list[dict]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/hello")
def hello():
    return {"message": "Hello depuis FastAPI !"}


class ProfileSaveRequest(BaseModel):
    name: str = ""
    title: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    github: str = ""
    summary: str = ""
    skills: str = ""
    experience: str = ""
    education_text: str = ""


@app.get("/api/profile")
def get_profile():
    p = Path("profil.json")
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


@app.post("/api/profile")
def save_profile_route(req: ProfileSaveRequest):
    p = Path("profil.json")
    p.write_text(json.dumps(req.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True}


@app.post("/api/likes")
def save_likes(req: LikeRequest):
    # Charge les likes existants
    existing = []
    if LIKED_FILE.exists():
        existing = json.loads(LIKED_FILE.read_text(encoding="utf-8"))

    # Ajoute les nouveaux sans doublons (par URL)
    seen = {j["url"] for j in existing}
    new_jobs = [j for j in req.jobs if j["url"] not in seen]
    existing.extend(new_jobs)

    LIKED_FILE.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f">>> {len(new_jobs)} nouveaux likes sauvegardés ({len(existing)} total)")
    return {"saved": len(new_jobs), "total": len(existing)}

class ScrapeRequest(BaseModel):
    poste: str
    ville: str = "France"
    limite: int = 20

@app.post("/api/generate-cvs")
async def generate_cvs(req: LikeRequest):
    from cv.generator import generate_cv

    if not LIKED_FILE.exists():
        raise HTTPException(status_code=404, detail="Aucun job liké trouvé")

    user = {}
    profil_path = Path("profil.json")
    if profil_path.exists():
        user = json.loads(profil_path.read_text(encoding="utf-8"))

    results = []
    for job in req.jobs:
        path = await generate_cv(job, user)
        results.append({
            "job":     job.get("title"),
            "company": job.get("company"),
            "path":    path,
            "ok":      path is not None,
        })

    return {"results": results}

@app.post("/api/scrape")
async def scrape(req: ScrapeRequest):
    try:
        jobs = await IndeedScraper(
            query=req.poste, city=req.ville, limit=req.limite
        ).scrape_async()
        print(f">>> {len(jobs)} jobs trouvés")
        return {"jobs": jobs}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 50)
    print("        JOB SCRAPER + CV GENERATOR")
    print("=" * 50 + "\n")

    poste      = input("Poste recherché : ").strip()
    ville      = input("Ville (vide = toute la France) : ").strip() or "France"
    limite_raw = input("Nombre max d'offres [20] : ").strip()
    limite     = int(limite_raw) if limite_raw.isdigit() else 20

    print(f"\n⏳ Scraping Indeed en cours...\n")

    try:
        jobs = IndeedScraper(query=poste, city=ville, limit=limite).scrape()
        print(f"\n✅ {len(jobs)} offres récupérées.\n")
        save_csv(jobs)
        offres_selectionnees = select_jobs(jobs)
        if offres_selectionnees:
            generer_cvs(offres_selectionnees)
        else:
            print("Aucune offre sélectionnée. À bientôt !")
    except Exception as e:
        print(f"❌ Erreur : {e}")


# ── CSV ───────────────────────────────────────────────────────────────────────

def save_csv(offres: list[dict]):
    csv_file   = "scraped_jobs.csv"
    fieldnames = [
        "source", "title", "company", "city", "salary",
        "contract_type", "education", "easily_apply", "description", "url",
    ]
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for job in offres:
            row = dict(job)
            if isinstance(row.get("easily_apply"), bool):
                row["easily_apply"] = "Oui" if row["easily_apply"] else "Non"
            writer.writerow(row)
    print(f"💾 Offres sauvegardées dans {csv_file}\n")


# ── Sélecteur CLI ─────────────────────────────────────────────────────────────

def select_jobs(offres: list[dict]) -> list[dict]:
    selected = []
    print("─" * 55)
    print(f"Sélection des offres ({len(offres)} au total)")
    print("  [o] garder   [n] ignorer   [q] terminer")
    print("─" * 55 + "\n")

    for i, offre in enumerate(offres, 1):
        easily = " ⚡ Candidature simplifiée" if offre.get("easily_apply") else ""
        print(f"[{i}/{len(offres)}] {offre.get('title', '?')} — {offre.get('company', '?')}")
        print(f"      📍 {offre.get('city', '?')}  💰 {offre.get('salary') or 'salaire non précisé'}{easily}")
        print(f"      🔗 {offre.get('url', '')[:80]}")
        if offre.get("description"):
            print(f"      📝 {offre['description'].splitlines()[0][:120]}")
        print()

        choix = input("      → Garder ? [o/n/q] : ").strip().lower()
        print()
        if choix == "q":
            break
        if choix == "o":
            selected.append(offre)

    print(f"{'─' * 55}")
    print(f"✅ {len(selected)} offre(s) sélectionnée(s).\n")
    return selected


# ── Génération CV ─────────────────────────────────────────────────────────────

def generer_cvs(offres: list[dict]):
    from cv.generator import generate_cv

    print("─" * 55)
    print("Génération des CVs")
    print("─" * 55 + "\n")

    user = collecter_infos_user()

    for offre in offres:
        print(f"  📄 {offre['title']} — {offre.get('company', '')}...")
        path = asyncio.run(generate_cv(offre, user))
        if path:
            print(f"     ✅ {path}")
        else:
            print("     ❌ Échec (Typst installé ?)")
    print()


# ── Profil utilisateur ────────────────────────────────────────────────────────

PROFIL_FILE = "profil.json"


def collecter_infos_user() -> dict:
    if os.path.exists(PROFIL_FILE):
        with open(PROFIL_FILE, encoding="utf-8") as f:
            profil = json.load(f)
        print(f"✅ Profil chargé depuis {PROFIL_FILE}")
        if input("   Modifier ? [o/N] : ").strip().lower() != "o":
            return profil

    print("\nTes informations pour le CV :\n")
    profil = {
        "name":           input("  Nom complet          : ").strip(),
        "title":          input("  Titre / poste visé   : ").strip(),
        "email":          input("  Email                : ").strip(),
        "phone":          input("  Téléphone            : ").strip(),
        "location":       input("  Ville                : ").strip(),
        "github":         input("  GitHub (optionnel)   : ").strip(),
        "summary":        input("  Accroche (1 ligne)   : ").strip(),
        "skills":         input("  Compétences (virgule) : ").strip().replace(",", "\n"),
        "experience":     "",
        "education_text": "",
    }

    with open(PROFIL_FILE, "w", encoding="utf-8") as f:
        json.dump(profil, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Profil sauvegardé dans {PROFIL_FILE}\n")
    return profil


if __name__ == "__main__":
    main()