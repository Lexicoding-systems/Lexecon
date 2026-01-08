"""
Risk Assessment Service - Deterministic risk scoring for governance decisions.

Integrates with canonical Risk model to provide:
- Deterministic risk scoring based on RiskDimensions
- One-to-one linkage between Decision and Risk records
- Versioned, immutable risk assessments
- Evidence artifact generation for audit trail
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Import canonical governance models
try:
    from model_governance_pack.models import (
        ArtifactType,
        EvidenceArtifact,
        Risk,
        RiskDimensions,
        RiskFactor,
        RiskLevel,
    )

    GOVERNANCE_MODELS_AVAILABLE = True
except ImportError:
    GOVERNANCE_MODELS_AVAILABLE = False
    Risk = None
    RiskDimensions = None
    RiskFactor = None
    RiskLevel = None
    EvidenceArtifact = None
    ArtifactType = None


def generate_risk_id(decision_id: str) -> str:
    """
    Generate a risk assessment ID linked to a decision.

    Format: rsk_dec_<decision_suffix>
    Enforces one-to-one linkage between Risk and Decision.
    """
    if decision_id.startswith("dec_"):
        suffix = decision_id[4:]  # Remove "dec_" prefix
        return f"rsk_dec_{suffix}"
    else:
        # Fallback for non-canonical decision IDs
        return f"rsk_dec_{decision_id}"


def generate_evidence_id(artifact_type: str) -> str:
    """
    Generate an evidence artifact ID.

    Format: evd_<type>_<8_hex_chars>
    """
    import uuid

    hex_suffix = uuid.uuid4().hex[:8]
    return f"evd_{artifact_type}_{hex_suffix}"


class RiskScoringEngine:
    """
    Deterministic risk scoring engine.

    Calculates overall risk score from dimensional risk factors
    using transparent, explainable logic (no ML).
    """

    # Default weights for risk dimensions (sum to 1.0)
    DEFAULT_WEIGHTS = {
        "security": 0.25,
        "privacy": 0.20,
        "compliance": 0.20,
        "operational": 0.15,
        "reputational": 0.10,
        "financial": 0.10,
    }

    # Risk level thresholds
    RISK_THRESHOLDS = {
        RiskLevel.CRITICAL: 80,  # >= 80
        RiskLevel.HIGH: 60,  # 60-79
        RiskLevel.MEDIUM: 30,  # 30-59
        RiskLevel.LOW: 0,  # 0-29
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize the risk scoring engine.

        Args:
            weights: Optional custom weights for risk dimensions.
                    Must sum to 1.0. Defaults to DEFAULT_WEIGHTS.
        """
        self.weights = weights or self.DEFAULT_WEIGHTS

        # Validate weights sum to 1.0
        total = sum(self.weights.values())
        if not (0.99 <= total <= 1.01):  # Allow small floating point error
            raise ValueError(f"Risk dimension weights must sum to 1.0, got {total}")

    def calculate_overall_score(
        self,
        dimensions: "RiskDimensions",
    ) -> int:
        """
        Calculate overall risk score from dimensions.

        Uses weighted average of populated dimensions.
        Returns integer score 0-100.

        Args:
            dimensions: RiskDimensions with scores for each dimension

        Returns:
            Overall risk score (0-100)
        """
        if not GOVERNANCE_MODELS_AVAILABLE:
            raise RuntimeError("Governance models not available")

        # Get dimension scores
        dim_scores = {
            "security": dimensions.security,
            "privacy": dimensions.privacy,
            "compliance": dimensions.compliance,
            "operational": dimensions.operational,
            "reputational": dimensions.reputational,
            "financial": dimensions.financial,
        }

        # Filter out None values
        populated_dims = {k: v for k, v in dim_scores.items() if v is not None}

        if not populated_dims:
            # No dimensions scored, return minimum risk
            return 1

        # Calculate weighted average using only populated dimensions
        total_weight = sum(self.weights[k] for k in populated_dims.keys())
        weighted_sum = sum(populated_dims[k] * self.weights[k] for k in populated_dims.keys())

        overall_score = int(weighted_sum / total_weight)

        # Ensure score is in valid range
        return max(1, min(100, overall_score))

    def determine_risk_level(self, overall_score: int) -> "RiskLevel":
        """
        Determine categorical risk level from overall score.

        Args:
            overall_score: Overall risk score (0-100)

        Returns:
            RiskLevel enum value
        """
        if not GOVERNANCE_MODELS_AVAILABLE:
            raise RuntimeError("Governance models not available")

        if overall_score >= self.RISK_THRESHOLDS[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif overall_score >= self.RISK_THRESHOLDS[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif overall_score >= self.RISK_THRESHOLDS[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def calculate_risk_factors(self, dimensions: "RiskDimensions") -> List["RiskFactor"]:
        """
        Generate explainable risk factors from dimensions.

        Args:
            dimensions: RiskDimensions with scores

        Returns:
            List of RiskFactor objects showing contribution to overall score
        """
        if not GOVERNANCE_MODELS_AVAILABLE:
            raise RuntimeError("Governance models not available")

        factors = []

        # Get dimension scores
        dim_scores = {
            "security": dimensions.security,
            "privacy": dimensions.privacy,
            "compliance": dimensions.compliance,
            "operational": dimensions.operational,
            "reputational": dimensions.reputational,
            "financial": dimensions.financial,
        }

        for dim_name, score in dim_scores.items():
            if score is not None:
                factors.append(
                    RiskFactor(
                        name=f"{dim_name}_risk",
                        weight=self.weights[dim_name],
                        value=float(score),
                    )
                )

        return factors


class RiskService:
    """
    Risk assessment service for governance decisions.

    Provides deterministic risk scoring with full audit trail.
    Enforces one-to-one linkage between Risk and Decision records.
    """

    def __init__(
        self,
        scoring_engine: Optional[RiskScoringEngine] = None,
        store_evidence: bool = True,
    ):
        """
        Initialize the risk service.

        Args:
            scoring_engine: Optional custom scoring engine
            store_evidence: Whether to generate evidence artifacts
        """
        if not GOVERNANCE_MODELS_AVAILABLE:
            raise RuntimeError("Governance models not available. Install model_governance_pack.")

        self.scoring_engine = scoring_engine or RiskScoringEngine()
        self.store_evidence = store_evidence

        # In-memory storage for risk assessments and evidence
        self._risk_assessments: Dict[str, Risk] = {}
        self._evidence_artifacts: Dict[str, EvidenceArtifact] = {}

        # Track decision-to-risk linkage (one-to-one)
        self._decision_to_risk: Dict[str, str] = {}

    def assess_risk(
        self,
        decision_id: str,
        dimensions: "RiskDimensions",
        likelihood: Optional[float] = None,
        impact: Optional[int] = None,
        mitigations: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Risk":
        """
        Assess risk for a decision.

        Creates a new Risk record with deterministic scoring.
        Enforces one-to-one linkage with Decision.

        Args:
            decision_id: Decision ID this risk assessment is for
            dimensions: RiskDimensions with scores
            likelihood: Optional probability of harm (0-1)
            impact: Optional severity of harm (1-5)
            mitigations: Optional list of mitigations applied
            metadata: Optional additional metadata

        Returns:
            Risk object validated against canonical schema

        Raises:
            ValueError: If decision already has a risk assessment
        """
        # Enforce one-to-one linkage
        if decision_id in self._decision_to_risk:
            existing_risk_id = self._decision_to_risk[decision_id]
            raise ValueError(
                f"Decision {decision_id} already has risk assessment {existing_risk_id}. "
                "Create new assessment with new decision_id for versioning."
            )

        # Generate risk ID
        risk_id = generate_risk_id(decision_id)

        # Calculate overall score
        overall_score = self.scoring_engine.calculate_overall_score(dimensions)

        # Determine risk level
        risk_level = self.scoring_engine.determine_risk_level(overall_score)

        # Generate risk factors
        factors = self.scoring_engine.calculate_risk_factors(dimensions)

        # Create Risk object (validates against schema)
        risk = Risk(
            risk_id=risk_id,
            decision_id=decision_id,
            overall_score=overall_score,
            timestamp=datetime.now(timezone.utc),
            risk_level=risk_level,
            dimensions=dimensions,
            likelihood=likelihood,
            impact=impact,
            factors=factors,
            mitigations_applied=mitigations or [],
            metadata=metadata,
        )

        # Store risk assessment
        self._risk_assessments[risk_id] = risk
        self._decision_to_risk[decision_id] = risk_id

        # Generate evidence artifact if enabled
        if self.store_evidence:
            self._create_evidence_artifact(risk)

        return risk

    def get_risk(self, risk_id: str) -> Optional["Risk"]:
        """Retrieve a risk assessment by ID."""
        return self._risk_assessments.get(risk_id)

    def get_risk_for_decision(self, decision_id: str) -> Optional["Risk"]:
        """Retrieve risk assessment for a decision."""
        risk_id = self._decision_to_risk.get(decision_id)
        if risk_id:
            return self._risk_assessments.get(risk_id)
        return None

    def list_risks(
        self,
        min_score: Optional[int] = None,
        risk_level: Optional["RiskLevel"] = None,
        limit: int = 100,
    ) -> List["Risk"]:
        """
        List risk assessments with optional filtering.

        Args:
            min_score: Minimum overall score filter
            risk_level: Risk level filter
            limit: Maximum number of results

        Returns:
            List of Risk objects
        """
        risks = list(self._risk_assessments.values())

        # Apply filters
        if min_score is not None:
            risks = [r for r in risks if r.overall_score >= min_score]

        if risk_level is not None:
            risks = [r for r in risks if r.risk_level == risk_level]

        # Sort by score descending (highest risk first)
        risks.sort(key=lambda r: r.overall_score, reverse=True)

        return risks[:limit]

    def _create_evidence_artifact(self, risk: "Risk") -> "EvidenceArtifact":
        """
        Create evidence artifact for risk assessment.

        Args:
            risk: Risk object to create artifact for

        Returns:
            EvidenceArtifact object
        """
        # Serialize risk to JSON
        risk_json = risk.model_dump_json(indent=2)
        risk_bytes = risk_json.encode("utf-8")

        # Generate SHA-256 hash
        sha256_hash = hashlib.sha256(risk_bytes).hexdigest()

        # Generate artifact ID
        artifact_id = generate_evidence_id("risk")

        # Create evidence artifact
        artifact = EvidenceArtifact(
            artifact_id=artifact_id,
            artifact_type=ArtifactType.DECISION_LOG,  # Risk is part of decision log
            sha256_hash=sha256_hash,
            created_at=datetime.now(timezone.utc),
            source="risk_service",
            content_type="application/json",
            size_bytes=len(risk_bytes),
            related_decision_ids=[risk.decision_id],
            is_immutable=True,
            metadata={
                "risk_id": risk.risk_id,
                "overall_score": risk.overall_score,
                "risk_level": risk.risk_level.value if risk.risk_level else None,
            },
        )

        # Store artifact
        self._evidence_artifacts[artifact_id] = artifact

        return artifact

    def get_evidence_artifact(self, artifact_id: str) -> Optional["EvidenceArtifact"]:
        """Retrieve an evidence artifact by ID."""
        return self._evidence_artifacts.get(artifact_id)

    def list_evidence_artifacts(
        self, decision_id: Optional[str] = None
    ) -> List["EvidenceArtifact"]:
        """
        List evidence artifacts with optional filtering.

        Args:
            decision_id: Filter by decision ID

        Returns:
            List of EvidenceArtifact objects
        """
        artifacts = list(self._evidence_artifacts.values())

        if decision_id:
            artifacts = [
                a
                for a in artifacts
                if a.related_decision_ids and decision_id in a.related_decision_ids
            ]

        return artifacts
