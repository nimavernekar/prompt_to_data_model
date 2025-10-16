from fastapi import APIRouter
from app.vectorstore import tiny_store

router = APIRouter()

@router.post("/clear")
def clear_store():
    tiny_store.clear()
    return {"cleared": True}
