"""
Relational / Tabular Data Layer (SQLite).
Provides mathematical precision for financial ledgers, account balances,
equity/mutual fund holdings, transactions, and numeric goal tracking.
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), "financial_ledger.db")


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_relational_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        currency TEXT DEFAULT 'INR',
        monthly_income REAL DEFAULT 150000,
        monthly_expenses REAL DEFAULT 65000,
        risk_profile TEXT DEFAULT 'Moderate',
        created_at TEXT
    );
    """)

    # Accounts (Bank accounts, Demat, EPF, etc.)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        institution_name TEXT NOT NULL,
        account_type TEXT NOT NULL, -- SAVINGS, DEMAT, MUTUAL_FUND, EPF, NPS
        account_number_masked TEXT,
        balance REAL NOT NULL,
        currency TEXT DEFAULT 'INR',
        last_synced_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)

    # Holdings (Individual stocks, MF schemes, Gold, Real Estate)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS holdings (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        account_id TEXT,
        asset_type TEXT NOT NULL, -- EQUITY, MUTUAL_FUND, DEBT, GOLD, REAL_ESTATE, LIQUID
        asset_name TEXT NOT NULL,
        symbol TEXT,
        units REAL,
        avg_buy_price REAL,
        current_value REAL NOT NULL,
        updated_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (account_id) REFERENCES accounts (id)
    );
    """)

    # Transactions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        account_id TEXT NOT NULL,
        date TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        type TEXT NOT NULL, -- CREDIT, DEBIT
        FOREIGN KEY (account_id) REFERENCES accounts (id)
    );
    """)

    # Life Goals
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS life_goals (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL, -- EDUCATION, RETIREMENT, HOME, VEHICLE, EMERGENCY
        target_amount REAL NOT NULL,
        target_year INTEGER NOT NULL,
        accumulated_amount REAL DEFAULT 0,
        priority TEXT DEFAULT 'High',
        status TEXT DEFAULT 'IN_PROGRESS',
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)

    # Extracted Facts Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS extracted_facts (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        source TEXT NOT NULL, -- CHAT, VOICE, STATEMENT, API
        raw_text TEXT,
        extracted_json TEXT,
        applied_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)

    conn.commit()
    conn.close()


class RelationalStore:
    def __init__(self):
        init_relational_db()

    def get_user(self, user_id: str = "default_user") -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        return dict(user) if user else None

    def get_accounts(self, user_id: str = "default_user") -> List[Dict[str, Any]]:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM accounts WHERE user_id = ?", (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_holdings(self, user_id: str = "default_user") -> List[Dict[str, Any]]:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM holdings WHERE user_id = ? ORDER BY current_value DESC", (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_goals(self, user_id: str = "default_user") -> List[Dict[str, Any]]:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM life_goals WHERE user_id = ? ORDER BY target_year ASC", (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_recent_transactions(self, user_id: str = "default_user", limit: int = 15) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT t.*, a.institution_name, a.account_type 
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            WHERE a.user_id = ?
            ORDER BY t.date DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_portfolio_summary(self, user_id: str = "default_user") -> Dict[str, Any]:
        conn = get_db_connection()
        user = self.get_user(user_id)
        if not user:
            conn.close()
            return {}

        # Holdings breakdown
        holdings = self.get_holdings(user_id)
        accounts = self.get_accounts(user_id)
        goals = self.get_goals(user_id)

        # Asset class allocations
        allocation_map: Dict[str, float] = {}
        total_holdings_val = 0.0
        for h in holdings:
            val = float(h["current_value"])
            total_holdings_val += val
            atype = h["asset_type"]
            allocation_map[atype] = allocation_map.get(atype, 0.0) + val

        # Cash & Liquid in accounts (not represented in holdings)
        bank_liquid = sum(float(a["balance"]) for a in accounts if a["account_type"] == "SAVINGS")
        if bank_liquid > 0:
            allocation_map["LIQUID"] = allocation_map.get("LIQUID", 0.0) + bank_liquid

        net_worth = total_holdings_val + bank_liquid
        monthly_income = float(user.get("monthly_income", 150000))
        monthly_expenses = float(user.get("monthly_expenses", 65000))
        monthly_savings = monthly_income - monthly_expenses

        # Allocation percentages
        allocations = []
        for cat, val in allocation_map.items():
            pct = round((val / net_worth * 100), 1) if net_worth > 0 else 0
            allocations.append({
                "asset_class": cat,
                "value": round(val, 2),
                "percentage": pct
            })

        conn.close()
        return {
            "user": user,
            "net_worth": round(net_worth, 2),
            "monthly_income": monthly_income,
            "monthly_expenses": monthly_expenses,
            "monthly_savings": monthly_savings,
            "allocations": allocations,
            "holdings": holdings,
            "accounts": accounts,
            "goals": goals
        }

    def upsert_holding(
        self,
        user_id: str,
        asset_type: str,
        asset_name: str,
        current_value: float,
        symbol: Optional[str] = None,
        units: Optional[float] = None,
        avg_buy_price: Optional[float] = None,
        account_id: Optional[str] = None
    ) -> str:
        conn = get_db_connection()
        now = datetime.now().isoformat()
        
        # Check if holding exists for this asset_name & asset_type
        existing = conn.execute(
            "SELECT id FROM holdings WHERE user_id = ? AND asset_type = ? AND LOWER(asset_name) = LOWER(?)",
            (user_id, asset_type, asset_name)
        ).fetchone()

        if existing:
            holding_id = existing["id"]
            conn.execute("""
                UPDATE holdings 
                SET current_value = ?, units = COALESCE(?, units), avg_buy_price = COALESCE(?, avg_buy_price), updated_at = ?
                WHERE id = ?
            """, (current_value, units, avg_buy_price, now, holding_id))
        else:
            holding_id = f"hld_{int(datetime.now().timestamp() * 1000)}"
            conn.execute("""
                INSERT INTO holdings (id, user_id, account_id, asset_type, asset_name, symbol, units, avg_buy_price, current_value, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (holding_id, user_id, account_id, asset_type, asset_name, symbol, units, avg_buy_price, current_value, now))

        conn.commit()
        conn.close()
        return holding_id

    def upsert_account(
        self,
        user_id: str,
        institution_name: str,
        account_type: str,
        balance: float,
        account_number_masked: str = "XXXX-XXXX"
    ) -> str:
        conn = get_db_connection()
        now = datetime.now().isoformat()
        
        existing = conn.execute(
            "SELECT id FROM accounts WHERE user_id = ? AND LOWER(institution_name) = LOWER(?) AND account_type = ?",
            (user_id, institution_name, account_type)
        ).fetchone()

        if existing:
            acc_id = existing["id"]
            conn.execute(
                "UPDATE accounts SET balance = ?, account_number_masked = ?, last_synced_at = ? WHERE id = ?",
                (balance, account_number_masked, now, acc_id)
            )
        else:
            acc_id = f"acc_{int(datetime.now().timestamp() * 1000)}"
            conn.execute(
                "INSERT INTO accounts (id, user_id, institution_name, account_type, account_number_masked, balance, last_synced_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (acc_id, user_id, institution_name, account_type, account_number_masked, balance, now)
            )

        conn.commit()
        conn.close()
        return acc_id

    def upsert_goal(
        self,
        user_id: str,
        title: str,
        category: str,
        target_amount: float,
        target_year: int,
        accumulated_amount: float = 0.0,
        priority: str = "High"
    ) -> str:
        conn = get_db_connection()
        existing = conn.execute(
            "SELECT id FROM life_goals WHERE user_id = ? AND LOWER(title) = LOWER(?)",
            (user_id, title)
        ).fetchone()

        if existing:
            goal_id = existing["id"]
            conn.execute("""
                UPDATE life_goals 
                SET target_amount = ?, target_year = ?, accumulated_amount = ?, priority = ?
                WHERE id = ?
            """, (target_amount, target_year, accumulated_amount, priority, goal_id))
        else:
            goal_id = f"goal_{int(datetime.now().timestamp() * 1000)}"
            conn.execute("""
                INSERT INTO life_goals (id, user_id, title, category, target_amount, target_year, accumulated_amount, priority, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'IN_PROGRESS')
            """, (goal_id, user_id, title, category, target_amount, target_year, accumulated_amount, priority))

        conn.commit()
        conn.close()
        return goal_id

    def log_extracted_fact(self, user_id: str, source: str, raw_text: str, extracted_dict: Dict[str, Any]):
        conn = get_db_connection()
        fact_id = f"fact_{int(datetime.now().timestamp() * 1000)}"
        conn.execute("""
            INSERT INTO extracted_facts (id, user_id, source, raw_text, extracted_json, applied_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (fact_id, user_id, source, raw_text, json.dumps(extracted_dict), datetime.now().isoformat()))
        conn.commit()
        conn.close()
