"""
main.py
Orchestrateur principal.
Lance agent1 (collecte patient) puis agent2 (analyse & recommandation).
Connexion unique au LLM et chargement unique de la base vectorielle.
"""

from load_or_create_index import load_or_create_index
from llm_client import get_client
from agent1 import run_agent1
from agent2 import run_agent2



def main():
    print("\n" + "="*60)
    print("🏥  ASSISTANT MÉDICAL — Conseil sur les médicaments")
    print("="*60)

    # ── Démarrage : chargements uniques ───────────────────
    print("\n🚀 Initialisation du système...\n")

    model, index, chunks = load_or_create_index()  # base vectorielle
    get_client()                                    # connexion Groq unique

    print("✅ Système prêt !\n")

    # ── Phase 1 : collecte du profil patient ──────────────
    try:
        profil, historique = run_agent1()
    except KeyboardInterrupt:
        print("\n\n[SYSTÈME] Session annulée. Au revoir !")
        return

    if not profil:
        print("[SYSTÈME] ❌ Impossible de collecter le profil patient.")
        return

    # ── Phase 2 : questions-réponses ──────────────────────
    print("="*60)
    print("💊 Posez vos questions sur les médicaments")
    print("   (tapez 'quitter' pour terminer)")
    print("="*60 + "\n")

    while True:
        # Lire la question du patient
        try:
            question = input("[Vous] ").strip()
        except KeyboardInterrupt:
            break

        if not question:
            continue

        if question.lower() in ["quitter", "quit", "exit", "q"]:
            break

        # Agent 2 : analyse et recommandation
        reponse = run_agent2(
            patient_profile=profil,
            question=question,
            model=model,
            index=index,
            chunks=chunks,
            historique=historique,
        )

        print(f"\n[AGENT 2] {reponse}\n")
        print("-"*60 + "\n")

    print("\n[SYSTÈME] Merci d'avoir utilisé l'assistant médical. Au revoir !")


if __name__ == "__main__":
    main()
