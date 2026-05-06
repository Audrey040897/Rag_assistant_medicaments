import streamlit as st
from sentence_transformers import SentenceTransformer
from rag import RAGAssistant

@st.cache_resource
def charger_rag():
    """Instanciation unique du RAGAssistant — connexion unique à Groq."""
    return RAGAssistant()

rag = charger_rag()

# ============================================================
# CONFIGURATION DE LA PAGE
# ============================================================
st.set_page_config(
    page_title="Assistant Médicaments",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS PERSONNALISÉ
# ============================================================
st.markdown("""
<style>
    /* Fond général blanc */
    .stApp {
        background-color: #f8fafc;
        color: #1e293b;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    /* Logo container */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 0 20px 0;
    }

    .logo-icon {
        width: 48px;
        height: 48px;
        background-color: #0f3460;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        flex-shrink: 0;
    }

    .logo-text-main {
        font-size: 18px;
        font-weight: 600;
        color: #0f3460;
        line-height: 1.2;
    }

    .logo-text-sub {
        font-size: 12px;
        color: #00d4aa;
        font-weight: 500;
    }

    /* Messages utilisateur */
    .user-message {
        background: #0f3460;
        border-radius: 18px 18px 4px 18px;
        padding: 12px 18px;
        margin: 6px 0 6px 15%;
        color: white;
        font-size: 15px;
        line-height: 1.6;
    }

    /* Messages assistant */
    .assistant-message {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #00d4aa;
        border-radius: 4px 18px 18px 18px;
        padding: 14px 18px;
        margin: 6px 15% 6px 0;
        color: #1e293b;
        font-size: 15px;
        line-height: 1.7;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }

    /* Avatar assistant */
    .assistant-avatar {
        width: 32px;
        height: 32px;
        background: #0f3460;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 16px;
        margin-bottom: 4px;
    }

    /* Avertissement médical */
    .warning-medical {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        border-radius: 8px;
        padding: 10px 14px;
        margin: 8px 15% 8px 0;
        color: #9a3412;
        font-size: 13px;
        display: flex;
        align-items: flex-start;
        gap: 8px;
    }

    /* Sources */
    .sources-box {
        background: #f0fdf9;
        border: 1px solid #99f6e4;
        border-radius: 8px;
        padding: 8px 14px;
        margin: 4px 15% 4px 0;
        font-size: 13px;
        color: #0f766e;
    }

    /* Score badges */
    .score-badge {
        display: inline-block;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 12px;
        color: #1d4ed8;
        margin-right: 6px;
        margin-top: 4px;
    }

    .score-container {
        margin: 4px 15% 8px 0;
    }

    /* Bouton envoyer */
    div[data-testid="stButton"] button {
        background-color: #00d4aa !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        transition: background-color 0.2s !important;
    }

    div[data-testid="stButton"] button:hover {
        background-color: #0f9a7e !important;
    }

    /* Input */
    div[data-testid="stTextInput"] input {
        border-radius: 10px !important;
        border: 1.5px solid #e2e8f0 !important;
        padding: 10px 16px !important;
        font-size: 15px !important;
        background: white !important;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #00d4aa !important;
        box-shadow: 0 0 0 3px rgba(0, 212, 170, 0.15) !important;
    }

    /* Tag médicament sidebar */
    .med-tag {
        display: inline-block;
        background: #f0fdf9;
        border: 1px solid #99f6e4;
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 12px;
        color: #0f766e;
        margin: 3px 3px 0 0;
    }

    /* Divider */
    hr {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 16px 0;
    }

    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #0f3460 0%, #1a5276 100%);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        color: white;
        display: flex;
        align-items: center;
        gap: 20px;
    }

    .main-header-icon {
        font-size: 48px;
    }

    .main-header-title {
        font-size: 26px;
        font-weight: 700;
        margin: 0;
    }

    .main-header-sub {
        font-size: 14px;
        opacity: 0.8;
        margin: 4px 0 0 0;
    }

    /* Message de bienvenue */
    .welcome-message {
        background: #f0fdf9;
        border: 1px solid #99f6e4;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 16px;
        color: #0f766e;
        font-size: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    # Logo
    st.markdown("""
    <div class="logo-container">
        <div class="logo-icon">⚕️</div>
        <div>
            <div class="logo-text-main">Assistant<br>Médicaments</div>
            <div class="logo-text-sub">Powered by BDPM + Groq</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("**📋 À propos**")
    st.markdown("""
    <div style="font-size:13px; color:#64748b; line-height:1.6;">
    Cet assistant répond à vos questions sur les médicaments en s'appuyant sur la 
    <strong>Base de Données Publique des Médicaments (BDPM)</strong>.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("**💊 Médicaments disponibles**")
    medicaments = [
        "Paracétamol", "Dafalgan", "Efferalgan",
        "Ibuprofène", "Advil", "Nurofen",
        "Aspirine", "Aspégic", "Amoxicilline",
        "Augmentin", "Smecta", "Imodium",
        "Ventoline", "Becotide", "Oméprazole",
        "Inexium", "Metformine", "Glucophage"
    ]
    tags_html = "".join([f'<span class="med-tag">{m}</span>' for m in medicaments])
    st.markdown(f'<div style="line-height:2">{tags_html}</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("**⚙️ Paramètres**")
    show_scores = st.toggle("Scores de similarité", value=True)
    show_sources = st.toggle("Sources", value=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    if st.button("🗑️ Effacer la conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ============================================================
# HEADER PRINCIPAL
# ============================================================
st.markdown("""
<div class="main-header">
    <div class="main-header-icon">⚕️</div>
    <div>
        <p class="main-header-title">Assistant Médicaments</p>
        <p class="main-header-sub">
            Posez vos questions sur les effets secondaires, posologies,
            contre-indications et interactions médicamenteuses.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# INITIALISATION HISTORIQUE
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ============================================================
# MESSAGE DE BIENVENUE
# ============================================================
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-message">
        👋 Bonjour ! Je suis votre assistant médicaments.<br>
        Je peux vous renseigner sur les <strong>effets secondaires</strong>,
        <strong>posologies</strong>, <strong>contre-indications</strong>
        et <strong>interactions</strong> des médicaments courants.<br><br>
        Exemple : <em>"Quels sont les effets secondaires du Paracétamol ?"</em>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# AFFICHAGE HISTORIQUE
# ============================================================
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="user-message">
            <strong>Vous</strong><br>{message["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="assistant-message">
            <strong>⚕️ Assistant</strong><br><br>{message["content"]}
        </div>
        """, unsafe_allow_html=True)

        if show_scores and message.get("scores"):
            badges = "".join([
                f'<span class="score-badge">Score {i+1} : {s:.2f}</span>'
                for i, s in enumerate(message["scores"])
            ])
            st.markdown(
                f'<div class="score-container">{badges}</div>',
                unsafe_allow_html=True
            )

        if show_sources and message.get("sources"):
            sources_text = " &nbsp;|&nbsp; ".join(message["sources"])
            st.markdown(f"""
            <div class="sources-box">
                📚 <strong>Sources :</strong> {sources_text}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div class="warning-medical">
            ⚠️ <span>Ces informations ne remplacent pas l'avis d'un professionnel de santé.
            En cas de doute, consultez votre médecin ou votre pharmacien.</span>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# ZONE DE SAISIE
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)
col1, col2 = st.columns([6, 1])

with col1:
    question = st.text_input(
        "",
        placeholder="Ex: Quels sont les effets secondaires du Paracétamol ?",
        key="input_question",
        label_visibility="collapsed"
    )

with col2:
    envoyer = st.button("Envoyer ➤", use_container_width=True)

# ============================================================
# TRAITEMENT
# ============================================================
if envoyer and question.strip():

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.spinner("🔍 Recherche dans la base médicaments..."):

        resultat = rag.interroger(
            question=question,
            profil_patient=st.session_state.get("profil_patient", "Non renseigné")
        )

        reponse = resultat["reponse"]
        scores = resultat["scores"]
        sources = resultat["sources"]

    st.session_state.messages.append({
        "role": "assistant",
        "content": reponse,
        "scores": scores,
        "sources": sources
    })

    st.rerun()