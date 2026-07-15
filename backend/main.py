"""
JobScraper — FastAPI backend + CLI
"""
import csv
import json
import os
import asyncio
import sys
import threading
from multiprocessing import freeze_support
freeze_support()  # required on Windows to avoid a RuntimeError when spawning processes

# Must run before the `scrapers.*` imports below, so this module is importable
# regardless of the current working directory (e.g. `import backend.main`).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from pydantic import BaseModel
from scrapers.indeed import IndeedScraper
from scrapers.remote_ok import RemoteOKScraper
from scrapers.linkedin import LinkedInScraper
from scrapers.wellfound import WellfoundScraper
from scraping import _run_scrape_in_process, _print_recap
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

CV_OUTPUT = Path(__file__).parent / "cv" / "output"
CV_OUTPUT.mkdir(parents=True, exist_ok=True)
app.mount("/cv", StaticFiles(directory=str(CV_OUTPUT)), name="cv")

# backend/chat/ is local-only (not committed - see README), so it's imported lazily
# on first use rather than at module load, same pattern as cv.generator below.
# Single session shared across requests — holds scraped jobs, last letter, chat history.
# This is intentionally single-user (personal-use tool, not a multi-tenant product):
# swap for a per-cookie dict if you need to support multiple concurrent users.
_session = None
_session_lock = threading.Lock()


def _get_session():
    global _session
    if _session is None:
        with _session_lock:
            if _session is None:  # re-check: another request may have won the race
                from chat.agent import Session
                _session = Session()
    return _session


class ChatRequest(BaseModel):
    message: str
    model: str = "qwen2.5:7b"  # mirrors chat.ollama_client.DEFAULT_MODEL


@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        from chat.agent import handle_message
    except ModuleNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Chat is unavailable: backend/chat/ is local-only and not included in this repo (see README).",
        )
    try:
        reply = handle_message(req.message, _get_session(), req.model)
        return {"reply": reply}
    except ConnectionError as e:
        # Ollama isn't running — return a clear 503 instead of a generic 500
        raise HTTPException(status_code=503, detail=str(e))


LIKED_FILE = Path("liked_jobs.json")


class LikeRequest(BaseModel):
    jobs: list[dict]


# Default covers the Docker frontend (8001) and "null" for index.html opened
# directly as a local file (Origin: null). The Docker frontend also proxies
# /api/ through nginx (same-origin), so CORS mainly matters for that file:// case.
# Override with a comma-separated list in CORS_ORIGINS for other setups.
_default_origins = "http://localhost:8001,null"
_cors_origins = os.getenv("CORS_ORIGINS", _default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI!"}


@app.get("/health")
def health():
    """Liveness probe for docker-compose / orchestrators."""
    return {"ok": True}


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
    # Load existing likes
    existing = []
    if LIKED_FILE.exists():
        existing = json.loads(LIKED_FILE.read_text(encoding="utf-8"))

    # Merge in new ones, deduplicating by URL
    seen = {j["url"] for j in existing}
    new_jobs = [j for j in req.jobs if j["url"] not in seen]
    existing.extend(new_jobs)

    LIKED_FILE.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f">>> saved {len(new_jobs)} new likes ({len(existing)} total)")
    return {"saved": len(new_jobs), "total": len(existing)}


class ScrapeRequest(BaseModel):
    poste: str
    ville: str = "France"
    limite: int = 20


@app.post("/api/generate-cvs")
async def generate_cvs(req: LikeRequest):
    try:
        from cv.generator import generate_cv
    except ModuleNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="CV generation is unavailable: backend/cv/ is a local-only prototype, not in this repo.",
        )

    if not LIKED_FILE.exists():
        raise HTTPException(status_code=404, detail="No liked jobs found")

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
        loop = asyncio.get_event_loop()
        jobs = await loop.run_in_executor(
            None,
            lambda: _run_scrape_in_process(req.poste, req.ville, req.limite)
        )
        print(f">>> {len(jobs)} jobs found")
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

    poste      = input("Job title (e.g. Python developer, data analyst): ").strip()
    ville      = input("City (leave blank for all of France): ").strip() or "France"
    limite_raw = input("Max results per site [20]: ").strip()
    limite     = int(limite_raw) if limite_raw.isdigit() else 20

    print("\nScraping Indeed + LinkedIn + Wellfound + Remote OK...\n")

    indeed_jobs = []
    try:
        indeed_jobs = IndeedScraper(query=poste, city=ville, limit=limite).scrape()
    except Exception as e:
        print(f"Indeed error: {e}")

    linkedin_jobs = []
    try:
        linkedin_jobs = LinkedInScraper(query=poste, city=ville, limit=limite).scrape()
    except Exception as e:
        print(f"LinkedIn error: {e}")

    remoteok_jobs = []
    try:
        remoteok_jobs = RemoteOKScraper(query=poste, city=ville, limit=limite).scrape()
    except Exception as e:
        print(f"Remote OK error: {e}")

    wellfound_jobs = []
    try:
        wellfound_jobs = WellfoundScraper(query=poste, city=ville, limit=limite).scrape()
    except Exception as e:
        print(f"Wellfound error: {e}")

    _print_recap({
        "Indeed":    indeed_jobs,
        "LinkedIn":  linkedin_jobs,
        "Remote OK": remoteok_jobs,
        "Wellfound": wellfound_jobs,
    })

    jobs = indeed_jobs + linkedin_jobs + remoteok_jobs + wellfound_jobs
    if not jobs:
        print("No jobs found.")
        return

    save_csv(jobs)
    selected = select_jobs(jobs)
    if selected:
        generate_cvs_cli(selected)
    else:
        print("No jobs selected. Bye!")


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
                row["easily_apply"] = "Yes" if row["easily_apply"] else "No"
            writer.writerow(row)
    print(f"Saved to {csv_file}\n")


# ── Job picker ────────────────────────────────────────────────────────────────

def select_jobs(offres: list[dict]) -> list[dict]:
    selected = []
    print("─" * 55)
    print(f"Pick your jobs ({len(offres)} total)")
    print("  [y] keep   [n] skip   [q] done")
    print("─" * 55 + "\n")

    for i, offre in enumerate(offres, 1):
        easily = " ⚡ Easy Apply" if offre.get("easily_apply") else ""
        print(f"[{i}/{len(offres)}] {offre.get('title', '?')} — {offre.get('company', '?')}")
        print(f"      📍 {offre.get('city', '?')}  💰 {offre.get('salary') or 'salary not listed'}{easily}")
        print(f"      🔗 {offre.get('url', '')[:80]}")
        if offre.get("description"):
            print(f"      📝 {offre['description'].splitlines()[0][:120]}")
        print()

        choice = input("      → Keep? [y/n/q]: ").strip().lower()
        print()
        if choice == "q":
            break
        if choice == "y":
            selected.append(offre)

    print(f"{'─' * 55}")
    print(f"{len(selected)} job(s) selected.\n")
    return selected


# ── CV generation ─────────────────────────────────────────────────────────────

def generate_cvs_cli(offres: list[dict]):
    try:
        from cv.generator import generate_cv
    except ModuleNotFoundError:
        print("\n⚠️  CV generation is unavailable: backend/cv/ is a local-only prototype, not in this repo.\n")
        return

    print("─" * 55)
    print("Generating CVs")
    print("─" * 55 + "\n")

    user = collect_user_profile()

    for offre in offres:
        print(f"  📄 {offre['title']} — {offre.get('company', '')}...")
        path = asyncio.run(generate_cv(offre, user))
        if path:
            print(f"     ✅ {path}")
        else:
            print("     ❌ Failed (is Typst installed?)")
    print()


# ── User profile ──────────────────────────────────────────────────────────────

PROFIL_FILE = "profil.json"


def collect_user_profile() -> dict:
    # Load saved profile if it exists
    if os.path.exists(PROFIL_FILE):
        with open(PROFIL_FILE, encoding="utf-8") as f:
            profil = json.load(f)
        print(f"Profile loaded from {PROFIL_FILE}")
        if input("   Edit profile? [y/N]: ").strip().lower() != "y":
            return profil

    print("\nYour details for the CV:\n")
    profil = {
        "name":           input("  Full name       : ").strip(),
        "title":          input("  Target title    : ").strip(),
        "email":          input("  Email           : ").strip(),
        "phone":          input("  Phone           : ").strip(),
        "location":       input("  City            : ").strip(),
        "github":         input("  GitHub (opt.)   : ").strip(),
        "summary":        input("  Tagline (1 line): ").strip(),
        "skills":         input("  Skills (comma-separated): ").strip().replace(",", "\n"),
        "experience":     "",
        "education_text": "",
    }

    # Save so it's pre-filled next run
    with open(PROFIL_FILE, "w", encoding="utf-8") as f:
        json.dump(profil, f, ensure_ascii=False, indent=2)
    print(f"\nProfile saved to {PROFIL_FILE}\n")
    return profil


if __name__ == "__main__":
    main()
