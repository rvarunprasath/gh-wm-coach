"""
API Endpoints for Knowledge Graph Inspection & Visualizer.
"""

from fastapi import APIRouter
from app.models.schemas import GraphResponse
from app.db.graph_store import KnowledgeGraphStore
from app.db.relational import RelationalStore
from app.services.seed_data import seed_initial_financial_data

router = APIRouter(prefix="/api/graph", tags=["Knowledge Graph"])
graph_store = KnowledgeGraphStore()
rel_store = RelationalStore()


@router.get("", response_model=GraphResponse)
async def get_graph(user_id: str = "default_user"):
    # If graph has no nodes or missing user, seed it
    if not graph_store.graph.has_node(f"user_{user_id}") or graph_store.graph.number_of_nodes() <= 1:
        seed_initial_financial_data(rel_store, graph_store, user_id)
        graph_store.load()

    subgraph = graph_store.get_user_subgraph(f"user_{user_id}")
    return subgraph
