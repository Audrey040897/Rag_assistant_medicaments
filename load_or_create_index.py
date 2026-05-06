"""
load_or_create_index.py
Vérifie si la base vectorielle existe → la charge
Sinon → la crée via indexation.py
"""

import json
import subprocess
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer

FAISS_DIR   = Path("faiss_index")
INDEX_PATH  = FAISS_DIR / "index.faiss"
CHUNKS_PATH = FAISS_DIR / "chunks.json"
META_PATH   = FAISS_DIR / "metadata.json"


def load_index():
    """Charge l'index FAISS et les chunks depuis le disque."""
    print("📂 Chargement de la base vectorielle existante...")

    # Lire le modèle utilisé lors de l'indexation
    with open(META_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    model_name = metadata["model_name"]
    print(f"   Modèle utilisé : {model_name}")
    print(f"   Chunks : {metadata['total_chunks']}")
    print(f"   Indexé le : {metadata['date_indexation']}")

    # Charger le modèle d'embedding
    model = SentenceTransformer(model_name)

    # Charger l'index FAISS
    index = faiss.read_index(str(INDEX_PATH))

    # Charger les chunks
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"✅ Base chargée ({index.ntotal} vecteurs)\n")
    return model, index, chunks


def create_index():
    """Lance indexation.py pour créer la base."""
    print("⚙️  Base vectorielle introuvable → création en cours...")
    result = subprocess.run(["python", "indexation.py"], check=True)
    if result.returncode == 0:
        print("✅ Base créée avec succès !\n")
    else:
        raise RuntimeError("❌ Erreur lors de l'indexation")


def load_or_create_index():
    fichiers_requis = [INDEX_PATH, CHUNKS_PATH, META_PATH]
    tous_presents = all(f.exists() for f in fichiers_requis)

    if tous_presents:
        # ── Vérification taille minimale ──────────────────
        with open(META_PATH) as f:
            meta = json.load(f)
        if meta.get("total_chunks", 0) < 100000:
            print("⚠️  Index incomplet détecté → réindexation...")
            create_index()
        # ─────────────────────────────────────────────────
        return load_index()
    else:
        manquants = [f.name for f in fichiers_requis if not f.exists()]
        print(f"⚠️  Fichiers manquants : {manquants}")
        create_index()
        return load_index()


if __name__ == "__main__":
    model, index, chunks = load_or_create_index()
    print(f"Prêt ! Modèle : {type(model).__name__}, "
          f"Index : {index.ntotal} vecteurs, "
          f"Chunks : {len(chunks)}")