from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import parser_service, rag_service

router = APIRouter()

class ExtractRequest(BaseModel):
    path: str

class QueryRequest(BaseModel):
    query: str
    top_k: int = 4

@router.post("/extract")
def extract(req: ExtractRequest):
    p = Path(req.path)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    ctx = parser_service.extract_context(p)
    return {"path": str(p), "context": ctx}

@router.post("/index")
def index(req: ExtractRequest):
    p = Path(req.path)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    ctx = parser_service.extract_context(p)
    rag_service.index_context(ctx)
    return {"indexed": True, "path": str(p), "summary": ctx.get("summary")}

@router.post("/ask")
def ask(req: QueryRequest):
    answer = rag_service.answer(req.query, top_k=req.top_k)
    return answer
