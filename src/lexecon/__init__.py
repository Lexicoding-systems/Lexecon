"""
Lexecon - Lexical Governance Protocol

A unified cryptographic governance system for AI safety, compliance, and auditability.
"""

__version__ = "0.1.0"
__author__ = "Lexicoding Systems"

from lexecon.capability.tokens import CapabilityToken
from lexecon.decision.service import DecisionService
from lexecon.identity.signing import KeyManager
from lexecon.ledger.chain import LedgerChain
from lexecon.policy.engine import PolicyEngine
from lexecon.policy.relations import PolicyRelation
from lexecon.policy.terms import PolicyTerm

__all__ = [
    "PolicyTerm",
    "PolicyRelation",
    "PolicyEngine",
    "DecisionService",
    "CapabilityToken",
    "LedgerChain",
    "KeyManager",
]
