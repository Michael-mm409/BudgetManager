from budget.infrastructure.db.connection import init_db
from budget.presentation.qt.main_window import run_app

from . import __all__  # noqa: F401


def main():  # pragma: no cover - thin wrapper
    init_db()
    return run_app()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
