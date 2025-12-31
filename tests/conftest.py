"""Pytest configuration and fixtures."""

import pytest
from lexecon.policy.engine import PolicyEngine, PolicyMode
from lexecon.policy.terms import PolicyTerm
from lexecon.policy.relations import PolicyRelation
from lexecon.ledger.chain import LedgerChain


@pytest.fixture
def policy_engine():
    """Create a basic policy engine."""
    return PolicyEngine(mode=PolicyMode.STRICT)


@pytest.fixture
def populated_policy_engine():
    """Create a policy engine with some terms and relations."""
    engine = PolicyEngine(mode=PolicyMode.STRICT)

    # Add terms
    engine.add_term(PolicyTerm.create_actor("user", "User"))
    engine.add_term(PolicyTerm.create_actor("model", "AI Model"))
    engine.add_term(PolicyTerm.create_action("read", "Read Data"))
    engine.add_term(PolicyTerm.create_action("write", "Write Data"))
    engine.add_term(PolicyTerm.create_data_class("pii", "PII"))

    # Add relations
    engine.add_relation(PolicyRelation.permits("actor:user", "action:read"))
    engine.add_relation(PolicyRelation.forbids("actor:model", "action:write"))

    return engine


@pytest.fixture
def ledger():
    """Create a fresh ledger."""
    return LedgerChain()


@pytest.fixture
def populated_ledger():
    """Create a ledger with some entries."""
    ledger = LedgerChain()
    ledger.append("decision", {"actor": "user", "action": "read", "decision": "permit"})
    ledger.append("decision", {"actor": "model", "action": "write", "decision": "deny"})
    return ledger
