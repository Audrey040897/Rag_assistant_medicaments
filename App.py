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

# ── CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background-color: #F0F4F8; }

[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0A3D6B 0%, #1565C0 100%);
}
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: white !important;
    font-family: 'DM Serif Display', serif;
}

/* Titre */
.main-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.4rem;
    color: #1565C0;
    margin-bottom: 0.1rem;
}
.main-title span { color: #0A3D6B; }
.main-subtitle {
    font-size: 0.92rem;
    color: #5A7A9A;
    margin-bottom: 1.5rem;
    font-weight: 300;
}

/* Section médicaments */
.meds-wrapper {
    background: white;
    border-radius: 16px;
    padding: 1.2rem 1.5rem 1rem 1.5rem;
    box-shadow: 0 2px 16px rgba(10,61,107,0.07);
    margin-bottom: 1.5rem;
}
.meds-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
}
.meds-header-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #0A3D6B;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.meds-header-sub {
    font-size: 0.78rem;
    color: #5A7A9A;
    margin-left: auto;
}
.meds-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.8rem;
}
.meds-cat {
    background: #F0F4F8;
    border-radius: 10px;
    padding: 0.7rem 0.9rem;
}
.meds-cat-title {
    font-size: 0.75rem;
    font-weight: 600;
    color: #0A3D6B;
    margin-bottom: 0.4rem;
}
.meds-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
}
.badge {
    background: white;
    border: 1.5px solid #C5D8F0;
    border-radius: 20px;
    padding: 0.2rem 0.6rem;
    font-size: 0.78rem;
    color: #1565C0;
    font-weight: 500;
    display: inline-block;
}

/* Messages */
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

/* Boutons */
.stButton button {
    background: #0A3D6B;
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
}
.stButton button:hover { background: #1565C0; }

hr { border: none; border-top: 1px solid #E0EAF4; margin: 1.2rem 0; }

.etape-bar { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
.etape { flex: 1; height: 4px; border-radius: 2px; background: #C5D8F0; }
.etape.active { background: #1565C0; }
.etape.done { background: #43A047; }
</style>
""", unsafe_allow_html=True)

# ── Médicaments exemples ───────────────────────────────────
MEDICAMENTS_EXEMPLES = {
    "💊 Antidouleurs":      ["Doliprane", "Ibuprofène", "Aspirine", "Advil"],
    "🦠 Antibiotiques":     ["Amoxicilline", "Augmentin", "Azithromycine"],
    "🫀 Cardio":            ["Kardégic", "Plavix", "Amlodipine"],
    "🧠 Neurologie":        ["Sertraline", "Bromazépam", "Gabapentine"],
    "🤧 Allergie":          ["Cetirizine", "Loratadine", "Fexofénadine"],
    "🫁 Respiratoire":      ["Ventoline", "Becotide", "Seretide"],
    "🍽️ Digestif":          ["Smecta", "Imodium", "Oméprazole"],
    "🩺 Diabète":           ["Metformine", "Glucophage", "Insuline"],
}


@st.cache_resource
def init_system():
    model, index, chunks = load_or_create_index()
    client = get_client()
    return model, index, chunks, client


CONTEXT_AGENT1 = Path("context_agent1.txt").read_text(encoding="utf-8")
CONTEXT_AGENT2 = Path("context_agent2.txt").read_text(encoding="utf-8")
SCORE_CONFIANCE_MIN = 0.30


def extraire_profil(texte):
    try:
        match = re.search(r"\{.*\}", texte, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass
    return None


def rechercher_chunks(question, model, index, chunks, k=8):
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
                "section":    c["section"],
                "priority":   c["priority"],
                "code_cis":   c["code_cis"],
            }
        })
    return resultats


def rescore_chunks(chunks_results, patient_profile):
    for chunk in chunks_results:
        score    = chunk["score"]
        priority = chunk["metadata"]["priority"]
        section  = chunk["metadata"]["section"]
        if section == "contre_indications":      priority *= 1.5
        if section == "conditions_prescription": priority *= 1.5
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
        model=LLM_MODEL, messages=messages, temperature=0.3,
    )
    return response.choices[0].message.content


def appeler_agent2(patient_profile, question, model, index, chunks, client):
    requete         = f"{question} {patient_profile.get('symptomes', '')}"
    chunks_trouves  = rechercher_chunks(requete, model, index, chunks)
    chunks_rescores = rescore_chunks(chunks_trouves, patient_profile)

    meilleur_score = chunks_rescores[0]["score"] if chunks_rescores else 0.0
    st.session_state.dernier_score = meilleur_score

    if meilleur_score < SCORE_CONFIANCE_MIN:
        return (
            f"⚠️ Je n'ai pas trouvé d'information suffisamment pertinente "
            f"dans ma base pour cette question "
            f"(score de confiance : {meilleur_score:.2f} / 1.00).\n\n"
            f"Le médicament demandé n'est peut-être pas dans ma base.\n\n"
            f"⚠️ Ces informations ne remplacent pas l'avis d'un professionnel "
            f"de santé. Consultez votre médecin ou pharmacien."
        )

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


def init_session():
    defaults = {
        "phase":         "collecte",
        "messages_a1":   [],
        "messages_ui":   [],
        "profil":        None,
        "dernier_score": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_sidebar():
    with st.sidebar:
        st.markdown("## 💊 Assistant\nMédical")
        st.markdown("---")

        phase = st.session_state.phase
        st.markdown("### Étapes")
        st.markdown(
            f"{'✅' if phase == 'questions' else '🔵'} **1. Collecte patient**\n\n"
            f"{'🔵' if phase == 'questions' else '⚪'} **2. Conseils médicaments**"
        )

        if st.session_state.dernier_score is not None:
            score = st.session_state.dernier_score
            st.markdown("---")
            st.markdown("### 📊 Dernière recherche")
            if score >= 0.50:
                st.markdown(f"🟢 Score : **{score:.2f}** — Fiable")
            elif score >= 0.30:
                st.markdown(f"🟡 Score : **{score:.2f}** — Acceptable")
            else:
                st.markdown(f"🔴 Score : **{score:.2f}** — Peu fiable")

        if st.session_state.profil:
            st.markdown("---")
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
        if st.button("🔄 Nouvelle consultation"):
            for k in ["phase", "messages_a1", "messages_ui", "profil", "dernier_score"]:
                del st.session_state[k]
            st.rerun()

        st.markdown(
            "<small>⚠️ Cet assistant ne remplace pas un professionnel de santé.</small>",
            unsafe_allow_html=True
        )


def render_medicaments_exemples():
    st.markdown("""
    <div class="meds-wrapper">
        <div class="meds-header">
            <span class="meds-header-title">💡 Médicaments disponibles dans la base</span>
            <span class="meds-header-sub">12 009 médicaments indexés — BDPM</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Grille 4 colonnes avec composants natifs Streamlit
    cats = list(MEDICAMENTS_EXEMPLES.items())
    for row_start in range(0, len(cats), 4):
        cols = st.columns(4)
        for col_idx, col in enumerate(cols):
            idx = row_start + col_idx
            if idx >= len(cats):
                break
            categorie, meds = cats[idx]
            with col:
                badges_html = "".join([
                    f'<span class="badge">{m}</span>' for m in meds
                ])
                st.markdown(f"""
                <div class="meds-cat">
                    <div class="meds-cat-title">{categorie}</div>
                    <div class="meds-badges">{badges_html}</div>
                </div>
                """, unsafe_allow_html=True)


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


def main():
    init_session()

    with st.spinner("Chargement du système..."):
        model, index, chunks, client = init_system()

    render_sidebar()

    # ── Header ────────────────────────────────────────────
    st.markdown(
        '<h1 class="main-title">💊 <span>Assistant</span> Médical</h1>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p class="main-subtitle">Conseils sur les médicaments — Base de Données Publique des Médicaments (BDPM)</p>',
        unsafe_allow_html=True
    )

    # ── Barre de progression ──────────────────────────────
    phase = st.session_state.phase
    st.markdown(
        f'<div class="etape-bar">'
        f'<div class="etape {"done" if phase == "questions" else "active"}"></div>'
        f'<div class="etape {"active" if phase == "questions" else ""}"></div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── Médicaments exemples — toujours visible ───────────
    render_medicaments_exemples()

    # ── Zone de chat ──────────────────────────────────────
    render_messages()
    st.markdown("---")

    # ── PHASE COLLECTE ────────────────────────────────────
    if phase == "collecte":
        if not st.session_state.messages_a1:
            st.session_state.messages_a1 = [
                {"role": "system", "content": CONTEXT_AGENT1}
            ]
            with st.spinner(""):
                reply = appeler_agent1(st.session_state.messages_a1, client)
            st.session_state.messages_a1.append({"role": "assistant", "content": reply})
            st.session_state.messages_ui.append({"role": "agent1", "content": reply})
            st.rerun()

        user_input = st.chat_input("Votre réponse...")
        if user_input:
            st.session_state.messages_ui.append({"role": "user", "content": user_input})
            st.session_state.messages_a1.append({"role": "user", "content": user_input})

            with st.spinner("L'assistant réfléchit..."):
                reply = appeler_agent1(st.session_state.messages_a1, client)

            st.session_state.messages_a1.append({"role": "assistant", "content": reply})

            if "[COLLECTE_TERMINEE]" in reply:
                profil = extraire_profil(reply)
                st.session_state.profil = profil
                st.session_state.phase  = "questions"

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

    # ── PHASE QUESTIONS ───────────────────────────────────
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