"""
agent2.py
Agent d'analyse qui reçoit le profil patient,
recherche dans FAISS et vérifie les conditions de prescription.
"""

import json
import numpy as np
from pathlib import Path

from llm_client import get_client
from config import LLM_MODEL

# ── Chargement du contexte depuis le fichier ───────────────
CONTEXT_AGENT2 = Path("context_agent2.txt").read_text(encoding="utf-8")


def rescore_chunks(chunks_results: list[dict], patient_profile: dict) -> list[dict]:
    """
    Re-score les chunks FAISS selon le profil patient.
    Booste les sections les plus pertinentes pour ce patient.
    """
    for chunk in chunks_results:
        score    = chunk["score"]
        priority = chunk["metadata"]["priority"]
        section  = chunk["metadata"]["section"]

        # Toujours booster contre-indications et conditions
        if section == "contre_indications":
            priority *= 1.5
        if section == "conditions_prescription":
            priority *= 1.5

        # Patient enceinte ou allaitant → booster grossesse
        if patient_profile.get("grossesse") and \
           section == "grossesse_allaitement":
            priority *= 1.5
        if patient_profile.get("allaitement") and \
           section == "grossesse_allaitement":
            priority *= 1.5

        # Médicaments en cours → booster interactions
        if patient_profile.get("medicaments_en_cours") and \
           section == "interactions":
            priority *= 1.5

        # Patient âgé > 65 ans → booster mises en garde
        if patient_profile.get("age", 0) > 65 and \
           section == "mises_en_garde":
            priority *= 1.3

        chunk["score_final"] = score * priority

    return sorted(chunks_results, key=lambda x: x["score_final"], reverse=True)


def rechercher_chunks(question: str, model, index, chunks: list[dict], k: int = 8) -> list[dict]:
    """Recherche les k chunks les plus pertinents dans FAISS."""
    vecteur = model.encode([question], normalize_embeddings=True)
    vecteur = np.array(vecteur, dtype=np.float32)

    scores, indices = index.search(vecteur, k)

    resultats = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = chunks[idx]
        resultats.append({
            "texte":       chunk["texte"],
            "score":       float(score),
            "score_final": float(score),
            "metadata": {
                "medicament": chunk["medicament"],
                "section":    chunk["section"],
                "priority":   chunk["priority"],
                "code_cis":   chunk["code_cis"],
            }
        })

    return resultats


def construire_contexte_chunks(chunks_rescores: list[dict]) -> str:
    """Formate les chunks pour les injecter dans le prompt."""
    contexte = ""
    for i, chunk in enumerate(chunks_rescores, 1):
        meta = chunk["metadata"]
        contexte += (
            f"\n--- Chunk {i} ---\n"
            f"Médicament : {meta['medicament']}\n"
            f"Section    : {meta['section']}\n"
            f"Contenu    : {chunk['texte']}\n"
        )
    return contexte


def run_agent2(
    patient_profile: dict,
    question: str,
    model,
    index,
    chunks: list[dict],
    historique: list[dict] = None,
) -> str:
    """
    Analyse le profil patient et génère une recommandation.
    """
    client = get_client()

    print("[SYSTÈME] 🔍 Recherche dans la base de connaissances...")

    # ── Recherche FAISS + re-scoring ──────────────────────
    requete        = f"{question} {patient_profile.get('symptomes', '')}"
    chunks_trouves = rechercher_chunks(requete, model, index, chunks, k=8)
    chunks_rescores = rescore_chunks(chunks_trouves, patient_profile)

    # ── Construction du prompt ────────────────────────────
    contexte_chunks = construire_contexte_chunks(chunks_rescores)

    prompt_user = (
        f"Profil patient :\n{json.dumps(patient_profile, ensure_ascii=False, indent=2)}\n\n"
        f"Question du patient : {question}\n\n"
        f"Chunks pertinents de la base BDPM :{contexte_chunks}"
    )

    messages = [
        {"role": "system", "content": CONTEXT_AGENT2},
        {"role": "user",   "content": prompt_user},
    ]

    print("[SYSTÈME] 🤖 Génération de la réponse...\n")

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.1,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    from load_or_create_index import load_or_create_index

    model, index, chunks = load_or_create_index()

    profil_test = {
        "symptomes": "maux de tête, fièvre",
        "age": 35,
        "poids": 70,
        "grossesse": False,
        "allaitement": False,
        "medicaments_en_cours": ["aspirine"],
        "allergies": [],
        "antecedents": ""
    }

    reponse = run_agent2(
        patient_profile=profil_test,
        question="Puis-je prendre du doliprane ?",
        model=model,
        index=index,
        chunks=chunks,
    )

    print(f"\n[AGENT 2] {reponse}")