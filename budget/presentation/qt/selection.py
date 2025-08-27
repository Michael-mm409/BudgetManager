from __future__ import annotations

import pandas as pd
from PyQt6.QtWidgets import QTableView


def selected_row_id(table: QTableView, df: pd.DataFrame) -> int | None:
    sel = table.selectionModel()
    if sel is None:
        return None
    rows = sel.selectedRows()
    if not rows:
        return None
    r = rows[0].row()
    try:
        return int(df.iloc[r]["id"])  # type: ignore[index]
    except Exception:  # pragma: no cover
        return None


__all__ = ["selected_row_id"]
