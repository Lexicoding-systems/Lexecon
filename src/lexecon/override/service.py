"""Override Service - Human authority mechanism for governance decisions.

Provides explicit override capability with:
- Mandatory justification for all overrides
- Authorization checks (who can override what)
- Immutable override audit trail
- Decision state integrity (original outcome preserved)
- Evidence artifact generation
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

# Import canonical governance models
try:
    from model_governance_pack.models import (
        ArtifactType,
        EvidenceArtifact,
        NewOutcome,
        OriginalOutcome,
        Override,
        OverrideScope,
        OverrideType,
    )

    GOVERNANCE_MODELS_AVAILABLE = True
except ImportError:
    GOVERNANCE_MODELS_AVAILABLE = False
    Override = None
    OverrideType = None
    OriginalOutcome = None
    NewOutcome = None
    OverrideScope = None
    EvidenceArtifact = None
    ArtifactType = None


def generate_override_id(decision_id: str) -> str:
    """Generate an override ID linked to a decision.

    Format: ovr_dec_<decision_suffix>_<short_uuid>
    Allows multiple overrides per decision (audit trail).
    """
    if decision_id.startswith("dec_"):
        suffix = decision_id[4:]  # Remove "dec_" prefix
    else:
        suffix = decision_id

    # Add short UUID for uniqueness
    short_uuid = uuid.uuid4().hex[:8]
    return f"ovr_dec_{suffix}_{short_uuid}"


def generate_evidence_id(artifact_type: str) -> str:
    """Generate an evidence artifact ID."""
    hex_suffix = uuid.uuid4().hex[:8]
    return f"evd_{artifact_type}_{hex_suffix}"


class OverrideConfig:
    """Configuration for override behavior."""

    # Authorization roles that can perform overrides
    AUTHORIZED_ROLES = [
        "act_human_user:executive",
        "act_human_user:governance_lead",
        "act_human_user:security_officer",
    ]

    # Override types that require executive approval
    EXECUTIVE_ONLY_TYPES = [
        OverrideType.EMERGENCY_BYPASS,
        OverrideType.EXECUTIVE_OVERRIDE,
    ]

    # Default time limits for time-limited exceptions (in hours)
    DEFAULT_TIME_LIMIT_HOURS = 24

    # Review period for overrides (in days)
    DEFAULT_REVIEW_PERIOD_DAYS = 30


class OverrideService:
    """Override service for governance decisions.

    Provides human authority mechanism to override system decisions
    with full audit trail and authorization controls.
    """

    def __init__(
        self,
        config: Optional[OverrideConfig] = None,
        store_evidence: bool = True,
    ):
        """Initialize the override service.

        Args:
            config: Optional custom configuration
            store_evidence: Whether to generate evidence artifacts
        """
        if not GOVERNANCE_MODELS_AVAILABLE:
            raise RuntimeError(
                "Governance models not available. Install model_governance_pack.",
            )

        self.config = config or OverrideConfig()
        self.store_evidence = store_evidence

        # In-memory storage (immutable records)
        self._overrides: Dict[str, Override] = {}
        self._decision_overrides: Dict[str, List[str]] = {}  # decision_id -> override_ids
        self._evidence_artifacts: Dict[str, EvidenceArtifact] = {}

    def is_authorized(
        self,
        actor_id: str,
        override_type: "OverrideType",
    ) -> bool:
        """Check if actor is authorized to perform override.

        Args:
            actor_id: Actor ID requesting override
            override_type: Type of override being requested

        Returns:
            True if actor is authorized
        """
        # Check if actor is in authorized roles
        is_in_authorized_roles = any(
            actor_id.startswith(role) or actor_id == role
            for role in self.config.AUTHORIZED_ROLES
        )

        if not is_in_authorized_roles:
            return False

        # Check if override type requires executive approval
        if override_type in self.config.EXECUTIVE_ONLY_TYPES:
            # Must be executive
            return actor_id.startswith("act_human_user:executive")

        return True

    def create_override(
        self,
        decision_id: str,
        override_type: "OverrideType",
        authorized_by: str,
        justification: str,
        original_outcome: Optional["OriginalOutcome"] = None,
        new_outcome: Optional["NewOutcome"] = None,
        expires_at: Optional[datetime] = None,
        scope: Optional["OverrideScope"] = None,
        review_required_by: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Override":
        """Create an override for a decision.

        Requires explicit justification (min 20 chars) and authorization.
        Validates via canonical schema and creates immutable record.

        Args:
            decision_id: Decision ID to override
            override_type: Type of override
            authorized_by: Actor ID authorizing override
            justification: Required justification (min 20 chars)
            original_outcome: What the decision was before override
            new_outcome: Outcome after override
            expires_at: Optional expiration for time-limited overrides
            scope: Optional scope limitations
            review_required_by: Optional review deadline
            metadata: Optional additional metadata

        Returns:
            Override object validated against canonical schema

        Raises:
            ValueError: If authorization fails or validation fails
        """
        # Enforce authorization check
        if not self.is_authorized(authorized_by, override_type):
            raise ValueError(
                f"Actor {authorized_by} not authorized for {override_type.value} override",
            )

        # Validate justification length (schema enforces min 20, but check explicitly)
        if len(justification.strip()) < 20:
            raise ValueError("Justification must be at least 20 characters")

        # Generate override ID
        override_id = generate_override_id(decision_id)

        # Set defaults for time-limited overrides
        if override_type == OverrideType.TIME_LIMITED_EXCEPTION and expires_at is None:
            expires_at = datetime.now(timezone.utc) + timedelta(
                hours=self.config.DEFAULT_TIME_LIMIT_HOURS,
            )

        # Set default review deadline
        if review_required_by is None:
            review_required_by = datetime.now(timezone.utc) + timedelta(
                days=self.config.DEFAULT_REVIEW_PERIOD_DAYS,
            )

        # Create override (validates against schema)
        override = Override(
            override_id=override_id,
            decision_id=decision_id,
            override_type=override_type,
            authorized_by=authorized_by,
            justification=justification,
            timestamp=datetime.now(timezone.utc),
            original_outcome=original_outcome,
            new_outcome=new_outcome,
            expires_at=expires_at,
            scope=scope,
            review_required_by=review_required_by,
            evidence_ids=[],
            metadata=metadata,
        )

        # Store override (immutable)
        self._overrides[override_id] = override

        # Track decision -> overrides mapping
        if decision_id not in self._decision_overrides:
            self._decision_overrides[decision_id] = []
        self._decision_overrides[decision_id].append(override_id)

        # Generate evidence artifact
        if self.store_evidence:
            artifact = self._create_evidence_artifact(override)
            # Link evidence to override
            override.evidence_ids.append(artifact.artifact_id)

        return override

    def get_override(self, override_id: str) -> Optional["Override"]:
        """Retrieve an override by ID.

        Returns immutable override record.
        """
        return self._overrides.get(override_id)

    def get_overrides_for_decision(self, decision_id: str) -> List["Override"]:
        """Get all overrides for a decision.

        Returns list of overrides in chronological order (oldest first).
        Multiple overrides indicate audit trail.

        Args:
            decision_id: Decision ID

        Returns:
            List of Override objects
        """
        override_ids = self._decision_overrides.get(decision_id, [])
        overrides = [self._overrides[oid] for oid in override_ids]

        # Sort by timestamp (oldest first)
        overrides.sort(key=lambda o: o.timestamp)

        return overrides

    def get_active_override(self, decision_id: str) -> Optional["Override"]:
        """Get the most recent active override for a decision.

        Checks expiration for time-limited overrides.

        Args:
            decision_id: Decision ID

        Returns:
            Most recent non-expired Override, or None
        """
        overrides = self.get_overrides_for_decision(decision_id)

        if not overrides:
            return None

        # Get most recent
        latest = overrides[-1]

        # Check expiration
        if latest.expires_at:
            now = datetime.now(timezone.utc)
            if now > latest.expires_at:
                return None  # Expired

        return latest

    def is_decision_overridden(self, decision_id: str) -> bool:
        """Check if a decision has an active override.

        Args:
            decision_id: Decision ID

        Returns:
            True if decision has active override
        """
        return self.get_active_override(decision_id) is not None

    def list_overrides(
        self,
        override_type: Optional["OverrideType"] = None,
        authorized_by: Optional[str] = None,
        expired: Optional[bool] = None,
        limit: int = 100,
    ) -> List["Override"]:
        """List overrides with optional filtering.

        Args:
            override_type: Filter by override type
            authorized_by: Filter by authorizing actor
            expired: Filter by expiration status (True=expired, False=active, None=all)
            limit: Maximum number of results

        Returns:
            List of Override objects
        """
        overrides = list(self._overrides.values())

        # Apply filters
        if override_type is not None:
            overrides = [o for o in overrides if o.override_type == override_type]

        if authorized_by is not None:
            overrides = [o for o in overrides if o.authorized_by == authorized_by]

        if expired is not None:
            now = datetime.now(timezone.utc)
            if expired:
                # Get expired overrides
                overrides = [
                    o for o in overrides if o.expires_at and now > o.expires_at
                ]
            else:
                # Get non-expired overrides
                overrides = [
                    o for o in overrides if not o.expires_at or now <= o.expires_at
                ]

        # Sort by timestamp descending (most recent first)
        overrides.sort(key=lambda o: o.timestamp, reverse=True)

        return overrides[:limit]

    def get_overrides_needing_review(self) -> List["Override"]:
        """Get overrides that need review (past review_required_by date).

        Returns:
            List of Override objects needing review
        """
        now = datetime.now(timezone.utc)
        overrides = []

        for override in self._overrides.values():
            if override.review_required_by and now > override.review_required_by:
                overrides.append(override)

        # Sort by review deadline (most overdue first)
        overrides.sort(key=lambda o: o.review_required_by)

        return overrides

    def get_decision_with_override_status(
        self, decision_id: str, decision_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Enrich decision data with override status.

        Preserves original decision outcome and adds override metadata.
        Never rewrites original decision record.

        Args:
            decision_id: Decision ID
            decision_data: Original decision data

        Returns:
            Decision data with override_status field
        """
        active_override = self.get_active_override(decision_id)

        # Create copy to avoid mutating original
        enriched = dict(decision_data)

        if active_override:
            enriched["override_status"] = {
                "is_overridden": True,
                "override_id": active_override.override_id,
                "override_type": active_override.override_type.value,
                "authorized_by": active_override.authorized_by,
                "justification": active_override.justification,
                "timestamp": active_override.timestamp.isoformat(),
                "original_outcome": (
                    active_override.original_outcome.value
                    if active_override.original_outcome
                    else None
                ),
                "new_outcome": (
                    active_override.new_outcome.value
                    if active_override.new_outcome
                    else None
                ),
                "expires_at": (
                    active_override.expires_at.isoformat()
                    if active_override.expires_at
                    else None
                ),
            }
        else:
            enriched["override_status"] = {
                "is_overridden": False,
            }

        return enriched

    def _create_evidence_artifact(self, override: "Override") -> "EvidenceArtifact":
        """Create evidence artifact for override.

        Args:
            override: Override object to create artifact for

        Returns:
            EvidenceArtifact object
        """
        # Serialize override to JSON
        override_json = override.model_dump_json(indent=2)
        override_bytes = override_json.encode("utf-8")

        # Generate SHA-256 hash
        sha256_hash = hashlib.sha256(override_bytes).hexdigest()

        # Generate artifact ID
        artifact_id = generate_evidence_id("override")

        # Create evidence artifact
        artifact = EvidenceArtifact(
            artifact_id=artifact_id,
            artifact_type=ArtifactType.ATTESTATION,  # Override is an attestation
            sha256_hash=sha256_hash,
            created_at=datetime.now(timezone.utc),
            source="override_service",
            content_type="application/json",
            size_bytes=len(override_bytes),
            related_decision_ids=[override.decision_id],
            is_immutable=True,
            metadata={
                "override_id": override.override_id,
                "override_type": override.override_type.value,
                "authorized_by": override.authorized_by,
                "justification_length": len(override.justification),
            },
        )

        # Store artifact
        self._evidence_artifacts[artifact_id] = artifact

        return artifact

    def get_evidence_artifact(self, artifact_id: str) -> Optional["EvidenceArtifact"]:
        """Retrieve an evidence artifact by ID."""
        return self._evidence_artifacts.get(artifact_id)

    def list_evidence_artifacts(
        self,
        override_id: Optional[str] = None,
        decision_id: Optional[str] = None,
    ) -> List["EvidenceArtifact"]:
        """List evidence artifacts with optional filtering.

        Args:
            override_id: Filter by override ID
            decision_id: Filter by decision ID

        Returns:
            List of EvidenceArtifact objects
        """
        artifacts = list(self._evidence_artifacts.values())

        if override_id:
            artifacts = [
                a
                for a in artifacts
                if a.metadata and a.metadata.get("override_id") == override_id
            ]

        if decision_id:
            artifacts = [
                a
                for a in artifacts
                if a.related_decision_ids and decision_id in a.related_decision_ids
            ]

        return artifacts


class OverrideValidator:
    """Helper class for validating override conditions."""

    @staticmethod
    def validate_justification(justification: str) -> bool:
        """Validate override justification.

        Args:
            justification: Justification text

        Returns:
            True if valid

        Raises:
            ValueError: If justification is invalid
        """
        if not justification or len(justification.strip()) < 20:
            raise ValueError("Justification must be at least 20 characters")

        # Check for generic/placeholder text
        generic_phrases = [
            "override needed",
            "emergency override",
            "approved by executive",
            "business requirement",
        ]

        justification_lower = justification.lower()
        if any(phrase in justification_lower for phrase in generic_phrases) and len(justification.strip()) < 50:
            raise ValueError(
                "Justification appears generic. Please provide specific reasoning.",
            )

        return True

    @staticmethod
    def validate_time_limit(
        override_type: "OverrideType",
        expires_at: Optional[datetime],
    ) -> bool:
        """Validate time limit for time-limited overrides.

        Args:
            override_type: Type of override
            expires_at: Expiration timestamp

        Returns:
            True if valid

        Raises:
            ValueError: If time limit is invalid
        """
        if override_type == OverrideType.TIME_LIMITED_EXCEPTION:
            if not expires_at:
                raise ValueError("Time-limited exception must have expiration")

            now = datetime.now(timezone.utc)
            if expires_at <= now:
                raise ValueError("Expiration must be in the future")

            # Check reasonable time limit (e.g., not more than 90 days)
            max_duration = timedelta(days=90)
            if expires_at - now > max_duration:
                raise ValueError("Time-limited exception cannot exceed 90 days")

        return True

    @staticmethod
    def validate_scope(
        override_type: "OverrideType",
        scope: Optional["OverrideScope"],
    ) -> bool:
        """Validate override scope.

        Args:
            override_type: Type of override
            scope: Scope limitations

        Returns:
            True if valid

        Raises:
            ValueError: If scope is invalid
        """
        # Emergency bypass should be one-time only
        if override_type == OverrideType.EMERGENCY_BYPASS and (not scope or not scope.is_one_time):
            raise ValueError("Emergency bypass must be one-time only")

        return True
