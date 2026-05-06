"""
indexation.py
Lit CIS_RCP_export.xlsx → chunks → embeddings → sauvegarde FAISS
"""

import json
from pathlib import Path
from datetime import datetime

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from config import MODEL_NAME

# ── Chemins ────────────────────────────────────────────────
EXCEL_PATH  = Path("data/CIS_RCP_export.xlsx")
FAISS_DIR   = Path("faiss_index")
INDEX_PATH  = FAISS_DIR / "index.faiss"
CHUNKS_PATH = FAISS_DIR / "chunks.json"
META_PATH   = FAISS_DIR / "metadata.json"

# ── Priorités et tailles de chunks par section ─────────────
SECTION_CONFIG = {
    "contre_indications":      {"priority": 1.0, "taille_max": 300},
    "grossesse_allaitement":   {"priority": 1.0, "taille_max": 300},
    "interactions":            {"priority": 1.0, "taille_max": 300},
    "conditions_prescription": {"priority": 1.0, "taille_max": 300},
    "mises_en_garde":          {"priority": 0.9, "taille_max": 300},
    "posologie":               {"priority": 0.7, "taille_max": 500},
    "effets_indesirables":     {"priority": 0.6, "taille_max": 500},
    "surdosage":               {"priority": 0.5, "taille_max": 500},
    "indications":             {"priority": 0.4, "taille_max": 700},
    "composition":             {"priority": 0.2, "taille_max": 700},
    "forme_pharmaceutique":    {"priority": 0.2, "taille_max": 700},
}

OVERLAP = 50


def chunker(texte: str, taille_max: int, overlap: int = OVERLAP) -> list[str]:
    """Découpe un texte en chunks avec chevauchement."""
    if not texte or not texte.strip():
        return []
    chunks = []
    start = 0
    while start < len(texte):
        end = start + taille_max
        chunks.append(texte[start:end].strip())
        start += taille_max - overlap
    return [c for c in chunks if c]


def build_chunks(df: pd.DataFrame) -> list[dict]:
    """Construit la liste complète des chunks avec métadonnées."""
    all_chunks = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Chunking"):
        medicament = str(row.get("denomination", "")).strip()
        code_cis   = str(row.get("code_cis", "")).strip()

        if not medicament or medicament == "nan":
            continue

        for section, config in SECTION_CONFIG.items():
            texte = str(row.get(section, "")).strip()
            if not texte or texte == "nan":
                continue

            morceaux = chunker(texte, config["taille_max"])
            for morceau in morceaux:
                all_chunks.append({
                    "texte":      morceau,
                    "medicament": medicament,
                    "code_cis":   code_cis,
                    "section":    section,
                    "priority":   config["priority"],
                })

    return all_chunks


def main():
    print(f"Lecture de {EXCEL_PATH}...")
    df = pd.read_excel(EXCEL_PATH, engine="openpyxl")
    df = df.dropna(subset=["denomination"])
    print(f"{len(df)} médicaments chargés.\n")

    FAISS_DIR.mkdir(exist_ok=True)
    model = SentenceTransformer(MODEL_NAME)

    index      = None
    all_chunks = []
    BATCH_SIZE = 500

    for i in range(0, len(df), BATCH_SIZE):
        batch = df.iloc[i:i + BATCH_SIZE]
        print(f"\n📦 Batch {i//BATCH_SIZE + 1}/{-(-len(df)//BATCH_SIZE)} "
              f"({i}→{min(i+BATCH_SIZE, len(df))})")

        # ── Chunking ──────────────────────────────────────
        chunks = build_chunks(batch)
        print(f"   {len(chunks)} chunks")

        # ── Embedding ─────────────────────────────────────
        textes  = [c["texte"] for c in chunks]
        vectors = model.encode(
            textes,
            batch_size=64,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        vectors = np.array(vectors, dtype=np.float32)

        # ── Ajout à l'index FAISS ─────────────────────────
        if index is None:
            index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        all_chunks.extend(chunks)

        # ── Sauvegarde intermédiaire ───────────────────────
        faiss.write_index(index, str(INDEX_PATH))
        with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, ensure_ascii=False)

        print(f"   ✅ Sauvegarde intermédiaire ({len(all_chunks)} chunks total)")

    # ── Résumé final ──────────────────────────────────────
    print(f"\n✅ Indexation complète ! {len(all_chunks)} chunks — {index.ntotal} vecteurs")

    # ── Sauvegarde metadata ───────────────────────────────
    metadata = {
        "model_name":        MODEL_NAME,
        "total_chunks":      len(all_chunks),
        "total_vecteurs":    index.ntotal,
        "date_indexation":   datetime.now().isoformat(),
        "nb_medicaments":    len(df),
        "sections_indexees": list(SECTION_CONFIG.keys()),
    }
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"✅ Metadata sauvegardée → {META_PATH}")


if __name__ == "__main__":
    main()