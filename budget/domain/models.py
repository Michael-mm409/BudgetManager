from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class Transaction:
    id: int | None
    date: date
    amount: float
    description: str
    category: str
    type: str  # 'expense' or 'income'
