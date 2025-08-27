from __future__ import annotations

from budget.infrastructure.db.connection import init_db
from budget.presentation.qt.main_window import run_app

"""Application launcher.

Usage:
    python main.py
    python -m budget    (if a __main__.py is added)
"""


def main() -> int:
    init_db()
    return run_app()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
