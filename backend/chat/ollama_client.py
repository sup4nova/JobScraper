"""
Client HTTP pour Ollama — stdlib urllib uniquement, zéro dépendances tierces.
Ollama doit tourner localement : ollama serve
"""
import json
import urllib.request
import urllib.error

DEFAULT_MODEL = "qwen2.5:7b"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"


def call(messages: list[dict], model: str = DEFAULT_MODEL) -> str:
    """Envoie une conversation à Ollama, retourne la réponse en string."""
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        OLLAMA_CHAT_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            return data["message"]["content"]
    except urllib.error.URLError as e:
        raise ConnectionError(
            "Ollama ne répond pas — lance 'd'abord : ollama serve\n"
            f"  (détail : {e})"
        ) from e


def list_local_models() -> list[str]:
    """Retourne les noms des modèles installés localement."""
    try:
        req = urllib.request.Request(OLLAMA_TAGS_URL)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def is_available(model: str = DEFAULT_MODEL) -> bool:
    """Vérifie qu'Ollama tourne ET que le modèle est installé."""
    models = list_local_models()
    base = model.split(":")[0]
    return any(m.startswith(base) for m in models)
