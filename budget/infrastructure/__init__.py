"""Infrastructure layer.

Adapts external resources (database, config files, APIs) to the application's
internal interfaces. Keep side-effectful code here.
"""

from .config_loader.categories_loader import CategoryPlan, CategoryRepository
from .db.connection import (
    delete_expense,
    delete_income,
    get_connection,
    init_db,
    insert_expense,
    insert_income,
    update_expense,
    update_income,
)

__all__ = [
    "get_connection",
    "init_db",
    "insert_expense",
    "insert_income",
    "update_expense",
    "delete_expense",
    "update_income",
    "delete_income",
    "CategoryRepository",
    "CategoryPlan",
]
