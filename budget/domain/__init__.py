"""Domain layer.

Contains business (UI-agnostic) models and pure logic.
Only expose stable dataclasses / enums here.
"""

from .models import Transaction

__all__ = ["Transaction"]
