from __future__ import annotations
from typing import List, Dict, Any
from app.services.embedding_service import embed_texts
from app.vectorstore import tiny_store
from app.utils import llama_client

SYSTEM_PROMPT = """
You are a helpful data assistant. Use the provided CONTEXT to answer faithfully.
If the context is insufficient, say you don't have enough information.
"""


def index_context(ctx: Dict[str, Any]):
    path = ctx.get("path")
    if tiny_store.already_indexed(path):
        return {"indexed": False, "reason": "already exists"}

    texts = [ctx["embed_text"]]
    vecs = embed_texts(texts)
    tiny_store.add(vecs, [{
        "path": ctx.get("path"),
        "type": ctx.get("type"),
        "summary": ctx.get("summary"),
        "embed_text": ctx.get("embed_text")
    }])
    return {"indexed": True}

def answer(query: str, top_k: int = 4) -> Dict[str, Any]:
    qvec = embed_texts([query])[0]
    hits = tiny_store.search(qvec, top_k=top_k)

    # Build context string from top matches
    ctx_sources = []
    for h in hits:
        # Use embedded text instead of summary
        embed_text = h.get("summary") if h.get("type") != "text" else None
        text = h.get("embed_text") if h.get("embed_text") else None

        # Try pulling full text or fallback to summary preview
        if text:
            ctx_sources.append(f"From file {h.get('path')}:\n{text}")
        else:
            ctx_sources.append(f"From file {h.get('path')}:\n{h.get('summary')}")
            
    ctx_text = "\n\n".join(ctx_sources) if ctx_sources else "<no context>"

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Use ONLY the provided context to answer. "
                "If the answer is in the document text, extract it directly."
            ),
        },
        {
            "role": "user",
            "content": (
                "The following context consists of file data. Use the content to answer.\n\n"
                f"{ctx_text}\n\n"
                f"Question: {query}"
            ),
        },
    ]
    completion = llama_client.chat(messages)
    return {"answer": completion, "context_used": hits}
