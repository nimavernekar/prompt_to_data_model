from __future__ import annotations
import os
from typing import List
import numpy as np
import ollama

EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Uses Ollama's embedding model to convert a list of texts
    into a NumPy array of shape (n_texts, embedding_dim).
    """
    vecs = []
    for t in texts:
        try:
            resp = ollama.embeddings(model=EMBED_MODEL, prompt=t)
        except Exception as e:
            print(f"Embedding error: {e}")
            raise

        vecs.append(resp["embedding"])  # type: ignore
    return np.array(vecs, dtype=np.float32)
