"""Application layer.

Coordinates domain + infrastructure to serve use cases for presentation.
"""

from .services import DataService

__all__ = ["DataService"]
