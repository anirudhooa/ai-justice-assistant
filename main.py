import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from core.rag_engine import LegalRAGEngine

app = FastAPI(
    title="AI Justice Department Assistant",
    description="RAG-Powered Conversational System for Indian Laws, BNS, BNSS, and Constitutional Rights",
    version="1.0.0"
)

# Mount static and templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Initialize RAG Engine
rag_engine = LegalRAGEngine()

class ChatRequest(BaseModel):
    query: str
    history: Optional[List[dict]] = []

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"total_statutes": len(rag_engine.statutes)}
    )

@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    result = rag_engine.answer_query(payload.query.strip())
    return JSONResponse(content=result)

@app.get("/api/search")
async def search_endpoint(q: str = "", top_k: int = 5):
    if not q.strip():
        return JSONResponse(content={"results": []})
    results = rag_engine.search_statutes(q.strip(), top_k=top_k)
    return JSONResponse(content={"results": results, "query": q})

@app.get("/api/convert")
async def convert_endpoint(code: str = ""):
    if not code.strip():
        raise HTTPException(status_code=400, detail="Code parameter required (e.g. ?code=420)")
    mapping = rag_engine.convert_code(code.strip())
    return JSONResponse(content=mapping)

@app.get("/api/statutes")
async def list_statutes():
    return JSONResponse(content={
        "total": len(rag_engine.statutes),
        "statutes": rag_engine.statutes
    })

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AI Justice Department Assistant",
        "statutes_indexed": len(rag_engine.statutes),
        "omniroute_configured": bool(os.environ.get("OMNIROUTE_API_KEY")),
        "omniroute_base_url": os.environ.get("OMNIROUTE_BASE_URL", "http://localhost:20128/v1"),
        "omniroute_model": os.environ.get("OMNIROUTE_MODEL", "antigravity/gemini-3.8-flash-tiered")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
