"""
Decision Service - Orchestrates governance decision workflow.

Receives decision requests, evaluates them using the policy engine,
generates capability tokens, and records decisions in the ledger.

This module integrates with the canonical governance models defined in
model_governance_pack.models for audit-defensible decision records.
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from lexecon.policy.engine import PolicyEngine

# Import canonical governance models
try:
    from model_governance_pack.models import (
        Decision as CanonicalDecision,
        DecisionOutcome,
        Risk,
        RiskLevel,
    )
    GOVERNANCE_MODELS_AVAILABLE = True
except ImportError:
    GOVERNANCE_MODELS_AVAILABLE = False
    CanonicalDecision = None
    DecisionOutcome = None
    Risk = None
    RiskLevel = None


def generate_ulid() -> str:
    """
    Generate a ULID-like identifier for decision IDs.

    Format: 26 uppercase alphanumeric characters.
    Uses timestamp + random component for sortability and uniqueness.
    """
    import time
    import secrets
    import string

    # ULID encoding alphabet (Crockford's Base32)
    alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

    # Timestamp component (48 bits = 10 chars)
    timestamp_ms = int(time.time() * 1000)
    timestamp_chars = []
    for _ in range(10):
        timestamp_chars.append(alphabet[timestamp_ms & 31])
        timestamp_ms >>= 5
    timestamp_part = "".join(reversed(timestamp_chars))

    # Random component (80 bits = 16 chars) - using secrets for cryptographic safety
    random_part = "".join(secrets.choice(alphabet) for _ in range(16))

    return timestamp_part + random_part


def generate_decision_id() -> str:
    """Generate a canonical decision ID in the format dec_<ULID>."""
    return f"dec_{generate_ulid()}"


def generate_risk_id(decision_id: str) -> str:
    """Generate a risk assessment ID linked to a decision."""
    return f"rsk_{decision_id}"


class DecisionRequest:
    """
    Represents a governance decision request.

    This is the legacy request format maintained for backwards compatibility.
    Internally converts to canonical governance models when available.
    """

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
        context: Dict[str, Any] = None,
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
        self.timestamp = datetime.now(timezone.utc).isoformat()

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
            "timestamp": self.timestamp,
        }

    def to_canonical_actor_id(self) -> str:
        """Convert actor to canonical actor_id format."""
        # If already in canonical format, return as-is
        if self.actor.startswith("act_"):
            return self.actor
        # Otherwise, infer type and format
        if self.actor in ["model", "ai", "assistant"]:
            return f"act_ai_agent:{self.actor}"
        elif self.actor in ["user", "human"]:
            return f"act_human_user:{self.actor}"
        else:
            return f"act_system_service:{self.actor}"

    def to_canonical_action_id(self) -> str:
        """Convert proposed_action to canonical action_id format."""
        # If already in canonical format, return as-is
        if self.proposed_action.startswith("axn_"):
            return self.proposed_action
        # Otherwise, infer category from action name
        action_lower = self.proposed_action.lower()
        if any(kw in action_lower for kw in ["read", "get", "fetch", "view"]):
            return f"axn_read:{self.proposed_action}"
        elif any(kw in action_lower for kw in ["write", "create", "update", "set"]):
            return f"axn_write:{self.proposed_action}"
        elif any(kw in action_lower for kw in ["execute", "run", "call"]):
            return f"axn_execute:{self.proposed_action}"
        elif any(kw in action_lower for kw in ["delete", "remove"]):
            return f"axn_delete:{self.proposed_action}"
        elif any(kw in action_lower for kw in ["send", "transmit", "post"]):
            return f"axn_transmit:{self.proposed_action}"
        else:
            return f"axn_execute:{self.proposed_action}"


class DecisionResponse:
    """
    Represents a governance decision response.

    This is the legacy response format maintained for backwards compatibility.
    Contains reference to canonical Decision when available.
    """

    def __init__(
        self,
        request_id: str,
        decision: str,
        reasoning: str,
        policy_version_hash: str,
        capability_token: Optional[Dict[str, Any]] = None,
        ledger_entry_hash: Optional[str] = None,
        signature: Optional[str] = None,
        timestamp: Optional[str] = None,
        decision_id: Optional[str] = None,
        canonical_decision: Optional["CanonicalDecision"] = None,
    ):
        self.request_id = request_id
        self.decision = decision
        self.reasoning = reasoning
        self.policy_version_hash = policy_version_hash
        self.capability_token = capability_token
        self.ledger_entry_hash = ledger_entry_hash
        self.signature = signature
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.decision_id = decision_id or generate_decision_id()
        self._canonical_decision = canonical_decision

    @property
    def canonical(self) -> Optional["CanonicalDecision"]:
        """Get the canonical Decision model if available."""
        return self._canonical_decision

    @property
    def decision_hash(self) -> str:
        """Generate a hash of the decision for verification purposes."""
        decision_data = {
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "decision": self.decision,
            "policy_version_hash": self.policy_version_hash,
            "timestamp": self.timestamp,
        }
        canonical_json = json.dumps(decision_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize response to dictionary."""
        # Map internal fields to API-expected field names
        allowed = self.decision in ["allow", "permit", "approved"]
        return {
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "allowed": allowed,
            "decision": self.decision,
            "reason": self.reasoning,
            "reasoning": self.reasoning,  # Keep for backwards compatibility
            "policy_version_hash": self.policy_version_hash,
            "capability_token": self.capability_token,
            "ledger_entry_hash": self.ledger_entry_hash,
            "signature": self.signature or "",
            "timestamp": self.timestamp,
        }

    def to_canonical_dict(self) -> Optional[Dict[str, Any]]:
        """Get canonical Decision as dictionary if available."""
        if self._canonical_decision:
            return self._canonical_decision.model_dump()
        return None


class DecisionService:
    """
    Decision service orchestrates the governance workflow.

    Evaluates requests, generates capability tokens, and maintains audit trail.
    Integrates with canonical governance models for audit-defensible records.
    """

    def __init__(
        self,
        policy_engine: PolicyEngine,
        ledger=None,
        identity=None,
        store_canonical: bool = True,
    ):
        """
        Initialize the decision service.

        Args:
            policy_engine: Policy engine for evaluation
            ledger: Optional ledger for audit trail
            identity: Optional identity for signing
            store_canonical: Whether to store canonical Decision records
        """
        self.policy_engine = policy_engine
        self.ledger = ledger
        self.identity = identity
        self.store_canonical = store_canonical and GOVERNANCE_MODELS_AVAILABLE
        self._canonical_decisions: Dict[str, "CanonicalDecision"] = {}

    def evaluate_request(self, request: DecisionRequest) -> DecisionResponse:
        """
        Evaluate a decision request.

        Returns a decision response with permit/deny decision,
        reasoning, and capability token if approved.
        """
        # Generate canonical decision ID
        decision_id = generate_decision_id()

        # Evaluate against policy
        evaluation = self.policy_engine.evaluate(
            actor=request.actor,
            action=request.proposed_action,
            data_classes=request.data_classes,
            risk_level=request.risk_level,
            context=request.context,
        )

        # Map evaluation result to decision outcome
        if evaluation.allowed:
            decision = "permit"
            outcome = DecisionOutcome.APPROVED if GOVERNANCE_MODELS_AVAILABLE else None
        else:
            decision = "deny"
            outcome = DecisionOutcome.DENIED if GOVERNANCE_MODELS_AVAILABLE else None

        reasoning = evaluation.reason

        # Generate capability token if permitted
        capability_token = None
        if evaluation.allowed:
            capability_token = self._generate_capability_token(
                request=request, policy_version_hash=evaluation.policy_version_hash
            )

        # Create canonical Decision if models available
        canonical_decision = None
        if self.store_canonical and GOVERNANCE_MODELS_AVAILABLE:
            canonical_decision = self._create_canonical_decision(
                decision_id=decision_id,
                request=request,
                outcome=outcome,
                reasoning=reasoning,
                policy_version_hash=evaluation.policy_version_hash,
            )
            self._canonical_decisions[decision_id] = canonical_decision

        response = DecisionResponse(
            request_id=request.request_id,
            decision=decision,
            reasoning=reasoning,
            policy_version_hash=evaluation.policy_version_hash,
            capability_token=capability_token,
            decision_id=decision_id,
            canonical_decision=canonical_decision,
        )

        # Create ledger entry if ledger is available
        if self.ledger:
            ledger_data = {
                "decision_id": decision_id,
                "request_id": request.request_id,
                "decision": decision,
                "actor": request.actor,
                "action": request.proposed_action,
            }
            # Include canonical data if available
            if canonical_decision:
                ledger_data["canonical"] = canonical_decision.model_dump(mode="json")

            ledger_entry = self.ledger.append("decision", ledger_data)
            response.ledger_entry_hash = ledger_entry.entry_hash

        # Sign decision if identity is available
        if self.identity:
            self._sign_response(response)

        return response

    def _create_canonical_decision(
        self,
        decision_id: str,
        request: DecisionRequest,
        outcome: "DecisionOutcome",
        reasoning: str,
        policy_version_hash: str,
    ) -> "CanonicalDecision":
        """Create a canonical Decision model from request and evaluation."""
        # Build context snapshot
        context_snapshot = {
            "user_intent": request.user_intent,
            "tool": request.tool,
            "data_classes": request.data_classes,
            "risk_level": request.risk_level,
            "policy_mode": request.policy_mode,
            "original_context": request.context,
        }

        return CanonicalDecision(
            decision_id=decision_id,
            request_id=request.request_id,
            actor_id=request.to_canonical_actor_id(),
            action_id=request.to_canonical_action_id(),
            outcome=outcome,
            timestamp=datetime.now(timezone.utc),
            policy_ids=[f"pol_active_{policy_version_hash[:8]}"],
            reasoning=reasoning,
            context_snapshot=context_snapshot,
            metadata={
                "legacy_actor": request.actor,
                "legacy_action": request.proposed_action,
                "requested_output_type": request.requested_output_type,
            },
        )

    def _sign_response(self, response: DecisionResponse) -> None:
        """Sign the decision response."""
        import base64

        decision_hash = response.decision_hash
        message = decision_hash.encode()
        signature_bytes = self.identity.key_manager.private_key.sign(message)
        response.signature = base64.b64encode(signature_bytes).decode()

    def evaluate(
        self,
        actor: str,
        action: str = None,
        proposed_action: str = None,
        tool: str = None,
        user_intent: str = None,
        data_classes: List[str] = None,
        risk_level: int = 1,
    ):
        """
        Evaluate a decision (convenience method).

        Can be used in two ways:
        1. Simple policy evaluation: evaluate(actor="...", action="...", data_classes=[...], risk_level=1)
        2. Full decision request: evaluate(actor="...", proposed_action="...", tool="...", user_intent="...", risk_level=1)
        """
        if data_classes is None:
            data_classes = []

        # If full parameters are provided, create a DecisionRequest and evaluate it
        if proposed_action is not None or tool is not None:
            request = DecisionRequest(
                actor=actor,
                proposed_action=proposed_action or action or "",
                tool=tool or "",
                user_intent=user_intent or "",
                data_classes=data_classes,
                risk_level=risk_level,
            )
            return self.evaluate_request(request)
        else:
            # Simple evaluation - return policy decision directly
            return self.policy_engine.evaluate(
                actor=actor, action=action, data_classes=data_classes, risk_level=risk_level
            )

    def _generate_capability_token(
        self, request: DecisionRequest, policy_version_hash: str
    ) -> Dict[str, Any]:
        """Generate an ephemeral capability token for approved action."""
        token_id = f"tok_{uuid.uuid4().hex[:16]}"
        expiry = datetime.now(timezone.utc) + timedelta(minutes=5)

        return {
            "token_id": token_id,
            "scope": {"action": request.proposed_action, "tool": request.tool},
            "expiry": expiry.isoformat(),
            "policy_version_hash": policy_version_hash,
            "granted_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_canonical_decision(self, decision_id: str) -> Optional["CanonicalDecision"]:
        """Retrieve a canonical decision by ID."""
        return self._canonical_decisions.get(decision_id)

    def list_canonical_decisions(
        self,
        limit: int = 100,
        outcome: Optional["DecisionOutcome"] = None,
    ) -> List["CanonicalDecision"]:
        """
        List canonical decisions with optional filtering.

        Args:
            limit: Maximum number of decisions to return
            outcome: Filter by outcome (approved, denied, etc.)

        Returns:
            List of canonical Decision objects
        """
        decisions = list(self._canonical_decisions.values())

        if outcome is not None:
            decisions = [d for d in decisions if d.outcome == outcome]

        # Sort by timestamp descending (most recent first)
        decisions.sort(key=lambda d: d.timestamp, reverse=True)

        return decisions[:limit]

    def export_decisions_for_audit(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Export canonical decisions for audit purposes.

        Args:
            start_time: Filter decisions after this time
            end_time: Filter decisions before this time

        Returns:
            List of decision dictionaries suitable for audit export
        """
        decisions = list(self._canonical_decisions.values())

        if start_time:
            decisions = [d for d in decisions if d.timestamp >= start_time]
        if end_time:
            decisions = [d for d in decisions if d.timestamp <= end_time]

        # Sort by timestamp ascending for audit trail
        decisions.sort(key=lambda d: d.timestamp)

        return [d.model_dump(mode="json") for d in decisions]
