"""Tests for risk assessment service."""


import pytest

from lexecon.risk.service import (
    RiskScoringEngine,
    RiskService,
    generate_evidence_id,
    generate_risk_id,
)

# Import canonical governance models
try:
    from model_governance_pack.models import (
        EvidenceArtifact,
        Risk,
        RiskDimensions,
        RiskFactor,
        RiskLevel,
    )

    GOVERNANCE_MODELS_AVAILABLE = True
except ImportError:
    GOVERNANCE_MODELS_AVAILABLE = False
    pytestmark = pytest.mark.skip("Governance models not available")


class TestRiskIdGeneration:
    """Tests for risk ID generation."""

    def test_generate_risk_id_from_canonical_decision(self):
        """Test risk ID generation from canonical decision ID."""
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"
        risk_id = generate_risk_id(decision_id)

        assert risk_id == "rsk_dec_01JQXYZ1234567890ABCDEFGH"
        assert risk_id.startswith("rsk_dec_")

    def test_generate_risk_id_from_legacy_decision(self):
        """Test risk ID generation from legacy decision ID."""
        decision_id = "legacy-decision-123"
        risk_id = generate_risk_id(decision_id)

        assert risk_id == "rsk_dec_legacy-decision-123"
        assert risk_id.startswith("rsk_dec_")

    def test_risk_id_one_to_one_mapping(self):
        """Test that each decision maps to exactly one risk ID."""
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        risk_id1 = generate_risk_id(decision_id)
        risk_id2 = generate_risk_id(decision_id)

        # Same decision always produces same risk ID
        assert risk_id1 == risk_id2

    def test_generate_evidence_id_format(self):
        """Test evidence artifact ID generation."""
        artifact_id = generate_evidence_id("risk")

        assert artifact_id.startswith("evd_risk_")
        assert len(artifact_id) == len("evd_risk_") + 8  # 8 hex chars

    def test_generate_evidence_id_uniqueness(self):
        """Test that evidence IDs are unique."""
        ids = {generate_evidence_id("risk") for _ in range(100)}
        assert len(ids) == 100  # All unique


class TestRiskScoringEngine:
    """Tests for deterministic risk scoring engine."""

    @pytest.fixture
    def scoring_engine(self):
        """Create a default scoring engine."""
        return RiskScoringEngine()

    def test_scoring_engine_initialization(self, scoring_engine):
        """Test scoring engine initializes with default weights."""
        assert scoring_engine.weights is not None
        assert sum(scoring_engine.weights.values()) == pytest.approx(1.0)

    def test_custom_weights_validation(self):
        """Test that custom weights must sum to 1.0."""
        invalid_weights = {
            "security": 0.5,
            "privacy": 0.3,
            "compliance": 0.1,
            "operational": 0.1,
            "reputational": 0.1,
            "financial": 0.1,
        }  # Sum = 1.1

        with pytest.raises(ValueError, match="must sum to 1.0"):
            RiskScoringEngine(weights=invalid_weights)

    def test_calculate_overall_score_all_dimensions(self, scoring_engine):
        """Test overall score calculation with all dimensions."""
        dimensions = RiskDimensions(
            security=80,
            privacy=60,
            compliance=40,
            operational=30,
            reputational=20,
            financial=10,
        )

        score = scoring_engine.calculate_overall_score(dimensions)

        # With default weights: 0.25*80 + 0.20*60 + 0.20*40 + 0.15*30 + 0.10*20 + 0.10*10
        # = 20 + 12 + 8 + 4.5 + 2 + 1 = 47.5 ≈ 47
        assert isinstance(score, int)
        assert 1 <= score <= 100
        assert score == 47

    def test_calculate_overall_score_partial_dimensions(self, scoring_engine):
        """Test score calculation with only some dimensions populated."""
        dimensions = RiskDimensions(
            security=100,
            privacy=80,
            # Other dimensions None
        )

        score = scoring_engine.calculate_overall_score(dimensions)

        # Should weight only populated dimensions
        # (100 * 0.25 + 80 * 0.20) / (0.25 + 0.20) = 41 / 0.45 ≈ 91
        assert isinstance(score, int)
        assert 80 <= score <= 100  # Should be high since both are high

    def test_calculate_overall_score_empty_dimensions(self, scoring_engine):
        """Test score calculation with no dimensions populated."""
        dimensions = RiskDimensions()  # All None

        score = scoring_engine.calculate_overall_score(dimensions)

        # Should return minimum score
        assert score == 1

    def test_calculate_overall_score_bounds(self, scoring_engine):
        """Test that overall score stays within valid bounds."""
        # Test minimum
        dimensions_min = RiskDimensions(security=0, privacy=0)
        score_min = scoring_engine.calculate_overall_score(dimensions_min)
        assert score_min >= 1

        # Test maximum
        dimensions_max = RiskDimensions(security=100, privacy=100)
        score_max = scoring_engine.calculate_overall_score(dimensions_max)
        assert score_max <= 100

    def test_determine_risk_level_low(self, scoring_engine):
        """Test risk level determination for low scores."""
        assert scoring_engine.determine_risk_level(1) == RiskLevel.LOW
        assert scoring_engine.determine_risk_level(15) == RiskLevel.LOW
        assert scoring_engine.determine_risk_level(29) == RiskLevel.LOW

    def test_determine_risk_level_medium(self, scoring_engine):
        """Test risk level determination for medium scores."""
        assert scoring_engine.determine_risk_level(30) == RiskLevel.MEDIUM
        assert scoring_engine.determine_risk_level(45) == RiskLevel.MEDIUM
        assert scoring_engine.determine_risk_level(59) == RiskLevel.MEDIUM

    def test_determine_risk_level_high(self, scoring_engine):
        """Test risk level determination for high scores."""
        assert scoring_engine.determine_risk_level(60) == RiskLevel.HIGH
        assert scoring_engine.determine_risk_level(70) == RiskLevel.HIGH
        assert scoring_engine.determine_risk_level(79) == RiskLevel.HIGH

    def test_determine_risk_level_critical(self, scoring_engine):
        """Test risk level determination for critical scores."""
        assert scoring_engine.determine_risk_level(80) == RiskLevel.CRITICAL
        assert scoring_engine.determine_risk_level(90) == RiskLevel.CRITICAL
        assert scoring_engine.determine_risk_level(100) == RiskLevel.CRITICAL

    def test_calculate_risk_factors(self, scoring_engine):
        """Test risk factor generation."""
        dimensions = RiskDimensions(
            security=80,
            privacy=60,
            compliance=40,
        )

        factors = scoring_engine.calculate_risk_factors(dimensions)

        assert len(factors) == 3
        assert all(isinstance(f, RiskFactor) for f in factors)

        # Check that factors have correct structure
        security_factor = next(f for f in factors if f.name == "security_risk")
        assert security_factor.weight == 0.25
        assert security_factor.value == 80.0

    def test_calculate_risk_factors_empty(self, scoring_engine):
        """Test risk factor generation with no dimensions."""
        dimensions = RiskDimensions()
        factors = scoring_engine.calculate_risk_factors(dimensions)

        assert len(factors) == 0


class TestRiskService:
    """Tests for risk assessment service."""

    @pytest.fixture
    def service(self):
        """Create a risk service instance."""
        return RiskService()

    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service.scoring_engine is not None
        assert service.store_evidence is True

    def test_assess_risk_creates_valid_risk(self, service):
        """Test that risk assessment creates valid Risk object."""
        dimensions = RiskDimensions(
            security=70,
            privacy=50,
            compliance=60,
        )

        risk = service.assess_risk(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            dimensions=dimensions,
            likelihood=0.6,
            impact=4,
            mitigations=["encryption", "access_control"],
        )

        # Validate against schema
        assert isinstance(risk, Risk)
        assert risk.risk_id == "rsk_dec_01JQXYZ1234567890ABCDEFGH"
        assert risk.decision_id == "dec_01JQXYZ1234567890ABCDEFGH"
        assert 1 <= risk.overall_score <= 100
        assert risk.risk_level in [
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        ]
        assert risk.likelihood == 0.6
        assert risk.impact == 4
        assert "encryption" in risk.mitigations_applied

    def test_assess_risk_one_to_one_enforcement(self, service):
        """Test that one decision can only have one risk assessment."""
        dimensions = RiskDimensions(security=50)
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        # First assessment succeeds
        risk1 = service.assess_risk(decision_id=decision_id, dimensions=dimensions)
        assert risk1 is not None

        # Second assessment for same decision fails
        with pytest.raises(ValueError, match="already has risk assessment"):
            service.assess_risk(decision_id=decision_id, dimensions=dimensions)

    def test_assess_risk_versioning(self, service):
        """Test that new decision creates new risk assessment."""
        dimensions = RiskDimensions(security=50)

        # First decision and risk
        risk1 = service.assess_risk(
            decision_id="dec_01JQXYZ1111111111111111111", dimensions=dimensions,
        )

        # Second decision with updated dimensions
        dimensions2 = RiskDimensions(security=80)
        risk2 = service.assess_risk(
            decision_id="dec_01JQXYZ2222222222222222222", dimensions=dimensions2,
        )

        # Both risks should exist independently
        assert risk1.risk_id != risk2.risk_id
        assert risk1.overall_score != risk2.overall_score

        # Original risk unchanged (immutable)
        retrieved_risk1 = service.get_risk(risk1.risk_id)
        assert retrieved_risk1.overall_score == risk1.overall_score

    def test_get_risk(self, service):
        """Test retrieving risk by ID."""
        dimensions = RiskDimensions(security=60)
        risk = service.assess_risk(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH", dimensions=dimensions,
        )

        retrieved = service.get_risk(risk.risk_id)
        assert retrieved is not None
        assert retrieved.risk_id == risk.risk_id

    def test_get_risk_not_found(self, service):
        """Test retrieving non-existent risk."""
        retrieved = service.get_risk("rsk_dec_nonexistent")
        assert retrieved is None

    def test_get_risk_for_decision(self, service):
        """Test retrieving risk by decision ID."""
        dimensions = RiskDimensions(security=60)
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        risk = service.assess_risk(decision_id=decision_id, dimensions=dimensions)

        retrieved = service.get_risk_for_decision(decision_id)
        assert retrieved is not None
        assert retrieved.decision_id == decision_id
        assert retrieved.risk_id == risk.risk_id

    def test_list_risks_no_filter(self, service):
        """Test listing all risks."""
        # Create multiple risk assessments
        for i in range(5):
            dimensions = RiskDimensions(security=20 * i)
            service.assess_risk(
                decision_id=f"dec_01JQXYZ{i:022d}", dimensions=dimensions,
            )

        risks = service.list_risks()
        assert len(risks) == 5

    def test_list_risks_with_min_score(self, service):
        """Test listing risks with minimum score filter."""
        # Create risks with different scores
        service.assess_risk("dec_01JQXYZ1111111111111111111", RiskDimensions(security=20))
        service.assess_risk("dec_01JQXYZ2222222222222222222", RiskDimensions(security=50))
        service.assess_risk("dec_01JQXYZ3333333333333333333", RiskDimensions(security=80))

        # Filter for medium+ risk
        risks = service.list_risks(min_score=30)
        assert all(r.overall_score >= 30 for r in risks)

    def test_list_risks_with_risk_level(self, service):
        """Test listing risks by risk level."""
        # Create risks at different levels
        service.assess_risk("dec_01JQXYZ1111111111111111111", RiskDimensions(security=20))
        service.assess_risk("dec_01JQXYZ2222222222222222222", RiskDimensions(security=50))
        service.assess_risk("dec_01JQXYZ3333333333333333333", RiskDimensions(security=90))

        # Filter for critical risks
        critical_risks = service.list_risks(risk_level=RiskLevel.CRITICAL)
        assert all(r.risk_level == RiskLevel.CRITICAL for r in critical_risks)

    def test_list_risks_sorted_by_score(self, service):
        """Test that risks are sorted by score descending."""
        # Create risks with different scores
        service.assess_risk("dec_01JQXYZ1111111111111111111", RiskDimensions(security=30))
        service.assess_risk("dec_01JQXYZ2222222222222222222", RiskDimensions(security=80))
        service.assess_risk("dec_01JQXYZ3333333333333333333", RiskDimensions(security=50))

        risks = service.list_risks()

        # Should be sorted highest to lowest
        for i in range(len(risks) - 1):
            assert risks[i].overall_score >= risks[i + 1].overall_score

    def test_evidence_artifact_generation(self, service):
        """Test that evidence artifacts are generated for risk assessments."""
        dimensions = RiskDimensions(security=70)
        risk = service.assess_risk(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH", dimensions=dimensions,
        )

        # Evidence artifact should be created
        artifacts = service.list_evidence_artifacts()
        assert len(artifacts) == 1

        artifact = artifacts[0]
        assert isinstance(artifact, EvidenceArtifact)
        assert artifact.artifact_id.startswith("evd_risk_")
        assert artifact.is_immutable is True
        assert risk.decision_id in artifact.related_decision_ids

    def test_evidence_artifact_immutability(self, service):
        """Test that evidence artifacts have SHA-256 hashes."""
        dimensions = RiskDimensions(security=70)
        service.assess_risk(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH", dimensions=dimensions,
        )

        artifacts = service.list_evidence_artifacts()
        artifact = artifacts[0]

        # Should have SHA-256 hash
        assert artifact.sha256_hash is not None
        assert len(artifact.sha256_hash) == 64  # SHA-256 hex
        assert all(c in "0123456789abcdef" for c in artifact.sha256_hash)

    def test_evidence_artifact_metadata(self, service):
        """Test that evidence artifacts contain risk metadata."""
        dimensions = RiskDimensions(security=85)
        risk = service.assess_risk(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH", dimensions=dimensions,
        )

        artifacts = service.list_evidence_artifacts()
        artifact = artifacts[0]

        assert artifact.metadata["risk_id"] == risk.risk_id
        assert artifact.metadata["overall_score"] == risk.overall_score
        assert artifact.metadata["risk_level"] == risk.risk_level.value

    def test_evidence_disabled(self):
        """Test that evidence generation can be disabled."""
        service = RiskService(store_evidence=False)

        dimensions = RiskDimensions(security=70)
        risk = service.assess_risk(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH", dimensions=dimensions,
        )

        # Risk should be created but no evidence
        assert risk is not None
        artifacts = service.list_evidence_artifacts()
        assert len(artifacts) == 0

    def test_list_evidence_artifacts_by_decision(self, service):
        """Test filtering evidence artifacts by decision ID."""
        # Create multiple risk assessments
        service.assess_risk("dec_01JQXYZ1111111111111111111", RiskDimensions(security=50))
        service.assess_risk("dec_01JQXYZ2222222222222222222", RiskDimensions(security=70))

        # Filter by specific decision
        artifacts = service.list_evidence_artifacts(
            decision_id="dec_01JQXYZ1111111111111111111",
        )
        assert len(artifacts) == 1
        assert "dec_01JQXYZ1111111111111111111" in artifacts[0].related_decision_ids


class TestRiskServiceIntegration:
    """Integration tests for risk service with complete workflows."""

    def test_complete_risk_assessment_workflow(self):
        """Test complete workflow from risk assessment to evidence."""
        service = RiskService()

        # 1. Create risk assessment
        dimensions = RiskDimensions(
            security=75,
            privacy=60,
            compliance=55,
            operational=40,
        )

        risk = service.assess_risk(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            dimensions=dimensions,
            likelihood=0.7,
            impact=4,
            mitigations=["encryption", "audit_logging", "access_control"],
            metadata={"action": "data_export", "user": "analyst@company.com"},
        )

        # 2. Validate risk object
        assert risk.risk_id == "rsk_dec_01JQXYZ1234567890ABCDEFGH"
        assert risk.overall_score > 50  # Should be medium-high
        assert risk.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]
        assert len(risk.factors) == 4  # Four dimensions provided
        assert risk.mitigations_applied == [
            "encryption",
            "audit_logging",
            "access_control",
        ]

        # 3. Retrieve risk by decision ID
        retrieved_risk = service.get_risk_for_decision("dec_01JQXYZ1234567890ABCDEFGH")
        assert retrieved_risk.risk_id == risk.risk_id

        # 4. Verify evidence artifact
        artifacts = service.list_evidence_artifacts(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
        )
        assert len(artifacts) == 1
        assert artifacts[0].is_immutable is True

    def test_high_risk_detection(self):
        """Test detection and categorization of high-risk assessments."""
        service = RiskService()

        # Create high-risk assessment
        high_risk_dims = RiskDimensions(
            security=90,
            privacy=85,
            compliance=80,
        )

        risk = service.assess_risk(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH", dimensions=high_risk_dims,
        )

        assert risk.overall_score >= 80
        assert risk.risk_level == RiskLevel.CRITICAL

        # Should appear in high-risk queries
        critical_risks = service.list_risks(risk_level=RiskLevel.CRITICAL)
        assert any(r.risk_id == risk.risk_id for r in critical_risks)

    def test_low_risk_assessment(self):
        """Test low-risk assessment workflow."""
        service = RiskService()

        low_risk_dims = RiskDimensions(
            security=10,
            privacy=15,
            operational=5,
        )

        risk = service.assess_risk(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH", dimensions=low_risk_dims,
        )

        assert risk.overall_score < 30
        assert risk.risk_level == RiskLevel.LOW
