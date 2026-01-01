"""
Policy Relations - Edges in the policy graph.

Relations define permissions, prohibitions, requirements, and other connections between terms.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class RelationType(Enum):
    """Types of policy relations."""

    PERMITS = "permits"
    FORBIDS = "forbids"
    REQUIRES = "requires"
    IMPLIES = "implies"
    CONFLICTS = "conflicts"


@dataclass
class PolicyRelation:
    """
    A policy relation represents an edge in the policy graph.

    Relations connect terms and define the governance rules.
    """

    relation_id: str
    relation_type: RelationType
    source: str  # Source term ID
    target: str  # Target term ID
    conditions: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.conditions is None:
            self.conditions = []
        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def permits(cls, source: str, target: str, conditions: List[str] = None) -> "PolicyRelation":
        """Create a permission relation."""
        relation_id = f"permits:{source}:{target}"
        return cls(
            relation_id=relation_id,
            relation_type=RelationType.PERMITS,
            source=source,
            target=target,
            conditions=conditions or [],
        )

    @classmethod
    def forbids(cls, source: str, target: str, conditions: List[str] = None) -> "PolicyRelation":
        """Create a prohibition relation."""
        relation_id = f"forbids:{source}:{target}"
        return cls(
            relation_id=relation_id,
            relation_type=RelationType.FORBIDS,
            source=source,
            target=target,
            conditions=conditions or [],
        )

    @classmethod
    def requires(cls, source: str, target: str, conditions: List[str] = None) -> "PolicyRelation":
        """Create a requirement relation."""
        relation_id = f"requires:{source}:{target}"
        return cls(
            relation_id=relation_id,
            relation_type=RelationType.REQUIRES,
            source=source,
            target=target,
            conditions=conditions or [],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize relation to dictionary."""
        return {
            "relation_id": self.relation_id,
            "relation_type": self.relation_type.value,
            "source": self.source,
            "target": self.target,
            "conditions": self.conditions,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyRelation":
        """Deserialize relation from dictionary."""
        return cls(
            relation_id=data["relation_id"],
            relation_type=RelationType(data["relation_type"]),
            source=data["source"],
            target=data["target"],
            conditions=data.get("conditions", []),
            metadata=data.get("metadata", {}),
        )
