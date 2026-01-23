"""Policy Relations - Edges in the policy graph.

Relations define permissions, prohibitions, requirements, and other connections between terms.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class RelationType(Enum):
    """Types of policy relations."""

    PERMITS = "permits"
    FORBIDS = "forbids"
    REQUIRES = "requires"
    IMPLIES = "implies"
    CONFLICTS = "conflicts"


@dataclass
class PolicyRelation:
    """A policy relation represents an edge in the policy graph.

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
    def permits(cls, source: str, target: str, conditions: Optional[List[str]] = None) -> "PolicyRelation":
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
    def forbids(cls, source: str, target: str, conditions: Optional[List[str]] = None) -> "PolicyRelation":
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
    def requires(cls, source: str, target: str, conditions: Optional[List[str]] = None) -> "PolicyRelation":
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
        """Deserialize relation from dictionary.

        Supports multiple formats:
        - Full: {"relation_id": "...", "relation_type": "permits", "source": "...", "target": "..."}
        - Simplified: {"type": "permits", "subject": "...", "action": "..."}
        - Three-field: {"type": "permits", "subject": "...", "action": "...", "object": "..."}
        """
        # Handle relation_type field (can be "type" or "relation_type")
        relation_type_value = data.get("relation_type") or data.get("type")
        if not relation_type_value:
            raise ValueError("Missing relation_type or type field")
        relation_type = RelationType(relation_type_value)

        # Handle source field (can be "source" or "subject")
        source = data.get("source") or data.get("subject")

        # Handle target field - more complex logic for three-field format
        # In three-field format: subject -> action -> object
        # We store: source=subject, target=action, and object goes in metadata
        target = data.get("target") or data.get("action")

        # For relations without explicit source/target/action, allow just subject or just action
        if not source and not target:
            raise ValueError("Missing source/target, subject/action, or subject fields")

        # If only one is provided, use it for both (for "requires" relations that may only have action)
        if not source and target:
            source = target
        elif source and not target:
            target = source

        # Store object field in metadata if present
        metadata = data.get("metadata", {})
        if "object" in data:
            metadata["object"] = data["object"]

        # Store other fields in metadata
        for field in ["justification", "condition"]:
            if field in data:
                metadata[field] = data[field]

        # Generate relation_id if not provided
        relation_id = data.get("relation_id")
        if not relation_id:
            relation_id = f"{relation_type_value}:{source}:{target}"

        return cls(
            relation_id=relation_id,
            relation_type=relation_type,
            source=source,
            target=target,
            conditions=data.get("conditions", []),
            metadata=metadata,
        )
