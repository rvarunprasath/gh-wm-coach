"""
Multi-format Statement Parser for Bank Statements, Mutual Fund CAS, and Broker Portfolios.
Supports PDF text extraction (using pypdf) and CSV parsing.
"""

import io
import csv
import re
from typing import Dict, Any, List
from pypdf import PdfReader
from app.services.extractor import FinancialFactExtractor, parse_indian_currency_amount


class StatementParser:
    def __init__(self, extractor: FinancialFactExtractor):
        self.extractor = extractor

    def parse_pdf(self, file_bytes: bytes, filename: str, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Extracts text from PDF, detects statement type (Bank / Mutual Fund / Demat),
        extracts tabular rows and passes text to the fact extractor.
        """
        reader = PdfReader(io.BytesIO(file_bytes))
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

        return self._process_statement_text(full_text, filename, user_id)

    def parse_csv(self, csv_content: str, filename: str, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Parses CSV statement (e.g. Zerodha holdings CSV, bank transactions CSV).
        """
        lines = csv_content.strip().split("\n")
        reader = csv.DictReader(lines)
        
        detected_items = 0
        total_valuation = 0.0

        for row in reader:
            # Case 1: Zerodha/Groww holdings CSV with Instrument/Symbol, Qty, Current Value
            keys_lower = {k.lower(): k for k in row.keys() if k}
            
            # Check for stock holding row
            inst_key = next((keys_lower[k] for k in ["instrument", "symbol", "stock", "scheme", "fund name"] if k in keys_lower), None)
            val_key = next((keys_lower[k] for k in ["current value", "cur. val", "value", "valuation", "total value"] if k in keys_lower), None)
            
            if inst_key and val_key and row[val_key]:
                try:
                    val = float(str(row[val_key]).replace(",", "").replace("₹", ""))
                    asset_name = str(row[inst_key]).strip()
                    asset_type = "MUTUAL_FUND" if "fund" in asset_name.lower() or "growth" in asset_name.lower() else "EQUITY"
                    
                    self.extractor.rel_store.upsert_holding(
                        user_id=user_id,
                        asset_type=asset_type,
                        asset_name=asset_name,
                        current_value=val
                    )
                    detected_items += 1
                    total_valuation += val
                except ValueError:
                    pass

        # Also run extractor on the raw text for any life events or accounts
        extracted_data, actions = self.extractor.extract_and_sync(csv_content, user_id, source="STATEMENT")
        
        return {
            "filename": filename,
            "detected_items": detected_items + len(extracted_data.holdings),
            "total_extracted_value": total_valuation,
            "actions": actions or [f"Successfully imported {detected_items} holdings totaling ₹{total_valuation:,.0f} from {filename}"]
        }

    def _process_statement_text(self, text: str, filename: str, user_id: str) -> Dict[str, Any]:
        """
        Analyzes raw statement text for balances, mutual fund schemes, banks.
        """
        # Detect Institution
        institution = "Bank"
        for inst in ["HDFC Bank", "ICICI Bank", "State Bank of India", "Axis Bank", "Zerodha", "Groww", "CAMS", "KFintech"]:
            if inst.lower() in text.lower():
                institution = inst
                break

        # Detect closing balance
        balance_match = re.search(r"(?:closing\s*balance|available\s*balance|net\s*portfolio\s*value|total\s*valuation)[^.\n\d]*?[:=]?\s*(?:inr|rs\.?|₹)?\s*([\d,]+\.?\d*)", text, re.IGNORECASE)
        detected_balance = 0.0
        if balance_match:
            try:
                detected_balance = float(balance_match.group(1).replace(",", ""))
                self.extractor.rel_store.upsert_account(
                    user_id=user_id,
                    institution_name=institution,
                    account_type="SAVINGS" if "bank" in institution.lower() else "DEMAT",
                    balance=detected_balance
                )
            except ValueError:
                pass

        # Run NLP fact extraction on entire document
        extracted_data, actions = self.extractor.extract_and_sync(text, user_id, source="STATEMENT")

        summary = f"Processed {filename} ({institution}). Detected balance: ₹{detected_balance:,.0f}."
        if actions:
            summary += " " + " ".join(actions)

        return {
            "filename": filename,
            "institution": institution,
            "detected_balance": detected_balance,
            "detected_items": len(extracted_data.holdings) + (1 if detected_balance > 0 else 0),
            "actions": actions,
            "summary": summary
        }
