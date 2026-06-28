"""
JobScraper CLI — scrape Indeed / LinkedIn / WTTJ and generate tailored CVs.
Usage: python main.py
"""
import csv
import json
import os
import asyncio

from scrapers.indeed import IndeedScraper
from scrapers.linkedin import LinkedInScraper
from scrapers.WIP.wttj import WTTJScraper


def main():
    print("\n" + "=" * 50)
    print("       JOB SCRAPER + CV GENERATOR")
    print("=" * 50 + "\n")

    poste = input("Job title (e.g. Python developer, data analyst): ").strip()
    ville = input("City (leave blank for all of France): ").strip() or "France"
    limite_raw = input("Max results per site [20]: ").strip()
    limite = int(limite_raw) if limite_raw.isdigit() else 20
    sites = pick_sites()

    print(f"\nScraping {', '.join(sites)}...\n")
    offres = []

    # Indeed uses Selenium (synchronous)
    if "indeed" in sites:
        print("  → Indeed...")
        try:
            jobs = IndeedScraper(query=poste, city=ville, limit=limite).scrape()
            offres.extend(jobs)
            print(f"     {len(jobs)} jobs found")
        except Exception as e:
            print(f"     Error: {e}")

    # LinkedIn and WTTJ use Playwright (async)
    async def scrape_async():
        results = []
        if "linkedin" in sites:
            print("  → LinkedIn...")
            try:
                jobs = await LinkedInScraper(query=poste, city=ville, limit=limite).scrape()
                results.extend(jobs)
                print(f"     {len(jobs)} jobs found")
            except Exception as e:
                print(f"     Error: {e}")
        if "wttj" in sites:
            print("  → Welcome to the Jungle...")
            try:
                jobs = await WTTJScraper(query=poste, city=ville, limit=limite).scrape()
                results.extend(jobs)
                print(f"     {len(jobs)} jobs found")
            except Exception as e:
                print(f"     Error: {e}")
        return results

    if "linkedin" in sites or "wttj" in sites:
        offres.extend(asyncio.run(scrape_async()))

    if not offres:
        print("\nNo jobs found. Check your query or connection.")
        return

    print(f"\n{len(offres)} jobs found in total.\n")
    save_csv(offres)

    selected = select_jobs(offres)
    if not selected:
        print("No jobs selected. Bye!")
        return

    generate_cvs(selected)


# ── CSV ───────────────────────────────────────────────────────────────────────

def save_csv(offres: list[dict]):
    csv_file = "scraped_jobs.csv"
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
            first_line = offre["description"].splitlines()[0]
            print(f"      📝 {first_line[:120]}")
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

def generate_cvs(offres: list[dict]):
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
        "linkedin_url":   input("  LinkedIn (opt.) : ").strip(),
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


# ── Site selection ────────────────────────────────────────────────────────────

def pick_sites() -> list[str]:
    print("Sites to scrape:")
    print("  [1] Indeed")
    print("  [2] LinkedIn")
    print("  [3] Welcome to the Jungle")
    print("  [4] All")
    choice = input("Choice [4]: ").strip() or "4"
    mapping = {
        "1": ["indeed"],
        "2": ["linkedin"],
        "3": ["wttj"],
        "4": ["indeed", "linkedin", "wttj"],
    }
    return mapping.get(choice, ["indeed", "linkedin", "wttj"])


if __name__ == "__main__":
    main()
