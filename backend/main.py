"""
JobScraper — FastAPI backend + CLI
"""
import csv
import json
import os
import asyncio
import sys
from pathlib import Path
from pydantic import BaseModel
from scrapers.indeed import IndeedScraper
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chat.agent import handle_message, Session
from chat.ollama_client import DEFAULT_MODEL

app = FastAPI()

# Single session shared across requests — holds scraped jobs, last letter, chat history.
# Not thread-safe; swap for a per-cookie dict to support multiple concurrent users.
_session = Session()


class ChatRequest(BaseModel):
    message: str
    model: str = DEFAULT_MODEL


@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        reply = handle_message(req.message, _session, req.model)
        return {"reply": reply}
    except ConnectionError as e:
        # Ollama isn't running — return a clear 503 instead of a generic 500
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
    return {"message": "Hello from FastAPI!"}


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
    from cv.generator import generate_cv

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
        jobs = await IndeedScraper(
            query=req.poste, city=req.ville, limit=req.limite
        ).scrape_async()
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

    print(f"\nScraping Indeed...\n")

    try:
        jobs = IndeedScraper(query=poste, city=ville, limit=limite).scrape()
        print(f"\n{len(jobs)} jobs found.\n")
        save_csv(jobs)
        selected = select_jobs(jobs)
        if selected:
            generate_cvs_cli(selected)
        else:
            print("No jobs selected. Bye!")
    except Exception as e:
        print(f"Error: {e}")


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
    from cv.generator import generate_cv

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

    # Collect from stdin
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
