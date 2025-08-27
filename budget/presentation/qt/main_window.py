from __future__ import annotations

import sys

import pandas as pd
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableView,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from budget.application import DataService
from budget.infrastructure.config_loader import CategoryRepository
from budget.infrastructure.db import (
    delete_expense,
    delete_income,
    insert_expense,
    insert_income,
    update_expense,
    update_income,
)

from .models import PandasModel


class BudgetMainWindow(QMainWindow):
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

        tabs = QTabWidget()
        tabs.addTab(self._build_transactions_tab(), "Transactions")
        tabs.addTab(self._build_summary_tab(), "Summary")
        self.setCentralWidget(tabs)

    # -------- Data reload --------
    def reload_data(self) -> None:
        self.expenses_df, self.income_df = self.service.load_frames()

    def reload_and_refresh(self) -> None:
        self.reload_data()
        self.expenses_table_model.df = self.expenses_df
        self.income_table_model.df = self.income_df
        self.refresh_summary()

    # -------- Transactions Tab --------
    def _build_transactions_tab(self) -> QWidget:
        tab = QWidget()
        layout = QHBoxLayout(tab)

        # Expenses column -------------------------------------------------
        exp_col = QVBoxLayout()
        exp_col.addWidget(QLabel("Expenses"))
        self.expenses_table_model = PandasModel(self.expenses_df)
        self.expenses_table = QTableView()
        self.expenses_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.expenses_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.expenses_table.setModel(self.expenses_table_model)
        exp_col.addWidget(self.expenses_table)

        self.exp_date = QDateEdit()
        self.exp_date.setCalendarPopup(True)
        self.exp_date.setDate(QDate.currentDate())
        self.exp_amount = QLineEdit()
        self.exp_amount.setPlaceholderText("Amount")
        self.exp_desc = QTextEdit()
        self.exp_desc.setPlaceholderText("Description (multi-line)")
        self.exp_desc.setFixedHeight(90)
        self.exp_cat = QComboBox()
        for cat in [c for c in self.EXPENSE_CATEGORIES if c != "Totals"]:
            self.exp_cat.addItem(cat)
        exp_bullets_btn = QPushButton("Bullets")
        exp_add_btn = QPushButton("Add")
        exp_update_btn = QPushButton("Update")
        exp_delete_btn = QPushButton("Delete")

        exp_form = QHBoxLayout()
        for w in [
            QLabel("Date"),
            self.exp_date,
            QLabel("Amount"),
            self.exp_amount,
            QLabel("Desc"),
            self.exp_desc,
            exp_bullets_btn,
            QLabel("Cat"),
            self.exp_cat,
            exp_add_btn,
            exp_update_btn,
            exp_delete_btn,
        ]:
            exp_form.addWidget(w)
        exp_col.addLayout(exp_form)
        layout.addLayout(exp_col)

        # Income column ---------------------------------------------------
        inc_col = QVBoxLayout()
        inc_col.addWidget(QLabel("Income"))
        self.income_table_model = PandasModel(self.income_df)
        self.income_table = QTableView()
        self.income_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.income_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.income_table.setModel(self.income_table_model)
        inc_col.addWidget(self.income_table)

        self.inc_date = QDateEdit()
        self.inc_date.setCalendarPopup(True)
        self.inc_date.setDate(QDate.currentDate())
        self.inc_amount = QLineEdit()
        self.inc_amount.setPlaceholderText("Amount")
        self.inc_desc = QTextEdit()
        self.inc_desc.setPlaceholderText("Description (multi-line)")
        self.inc_desc.setFixedHeight(90)
        self.inc_cat = QComboBox()
        for cat in [c for c in self.INCOME_CATEGORIES if c != "Totals"]:
            self.inc_cat.addItem(cat)
        inc_bullets_btn = QPushButton("Bullets")
        inc_add_btn = QPushButton("Add")
        inc_update_btn = QPushButton("Update")
        inc_delete_btn = QPushButton("Delete")

        inc_form = QHBoxLayout()
        for w in [
            QLabel("Date"),
            self.inc_date,
            QLabel("Amount"),
            self.inc_amount,
            QLabel("Desc"),
            self.inc_desc,
            inc_bullets_btn,
            QLabel("Cat"),
            self.inc_cat,
            inc_add_btn,
            inc_update_btn,
            inc_delete_btn,
        ]:
            inc_form.addWidget(w)
        inc_col.addLayout(inc_form)
        layout.addLayout(inc_col)

        # Validation helpers ----------------------------------------------
        amt_validator = QDoubleValidator(0.0, 1_000_000_000.0, 2, self)
        self.exp_amount.setValidator(amt_validator)
        self.inc_amount.setValidator(amt_validator)

        def _clear_error(widget):
            widget.setStyleSheet("")

        def _mark_error(widget):
            widget.setStyleSheet("border:1px solid red")

        def _validate_amount(edit: QLineEdit) -> float | None:
            text = edit.text().strip()
            if not text:
                _mark_error(edit)
                return None
            try:
                val = float(text)
            except ValueError:
                _mark_error(edit)
                return None
            if val < 0:
                _mark_error(edit)
                return None
            _clear_error(edit)
            return val

        def _validate_date(d_edit: QDateEdit) -> QDate | None:
            d = d_edit.date()
            if not d.isValid() or d > QDate.currentDate():
                _mark_error(d_edit)
                return None
            _clear_error(d_edit)
            return d

        def _selected_row_id(table: QTableView, df: pd.DataFrame) -> int | None:
            sel = table.selectionModel()
            if sel is None:
                return None
            rows = sel.selectedRows()
            if not rows:
                return None
            r = rows[0].row()
            try:
                return int(df.iloc[r]["id"])  # type: ignore[index]
            except Exception:
                return None

        def _populate(which: str) -> None:
            if which == "exp":
                rid = _selected_row_id(self.expenses_table, self.expenses_df)
                if rid is None:
                    return
                row = self.expenses_df[self.expenses_df["id"] == rid].iloc[0]
                d = pd.to_datetime(row["date"], errors="coerce")
                if pd.isna(d):
                    d = pd.Timestamp.today()
                self.exp_date.setDate(QDate(d.year, d.month, d.day))
                self.exp_amount.setText(str(row.get("amount", "")))
                self.exp_desc.setPlainText(str(row.get("description", "")))
                cat = str(row.get("category", ""))
                idx = self.exp_cat.findText(cat)
                if idx >= 0:
                    self.exp_cat.setCurrentIndex(idx)
            else:
                rid = _selected_row_id(self.income_table, self.income_df)
                if rid is None:
                    return
                row = self.income_df[self.income_df["id"] == rid].iloc[0]
                d = pd.to_datetime(row["date"], errors="coerce")
                if pd.isna(d):
                    d = pd.Timestamp.today()
                self.inc_date.setDate(QDate(d.year, d.month, d.day))
                self.inc_amount.setText(str(row.get("amount", "")))
                self.inc_desc.setPlainText(str(row.get("description", "")))
                cat = str(row.get("category", ""))
                idx = self.inc_cat.findText(cat)
                if idx >= 0:
                    self.inc_cat.setCurrentIndex(idx)

        def _apply_bullets(edit: QTextEdit) -> None:
            lines = edit.toPlainText().splitlines()
            out: list[str] = []
            for ln in lines:
                s = ln.strip()
                if not s:
                    out.append("")
                elif s.startswith(("•", "- ", "* ")):
                    out.append(s)
                else:
                    out.append(f"• {s}")
            edit.setPlainText("\n".join(out))

        # Signals ---------------------------------------------------------
        self.expenses_table.selectionModel().selectionChanged.connect(lambda *_: _populate("exp"))  # type: ignore[arg-type]
        self.income_table.selectionModel().selectionChanged.connect(lambda *_: _populate("inc"))  # type: ignore[arg-type]
        exp_bullets_btn.clicked.connect(lambda: _apply_bullets(self.exp_desc))  # type: ignore[arg-type]
        inc_bullets_btn.clicked.connect(lambda: _apply_bullets(self.inc_desc))  # type: ignore[arg-type]

        # CRUD handlers ---------------------------------------------------
        def add_expense() -> None:
            date_q = _validate_date(self.exp_date)
            amt = _validate_amount(self.exp_amount)
            if date_q is None or amt is None:
                QMessageBox.warning(self, "Invalid Data", "Fix highlighted fields before adding expense.")
                return
            insert_expense(
                date_q.toPyDate(),
                amt,
                self.exp_desc.toPlainText(),
                self.exp_cat.currentText() or "Other",
            )
            self.reload_and_refresh()

        def update_expense_record() -> None:
            rid = _selected_row_id(self.expenses_table, self.expenses_df)
            if rid is None:
                QMessageBox.information(self, "Update Expense", "Select a row first")
                return
            date_q = _validate_date(self.exp_date)
            amt = _validate_amount(self.exp_amount)
            if date_q is None or amt is None:
                QMessageBox.warning(self, "Invalid Data", "Fix highlighted fields before updating expense.")
                return
            update_expense(
                rid,
                date_q.toPyDate(),
                amt,
                self.exp_desc.toPlainText(),
                self.exp_cat.currentText() or "Other",
            )
            self.reload_and_refresh()

        def delete_expense_record() -> None:
            rid = _selected_row_id(self.expenses_table, self.expenses_df)
            if rid is None:
                QMessageBox.information(self, "Delete Expense", "Select a row first")
                return
            if QMessageBox.question(self, "Delete", "Delete selected expense?") != QMessageBox.StandardButton.Yes:
                return
            delete_expense(rid)
            self.reload_and_refresh()

        def add_income() -> None:
            date_q = _validate_date(self.inc_date)
            amt = _validate_amount(self.inc_amount)
            if date_q is None or amt is None:
                QMessageBox.warning(self, "Invalid Data", "Fix highlighted fields before adding income.")
                return
            insert_income(
                date_q.toPyDate(),
                amt,
                self.inc_desc.toPlainText(),
                self.inc_cat.currentText() or "Other",
            )
            self.reload_and_refresh()

        def update_income_record() -> None:
            rid = _selected_row_id(self.income_table, self.income_df)
            if rid is None:
                QMessageBox.information(self, "Update Income", "Select a row first")
                return
            date_q = _validate_date(self.inc_date)
            amt = _validate_amount(self.inc_amount)
            if date_q is None or amt is None:
                QMessageBox.warning(self, "Invalid Data", "Fix highlighted fields before updating income.")
                return
            update_income(
                rid,
                date_q.toPyDate(),
                amt,
                self.inc_desc.toPlainText(),
                self.inc_cat.currentText() or "Other",
            )
            self.reload_and_refresh()

        def delete_income_record() -> None:
            rid = _selected_row_id(self.income_table, self.income_df)
            if rid is None:
                QMessageBox.information(self, "Delete Income", "Select a row first")
                return
            if QMessageBox.question(self, "Delete", "Delete selected income?") != QMessageBox.StandardButton.Yes:
                return
            delete_income(rid)
            self.reload_and_refresh()

        exp_add_btn.clicked.connect(add_expense)  # type: ignore[arg-type]
        exp_update_btn.clicked.connect(update_expense_record)  # type: ignore[arg-type]
        exp_delete_btn.clicked.connect(delete_expense_record)  # type: ignore[arg-type]
        inc_add_btn.clicked.connect(add_income)  # type: ignore[arg-type]
        inc_update_btn.clicked.connect(update_income_record)  # type: ignore[arg-type]
        inc_delete_btn.clicked.connect(delete_income_record)  # type: ignore[arg-type]

        return tab

    # -------- Summary Tab --------
    def _build_summary_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        month_selector = QDateEdit()
        month_selector.setCalendarPopup(True)
        month_selector.setDisplayFormat("MMMM yyyy")
        month_selector.setDate(QDate.currentDate())
        layout.addWidget(QLabel("Select Month"))
        layout.addWidget(month_selector)

        tables = QHBoxLayout()
        layout.addLayout(tables)

        exp_box = QVBoxLayout()
        exp_box.addWidget(QLabel("Expenses"))
        self.summary_exp_table = QTableView()
        exp_box.addWidget(self.summary_exp_table)
        tables.addLayout(exp_box)

        inc_box = QVBoxLayout()
        inc_box.addWidget(QLabel("Income"))
        self.summary_inc_table = QTableView()
        inc_box.addWidget(self.summary_inc_table)
        tables.addLayout(inc_box)

        def update_summary() -> None:
            period = pd.Period(month_selector.date().toPyDate(), freq="M")
            exp_dates = pd.to_datetime(self.expenses_df["date"], errors="coerce", dayfirst=True)
            inc_dates = pd.to_datetime(self.income_df["date"], errors="coerce", dayfirst=True)
            exp_mask = exp_dates.dt.to_period("M") == period
            inc_mask = inc_dates.dt.to_period("M") == period
            exp = self.expenses_df[exp_mask]
            inc = self.income_df[inc_mask]
            exp_actuals = exp.groupby("category")["amount"].sum().to_dict()
            inc_actuals = inc.groupby("category")["amount"].sum().to_dict()

            rows_exp: list[list[str]] = []
            for cat in self.EXPENSE_CATEGORIES:
                planned = self.PLANNED_EXPENSES.get(cat, 0.0)
                actual = exp["amount"].sum() if cat == "Totals" else exp_actuals.get(cat, 0.0)
                diff = planned - actual
                rows_exp.append([cat, f"${planned:.2f}", f"${actual:.2f}", f"${diff:+.2f}"])
            self.summary_exp_table.setModel(
                PandasModel(
                    pd.DataFrame(
                        rows_exp,
                        columns=["Category", "Planned", "Actual", "Diff."],
                    )
                )
            )

            rows_inc: list[list[str]] = []
            for cat in self.INCOME_CATEGORIES:
                planned = self.PLANNED_INCOME.get(cat, 0.0)
                actual = inc["amount"].sum() if cat == "Totals" else inc_actuals.get(cat, 0.0)
                diff = planned - actual
                rows_inc.append([cat, f"${planned:.2f}", f"${actual:.2f}", f"${diff:+.2f}"])
            self.summary_inc_table.setModel(
                PandasModel(
                    pd.DataFrame(
                        rows_inc,
                        columns=["Category", "Planned", "Actual", "Diff."],
                    )
                )
            )

        month_selector.dateChanged.connect(update_summary)  # type: ignore[arg-type]
        update_summary()
        self._update_summary_fn = update_summary
        return tab

    def refresh_summary(self) -> None:
        if hasattr(self, "_update_summary_fn"):
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
