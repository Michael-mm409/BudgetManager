from __future__ import annotations

import sys
from typing import Callable, Optional

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget

from budget.application import DataService
from budget.infrastructure.config_loader import CategoryRepository

from .summary_tab import build_summary_tab
from .transactions_tab import build_transactions_tab


class BudgetMainWindow(QMainWindow):
    # Class-level attribute annotations for static type checkers
    summary_exp_table: object | None
    summary_inc_table: object | None
    _update_summary_fn: Optional[Callable[[], None]] | None

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Budget Manager")
        self.resize(1200, 700)

        repo = CategoryRepository()
        (
            self.EXPENSE_CATEGORIES,
            self.INCOME_CATEGORIES,
            self.PLANNED_EXPENSES,
            self.PLANNED_INCOME,
        ) = repo.load()

        self.service = DataService()
        self.expenses_df, self.income_df = self.service.load_frames()

        # Placeholders (populated by tab builders)
        self.expenses_table_model = None
        self.expenses_table = None
        self.exp_date = None
        self.exp_amount = None
        self.exp_desc = None
        self.exp_cat = None
        self.income_table_model = None
        self.income_table = None
        self.inc_date = None
        self.inc_amount = None
        self.inc_desc = None
        self.inc_cat = None
        self.summary_exp_table = None
        self.summary_inc_table = None
        self._update_summary_fn: Optional[Callable[[], None]] = None

        tabs = QTabWidget()
        tabs.addTab(build_transactions_tab(self), "Transactions")
        tabs.addTab(build_summary_tab(self), "Summary")
        self.setCentralWidget(tabs)

    def reload_data(self) -> None:
        self.expenses_df, self.income_df = self.service.load_frames()

    def reload_and_refresh(self) -> None:
        self.reload_data()
        if self.expenses_table_model is not None:
            self.expenses_table_model.df = self.expenses_df  # type: ignore[attr-defined]
        if self.income_table_model is not None:
            self.income_table_model.df = self.income_df  # type: ignore[attr-defined]
        self.refresh_summary()

    def refresh_summary(self) -> None:
        if self._update_summary_fn:
            self._update_summary_fn()


def run_app():
    app = QApplication(sys.argv)
    win = BudgetMainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover
    from budget.infrastructure.db.connection import init_db

    init_db()
    sys.exit(run_app())
