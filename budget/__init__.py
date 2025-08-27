"""Budget application package.

Layered layout:
        domain              – pure business models
        infrastructure/     – db + config loading
        application/        – service layer (use cases)
        presentation/qt/    – GUI components

Convenience re-exports keep external import paths stable.
"""

from .domain.models import Transaction  # noqa: F401

__all__ = ["Transaction"]
