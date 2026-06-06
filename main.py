"""
JobScraper CLI — Scrape Indeed / LinkedIn / WTTJ et génère des CVs adaptés.
Usage: python main.py
"""
import csv
import json
import os
import asyncio

from backend.scrapers.indeed import IndeedScraper
from backend.scrapers.linkedin import LinkedInScraper
from backend.scrapers.WIP.wttj import WTTJScraper



def main():
    print("\n" + "=" * 50)
    print("       🔍 JOB SCRAPER + CV GENERATOR")
    print("=" * 50 + "\n")

    poste = input("Poste recherché (ex: développeur python, data analyst) : ").strip()
    ville = input("Ville (ex: Lyon, Paris — laisser vide = toute la France) : ").strip() or "France"
    limite_raw = input("Nombre max d'offres à scraper par site [20] : ").strip()
    limite = int(limite_raw) if limite_raw.isdigit() else 20
    sites = choisir_sites()

    print(f"\n⏳ Scraping en cours sur {', '.join(sites)}...\n")
    offres = []

    # Indeed — Selenium (synchrone)
    if "indeed" in sites:
        print("  → Indeed...")
        try:
            jobs = IndeedScraper(query=poste, city=ville, limit=limite).scrape()
            offres.extend(jobs)
            print(f"     {len(jobs)} offres trouvées")
        except Exception as e:
            print(f"     ❌ Erreur Indeed : {e}")

    # LinkedIn & WTTJ — Playwright (asynchrone)
    async def scrape_async():
        results = []
        if "linkedin" in sites:
            print("  → LinkedIn...")
            try:
                jobs = await LinkedInScraper(query=poste, city=ville, limit=limite).scrape()
                results.extend(jobs)
                print(f"     {len(jobs)} offres trouvées")
            except Exception as e:
                print(f"     ❌ Erreur LinkedIn : {e}")
        if "wttj" in sites:
            print("  → Welcome to the Jungle...")
            try:
                jobs = await WTTJScraper(query=poste, city=ville, limit=limite).scrape()
                results.extend(jobs)
                print(f"     {len(jobs)} offres trouvées")
            except Exception as e:
                print(f"     ❌ Erreur WTTJ : {e}")
        return results

    if "linkedin" in sites or "wttj" in sites:
        offres.extend(asyncio.run(scrape_async()))

    if not offres:
        print("\n❌ Aucune offre trouvée. Vérifie les paramètres ou ta connexion.")
        return

    print(f"\n✅ {len(offres)} offres récupérées au total.\n")
    save_csv(offres)

    offres_selectionnees = select_jobs(offres)
    if not offres_selectionnees:
        print("Aucune offre sélectionnée. À bientôt !")
        return

    generer_cvs(offres_selectionnees)


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
                row["easily_apply"] = "Oui" if row["easily_apply"] else "Non"
            writer.writerow(row)
    print(f"💾 Offres sauvegardées dans {csv_file}\n")


# ── Sélecteur CLI ─────────────────────────────────────────────────────────────

def select_jobs(offres: list[dict]) -> list[dict]:
    selected = []
    print("─" * 55)
    print(f"Sélection des offres ({len(offres)} au total)")
    print("  [o] garder   [n] ignorer   [q] terminer la sélection")
    print("─" * 55 + "\n")

    for i, offre in enumerate(offres, 1):
        easily = " ⚡ Candidature simplifiée" if offre.get("easily_apply") else ""
        print(f"[{i}/{len(offres)}] {offre.get('title', '?')} — {offre.get('company', '?')}")
        print(f"      📍 {offre.get('city', '?')}  💰 {offre.get('salary') or 'salaire non précisé'}{easily}")
        print(f"      🔗 {offre.get('url', '')[:80]}")
        if offre.get("description"):
            first_line = offre["description"].splitlines()[0]
            print(f"      📝 {first_line[:120]}")
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
    from backend.cv.generator import generate_cv

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
    # Si le profil existe déjà, on le charge directement
    if os.path.exists(PROFIL_FILE):
        with open(PROFIL_FILE, encoding="utf-8") as f:
            profil = json.load(f)
        print(f"✅ Profil chargé depuis {PROFIL_FILE}")

        modifier = input("   Modifier le profil ? [o/N] : ").strip().lower()
        if modifier != "o":
            return profil

    # Saisie du profil
    print("\nTes informations pour le CV (Entrée = passer) :\n")
    profil = {
        "name":           input("  Nom complet          : ").strip(),
        "title":          input("  Titre / poste visé   : ").strip(),
        "email":          input("  Email                : ").strip(),
        "phone":          input("  Téléphone            : ").strip(),
        "location":       input("  Ville                : ").strip(),
        "github":         input("  GitHub (optionnel)   : ").strip(),
        "linkedin_url":   input("  LinkedIn (optionnel) : ").strip(),
        "summary":        input("  Accroche (1 ligne)   : ").strip(),
        "skills":         input("  Compétences (séparées par virgule) : ").strip().replace(",", "\n"),
        "experience":     "",
        "education_text": "",
    }

    # Sauvegarde pour les prochains runs
    with open(PROFIL_FILE, "w", encoding="utf-8") as f:
        json.dump(profil, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Profil sauvegardé dans {PROFIL_FILE} (rechargé automatiquement au prochain lancement)\n")

    return profil


# ── Menu sites ────────────────────────────────────────────────────────────────

def choisir_sites() -> list[str]:
    print("Sites à scraper :")
    print("  [1] Indeed")
    print("  [2] LinkedIn")
    print("  [3] Welcome to the Jungle")
    print("  [4] Tous")
    choix = input("Choix [4] : ").strip() or "4"
    mapping = {
        "1": ["indeed"],
        "2": ["linkedin"],
        "3": ["wttj"],
        "4": ["indeed", "linkedin", "wttj"],
    }
    return mapping.get(choix, ["indeed", "linkedin", "wttj"])


if __name__ == "__main__":
    main()