from __future__ import annotations

from PyQt6.QtCore import QDate
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QDateEdit, QLineEdit, QWidget

from .constants import DECIMALS, ERROR_STYLE, MAX_AMOUNT


def clear_error(widget: QWidget) -> None:
    widget.setStyleSheet("")


def mark_error(widget: QWidget) -> None:
    widget.setStyleSheet(ERROR_STYLE)


def validate_amount(edit: QLineEdit) -> float | None:
    text = edit.text().strip()
    if not text:
        mark_error(edit)
        return None
    try:
        val = float(text)
    except ValueError:
        mark_error(edit)
        return None
    if val < 0:
        mark_error(edit)
        return None
    clear_error(edit)
    return val


def validate_date(d_edit: QDateEdit) -> QDate | None:
    d = d_edit.date()
    if not d.isValid() or d > QDate.currentDate():
        mark_error(d_edit)
        return None
    clear_error(d_edit)
    return d


def make_amount_validator(parent: QWidget) -> QDoubleValidator:
    return QDoubleValidator(0.0, MAX_AMOUNT, DECIMALS, parent)


__all__ = [
    "clear_error",
    "mark_error",
    "validate_amount",
    "validate_date",
    "make_amount_validator",
]
