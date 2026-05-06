# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# MODÈLES
# ============================================================
LLM_MODEL = "llama-3.3-70b-versatile"
EMBEDDING_MODEL = "paraphrase-multilingual-mpnet-base-v2"

# ============================================================
# CHEMINS
# ============================================================
DATA_PATH = "data/cisdata.xlsx"
INDEX_PATH = "data/faiss_index.bin"
CHUNKS_PATH = "data/chunks_meta.json"

# ============================================================
# PARAMÈTRES RAG
# ============================================================
N_MEDICAMENTS = None  # None = tout le fichier
TOP_K = 4
BATCH_SIZE = 32

# ============================================================
# API
# ============================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")