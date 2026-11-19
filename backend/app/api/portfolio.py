"""
API Endpoints for Financial Portfolio Snapshot and Asset Allocations.
"""

from fastapi import APIRouter
from app.models.schemas import PortfolioSnapshot
from app.db.relational import RelationalStore
from app.db.graph_store import KnowledgeGraphStore
from app.services.seed_data import seed_initial_financial_data

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])

rel_store = RelationalStore()
graph_store = KnowledgeGraphStore()


@router.get("", response_model=PortfolioSnapshot)
async def get_portfolio(user_id: str = "default_user"):
    summary = rel_store.get_portfolio_summary(user_id)
    if not summary:
        seed_initial_financial_data(rel_store, graph_store, user_id)
        summary = rel_store.get_portfolio_summary(user_id)
    return summary


@router.post("/reset")
async def reset_portfolio(user_id: str = "default_user"):
    seed_initial_financial_data(rel_store, graph_store, user_id)
    return {"status": "success", "message": "Portfolio and Knowledge Graph re-seeded to initial state."}
