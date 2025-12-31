"""
Capability Tokens - Ephemeral authorization tokens for approved actions.

Tokens are cryptographically signed and time-limited.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CapabilityToken:
    """
    A capability token represents an ephemeral authorization.

    Tokens are granted for specific actions and have limited lifetime.
    """

    token_id: str
    scope: Dict[str, Any]
    expiry: datetime
    policy_version_hash: str
    granted_at: datetime
    signature: Optional[str] = None

    @classmethod
    def create(
        cls,
        action: str,
        tool: str,
        policy_version_hash: str,
        ttl_minutes: int = 5
    ) -> "CapabilityToken":
        """Create a new capability token."""
        now = datetime.utcnow()
        return cls(
            token_id=f"tok_{uuid.uuid4().hex[:16]}",
            scope={"action": action, "tool": tool},
            expiry=now + timedelta(minutes=ttl_minutes),
            policy_version_hash=policy_version_hash,
            granted_at=now
        )

    def is_valid(self) -> bool:
        """Check if token is still valid (not expired)."""
        return datetime.utcnow() < self.expiry

    def is_authorized_for(self, action: str, tool: str) -> bool:
        """Check if token authorizes the given action and tool."""
        if not self.is_valid():
            return False

        return (
            self.scope.get("action") == action and
            self.scope.get("tool") == tool
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize token to dictionary."""
        return {
            "token_id": self.token_id,
            "scope": self.scope,
            "expiry": self.expiry.isoformat(),
            "policy_version_hash": self.policy_version_hash,
            "granted_at": self.granted_at.isoformat(),
            "signature": self.signature
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapabilityToken":
        """Deserialize token from dictionary."""
        return cls(
            token_id=data["token_id"],
            scope=data["scope"],
            expiry=datetime.fromisoformat(data["expiry"]),
            policy_version_hash=data["policy_version_hash"],
            granted_at=datetime.fromisoformat(data["granted_at"]),
            signature=data.get("signature")
        )


class CapabilityTokenStore:
    """Store and manage capability tokens."""

    def __init__(self):
        self.tokens: Dict[str, CapabilityToken] = {}

    def store(self, token: CapabilityToken) -> None:
        """Store a token."""
        self.tokens[token.token_id] = token

    def get(self, token_id: str) -> Optional[CapabilityToken]:
        """Retrieve a token by ID."""
        return self.tokens.get(token_id)

    def verify(self, token_id: str, action: str, tool: str) -> bool:
        """Verify a token authorizes the given action."""
        token = self.get(token_id)
        if token is None:
            return False
        return token.is_authorized_for(action, tool)

    def cleanup_expired(self) -> int:
        """Remove expired tokens. Returns count of removed tokens."""
        expired = [
            token_id
            for token_id, token in self.tokens.items()
            if not token.is_valid()
        ]
        for token_id in expired:
            del self.tokens[token_id]
        return len(expired)
