"""
Point d'entrée du chatbot JobBot.
Usage : python chat.py [--model qwen2.5:7b]
"""
import sys
import os
import argparse

# Ajoute backend/ au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from chat.agent import run
from chat.ollama_client import DEFAULT_MODEL

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JobBot — Assistant de recherche d'emploi (100% local)")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Modèle Ollama à utiliser (défaut : {DEFAULT_MODEL}). Ex : mistral, llama3.2",
    )
    args = parser.parse_args()
    run(args.model)
