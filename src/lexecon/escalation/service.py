"""
Escalation Service - Safety valve for high-risk governance decisions.

Provides explicit escalation workflow with:
- Auto-escalation based on risk thresholds
- SLA tracking and notifications
- Explicit human resolution requirement
- Full audit trail via evidence artifacts
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

# Import canonical governance models
try:
    from model_governance_pack.models import (
        Escalation,
        EscalationTrigger,
        EscalationStatus,
        EscalationPriority,
        Resolution,
        ResolutionOutcome,
        EvidenceArtifact,
        ArtifactType,
        Risk,
        RiskLevel,
    )

    GOVERNANCE_MODELS_AVAILABLE = True
except ImportError:
    GOVERNANCE_MODELS_AVAILABLE = False
    Escalation = None
    EscalationTrigger = None
    EscalationStatus = None
    EscalationPriority = None
    Resolution = None
    ResolutionOutcome = None
    EvidenceArtifact = None
    ArtifactType = None
    Risk = None
    RiskLevel = None


def generate_escalation_id(decision_id: str) -> str:
    """
    Generate an escalation ID linked to a decision.

    Format: esc_dec_<decision_suffix>_<short_uuid>
    Allows multiple escalations per decision (e.g., re-escalation).
    """
    if decision_id.startswith("dec_"):
        suffix = decision_id[4:]  # Remove "dec_" prefix
    else:
        suffix = decision_id

    # Add short UUID for uniqueness (allows re-escalation)
    short_uuid = uuid.uuid4().hex[:8]
    return f"esc_dec_{suffix}_{short_uuid}"


def generate_evidence_id(artifact_type: str) -> str:
    """Generate an evidence artifact ID."""
    hex_suffix = uuid.uuid4().hex[:8]
    return f"evd_{artifact_type}_{hex_suffix}"


class EscalationConfig:
    """Configuration for escalation behavior."""

    # Auto-escalation risk thresholds
    AUTO_ESCALATE_RISK_SCORE = 80  # Critical risk
    AUTO_ESCALATE_RISK_LEVEL = RiskLevel.CRITICAL if GOVERNANCE_MODELS_AVAILABLE else None

    # SLA deadlines by priority (in hours)
    SLA_DEADLINES = {
        EscalationPriority.CRITICAL: 2,  # 2 hours
        EscalationPriority.HIGH: 8,  # 8 hours
        EscalationPriority.MEDIUM: 24,  # 1 day
        EscalationPriority.LOW: 72,  # 3 days
    }

    # SLA warning threshold (notify before deadline)
    SLA_WARNING_HOURS = 1  # Warn 1 hour before deadline

    # Default escalation recipients
    DEFAULT_ESCALATION_RECIPIENTS = ["act_human_user:governance_team"]


class NotificationEvent:
    """Represents a notification event."""

    def __init__(
        self,
        escalation_id: str,
        event_type: str,
        message: str,
        priority: "EscalationPriority",
        timestamp: datetime,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.escalation_id = escalation_id
        self.event_type = event_type
        self.message = message
        self.priority = priority
        self.timestamp = timestamp
        self.metadata = metadata or {}


class EscalationService:
    """
    Escalation service for governance decisions.

    Safety valve that routes high-risk decisions to human reviewers
    with explicit resolution requirements and SLA tracking.
    """

    def __init__(
        self,
        config: Optional[EscalationConfig] = None,
        emit_notifications: bool = True,
        store_evidence: bool = True,
    ):
        """
        Initialize the escalation service.

        Args:
            config: Optional custom configuration
            emit_notifications: Whether to emit notification events
            store_evidence: Whether to generate evidence artifacts
        """
        if not GOVERNANCE_MODELS_AVAILABLE:
            raise RuntimeError(
                "Governance models not available. Install model_governance_pack."
            )

        self.config = config or EscalationConfig()
        self.emit_notifications = emit_notifications
        self.store_evidence = store_evidence

        # In-memory storage
        self._escalations: Dict[str, Escalation] = {}
        self._notifications: List[NotificationEvent] = []
        self._evidence_artifacts: Dict[str, EvidenceArtifact] = {}

    def should_auto_escalate(self, risk: Optional["Risk"]) -> bool:
        """
        Determine if a decision should be auto-escalated based on risk.

        Args:
            risk: Risk assessment for the decision

        Returns:
            True if decision should be auto-escalated
        """
        if not risk:
            return False

        # Check risk score threshold
        if risk.overall_score >= self.config.AUTO_ESCALATE_RISK_SCORE:
            return True

        # Check risk level threshold
        if (
            risk.risk_level
            and risk.risk_level == self.config.AUTO_ESCALATE_RISK_LEVEL
        ):
            return True

        return False

    def create_escalation(
        self,
        decision_id: str,
        trigger: "EscalationTrigger",
        escalated_to: List[str],
        priority: Optional["EscalationPriority"] = None,
        context_summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Escalation":
        """
        Create an escalation for a decision.

        Validates escalation via canonical schema and sets up SLA tracking.

        Args:
            decision_id: Decision ID to escalate
            trigger: What triggered the escalation
            escalated_to: List of actor IDs to escalate to (min 1)
            priority: Optional escalation priority
            context_summary: Optional summary for reviewers
            metadata: Optional additional metadata

        Returns:
            Escalation object validated against canonical schema

        Raises:
            ValueError: If escalated_to is empty or validation fails
        """
        if not escalated_to:
            raise ValueError("Must specify at least one escalation recipient")

        # Generate escalation ID
        escalation_id = generate_escalation_id(decision_id)

        # Determine priority if not specified
        if priority is None:
            priority = self._infer_priority_from_trigger(trigger)

        # Calculate SLA deadline
        sla_deadline = self._calculate_sla_deadline(priority)

        # Create escalation (validates against schema)
        escalation = Escalation(
            escalation_id=escalation_id,
            decision_id=decision_id,
            trigger=trigger,
            escalated_to=escalated_to,
            status=EscalationStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            priority=priority,
            sla_deadline=sla_deadline,
            context_summary=context_summary,
            metadata=metadata,
        )

        # Store escalation
        self._escalations[escalation_id] = escalation

        # Emit notification for new escalation
        if self.emit_notifications:
            self._emit_notification(
                escalation=escalation,
                event_type="escalation_created",
                message=f"New {priority.value} priority escalation created",
            )

        # Generate evidence artifact
        if self.store_evidence:
            self._create_evidence_artifact(
                escalation=escalation,
                event_type="escalation_created",
            )

        return escalation

    def auto_escalate_for_risk(
        self,
        decision_id: str,
        risk: "Risk",
        escalated_to: Optional[List[str]] = None,
    ) -> Optional["Escalation"]:
        """
        Auto-escalate a decision based on risk assessment.

        Only escalates if risk meets threshold criteria.
        Uses RISK_THRESHOLD trigger to indicate automatic escalation.

        Args:
            decision_id: Decision ID to potentially escalate
            risk: Risk assessment for the decision
            escalated_to: Optional recipients (defaults to config)

        Returns:
            Escalation object if escalated, None otherwise
        """
        if not self.should_auto_escalate(risk):
            return None

        recipients = escalated_to or self.config.DEFAULT_ESCALATION_RECIPIENTS

        # Build context summary from risk
        context_summary = (
            f"Auto-escalated due to {risk.risk_level.value} risk. "
            f"Risk score: {risk.overall_score}/100. "
        )

        if risk.dimensions:
            high_dims = []
            for dim_name in ["security", "privacy", "compliance"]:
                dim_value = getattr(risk.dimensions, dim_name, None)
                if dim_value and dim_value >= 70:
                    high_dims.append(f"{dim_name}={dim_value}")
            if high_dims:
                context_summary += f"High dimensions: {', '.join(high_dims)}. "

        # Create escalation
        escalation = self.create_escalation(
            decision_id=decision_id,
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=recipients,
            priority=EscalationPriority.CRITICAL,
            context_summary=context_summary,
            metadata={
                "auto_escalated": True,
                "risk_id": risk.risk_id,
                "risk_score": risk.overall_score,
                "risk_level": risk.risk_level.value if risk.risk_level else None,
            },
        )

        return escalation

    def acknowledge_escalation(
        self,
        escalation_id: str,
        acknowledged_by: str,
    ) -> "Escalation":
        """
        Acknowledge an escalation.

        Updates status to ACKNOWLEDGED and records who acknowledged it.

        Args:
            escalation_id: Escalation ID to acknowledge
            acknowledged_by: Actor ID of acknowledger

        Returns:
            Updated Escalation object

        Raises:
            ValueError: If escalation not found or already resolved
        """
        escalation = self._escalations.get(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")

        if escalation.status in [EscalationStatus.RESOLVED, EscalationStatus.EXPIRED]:
            raise ValueError(
                f"Cannot acknowledge escalation in {escalation.status.value} state"
            )

        # Create updated escalation (immutable pattern)
        updated = escalation.model_copy(
            update={
                "status": EscalationStatus.ACKNOWLEDGED,
                "acknowledged_at": datetime.now(timezone.utc),
                "acknowledged_by": acknowledged_by,
            }
        )

        self._escalations[escalation_id] = updated

        # Emit notification
        if self.emit_notifications:
            self._emit_notification(
                escalation=updated,
                event_type="escalation_acknowledged",
                message=f"Escalation acknowledged by {acknowledged_by}",
            )

        # Generate evidence artifact
        if self.store_evidence:
            self._create_evidence_artifact(
                escalation=updated,
                event_type="escalation_acknowledged",
            )

        return updated

    def resolve_escalation(
        self,
        escalation_id: str,
        resolved_by: str,
        outcome: "ResolutionOutcome",
        notes: Optional[str] = None,
    ) -> "Escalation":
        """
        Resolve an escalation with explicit outcome.

        Requires explicit human action - escalations cannot auto-resolve.

        Args:
            escalation_id: Escalation ID to resolve
            resolved_by: Actor ID of resolver (must be human)
            outcome: Resolution outcome (approved/denied/deferred)
            notes: Optional resolution notes

        Returns:
            Updated Escalation object with resolution

        Raises:
            ValueError: If escalation not found or validation fails
        """
        escalation = self._escalations.get(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")

        if escalation.status == EscalationStatus.RESOLVED:
            raise ValueError("Escalation already resolved")

        # Validate resolver is in escalated_to list
        if resolved_by not in escalation.escalated_to:
            # Allow if resolver acknowledged it
            if resolved_by != escalation.acknowledged_by:
                raise ValueError(
                    f"Resolver {resolved_by} not authorized for this escalation"
                )

        # Create resolution
        resolution = Resolution(
            outcome=outcome,
            resolved_by=resolved_by,
            notes=notes,
        )

        # Create updated escalation
        updated = escalation.model_copy(
            update={
                "status": EscalationStatus.RESOLVED,
                "resolved_at": datetime.now(timezone.utc),
                "resolution": resolution,
            }
        )

        self._escalations[escalation_id] = updated

        # Emit notification
        if self.emit_notifications:
            self._emit_notification(
                escalation=updated,
                event_type="escalation_resolved",
                message=f"Escalation resolved: {outcome.value} by {resolved_by}",
            )

        # Generate evidence artifact
        if self.store_evidence:
            self._create_evidence_artifact(
                escalation=updated,
                event_type="escalation_resolved",
            )

        return updated

    def get_escalation(self, escalation_id: str) -> Optional["Escalation"]:
        """Retrieve an escalation by ID."""
        return self._escalations.get(escalation_id)

    def list_escalations(
        self,
        status: Optional["EscalationStatus"] = None,
        priority: Optional["EscalationPriority"] = None,
        decision_id: Optional[str] = None,
        limit: int = 100,
    ) -> List["Escalation"]:
        """
        List escalations with optional filtering.

        Args:
            status: Filter by status
            priority: Filter by priority
            decision_id: Filter by decision ID
            limit: Maximum number of results

        Returns:
            List of Escalation objects
        """
        escalations = list(self._escalations.values())

        # Apply filters
        if status is not None:
            escalations = [e for e in escalations if e.status == status]

        if priority is not None:
            escalations = [e for e in escalations if e.priority == priority]

        if decision_id is not None:
            escalations = [e for e in escalations if e.decision_id == decision_id]

        # Sort by created_at descending (most recent first)
        escalations.sort(key=lambda e: e.created_at, reverse=True)

        return escalations[:limit]

    def check_sla_status(self) -> List[NotificationEvent]:
        """
        Check SLA status for all pending/acknowledged escalations.

        Emits notifications for escalations approaching or past deadline.
        Only emits when SLA risk exists (no spam).

        Returns:
            List of notification events generated
        """
        now = datetime.now(timezone.utc)
        notifications = []

        for escalation in self._escalations.values():
            # Skip resolved/expired escalations
            if escalation.status in [
                EscalationStatus.RESOLVED,
                EscalationStatus.EXPIRED,
            ]:
                continue

            # Skip if no SLA deadline
            if not escalation.sla_deadline:
                continue

            # Check if past deadline
            if now > escalation.sla_deadline:
                # Mark as expired
                self._mark_expired(escalation)

                # Emit critical notification
                notification = self._emit_notification(
                    escalation=escalation,
                    event_type="sla_exceeded",
                    message=f"SLA EXCEEDED: Escalation {escalation.escalation_id} past deadline",
                )
                notifications.append(notification)

            else:
                # Check if approaching deadline
                warning_time = escalation.sla_deadline - timedelta(
                    hours=self.config.SLA_WARNING_HOURS
                )

                if now > warning_time:
                    # Check if we already warned
                    recent_warnings = [
                        n
                        for n in self._notifications
                        if n.escalation_id == escalation.escalation_id
                        and n.event_type == "sla_warning"
                        and (now - n.timestamp).total_seconds() < 3600  # Last hour
                    ]

                    if not recent_warnings:
                        notification = self._emit_notification(
                            escalation=escalation,
                            event_type="sla_warning",
                            message=f"SLA WARNING: Escalation {escalation.escalation_id} approaching deadline",
                        )
                        notifications.append(notification)

        return notifications

    def _infer_priority_from_trigger(
        self, trigger: "EscalationTrigger"
    ) -> "EscalationPriority":
        """Infer escalation priority from trigger type."""
        priority_map = {
            EscalationTrigger.RISK_THRESHOLD: EscalationPriority.CRITICAL,
            EscalationTrigger.POLICY_CONFLICT: EscalationPriority.HIGH,
            EscalationTrigger.ANOMALY_DETECTED: EscalationPriority.HIGH,
            EscalationTrigger.EXPLICIT_RULE: EscalationPriority.MEDIUM,
            EscalationTrigger.ACTOR_REQUEST: EscalationPriority.MEDIUM,
        }
        return priority_map.get(trigger, EscalationPriority.MEDIUM)

    def _calculate_sla_deadline(self, priority: "EscalationPriority") -> datetime:
        """Calculate SLA deadline based on priority."""
        hours = self.config.SLA_DEADLINES.get(priority, 24)
        return datetime.now(timezone.utc) + timedelta(hours=hours)

    def _mark_expired(self, escalation: "Escalation") -> None:
        """Mark an escalation as expired due to SLA breach."""
        updated = escalation.model_copy(update={"status": EscalationStatus.EXPIRED})
        self._escalations[escalation.escalation_id] = updated

        # Generate evidence artifact for expiration
        if self.store_evidence:
            self._create_evidence_artifact(
                escalation=updated,
                event_type="escalation_expired",
            )

    def _emit_notification(
        self,
        escalation: "Escalation",
        event_type: str,
        message: str,
    ) -> NotificationEvent:
        """Emit a notification event."""
        notification = NotificationEvent(
            escalation_id=escalation.escalation_id,
            event_type=event_type,
            message=message,
            priority=escalation.priority,
            timestamp=datetime.now(timezone.utc),
            metadata={
                "decision_id": escalation.decision_id,
                "status": escalation.status.value,
                "trigger": escalation.trigger.value,
            },
        )

        self._notifications.append(notification)

        # Generate evidence artifact for notification
        if self.store_evidence:
            self._create_notification_artifact(notification)

        return notification

    def _create_evidence_artifact(
        self,
        escalation: "Escalation",
        event_type: str,
    ) -> "EvidenceArtifact":
        """Create evidence artifact for escalation event."""
        # Serialize escalation to JSON
        escalation_json = escalation.model_dump_json(indent=2)
        escalation_bytes = escalation_json.encode("utf-8")

        # Generate SHA-256 hash
        sha256_hash = hashlib.sha256(escalation_bytes).hexdigest()

        # Generate artifact ID
        artifact_id = generate_evidence_id("escalation")

        # Create evidence artifact
        artifact = EvidenceArtifact(
            artifact_id=artifact_id,
            artifact_type=ArtifactType.AUDIT_TRAIL,
            sha256_hash=sha256_hash,
            created_at=datetime.now(timezone.utc),
            source="escalation_service",
            content_type="application/json",
            size_bytes=len(escalation_bytes),
            related_decision_ids=[escalation.decision_id],
            is_immutable=True,
            metadata={
                "escalation_id": escalation.escalation_id,
                "event_type": event_type,
                "status": escalation.status.value,
                "priority": escalation.priority.value if escalation.priority else None,
            },
        )

        # Store artifact
        self._evidence_artifacts[artifact_id] = artifact

        return artifact

    def _create_notification_artifact(
        self, notification: NotificationEvent
    ) -> "EvidenceArtifact":
        """Create evidence artifact for notification."""
        # Serialize notification
        notification_data = {
            "escalation_id": notification.escalation_id,
            "event_type": notification.event_type,
            "message": notification.message,
            "priority": notification.priority.value,
            "timestamp": notification.timestamp.isoformat(),
            "metadata": notification.metadata,
        }
        notification_json = str(notification_data)
        notification_bytes = notification_json.encode("utf-8")

        # Generate SHA-256 hash
        sha256_hash = hashlib.sha256(notification_bytes).hexdigest()

        # Generate artifact ID
        artifact_id = generate_evidence_id("notification")

        # Get decision ID from metadata
        decision_id = notification.metadata.get("decision_id")

        # Create evidence artifact
        artifact = EvidenceArtifact(
            artifact_id=artifact_id,
            artifact_type=ArtifactType.AUDIT_TRAIL,
            sha256_hash=sha256_hash,
            created_at=datetime.now(timezone.utc),
            source="escalation_service",
            content_type="application/json",
            size_bytes=len(notification_bytes),
            related_decision_ids=[decision_id] if decision_id else [],
            is_immutable=True,
            metadata={
                "notification_type": notification.event_type,
                "escalation_id": notification.escalation_id,
                "priority": notification.priority.value,
            },
        )

        # Store artifact
        self._evidence_artifacts[artifact_id] = artifact

        return artifact

    def get_notifications(
        self,
        escalation_id: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> List[NotificationEvent]:
        """
        Get notification events with optional filtering.

        Args:
            escalation_id: Filter by escalation ID
            event_type: Filter by event type

        Returns:
            List of notification events
        """
        notifications = list(self._notifications)

        if escalation_id:
            notifications = [n for n in notifications if n.escalation_id == escalation_id]

        if event_type:
            notifications = [n for n in notifications if n.event_type == event_type]

        return notifications

    def get_evidence_artifacts(
        self,
        escalation_id: Optional[str] = None,
        decision_id: Optional[str] = None,
    ) -> List["EvidenceArtifact"]:
        """
        Get evidence artifacts with optional filtering.

        Args:
            escalation_id: Filter by escalation ID
            decision_id: Filter by decision ID

        Returns:
            List of evidence artifacts
        """
        artifacts = list(self._evidence_artifacts.values())

        if escalation_id:
            artifacts = [
                a
                for a in artifacts
                if a.metadata and a.metadata.get("escalation_id") == escalation_id
            ]

        if decision_id:
            artifacts = [
                a
                for a in artifacts
                if a.related_decision_ids and decision_id in a.related_decision_ids
            ]

        return artifacts
