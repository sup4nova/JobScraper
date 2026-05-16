import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

CV_DIR = Path(__file__).parent.parent / "data" / "cv"
TEMPLATE_PATH = Path(__file__).parent / "template.typ"


def _escape_typst(s: str) -> str:
    """Escape special chars for Typst string literals."""
    return (
        str(s or "")
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def _skills_to_typst(skills_raw: str) -> str:
    lines = [l.strip() for l in skills_raw.strip().splitlines() if l.strip()]
    if not lines:
        return '()'
    items = ", ".join(f'"{_escape_typst(l)}"' for l in lines)
    return f"({items},)"


def _experience_to_typst(exp_raw: str) -> str:
    """Convert plain text experience blocks to Typst array of dicts."""
    blocks = []
    current: dict | None = None
    bullets: list[str] = []

    for line in exp_raw.strip().splitlines():
        line = line.strip()
        if not line:
            if current:
                current["bullets"] = bullets[:]
                blocks.append(current)
                current = None
                bullets = []
            continue
        if line.startswith("-"):
            bullets.append(line[1:].strip())
        elif "|" in line and current is None:
            parts = [p.strip() for p in line.split("|")]
            current = {
                "period": parts[0] if len(parts) > 0 else "",
                "role": parts[1] if len(parts) > 1 else "",
                "company": parts[2] if len(parts) > 2 else "",
                "location": parts[3] if len(parts) > 3 else "",
            }
            bullets = []
        else:
            bullets.append(line)

    if current:
        current["bullets"] = bullets
        blocks.append(current)

    if not blocks:
        return "()"

    items = []
    for b in blocks:
        blist = ", ".join(f'"{_escape_typst(x)}"' for x in b.get("bullets", []))
        items.append(
            f'(period: "{_escape_typst(b["period"])}", '
            f'role: "{_escape_typst(b["role"])}", '
            f'company: "{_escape_typst(b["company"])}", '
            f'location: "{_escape_typst(b["location"])}", '
            f'bullets: ({blist},))'
        )
    return "(" + ", ".join(items) + ",)"


def _education_to_typst(edu_raw: str) -> str:
    lines = [l.strip() for l in edu_raw.strip().splitlines() if l.strip()]
    if not lines:
        return "()"
    items = []
    for line in lines:
        parts = [p.strip() for p in line.split("|")]
        year = parts[0] if len(parts) > 0 else ""
        degree = parts[1] if len(parts) > 1 else ""
        school = parts[2] if len(parts) > 2 else ""
        items.append(
            f'(year: "{_escape_typst(year)}", '
            f'degree: "{_escape_typst(degree)}", '
            f'school: "{_escape_typst(school)}")'
        )
    return "(" + ", ".join(items) + ",)"


async def generate_cv(job: dict, user: dict) -> Path | None:
    CV_DIR.mkdir(parents=True, exist_ok=True)

    safe_company = "".join(c if c.isalnum() else "_" for c in (job.get("company") or "job"))
    safe_title = "".join(c if c.isalnum() else "_" for c in (job.get("title") or "cv"))[:30]
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = CV_DIR / f"cv_{safe_company}_{safe_title}_{ts}.pdf"

    variables = f"""
#let cv_name = "{_escape_typst(user['name'])}"
#let cv_title = "{_escape_typst(user['title'])}"
#let cv_email = "{_escape_typst(user['email'])}"
#let cv_phone = "{_escape_typst(user.get('phone', ''))}"
#let cv_location = "{_escape_typst(user.get('location', ''))}"
#let cv_github = "{_escape_typst(user.get('github', ''))}"
#let cv_linkedin_url = "{_escape_typst(user.get('linkedin_url', ''))}"
#let cv_summary = "{_escape_typst(user.get('summary', ''))}"
#let cv_skills = {_skills_to_typst(user.get('skills', ''))}
#let cv_experience = {_experience_to_typst(user.get('experience', ''))}
#let cv_education = {_education_to_typst(user.get('education_text', ''))}

#let job_title = "{_escape_typst(job.get('title', ''))}"
#let job_company = "{_escape_typst(job.get('company', ''))}"
#let job_city = "{_escape_typst(job.get('city', ''))}"
#let job_salary = "{_escape_typst(job.get('salary', ''))}"
#let job_contract = "{_escape_typst(job.get('contract_type', ''))}"
#let job_education = "{_escape_typst(job.get('education', ''))}"
#let job_url = "{_escape_typst(job.get('url', ''))}"
"""

    template_content = TEMPLATE_PATH.read_text()
    full_source = variables + "\n" + template_content

    with tempfile.NamedTemporaryFile(suffix=".typ", mode="w", delete=False) as f:
        f.write(full_source)
        tmp_path = Path(f.name)

    try:
        result = subprocess.run(
            ["typst", "compile", str(tmp_path), str(output_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print("Typst error:", result.stderr)
            return None
        return output_path
    except FileNotFoundError:
        print("Typst not found. Install: https://github.com/typst/typst/releases")
        return None
    except subprocess.TimeoutExpired:
        return None
    finally:
        tmp_path.unlink(missing_ok=True)
