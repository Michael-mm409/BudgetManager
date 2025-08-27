"""Configuration loading utilities.

Currently supports category / planned amount CSV ingestion.
"""

from .categories_loader import CategoryPlan, CategoryRepository

__all__ = ["CategoryRepository", "CategoryPlan"]
