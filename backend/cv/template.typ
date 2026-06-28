#set text(size: 10pt)
#set document(
  title: "{{nom}} - {{poste_vise}} - {{entreprise}}",
  author: "{{nom}}",
)
#set page(margin: (top: 1.5cm, right: 1.5cm, bottom: 1.5cm, left: 1.5cm))

#text(size: 13pt, weight: "bold")[{{nom}}]

#text(size: 11pt)[{{poste_vise}} — {{entreprise}} | Python · Data Engineering · DevOps]

#par[
  {{ville}} |
  #link("mailto:{{email}}")[{{email}}] · {{telephone}} ·
  #link("{{linkedin}}")[LinkedIn] ·
  #link("{{github}}")[GitHub]
]

#v(0.25cm)

== Profil

Développeur Python avec une expérience en **data engineering**, **automatisation** et **scripting**.
Habitué à travailler sur des pipelines de données, des APIs REST et des outils DevOps.
Rigoureux, curieux et à l'aise dans des environnements techniques exigeants.

{{accroche}}

#v(0.25cm)

== Pourquoi ce poste

Poste visé : *{{poste_vise}}* chez **{{entreprise}}** ({{ville_job}})
#if "{{contrat}}" != "" [ · Contrat : {{contrat}} ]
#if "{{salaire}}" != "" [ · Rémunération : {{salaire}} ]

{{description}}

#v(0.25cm)

== Expérience professionnelle

{{experience}}

#v(0.25cm)

== Compétences techniques

#grid(
  columns: 2,
  gutter: 6mm,
  [
    - **Langages** : Python, SQL, Bash
    - **Data** : Pandas, PySpark, dbt, Airflow
    - **APIs** : FastAPI, REST, JSON
    - **Scraping** : Selenium, Playwright, BeautifulSoup
  ],
  [
    - **DevOps** : Docker, Git, CI/CD, Linux
    - **Cloud** : AWS / GCP (bases)
    - **BDD** : PostgreSQL, BigQuery, SQLite
    - **Outils** : VSCode, Jira, Notion, Confluence
  ]
)

{{competences}}

#v(0.25cm)

== Formation

{{formation}}

#v(0.25cm)

== Certifications & Formations complémentaires

- À compléter selon ton profil

#v(0.25cm)

== Centres d'intérêt

Développement open source · Automatisation · Data & IA · Jeux vidéo · Randonnée
