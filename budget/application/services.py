from __future__ import annotations

import pandas as pd

from budget.infrastructure.db import get_connection


class DataService:
    def load_frames(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        conn = get_connection()
        try:
            expenses = pd.read_sql("SELECT * FROM expenses", conn)
            income = pd.read_sql("SELECT * FROM income", conn)
        finally:
            conn.close()
        # Normalize date columns to datetime64 (handle multiple possible stored formats)

        def _normalize(df: pd.DataFrame) -> None:
            if df.empty or "date" not in df.columns:
                return
            col = df["date"]
            # If already datetime-like, nothing to do
            if pd.api.types.is_datetime64_any_dtype(col):
                return
            # Try dd-mm-YYYY
            dt = pd.to_datetime(col, format="%d-%m-%Y", errors="coerce")
            # If many NaT, try ISO YYYY-MM-DD
            if dt.isna().mean() > 0.5:
                dt2 = pd.to_datetime(col, format="%Y-%m-%d", errors="coerce")
                # Choose better parse (fewer NaT)
                if dt2.isna().sum() < dt.isna().sum():
                    dt = dt2
            # Final fallback: generic parse with dayfirst True
            if dt.isna().all():
                dt = pd.to_datetime(col, errors="coerce", dayfirst=True)
            df["date"] = dt

        _normalize(expenses)
        _normalize(income)
        return expenses, income
