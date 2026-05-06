"""
app.py
Interface Streamlit pour l'assistant médical multi-agents.
Style médical professionnel — blanc et bleu.
"""

import json
import re
import streamlit as st
from load_or_create_index import load_or_create_index
from llm_client import get_client
from config import LLM_MODEL
from pathlib import Path

# ── Configuration de la page ───────────────────────────────
st.set_page_config(
    page_title="Assistant Médical",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personnalisé médical blanc/bleu ───────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');

/* Reset général */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Fond principal */
.stApp {
    background-color: #F0F4F8;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0A3D6B 0%, #1565C0 100%);
    border-right: none;
}
[data-testid="stSidebar"] * {
    color: white !important;
}
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: white !important;
    font-family: 'DM Serif Display', serif;
}

/* Titre principal */
.main-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.2rem;
    color: #0A3D6B;
    margin-bottom: 0.2rem;
}
.main-subtitle {
    font-size: 0.95rem;
    color: #5A7A9A;
    margin-bottom: 2rem;
    font-weight: 300;
}

/* Carte principale */
.card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    box-shadow: 0 2px 20px rgba(10, 61, 107, 0.08);
    margin-bottom: 1rem;
}

/* Messages chat */
.msg-agent {
    background: #E8F0FE;
    border-left: 4px solid #1565C0;
    border-radius: 0 12px 12px 12px;
    padding: 0.9rem 1.2rem;
    margin: 0.6rem 0;
    max-width: 80%;
    color: #1A2B4A;
    font-size: 0.95rem;
    line-height: 1.6;
}
.msg-user {
    background: #0A3D6B;
    border-radius: 12px 0 12px 12px;
    padding: 0.9rem 1.2rem;
    margin: 0.6rem 0 0.6rem auto;
    max-width: 75%;
    color: white;
    font-size: 0.95rem;
    line-height: 1.6;
    text-align: right;
}
.msg-system {
    background: #FFF8E1;
    border-left: 4px solid #F59E0B;
    border-radius: 0 12px 12px 12px;
    padding: 0.7rem 1rem;
    margin: 0.4rem 0;
    font-size: 0.85rem;
    color: #78550A;
}
.msg-warning {
    background: #FFF3F3;
    border-left: 4px solid #E53935;
    border-radius: 0 12px 12px 12px;
    padding: 0.9rem 1.2rem;
    margin: 0.6rem 0;
    font-size: 0.9rem;
    color: #B71C1C;
}

/* Avatar agent */
.agent-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #1565C0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.2rem;
}
.user-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #5A7A9A;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.2rem;
    text-align: right;
}

/* Badge profil */
.profil-badge {
    background: #E8F5E9;
    border: 1px solid #A5D6A7;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
    color: #2E7D32;
    margin-bottom: 0.5rem;
}
.profil-item {
    display: flex;
    justify-content: space-between;
    padding: 0.3rem 0;
    border-bottom: 1px solid #F0F4F8;
    font-size: 0.85rem;
}
.profil-key {
    color: #5A7A9A;
    font-weight: 500;
}
.profil-val {
    color: #1A2B4A;
    font-weight: 400;
}

/* Bouton reset */
.stButton button {
    background: #0A3D6B;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.5rem;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    transition: background 0.2s;
}
.stButton button:hover {
    background: #1565C0;
}

/* Input */
.stTextInput input, .stChatInput textarea {
    border: 1.5px solid #C5D8F0;
    border-radius: 10px;
    font-family: 'DM Sans', sans-serif;
}
.stTextInput input:focus, .stChatInput textarea:focus {
    border-color: #1565C0;
    box-shadow: 0 0 0 3px rgba(21,101,192,0.1);
}

/* Divider */
hr {
    border: none;
    border-top: 1px solid #E0EAF4;
    margin: 1.5rem 0;
}

/* Progress bar */
.etape-bar {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
}
.etape {
    flex: 1;
    height: 4px;
    border-radius: 2px;
    background: #C5D8F0;
}
.etape.active {
    background: #1565C0;
}
.etape.done {
    background: #43A047;
}
</style>
""", unsafe_allow_html=True)


# ── Chargement des ressources (une seule fois) ─────────────
@st.cache_resource
def init_system():
    """Charge la base vectorielle et le client LLM une seule fois."""
    model, index, chunks = load_or_create_index()
    client = get_client()
    return model, index, chunks, client


# ── Chargement des contextes ───────────────────────────────
CONTEXT_AGENT1 = Path("context_agent1.txt").read_text(encoding="utf-8")
CONTEXT_AGENT2 = Path("context_agent2.txt").read_text(encoding="utf-8")


# ── Fonctions utilitaires ──────────────────────────────────
def extraire_profil(texte: str) -> dict | None:
    try:
        match = re.search(r"\{.*\}", texte, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass
    return None


def rechercher_chunks(question: str, model, index, chunks, k: int = 8):
    import numpy as np
    vecteur = model.encode([question], normalize_embeddings=True)
    vecteur = np.array(vecteur, dtype="float32")
    scores, indices = index.search(vecteur, k)
    resultats = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        c = chunks[idx]
        resultats.append({
            "texte": c["texte"],
            "score": float(score),
            "score_final": float(score),
            "metadata": {
                "medicament": c["medicament"],
                "section": c["section"],
                "priority": c["priority"],
                "code_cis": c["code_cis"],
            }
        })
    return resultats


def rescore_chunks(chunks_results, patient_profile):
    for chunk in chunks_results:
        score    = chunk["score"]
        priority = chunk["metadata"]["priority"]
        section  = chunk["metadata"]["section"]
        if section == "contre_indications":       priority *= 1.5
        if section == "conditions_prescription":  priority *= 1.5
        if patient_profile.get("grossesse") and section == "grossesse_allaitement":
            priority *= 1.5
        if patient_profile.get("allaitement") and section == "grossesse_allaitement":
            priority *= 1.5
        if patient_profile.get("medicaments_en_cours") and section == "interactions":
            priority *= 1.5
        if patient_profile.get("age", 0) > 65 and section == "mises_en_garde":
            priority *= 1.3
        chunk["score_final"] = score * priority
    return sorted(chunks_results, key=lambda x: x["score_final"], reverse=True)


def appeler_agent1(messages, client):
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.3,
    )
    return response.choices[0].message.content


def appeler_agent2(patient_profile, question, model, index, chunks, client):
    requete = f"{question} {patient_profile.get('symptomes', '')}"
    chunks_trouves  = rechercher_chunks(requete, model, index, chunks)
    chunks_rescores = rescore_chunks(chunks_trouves, patient_profile)

    contexte = ""
    for i, c in enumerate(chunks_rescores, 1):
        m = c["metadata"]
        contexte += (
            f"\n--- Chunk {i} ---\n"
            f"Médicament : {m['medicament']}\n"
            f"Section    : {m['section']}\n"
            f"Contenu    : {c['texte']}\n"
        )

    prompt_user = (
        f"Profil patient :\n{json.dumps(patient_profile, ensure_ascii=False, indent=2)}\n\n"
        f"Question du patient : {question}\n\n"
        f"Chunks pertinents de la base BDPM :{contexte}"
    )

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": CONTEXT_AGENT2},
            {"role": "user",   "content": prompt_user},
        ],
        temperature=0.1,
    )
    return response.choices[0].message.content


# ── Initialisation du session state ───────────────────────
def init_session():
    defaults = {
        "phase":       "collecte",   # collecte | questions
        "messages_a1": [],           # historique agent1
        "messages_ui": [],           # messages affichés dans le chat
        "profil":      None,         # profil patient JSON
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Sidebar ────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("## 💊 Assistant\nMédical")
        st.markdown("---")

        # Étapes
        phase = st.session_state.phase
        st.markdown("### Étapes")
        st.markdown(
            f"{'✅' if phase == 'questions' else '🔵'} **1. Collecte patient**\n\n"
            f"{'🔵' if phase == 'questions' else '⚪'} **2. Conseils médicaments**"
        )
        st.markdown("---")

        # Profil patient si disponible
        if st.session_state.profil:
            st.markdown("### 👤 Profil patient")
            p = st.session_state.profil
            infos = {
                "Symptômes":   p.get("symptomes", "—"),
                "Âge":         f"{p.get('age', '—')} ans",
                "Poids":       f"{p.get('poids', '—')} kg",
                "Grossesse":   "Oui" if p.get("grossesse") else "Non",
                "Allaitement": "Oui" if p.get("allaitement") else "Non",
                "Médicaments": ", ".join(p.get("medicaments_en_cours", [])) or "Aucun",
                "Allergies":   ", ".join(p.get("allergies", [])) or "Aucune",
            }
            for k, v in infos.items():
                st.markdown(f"**{k}** : {v}")

        st.markdown("---")

        # Bouton reset
        if st.button("🔄 Nouvelle consultation"):
            for k in ["phase", "messages_a1", "messages_ui", "profil"]:
                del st.session_state[k]
            st.rerun()

        st.markdown("---")
        st.markdown(
            "<small>⚠️ Cet assistant ne remplace pas un professionnel de santé.</small>",
            unsafe_allow_html=True
        )


# ── Affichage des messages ─────────────────────────────────
def render_messages():
    for msg in st.session_state.messages_ui:
        role    = msg["role"]
        content = msg["content"]

        if role == "agent1":
            st.markdown('<div class="agent-label">🤖 Assistant — Collecte</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="msg-agent">{content}</div>', unsafe_allow_html=True)
        elif role == "agent2":
            st.markdown('<div class="agent-label">💊 Assistant — Conseil</div>', unsafe_allow_html=True)
            if "⚠️" in content:
                st.markdown(f'<div class="msg-warning">{content}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="msg-agent">{content}</div>', unsafe_allow_html=True)
        elif role == "user":
            st.markdown('<div class="user-label">Vous</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="msg-user">{content}</div>', unsafe_allow_html=True)
        elif role == "system":
            st.markdown(f'<div class="msg-system">{content}</div>', unsafe_allow_html=True)


# ── Page principale ────────────────────────────────────────
def main():
    init_session()

    # Chargement système
    with st.spinner("Chargement du système..."):
        model, index, chunks, client = init_system()

    # Sidebar
    render_sidebar()

    # Header
    st.markdown('<h1 class="main-title">💊 Assistant Médical</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="main-subtitle">Conseils sur les médicaments basés sur la Base de Données Publique des Médicaments (BDPM)</p>',
        unsafe_allow_html=True
    )

    # Barre de progression
    phase = st.session_state.phase
    st.markdown(
        f'<div class="etape-bar">'
        f'<div class="etape {"done" if phase == "questions" else "active"}"></div>'
        f'<div class="etape {"active" if phase == "questions" else ""}"></div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Zone de chat
    with st.container():
        render_messages()

    st.markdown("---")

    # ── PHASE COLLECTE (Agent 1) ───────────────────────────
    if phase == "collecte":

        # Premier message de l'agent si chat vide
        if not st.session_state.messages_a1:
            st.session_state.messages_a1 = [
                {"role": "system", "content": CONTEXT_AGENT1}
            ]
            with st.spinner(""):
                reply = appeler_agent1(st.session_state.messages_a1, client)
            st.session_state.messages_a1.append({"role": "assistant", "content": reply})
            st.session_state.messages_ui.append({"role": "agent1", "content": reply})
            st.rerun()

        # Input patient
        user_input = st.chat_input("Votre réponse...")
        if user_input:
            # Ajouter message utilisateur
            st.session_state.messages_ui.append({"role": "user", "content": user_input})
            st.session_state.messages_a1.append({"role": "user", "content": user_input})

            # Réponse agent 1
            with st.spinner("L'assistant réfléchit..."):
                reply = appeler_agent1(st.session_state.messages_a1, client)

            st.session_state.messages_a1.append({"role": "assistant", "content": reply})

            # Collecte terminée ?
            if "[COLLECTE_TERMINEE]" in reply:
                profil = extraire_profil(reply)
                st.session_state.profil = profil
                st.session_state.phase  = "questions"

                # Message propre sans JSON
                message_propre = re.sub(r"\{.*\}", "", reply, flags=re.DOTALL)
                message_propre = message_propre.replace("[COLLECTE_TERMINEE]", "").strip()
                if message_propre:
                    st.session_state.messages_ui.append({"role": "agent1", "content": message_propre})

                st.session_state.messages_ui.append({
                    "role": "system",
                    "content": "✅ Profil collecté ! Vous pouvez maintenant poser vos questions sur les médicaments."
                })
            else:
                st.session_state.messages_ui.append({"role": "agent1", "content": reply})

            st.rerun()

    # ── PHASE QUESTIONS (Agent 2) ──────────────────────────
    elif phase == "questions":

        user_input = st.chat_input("Posez votre question sur un médicament...")
        if user_input:
            st.session_state.messages_ui.append({"role": "user", "content": user_input})

            with st.spinner("Recherche dans la base BDPM..."):
                reponse = appeler_agent2(
                    patient_profile=st.session_state.profil,
                    question=user_input,
                    model=model,
                    index=index,
                    chunks=chunks,
                    client=client,
                )

            st.session_state.messages_ui.append({"role": "agent2", "content": reponse})
            st.rerun()


if __name__ == "__main__":
    main()