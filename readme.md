# 🔍 JobScraper + CV Generator

Scrape Indeed / LinkedIn / Welcome to the Jungle, sélectionne les offres qui te plaisent, et génère automatiquement un CV adapté à chaque annonce.

---

## 🗂 Structure du projet

```
job-scraper/
├── main.py                  ← point d'entrée, lance tout
├── models.py                ← structure d'une offre
├── requirements.txt
├── scrapers/
│   ├── orchestrator.py      ← lance les scrapers en parallèle
│   ├── indeed.py            ← scraper Indeed
│   ├── linkedin.py          ← scraper LinkedIn
│   └── wttj.py              ← scraper Welcome to the Jungle
├── ui/
│   └── selector.py          ← interface CLI de sélection
├── cv/
│   └── generator.py         ← génération CV (Typst / Markdown / TXT)
├── data/                    ← offres sauvegardées en JSON
└── output/                  ← CVs générés
```

---

## ⚙️ Setup (pour les nuls)

### 1. Cloner le repo

```bash
git clone https://github.com/ton-user/job-scraper.git
cd job-scraper
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
```

### 3. Activer l'environnement virtuel

**Windows (CMD) :**
```bash
venv\Scripts\activate
```

**Windows (PowerShell) :**
```bash
venv\Scripts\Activate.ps1
```

**Mac / Linux :**
```bash
source venv/bin/activate
```

> Tu dois voir `(venv)` apparaître au début de ta ligne de commande.

### 4. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## 🚀 Lancer le script

```bash
python main.py
```

Le script va te demander :
1. Le **poste** recherché (ex: `développeur python`)
2. La **ville** (ex: `Lyon` — laisser vide = toute la France)
3. Le **nombre max d'offres** à scraper par site
4. Les **sites** à utiliser (Indeed / LinkedIn / WTTJ / Tous)

Ensuite tu sélectionnes les offres qui t'intéressent, et les CVs sont générés dans `/output/`.

---

## 📄 Configuration du CV

Ouvre `cv/generator.py` et remplis le dictionnaire `MON_PROFIL` avec tes infos :

```python
MON_PROFIL = {
    "nom": "Prénom NOM",
    "email": "ton@email.com",
    "tel": "+33 6 XX XX XX XX",
    "competences": ["Python", "SQL", "Docker"],
    "experiences": [...],
    "formations": [...],
}
```

### Format de sortie

Change la variable `MODE` dans `cv/generator.py` :

| Mode | Fichier généré | Utilisation |
|------|---------------|-------------|
| `"typst"` | `.typ` + `.pdf` | Meilleur rendu — nécessite [Typst](https://typst.app) |
| `"md"` | `.md` | Ouvrir avec VS Code, Obsidian, etc. |
| `"txt"` | `.txt` | Brut, universel |

Pour Typst : installer depuis [typst.app](https://typst.app/docs/install) ou `winget install Typst.Typst`

---

## ⚠️ Notes importantes

- **Indeed et LinkedIn bloquent les bots** — si ça ne scrape rien, c'est normal. Pistes : changer le User-Agent, ajouter des délais, utiliser Playwright.
- **WTTJ** est le plus permissif des trois (API JSON publique).
- Les offres scrapées sont sauvegardées dans `/data/` en JSON — tu peux les relire sans re-scraper.
- Les sélecteurs CSS **peuvent casser** si les sites changent leur HTML — c'est la vie du scraping.

---

## 🔧 Dépendances

| Package | Usage |
|---------|-------|
| `requests` | Requêtes HTTP |
| `beautifulsoup4` | Parsing HTML |
| `lxml` | Parser HTML rapide |

> Pas de Playwright par défaut pour rester léger — à ajouter si les sites bloquent `requests`.