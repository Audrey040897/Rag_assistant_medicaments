# Rag_assistant_medicaments
# 💊 Assistant Médical RAG

Système de conseil médical multi-agents basé sur la **Base de Données Publique des Médicaments (BDPM)**.  
Construit sans LangChain ni LlamaIndex — chaque brique est implémentée manuellement.

> ⚠️ Cet assistant est un outil pédagogique. Il ne remplace pas l'avis d'un professionnel de santé.

---

## Architecture

```
CIS_RCP.html (BDPM)
      │
      ▼
parse_cis_rcp.py ──► CIS_RCP_export.xlsx
      │
      ▼
indexation.py ──► faiss_index/
                  ├── index.faiss
                  ├── chunks.json
                  └── metadata.json
      │
      ▼
┌─────────────────────────────────┐
│         main.py / app.py        │
│                                 │
│  Agent 1 — Collecte patient     │
│  (questions une par une)        │
│         │                       │
│         ▼ profil JSON           │
│  Agent 2 — Analyse & Match      │
│  (FAISS + re-scoring + LLM)     │
└─────────────────────────────────┘
```

---

## Structure du projet

```
rag-medicaments/
│
├── data/
│   ├── CIS_RCP.html              # fichier source BDPM (à télécharger)
│   └── CIS_RCP_export.xlsx       # produit par parse_cis_rcp.py
│
├── faiss_index/
│   ├── index.faiss               # base vectorielle
│   ├── chunks.json               # chunks + métadonnées
│   └── metadata.json             # modèle utilisé + stats
│
├── parse_cis_rcp.py              # HTML → Excel
├── indexation.py                 # Excel → FAISS
├── load_or_create_index.py       # chargement intelligent de la base
├── llm_client.py                 # connexion unique Groq (Singleton)
├── agent1.py                     # agent collecte patient
├── agent2.py                     # agent analyse & recommandation
├── main.py                       # interface terminal
├── app.py                        # interface Streamlit
├── config.py                     # configuration centralisée
├── context_agent1.txt            # prompt système agent 1
├── context_agent2.txt            # prompt système agent 2
│
├── .env                          # clé API (non versionné)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Installation

### 1. Cloner le projet

```bash
git clone <url-du-repo>
cd rag-medicaments
```

### 2. Créer l'environnement virtuel

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

`requirements.txt` :
```
groq
sentence-transformers
faiss-cpu
pandas
openpyxl
beautifulsoup4
lxml
python-dotenv
numpy
tqdm
streamlit
```

### 4. Configurer la clé API

Créer un fichier `.env` à la racine :
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
```

---

## Données

Télécharger le fichier source depuis :  
👉 [data.gouv.fr — Base de Données Publique des Médicaments](https://www.data.gouv.fr/fr/datasets/base-de-donnees-publique-des-medicaments-base-officielle/)

Placer le fichier `CIS_RCP.html` dans le dossier `data/`.

---

## Lancement

### Étape 1 — Parser les données (une fois)

```bash
python parse_cis_rcp.py

# Test sur 100 médicaments
python parse_cis_rcp.py --sample 100
```

Produit `data/CIS_RCP_export.xlsx` avec 15 649 médicaments.

### Étape 2 — Indexer la base vectorielle (une fois)

```bash
python indexation.py
```

⏱️ Durée estimée : ~2h pour 12 009 médicaments et 949 301 chunks.  
Les sauvegardes sont automatiques à chaque batch de 500 médicaments.

### Étape 3 — Lancer l'assistant

**Interface Streamlit (recommandée) :**
```bash
streamlit run app.py
```
Ouvre automatiquement http://localhost:8501

**Interface terminal :**
```bash
python main.py
```

---

## Configuration (`config.py`)

```python
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"  # modèle embedding
LLM_MODEL  = "llama-3.3-70b-versatile"                # modèle LLM Groq
```

---

## Fonctionnement des agents

### Agent 1 — Collecte patient
Pose les questions une par une et collecte :

| Champ | Obligatoire |
|---|---|
| Symptômes | ✅ |
| Âge / Poids | ✅ |
| Grossesse / Allaitement | ✅ |
| Médicaments en cours | ✅ |
| Allergies | ✅ |
| Antécédents | ⚪ optionnel |

Produit un JSON structuré transmis à l'Agent 2.

### Agent 2 — Analyse & Recommandation
Reçoit le profil patient et analyse dans cet ordre strict :

1. **Conditions de prescription** → ordonnance requise ?
2. **Contre-indications** → STOP si détectée
3. **Interactions médicamenteuses** → avec les médicaments en cours
4. **Grossesse / Allaitement** → si applicable
5. **Posologie** → adaptée à l'âge et au poids
6. **Effets indésirables** → à surveiller

**Re-scoring FAISS selon le profil :**

| Condition patient | Section boostée | Facteur |
|---|---|---|
| Enceinte | grossesse_allaitement | ×1.5 |
| Médicaments en cours | interactions | ×1.5 |
| Âge > 65 ans | mises_en_garde | ×1.3 |
| Tous | contre_indications | ×1.5 |
| Tous | conditions_prescription | ×1.5 |

---

## Résultats

| Métrique | Valeur |
|---|---|
| Médicaments indexés | 12 009 |
| Chunks total | 949 301 |
| Modèle embedding | paraphrase-multilingual-MiniLM-L12-v2 |
| LLM | LLaMA 3.3 70B via Groq |
| Interface | Streamlit |

---

## .gitignore

```
.env
data/
faiss_index/
__pycache__/
venv/
*.pkl
```