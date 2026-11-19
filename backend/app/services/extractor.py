"""
Structured Financial Information Extractor.
Parses conversational utterances (voice transcripts, chat messages) and raw document text.
Extracts financial holdings (with Lakh/Crore conversions), family members,
life events, and accounts, then synchronizes them to Relational DB and Knowledge Graph.
"""

import re
from typing import Dict, Any, List, Tuple
from datetime import datetime
from app.db.relational import RelationalStore
from app.db.graph_store import KnowledgeGraphStore
from app.models.schemas import (
    ExtractedHoldingFact,
    ExtractedFamilyFact,
    ExtractedLifeEventFact,
    ExtractedFinancialData
)


def parse_indian_currency_amount(text: str) -> float:
    """
    Parses currency expressions like:
    - 20 lakhs, 20L, 20 lacs -> 2,000,000
    - 1.5 crore, 1.5cr -> 15,000,000
    - 50k, 50 thousand -> 50,000
    - ₹25,00,000 or 2500000 -> 2,500,000
    """
    clean = text.lower().replace(",", "").replace("₹", "").replace("rs.", "").replace("rs", "").strip()

    # Match crore
    cr_match = re.search(r"([\d\.]+)\s*(?:crore|crores|cr)", clean)
    if cr_match:
        return float(cr_match.group(1)) * 10_000_000

    # Match lakh
    lakh_match = re.search(r"([\d\.]+)\s*(?:lakh|lakhs|lac|lacs|l)\b", clean)
    if lakh_match:
        return float(lakh_match.group(1)) * 100_000

    # Match thousand / k
    k_match = re.search(r"([\d\.]+)\s*(?:thousand|k)\b", clean)
    if k_match:
        return float(k_match.group(1)) * 1_000

    # Plain digits
    num_match = re.search(r"([\d\.]+)", clean)
    if num_match:
        return float(num_match.group(1))

    return 0.0


class FinancialFactExtractor:
    def __init__(self, rel_store: RelationalStore, graph_store: KnowledgeGraphStore):
        self.rel_store = rel_store
        self.graph_store = graph_store

    def extract_and_sync(self, text: str, user_id: str = "default_user", source: str = "CHAT") -> Tuple[ExtractedFinancialData, List[str]]:
        """
        Analyzes the text, extracts structured entities, and updates:
        1. Relational tables (holdings, accounts, goals)
        2. Knowledge graph nodes and edges
        Returns extracted data and list of human-readable action summaries.
        """
        extracted = ExtractedFinancialData()
        action_summaries = []
        lower_text = text.lower()

        # -------------------------------------------------------------
        # 1. HOLDINGS EXTRACTION (e.g., "hold equity in stocks worth 20 lakhs")
        # -------------------------------------------------------------
        # Regex patterns for asset mentions
        asset_patterns = [
            (r"(?:equity|stocks?|shares?)[^.\n\d]*?(?:worth|value|of|holding|total)?\s*[:=]?\s*(₹?[\d\.]+\s*(?:crores?|cr|lakhs?|lacs?|l|k|thousand)?)", "EQUITY", "Equity Stocks"),
            (r"(?:mutual\s*funds?|mf|sip)[^.\n\d]*?(?:worth|value|of|holding|total)?\s*[:=]?\s*(₹?[\d\.]+\s*(?:crores?|cr|lakhs?|lacs?|l|k|thousand)?)", "MUTUAL_FUND", "Mutual Funds Portfolio"),
            (r"(?:fixed\s*deposit|fd|term\s*deposit)[^.\n\d]*?(?:worth|value|of|holding)?\s*[:=]?\s*(₹?[\d\.]+\s*(?:crores?|cr|lakhs?|lacs?|l|k|thousand)?)", "DEBT", "Fixed Deposits"),
            (r"(?:gold|digital\s*gold|sgb)[^.\n\d]*?(?:worth|value|of|holding)?\s*[:=]?\s*(₹?[\d\.]+\s*(?:crores?|cr|lakhs?|lacs?|l|k|thousand)?)", "GOLD", "Gold Holdings"),
            (r"(?:real\s*estate|property|flat|apartment|plot)[^.\n\d]*?(?:worth|value|of)?\s*[:=]?\s*(₹?[\d\.]+\s*(?:crores?|cr|lakhs?|lacs?|l|k|thousand)?)", "REAL_ESTATE", "Real Estate"),
            (r"(?:cash|savings\s*balance|bank\s*balance)[^.\n\d]*?(?:of|is|worth)?\s*[:=]?\s*(₹?[\d\.]+\s*(?:crores?|cr|lakhs?|lacs?|l|k|thousand)?)", "LIQUID", "Liquid Savings")
        ]

        for pattern, asset_type, default_name in asset_patterns:
            match = re.search(pattern, lower_text)
            if match:
                raw_amt = match.group(1)
                amount = parse_indian_currency_amount(raw_amt)
                if amount > 0:
                    holding_fact = ExtractedHoldingFact(
                        asset_type=asset_type,
                        asset_name=default_name,
                        valuation=amount
                    )
                    extracted.holdings.append(holding_fact)

                    # 1. Update Relational DB
                    self.rel_store.upsert_holding(
                        user_id=user_id,
                        asset_type=asset_type,
                        asset_name=default_name,
                        current_value=amount
                    )

                    # 2. Update Knowledge Graph
                    asset_node_id = f"asset_{asset_type.lower()}"
                    self.graph_store.add_node(
                        node_id=asset_node_id,
                        label="Asset",
                        properties={
                            "name": default_name,
                            "asset_class": asset_type,
                            "current_value": amount,
                            "last_updated": datetime.now().isoformat()
                        }
                    )
                    user_node_id = f"user_{user_id}"
                    self.graph_store.add_edge(
                        source_id=user_node_id,
                        target_id=asset_node_id,
                        relation="OWNS",
                        properties={"valuation": amount}
                    )

                    action_summaries.append(f"Updated {default_name} ({asset_type}) valuation to ₹{amount:,.0f} in Portfolio Ledger and Knowledge Graph.")

        # -------------------------------------------------------------
        # 2. FAMILY MEMBER EXTRACTION (e.g., "my daughter Ananya", "my son Aarav", "my wife Priya")
        # -------------------------------------------------------------
        family_relations = [
            (r"(?:my\s+)?daughter\s+([A-Za-z]+)", "Daughter"),
            (r"(?:my\s+)?son\s+([A-Za-z]+)", "Son"),
            (r"(?:my\s+)?wife\s+([A-Za-z]+)", "Spouse"),
            (r"(?:my\s+)?husband\s+([A-Za-z]+)", "Spouse"),
            (r"(?:my\s+)?spouse\s+([A-Za-z]+)", "Spouse"),
            (r"(?:my\s+)?mother\s+([A-Za-z]+)", "Mother"),
            (r"(?:my\s+)?father\s+([A-Za-z]+)", "Father"),
        ]

        for pattern, rel_type in family_relations:
            f_match = re.search(pattern, text, re.IGNORECASE)
            if f_match:
                name = f_match.group(1).capitalize()
                
                # Check for age (e.g., "Ananya who is 14" or "aged 14")
                age_match = re.search(rf"{name}[^.\n]*?(?:is|aged|age)?\s*(\d{{1,2}})\s*(?:years|yrs|yo)?", text, re.IGNORECASE)
                age = int(age_match.group(1)) if age_match else None

                fam_fact = ExtractedFamilyFact(
                    name=name,
                    relation=rel_type,
                    age=age,
                    is_dependent=True
                )
                extracted.family_members.append(fam_fact)

                # Add to Knowledge Graph
                fam_node_id = f"family_{name.lower()}"
                self.graph_store.add_node(
                    node_id=fam_node_id,
                    label="FamilyMember",
                    properties={
                        "name": name,
                        "relation": rel_type,
                        "age": age,
                        "is_dependent": True
                    }
                )
                user_node_id = f"user_{user_id}"
                self.graph_store.add_edge(
                    source_id=user_node_id,
                    target_id=fam_node_id,
                    relation="HAS_DEPENDENT",
                    properties={"relation": rel_type}
                )
                action_summaries.append(f"Captured family member: {name} ({rel_type}{f', {age} yrs' if age else ''}) into Knowledge Graph.")

        # -------------------------------------------------------------
        # 3. LIFE EVENTS & GOALS (e.g., "college in 2028", "buy house in 2027", "retirement")
        # -------------------------------------------------------------
        event_patterns = [
            (r"(?:college|higher education|university)[^.\n]*?(?:in|by)?\s*(20\d{2})", "EDUCATION", "Higher Education Fund"),
            (r"(?:school admission|schooling)[^.\n]*?(?:in|by)?\s*(20\d{2})", "EDUCATION", "School Education Fund"),
            (r"(?:buy|purchase|own)\s+(?:a\s+)?(?:house|home|flat|apartment|property)[^.\n]*?(?:in|by)?\s*(20\d{2})", "HOME", "Home Purchase"),
            (r"(?:buy|purchase)\s+(?:a\s+)?(?:car|vehicle)[^.\n]*?(?:in|by)?\s*(20\d{2})", "VEHICLE", "New Car Purchase"),
            (r"(?:retire|retirement)[^.\n]*?(?:in|by)?\s*(20\d{2})", "RETIREMENT", "Retirement Corpus"),
            (r"(?:wedding|marriage)[^.\n]*?(?:in|by)?\s*(20\d{2})", "WEDDING", "Wedding Expense")
        ]

        for pattern, cat, default_title in event_patterns:
            e_match = re.search(pattern, lower_text)
            if e_match:
                target_year = int(e_match.group(1))

                # Check if an amount was specified with this goal
                amt_match = re.search(rf"(?:need|target|budget|cost|worth)?\s*(?:of|about)?\s*(₹?[\d\.]+\s*(?:crores?|cr|lakhs?|lacs?|l)\b)", text, re.IGNORECASE)
                target_amount = parse_indian_currency_amount(amt_match.group(1)) if amt_match else 2500000.0  # default 25L for education/home if unspecified

                goal_fact = ExtractedLifeEventFact(
                    title=default_title,
                    event_type=cat,
                    target_year=target_year,
                    target_amount=target_amount
                )
                extracted.life_events.append(goal_fact)

                # 1. Update Relational Goals
                self.rel_store.upsert_goal(
                    user_id=user_id,
                    title=default_title,
                    category=cat,
                    target_amount=target_amount,
                    target_year=target_year
                )

                # 2. Update Knowledge Graph
                event_node_id = f"event_{cat.lower()}_{target_year}"
                self.graph_store.add_node(
                    node_id=event_node_id,
                    label="LifeEvent",
                    properties={
                        "title": default_title,
                        "type": cat,
                        "target_year": target_year,
                        "target_amount": target_amount
                    }
                )
                user_node_id = f"user_{user_id}"
                self.graph_store.add_edge(
                    source_id=user_node_id,
                    target_id=event_node_id,
                    relation="PLANS_FOR",
                    properties={"target_year": target_year, "target_amount": target_amount}
                )

                # Link to family member if beneficiary detected
                for fam in extracted.family_members:
                    fam_node_id = f"family_{fam.name.lower()}"
                    self.graph_store.add_edge(
                        source_id=event_node_id,
                        target_id=fam_node_id,
                        relation="BENEFICIARY",
                        properties={"name": fam.name}
                    )

                action_summaries.append(f"Recorded Life Milestone: {default_title} targeted for year {target_year} (₹{target_amount:,.0f}).")

        # Log extraction in audit table
        if action_summaries:
            self.rel_store.log_extracted_fact(
                user_id=user_id,
                source=source,
                raw_text=text,
                extracted_dict={
                    "holdings": [h.dict() for h in extracted.holdings],
                    "family": [f.dict() for f in extracted.family_members],
                    "events": [e.dict() for e in extracted.life_events]
                }
            )

        return extracted, action_summaries
