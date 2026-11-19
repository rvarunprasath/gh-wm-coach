"""
FastAPI Main Application Entry Point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.relational import RelationalStore, IS_POSTGRES
from app.db.graph_store import KnowledgeGraphStore
from app.services.agent import is_valid_gemini_config
from app.services.seed_data import seed_initial_financial_data
from app.api.chat import router as chat_router
from app.api.portfolio import router as portfolio_router
from app.api.graph import router as graph_router
from app.api.ingestion import router as ingestion_router

app = FastAPI(
    title="AI Financial Coach (gh-wm-coach)",
    description="Knowledge Graph & Relational Dual-Store AI Wealth Management Coach",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(chat_router)
app.include_router(portfolio_router)
app.include_router(graph_router)
app.include_router(ingestion_router)


@app.on_event("startup")
async def startup_event():
    print("[Startup] Initializing Relational DB and Knowledge Graph...")
    rel_store = RelationalStore()
    graph_store = KnowledgeGraphStore()
    seed_initial_financial_data(rel_store, graph_store, "default_user")
    print(f"[Startup] System ready. Database: {'AlloyDB/PostgreSQL' if IS_POSTGRES else 'SQLite'}. Gemini: {'Active' if is_valid_gemini_config() else 'Fallback'}.")


@app.get("/")
async def root():
    return {
        "app": "AI Financial Coach API",
        "status": "healthy",
        "endpoints": ["/api/chat", "/api/portfolio", "/api/graph", "/api/ingest/upload", "/api/ingest/connect-api"]
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "database": "alloydb" if IS_POSTGRES else "sqlite",
        "gemini": "active" if is_valid_gemini_config() else "fallback"
    }
