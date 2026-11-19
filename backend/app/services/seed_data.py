"""
Realistic Seed Data Initializer for Financial Ledger and Knowledge Graph.
"""

from datetime import datetime
from app.db.relational import RelationalStore, get_db_connection
from app.db.graph_store import KnowledgeGraphStore


def seed_initial_financial_data(rel_store: RelationalStore, graph_store: KnowledgeGraphStore, user_id: str = "default_user"):
    conn = get_db_connection()
    user_email = f"{user_id}@example.com" if user_id != "default_user" else "rahul.sharma@example.com"
    user_exists = conn.execute("SELECT id FROM users WHERE id = ? OR email = ?", (user_id, user_email)).fetchone()
    
    # Always ensure user exists in Relational DB
    if not user_exists:
        conn.execute("""
            INSERT OR REPLACE INTO users (id, name, email, currency, monthly_income, monthly_expenses, risk_profile, created_at)
            VALUES (?, ?, ?, 'INR', 150000, 65000, 'Moderate', ?)
        """, (user_id, "Rahul Sharma", user_email, datetime.now().isoformat()))
        conn.commit()

        # Seed Accounts
        acc1 = rel_store.upsert_account(user_id, "HDFC Bank", "SAVINGS", 450000.0, "XXXX-4821")
        acc2 = rel_store.upsert_account(user_id, "ICICI Bank", "SAVINGS", 250000.0, "XXXX-9102")
        acc3 = rel_store.upsert_account(user_id, "Zerodha Demat", "DEMAT", 150000.0, "1208-XXXX")

        # Seed Holdings
        rel_store.upsert_holding(user_id, "MUTUAL_FUND", "Parag Parikh Flexi Cap Fund", 850000.0, symbol="PPFC", account_id=acc3)
        rel_store.upsert_holding(user_id, "MUTUAL_FUND", "UTI Nifty 50 Index Fund", 650000.0, symbol="NIFTY50", account_id=acc3)
        rel_store.upsert_holding(user_id, "DEBT", "HDFC Fixed Deposit (7.25%)", 800000.0, account_id=acc1)
        rel_store.upsert_holding(user_id, "GOLD", "Sovereign Gold Bonds (SGB)", 350000.0, account_id=acc3)

        # Seed Life Goals
        rel_store.upsert_goal(user_id, "Ananya Higher Education", "EDUCATION", 2500000.0, 2028, 650000.0, "High")
        rel_store.upsert_goal(user_id, "Emergency Fund Reserve", "EMERGENCY", 500000.0, 2025, 500000.0, "High")
        rel_store.upsert_goal(user_id, "Retirement Freedom Corpus", "RETIREMENT", 30000000.0, 2045, 2350000.0, "Medium")

    conn.close()

    # Seed Knowledge Graph
    user_node_id = f"user_{user_id}"
    graph_store.add_node(
        node_id=user_node_id,
        label="User",
        properties={
            "name": "Rahul Sharma",
            "age": 40,
            "risk_profile": "Moderate",
            "monthly_income": 150000,
            "monthly_expenses": 65000
        }
    )

    # Family Members
    daughter_id = "family_ananya"
    graph_store.add_node(
        node_id=daughter_id,
        label="FamilyMember",
        properties={"name": "Ananya", "relation": "Daughter", "age": 14, "is_dependent": True}
    )
    graph_store.add_edge(user_node_id, daughter_id, "HAS_DEPENDENT", {"relation": "Daughter"})

    spouse_id = "family_priya"
    graph_store.add_node(
        node_id=spouse_id,
        label="FamilyMember",
        properties={"name": "Priya", "relation": "Spouse", "age": 38, "is_dependent": False}
    )
    graph_store.add_edge(user_node_id, spouse_id, "HAS_DEPENDENT", {"relation": "Spouse"})

    # Life Events
    college_event_id = "event_education_2028"
    graph_store.add_node(
        node_id=college_event_id,
        label="LifeEvent",
        properties={
            "title": "Ananya College Admission",
            "type": "EDUCATION",
            "target_year": 2028,
            "target_amount": 2500000
        }
    )
    graph_store.add_edge(user_node_id, college_event_id, "PLANS_FOR", {"target_year": 2028})
    graph_store.add_edge(college_event_id, daughter_id, "BENEFICIARY", {"name": "Ananya"})

    retirement_event_id = "event_retirement_2045"
    graph_store.add_node(
        node_id=retirement_event_id,
        label="LifeEvent",
        properties={
            "title": "Retirement Freedom",
            "type": "RETIREMENT",
            "target_year": 2045,
            "target_amount": 30000000
        }
    )
    graph_store.add_edge(user_node_id, retirement_event_id, "PLANS_FOR", {"target_year": 2045})
