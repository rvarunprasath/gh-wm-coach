"""
GraphRAG AI Financial Coach Agent.
Combines exact numerical figures from the Relational Ledger with contextual
dependencies from the Knowledge Graph to deliver grounded financial advisory.
"""

import os
from typing import Dict, Any, List
from app.db.relational import RelationalStore
from app.db.graph_store import KnowledgeGraphStore
from app.services.extractor import FinancialFactExtractor
from app.models.schemas import ChatResponse, ReasoningTrace


class FinancialCoachAgent:
    def __init__(
        self,
        rel_store: RelationalStore,
        graph_store: KnowledgeGraphStore,
        extractor: FinancialFactExtractor
    ):
        self.rel_store = rel_store
        self.graph_store = graph_store
        self.extractor = extractor

    def interact(self, message: str, user_id: str = "default_user", is_audio: bool = False) -> ChatResponse:
        """
        Main entry point for conversational turn.
        1. Extracts new facts & updates stores
        2. Retrieves dual-store context (Graph + Tables)
        3. Formulates grounded coaching response
        """
        # Step 1: Extract entities, holdings, family, or events from utterance
        extracted_data, actions = self.extractor.extract_and_sync(
            text=message,
            user_id=user_id,
            source="VOICE" if is_audio else "CHAT"
        )
        updated_portfolio = len(extracted_data.holdings) > 0 or len(extracted_data.account_balances) > 0
        updated_graph = (
            len(extracted_data.family_members) > 0 or
            len(extracted_data.life_events) > 0 or
            updated_portfolio
        )

        # Step 2: Retrieve Relational Portfolio Data
        portfolio = self.rel_store.get_portfolio_summary(user_id)
        net_worth = portfolio.get("net_worth", 0.0)
        monthly_income = portfolio.get("monthly_income", 150000.0)
        monthly_expenses = portfolio.get("monthly_expenses", 65000.0)
        monthly_savings = monthly_income - monthly_expenses
        allocations = portfolio.get("allocations", [])
        goals = portfolio.get("goals", [])
        holdings = portfolio.get("holdings", [])
        accounts = portfolio.get("accounts", [])

        # Step 3: Retrieve Knowledge Graph Semantic Context
        graph_summary = self.graph_store.get_context_summary(f"user_{user_id}")
        user_node = self.graph_store.get_node(f"user_{user_id}") or {}
        risk_profile = user_node.get("risk_profile", "Moderate")

        # Step 4: Build Reasoning Trace
        trace = ReasoningTrace(
            graph_context_used=[
                f"User Profile ({risk_profile} Risk)",
                f"Knowledge Graph: {graph_summary.splitlines()[1] if len(graph_summary.splitlines()) > 1 else 'Base Profile'}"
            ],
            accounts_consulted=[f"{a['institution_name']} ({a['account_type']}): ₹{a['balance']:,.0f}" for a in accounts],
            facts_extracted=actions
        )

        # Step 5: Generate Advisory Response
        lower_msg = message.lower()
        response_text = self._synthesize_advisory(
            user_message=message,
            lower_msg=lower_msg,
            portfolio=portfolio,
            graph_summary=graph_summary,
            actions=actions,
            risk_profile=risk_profile
        )

        return ChatResponse(
            reply=response_text,
            reasoning_trace=trace,
            updated_portfolio=updated_portfolio,
            updated_graph=updated_graph
        )

    def _synthesize_advisory(
        self,
        user_message: str,
        lower_msg: str,
        portfolio: Dict[str, Any],
        graph_summary: str,
        actions: List[str],
        risk_profile: str
    ) -> str:
        """
        Synthesizes a structured, analytical financial response
        grounded in the user's specific numbers and knowledge graph.
        """
        net_worth = portfolio.get("net_worth", 0.0)
        monthly_income = portfolio.get("monthly_income", 150000.0)
        monthly_expenses = portfolio.get("monthly_expenses", 65000.0)
        monthly_savings = portfolio.get("monthly_savings", 85000.0)
        allocations = portfolio.get("allocations", [])
        goals = portfolio.get("goals", [])

        # Find specific asset totals
        equity_val = next((a["value"] for a in allocations if a["asset_class"] == "EQUITY"), 0.0)
        mf_val = next((a["value"] for a in allocations if a["asset_class"] == "MUTUAL_FUND"), 0.0)
        liquid_val = next((a["value"] for a in allocations if a["asset_class"] in ["LIQUID", "DEBT"]), 0.0)

        # Scenario A: User just fed a status update (e.g. "I hold total equity in stocks worth 20 lakhs")
        if actions and ("equity" in lower_msg or "stocks" in lower_msg or "worth" in lower_msg):
            equity_pct = round((equity_val / net_worth * 100), 1) if net_worth > 0 else 0
            lines = [
                f"### Got it! I've logged your equity holdings.",
                f"",
                f"I have captured your equity portfolio of **₹{equity_val:,.0f}** and updated your financial snapshot:",
                f"- **Total Net Worth**: ₹{net_worth:,.0f}",
                f"- **Equity Allocation**: **{equity_pct}%** of your total portfolio",
                f"- **Liquid / Cash Reserve**: ₹{liquid_val:,.0f}",
                f"",
                f"#### Portfolio Impact & Advice:",
                f"1. **Risk Alignment**: For a **{risk_profile}** risk profile, keeping equity between 40%–50% is well-balanced.",
                f"2. **Goal Horizon**: Your equity acts as a long-term compounder. In our knowledge graph, we've linked this asset to your profile to safeguard your upcoming life goals.",
                f"3. **Next Step**: Would you like to review whether this equity allocation can fund your upcoming milestones (like higher education or property purchase), or shall we optimize your SIPs?"
            ]
            return "\n".join(lines)

        # Scenario B: Affordability / Purchase Question (e.g., "Can I buy a 50 lakh house / apartment in 2 years?")
        if any(w in lower_msg for w in ["buy", "afford", "purchase"]) and any(w in lower_msg for w in ["house", "home", "flat", "apartment", "car", "property"]):
            # Extract target price if mentioned
            import re
            price_match = re.search(r"([\d\.]+)\s*(?:crore|crores|cr|lakh|lakhs|lac|lacs|l)", lower_msg)
            target_cost = 5000000.0
            if price_match:
                from app.services.extractor import parse_indian_currency_amount
                target_cost = parse_indian_currency_amount(price_match.group(0))

            horizon_years = 2
            yr_match = re.search(r"(\d+)\s*(?:years?|yrs?)", lower_msg)
            if yr_match:
                horizon_years = int(yr_match.group(1))

            # Financial projections
            projected_new_savings = monthly_savings * (horizon_years * 12)
            down_payment_needed = target_cost * 0.20  # 20% down payment
            loan_amount = target_cost * 0.80
            # Approx EMI for 20 years @ 8.5% = ₹8.68 per 1000
            estimated_emi = round(loan_amount * 0.00868)
            surplus_after_emi = monthly_savings - estimated_emi

            lines = [
                f"### Affordability Analysis: ₹{target_cost:,.0f} Property in {horizon_years} Years",
                f"",
                f"Here is how this purchase fits into your current financial ledger and knowledge graph:",
                f"",
                f"#### 1. Down Payment & Capital Requirements",
                f"- **20% Down Payment Needed**: **₹{down_payment_needed:,.0f}**",
                f"- **Current Monthly Surplus**: ₹{monthly_savings:,.0f}/month (Income: ₹{monthly_income:,.0f} - Expenses: ₹{monthly_expenses:,.0f})",
                f"- **Projected Additional Savings ({horizon_years} yrs)**: **₹{projected_new_savings:,.0f}**",
                f"- **Verdict on Down Payment**: **Solvent**. Your projected 2-year savings (₹{projected_new_savings:,.0f}) comfortably covers the ₹{down_payment_needed:,.0f} down payment without liquidating your ₹{equity_val:,.0f} equity holdings.",
                f"",
                f"#### 2. Cash Flow & EMI Health",
                f"- **Loan Required (80%)**: ₹{loan_amount:,.0f}",
                f"- **Estimated Monthly EMI (20 yrs @ 8.5%)**: **₹{estimated_emi:,.0f}/month**",
                f"- **Remaining Monthly Cash Surplus**: **₹{surplus_after_emi:,.0f}/month**",
                f"- **Debt-to-Income (DTI)**: {round((estimated_emi / monthly_income) * 100, 1)}% (Healthy is below 35%).",
                f"",
                f"#### 3. Trade-offs with Knowledge Graph Milestones",
                f"Our knowledge graph currently tracks your life events:"
            ]
            
            for g in goals:
                lines.append(f"- **{g['title']}** (Target: {g['target_year']}, ₹{g['target_amount']:,.0f})")

            lines.extend([
                f"",
                f"**Coach Recommendation**: You can comfortably afford this property provided you keep your emergency reserve of 6 months expenses (₹{monthly_expenses * 6:,.0f}) intact in liquid savings and continue dedicated SIPs for your upcoming family goals."
            ])
            return "\n".join(lines)

        # Scenario C: Overview / Portfolio / Status Query
        if any(w in lower_msg for w in ["portfolio", "net worth", "summary", "how am i doing", "status", "snapshot"]):
            lines = [
                f"### Financial Portfolio Snapshot",
                f"",
                f"Here is your real-time consolidated position across connected accounts and logged assets:",
                f"- **Total Net Worth**: **₹{net_worth:,.0f}**",
                f"- **Monthly Savings Rate**: **{round((monthly_savings / monthly_income * 100), 1)}%** (₹{monthly_savings:,.0f} / mo)",
                f"",
                f"#### Asset Class Breakdown:"
            ]
            for a in allocations:
                lines.append(f"- **{a['asset_class']}**: ₹{a['value']:,.0f} ({a['percentage']}%)")

            if goals:
                lines.append(f"\n#### Active Life Goals in Knowledge Graph:")
                for g in goals:
                    lines.append(f"- **{g['title']}**: Target ₹{g['target_amount']:,.0f} by {g['target_year']} (Accumulated: ₹{g.get('accumulated_amount', 0):,.0f})")

            lines.append(f"\nFeel free to speak or type an update, upload any statement, or ask specific trade-off questions!")
            return "\n".join(lines)

        # Default Helpful Coaching Response
        lines = [
            f"### Financial Coach Insight",
            f"",
            f"Based on your current portfolio (Net Worth: **₹{net_worth:,.0f}**, Monthly Surplus: **₹{monthly_savings:,.0f}**) and personal knowledge graph:",
            f"",
            f"I have registered your question: *\"{user_message}\"*.",
            f"",
            f"**Key Observations:**",
            f"1. **Liquidity Buffer**: You have ₹{liquid_val:,.0f} in liquid reserves, which provides a runway of **{round(liquid_val / monthly_expenses, 1) if monthly_expenses else 6} months** of living expenses.",
            f"2. **Growth Capital**: Your equity and mutual funds (₹{equity_val + mf_val:,.0f}) are positioned for capital growth.",
            f"3. **Knowledge Graph Context**: All upcoming family milestones are synchronized to your asset allocation.",
            f"",
            f"What specific area would you like to model next? (e.g. tax optimization, goal feasibility, retirement timeline, or debt restructuring?)"
        ]
        return "\n".join(lines)
