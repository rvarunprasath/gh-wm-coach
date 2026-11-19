"""
Pydantic Schemas for API Requests, Responses, and Extraction Data Models.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    audio_transcript: Optional[bool] = False


class ReasoningTrace(BaseModel):
    graph_context_used: List[str] = []
    accounts_consulted: List[str] = []
    facts_extracted: List[str] = []


class ChatResponse(BaseModel):
    reply: str
    reasoning_trace: ReasoningTrace
    updated_portfolio: bool = False
    updated_graph: bool = False


class ExtractedHoldingFact(BaseModel):
    asset_type: str = Field(description="EQUITY, MUTUAL_FUND, DEBT, GOLD, REAL_ESTATE, LIQUID")
    asset_name: str
    valuation: float
    units: Optional[float] = None
    symbol: Optional[str] = None


class ExtractedFamilyFact(BaseModel):
    name: str
    relation: str
    age: Optional[int] = None
    is_dependent: bool = True


class ExtractedLifeEventFact(BaseModel):
    title: str
    event_type: str  # EDUCATION, RETIREMENT, HOME, WEDDING, etc.
    target_year: int
    target_amount: Optional[float] = None
    beneficiary: Optional[str] = None


class ExtractedFinancialData(BaseModel):
    holdings: List[ExtractedHoldingFact] = []
    family_members: List[ExtractedFamilyFact] = []
    life_events: List[ExtractedLifeEventFact] = []
    account_balances: List[Dict[str, Any]] = []


class AllocationItem(BaseModel):
    asset_class: str
    value: float
    percentage: float


class PortfolioSnapshot(BaseModel):
    net_worth: float
    monthly_income: float
    monthly_expenses: float
    monthly_savings: float
    currency: str = "INR"
    allocations: List[AllocationItem]
    holdings: List[Dict[str, Any]]
    accounts: List[Dict[str, Any]]
    goals: List[Dict[str, Any]]


class GraphNode(BaseModel):
    id: str
    label: str
    name: str
    properties: Dict[str, Any]


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: str
    properties: Dict[str, Any]


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class StatementUploadResponse(BaseModel):
    filename: str
    status: str
    extracted_summary: str
    items_detected: int
    updated_graph: bool = True
