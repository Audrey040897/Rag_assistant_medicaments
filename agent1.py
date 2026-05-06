"""
Agent conversationnel qui collecte les informations du patient
et produit un profil JSON structuré.
"""

import json
import re
from pathlib import Path

from llm_client import get_client
from config import LLM_MODEL

# ── Chargement du contexte depuis le fichier ───────────────
CONTEXT_AGENT1 = Path("context_agent1.txt").read_text(encoding="utf-8")


def extraire_profil(texte: str) -> dict | None:
    """Extrait le JSON du profil patient depuis la réponse de l'agent."""
    try:
        match = re.search(r"\{.*\}", texte, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass
    return None


def run_agent1() -> tuple[dict, list]:
    """
    Lance la conversation avec le patient.
    Retourne le profil patient JSON + l'historique de conversation.
    """
    client = get_client()

    messages = [
        {"role": "system", "content": CONTEXT_AGENT1}
    ]

    print("\n" + "="*60)
    print("💊 ASSISTANT MÉDICAL — Collecte des informations patient")
    print("="*60 + "\n")

    while True:
        # ── Appel LLM ─────────────────────────────────────
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.3,
        )

        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})

        # ── Collecte terminée ? ────────────────────────────
        if "[COLLECTE_TERMINEE]" in reply:
            profil = extraire_profil(reply)

            # Afficher le message sans le JSON brut
            message_propre = re.sub(r"\{.*\}", "", reply, flags=re.DOTALL)
            message_propre = message_propre.replace("[COLLECTE_TERMINEE]", "").strip()
            if message_propre:
                print(f"[AGENT 1] {message_propre}\n")

            print("[SYSTÈME] ✅ Profil patient collecté !\n")
            return profil, messages

        # ── Afficher la réponse ────────────────────────────
        print(f"[AGENT 1] {reply}\n")

        # ── Lire la réponse du patient ─────────────────────
        try:
            user_input = input("[Vous] ").strip()
        except KeyboardInterrupt:
            print("\n\n[SYSTÈME] Session interrompue.")
            raise

        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})


if __name__ == "__main__":
    profil, _ = run_agent1()
    print("\n📋 Profil collecté :")
    print(json.dumps(profil, ensure_ascii=False, indent=2))
