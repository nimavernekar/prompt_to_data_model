from fastapi import FastAPI
from app.routers import files, context, vectorstore

app = FastAPI(title="Smart File Context API", version="0.1.0")

app.include_router(files.router, prefix="/files", tags=["files"])
app.include_router(context.router, prefix="/context", tags=["context"])
app.include_router(vectorstore.router, prefix="/vectorstore", tags=["vectorstore"])

@app.get("/")
def root():
    return {"ok": True, "service": "smart-file-context", "version": "0.1.0"}
