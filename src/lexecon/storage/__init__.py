"""
Storage Layer - Persistent storage for audit ledger

Provides SQLite-based persistence for EU AI Act compliance requirements.
"""

from .persistence import LedgerStorage

__all__ = ["LedgerStorage"]
