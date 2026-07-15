"""
Shared scraping orchestration, reused by both the FastAPI backend (main.py)
and the standalone Discord bot (bot.py).
"""
from multiprocessing import Pool

from scrapers.indeed import IndeedScraper
from scrapers.remote_ok import RemoteOKScraper, tags_for
from scrapers.linkedin import LinkedInScraper
from scrapers.wellfound import WellfoundScraper


def _run_scrape_in_process(poste: str, ville: str, limite: int) -> list[dict]:
    """Run all scrapers and return the merged results. Chrome-based ones run in a subprocess."""
    indeed_jobs = []
    linkedin_jobs = []
    wellfound_jobs = []
    try:
        linkedin_jobs = LinkedInScraper(query=poste, city=ville, limit=limite).scrape()
        print(f">>> {len(linkedin_jobs)} LinkedIn jobs")
    except Exception as e:
        print(f"LinkedIn error: {type(e).__name__}: {e}")
    try:
        with Pool(1) as p:
            wellfound_jobs = p.apply(WellfoundScraper(query=poste, city=ville, limit=limite).scrape)
        print(f">>> {len(wellfound_jobs)} Wellfound jobs")
    except Exception as e:
        print(f"Wellfound error: {type(e).__name__}: {e}")
    try:
        with Pool(1) as p:
            indeed_jobs = p.apply(IndeedScraper(query=poste, city=ville, limit=limite).scrape)
        print(f">>> {len(indeed_jobs)} Indeed jobs")
    except Exception as e:
        print(f"Indeed error: {type(e).__name__}: {e}")

    remoteok_jobs = []
    try:
        remoteok_jobs = RemoteOKScraper(
            query=poste, city=ville, limit=limite, tags=tags_for(poste)
        ).scrape()
        print(f">>> {len(remoteok_jobs)} Remote OK jobs")
    except Exception as e:
        print(f"Remote OK error: {type(e).__name__}: {e}")

    _print_recap({
        "Indeed":    indeed_jobs,
        "LinkedIn":  linkedin_jobs,
        "Remote OK": remoteok_jobs,
        "Wellfound": wellfound_jobs,
    })

    return indeed_jobs + linkedin_jobs + remoteok_jobs + wellfound_jobs


def _print_recap(resultats: dict[str, list]):
    """Print a scraping summary per source."""
    print("\n" + "═" * 50)
    print("  SCRAPING SUMMARY")
    print("═" * 50)
    total = 0
    for source, jobs in resultats.items():
        n = len(jobs)
        total += n
        status = "✅" if n > 0 else "⚠️ "
        print(f"  {status} {source:<12} : {n:>3} job(s)")
    print("─" * 50)
    print(f"  📦 TOTAL       : {total:>3} job(s)")
    print("═" * 50 + "\n")

    if total == 0:
        print("ALERT: scrape cycle returned 0 jobs from all sources")
