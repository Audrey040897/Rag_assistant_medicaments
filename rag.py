# rag.py
import os
import json
import faiss
import numpy as np
from groq import Groq
from sentence_transformers import SentenceTransformer
from config import (
    LLM_MODEL, EMBEDDING_MODEL,
    INDEX_PATH, CHUNKS_PATH,
    TOP_K, GROQ_API_KEY
)

# ============================================================
# CLASSE RAG — connexion unique au provider
# ============================================================
class RAGAssistant:
    """
    Système RAG complet avec 2 agents.
    Connexion unique au provider Groq à l'instanciation.
    Idempotent : si l'index existe, il est rechargé sans réindexation.
    """

    def __init__(self):
        # Connexion unique au provider Groq
        self.client = Groq(api_key=GROQ_API_KEY)
        self.modele = None
        self.index = None
        self.chunks = None
        self._charge_ressources()

    def _charge_ressources(self):
        """Charge le modèle d'embedding et l'index FAISS une seule fois."""
        print("🤖 Chargement du modèle d'embedding...")
        self.modele = SentenceTransformer(EMBEDDING_MODEL)

        print("📂 Chargement de l'index FAISS...")
        self.index = faiss.read_index(INDEX_PATH)
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)
        print(f"✅ {self.index.ntotal} vecteurs chargés")

    # ============================================================
    # RECHERCHE VECTORIELLE
    # ============================================================
    def rechercher(self, question: str, k: int = TOP_K) -> list:
        """Recherche les k chunks les plus pertinents (vectoriel + boost par mot-clé)."""

        # Recherche vectorielle
        vecteur = np.array(
            self.modele.encode([question]),
            dtype=np.float32
        )
        faiss.normalize_L2(vecteur)
        distances, indices = self.index.search(vecteur, k * 3)

        resultats = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:
                continue
            resultats.append({
                "contenu": self.chunks[idx]["contenu"],
                "metadata": self.chunks[idx]["metadata"],
                "score": float(1 - distances[0][i])
            })

        # Boost par mot-clé
        mots_question = question.lower().split()
        for r in resultats:
            nom = r["metadata"].get("medicament", "").lower()
            for mot in mots_question:
                if len(mot) > 4 and mot in nom:
                    r["score"] += 0.3
                    break

        # Trier par score final
        resultats.sort(key=lambda x: x["score"], reverse=True)
        return resultats[:k]

    # ============================================================
    # AGENT 1 — Collecte infos utilisateur
    # ============================================================
    def agent_collecte(self, historique: list) -> dict:
        """
        Pose des questions à l'utilisateur pour collecter
        son profil patient et construire une requête enrichie.
        """
        prompt_systeme = """Tu es un assistant médical qui collecte des informations 
pour aider à trouver le bon médicament.

Tu dois collecter ces informations de manière naturelle :
- Le problème de santé ou symptôme principal
- La durée des symptômes
- Les allergies connues
- Les autres médicaments pris actuellement
- Si la personne est enceinte ou allaite
- L'âge (adulte, enfant, personne âgée)

Pose UNE SEULE question à la fois. Sois bref et bienveillant.
Quand tu as assez d'informations (au moins 2-3 réponses),
réponds UNIQUEMENT avec ce format JSON et rien d'autre :
{
    "collecte_terminee": true,
    "resume": "résumé du profil patient en une phrase",
    "requete_rag": "requête optimisée pour chercher dans la base médicaments"
}
Si tu n'as pas encore assez d'infos, pose juste ta question suivante."""

        messages = [{"role": "system", "content": prompt_systeme}]
        messages.extend(historique)

        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            max_tokens=300
        )

        contenu = response.choices[0].message.content.strip()

        try:
            if "collecte_terminee" in contenu:
                debut = contenu.find("{")
                fin = contenu.rfind("}") + 1
                data = json.loads(contenu[debut:fin])
                if data.get("collecte_terminee"):
                    return {
                        "termine": True,
                        "resume": data.get("resume", ""),
                        "requete_rag": data.get("requete_rag", "")
                    }
        except Exception:
            pass

        return {"termine": False, "question": contenu}

    # ============================================================
    # AGENT 2 — Vérification contre-indications
    # ============================================================
    def agent_contre_indications(self, profil_patient: str, chunks_pertinents: list) -> dict:
        """
        Analyse les chunks et détecte les contre-indications
        selon le profil du patient.
        """
        contexte = "\n\n".join([
            f"[{c['metadata']['medicament']} - {c['metadata']['section']}]\n{c['contenu']}"
            for c in chunks_pertinents
        ])

        prompt = f"""Tu es un expert pharmaceutique qui analyse les contre-indications.

Profil du patient : {profil_patient}

Base de données médicaments :
{contexte}

Analyse les contre-indications pour ce patient :
- Grossesse / allaitement
- Allergies
- Interactions avec d'autres médicaments
- Populations particulières (enfants, personnes âgées)
- Conditions de prescription requises

Réponds UNIQUEMENT en JSON avec ce format exact :
{{
    "contre_indications_detectees": ["liste des contre-indications trouvées"],
    "niveau_risque": "faible/modéré/élevé",
    "recommandation": "ta recommandation en une phrase",
    "consulter_medecin": true
}}"""

        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        contenu = response.choices[0].message.content.strip()

        try:
            debut = contenu.find("{")
            fin = contenu.rfind("}") + 1
            return json.loads(contenu[debut:fin])
        except Exception:
            return {
                "contre_indications_detectees": [],
                "niveau_risque": "inconnu",
                "recommandation": contenu,
                "consulter_medecin": True
            }

    # ============================================================
    # GÉNÉRATION RÉPONSE FINALE
    # ============================================================
    def generer_reponse(self, question: str, profil_patient: str,
                        chunks_pertinents: list, analyse_ci: dict) -> str:
        """Génère la réponse finale en combinant RAG et analyse CI."""

        contexte = "\n\n".join([
            f"[{c['metadata']['medicament']} - {c['metadata']['section']}]\n{c['contenu']}"
            for c in chunks_pertinents
        ])

        prompt_systeme = """Tu es un assistant médical expert et bienveillant.
Réponds en français de manière claire et structurée.
Base-toi UNIQUEMENT sur les informations fournies dans le contexte.
Si l'information n'est pas dans le contexte, dis-le clairement.
Ne jamais inventer des informations médicales.
Cite toujours le nom du médicament dont tu parles."""

        prompt_user = f"""Profil patient : {profil_patient}

Question : {question}

Contexte médical :
{contexte}

Contre-indications détectées : {', '.join(analyse_ci.get('contre_indications_detectees', [])) or 'Aucune'}
Niveau de risque : {analyse_ci.get('niveau_risque', 'inconnu')}

Donne une réponse claire et utile basée sur ces informations."""

        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": prompt_systeme},
                {"role": "user", "content": prompt_user}
            ],
            max_tokens=800
        )

        return response.choices[0].message.content

    # ============================================================
    # MÉTHODE PRINCIPALE — appelée par Streamlit
    # ============================================================
    def interroger(self, question: str, profil_patient: str = "Non renseigné") -> dict:
        """
        Méthode principale appelée par le frontend.
        Retourne la réponse complète avec sources et scores.
        """
        # Recherche vectorielle
        chunks_pertinents = self.rechercher(question)

        # Agent 2 — Vérification contre-indications
        analyse_ci = self.agent_contre_indications(profil_patient, chunks_pertinents)

        # Génération réponse
        reponse = self.generer_reponse(question, profil_patient, chunks_pertinents, analyse_ci)

        return {
            "reponse": reponse,
            "sources": list(set([c["metadata"]["medicament"] for c in chunks_pertinents])),
            "scores": [c["score"] for c in chunks_pertinents],
            "contre_indications": analyse_ci.get("contre_indications_detectees", []),
            "niveau_risque": analyse_ci.get("niveau_risque", "inconnu"),
            "consulter_medecin": analyse_ci.get("consulter_medecin", True)
        }