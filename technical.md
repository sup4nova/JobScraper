LLM =
chaque message passe d'abord par le LLM en mode "routeur" qui retourne un JSON {"intent": "...", "args": {...}}. Ça gère toutes les formulations naturelles.

Session state : les offres scrapées restent en mémoire pendant toute la conversation — "la 3ème" fonctionne sans re-scraper.

ollama_client.py = La cuisine

Elle ne sait faire qu'une seule chose : parler au modèle d'IA (Ollama).
Tu lui envoies des messages, elle te retourne du texte. C'est tout.
Elle ne sait pas ce qu'est une lettre de motivation ou une offre d'emploi — elle s'en fiche.


ollama_client.call([{"role": "user", "content": "Bonjour"}])
→ "Bonjour ! Comment puis-je vous aider ?"


tools.py = Le menu

Ce sont les recettes concrètes de l'application.
Chaque fonction sait comment utiliser la cuisine (ollama_client) pour faire quelque chose d'utile :

generate_letter() construit le bon prompt + appelle la cuisine
analyze_gap() construit un autre prompt + appelle la cuisine
scrape_jobs() ne passe même pas par la cuisine — elle lance les scrapers directement
tools.py sait ce qu'est une offre d'emploi, un profil, une lettre. Mais il ne décide pas quand les utiliser.

agent.py = Le serveur

Il parle à toi (l'utilisateur), comprend ce que tu veux, et choisit quel outil appeler.

Quand tu dis "génère une lettre", c'est l'agent qui :

Demande à l'IA de classifier ton message → intent = "letter"
Récupère la bonne offre en mémoire
Appelle tools.generate_letter()
Affiche le résultat
Résumé en une ligne chacun :

Fichier	Rôle	Sait quoi ?
ollama_client.py	Envoie/reçoit du texte à l'IA	Rien sur le domaine
tools.py	Fait les actions métier	Ce qu'est une lettre, un gap, un scraping
agent.py	Comprend l'utilisateur et orchestre	Ce que l'utilisateur veut faire


Toi
 ↓  (texte brut)
agent.py        → "c'est quoi l'intent ?" → demande à ollama_client
 ↓  (intent classifié : "letter", "scrape"...)
tools.py        → construit le bon prompt + appelle ollama_client
 ↓
ollama_client.py → envoie à Ollama → reçoit la réponse
 ↓
agent.py        → affiche le résultat
Une nuance : tools.py n'aide pas à la "traduction" du message utilisateur — ça c'est l'agent tout seul qui le fait via le routeur. Les tools, c'est après que l'intent est connu, pour exécuter l'action.

Donc :

agent = comprend ce que tu veux
tools = fait le travail (avec l'IA ou les scrapers)
ollama_client = le seul qui parle vraiment à Ollama

on initialise une session et appelle lagent dansw fast api avec une requete post à /api/chat
