"""Presentation layer root.

Framework/UI specific adapters live under subpackages (e.g. qt).
"""

from .qt.main_window import BudgetMainWindow, run_app  # noqa: F401
