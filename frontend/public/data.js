/* Mock job data matching the scraper output schema:
   { source, title, company, city, salary, contract_type, education,
     easily_apply, description, url }
*/

window.MOCK_JOBS = [
  {
    source: "wellfound",
    title: "Python Backend Developer",
    company: "Rendezo",
    city: "Paris (75)",
    salary: "55–70 k€ / yr",
    contract_type: "Permanent · Hybrid",
    education: "Master's degree",
    easily_apply: true,
    description: "Join the Platform team to build FastAPI APIs that scale to millions of appointments. Modern stack: Python 3.12, PostgreSQL, Redis, Kafka, AWS. You'll work in pair-programming, continuous deployment, demanding but supportive code reviews.\n\n• 4+ years in Python (FastAPI/Django)\n• Experience with relational databases\n• Professional English (European team)\n• Bonus: Kubernetes, observability",
    url: "https://www.linkedin.com/jobs/view/9001000001",
    yourScore: 92,
  },
  {
    source: "indeed",
    title: "Senior Data Engineer",
    company: "Recircl",
    city: "Bordeaux (33)",
    salary: "60–80 k€",
    contract_type: "Permanent · Full remote",
    education: "Master's degree",
    easily_apply: false,
    description: "Build the data backbone of the circular economy. Stack: Airflow, dbt, Snowflake, Python, Terraform. You'll design critical pipelines for millions of customers.\n\n• 5+ years in data engineering\n• Proficiency in dbt + cloud warehouse\n• Product mindset\n• Fluent English",
    url: "https://fr.indeed.com/viewjob?jk=mock0002",
    yourScore: 78,
  },
  {
    source: "linkedin",
    title: "Lead Backend — Python / Go",
    company: "Paymio",
    city: "Lyon (69)",
    salary: "75–95 k€ + stock options",
    contract_type: "Permanent · Hybrid 2d",
    education: "Master's degree",
    easily_apply: true,
    description: "Lead a squad of 5 engineers building European payment infrastructure. Distributed platform with high reliability standards and a strong engineering craft culture.\n\n• 7+ years backend including 2 in lead role\n• Strong Python or Go skills\n• Able to design distributed systems\n• Enjoy mentoring",
    url: "https://www.linkedin.com/jobs/view/9001000003",
    yourScore: 85,
  },
  {
    source: "remoteok",
    title: "Fullstack Developer Python / Vue",
    company: "Carelink",
    city: "Paris (75)",
    salary: "50–65 k€",
    contract_type: "Permanent · fully remote possible",
    education: "Bachelor's degree min.",
    easily_apply: true,
    description: "Healthcare tech — connecting health professionals. Stack: Python + Vue 3 + Postgres. You'll touch the product from design system to async jobs.\n\n• 3+ years fullstack\n• Vue 3 (Composition API)\n• Python + a web framework\n• Product & UX sensibility",
    url: "https://fr.remoteok.com/viewjob?jk=mock0004",
    yourScore: 88,
  },
  {
    source: "linkedin",
    title: "Site Reliability Engineer",
    company: "Findexa",
    city: "Paris (75) · Remote",
    salary: "70–90 k€",
    contract_type: "Permanent · Full remote possible",
    education: "Master's degree",
    easily_apply: false,
    description: "Keep the infrastructure that serves billions of requests a year running. Kubernetes, Terraform, observability, capacity planning. Well-organized on-call rotations, global team.\n\n• 4+ years in SRE/DevOps\n• Kubernetes in production\n• Programming (Go or Python)\n• Fluent English",
    url: "https://www.linkedin.com/jobs/view/9001000005",
    yourScore: 65,
  },
  {
    source: "indeed",
    title: "Python Developer — Junior welcome",
    company: "Néobiz",
    city: "Nantes (44)",
    salary: "38–48 k€",
    contract_type: "Permanent · Hybrid",
    education: "Bachelor's degree",
    easily_apply: true,
    description: "Neobank for professionals — small team, personalized support. Stack: Django, Postgres, AWS. You learn, you code, you ship.\n\n• 1–3 years in Python\n• You want to grow fast\n• You care about code quality\n• Bonus: fintech knowledge",
    url: "https://fr.indeed.com/viewjob?jk=mock0006",
    yourScore: 81,
  },
  {
    source: "wellfound",
    title: "Tech Lead Data Platform",
    company: "Trajeo",
    city: "Paris (75)",
    salary: "85–110 k€ + equity",
    contract_type: "Permanent · Hybrid 3d",
    education: "Master's degree (engineering school)",
    easily_apply: false,
    description: "Build a self-service data platform for 300+ employees. You'll have impact on tens of millions of users.\n\n• 8+ years including 3 in lead\n• Python + Scala/Java\n• Spark, Airflow, Kafka\n• Fluent English",
    url: "https://www.wellfound.com/jobs/view/9001000007",
    yourScore: 72,
  },
  {
    source: "indeed",
    title: "Python Backend Developer",
    company: "Hireloop",
    city: "Paris (75)",
    salary: "55–72 k€",
    contract_type: "Permanent · Hybrid 2d",
    education: "Master's degree",
    easily_apply: true,
    description: "Join a squad building recruitment tools used by thousands of companies. FastAPI, Postgres, Redis, ElasticSearch.\n\n• 4+ years Python backend\n• Best practices (tests, CI/CD)\n• Curious about product\n• English OK",
    url: "https://fr.indeed.com/viewjob?jk=mock0008",
    yourScore: 90,
  },
  {
    source: "linkedin",
    title: "Software Engineer — Search",
    company: "Marketly",
    city: "Paris (75)",
    salary: "60–78 k€",
    contract_type: "Permanent · Hybrid",
    education: "Master's degree",
    easily_apply: false,
    description: "Work on the e-commerce search engine powering major retail brands. ElasticSearch, Java, Python. Highly technical role.\n\n• 4+ years backend dev\n• Search/IR a plus\n• Strong algorithms background\n• Fluent English",
    url: "https://www.linkedin.com/jobs/view/9001000009",
    yourScore: 68,
  },
  {
    source: "remoteok",
    title: "Senior Python Developer",
    company: "Energo",
    city: "Lille (59)",
    salary: "55–70 k€",
    contract_type: "Permanent · Full remote",
    education: "Master's degree",
    easily_apply: true,
    description: "Energy transition — helping people consume smarter. Stack: Django, Vue, Postgres. Team of 25 devs, craft culture.\n\n• 5+ years Python\n• Django or FastAPI\n• You care about impact\n• Autonomous",
    url: "https://fr.remoteok.com/viewjob?jk=mock0010",
    yourScore: 86,
  },
  {
    source: "linkedin",
    title: "Engineering Manager Backend",
    company: "Spendly",
    city: "Paris (75)",
    salary: "90–115 k€",
    contract_type: "Permanent · Hybrid",
    education: "Master's degree",
    easily_apply: false,
    description: "Manage a team of 6 backend engineers. 30% coding, 70% management, growth & process.\n\n• 8+ years dev including 2+ in management\n• Backend (Node/Python/Go)\n• Fluent English\n• You know how to hire and grow your team",
    url: "https://www.linkedin.com/jobs/view/9001000011",
    yourScore: 58,
  },
  {
    source: "indeed",
    title: "Python / FastAPI Developer",
    company: "Tablo",
    city: "Lyon (69)",
    salary: "48–62 k€",
    contract_type: "Permanent · Hybrid",
    education: "Bachelor's degree min.",
    easily_apply: true,
    description: "Food-tech revolutionizing restaurant payments. Stack: FastAPI, Postgres, Vue 3. Hyper-growth startup.\n\n• 3+ years Python backend\n• FastAPI a big plus\n• You thrive in startup speed\n• Bonus: Vue.js",
    url: "https://fr.indeed.com/viewjob?jk=mock0012",
    yourScore: 94,
  },
];

window.SOURCE_LABELS = {
  linkedin: "LinkedIn",
  indeed:   "Indeed",
  remoteok:  "RemoteOK",
  wellfound: "Wellfound",
};

// ─── Mock chat for demo branch ───────────────────────
window.mockChatResponse = function(text) {
  const jobs = window.MOCK_JOBS || [];

  if (/scrape|cherche|trouve|offres|search|find|jobs/i.test(text)) {
    const preview = jobs.slice(0, 5)
      .map((j, i) => `  ${i + 1}. **${j.title}** — ${j.company} (${j.city})`)
      .join("\n");
    return `I simulated a scrape and found **${jobs.length} listings**!\n\n${preview}\n\n...(and ${jobs.length - 5} more)\n\nTry "generate a cover letter for job 1" or "show all jobs".`;
  }

  if (/letter|cover|motivation|write|generate/i.test(text)) {
    return `Dear Hiring Team,\n\nI am writing to express my strong interest in the **Python Backend Developer** position.\n\nWith 4 years of experience building Python APIs with FastAPI and PostgreSQL, I have developed scalable, high-performance systems. I thrive in craft-oriented engineering cultures with rigorous code reviews and continuous deployment.\n\nI would love to discuss how my background aligns with your team's mission. Thank you for your consideration.\n\nBest regards,\n[Your name]\n\n---\n_⚠️ Demo mode — in production, the letter is generated by Ollama based on your real profile._`;
  }

  if (/gap|missing|analyze|skills|profile|match/i.test(text)) {
    return `**Gap analysis — Python Backend Developer @ Doctolib**\n\n✅ **What matches:**\n- Python / FastAPI — perfect\n- PostgreSQL — solid\n- REST API experience — validated\n- Agile teamwork — OK\n\n❌ **What's missing:**\n- Kafka (message broker)\n- Kubernetes (listed as bonus)\n- Redis in production\n\n**Estimated score: 8/10** — Excellent match! The missing items are bonuses, not blockers.\n\n---\n_⚠️ Demo mode — in production, the analysis compares your real profile to the listing._`;
  }

  if (/translat|french|english/i.test(text)) {
    return `**Translated version (French):**\n\nMadame, Monsieur,\n\nVivement intéressé(e) par le poste de **Développeur Python Backend**, je me permets de vous adresser ma candidature.\n\nFort(e) de 4 ans d'expérience en développement Python avec FastAPI et PostgreSQL, j'ai conçu des APIs performantes pour des systèmes à fort trafic.\n\nCordialement,\n[Votre nom]\n\n---\n_⚠️ Demo mode — real translation powered by Ollama._`;
  }

  if (/show|list|all|display/i.test(text)) {
    const list = jobs
      .map((j, i) => `  ${i + 1}. **${j.title}** — ${j.company} [${(j.source || "").toUpperCase()}]\n     📍 ${j.city}  💶 ${j.salary || "N/A"}`)
      .join("\n");
    return `**${jobs.length} jobs in memory:**\n\n${list}`;
  }

  return `Hey! I'm **JobBot** in demo mode 👋\n\nI can simulate:\n- **Scraping jobs** — "find Python jobs"\n- **Generating a cover letter** — "generate a letter for job 1"\n- **Analyzing profile/job gap** — "what's missing from my profile?"\n- **Translating** — "translate the letter to French"\n- **Listing jobs** — "show all jobs"\n\n_In production, these actions use Ollama locally — 100% private._`;
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
