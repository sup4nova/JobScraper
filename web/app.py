import asyncio
import subprocess
from pathlib import Path
from fastapi import FastAPI, Request, Form, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db.models import init_db, get_jobs, get_job, update_job_status, delete_job, log_cv_generation
from scrapers.indeed import IndeedScraper
from scrapers.linkedin import LinkedInScraper
from scrapers.wttj import WTTJScraper
from db.models import upsert_job
from cv.generator import generate_cv

app = FastAPI(title="JobScrapper")

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

SCRAPERS = {
    "indeed": IndeedScraper,
    "linkedin": LinkedInScraper,
    "wttj": WTTJScraper,
}

scrape_status: dict = {"running": False, "message": "", "count": 0}


@app.on_event("startup")
async def startup():
    await init_db()


# ── Home ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ── Scraping ─────────────────────────────────────────────────────────────────

@app.post("/scrape")
async def start_scrape(
    background_tasks: BackgroundTasks,
    query: str = Form(...),
    city: str = Form(...),
    limit: int = Form(20),
    sources: list[str] = Form(...),
):
    if scrape_status["running"]:
        return RedirectResponse("/?error=already_running", status_code=303)
    background_tasks.add_task(_run_scrape, query, city, limit, sources)
    return RedirectResponse("/jobs?status=new", status_code=303)


async def _run_scrape(query: str, city: str, limit: int, sources: list[str]):
    scrape_status["running"] = True
    scrape_status["count"] = 0
    scrape_status["message"] = "Scraping en cours..."

    for source in sources:
        cls = SCRAPERS.get(source)
        if not cls:
            continue
        scrape_status["message"] = f"Scraping {source}..."
        try:
            scraper = cls(query=query, city=city, limit=limit)
            jobs = await scraper.scrape()
            for job in jobs:
                job_id = await upsert_job(job)
                if job_id:
                    scrape_status["count"] += 1
        except Exception as e:
            scrape_status["message"] = f"Erreur {source}: {e}"

    scrape_status["running"] = False
    scrape_status["message"] = f"Terminé — {scrape_status['count']} nouvelles offres"


@app.get("/scrape/status")
async def scrape_progress():
    return JSONResponse(scrape_status)


# ── Jobs list ─────────────────────────────────────────────────────────────────

@app.get("/jobs", response_class=HTMLResponse)
async def jobs_list(
    request: Request,
    status: str | None = Query(None),
    search: str | None = Query(None),
    source: str | None = Query(None),
):
    jobs = await get_jobs(status=status, search=search, source=source)
    counts = {
        "all": len(await get_jobs()),
        "new": len(await get_jobs(status="new")),
        "liked": len(await get_jobs(status="liked")),
        "ignored": len(await get_jobs(status="ignored")),
    }
    return templates.TemplateResponse("jobs.html", {
        "request": request,
        "jobs": jobs,
        "counts": counts,
        "current_status": status,
        "current_search": search or "",
        "current_source": source or "",
        "scrape_status": scrape_status,
    })


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: int):
    job = await get_job(job_id)
    if not job:
        return RedirectResponse("/jobs")
    return templates.TemplateResponse("job_detail.html", {"request": request, "job": job})


# ── Actions ───────────────────────────────────────────────────────────────────

@app.post("/jobs/{job_id}/status")
async def set_status(job_id: int, status: str = Form(...), redirect_to: str = Form("/jobs")):
    await update_job_status(job_id, status)
    return RedirectResponse(redirect_to, status_code=303)


@app.post("/jobs/{job_id}/delete")
async def remove_job(job_id: int, redirect_to: str = Form("/jobs")):
    await delete_job(job_id)
    return RedirectResponse(redirect_to, status_code=303)


# ── CV generation ─────────────────────────────────────────────────────────────

@app.get("/jobs/{job_id}/cv", response_class=HTMLResponse)
async def cv_form(request: Request, job_id: int):
    job = await get_job(job_id)
    if not job:
        return RedirectResponse("/jobs")
    return templates.TemplateResponse("cv_form.html", {"request": request, "job": job})


@app.post("/jobs/{job_id}/cv/generate")
async def cv_generate(
    request: Request,
    job_id: int,
    cv_name: str = Form(...),
    cv_title: str = Form(...),
    cv_email: str = Form(...),
    cv_phone: str = Form(...),
    cv_location: str = Form(...),
    cv_github: str = Form(""),
    cv_linkedin: str = Form(""),
    cv_summary: str = Form(""),
    cv_skills: str = Form(""),
    cv_experience: str = Form(""),
    cv_education: str = Form(""),
):
    job = await get_job(job_id)
    if not job:
        return RedirectResponse("/jobs")

    user_info = {
        "name": cv_name,
        "title": cv_title,
        "email": cv_email,
        "phone": cv_phone,
        "location": cv_location,
        "github": cv_github,
        "linkedin_url": cv_linkedin,
        "summary": cv_summary,
        "skills": cv_skills,
        "experience": cv_experience,
        "education_text": cv_education,
    }

    output_path = await generate_cv(job, user_info)
    if not output_path:
        job = await get_job(job_id)
        return templates.TemplateResponse("cv_form.html", {
            "request": request,
            "job": job,
            "error": "Erreur lors de la génération du CV. Typst est-il installé ?",
        })

    await log_cv_generation(job_id, str(output_path))
    return FileResponse(
        path=output_path,
        filename=output_path.name,
        media_type="application/pdf",
    )
