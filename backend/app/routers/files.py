import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services import parser_service

UPLOAD_DIR = Path("backend/data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    dest = UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        f.write(await file.read())

    try:
        ctx = parser_service.extract_context(dest)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    return {"filename": file.filename, "path": str(dest), "context": ctx}

@router.get("/")
async def list_files():
    return {
        "files": [p.name for p in UPLOAD_DIR.glob("*") if p.is_file()]
    }
