"""
Decision Service - Orchestrates governance decision workflow.

Receives decision requests, evaluates them using the policy engine,
generates capability tokens, and records decisions in the ledger.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from lexecon.policy.engine import PolicyEngine


class DecisionRequest:
    """Represents a governance decision request."""

    def __init__(
        self,
        actor: str,
        proposed_action: str,
        tool: str,
        user_intent: str,
        request_id: Optional[str] = None,
        data_classes: list = None,
        risk_level: int = 1,
        requested_output_type: str = "tool_action",
        policy_mode: str = "strict",
        context: Dict[str, Any] = None
    ):
        self.request_id = request_id or str(uuid.uuid4())
        self.actor = actor
        self.proposed_action = proposed_action
        self.tool = tool
        self.user_intent = user_intent
        self.data_classes = data_classes or []
        self.risk_level = risk_level
        self.requested_output_type = requested_output_type
        self.policy_mode = policy_mode
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize request to dictionary."""
        return {
            "request_id": self.request_id,
            "actor": self.actor,
            "proposed_action": self.proposed_action,
            "tool": self.tool,
            "user_intent": self.user_intent,
            "data_classes": self.data_classes,
            "risk_level": self.risk_level,
            "requested_output_type": self.requested_output_type,
            "policy_mode": self.policy_mode,
            "context": self.context,
            "timestamp": self.timestamp
        }


class DecisionResponse:
    """Represents a governance decision response."""

    def __init__(
        self,
        request_id: str,
        decision: str,
        reasoning: str,
        policy_version_hash: str,
        capability_token: Optional[Dict[str, Any]] = None,
        ledger_entry_hash: Optional[str] = None,
        timestamp: Optional[str] = None
    ):
        self.request_id = request_id
        self.decision = decision
        self.reasoning = reasoning
        self.policy_version_hash = policy_version_hash
        self.capability_token = capability_token
        self.ledger_entry_hash = ledger_entry_hash
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize response to dictionary."""
        return {
            "request_id": self.request_id,
            "decision": self.decision,
            "reasoning": self.reasoning,
            "policy_version_hash": self.policy_version_hash,
            "capability_token": self.capability_token,
            "ledger_entry_hash": self.ledger_entry_hash,
            "timestamp": self.timestamp
        }


class DecisionService:
    """
    Decision service orchestrates the governance workflow.

    Evaluates requests, generates capability tokens, and maintains audit trail.
    """

    def __init__(self, policy_engine: PolicyEngine):
        self.policy_engine = policy_engine

    def evaluate_request(self, request: DecisionRequest) -> DecisionResponse:
        """
        Evaluate a decision request.

        Returns a decision response with permit/deny decision,
        reasoning, and capability token if approved.
        """
        # Evaluate against policy
        evaluation = self.policy_engine.evaluate(
            actor=request.actor,
            action=request.proposed_action,
            data_classes=request.data_classes,
            context=request.context
        )

        decision = "permit" if evaluation["permitted"] else "deny"
        reasoning = evaluation["reasoning"]

        # Generate capability token if permitted
        capability_token = None
        if evaluation["permitted"]:
            capability_token = self._generate_capability_token(
                request=request,
                policy_version_hash=evaluation["policy_version_hash"]
            )

        response = DecisionResponse(
            request_id=request.request_id,
            decision=decision,
            reasoning=reasoning,
            policy_version_hash=evaluation["policy_version_hash"],
            capability_token=capability_token
        )

        return response

    def _generate_capability_token(
        self,
        request: DecisionRequest,
        policy_version_hash: str
    ) -> Dict[str, Any]:
        """Generate an ephemeral capability token for approved action."""
        token_id = f"tok_{uuid.uuid4().hex[:16]}"
        expiry = datetime.utcnow() + timedelta(minutes=5)

        return {
            "token_id": token_id,
            "scope": {
                "action": request.proposed_action,
                "tool": request.tool
            },
            "expiry": expiry.isoformat(),
            "policy_version_hash": policy_version_hash,
            "granted_at": datetime.utcnow().isoformat()
        }
