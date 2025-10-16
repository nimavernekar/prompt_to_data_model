from __future__ import annotations
import os
from typing import List, Dict
import ollama

LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")


def chat(messages: List[Dict[str, str]]) -> str:
    """
    messages = [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "..."}
    ]
    """
    resp = ollama.chat(model=LLM_MODEL, messages=messages)
    return resp["message"]["content"]  # type: ignore
