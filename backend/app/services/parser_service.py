from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict
import pandas as pd
import chardet

SUPPORTED = {".csv", ".json", ".xlsx", ".xls",".txt"}


def _infer_encoding(p: Path) -> str:
    with open(p, 'rb') as f:
        raw = f.read(100000)
    guess = chardet.detect(raw)
    return guess.get("encoding") or "utf-8"


def _read_tabular(p: Path) -> pd.DataFrame:
    ext = p.suffix.lower()
    if ext == ".csv":
        enc = _infer_encoding(p)
        return pd.read_csv(p, nrows=5000, encoding=enc)
    if ext in {".xlsx", ".xls"}:
        return pd.read_excel(p, nrows=5000)
    if ext == ".json":
        try:
            with open(p, 'r', encoding=_infer_encoding(p)) as f:
                first = f.read(1)
                f.seek(0)
                if first == '[':
                    return pd.json_normalize(json.load(f))
                else:
                    return pd.read_json(p, lines=True)
        except Exception:
            return pd.read_json(p)
    raise ValueError(f"Unsupported extension: {ext}")

def _read_text(p: Path) -> str:
    enc = _infer_encoding(p)
    with open(p, "r", encoding=enc) as f:
        return f.read()


def _summarize_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    cols = []
    sample_rows = df.head(5).to_dict(orient="records")
    for c in df.columns:
        s = df[c]
        dtype = str(s.dtype)
        nulls = int(s.isna().sum())
        unique = int(s.nunique(dropna=True))
        example = None
        for v in s.head(5):
            if pd.notna(v):
                example = v
                break
        cols.append({
            "name": c,
            "dtype": dtype,
            "nulls": nulls,
            "unique": unique,
            "example": example,
        })
    summary = {
        "n_rows": int(df.shape[0]),
        "n_cols": int(df.shape[1]),
        "columns": cols,
        "samples": sample_rows,
    }
    return summary


def extract_context(path: Path) -> Dict[str, Any]:
    ext = path.suffix.lower()

    if ext in {".csv", ".json", ".xlsx", ".xls"}:
        df = _read_tabular(path)
        summary = _summarize_dataframe(df)
        schema_lines = [
            f"{c['name']} ({c['dtype']}), nulls={c['nulls']}, unique={c['unique']} example={c['example']}"
            for c in summary["columns"]
        ]
        schema_text = "\n".join(schema_lines)
        content = {
            "type": "tabular",
            "path": str(path),
            "summary": summary,
            "embed_text": f"Table with {summary['n_rows']} rows and {summary['n_cols']} columns.\n" + schema_text,
        }

    elif ext == ".txt":
        text = _read_text(path)

        # Optional: trim text if extremely large
        MAX_CHARS = 8000  # safeguard limit
        embed_text = text[:MAX_CHARS]

        content = {
            "type": "text",
            "path": str(path),
            "summary": {
                "n_chars": len(text),
                "preview": text[:200]
            },
            "embed_text": f"Document notes:\n{embed_text}"
        }

    else:
        raise ValueError(f"File type {ext} not supported. Supported: {sorted(SUPPORTED)}")

    return content
