"""
Decision Responsibility Tracker

Tracks WHO made decisions, WHY, and maintains accountability chains.
Critical for audits, legal liability, and EU AI Act Article 14 compliance.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DecisionMaker(Enum):
    """Who made the decision."""
    AI_SYSTEM = "ai_system"  # Fully automated
    HUMAN_OPERATOR = "human_operator"  # Human with AI assistance
    HUMAN_SUPERVISOR = "human_supervisor"  # Supervisory override
    HUMAN_EXECUTIVE = "human_executive"  # Executive decision
    DELEGATED = "delegated"  # Delegated authority
    EMERGENCY_OVERRIDE = "emergency_override"  # Emergency human intervention


class ResponsibilityLevel(Enum):
    """Level of responsibility for the decision."""
    FULL = "full"  # Full legal responsibility
    SHARED = "shared"  # Shared between human and AI
    SUPERVISED = "supervised"  # AI decision with human oversight
    AUTOMATED = "automated"  # Fully automated, organization responsible


@dataclass
class ResponsibilityRecord:
    """
    Records who is responsible for a decision and why.

    Critical for legal liability and compliance audits.
    """
    record_id: str
    decision_id: str
    timestamp: str

    # WHO
    decision_maker: DecisionMaker
    responsible_party: str  # Name, ID, or "system"
    role: str  # Job title or role

    # WHY
    reasoning: str
    confidence: float  # 0.0-1.0

    # ACCOUNTABILITY
    responsibility_level: ResponsibilityLevel
    delegated_from: Optional[str] = None  # If delegated, who delegated
    escalated_to: Optional[str] = None  # If escalated, who received it

    # CONTEXT
    override_ai: bool = False  # Did human override AI?
    ai_recommendation: Optional[str] = None  # What did AI recommend?
    review_required: bool = False  # Does this need review?
    reviewed_by: Optional[str] = None  # Who reviewed it
    reviewed_at: Optional[str] = None  # When reviewed

    # LEGAL
    liability_accepted: bool = False  # Did responsible party accept liability?
    liability_signature: Optional[str] = None  # Cryptographic signature

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **asdict(self),
            "decision_maker": self.decision_maker.value,
            "responsibility_level": self.responsibility_level.value
        }


class ResponsibilityTracker:
    """
    Tracks decision responsibility for compliance and liability.

    Answers critical questions:
    - Who decided this?
    - Why did they decide it?
    - Did they have authority?
    - Is there accountability?
    """

    def __init__(self, storage=None):
        """
        Initialize responsibility tracker.

        Args:
            storage: Optional ResponsibilityStorage instance for persistence
        """
        self.storage = storage
        self.records: List[ResponsibilityRecord] = []

        # Load existing records from storage if available
        if self.storage:
            self.records = self.storage.load_all_records()

    def record_decision(
        self,
        decision_id: str,
        decision_maker: DecisionMaker,
        responsible_party: str,
        role: str,
        reasoning: str,
        confidence: float = 1.0,
        responsibility_level: ResponsibilityLevel = ResponsibilityLevel.FULL,
        override_ai: bool = False,
        ai_recommendation: Optional[str] = None,
        delegated_from: Optional[str] = None,
        escalated_to: Optional[str] = None,
        review_required: bool = False,
        liability_accepted: bool = False,
        liability_signature: Optional[str] = None
    ) -> ResponsibilityRecord:
        """
        Record who is responsible for a decision.

        Call this for EVERY decision to maintain accountability.
        """
        record = ResponsibilityRecord(
            record_id=f"resp_{len(self.records) + 1}",
            decision_id=decision_id,
            timestamp=datetime.utcnow().isoformat(),
            decision_maker=decision_maker,
            responsible_party=responsible_party,
            role=role,
            reasoning=reasoning,
            confidence=confidence,
            responsibility_level=responsibility_level,
            override_ai=override_ai,
            ai_recommendation=ai_recommendation,
            delegated_from=delegated_from,
            escalated_to=escalated_to,
            review_required=review_required,
            liability_accepted=liability_accepted,
            liability_signature=liability_signature
        )

        self.records.append(record)

        # Auto-save to storage if available
        if self.storage:
            self.storage.save_record(record)

        return record

    def mark_reviewed(
        self,
        record_id: str,
        reviewed_by: str,
        notes: Optional[str] = None
    ) -> bool:
        """Mark a decision as reviewed."""
        for record in self.records:
            if record.record_id == record_id:
                record.reviewed_by = reviewed_by
                record.reviewed_at = datetime.utcnow().isoformat()

                # Auto-save update to storage if available
                if self.storage:
                    self.storage.update_record(
                        record_id,
                        reviewed_by=reviewed_by,
                        reviewed_at=record.reviewed_at
                    )

                return True
        return False

    def get_responsibility_chain(self, decision_id: str) -> List[ResponsibilityRecord]:
        """
        Get the full chain of responsibility for a decision.

        Shows delegations, escalations, and reviews.
        """
        return [r for r in self.records if r.decision_id == decision_id]

    def get_by_responsible_party(self, party: str) -> List[ResponsibilityRecord]:
        """Get all decisions made by a specific party."""
        return [r for r in self.records if r.responsible_party == party]

    def get_ai_overrides(self) -> List[ResponsibilityRecord]:
        """Get all decisions where humans overrode AI."""
        return [r for r in self.records if r.override_ai]

    def get_pending_reviews(self) -> List[ResponsibilityRecord]:
        """Get decisions awaiting review."""
        return [r for r in self.records if r.review_required and not r.reviewed_by]

    def generate_accountability_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate accountability report.

        Critical for audits and legal defense.
        """
        records = self.records

        # Filter by date if provided
        if start_date:
            records = [r for r in records if r.timestamp >= start_date]
        if end_date:
            records = [r for r in records if r.timestamp <= end_date]

        # Calculate statistics
        total = len(records)
        by_maker = {}
        by_responsibility_level = {}
        overrides = 0
        pending_reviews = 0
        liability_accepted = 0

        for record in records:
            # Count by decision maker
            maker = record.decision_maker.value
            by_maker[maker] = by_maker.get(maker, 0) + 1

            # Count by responsibility level
            level = record.responsibility_level.value
            by_responsibility_level[level] = by_responsibility_level.get(level, 0) + 1

            # Count overrides
            if record.override_ai:
                overrides += 1

            # Count pending reviews
            if record.review_required and not record.reviewed_by:
                pending_reviews += 1

            # Count liability acceptance
            if record.liability_accepted:
                liability_accepted += 1

        # Identify most responsible parties
        party_counts = {}
        for record in records:
            party_counts[record.responsible_party] = party_counts.get(record.responsible_party, 0) + 1

        top_parties = sorted(party_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "report_type": "ACCOUNTABILITY_REPORT",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start": start_date or "inception",
                "end": end_date or "present"
            },
            "summary": {
                "total_decisions": total,
                "by_decision_maker": by_maker,
                "by_responsibility_level": by_responsibility_level,
                "ai_overrides": overrides,
                "override_rate": (overrides / total * 100) if total > 0 else 0,
                "pending_reviews": pending_reviews,
                "liability_accepted_count": liability_accepted,
                "liability_acceptance_rate": (liability_accepted / total * 100) if total > 0 else 0
            },
            "top_responsible_parties": [
                {"party": party, "decision_count": count}
                for party, count in top_parties
            ],
            "compliance_indicators": {
                "human_oversight_active": overrides > 0 or any(
                    r.decision_maker != DecisionMaker.AI_SYSTEM for r in records
                ),
                "review_process_active": any(r.reviewed_by for r in records),
                "liability_framework_active": liability_accepted > 0,
                "delegation_chain_documented": any(r.delegated_from for r in records)
            }
        }

    def export_for_legal(self, decision_id: str) -> Dict[str, Any]:
        """
        Export responsibility chain for legal proceedings.

        Provides full accountability trail with signatures.
        """
        chain = self.get_responsibility_chain(decision_id)

        return {
            "export_type": "LEGAL_RESPONSIBILITY_CHAIN",
            "decision_id": decision_id,
            "generated_at": datetime.utcnow().isoformat(),
            "chain_length": len(chain),
            "responsibility_records": [r.to_dict() for r in chain],
            "final_responsible_party": chain[-1].responsible_party if chain else None,
            "human_in_loop": any(r.decision_maker != DecisionMaker.AI_SYSTEM for r in chain),
            "signatures_present": [
                r.record_id for r in chain if r.liability_signature
            ],
            "legal_attestation": {
                "accountability_established": len(chain) > 0,
                "human_oversight_documented": any(
                    r.decision_maker != DecisionMaker.AI_SYSTEM for r in chain
                ),
                "liability_accepted": any(r.liability_accepted for r in chain)
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize all records."""
        return {
            "records": [r.to_dict() for r in self.records]
        }
