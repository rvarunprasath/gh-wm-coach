"""
API Endpoints for Document Ingestion (Bank Statements, CAS) & API Integrations.
"""

from fastapi import APIRouter, UploadFile, File, Form
from app.models.schemas import StatementUploadResponse
from app.db.relational import RelationalStore
from app.db.graph_store import KnowledgeGraphStore
from app.services.extractor import FinancialFactExtractor
from app.services.parser import StatementParser

router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])

rel_store = RelationalStore()
graph_store = KnowledgeGraphStore()
extractor = FinancialFactExtractor(rel_store, graph_store)
parser = StatementParser(extractor)


@router.post("/upload", response_model=StatementUploadResponse)
async def upload_statement(
    file: UploadFile = File(...),
    user_id: str = Form("default_user")
):
    content = await file.read()
    filename = file.filename or "statement.pdf"

    if filename.endswith(".pdf"):
        result = parser.parse_pdf(content, filename, user_id)
    elif filename.endswith(".csv"):
        result = parser.parse_csv(content.decode("utf-8", errors="ignore"), filename, user_id)
    else:
        # Treat as plain text
        result = parser.parse_csv(content.decode("utf-8", errors="ignore"), filename, user_id)

    return StatementUploadResponse(
        filename=filename,
        status="SUCCESS",
        extracted_summary=result.get("summary", f"Extracted {result.get('detected_items', 0)} holdings/accounts"),
        items_detected=result.get("detected_items", 0),
        updated_graph=True
    )


@router.post("/connect-api")
async def connect_external_api(
    provider: str,
    api_key_or_consent: str = "mock_consent",
    user_id: str = "default_user"
):
    """
    Connects with Account Aggregator (Setu / Finvu / OneMoney) or Broker API (Zerodha Kite / Groww).
    Simulates sync of live balances and holdings into Relational tables and Knowledge Graph.
    """
    if provider.lower() in ["zerodha", "groww"]:
        rel_store.upsert_account(user_id, f"{provider.capitalize()} Demat", "DEMAT", 50000.0)
        rel_store.upsert_holding(user_id, "EQUITY", "Reliance Industries Ltd", 480000.0, symbol="RELIANCE")
        rel_store.upsert_holding(user_id, "EQUITY", "Tata Consultancy Services", 520000.0, symbol="TCS")
        rel_store.upsert_holding(user_id, "EQUITY", "Infosys Ltd", 350000.0, symbol="INFY")
        
        # Update Knowledge Graph
        graph_store.add_node(f"asset_equity_{provider.lower()}", "Asset", {
            "name": f"{provider.capitalize()} Equity Portfolio",
            "valuation": 1350000.0,
            "provider": provider
        })
        graph_store.add_edge(f"user_{user_id}", f"asset_equity_{provider.lower()}", "OWNS")
        msg = f"Synced with {provider.capitalize()}! Imported 3 equity stocks totaling ₹13.5 Lakhs."

    elif "bank" in provider.lower() or "aggregator" in provider.lower():
        rel_store.upsert_account(user_id, "Axis Bank", "SAVINGS", 380000.0, "XXXX-3199")
        graph_store.add_node("account_axis", "Account", {
            "institution": "Axis Bank",
            "type": "SAVINGS",
            "balance": 380000.0
        })
        graph_store.add_edge(f"user_{user_id}", "account_axis", "HOLDS_ACCOUNT")
        msg = f"Connected via Account Aggregator! Synced Axis Bank Savings (Balance: ₹3,80,000)."
    else:
        msg = f"Connected to {provider} successfully."

    return {
        "status": "CONNECTED",
        "provider": provider,
        "message": msg
    }
