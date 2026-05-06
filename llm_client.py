"""
llm_client.py
Initialise le client Groq UNE SEULE FOIS au démarrage.
Tous les agents importent ce module pour utiliser le même client.
"""

import os
from groq import Groq
from dotenv import load_dotenv
from config import LLM_MODEL

load_dotenv()

# ── Connexion unique au démarrage ──────────────────────────
_client = None

def get_client() -> Groq:
    """
    Retourne le client Groq.
    Le crée une seule fois (pattern Singleton).
    """
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("❌ GROQ_API_KEY manquante dans le .env")
        _client = Groq(api_key=api_key)
        print("✅ Client Groq initialisé\n")
    return _client

