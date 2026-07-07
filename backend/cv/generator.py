"""
CV Generator — remplace les variables dans le template Typst
et compile en PDF via la CLI Typst.
"""
import asyncio
import json
import re
import subprocess
from pathlib import Path

TEMPLATE = Path(__file__).parent / "template.typ"
OUTPUT   = Path(__file__).parent / "output"

async def generate_cv(job: dict, user: dict) -> str | None:
    OUTPUT.mkdir(exist_ok=True)

    # Nom du fichier de sortie
    company_slug = re.sub(r"[^\w]", "_", job.get("company", "Entreprise"))
    title_slug   = re.sub(r"[^\w]", "_", job.get("title",   "Poste"))[:30]
    out_path     = OUTPUT / f"{company_slug}_{title_slug}.pdf"
    typ_path     = OUTPUT / f"{company_slug}_{title_slug}.typ"

    # Lire le template et remplacer les variables
    template = TEMPLATE.read_text(encoding="utf-8")
    variables = {
        "{{nom}}":          user.get("name", ""),
        "{{titre}}":        job.get("title", ""),
        "{{email}}":        user.get("email", ""),
        "{{telephone}}":    user.get("phone", ""),
        "{{ville}}":        user.get("location", ""),
        "{{github}}":       user.get("github", ""),
        "{{linkedin}}":     user.get("linkedin_url", ""),
        "{{accroche}}":     user.get("summary", ""),
        "{{competences}}":  user.get("skills", ""),
        "{{experience}}":   user.get("experience", ""),
        "{{formation}}":    user.get("education_text", ""),
        "{{poste_vise}}":   job.get("title", ""),
        "{{entreprise}}":   job.get("company", ""),
        "{{ville_job}}":    job.get("city", ""),
        "{{contrat}}":      job.get("contract_type", ""),
        "{{salaire}}":      job.get("salary", ""),
        "{{description}}":  job.get("description", "")[:500],
    }
    for key, val in variables.items():
        template = template.replace(key, str(val))
    print(f"Variables utilisées : {variables}")
    # Écrire le .typ compilé
    typ_path.write_text(template, encoding="utf-8")

    # Compiler via CLI Typst
    try:
        result = subprocess.run(
            ["typst", "compile", str(typ_path), str(out_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"     Typst erreur : {result.stderr}")
            return None
        return str(out_path)
    except FileNotFoundError:
        print("     ❌ Typst non trouvé — installe-le : https://github.com/typst/typst")
        return None
    except subprocess.TimeoutExpired:
        print("     ❌ Typst timeout")
        return None
    
if __name__ == "__main__":
    job = {
        "title": "Développeur Python",
        "company": "TechCorp",
        "city": "Paris",
        "contract_type": "CDI",
        "salary": "50k-60k€",
        "description": "Nous recherchons un développeur Python expérimenté...",
    }
    user = {
        "name": "Alice Dupont",
        "email": "alice@example.com",
        "phone": "0600000000",
        "location": "Paris",
        "github": "",
        "linkedin_url": "",
        "summary": "Développeuse Python passionnée.",
        "skills": "Python\nFastAPI\nSQL",
        "experience": "",
        "education_text": "",
    }
    path = asyncio.run(generate_cv(job, user))
    print("CV généré :", path if path else "ÉCHEC")