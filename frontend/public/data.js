/* Mock job data matching the scraper output schema:
   { source, title, company, city, salary, contract_type, education,
     easily_apply, description, url }
*/

window.MOCK_JOBS = [
  {
    source: "linkedin",
    title: "Développeur Python Backend",
    company: "Doctolib",
    city: "Paris (75)",
    salary: "55–70 k€ / an",
    contract_type: "CDI · Hybride",
    education: "Bac+5",
    easily_apply: true,
    description: "Rejoins l'équipe Plateforme pour bâtir des APIs FastAPI qui scalent à des millions de RDV. Stack moderne : Python 3.12, PostgreSQL, Redis, Kafka, AWS. Tu travailleras en pair-programming, déploiement continu, code review exigeant mais bienveillant.\n\n• 4+ ans en Python (FastAPI/Django)\n• Expérience BDD relationnelles\n• Anglais pro (équipe européenne)\n• Bonus : Kubernetes, observabilité",
    url: "https://www.linkedin.com/jobs/view/3891234567",
    yourScore: 92,
  },
  {
    source: "indeed",
    title: "Data Engineer Senior",
    company: "Back Market",
    city: "Bordeaux (33)",
    salary: "60–80 k€",
    contract_type: "CDI · Full remote",
    education: "Bac+5",
    easily_apply: false,
    description: "Build the data backbone of the circular economy. Stack : Airflow, dbt, Snowflake, Python, Terraform. Tu vas designer des pipelines critiques pour 15M de clients.\n\n• 5+ ans en data engineering\n• Maîtrise dbt + warehouse cloud\n• Mindset produit\n• English fluent",
    url: "https://fr.indeed.com/viewjob?jk=abc123",
    yourScore: 78,
  },
  {
    source: "linkedin",
    title: "Lead Backend — Python / Go",
    company: "Qonto",
    city: "Lyon (69)",
    salary: "75–95 k€ + BSPCE",
    contract_type: "CDI · Hybride 2j",
    education: "Bac+5",
    easily_apply: true,
    description: "Tu encadres une squad de 5 ingénieurs qui construit les briques de paiement européennes. Plateforme distribuée, exigence forte sur la fiabilité, culture craft.\n\n• 7+ ans backend dont 2 en lead\n• Solide en Python ou Go\n• Tu sais designer un système distribué\n• Tu aimes mentorer",
    url: "https://www.linkedin.com/jobs/view/3891234568",
    yourScore: 85,
  },
  {
    source: "indeed",
    title: "Développeur Fullstack Python / Vue",
    company: "Lifen",
    city: "Paris (75)",
    salary: "50–65 k€",
    contract_type: "CDI · Hybride",
    education: "Bac+3 minimum",
    easily_apply: true,
    description: "Healthcare tech — on connecte 200k pros de santé. Stack Python + Vue 3 + Postgres. Tu touches au produit, du design system aux jobs async.\n\n• 3+ ans fullstack\n• Vue 3 (composition API)\n• Python + un framework web\n• Sensibilité produit & UX",
    url: "https://fr.indeed.com/viewjob?jk=def456",
    yourScore: 88,
  },
  {
    source: "linkedin",
    title: "Site Reliability Engineer",
    company: "Algolia",
    city: "Paris (75) · Remote",
    salary: "70–90 k€",
    contract_type: "CDI · Full remote possible",
    education: "Bac+5",
    easily_apply: false,
    description: "Garde l'infra qui sert 1.7 trillion de requêtes / an. Kubernetes, Terraform, observabilité, capacity planning. Astreintes bien organisées, équipe globale.\n\n• 4+ ans en SRE/DevOps\n• K8s en production\n• Programmation (Go ou Python)\n• Anglais courant",
    url: "https://www.linkedin.com/jobs/view/3891234569",
    yourScore: 65,
  },
  {
    source: "indeed",
    title: "Développeur Python — Junior accepté",
    company: "Shine",
    city: "Nantes (44)",
    salary: "38–48 k€",
    contract_type: "CDI · Hybride",
    education: "Bac+3",
    easily_apply: true,
    description: "Néobanque pour pros — équipe à taille humaine, accompagnement personnalisé. Stack Django, Postgres, AWS. Tu apprends, tu codes, tu ships.\n\n• 1–3 ans en Python\n• Tu veux progresser vite\n• Tu aimes la qualité de code\n• Bonus : connaissance fintech",
    url: "https://fr.indeed.com/viewjob?jk=ghi789",
    yourScore: 81,
  },
  {
    source: "linkedin",
    title: "Tech Lead Data Platform",
    company: "BlaBlaCar",
    city: "Paris (75)",
    salary: "85–110 k€ + equity",
    contract_type: "CDI · Hybride 3j",
    education: "Bac+5 école d'ingé",
    easily_apply: false,
    description: "Construis la plateforme data self-service pour 300+ employés. Tu auras de l'impact sur 100M+ d'utilisateurs.\n\n• 8+ ans dont 3 en lead\n• Python + Scala/Java\n• Spark, Airflow, Kafka\n• Anglais fluent",
    url: "https://www.linkedin.com/jobs/view/3891234570",
    yourScore: 72,
  },
  {
    source: "indeed",
    title: "Développeur Python Backend",
    company: "Welcome to the Jungle",
    city: "Paris (75)",
    salary: "55–72 k€",
    contract_type: "CDI · Hybride 2j",
    education: "Bac+5",
    easily_apply: true,
    description: "Tu rejoins une squad qui construit les outils de recrutement utilisés par 7000+ entreprises. FastAPI, Postgres, Redis, ElasticSearch.\n\n• 4+ ans Python backend\n• Bonnes pratiques (tests, CI/CD)\n• Curieux produit\n• Anglais OK",
    url: "https://fr.indeed.com/viewjob?jk=jkl012",
    yourScore: 90,
  },
  {
    source: "linkedin",
    title: "Software Engineer — Search",
    company: "Mirakl",
    city: "Paris (75)",
    salary: "60–78 k€",
    contract_type: "CDI · Hybride",
    education: "Bac+5",
    easily_apply: false,
    description: "Travaille sur le moteur de recherche e-commerce derrière Carrefour, Decathlon, Best Buy. ElasticSearch, Java, Python. Très technique.\n\n• 4+ ans dev backend\n• Recherche/IR un plus\n• Solide en algorithmique\n• Anglais courant",
    url: "https://www.linkedin.com/jobs/view/3891234571",
    yourScore: 68,
  },
  {
    source: "indeed",
    title: "Développeur Python Senior",
    company: "Hello Watt",
    city: "Lille (59)",
    salary: "55–70 k€",
    contract_type: "CDI · Full remote",
    education: "Bac+5",
    easily_apply: true,
    description: "Transition énergétique — on aide les Français à consommer mieux. Stack Django, Vue, Postgres. Équipe de 25 devs, culture craft.\n\n• 5+ ans Python\n• Django ou FastAPI\n• Tu aimes la mission impact\n• Autonome",
    url: "https://fr.indeed.com/viewjob?jk=mno345",
    yourScore: 86,
  },
  {
    source: "linkedin",
    title: "Engineering Manager Backend",
    company: "Spendesk",
    city: "Paris (75)",
    salary: "90–115 k€",
    contract_type: "CDI · Hybride",
    education: "Bac+5",
    easily_apply: false,
    description: "Manage une équipe de 6 backend engineers. Tu fais 30% de code, 70% de management, growth & process.\n\n• 8+ ans dev dont 2+ en management\n• Backend (Node/Python/Go)\n• Anglais fluent\n• Tu sais hire et grow ton équipe",
    url: "https://www.linkedin.com/jobs/view/3891234572",
    yourScore: 58,
  },
  {
    source: "indeed",
    title: "Développeur Python / FastAPI",
    company: "Sunday",
    city: "Lyon (69)",
    salary: "48–62 k€",
    contract_type: "CDI · Hybride",
    education: "Bac+3 minimum",
    easily_apply: true,
    description: "Food-tech qui révolutionne le paiement en restaurant. Stack FastAPI, Postgres, Vue 3. Startup en hyper-croissance.\n\n• 3+ ans en backend Python\n• FastAPI un gros plus\n• Tu aimes la vitesse startup\n• Bonus : Vue.js",
    url: "https://fr.indeed.com/viewjob?jk=pqr678",
    yourScore: 94,
  },
];

window.SOURCE_LABELS = {
  linkedin: "LinkedIn",
  indeed:   "Indeed",
  wttj:     "WTTJ",
};

// ─── Mock chat pour la branche demo ───────────────────────
window.mockChatResponse = function(text) {
  const jobs = window.MOCK_JOBS || [];

  if (/scrape|cherche|trouve|offres|search/i.test(text)) {
    const preview = jobs.slice(0, 5)
      .map((j, i) => `  ${i + 1}. **${j.title}** — ${j.company} (${j.city})`)
      .join("\n");
    return `J'ai simulé un scraping et trouvé **${jobs.length} offres** !\n\n${preview}\n\n...(et ${jobs.length - 5} autres)\n\nDis-moi "génère une lettre pour la 1ère" ou "montre toutes les offres".`;
  }

  if (/lettre|motivation|rédige|génère/i.test(text)) {
    return `Madame, Monsieur,\n\nVivement intéressé(e) par le poste de **Développeur Python Backend** chez **Doctolib**, je me permets de vous adresser ma candidature.\n\nFort(e) de 4 ans d'expérience en développement Python avec FastAPI et PostgreSQL, j'ai conçu des APIs performantes pour des systèmes à fort trafic. Ma maîtrise des bonnes pratiques (CI/CD, code review, tests automatisés) s'aligne avec la culture craft que vous valorisez.\n\nConvaincu(e) que mon profil correspond aux attentes du poste, je serais ravi(e) d'en discuter lors d'un entretien.\n\nCordialement,\n[Ton nom]\n\n---\n_⚠️ Mode démo — en production, la lettre est générée par Ollama selon ton profil réel._`;
  }

  if (/gap|manque|analyse|compétences|profil|match/i.test(text)) {
    return `**Analyse du gap — Développeur Python Backend @ Doctolib**\n\n✅ **Ce qui matche :**\n- Python / FastAPI — parfait\n- PostgreSQL — solide\n- Expérience APIs REST — validé\n- Travail en équipe agile — OK\n\n❌ **Ce qui manque :**\n- Kafka (message broker)\n- Kubernetes (mentionné comme bonus)\n- Redis en production\n\n**Score estimé : 8/10** — Excellent match ! Les éléments manquants sont des bonus, pas des bloquants.\n\n---\n_⚠️ Mode démo — en production, l'analyse compare ton profil réel à l'offre._`;
  }

  if (/traduis|anglais|translate|english/i.test(text)) {
    return `**Translated version (English) :**\n\nDear Hiring Team,\n\nI am writing to express my strong interest in the **Python Backend Developer** position at **Doctolib**.\n\nWith 4 years of experience building Python APIs with FastAPI and PostgreSQL, I have developed robust, scalable systems for high-traffic applications. I thrive in craft-oriented engineering cultures with rigorous code review and continuous deployment.\n\nI would love to discuss how my background aligns with your team's mission. Thank you for your consideration.\n\nBest regards,\n[Your name]\n\n---\n_⚠️ Demo mode — real translation powered by Ollama._`;
  }

  if (/montre|liste|voir|affiche|show/i.test(text)) {
    const list = jobs
      .map((j, i) => `  ${i + 1}. **${j.title}** — ${j.company} [${(j.source || "").toUpperCase()}]\n     📍 ${j.city}  💶 ${j.salary || "NC"}`)
      .join("\n");
    return `**${jobs.length} offres en mémoire :**\n\n${list}`;
  }

  return `Bonjour ! Je suis **JobBot** en mode démo 👋\n\nJe peux simuler :\n- **Scraper des offres** — "cherche des offres Python"\n- **Générer une lettre** — "génère une lettre pour l'offre 1"\n- **Analyser le gap profil/offre** — "qu'est-ce qui manque dans mon profil ?"\n- **Traduire** — "traduis la lettre en anglais"\n- **Lister les offres** — "montre toutes les offres"\n\n_En production, ces actions utilisent Ollama en local — 100% privé._`;
};

window.COMPANY_COLORS = {
  Doctolib: "#1AB1A8",
  "Back Market": "#1B6F4A",
  Qonto: "#1B194C",
  Lifen: "#E55E3B",
  Algolia: "#5468FF",
  Shine: "#FF8870",
  BlaBlaCar: "#1A2C5B",
  "Welcome to the Jungle": "#FFCD00",
  Mirakl: "#0E5CFF",
  "Hello Watt": "#FF6B00",
  Spendesk: "#0066FF",
  Sunday: "#FF7A45",
};
