from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from budget.infrastructure.db import (
    delete_expense,
    delete_income,
    insert_expense,
    insert_income,
    update_expense,
    update_income,
)

from .bullet_utils import apply_bullets
from .models import PandasModel
from .selection import selected_row_id
from .ui_text import (
    BTN_ADD,
    BTN_BULLETS,
    BTN_DELETE,
    BTN_UPDATE,
    LBL_AMOUNT,
    LBL_CAT,
    LBL_DATE,
    LBL_DESC,
    TITLE_EXPENSES,
    TITLE_INCOME,
)
from .validators import make_amount_validator, validate_amount, validate_date


@dataclass
class TransactionForm:
    date: QDateEdit
    amount: QLineEdit
    desc: QTextEdit
    cat: QComboBox
    table: QTableView
    model: PandasModel


def _populate_row(form: TransactionForm, df: pd.DataFrame) -> None:
    rid = selected_row_id(form.table, df)
    if rid is None:
        return
    row = df[df["id"] == rid].iloc[0]
    d = pd.to_datetime(row["date"], errors="coerce")
    if pd.isna(d):
        d = pd.Timestamp.today()
    form.date.setDate(QDate(d.year, d.month, d.day))
    form.amount.setText(str(row.get("amount", "")))
    form.desc.setPlainText(str(row.get("description", "")))
    cat = str(row.get("category", ""))
    idx = form.cat.findText(cat)
    if idx >= 0:
        form.cat.setCurrentIndex(idx)


def _build_side(
    parent, title: str, categories: list[str], df: pd.DataFrame
) -> tuple[QVBoxLayout, TransactionForm, dict[str, QPushButton]]:
    box = QVBoxLayout()
    box.addWidget(QLabel(title))
    model = PandasModel(df)
    table = QTableView()
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setModel(model)
    box.addWidget(table)

    date = QDateEdit()
    date.setCalendarPopup(True)
    date.setDate(QDate.currentDate())
    amount = QLineEdit()
    amount.setPlaceholderText(LBL_AMOUNT)
    desc = QTextEdit()
    desc.setPlaceholderText("Description (multi-line)")
    desc.setFixedHeight(90)
    cat = QComboBox()
    for c in categories:
        if c != "Totals":
            cat.addItem(c)

    bullets_btn = QPushButton(BTN_BULLETS)
    add_btn = QPushButton(BTN_ADD)
    upd_btn = QPushButton(BTN_UPDATE)
    del_btn = QPushButton(BTN_DELETE)

    form_layout = QHBoxLayout()
    for w in [
        QLabel(LBL_DATE),
        date,
        QLabel(LBL_AMOUNT),
        amount,
        QLabel(LBL_DESC),
        desc,
        bullets_btn,
        QLabel(LBL_CAT),
        cat,
        add_btn,
        upd_btn,
        del_btn,
    ]:
        form_layout.addWidget(w)
    box.addLayout(form_layout)

    form = TransactionForm(date=date, amount=amount, desc=desc, cat=cat, table=table, model=model)
    return box, form, {"bullets": bullets_btn, "add": add_btn, "update": upd_btn, "delete": del_btn}


def build_transactions_tab(window) -> QWidget:
    tab = QWidget()
    layout = QHBoxLayout(tab)

    exp_box, exp_form, exp_btns = _build_side(window, TITLE_EXPENSES, window.EXPENSE_CATEGORIES, window.expenses_df)
    inc_box, inc_form, inc_btns = _build_side(window, TITLE_INCOME, window.INCOME_CATEGORIES, window.income_df)

    window.expenses_table_model = exp_form.model
    window.expenses_table = exp_form.table
    window.exp_date = exp_form.date
    window.exp_amount = exp_form.amount
    window.exp_desc = exp_form.desc
    window.exp_cat = exp_form.cat

    window.income_table_model = inc_form.model
    window.income_table = inc_form.table
    window.inc_date = inc_form.date
    window.inc_amount = inc_form.amount
    window.inc_desc = inc_form.desc
    window.inc_cat = inc_form.cat

    layout.addLayout(exp_box)
    layout.addLayout(inc_box)

    # Validators
    amt_val = make_amount_validator(window)
    window.exp_amount.setValidator(amt_val)
    window.inc_amount.setValidator(amt_val)

    def populate_exp():
        _populate_row(exp_form, window.expenses_df)

    def populate_inc():
        _populate_row(inc_form, window.income_df)

    window.expenses_table.selectionModel().selectionChanged.connect(lambda *_: populate_exp())  # type: ignore[arg-type]
    window.income_table.selectionModel().selectionChanged.connect(lambda *_: populate_inc())  # type: ignore[arg-type]
    exp_btns["bullets"].clicked.connect(lambda: apply_bullets(window.exp_desc))  # type: ignore[arg-type]
    inc_btns["bullets"].clicked.connect(lambda: apply_bullets(window.inc_desc))  # type: ignore[arg-type]

    # CRUD generic helpers
    def add(kind: str):
        if kind == "expense":
            date_q = validate_date(window.exp_date)
            amt = validate_amount(window.exp_amount)
            if date_q is None or amt is None:
                QMessageBox.warning(window, "Invalid Data", "Fix highlighted fields before adding expense.")
                return
            insert_expense(
                date_q.toPyDate(), amt, window.exp_desc.toPlainText(), window.exp_cat.currentText() or "Other"
            )
        else:
            date_q = validate_date(window.inc_date)
            amt = validate_amount(window.inc_amount)
            if date_q is None or amt is None:
                QMessageBox.warning(window, "Invalid Data", "Fix highlighted fields before adding income.")
                return
            insert_income(
                date_q.toPyDate(), amt, window.inc_desc.toPlainText(), window.inc_cat.currentText() or "Other"
            )
        window.reload_and_refresh()

    def update(kind: str):
        if kind == "expense":
            rid = selected_row_id(window.expenses_table, window.expenses_df)
            if rid is None:
                QMessageBox.information(window, "Update Expense", "Select a row first")
                return
            date_q = validate_date(window.exp_date)
            amt = validate_amount(window.exp_amount)
            if date_q is None or amt is None:
                QMessageBox.warning(window, "Invalid Data", "Fix highlighted fields before updating expense.")
                return
            update_expense(
                rid, date_q.toPyDate(), amt, window.exp_desc.toPlainText(), window.exp_cat.currentText() or "Other"
            )
        else:
            rid = selected_row_id(window.income_table, window.income_df)
            if rid is None:
                QMessageBox.information(window, "Update Income", "Select a row first")
                return
            date_q = validate_date(window.inc_date)
            amt = validate_amount(window.inc_amount)
            if date_q is None or amt is None:
                QMessageBox.warning(window, "Invalid Data", "Fix highlighted fields before updating income.")
                return
            update_income(
                rid, date_q.toPyDate(), amt, window.inc_desc.toPlainText(), window.inc_cat.currentText() or "Other"
            )
        window.reload_and_refresh()

    def delete(kind: str):
        if kind == "expense":
            rid = selected_row_id(window.expenses_table, window.expenses_df)
            if rid is None:
                QMessageBox.information(window, "Delete Expense", "Select a row first")
                return
            if QMessageBox.question(window, "Delete", "Delete selected expense?") != QMessageBox.StandardButton.Yes:
                return
            delete_expense(rid)
        else:
            rid = selected_row_id(window.income_table, window.income_df)
            if rid is None:
                QMessageBox.information(window, "Delete Income", "Select a row first")
                return
            if QMessageBox.question(window, "Delete", "Delete selected income?") != QMessageBox.StandardButton.Yes:
                return
            delete_income(rid)
        window.reload_and_refresh()

    exp_btns["add"].clicked.connect(lambda: add("expense"))  # type: ignore[arg-type]
    exp_btns["update"].clicked.connect(lambda: update("expense"))  # type: ignore[arg-type]
    exp_btns["delete"].clicked.connect(lambda: delete("expense"))  # type: ignore[arg-type]
    inc_btns["add"].clicked.connect(lambda: add("income"))  # type: ignore[arg-type]
    inc_btns["update"].clicked.connect(lambda: update("income"))  # type: ignore[arg-type]
    inc_btns["delete"].clicked.connect(lambda: delete("income"))  # type: ignore[arg-type]

    return tab


__all__ = ["build_transactions_tab", "TransactionForm"]
