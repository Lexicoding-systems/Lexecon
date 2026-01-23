"""Ledger module for Lexecon."""

from lexecon.ledger.chain import LedgerChain, LedgerEntry

# Alias for backwards compatibility and convenience
Ledger = LedgerChain

__all__ = ["Ledger", "LedgerChain", "LedgerEntry"]
