from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class PlanEditorDialog(QDialog):
    """Dialog for editing, adding, and removing planned budget categories.

    Provides two panels (Expenses / Income) each containing rows of (label, amount spinbox, remove button).
    Supports adding new categories with initial planned amount and preventing removal of categories that
    are currently referenced by existing transactions.
    """

    def __init__(
        self,
        parent: QWidget | None,
        *,
        expense_categories: list[str],
        income_categories: list[str],
        expense_plans: dict[str, float],
        income_plans: dict[str, float],
        used_expense_categories: set[str] | None = None,
        used_income_categories: set[str] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Planned Amounts")
        self._expense_boxes: dict[str, QDoubleSpinBox] = {}
        self._income_boxes: dict[str, QDoubleSpinBox] = {}
        self._used_exp = used_expense_categories or set()
        self._used_inc = used_income_categories or set()

        layout = QVBoxLayout(self)
        sections = QHBoxLayout()
        layout.addLayout(sections)

        self._exp_container = QVBoxLayout()
        exp_wrap = self._wrap_scroll(self._exp_container, "Expenses")
        sections.addWidget(exp_wrap)
        for cat in expense_categories:
            self._add_expense_row(cat, float(expense_plans.get(cat, 0.0)))
        add_exp_btn = QPushButton("Add Expense Category")
        add_exp_btn.clicked.connect(self._prompt_add_expense)  # type: ignore[arg-type]
        self._exp_container.addWidget(add_exp_btn)

        self._inc_container = QVBoxLayout()
        inc_wrap = self._wrap_scroll(self._inc_container, "Income")
        sections.addWidget(inc_wrap)
        for cat in income_categories:
            self._add_income_row(cat, float(income_plans.get(cat, 0.0)))
        add_inc_btn = QPushButton("Add Income Category")
        add_inc_btn.clicked.connect(self._prompt_add_income)  # type: ignore[arg-type]
        self._inc_container.addWidget(add_inc_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)  # type: ignore[arg-type]
        buttons.rejected.connect(self.reject)  # type: ignore[arg-type]
        layout.addWidget(buttons)

    # --- UI construction helpers -------------------------------------------------
    def _wrap_scroll(self, inner_layout: QVBoxLayout, title: str) -> QWidget:
        holder = QWidget()
        outer = QVBoxLayout(holder)
        outer.addWidget(QLabel(title))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner_widget = QWidget()
        inner_widget.setLayout(inner_layout)
        scroll.setWidget(inner_widget)
        outer.addWidget(scroll)
        return holder

    def _make_row(self, category: str, value: float, remove_cb) -> tuple[QWidget, QDoubleSpinBox]:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        label = QLabel(category)
        spin = QDoubleSpinBox()
        spin.setRange(0.0, 1_000_000_000.0)
        spin.setDecimals(2)
        spin.setValue(value)
        remove_btn = QPushButton("✕")
        remove_btn.setFixedWidth(28)
        remove_btn.clicked.connect(lambda *_: remove_cb(category, row))  # type: ignore[arg-type]
        h.addWidget(label)
        h.addStretch(1)
        h.addWidget(spin)
        h.addWidget(remove_btn)
        return row, spin

    # --- Row management ----------------------------------------------------------
    def _add_expense_row(self, category: str, value: float) -> None:
        if category in self._expense_boxes:
            return
        row, spin = self._make_row(category, value, self._remove_expense_category)
        self._expense_boxes[category] = spin
        self._exp_container.insertWidget(self._exp_container.count() - 1, row)

    def _add_income_row(self, category: str, value: float) -> None:
        if category in self._income_boxes:
            return
        row, spin = self._make_row(category, value, self._remove_income_category)
        self._income_boxes[category] = spin
        self._inc_container.insertWidget(self._inc_container.count() - 1, row)

    def _remove_expense_category(self, category: str, row_widget: QWidget) -> None:
        if category in self._used_exp:
            QMessageBox.warning(self, "In Use", f"Cannot remove '{category}' – it has existing expenses.")
            return
        self._expense_boxes.pop(category, None)
        row_widget.setParent(None)

    def _remove_income_category(self, category: str, row_widget: QWidget) -> None:
        if category in self._used_inc:
            QMessageBox.warning(self, "In Use", f"Cannot remove '{category}' – it has existing income records.")
            return
        self._income_boxes.pop(category, None)
        row_widget.setParent(None)

    # --- Add dialogs -------------------------------------------------------------
    def _prompt_add_expense(self) -> None:
        self._prompt_add_generic(True)

    def _prompt_add_income(self) -> None:
        self._prompt_add_generic(False)

    def _prompt_add_generic(self, is_expense: bool) -> None:
        name, ok = QInputDialog.getText(self, "New Category", "Category name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name.lower() == "totals":
            QMessageBox.warning(self, "Invalid", "'Totals' is reserved.")
            return
        target = self._expense_boxes if is_expense else self._income_boxes
        if name in target:
            QMessageBox.warning(self, "Exists", "Category already exists.")
            return
        amt, ok2 = QInputDialog.getDouble(
            self, "Planned Amount", f"Planned amount for '{name}':", 0.0, 0.0, 1_000_000_000.0, 2
        )
        if not ok2:
            return
        if is_expense:
            self._add_expense_row(name, amt)
        else:
            self._add_income_row(name, amt)

    # --- Public API --------------------------------------------------------------
    def get_plans(self) -> tuple[dict[str, float], dict[str, float]]:
        exp = {k: float(box.value()) for k, box in self._expense_boxes.items()}
        inc = {k: float(box.value()) for k, box in self._income_boxes.items()}
        return exp, inc
