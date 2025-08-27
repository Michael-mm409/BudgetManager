from __future__ import annotations

import csv
import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

# Default packaged data directory (read-only defaults)
PACKAGE_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PACKAGE_DATA_DIR.mkdir(exist_ok=True)
DEFAULT_CATEGORIES_FILE = PACKAGE_DATA_DIR / "categories.csv"

# Override locations (highest precedence first):
# 1. Project root categories.csv (adjacent to README when running from source)
# 2. User config directory (platform-dependent)
# 3. Packaged default (inside package data)


def _user_config_dir() -> Path:
    # Windows: %APPDATA%/BudgetApp ; others: ~/.config/budget
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "BudgetApp"
    # POSIX
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "budget"
    return Path.home() / ".config" / "budget"


ROOT_CANDIDATE = (
    (Path(__file__).resolve().parents[4] / "categories.csv") if len(Path(__file__).resolve().parents) >= 5 else None
)
USER_CONFIG_DIR = _user_config_dir()
USER_CONFIG_FILE = USER_CONFIG_DIR / "categories.csv"


def _resolve_csv_path() -> Path:
    for candidate in [ROOT_CANDIDATE, USER_CONFIG_FILE, DEFAULT_CATEGORIES_FILE]:
        if candidate and candidate.exists():
            return candidate
    # If none exist, fallback to default path (may not exist yet) so caller can create
    return DEFAULT_CATEGORIES_FILE


@dataclass
class CategoryPlan:
    type: str  # 'expense' or 'income'
    category: str
    planned: float


class CategoryRepository:
    def __init__(self, csv_path: Path | None = None, auto_create: bool = True):
        self.logger = logging.getLogger(__name__)
        resolved = csv_path or _resolve_csv_path()
        self.source = "package-default"
        if resolved == ROOT_CANDIDATE:
            self.source = "root"
        elif resolved == USER_CONFIG_FILE:
            self.source = "user-config"
        elif resolved == DEFAULT_CATEGORIES_FILE:
            self.source = "package-default"
        self.csv_path = resolved

        # Ensure existence (create user-config copy or template)
        if auto_create and not self.csv_path.exists():
            try:
                USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                if DEFAULT_CATEGORIES_FILE.exists():
                    shutil.copy(DEFAULT_CATEGORIES_FILE, USER_CONFIG_FILE)
                    self.csv_path = USER_CONFIG_FILE
                    self.source = "user-config-copied"
                    self.logger.info("Copied default categories.csv to %s", USER_CONFIG_FILE)
                else:
                    # Create minimal template file
                    with USER_CONFIG_FILE.open("w", encoding="utf-8", newline="") as tf:
                        tf.write("type,category,planned\n")
                        tf.write("expense,Other,0\n")
                        tf.write("income,Other,0\n")
                    self.csv_path = USER_CONFIG_FILE
                    self.source = "user-config-created"
                    self.logger.info("Created minimal categories.csv at %s", USER_CONFIG_FILE)
            except Exception as e:
                self.logger.warning("Could not create categories.csv override: %s", e)

        # If still pointing at packaged default, optionally copy to user-config for editing convenience
        if self.csv_path == DEFAULT_CATEGORIES_FILE and DEFAULT_CATEGORIES_FILE.exists():
            try:
                if not USER_CONFIG_FILE.exists():
                    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                    shutil.copy(DEFAULT_CATEGORIES_FILE, USER_CONFIG_FILE)
                    self.csv_path = USER_CONFIG_FILE
                    self.source = "user-config-copied"
                    self.logger.info("Copied default categories.csv to %s", USER_CONFIG_FILE)
            except Exception as e:
                self.logger.debug("Skip copy to user config: %s", e)

    def load(self) -> Tuple[List[str], List[str], Dict[str, float], Dict[str, float]]:
        expense_categories: List[str] = []
        income_categories: List[str] = []
        planned_expenses: Dict[str, float] = {}
        planned_income: Dict[str, float] = {}
        if not self.csv_path.exists():
            expense_categories = ["Totals", "Other"]
            income_categories = ["Totals", "Other"]
            planned_expenses = {"Totals": 0.0, "Other": 0.0}
            planned_income = {"Totals": 0.0, "Other": 0.0}
            return expense_categories, income_categories, planned_expenses, planned_income

        with self.csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ctype = (row.get("type") or "").strip().lower()
                category = (row.get("category") or "").strip() or "Other"
                try:
                    planned = float(row.get("planned") or 0)
                except ValueError:
                    planned = 0.0
                if ctype == "expense":
                    if category not in expense_categories:
                        expense_categories.append(category)
                    planned_expenses[category] = planned
                elif ctype == "income":
                    if category not in income_categories:
                        income_categories.append(category)
                    planned_income[category] = planned

        def order(lst: List[str]) -> List[str]:
            return (["Totals"] if "Totals" in lst else []) + [c for c in lst if c != "Totals"]

        return (
            order(expense_categories),
            order(income_categories),
            planned_expenses,
            planned_income,
        )


def get_active_categories_file() -> Path:
    repo = CategoryRepository(auto_create=False)
    return repo.csv_path


def describe_categories_source() -> str:
    repo = CategoryRepository(auto_create=False)
    return f"{repo.csv_path} (source={repo.source})"
