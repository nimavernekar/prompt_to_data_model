from __future__ import annotations
import os
import json
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

STORE_DIR = Path("backend/data/vectorstore")
STORE_DIR.mkdir(parents=True, exist_ok=True)
VECTORS_NPZ = STORE_DIR / "vectors.npz"
META_JSON = STORE_DIR / "meta.json"


def _load() -> (np.ndarray, List[Dict[str, Any]]):
    if VECTORS_NPZ.exists():
        arr = np.load(VECTORS_NPZ)["arr"]
    else:
        arr = np.zeros((0, 768), dtype=np.float32)  # default dim placeholder
    if META_JSON.exists():
        meta = json.loads(META_JSON.read_text())
    else:
        meta = []
    return arr, meta


def _save(vecs: np.ndarray, meta: List[Dict[str, Any]]):
    np.savez_compressed(VECTORS_NPZ, arr=vecs)
    META_JSON.write_text(json.dumps(meta, indent=2))


def add(vectors: np.ndarray, metadatas: List[Dict[str, Any]]):
    assert vectors.shape[0] == len(metadatas)
    cur, meta = _load()

    new_vecs = []
    new_meta = []

    for vec, m in zip(vectors, metadatas):
        if not any(entry.get("path") == m.get("path") for entry in meta):
            new_vecs.append(vec)
            new_meta.append(m)

    if not new_vecs:
        return  # nothing new to add

    new_vecs = np.array(new_vecs, dtype=np.float32)

    if cur.size == 0:
        updated_vecs = new_vecs
    else:
        updated_vecs = np.vstack([cur, new_vecs])

    meta.extend(new_meta)
    _save(updated_vecs, meta)




def search(query_vec: np.ndarray, top_k: int = 4) -> List[Dict[str, Any]]:
    vecs, meta = _load()
    if vecs.shape[0] == 0:
        return []
    sims = cosine_similarity(query_vec.reshape(1, -1), vecs)[0]
    idx = np.argsort(-sims)[:top_k]
    results = []
    for i in idx:
        item = meta[i].copy()
        item["score"] = float(sims[i])
        results.append(item)
    return results

def clear():
    """Remove all vectors and metadata from the local store."""
    if VECTORS_NPZ.exists():
        VECTORS_NPZ.unlink()
    if META_JSON.exists():
        META_JSON.unlink()

def already_indexed(path: str) -> bool:
    _, meta = _load()
    return any(entry.get("path") == path for entry in meta)
