import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import os

# ============================================================
# CONFIG
# ============================================================
DATA_PATH = "data/cisdata.xlsx"
INDEX_PATH = "data/faiss_index.bin"
CHUNKS_PATH = "data/chunks_meta.json"

# ============================================================
# CHUNKING
# ============================================================
def creer_chunks(df):
    chunks = []

    sections = [
        ("conditions_prescription", "Conditions de prescription"),
        ("contre_indications", "Contre-indications"),
        ("grossesse_allaitement", "Grossesse et allaitement"),
        ("effets_indesirables", "Effets indésirables"),
        ("posologie", "Posologie"),
        ("indications", "Indications"),
        ("interactions", "Interactions"),
    ]

    for _, row in df.iterrows():
        code = row["code_cis"]
        nom = str(row.get("denomination", ""))

        for champ, label in sections:
            contenu = row.get(champ, "")

            if pd.isna(contenu):
                continue

            contenu = str(contenu).strip()

            if len(contenu) < 20:
                continue

            chunks.append({
                "id": f"{code}_{champ}",
                "contenu": f"{nom}\n{label}\n{contenu}",
                "metadata": {
                    "code_cis": code,
                    "medicament": nom,
                    "section": champ
                }
            })

    return chunks

# ============================================================
# EMBEDDING
# ============================================================
def embedder(chunks, model):
    texts = [c["contenu"] for c in chunks]
    vectors = model.encode(texts, batch_size=32, show_progress_bar=True)
    return np.array(vectors, dtype=np.float32)

# ============================================================
# FAISS
# ============================================================
def build_index(vectors):
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    return index

# ============================================================
# SAVE
# ============================================================
def save(index, chunks):
    os.makedirs("data", exist_ok=True)

    faiss.write_index(index, INDEX_PATH)

    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":

    print("📂 Chargement data...")
    df = pd.read_excel(DATA_PATH)

    print(df.columns)
    print("Total :", len(df))

    # ❌ PAS DE FILTRE (IMPORTANT)
    df = df.dropna(subset=["code_cis"])

    print("\n✂️ chunking...")
    chunks = creer_chunks(df)

    print("chunks :", len(chunks))

    if len(chunks) == 0:
        raise ValueError("❌ Aucun chunk → problème dataset")

    print("\n🤖 embedding...")
    model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

    vectors = embedder(chunks, model)
    print("shape :", vectors.shape)

    print("\n📊 FAISS...")
    index = build_index(vectors)

    print("saved...")

    save(index, chunks)

    print("🎉 DONE")