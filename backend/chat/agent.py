"""
Boucle principale du chatbot JobBot.
Lancement : python chat.py  (depuis la racine du projet)
"""
import json
import os
import re
import sys

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from chat.ollama_client import call, is_available, list_local_models, DEFAULT_MODEL
from chat import tools


# ── Prompt du routeur ─────────────────────────────────────────────────────────
#Le _ROUTER_SYSTEM (agent.py:20) est un prompt qui demande à l'IA 
# de répondre uniquement avec un JSON comme 
# {"intent": "letter", "args": {"index": 2}}. 
# C'est ce qu'on appelle un routeur d'intentions.

# Intent	Déclencheur exemple	Action
# scrape	"cherche des offres dev Python"	Lance tools.scrape_jobs()
# letter	"génère une lettre pour l'offre 1"	Lance tools.generate_letter()
# gap	"qu'est-ce qui manque dans mon profil ?"	Lance tools.analyze_gap()
# translate	"traduis en anglais"	Lance tools.translate_text()
# show	"montre les offres"	Réaffiche les offres en mémoire
# chat	"c'est quoi un CDI ?"	Conversation libre avec l'IA

_ROUTER_SYSTEM = """\
Tu es le routeur d'un assistant de recherche d'emploi.
Analyse le message utilisateur et réponds UNIQUEMENT avec un JSON valide, sans texte autour.

Format strict : {"intent": "INTENT", "args": {}}

Intents disponibles :
- "scrape"    : l'utilisateur veut chercher/scraper des offres d'emploi
  args: {"query": "<poste recherché>", "sites": ["indeed"|"linkedin"|"wttj"], "limit": <int>}
  → sites par défaut : ["linkedin","wttj"] si non précisé ; limit par défaut : 10

- "letter"    : l'utilisateur veut une lettre de motivation
  args: {"index": <numéro de l'offre (1-based), 0 si non précisé>}

- "gap"       : l'utilisateur veut analyser le gap profil/offre ou les compétences manquantes
  args: {"index": <numéro de l'offre (1-based), 0 si non précisé>}

- "translate" : l'utilisateur veut traduire quelque chose (la dernière lettre par défaut)
  args: {"target": "en"|"fr"|"de"|"es"}

- "show"      : l'utilisateur veut voir la liste des offres déjà scrapées
  args: {}

- "chat"      : toute autre question ou conversation générale
  args: {}

Exemples :
  "Scrape les offres AI remote sur LinkedIn" → {"intent":"scrape","args":{"query":"AI remote","sites":["linkedin"],"limit":10}}
  "Génère une lettre pour la 3ème"           → {"intent":"letter","args":{"index":3}}
  "Qu'est-ce qui manque dans mon profil pour ce poste ?" → {"intent":"gap","args":{"index":0}}
  "Traduis la lettre en anglais"             → {"intent":"translate","args":{"target":"en"}}
  "Montre-moi les offres"                   → {"intent":"show","args":{}}
"""


def _route(message: str, model: str) -> dict:
    """Demande au LLM de classifier l'intent. Fallback sur 'chat' si JSON invalide."""
    resp = call(
        [
            {"role": "system", "content": _ROUTER_SYSTEM},
            {"role": "user", "content": message},
        ],
        model,
    )
    match = re.search(r"\{.*\}", resp, re.DOTALL)
    if not match:
        return {"intent": "chat", "args": {}}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {"intent": "chat", "args": {}}


def _get_job(offres: list[dict], index: int) -> dict | None:
    """Retourne l'offre à l'index (1-based). index=0 → première offre."""
    if not offres:
        return None
    if index <= 0:
        return offres[0]
    if index > len(offres):
        return None
    return offres[index - 1]


def _load_profil() -> dict:
    candidates = [
        os.path.join(_BACKEND, "profil.json"),
        os.path.join(os.path.dirname(_BACKEND), "profil.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return {}


# ── API handler (sans print, sans input) ─────────────────────────────────────

class Session:
    """État d'une conversation : offres scrapées, dernière lettre, historique."""
    def __init__(self):
        self.offres: list[dict] = []
        self.last_letter: str = ""
        self.history: list[dict] = []


def handle_message(user_input: str, session: Session, model: str = DEFAULT_MODEL) -> str:
    """Traite un message et retourne la réponse en string (pour l'API HTTP)."""
    profil = _load_profil()

    route = _route(user_input, model)
    intent = route.get("intent", "chat")
    args = route.get("args", {})

    if intent == "scrape":
        query = args.get("query") or user_input
        sites = args.get("sites") or ["linkedin", "wttj"]
        limit = int(args.get("limit") or 10)
        offres = tools.scrape_jobs(query, sites, limit)
        if not offres:
            return "Aucune offre trouvée. Essaie d'autres termes ou sites."
        session.offres = offres
        return f"{len(offres)} offre(s) trouvée(s) :\n\n" + tools.format_jobs_list(offres)

    if intent == "letter":
        if not profil:
            return "Ton profil est vide. Configure-le d'abord via l'interface."
        job = _get_job(session.offres, int(args.get("index") or 0))
        if job is None:
            msg = "Scrape d'abord des offres." if not session.offres else f"Il n'y a que {len(session.offres)} offre(s)."
            return f"Pas d'offre à cet index. {msg}"
        letter = tools.generate_letter(job, profil, model)
        session.last_letter = letter
        return letter

    if intent == "gap":
        if not profil:
            return "Ton profil est vide. Configure-le d'abord via l'interface."
        job = _get_job(session.offres, int(args.get("index") or 0))
        if job is None:
            msg = "Scrape d'abord des offres." if not session.offres else f"Il n'y a que {len(session.offres)} offre(s)."
            return f"Pas d'offre à cet index. {msg}"
        return tools.analyze_gap(job, profil, model)

    if intent == "translate":
        if not session.last_letter:
            return "Je n'ai rien à traduire — génère d'abord une lettre."
        return tools.translate_text(session.last_letter, args.get("target", "en"), model)

    if intent == "show":
        if not session.offres:
            return "Pas d'offres en mémoire. Lance un scraping d'abord."
        return f"{len(session.offres)} offre(s) en mémoire :\n\n" + tools.format_jobs_list(session.offres)

    # chat général
    session.history.append({"role": "user", "content": user_input})
    sys_msg = (
        "Tu es un assistant de recherche d'emploi. "
        "Réponds en français, de manière concise et utile. "
        f"Profil de l'utilisateur : {json.dumps(profil, ensure_ascii=False)}"
    )
    reply = call([{"role": "system", "content": sys_msg}, *session.history[-6:]], model)
    session.history.append({"role": "assistant", "content": reply})
    return reply


# ── Boucle principale ─────────────────────────────────────────────────────────

def run(model: str = DEFAULT_MODEL):
    print("\n" + "═" * 58)
    print("  JobBot — Assistant de recherche d'emploi (100% local)")
    print(f"  Modèle : {model}")
    print("  'exit' pour quitter • 'modèles' pour voir ceux installés")
    print("═" * 58)

    # Vérification Ollama
    if not is_available(model):
        local = list_local_models()
        if not local:
            print(
                "\n⚠️  Ollama ne répond pas. Lance d'abord :\n"
                "     ollama serve\n"
                "  Puis dans un autre terminal :\n"
                f"     ollama pull {model}\n"
            )
        else:
            print(f"\n⚠️  Modèle '{model}' non trouvé. Modèles installés :")
            for m in local:
                print(f"     • {m}")
            print(f"\n  Lance : ollama pull {model}")
            print(f"  Ou relance avec : python chat.py --model {local[0]}\n")
        return

    # # Chargement du profil

    # La mémoire de session (agent.py:140) : le bot garde en RAM pendant la conversation :

    # session_offres — la liste des offres scrapées
    # last_letter — la dernière lettre générée (pour pouvoir la traduire)
    # history — les derniers échanges du mode chat (pour que l'IA se souvienne du contexte)
                                                
    profil = _load_profil()
    if profil and profil.get("name") not in ("", "test", None):
        print(f"\nProfil : {profil.get('name')} — {profil.get('title')}")
    else:
        print("\n⚠️  Profil vide ou non configuré. Lance main.py pour le remplir.")
        profil = {}

    # Exemples rapides
    print("\nExemples :")
    print('  "Scrape les offres data scientist remote sur LinkedIn"')
    print('  "Génère une lettre pour la 2ème offre"')
    print('  "Qu\'est-ce qui manque dans mon profil pour l\'offre 1 ?"')
    print('  "Traduis la lettre en anglais"')
    print('  "Montre les offres"\n')

    # État de session
    session_offres: list[dict] = []
    last_letter: str = ""
    history: list[dict] = []          # pour le mode "chat" général

    while True:
        try:
            user_input = input("Toi : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAu revoir !")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q", "bye", "au revoir"):
            print("Au revoir !")
            break

        if user_input.lower() in ("modèles", "models"):
            local = list_local_models()
            print("Modèles installés :", ", ".join(local) if local else "aucun")
            continue

        # Routing
        print("  ⚙️  ...", end="\r", flush=True)
        route = _route(user_input, model)
        intent = route.get("intent", "chat")
        args = route.get("args", {})
        print("        ", end="\r")   # efface l'indicateur

        # ── SCRAPE ────────────────────────────────────────────────────────────
        if intent == "scrape":
            query = args.get("query") or user_input
            sites = args.get("sites") or ["linkedin", "wttj"]
            limit = int(args.get("limit") or 10)

            print(f"\nBot : Scraping '{query}' sur {', '.join(sites)} (max {limit}) ...\n")
            offres = tools.scrape_jobs(query, sites, limit)

            if not offres:
                print("Bot : Aucune offre trouvée. Essaie d'autres termes ou sites.\n")
            else:
                session_offres = offres
                print(f"\nBot : {len(offres)} offre(s) trouvée(s) :\n")
                print(tools.format_jobs_list(offres))

        # ── LETTRE ────────────────────────────────────────────────────────────
        elif intent == "letter":
            if not profil:
                print("Bot : Ton profil est vide. Lance main.py pour le configurer d'abord.\n")
                continue
            index = int(args.get("index") or 0)
            job = _get_job(session_offres, index)
            if job is None:
                msg = "Scrape d'abord des offres." if not session_offres else f"Il n'y a que {len(session_offres)} offre(s)."
                print(f"Bot : Pas d'offre à cet index. {msg}\n")
            else:
                print(f"\nBot : Génération de la lettre pour '{job.get('title')}' @ {job.get('company')}...\n")
                letter = tools.generate_letter(job, profil, model)
                last_letter = letter
                print("─" * 58)
                print(letter)
                print("─" * 58)
                print("\n(Astuce : 'Traduis en anglais' pour obtenir la version EN)\n")

        # ── GAP ANALYSIS ──────────────────────────────────────────────────────
        elif intent == "gap":
            if not profil:
                print("Bot : Ton profil est vide. Lance main.py pour le configurer d'abord.\n")
                continue
            index = int(args.get("index") or 0)
            job = _get_job(session_offres, index)
            if job is None:
                msg = "Scrape d'abord des offres." if not session_offres else f"Il n'y a que {len(session_offres)} offre(s)."
                print(f"Bot : Pas d'offre à cet index. {msg}\n")
            else:
                print(f"\nBot : Analyse du gap pour '{job.get('title')}' @ {job.get('company')}...\n")
                analysis = tools.analyze_gap(job, profil, model)
                print("─" * 58)
                print(analysis)
                print("─" * 58 + "\n")

        # ── TRADUCTION ────────────────────────────────────────────────────────
        elif intent == "translate":
            if not last_letter:
                print("Bot : Je n'ai rien à traduire — génère d'abord une lettre.\n")
            else:
                target = args.get("target", "en")
                lang_label = {"en": "anglais", "fr": "français", "de": "allemand", "es": "espagnol"}.get(target, target)
                print(f"\nBot : Traduction en {lang_label}...\n")
                translated = tools.translate_text(last_letter, target, model)
                print("─" * 58)
                print(translated)
                print("─" * 58 + "\n")

        # ── SHOW ──────────────────────────────────────────────────────────────
        elif intent == "show":
            if not session_offres:
                print("Bot : Pas d'offres en mémoire. Lance un scraping d'abord.\n")
            else:
                print(f"\nBot : {len(session_offres)} offre(s) en mémoire :\n")
                print(tools.format_jobs_list(session_offres))

        # ── CHAT GÉNÉRAL ──────────────────────────────────────────────────────
        else:
            history.append({"role": "user", "content": user_input})
            sys_msg = (
                "Tu es un assistant de recherche d'emploi. "
                "Réponds en français, de manière concise et utile. "
                f"Profil de l'utilisateur : {json.dumps(profil, ensure_ascii=False)}"
            )
            reply = call(
                [{"role": "system", "content": sys_msg}, *history[-6:]],
                model,
            )
            history.append({"role": "assistant", "content": reply})
            print(f"\nBot : {reply}\n")
