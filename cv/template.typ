// ─── Variables injected by generator.py above this line ───────────────────────
// cv_name, cv_title, cv_email, cv_phone, cv_location, cv_github, cv_linkedin_url
// cv_summary, cv_skills, cv_experience, cv_education
// job_title, job_company, job_city, job_salary, job_contract, job_url

#set document(title: cv_name + " — " + job_title)
#set page(
  margin: (x: 1.8cm, y: 1.6cm),
  paper: "a4",
)
#set text(font: "Liberation Sans", size: 10pt, fill: rgb("#1a1a2e"))
#set par(leading: 0.65em)

// ─── Color palette ────────────────────────────────────────────────────────────
#let accent = rgb("#6c63ff")
#let muted  = rgb("#6b7280")
#let light  = rgb("#f3f4f6")
#let border = rgb("#e5e7eb")

// ─── Helpers ──────────────────────────────────────────────────────────────────
#let section(title) = [
  #v(0.6em)
  #text(weight: "bold", size: 10.5pt, fill: accent)[#upper(title)]
  #line(length: 100%, stroke: 0.5pt + accent)
  #v(0.25em)
]

#let tag(content) = box(
  fill: rgb("#ede9fe"),
  inset: (x: 6pt, y: 3pt),
  radius: 4pt,
  text(size: 8.5pt, fill: accent, weight: "medium")[#content]
)

#let icon_row(items) = {
  let filtered = items.filter(it => it.at(1) != "")
  if filtered.len() == 0 { return }
  filtered.map(it => {
    box[#text(fill: muted)[#it.at(0)] #it.at(1)]
  }).join(h(1.2em))
}

// ─── HEADER ───────────────────────────────────────────────────────────────────
#block(width: 100%)[
  #grid(
    columns: (1fr, auto),
    gutter: 1em,
    [
      #text(size: 22pt, weight: "bold", fill: rgb("#1a1a2e"))[#cv_name]
      #v(0.15em)
      #text(size: 12pt, fill: accent, weight: "medium")[#cv_title]
    ],
    [
      #set align(right)
      #set text(size: 8.5pt, fill: muted)
      #stack(spacing: 0.4em,
        if cv_email != "" { [✉ #cv_email] },
        if cv_phone != "" { [📞 #cv_phone] },
        if cv_location != "" { [📍 #cv_location] },
        if cv_github != "" { [⌥ #cv_github] },
        if cv_linkedin_url != "" { [in #cv_linkedin_url] },
      )
    ]
  )
]

// ─── TARGET JOB INFO (subtle banner) ─────────────────────────────────────────
#v(0.5em)
#block(
  width: 100%,
  fill: rgb("#f5f3ff"),
  stroke: (left: 3pt + accent),
  inset: (x: 10pt, y: 6pt),
  radius: (right: 4pt),
)[
  #text(size: 8pt, fill: muted)[Candidature pour :]
  #h(0.5em)
  #text(weight: "bold", size: 9pt)[#job_title]
  #h(0.5em)
  #text(fill: muted, size: 8.5pt)[— #job_company]
  #if job_city != "" [#h(0.5em)#text(fill: muted, size: 8pt)[📍 #job_city]]
  #if job_salary != "" [#h(0.5em)#text(fill: muted, size: 8pt)[💰 #job_salary]]
  #if job_contract != "" [#h(0.5em)#text(fill: muted, size: 8pt)[📄 #job_contract]]
]

// ─── SUMMARY ──────────────────────────────────────────────────────────────────
#if cv_summary != "" {
  section("Profil")
  par(justify: true)[#cv_summary]
}

// ─── SKILLS ───────────────────────────────────────────────────────────────────
#if cv_skills.len() > 0 {
  section("Compétences")
  wrap(cv_skills.map(s => tag(s)).join(h(0.4em) + v(0.3em)))
}

// ─── EXPERIENCE ───────────────────────────────────────────────────────────────
#if cv_experience.len() > 0 {
  section("Expérience")
  for exp in cv_experience {
    grid(
      columns: (auto, 1fr),
      gutter: 1em,
      [
        #text(size: 8.5pt, fill: muted, weight: "medium")[#exp.period]
      ],
      [
        #text(weight: "bold")[#exp.role]
        #h(0.4em)
        #text(fill: accent)[#exp.company]
        #if exp.location != "" [ #text(fill: muted, size: 8.5pt)[— #exp.location] ]
        #if exp.bullets.len() > 0 {
          v(0.2em)
          for b in exp.bullets {
            [• #b \ ]
          }
        }
      ]
    )
    v(0.5em)
  }
}

// ─── EDUCATION ────────────────────────────────────────────────────────────────
#if cv_education.len() > 0 {
  section("Formation")
  for edu in cv_education {
    grid(
      columns: (auto, 1fr),
      gutter: 1em,
      [#text(size: 8.5pt, fill: muted)[#edu.year]],
      [
        #text(weight: "bold")[#edu.degree]
        #if edu.school != "" [ — #text(fill: muted)[#edu.school] ]
      ]
    )
    v(0.3em)
  }
}

// ─── FOOTER ───────────────────────────────────────────────────────────────────
#v(1fr)
#line(length: 100%, stroke: 0.4pt + border)
#text(size: 7.5pt, fill: muted)[
  #cv_name — #cv_title
  #h(1fr)
  Généré via JobScrapper
]
