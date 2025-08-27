from __future__ import annotations

import datetime as _dt
import sqlite3
from pathlib import Path
from typing import Sequence

# Runtime database goes into project-level var/ (not packaged code dir)
# Directory structure assumption: app/budget/infrastructure/db/connection.py
# parents: 0=db,1=infrastructure,2=budget,3=app,4=project root
PROJECT_ROOT = Path(__file__).resolve().parents[4]
RUNTIME_DIR = PROJECT_ROOT / "var"
RUNTIME_DIR.mkdir(exist_ok=True)
DB_FILE = RUNTIME_DIR / "budget.db"

SCHEMA_STATEMENTS: Sequence[str] = (
    """
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        category TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS income (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        category TEXT
    )
    """,
)


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_FILE)


def init_db() -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        for stmt in SCHEMA_STATEMENTS:
            cur.execute(stmt)
        conn.commit()
    finally:
        conn.close()


def _format_date(value) -> str:
    """Return date value as dd-mm-YYYY string.

    Accepts date/datetime or preformatted string. Leaves string that already
    matches desired pattern untouched; otherwise attempts to parse common
    ISO format and reformat.
    """
    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.strftime("%d-%m-%Y")
    if isinstance(value, str):
        # Fast path: already desired format
        if len(value) == 10 and value[2] == "-" and value[5] == "-":
            return value
        # Try parse ISO then format
        try:
            parsed = _dt.datetime.strptime(value, "%Y-%m-%d")
            return parsed.strftime("%d-%m-%Y")
        except Exception:
            # Fall back to dateutil-like loose parse (avoid dependency) - leave as is
            return value
    raise TypeError("Unsupported date value type")


def insert_expense(date, amount: float, description: str, category: str) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO expenses (date, amount, description, category) VALUES (?, ?, ?, ?)",
            (_format_date(date), amount, description, category),
        )
        conn.commit()
    finally:
        conn.close()


def insert_income(date, amount: float, description: str, category: str) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO income (date, amount, description, category) VALUES (?, ?, ?, ?)",
            (_format_date(date), amount, description, category),
        )
        conn.commit()
    finally:
        conn.close()


# ---- Update / Delete helpers -------------------------------------------------


def update_expense(expense_id: int, date, amount: float, description: str, category: str) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE expenses SET date = ?, amount = ?, description = ?, category = ? WHERE id = ?",
            (_format_date(date), amount, description, category, expense_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_expense(expense_id: int) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
    finally:
        conn.close()


def update_income(income_id: int, date, amount: float, description: str, category: str) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE income SET date = ?, amount = ?, description = ?, category = ? WHERE id = ?",
            (_format_date(date), amount, description, category, income_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_income(income_id: int) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM income WHERE id = ?", (income_id,))
        conn.commit()
    finally:
        conn.close()
