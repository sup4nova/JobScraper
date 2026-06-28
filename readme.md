# JobScraper

Scrape Indeed, LinkedIn et Welcome to the Jungle, swipe les offres qui t'intéressent, et génère des lettres de motivation personnalisées via une IA locale.

## Stack

**Backend** — Python, FastAPI, Selenium + undetected-chromedriver, BeautifulSoup, Playwright, Ollama  
**Frontend** — Vue.js 3, CSS vanilla (pas de build)

## Architecture

```
JobScrapper/
├── main.py                  ← CLI : scrape + sélection + génération CV
├── chat.py                  ← CLI : chatbot JobBot
├── backend/
│   ├── main.py              ← API FastAPI
│   ├── models.py            ← Modèle de données offre
│   ├── requirements.txt
│   ├── scrapers/
│   │   ├── indeed.py        ← Scraper Selenium (anti-bot)
│   │   ├── linkedin.py      ← Scraper Selenium + BeautifulSoup
│   │   └── WIP/
│   │       └── wttj.py      ← Scraper Playwright + API Algolia
│   ├── chat/
│   │   ├── agent.py         ← Routeur d'intents + boucle conversation
│   │   ├── tools.py         ← Lettre de motivation, gap analysis, traduction
│   │   └── ollama_client.py ← Client HTTP pour Ollama local
│   └── cv/
│       ├── generator.py     ← Génération CV via Typst
│       └── template.typ     ← Template CV
└── frontend/
    ├── index.html           ← SPA Vue 3 (UI swipe mobile-first)
    ├── public/
    │   ├── app.js
    │   └── data.js          ← Données de démo
    └── styles.css
```

## Installation

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac / Linux
pip install -r requirements.txt
```

Lancer l'API :
```bash
uvicorn main:app --reload
```

### Frontend

Ouvrir `frontend/index.html` directement dans un navigateur — aucun build requis.  
La démo tourne avec des données simulées, sans backend.

### Chatbot IA (local)

Nécessite [Ollama](https://ollama.ai) en local :

```bash
ollama serve
ollama pull qwen2.5:7b
python chat.py
```

Changer de modèle :
```bash
python chat.py --model mistral
```

### Génération de CV

Nécessite [Typst](https://typst.app) :
```bash
winget install Typst.Typst
```

## Fonctionnalités

| Feature | État |
|---------|------|
| Scraper Indeed | ✅ |
| Scraper LinkedIn | ✅ |
| Scraper WTTJ (Algolia + Playwright) | ✅ WIP |
| UI swipe (démo) | ✅ |
| Génération lettre de motivation (Ollama) | ✅ local |
| Analyse gap profil / offre | ✅ local |
| Génération CV (Typst) | ✅ |
| Bot Discord | 🚧 bientôt |
| Déploiement chatbot IA | 🚧 bientôt |

## Notes

- Indeed et LinkedIn bloquent activement les bots — rotation de User-Agent et délais aléatoires déjà intégrés.
- WTTJ utilise une API Algolia publique + Playwright pour les pages d'offres.
- L'assistant IA tourne 100% en local via Ollama (aucune clé API requise).
- Le projet tourne localement ; le déploiement en production est en cours.
