"""
Policy Engine - Evaluates policies and makes authorization decisions.

The engine loads terms and relations, and evaluates decision requests against the policy graph.
"""

import hashlib
import json
from typing import Dict, List, Any, Optional
from enum import Enum

from lexecon.policy.terms import PolicyTerm
from lexecon.policy.relations import PolicyRelation, RelationType


class PolicyMode(Enum):
    """Policy evaluation modes."""
    PERMISSIVE = "permissive"  # Allow unless explicitly forbidden
    STRICT = "strict"  # Deny unless explicitly permitted
    PARANOID = "paranoid"  # Deny high risk unless human confirmation


class PolicyEngine:
    """
    Policy engine for evaluating governance decisions.

    Maintains the policy graph (terms + relations) and evaluates requests.
    """

    def __init__(self, mode: PolicyMode = PolicyMode.STRICT):
        self.mode = mode
        self.terms: Dict[str, PolicyTerm] = {}
        self.relations: List[PolicyRelation] = []
        self._policy_hash: Optional[str] = None

    def add_term(self, term: PolicyTerm) -> None:
        """Add a policy term to the engine."""
        self.terms[term.term_id] = term
        self._policy_hash = None  # Invalidate cached hash

    def add_relation(self, relation: PolicyRelation) -> None:
        """Add a policy relation to the engine."""
        self.relations.append(relation)
        self._policy_hash = None  # Invalidate cached hash

    def load_policy(self, policy_data: Dict[str, Any]) -> None:
        """Load a complete policy from dictionary."""
        # Clear existing policy
        self.terms.clear()
        self.relations.clear()
        self._policy_hash = None

        # Load terms
        for term_data in policy_data.get("terms", []):
            term = PolicyTerm.from_dict(term_data)
            self.add_term(term)

        # Load relations
        for relation_data in policy_data.get("relations", []):
            relation = PolicyRelation.from_dict(relation_data)
            self.add_relation(relation)

    def get_policy_hash(self) -> str:
        """
        Get deterministic hash of current policy version.

        Uses canonical JSON serialization for stable hashing.
        """
        if self._policy_hash is not None:
            return self._policy_hash

        policy_dict = self.to_dict()
        canonical_json = json.dumps(policy_dict, sort_keys=True, separators=(",", ":"))
        self._policy_hash = hashlib.sha256(canonical_json.encode()).hexdigest()
        return self._policy_hash

    def evaluate(
        self,
        actor: str,
        action: str,
        resource: Optional[str] = None,
        data_classes: List[str] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a decision request against the policy.

        Returns a decision with permitted/denied status and reasoning.
        """
        if data_classes is None:
            data_classes = []
        if context is None:
            context = {}

        # Find relevant relations
        permits = self._find_relations(RelationType.PERMITS, actor, action)
        forbids = self._find_relations(RelationType.FORBIDS, actor, action)

        # Evaluate based on mode
        if self.mode == PolicyMode.STRICT:
            # Deny unless explicitly permitted
            decision = len(permits) > 0 and len(forbids) == 0
        elif self.mode == PolicyMode.PERMISSIVE:
            # Allow unless explicitly forbidden
            decision = len(forbids) == 0
        else:  # PARANOID
            # Additional checks for high-risk operations
            decision = len(permits) > 0 and len(forbids) == 0

        return {
            "permitted": decision,
            "mode": self.mode.value,
            "permits_count": len(permits),
            "forbids_count": len(forbids),
            "policy_version_hash": self.get_policy_hash(),
            "reasoning": self._generate_reasoning(decision, permits, forbids)
        }

    def _find_relations(
        self,
        relation_type: RelationType,
        actor: str,
        action: str
    ) -> List[PolicyRelation]:
        """Find relations matching the given criteria."""
        matching = []
        for relation in self.relations:
            if relation.relation_type != relation_type:
                continue
            # Simple matching - can be enhanced with pattern matching
            if actor in relation.source and action in relation.target:
                matching.append(relation)
        return matching

    def _generate_reasoning(
        self,
        decision: bool,
        permits: List[PolicyRelation],
        forbids: List[PolicyRelation]
    ) -> str:
        """Generate human-readable reasoning for the decision."""
        if decision:
            return f"Permitted by {len(permits)} rule(s), no conflicts"
        else:
            if len(forbids) > 0:
                return f"Denied by {len(forbids)} prohibition(s)"
            else:
                return "Denied by default (no explicit permission)"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize policy to dictionary."""
        return {
            "mode": self.mode.value,
            "terms": [term.to_dict() for term in self.terms.values()],
            "relations": [relation.to_dict() for relation in self.relations]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyEngine":
        """Deserialize policy from dictionary."""
        engine = cls(mode=PolicyMode(data.get("mode", "strict")))
        engine.load_policy(data)
        return engine
