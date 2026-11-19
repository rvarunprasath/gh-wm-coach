"""
API Endpoints for Conversational Interaction (Chat and Voice).
"""

from fastapi import APIRouter, Depends
from app.models.schemas import ChatRequest, ChatResponse
from app.services.agent import FinancialCoachAgent
from app.db.relational import RelationalStore
from app.db.graph_store import KnowledgeGraphStore
from app.services.extractor import FinancialFactExtractor

router = APIRouter(prefix="/api", tags=["Chat & Voice"])

rel_store = RelationalStore()
graph_store = KnowledgeGraphStore()
extractor = FinancialFactExtractor(rel_store, graph_store)
agent = FinancialCoachAgent(rel_store, graph_store, extractor)


@router.post("/chat", response_model=ChatResponse)
async def chat_interaction(req: ChatRequest):
    return agent.interact(message=req.message, user_id=req.user_id, is_audio=req.audio_transcript)


@router.post("/voice", response_model=ChatResponse)
async def voice_interaction(req: ChatRequest):
    return agent.interact(message=req.message, user_id=req.user_id, is_audio=True)
