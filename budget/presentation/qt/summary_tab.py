from __future__ import annotations

import calendar
from datetime import date
from typing import TYPE_CHECKING, Any, cast

import pandas as pd
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from budget.infrastructure.config_loader import CategoryRepository
from budget.infrastructure.config_loader import categories_loader as _cat_mod

if TYPE_CHECKING:  # pragma: no cover
    from .main_window import BudgetMainWindow

from .models import PandasModel
from .plan_editor_dialog import PlanEditorDialog


def build_summary_tab(window: "BudgetMainWindow") -> QWidget:
    """Create the Summary tab and attach update callback to the window.

    The window is expected to expose:
      - EXPENSE_CATEGORIES, INCOME_CATEGORIES
      - PLANNED_EXPENSES, PLANNED_INCOME
      - expenses_df, income_df (dataframes)
      - refresh_summary() method (uses _update_summary_fn if present)
    """
    tab = QWidget()
    layout = QVBoxLayout(tab)
    top_bar = QHBoxLayout()
    # Month/Year selectors (no calendar popup)
    top_bar.addWidget(QLabel("Month"))
    month_combo = QComboBox()
    month_names = [calendar.month_name[month_index] for month_index in range(1, 13)]
    month_combo.addItems(month_names)
    current_qdate = QDate.currentDate()
    month_combo.setCurrentIndex(current_qdate.month() - 1)
    top_bar.addWidget(month_combo)
    top_bar.addWidget(QLabel("Year"))
    year_spin = QSpinBox()
    year_spin.setRange(2000, 2100)
    year_spin.setValue(current_qdate.year())
    top_bar.addWidget(year_spin)
    top_bar.addStretch(1)
    edit_plans_btn = QPushButton("Edit Planned Amounts")
    top_bar.addWidget(edit_plans_btn)
    layout.addLayout(top_bar)

    tables = QHBoxLayout()
    layout.addLayout(tables)

    exp_box = QVBoxLayout()
    exp_box.addWidget(QLabel("Expenses"))
    setattr(window, "summary_exp_table", QTableView())
    exp_box.addWidget(cast(Any, getattr(window, "summary_exp_table")))
    tables.addLayout(exp_box)

    inc_box = QVBoxLayout()
    inc_box.addWidget(QLabel("Income"))
    setattr(window, "summary_inc_table", QTableView())
    inc_box.addWidget(cast(Any, getattr(window, "summary_inc_table")))
    tables.addLayout(inc_box)

    def update_summary() -> None:
        selected_name = month_combo.currentText()
        try:
            month_num = month_names.index(selected_name) + 1
        except ValueError:  # fallback safeguard
            month_num = QDate.currentDate().month()
        selected = date(year_spin.value(), month_num, 1)
        period = pd.Period(selected, freq="M")
        exp_dates = pd.to_datetime(window.expenses_df["date"], errors="coerce", dayfirst=True)
        inc_dates = pd.to_datetime(window.income_df["date"], errors="coerce", dayfirst=True)
        exp_mask = exp_dates.dt.to_period("M") == period
        inc_mask = inc_dates.dt.to_period("M") == period
        exp = window.expenses_df[exp_mask]
        inc = window.income_df[inc_mask]
        exp_actuals = exp.groupby("category")["amount"].sum().to_dict()
        inc_actuals = inc.groupby("category")["amount"].sum().to_dict()

        rows_exp: list[list[str]] = []
        for cat in window.EXPENSE_CATEGORIES:
            planned = window.PLANNED_EXPENSES.get(cat, 0.0)
            actual = exp["amount"].sum() if cat == "Totals" else exp_actuals.get(cat, 0.0)
            diff = planned - actual
            rows_exp.append([cat, f"${planned:.2f}", f"${actual:.2f}", f"${diff:+.2f}"])
        cast(Any, getattr(window, "summary_exp_table")).setModel(
            PandasModel(
                pd.DataFrame(
                    rows_exp,
                    columns=["Category", "Planned", "Actual", "Diff."],
                )
            )
        )
        rows_inc: list[list[str]] = []
        for cat in window.INCOME_CATEGORIES:
            planned = window.PLANNED_INCOME.get(cat, 0.0)
            actual = inc["amount"].sum() if cat == "Totals" else inc_actuals.get(cat, 0.0)
            diff = planned - actual
            rows_inc.append([cat, f"${planned:.2f}", f"${actual:.2f}", f"${diff:+.2f}"])
        cast(Any, getattr(window, "summary_inc_table")).setModel(
            PandasModel(
                pd.DataFrame(
                    rows_inc,
                    columns=["Category", "Planned", "Actual", "Diff."],
                )
            )
        )

    month_combo.currentIndexChanged.connect(lambda _i: update_summary())  # type: ignore[arg-type]
    year_spin.valueChanged.connect(lambda _v: update_summary())  # type: ignore[arg-type]
    update_summary()
    setattr(window, "_update_summary_fn", update_summary)  # noqa: SLF001

    def open_plan_editor() -> None:
        dlg = PlanEditorDialog(
            window,
            expense_categories=[c for c in window.EXPENSE_CATEGORIES if c != "Totals"],
            income_categories=[c for c in window.INCOME_CATEGORIES if c != "Totals"],
            expense_plans=window.PLANNED_EXPENSES,
            income_plans=window.PLANNED_INCOME,
            used_expense_categories=set(window.expenses_df.get("category", [])),
            used_income_categories=set(window.income_df.get("category", [])),
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            exp_plans, inc_plans = dlg.get_plans()
            _cat_mod.save_category_plans(exp_plans, inc_plans, window.EXPENSE_CATEGORIES, window.INCOME_CATEGORIES)
            repo = CategoryRepository()
            (
                window.EXPENSE_CATEGORIES,
                window.INCOME_CATEGORIES,
                window.PLANNED_EXPENSES,
                window.PLANNED_INCOME,
            ) = repo.load()
            window.refresh_summary()

    edit_plans_btn.clicked.connect(open_plan_editor)  # type: ignore[arg-type]
    return tab


__all__ = ["build_summary_tab"]
