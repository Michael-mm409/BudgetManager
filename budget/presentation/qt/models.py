from __future__ import annotations

import datetime

import pandas as pd
from PyQt6.QtCore import QAbstractTableModel, Qt
from PyQt6.QtGui import QBrush, QColor


class PandasModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame | None = None):
        super().__init__()
        # Avoid ambiguous truth-value check on DataFrame
        self._df = df if df is not None else pd.DataFrame()

    @property
    def df(self) -> pd.DataFrame:
        return self._df

    @df.setter
    def df(self, new_df: pd.DataFrame):
        self.beginResetModel()
        self._df = new_df
        self.endResetModel()

    def rowCount(self, parent=None):  # type: ignore[override]
        return len(self._df)

    def columnCount(self, parent=None):  # type: ignore[override]
        return self._df.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):  # type: ignore[override]
        if not index.isValid():
            return None
        value = self._df.iloc[index.row(), index.column()]
        col_name = self._df.columns[index.column()]

        # Foreground color for diff column
        if role == Qt.ItemDataRole.ForegroundRole and col_name.lower().startswith("diff"):
            try:
                raw = str(value).replace("$", "").replace(",", "").strip()
                num = float(raw)
                if num > 0:
                    return QBrush(QColor("green"))
                if num < 0:
                    return QBrush(QColor("red"))
            except Exception:  # pragma: no cover
                return None
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            if col_name == "date" and pd.notnull(value):
                if isinstance(value, (datetime.date, datetime.datetime)):
                    return value.strftime("%d-%m-%Y")
                try:
                    return pd.to_datetime(str(value)).strftime("%d-%m-%Y")
                except Exception:  # pragma: no cover - fallback
                    return str(value)
            if col_name == "amount":
                try:
                    num = float(str(value))
                    return f"${num:.2f}"
                except Exception:
                    return str(value)
            return str(value)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # type: ignore[override]
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._df.columns[section]
            return section
        return None
