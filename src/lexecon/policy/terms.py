"""Policy Terms - Nodes in the policy graph.

Terms represent entities, actions, data classes, and other policy primitives.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class TermType(Enum):
    """Types of policy terms."""

    ACTION = "action"
    ACTOR = "actor"
    DATA_CLASS = "data_class"
    RESOURCE = "resource"
    CONTEXT = "context"


@dataclass
class PolicyTerm:
    """A policy term represents a node in the policy graph.

    Terms can represent actions, actors, data classes, resources, or contexts.
    """

    term_id: str
    term_type: TermType
    label: str
    description: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def create_action(cls, term_id: str, label: str, description: str = "") -> "PolicyTerm":
        """Create an action term."""
        return cls(
            term_id=f"action:{term_id}",
            term_type=TermType.ACTION,
            label=label,
            description=description,
        )

    @classmethod
    def create_actor(cls, term_id: str, label: str, description: str = "") -> "PolicyTerm":
        """Create an actor term."""
        return cls(
            term_id=f"actor:{term_id}",
            term_type=TermType.ACTOR,
            label=label,
            description=description,
        )

    @classmethod
    def create_data_class(cls, term_id: str, label: str, description: str = "") -> "PolicyTerm":
        """Create a data class term."""
        return cls(
            term_id=f"data:{term_id}",
            term_type=TermType.DATA_CLASS,
            label=label,
            description=description,
        )

    @classmethod
    def create_resource(cls, term_id: str, label: str, description: str = "") -> "PolicyTerm":
        """Create a resource term."""
        return cls(
            term_id=f"resource:{term_id}",
            term_type=TermType.RESOURCE,
            label=label,
            description=description,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize term to dictionary."""
        return {
            "term_id": self.term_id,
            "term_type": self.term_type.value,
            "label": self.label,
            "description": self.description,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyTerm":
        """Deserialize term from dictionary.

        Supports both full format and simplified format:
        - Full: {"term_id": "...", "term_type": "...", "label": "...", "description": "..."}
        - Simplified: {"id": "...", "type": "...", "name": "..."}
        """
        # Handle term_id field (can be "term_id" or "id")
        term_id = data.get("term_id") or data.get("id")
        if not term_id:
            raise ValueError("Missing term_id or id field")

        # Handle term_type field (can be "term_type" or "type")
        term_type_value = data.get("term_type") or data.get("type")
        if not term_type_value:
            raise ValueError("Missing term_type or type field")
        term_type = TermType(term_type_value)

        # Handle label field (can be "label" or "name")
        label = data.get("label") or data.get("name", "")

        # Description is optional
        description = data.get("description", "")

        return cls(
            term_id=term_id,
            term_type=term_type,
            label=label,
            description=description,
            metadata=data.get("metadata", {}),
        )
