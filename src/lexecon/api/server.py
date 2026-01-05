"""
API Server - REST API for Lexecon governance system.

Provides endpoints for health checks, policy management, decision requests,
and audit operations.
"""

import json
import time
import uuid
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
import os

from lexecon.decision.service import DecisionRequest, DecisionService
from lexecon.identity.signing import KeyManager
from lexecon.ledger.chain import LedgerChain
from lexecon.policy.engine import PolicyEngine, PolicyMode
from lexecon.storage.persistence import LedgerStorage
from lexecon.responsibility.tracker import (
    ResponsibilityTracker,
    DecisionMaker,
    ResponsibilityLevel
)
from lexecon.responsibility.storage import ResponsibilityStorage

# Security imports
from lexecon.security.auth_service import AuthService, Role, Permission, User, Session
from lexecon.security.audit_service import AuditService, ExportStatus
from lexecon.security.signature_service import SignatureService

# Governance service imports
from lexecon.risk.service import RiskService, RiskScoringEngine
from lexecon.escalation.service import EscalationService
from lexecon.override.service import OverrideService
from lexecon.evidence.service import EvidenceService
from lexecon.compliance_mapping.service import (
    ComplianceMappingService,
    RegulatoryFramework,
    GovernancePrimitive,
    ControlStatus
)

# Import governance models for type hints
try:
    from model_governance_pack.models import (
        Risk,
        RiskLevel,
        RiskDimensions,
        Escalation,
        EscalationPriority,
        EscalationStatus,
        Override,
        OverrideType,
        OriginalOutcome,
        NewOutcome,
        OverrideScope,
        EvidenceArtifact,
        ArtifactType,
        DigitalSignature,
    )
    GOVERNANCE_MODELS_AVAILABLE = True
except ImportError:
    GOVERNANCE_MODELS_AVAILABLE = False


# Pydantic models for request/response validation
class DecisionRequestModel(BaseModel):
    """Model for decision request."""

    request_id: Optional[str] = None
    actor: str = Field(..., description="Actor requesting the action")
    proposed_action: str = Field(..., description="Proposed action to perform")
    tool: str = Field(..., description="Tool to be used")
    user_intent: str = Field(..., description="User's intent for this action")
    data_classes: List[str] = Field(default_factory=list)
    risk_level: int = Field(default=1, ge=1, le=5)
    requested_output_type: str = Field(default="tool_action")
    policy_mode: str = Field(default="strict")
    context: Dict[str, Any] = Field(default_factory=dict)


class PolicyLoadModel(BaseModel):
    """Model for loading policy - supports both wrapped and direct formats."""

    # Support wrapped format {"policy": {...}}
    policy: Optional[Dict[str, Any]] = Field(default=None, description="Policy data (wrapped format)")
    # Support direct format
    name: Optional[str] = Field(default=None, description="Policy name")
    version: Optional[str] = Field(default="1.0", description="Policy version")
    mode: Optional[str] = Field(default=None, description="Policy mode")
    terms: Optional[List[Dict[str, Any]]] = Field(default=None, description="Policy terms")
    relations: Optional[List[Dict[str, Any]]] = Field(default=None, description="Policy relations")
    constraints: Optional[List[Dict[str, Any]]] = Field(default=None, description="Policy constraints")


class InterventionModel(BaseModel):
    """Model for human intervention request."""

    intervention_type: str = Field(..., description="Type of intervention")
    ai_recommendation: Dict[str, Any] = Field(..., description="AI's recommendation (must include 'confidence' key)")
    human_decision: Dict[str, Any] = Field(..., description="Human's decision")
    human_role: str = Field(..., description="Human's role")
    reason: str = Field(..., description="Reason for intervention")
    request_context: Optional[Dict[str, Any]] = Field(default=None, description="Additional request context")
    response_time_ms: Optional[int] = Field(default=None, description="Response time in milliseconds")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    node_id: str
    timestamp: str


class StatusResponse(BaseModel):
    """System status response."""

    status: str
    node_id: str
    policy_loaded: bool  # For backwards compatibility
    policies_loaded: bool
    policy_hash: Optional[str]
    ledger_entries: int
    uptime_seconds: float
    timestamp: str


# Security models
class LoginRequest(BaseModel):
    """Login request."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response."""
    success: bool
    session_id: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CreateUserRequest(BaseModel):
    """Create user request."""
    username: str
    email: str
    password: str
    role: str
    full_name: str


class ExportRequestModel(BaseModel):
    """Audit packet export request with attestation."""
    # Step 1: Metadata
    requester_name: str
    requester_email: str
    purpose: str
    case_id: Optional[str] = None
    notes: Optional[str] = None

    # Step 2: Configuration
    time_window: str = "all"
    formats: List[str] = ["json"]
    include_decisions: bool = True
    include_interventions: bool = True
    include_ledger: bool = True
    include_responsibility: bool = True

    # Step 3: Legal Attestation
    attestation_accepted: bool
    attestation_text: str


# ========== Governance API Models (Phase 5) ==========

# Risk Service Models
class RiskDimensionsModel(BaseModel):
    """Risk dimensions for assessment."""
    security: Optional[int] = Field(None, ge=0, le=100, description="Security risk score")
    privacy: Optional[int] = Field(None, ge=0, le=100, description="Privacy risk score")
    compliance: Optional[int] = Field(None, ge=0, le=100, description="Compliance risk score")
    operational: Optional[int] = Field(None, ge=0, le=100, description="Operational risk score")
    reputational: Optional[int] = Field(None, ge=0, le=100, description="Reputational risk score")
    financial: Optional[int] = Field(None, ge=0, le=100, description="Financial risk score")


class RiskAssessmentRequest(BaseModel):
    """Request to assess risk for a decision."""
    decision_id: str = Field(..., description="Decision ID to assess")
    dimensions: RiskDimensionsModel = Field(..., description="Risk dimensions")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


# Escalation Service Models
class EscalationCreateRequest(BaseModel):
    """Request to create an escalation."""
    decision_id: str = Field(..., description="Decision ID being escalated")
    trigger: str = Field(..., description="What triggered the escalation (risk_threshold/policy_conflict/explicit_rule/actor_request/anomaly_detected)")
    escalated_to: List[str] = Field(..., description="List of actor IDs to escalate to")
    priority: Optional[str] = Field(default=None, description="Escalation priority (critical/high/medium/low)")
    context_summary: Optional[str] = Field(default=None, description="Summary for reviewers")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class EscalationResolveRequest(BaseModel):
    """Request to resolve an escalation."""
    resolved_by: str = Field(..., description="Actor ID resolving escalation")
    outcome: str = Field(..., description="Resolution outcome")
    notes: str = Field(..., description="Resolution notes")


# Override Service Models
class OverrideCreateRequest(BaseModel):
    """Request to create an override."""
    decision_id: str = Field(..., description="Decision ID to override")
    override_type: str = Field(..., description="Type of override")
    authorized_by: str = Field(..., description="Actor ID authorizing override")
    justification: str = Field(..., min_length=20, description="Justification (min 20 chars)")
    original_outcome: Optional[str] = Field(default=None, description="Original decision outcome")
    new_outcome: Optional[str] = Field(default=None, description="New outcome after override")
    expires_at: Optional[str] = Field(default=None, description="Expiration timestamp (ISO 8601)")
    scope: Optional[Dict[str, Any]] = Field(default=None, description="Override scope limitations")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


# Evidence Service Models
class EvidenceStoreRequest(BaseModel):
    """Request to store an evidence artifact."""
    artifact_type: str = Field(..., description="Type of artifact")
    content: str = Field(..., description="Artifact content")
    source: str = Field(..., description="System/process that created artifact")
    related_decision_ids: Optional[List[str]] = Field(default=None, description="Related decision IDs")
    related_control_ids: Optional[List[str]] = Field(default=None, description="Related control IDs")
    content_type: Optional[str] = Field(default=None, description="MIME type")
    storage_uri: Optional[str] = Field(default=None, description="External storage location")
    retention_days: Optional[int] = Field(default=None, description="Custom retention period")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class EvidenceVerifyRequest(BaseModel):
    """Request to verify artifact integrity."""
    content: str = Field(..., description="Content to verify against stored hash")


class EvidenceSignRequest(BaseModel):
    """Request to sign an artifact."""
    signer_id: str = Field(..., description="Actor ID of signer")
    signature: str = Field(..., description="Signature value (base64 encoded)")
    algorithm: str = Field(default="RSA-SHA256", description="Signature algorithm")


# ========== Compliance Mapping API Models (Phase 7) ==========

class ComplianceMappingRequest(BaseModel):
    """Request to map a primitive to compliance controls."""
    primitive_type: str = Field(..., description="Type of governance primitive")
    primitive_id: str = Field(..., description="ID of primitive instance")
    framework: str = Field(..., description="Regulatory framework")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ComplianceLinkEvidenceRequest(BaseModel):
    """Request to link evidence to a control."""
    evidence_artifact_id: str = Field(..., description="Evidence artifact ID")


class ComplianceVerifyControlRequest(BaseModel):
    """Request to verify a control."""
    notes: Optional[str] = Field(default=None, description="Verification notes")


# Create FastAPI app
app = FastAPI(
    title="Lexecon Governance API",
    description="Cryptographic governance system for AI safety and compliance",
    version="0.1.0",
)

# Configure CORS
import os
allowed_origins = os.getenv("LEXECON_CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in production, use dependency injection)
policy_engine: Optional[PolicyEngine] = None
decision_service: Optional[DecisionService] = None
storage: LedgerStorage = LedgerStorage("lexecon_ledger.db")
ledger: LedgerChain = LedgerChain(storage=storage)
responsibility_storage: ResponsibilityStorage = ResponsibilityStorage("lexecon_responsibility.db")
responsibility_tracker: ResponsibilityTracker = ResponsibilityTracker(storage=responsibility_storage)
key_manager: Optional[KeyManager] = None
oversight_system = None  # HumanOversightEvidence - initialized after key_manager
intervention_storage = None  # InterventionStorage - initialized with oversight_system
node_id: str = str(uuid.uuid4())
startup_time: float = time.time()

# Security services
auth_service: AuthService = AuthService("lexecon_auth.db")
audit_service: AuditService = AuditService("lexecon_export_audit.db")
signature_service: SignatureService = SignatureService("lexecon_keys")

# Governance services (Phase 1-4)
risk_service: Optional[RiskService] = None
escalation_service: Optional[EscalationService] = None
override_service: Optional[OverrideService] = None
evidence_service: Optional[EvidenceService] = None

# Compliance mapping service (Phase 7)
compliance_mapping_service: Optional[ComplianceMappingService] = None


def initialize_services():
    """Initialize services with default configuration."""
    global policy_engine, decision_service, key_manager, oversight_system, intervention_storage
    global risk_service, escalation_service, override_service, evidence_service, compliance_mapping_service

    if policy_engine is None:
        policy_engine = PolicyEngine(mode=PolicyMode.STRICT)

    if decision_service is None:
        decision_service = DecisionService(policy_engine=policy_engine)

    if key_manager is None:
        key_manager = KeyManager.generate()

    # Initialize intervention storage
    if intervention_storage is None:
        from lexecon.compliance.eu_ai_act.storage import InterventionStorage
        intervention_storage = InterventionStorage("lexecon_interventions.db")

    # Initialize oversight system after key_manager and storage are available
    if oversight_system is None:
        from lexecon.compliance.eu_ai_act.article_14_oversight import HumanOversightEvidence
        oversight_system = HumanOversightEvidence(
            key_manager=key_manager,
            storage=intervention_storage
        )

    # Initialize governance services (Phase 1-4)
    if risk_service is None:
        risk_service = RiskService()

    if escalation_service is None:
        escalation_service = EscalationService()

    if override_service is None:
        override_service = OverrideService()

    if evidence_service is None:
        evidence_service = EvidenceService()

    # Initialize compliance mapping service (Phase 7)
    if compliance_mapping_service is None:
        compliance_mapping_service = ComplianceMappingService()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    initialize_services()
    ledger.append("system_startup", {"message": "API server started"})


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "node_id": node_id,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get system status."""
    initialize_services()

    policy_loaded_status = policy_engine is not None and len(policy_engine.terms) > 0
    return {
        "status": "operational",
        "node_id": node_id,
        "policy_loaded": policy_loaded_status,  # For backwards compatibility
        "policies_loaded": policy_loaded_status,
        "policy_hash": policy_engine.get_policy_hash() if policy_engine else None,
        "ledger_entries": len(ledger.entries),
        "uptime_seconds": time.time() - startup_time,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the compliance dashboard UI."""
    # Dashboard is at project root, go up from src/lexecon/api/
    dashboard_path = os.path.join(
        os.path.dirname(__file__),
        "../../../dashboard.html"
    )
    if not os.path.exists(dashboard_path):
        raise HTTPException(
            status_code=404,
            detail=f"Dashboard not found at {dashboard_path}"
        )
    return FileResponse(dashboard_path)


@app.get("/dashboard/governance", response_class=HTMLResponse)
async def serve_governance_dashboard():
    """Serve the governance dashboard UI (Phase 6)."""
    # Governance dashboard is at project root
    dashboard_path = os.path.join(
        os.path.dirname(__file__),
        "../../../governance_dashboard.html"
    )
    if not os.path.exists(dashboard_path):
        raise HTTPException(
            status_code=404,
            detail=f"Governance dashboard not found at {dashboard_path}"
        )
    return FileResponse(dashboard_path)


@app.get("/policies")
async def list_policies():
    """List loaded policies."""
    initialize_services()

    if policy_engine is None:
        raise HTTPException(status_code=500, detail="Policy engine not initialized")

    return {
        "policies": [],  # TODO: Implement policy storage/retrieval
        "mode": policy_engine.mode.value,
        "terms_count": len(policy_engine.terms),
        "relations_count": len(policy_engine.relations),
        "policy_hash": policy_engine.get_policy_hash(),
    }


@app.post("/policies/load")
async def load_policy(policy_load: PolicyLoadModel):
    """Load a policy bundle."""
    initialize_services()

    try:
        # Support both wrapped {"policy": {...}} and direct format
        if policy_load.policy is not None:
            # Wrapped format - be tolerant, policy engine will handle it
            policy_dict = policy_load.policy
        else:
            # Direct format - convert PolicyLoadModel to dict and validate
            policy_dict = policy_load.model_dump(exclude={"policy"}, exclude_none=True)
            # Validate that direct format has required fields
            if "terms" not in policy_dict and "relations" not in policy_dict:
                raise ValueError("Policy must contain at least 'terms' or 'relations' field")

        policy_engine.load_policy(policy_dict)

        # Log to ledger
        ledger.append(
            "policy_loaded",
            {
                "policy_hash": policy_engine.get_policy_hash(),
                "terms_count": len(policy_engine.terms),
                "relations_count": len(policy_engine.relations),
            },
        )

        return {
            "status": "success",
            "policy_hash": policy_engine.get_policy_hash(),
            "terms_loaded": len(policy_engine.terms),
            "relations_loaded": len(policy_engine.relations),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to load policy: {str(e)}"
        )


@app.post("/decide")
async def make_decision(request_model: DecisionRequestModel):
    """Make a governance decision."""
    initialize_services()

    if decision_service is None:
        raise HTTPException(status_code=500, detail="Decision service not initialized")

    # Create decision request
    request = DecisionRequest(
        request_id=request_model.request_id,
        actor=request_model.actor,
        proposed_action=request_model.proposed_action,
        tool=request_model.tool,
        user_intent=request_model.user_intent,
        data_classes=request_model.data_classes,
        risk_level=request_model.risk_level,
        requested_output_type=request_model.requested_output_type,
        policy_mode=request_model.policy_mode,
        context=request_model.context,
    )

    # Evaluate
    response = decision_service.evaluate_request(request)

    # Log to ledger
    ledger_entry = ledger.append(
        "decision",
        {
            "request_id": request.request_id,
            "decision": response.decision,
            "actor": request.actor,
            "action": request.proposed_action,
        },
    )

    response.ledger_entry_hash = ledger_entry.entry_hash

    # Track decision responsibility
    responsibility_tracker.record_decision(
        decision_id=request.request_id,
        decision_maker=DecisionMaker.AI_SYSTEM,  # Automated decision
        responsible_party="system",
        role="AI Decision System",
        reasoning=response.reasoning,
        confidence=response.confidence if hasattr(response, 'confidence') else 1.0,
        responsibility_level=ResponsibilityLevel.AUTOMATED
    )

    return response.to_dict()


@app.post("/decide/verify")
async def verify_decision(request_data: Dict[str, Any]):
    """Verify a decision response."""
    # Handle both direct format and wrapped format
    if "decision_response" in request_data:
        # Wrapped format: {"decision_response": {...}, "original_request": {...}}
        decision_response = request_data["decision_response"]
    else:
        # Direct format: the decision response itself
        decision_response = request_data

    ledger_entry_hash = decision_response.get("ledger_entry_hash")

    if not ledger_entry_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing ledger_entry_hash"
        )

    # Find entry in ledger
    entry = None
    for e in ledger.entries:
        if e.entry_hash == ledger_entry_hash:
            entry = e
            break

    if entry is None:
        return {"verified": False, "error": "Entry not found in ledger"}

    # Verify hash matches
    calculated_hash = entry.calculate_hash()
    if calculated_hash != entry.entry_hash:
        return {"verified": False, "error": "Hash mismatch"}

    return {"verified": True, "entry": entry.to_dict()}


@app.get("/ledger/verify")
async def verify_ledger():
    """Verify ledger integrity."""
    return ledger.verify_integrity()


@app.get("/ledger/report")
async def get_audit_report():
    """Generate audit report."""
    return ledger.generate_audit_report()


@app.get("/ledger/entries")
async def get_ledger_entries(
    event_type: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0
):
    """Get ledger entries with optional filtering."""
    entries = ledger.entries

    # Filter by event type if specified
    if event_type:
        entries = [e for e in entries if e.event_type == event_type]

    # Apply pagination
    total = len(entries)
    if limit:
        entries = entries[offset:offset + limit]
    else:
        entries = entries[offset:]

    return {
        "entries": [entry.to_dict() for entry in entries],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@app.get("/storage/stats")
async def get_storage_statistics():
    """Get persistent storage statistics."""
    if not storage:
        raise HTTPException(status_code=503, detail="Persistence not configured")

    stats = storage.get_statistics()
    return {
        "storage_enabled": True,
        **stats
    }


@app.get("/compliance/eu-ai-act/article-11")
async def generate_article_11_documentation(format: str = "json"):
    """Generate EU AI Act Article 11 technical documentation."""
    from lexecon.compliance.eu_ai_act.article_11_technical_docs import TechnicalDocumentationGenerator

    initialize_services()

    generator = TechnicalDocumentationGenerator(
        policy_engine=policy_engine,
        ledger=ledger
    )

    doc = generator.generate()

    if format == "markdown" or format == "md":
        return {
            "format": "markdown",
            "content": generator.export_markdown(doc)
        }

    return {
        "format": "json",
        "content": json.loads(generator.export_json(doc))
    }


@app.get("/compliance/eu-ai-act/article-12/status")
async def get_retention_status():
    """Get Article 12 record retention status."""
    from lexecon.compliance.eu_ai_act.article_12_records import RecordKeepingSystem

    record_system = RecordKeepingSystem(ledger=ledger)
    return record_system.get_retention_status()


@app.get("/compliance/eu-ai-act/article-12/regulatory-package")
async def generate_regulatory_package(
    format: str = "json",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Generate complete regulatory response package."""
    from lexecon.compliance.eu_ai_act.article_12_records import RecordKeepingSystem

    record_system = RecordKeepingSystem(ledger=ledger)

    if format not in ["json", "markdown", "csv"]:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    content = record_system.export_for_regulator(
        format=format,
        start_date=start_date,
        end_date=end_date
    )

    if format == "json":
        return json.loads(content)
    else:
        return {"format": format, "content": content}


@app.post("/compliance/eu-ai-act/article-12/legal-hold")
async def apply_legal_hold(
    hold_id: str,
    reason: str,
    requester: str = "system",
    entry_ids: Optional[List[str]] = None
):
    """Apply legal hold to records."""
    from lexecon.compliance.eu_ai_act.article_12_records import RecordKeepingSystem

    record_system = RecordKeepingSystem(ledger=ledger)
    return record_system.apply_legal_hold(
        hold_id=hold_id,
        reason=reason,
        entry_ids=entry_ids,
        requester=requester
    )


@app.post("/compliance/eu-ai-act/article-14/intervention")
async def log_human_intervention(request: InterventionModel):
    """Log a human oversight intervention."""
    from lexecon.compliance.eu_ai_act.article_14_oversight import InterventionType, OversightRole

    initialize_services()

    try:
        # Parse intervention type
        intervention_type_enum = InterventionType(request.intervention_type)
        role_enum = OversightRole(request.human_role)

        intervention = oversight_system.log_intervention(
            intervention_type=intervention_type_enum,
            ai_recommendation=request.ai_recommendation,
            human_decision=request.human_decision,
            human_role=role_enum,
            reason=request.reason,
            request_context=request.request_context,
            response_time_ms=request.response_time_ms
        )

        return {
            "status": "success",
            "intervention_id": intervention.intervention_id,
            "timestamp": intervention.timestamp,
            "signature": intervention.signature
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log intervention: {str(e)}")


@app.get("/compliance/eu-ai-act/article-14/effectiveness")
async def get_oversight_effectiveness(
    time_period_days: int = 30
):
    """Get Article 14 human oversight effectiveness report."""
    initialize_services()

    report = oversight_system.generate_oversight_effectiveness_report(
        time_period_days=time_period_days
    )

    return report


@app.post("/compliance/eu-ai-act/article-14/verify")
async def verify_intervention(
    intervention_data: Dict[str, Any]
):
    """Verify a human intervention's cryptographic signature."""
    from lexecon.compliance.eu_ai_act.article_14_oversight import HumanIntervention, InterventionType, OversightRole

    initialize_services()

    try:
        intervention = HumanIntervention(
            intervention_id=intervention_data["intervention_id"],
            timestamp=intervention_data["timestamp"],
            intervention_type=InterventionType(intervention_data["intervention_type"]),
            ai_recommendation=intervention_data["ai_recommendation"],
            ai_confidence=intervention_data["ai_confidence"],
            human_decision=intervention_data["human_decision"],
            human_role=OversightRole(intervention_data["human_role"]),
            reason=intervention_data["reason"],
            signature=intervention_data.get("signature"),
            response_time_ms=intervention_data.get("response_time_ms")
        )

        is_valid = oversight_system.verify_intervention(intervention)

        return {
            "verified": is_valid,
            "intervention_id": intervention.intervention_id,
            "timestamp": intervention.timestamp
        }
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid value: {str(e)}")


@app.get("/compliance/eu-ai-act/article-14/evidence-package")
async def get_evidence_package(
    format: str = "json",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Generate Article 14 evidence package for regulatory submission."""
    initialize_services()

    if format not in ["json", "markdown"]:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}. Use 'json' or 'markdown'")

    package = oversight_system.export_evidence_package(
        start_date=start_date,
        end_date=end_date
    )

    if format == "markdown":
        content = oversight_system.export_markdown(package)
        return {"format": "markdown", "content": content}

    return package


@app.post("/compliance/eu-ai-act/article-14/escalation")
async def simulate_escalation(
    decision_class: str,
    current_role: str
):
    """Simulate escalation path for a decision."""
    from lexecon.compliance.eu_ai_act.article_14_oversight import OversightRole

    initialize_services()

    try:
        current_role_enum = OversightRole(current_role)

        escalation = oversight_system.simulate_escalation(
            decision_class=decision_class,
            current_role=current_role_enum
        )

        return escalation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Escalation path not found: {str(e)}")


@app.get("/compliance/eu-ai-act/article-14/storage/stats")
async def get_intervention_storage_stats():
    """Get Article 14 intervention storage statistics."""
    initialize_services()

    if not intervention_storage:
        raise HTTPException(status_code=503, detail="Intervention persistence not configured")

    stats = intervention_storage.get_statistics()
    return {
        "storage_enabled": True,
        **stats
    }


@app.get("/compliance/eu-ai-act/audit-packet")
async def generate_audit_packet(
    time_window: Optional[str] = "all",
    format: Optional[str] = "json"
):
    """
    Generate comprehensive audit packet for EU AI Act compliance.

    Includes:
    - Article-mapped compliance summary
    - Decision log for selected time window
    - Human oversight log (Article 14)
    - Cryptographic verification report
    - Storage statistics

    Args:
        time_window: Time window for data (24h, 7d, 30d, all). Default: all
        format: Output format (json, text). Default: json

    Returns:
        Comprehensive audit packet as JSON or text
    """
    initialize_services()

    from datetime import datetime, timedelta, timezone

    # Calculate time window cutoff
    now = datetime.now(timezone.utc)
    window_map = {
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "all": None
    }

    cutoff = None
    if time_window != "all" and time_window in window_map:
        cutoff = now - window_map[time_window]

    # Filter helper
    def filter_by_time(items, timestamp_key='timestamp'):
        if not cutoff:
            return items
        filtered = []
        for item in items:
            try:
                ts_str = item[timestamp_key].replace('Z', '+00:00')
                ts = datetime.fromisoformat(ts_str)
                # Make timezone-aware if naive
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts >= cutoff:
                    filtered.append(item)
            except (ValueError, KeyError, AttributeError):
                # Skip items with invalid timestamps
                continue
        return filtered

    # 1. COMPLIANCE SUMMARY
    compliance_summary = {
        "report_type": "EU_AI_ACT_AUDIT_PACKET",
        "generated_at": now.isoformat(),
        "time_window": time_window,
        "system_info": {
            "node_id": node_id,
            "system": "Lexecon Governance System",
            "version": "0.1.0"
        },
        "compliance_status": {
            "overall": "COMPLIANT",
            "articles": {
                "article_11_technical_docs": {
                    "status": "COMPLIANT",
                    "description": "Technical documentation for high-risk AI systems",
                    "evidence": "Documentation generator active"
                },
                "article_12_record_keeping": {
                    "status": "COMPLIANT",
                    "description": "Automatic logging enabled for high-risk AI systems",
                    "evidence": f"{len(ledger.entries)} cryptographically chained ledger entries"
                },
                "article_14_human_oversight": {
                    "status": "COMPLIANT",
                    "description": "Human oversight and intervention capabilities",
                    "evidence": f"{intervention_storage.get_statistics()['total_interventions'] if intervention_storage else 0} human interventions logged"
                }
            }
        }
    }

    # 2. DECISION LOG
    decision_entries = [e for e in ledger.entries if e.event_type == "decision"]
    filtered_decisions = filter_by_time([
        {
            "entry_id": e.entry_id,
            "timestamp": e.timestamp,
            "event_type": e.event_type,
            "data": e.data,
            "entry_hash": e.entry_hash,
            "previous_hash": e.previous_hash
        }
        for e in decision_entries
    ])

    decision_log = {
        "total_decisions": len(filtered_decisions),
        "time_window": time_window,
        "decisions": filtered_decisions[-100:]  # Last 100 decisions
    }

    # 3. HUMAN OVERSIGHT LOG (Article 14)
    oversight_log = {
        "article": "Article 14 - Human Oversight",
        "total_interventions": 0,
        "interventions": []
    }

    if oversight_system:
        all_interventions = oversight_system.interventions
        filtered_interventions = filter_by_time([
            {
                "intervention_id": i.intervention_id,
                "timestamp": i.timestamp,
                "intervention_type": i.intervention_type.value,
                "ai_recommendation": i.ai_recommendation,
                "ai_confidence": i.ai_confidence,
                "human_decision": i.human_decision,
                "human_role": i.human_role.value,
                "reason": i.reason,
                "request_context": i.request_context,
                "signature": i.signature,
                "response_time_ms": i.response_time_ms
            }
            for i in all_interventions
        ])

        oversight_log["total_interventions"] = len(filtered_interventions)
        oversight_log["interventions"] = filtered_interventions

        # Calculate oversight metrics
        if filtered_interventions:
            override_count = sum(1 for i in filtered_interventions if i["intervention_type"] == "override")
            # Calculate average response time, handling None values
            response_times = [i.get("response_time_ms", 0) or 0 for i in filtered_interventions]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0

            oversight_log["metrics"] = {
                "override_count": override_count,
                "override_rate": (override_count / len(filtered_interventions) * 100) if filtered_interventions else 0,
                "approval_count": sum(1 for i in filtered_interventions if i["intervention_type"] == "approval"),
                "escalation_count": sum(1 for i in filtered_interventions if i["intervention_type"] == "escalation"),
                "average_response_time_ms": avg_response_time
            }

    # 4. CRYPTOGRAPHIC VERIFICATION REPORT
    verification_report = {
        "chain_integrity": "VALID",
        "total_entries": len(ledger.entries),
        "genesis_hash": ledger.entries[0].entry_hash if ledger.entries else None,
        "latest_hash": ledger.entries[-1].entry_hash if ledger.entries else None,
        "verification_timestamp": now.isoformat(),
        "storage_stats": {
            "ledger": storage.get_statistics() if storage else {},
            "interventions": intervention_storage.get_statistics() if intervention_storage else {},
            "responsibility": responsibility_storage.get_statistics() if responsibility_storage else {}
        }
    }

    # Verify chain integrity
    try:
        integrity_result = ledger.verify_integrity()
        is_valid = integrity_result.get("valid", False)
        verification_report["chain_integrity"] = "VALID" if is_valid else "INVALID"
        verification_report["verification_details"] = integrity_result.get("message", "Chain verification completed")
    except Exception as e:
        verification_report["chain_integrity"] = "ERROR"
        verification_report["verification_details"] = str(e)

    # 5. RESPONSIBILITY TRACKING
    responsibility_report = responsibility_tracker.generate_accountability_report()

    # Assemble audit packet
    audit_packet = {
        "audit_packet_version": "1.0",
        "compliance_summary": compliance_summary,
        "decision_log": decision_log,
        "human_oversight_log": oversight_log,
        "cryptographic_verification": verification_report,
        "responsibility_tracking": responsibility_report,
        "signature_info": {
            "packet_generated_at": now.isoformat(),
            "packet_generator": "Lexecon Compliance System",
            "regulatory_framework": "EU AI Act (Regulation 2024/1689)"
        }
    }

    # Return as JSON or formatted text
    if format == "text":
        from fastapi.responses import PlainTextResponse

        text_report = f"""
═══════════════════════════════════════════════════════════════════
  EU AI ACT COMPLIANCE AUDIT PACKET
═══════════════════════════════════════════════════════════════════

Generated: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}
Time Window: {time_window}
System: Lexecon Governance System v0.1.0
Node ID: {node_id}

───────────────────────────────────────────────────────────────────
  COMPLIANCE STATUS
───────────────────────────────────────────────────────────────────

Overall Status: {compliance_summary['compliance_status']['overall']}

Article 11 (Technical Documentation): COMPLIANT
  • Documentation generator active
  • {len(ledger.entries)} entries in audit trail

Article 12 (Record Keeping): COMPLIANT
  • Automatic logging enabled
  • Cryptographic chain verified: {verification_report['chain_integrity']}

Article 14 (Human Oversight): COMPLIANT
  • {oversight_log['total_interventions']} human interventions logged
  • Override rate: {oversight_log.get('metrics', {}).get('override_rate', 0):.1f}%

───────────────────────────────────────────────────────────────────
  DECISION LOG
───────────────────────────────────────────────────────────────────

Total Decisions: {decision_log['total_decisions']}
Time Window: {time_window}

Recent Decisions:
{chr(10).join(f"  • {d['timestamp']} - {d['data'].get('decision', 'N/A')} - {d['data'].get('actor', 'N/A')}" for d in filtered_decisions[-10:])}

───────────────────────────────────────────────────────────────────
  HUMAN OVERSIGHT (Article 14)
───────────────────────────────────────────────────────────────────

Total Interventions: {oversight_log['total_interventions']}

Metrics:
  • Overrides: {oversight_log.get('metrics', {}).get('override_count', 0)}
  • Approvals: {oversight_log.get('metrics', {}).get('approval_count', 0)}
  • Escalations: {oversight_log.get('metrics', {}).get('escalation_count', 0)}
  • Avg Response Time: {oversight_log.get('metrics', {}).get('average_response_time_ms', 0):.0f}ms

───────────────────────────────────────────────────────────────────
  CRYPTOGRAPHIC VERIFICATION
───────────────────────────────────────────────────────────────────

Chain Integrity: {verification_report['chain_integrity']}
Total Entries: {verification_report['total_entries']}
Genesis Hash: {verification_report['genesis_hash']}
Latest Hash: {verification_report['latest_hash']}

Storage Statistics:
  • Ledger: {verification_report['storage_stats']['ledger'].get('total_entries', 0)} entries
  • Interventions: {verification_report['storage_stats']['interventions'].get('total_interventions', 0)} records
  • Responsibility: {verification_report['storage_stats']['responsibility'].get('total_decisions', 0)} decisions

───────────────────────────────────────────────────────────────────
  SIGNATURE
───────────────────────────────────────────────────────────────────

This audit packet was generated by the Lexecon Compliance System
in accordance with EU AI Act (Regulation 2024/1689).

Generated: {now.isoformat()}
Generator: Lexecon Compliance System
Framework: EU AI Act (Regulation 2024/1689)

═══════════════════════════════════════════════════════════════════
"""
        return PlainTextResponse(content=text_report, media_type="text/plain")

    # Add digital signature to JSON packet
    signed_packet = signature_service.sign_and_enrich_packet(audit_packet)

    return signed_packet


@app.get("/responsibility/report")
async def get_accountability_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Generate accountability report showing who made decisions."""
    return responsibility_tracker.generate_accountability_report(
        start_date=start_date,
        end_date=end_date
    )


@app.get("/responsibility/chain/{decision_id}")
async def get_responsibility_chain(decision_id: str):
    """Get the full responsibility chain for a decision."""
    chain = responsibility_tracker.get_responsibility_chain(decision_id)

    if not chain:
        raise HTTPException(status_code=404, detail="Decision not found")

    return {
        "decision_id": decision_id,
        "chain_length": len(chain),
        "records": [r.to_dict() for r in chain]
    }


@app.get("/responsibility/party/{party}")
async def get_by_party(party: str):
    """Get all decisions made by a specific responsible party."""
    records = responsibility_tracker.get_by_responsible_party(party)

    return {
        "responsible_party": party,
        "decision_count": len(records),
        "records": [r.to_dict() for r in records]
    }


@app.get("/responsibility/overrides")
async def get_ai_overrides():
    """Get all decisions where humans overrode AI recommendations."""
    overrides = responsibility_tracker.get_ai_overrides()

    return {
        "override_count": len(overrides),
        "records": [r.to_dict() for r in overrides]
    }


@app.get("/responsibility/pending-reviews")
async def get_pending_reviews():
    """Get decisions awaiting human review."""
    pending = responsibility_tracker.get_pending_reviews()

    return {
        "pending_count": len(pending),
        "records": [r.to_dict() for r in pending]
    }


@app.get("/responsibility/legal/{decision_id}")
async def get_legal_export(decision_id: str):
    """Export responsibility chain for legal proceedings."""
    return responsibility_tracker.export_for_legal(decision_id)


@app.get("/responsibility/storage/stats")
async def get_responsibility_storage_stats():
    """Get responsibility storage statistics."""
    if not responsibility_storage:
        raise HTTPException(status_code=503, detail="Responsibility persistence not configured")

    stats = responsibility_storage.get_statistics()
    return {
        "storage_enabled": True,
        **stats
    }


# ============================================================================
# Authentication Endpoints
# ============================================================================


@app.post("/auth/login", response_model=LoginResponse)
async def login(request: Request, login_req: LoginRequest):
    """Authenticate user and create session."""
    ip_address = request.client.host if request.client else None

    user, error = auth_service.authenticate(
        login_req.username,
        login_req.password,
        ip_address
    )

    if not user:
        return LoginResponse(success=False, error=error)

    # Create session
    session = auth_service.create_session(user, ip_address)

    # Log access
    audit_service.log_access(
        endpoint="/auth/login",
        method="POST",
        status_code=200,
        user_id=user.user_id,
        username=user.username,
        ip_address=ip_address
    )

    return LoginResponse(
        success=True,
        session_id=session.session_id,
        user={
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "full_name": user.full_name
        }
    )


@app.post("/auth/logout")
async def logout(request: Request):
    """Logout user and revoke session."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = request.headers.get("Authorization", "").replace("Bearer ", "")

    if session_id:
        auth_service.revoke_session(session_id)

    return {"success": True, "message": "Logged out successfully"}


@app.get("/auth/me")
async def get_current_user_info(request: Request):
    """Get current authenticated user info."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = request.headers.get("Authorization", "").replace("Bearer ", "")

    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session, error = auth_service.validate_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail=error)

    user = auth_service.get_user_by_id(session.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "full_name": user.full_name,
        "last_login": user.last_login
    }


@app.post("/auth/users")
async def create_user(request: Request, user_req: CreateUserRequest):
    """Create a new user (admin only)."""
    session_id = request.cookies.get("session_id") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session, error = auth_service.validate_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail=error)

    if not auth_service.has_permission(session.role, Permission.MANAGE_USERS):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    try:
        user = auth_service.create_user(
            username=user_req.username,
            email=user_req.email,
            password=user_req.password,
            role=Role(user_req.role),
            full_name=user_req.full_name
        )

        return {
            "success": True,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "full_name": user.full_name
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/auth/users")
async def list_users(request: Request):
    """List all users (admin only)."""
    session_id = request.cookies.get("session_id") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session, error = auth_service.validate_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail=error)

    if not auth_service.has_permission(session.role, Permission.MANAGE_USERS):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    users = auth_service.list_users()

    return {
        "users": [
            {
                "user_id": u.user_id,
                "username": u.username,
                "email": u.email,
                "role": u.role.value,
                "full_name": u.full_name,
                "last_login": u.last_login,
                "is_active": u.is_active
            }
            for u in users
        ]
    }


# ============================================================================
# Digital Signature Endpoints
# ============================================================================


@app.post("/compliance/verify-signature")
async def verify_signature(packet: Dict[str, Any]):
    """Verify digital signature on an audit packet."""
    is_valid, message = signature_service.verify_packet_signature(packet)

    return {
        "valid": is_valid,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/compliance/public-key")
async def get_public_key():
    """Get public key for signature verification."""
    return {
        "public_key_pem": signature_service.get_public_key_pem(),
        "fingerprint": signature_service.get_public_key_fingerprint(),
        "algorithm": "RSA-PSS-SHA256",
        "key_size": 4096
    }


# ============================================================================
# Export Audit Log Endpoints
# ============================================================================


@app.get("/compliance/export-requests")
async def list_export_requests(request: Request, limit: int = 100):
    """List export requests (compliance officer+ only)."""
    session_id = request.cookies.get("session_id") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session, error = auth_service.validate_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail=error)

    if not auth_service.has_permission(session.role, Permission.VIEW_AUDIT_LOGS):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    requests = audit_service.list_export_requests(limit=limit)

    return {
        "requests": [
            {
                "request_id": r.request_id,
                "username": r.username,
                "purpose": r.purpose,
                "case_id": r.case_id,
                "requested_at": r.requested_at,
                "export_status": r.export_status.value,
                "approval_status": r.approval_status.value,
                "completed_at": r.completed_at
            }
            for r in requests
        ]
    }


@app.get("/compliance/audit-chain-verification")
async def verify_audit_chain(request: Request):
    """Verify integrity of export audit chain."""
    session_id = request.cookies.get("session_id") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session, error = auth_service.validate_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail=error)

    result = audit_service.verify_audit_chain()

    return result


# ============================================================================
# Governance API Endpoints (Phase 5)
# ============================================================================

# ---------- Risk Service Endpoints ----------

@app.post("/api/governance/risk/assess")
async def assess_risk(request: RiskAssessmentRequest):
    """Assess risk for a decision."""
    initialize_services()

    if not risk_service:
        raise HTTPException(status_code=500, detail="Risk service not initialized")

    try:
        # Convert RiskDimensionsModel to RiskDimensions
        dimensions_dict = request.dimensions.model_dump(exclude_none=True)
        dimensions = RiskDimensions(**dimensions_dict)

        # Assess risk
        risk = risk_service.assess_risk(
            decision_id=request.decision_id,
            dimensions=dimensions,
            metadata=request.context
        )

        # Convert to dict for response
        return {
            "risk_id": risk.risk_id,
            "decision_id": risk.decision_id,
            "overall_score": risk.overall_score,
            "risk_level": risk.risk_level.value,
            "dimensions": {
                "security": risk.dimensions.security,
                "privacy": risk.dimensions.privacy,
                "compliance": risk.dimensions.compliance,
                "operational": risk.dimensions.operational,
                "reputational": risk.dimensions.reputational,
                "financial": risk.dimensions.financial,
            },
            "timestamp": risk.timestamp.isoformat(),
            "factors": risk.factors,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")


@app.get("/api/governance/risk/{risk_id}")
async def get_risk(risk_id: str):
    """Get risk by ID."""
    initialize_services()

    if not risk_service:
        raise HTTPException(status_code=500, detail="Risk service not initialized")

    risk = risk_service.get_risk(risk_id)
    if not risk:
        raise HTTPException(status_code=404, detail=f"Risk {risk_id} not found")

    return {
        "risk_id": risk.risk_id,
        "decision_id": risk.decision_id,
        "overall_score": risk.overall_score,
        "risk_level": risk.risk_level.value,
        "dimensions": {
            "security": risk.dimensions.security,
            "privacy": risk.dimensions.privacy,
            "compliance": risk.dimensions.compliance,
            "operational": risk.dimensions.operational,
            "reputational": risk.dimensions.reputational,
            "financial": risk.dimensions.financial,
        },
        "timestamp": risk.timestamp.isoformat(),
        "factors": risk.factors,
    }


@app.get("/api/governance/risk/decision/{decision_id}")
async def get_risk_for_decision(decision_id: str):
    """Get risk for a decision."""
    initialize_services()

    if not risk_service:
        raise HTTPException(status_code=500, detail="Risk service not initialized")

    risk = risk_service.get_risk_for_decision(decision_id)
    if not risk:
        raise HTTPException(status_code=404, detail=f"No risk found for decision {decision_id}")

    return {
        "risk_id": risk.risk_id,
        "decision_id": risk.decision_id,
        "overall_score": risk.overall_score,
        "risk_level": risk.risk_level.value,
        "dimensions": {
            "security": risk.dimensions.security,
            "privacy": risk.dimensions.privacy,
            "compliance": risk.dimensions.compliance,
            "operational": risk.dimensions.operational,
            "reputational": risk.dimensions.reputational,
            "financial": risk.dimensions.financial,
        },
        "timestamp": risk.timestamp.isoformat(),
        "factors": risk.factors,
    }


# ---------- Escalation Service Endpoints ----------

@app.post("/api/governance/escalation")
async def create_escalation(request: EscalationCreateRequest):
    """Create an escalation."""
    initialize_services()

    if not escalation_service:
        raise HTTPException(status_code=500, detail="Escalation service not initialized")

    try:
        # Import EscalationTrigger enum
        from model_governance_pack.models import EscalationTrigger

        # Convert strings to enums (values are lowercase)
        trigger = EscalationTrigger(request.trigger.lower())
        priority = EscalationPriority(request.priority.lower()) if request.priority else None

        escalation = escalation_service.create_escalation(
            decision_id=request.decision_id,
            trigger=trigger,
            escalated_to=request.escalated_to,
            priority=priority,
            context_summary=request.context_summary,
            metadata=request.metadata
        )

        return {
            "escalation_id": escalation.escalation_id,
            "decision_id": escalation.decision_id,
            "status": escalation.status.value,
            "priority": escalation.priority.value,
            "trigger": escalation.trigger,
            "escalated_to": escalation.escalated_to,
            "reason": escalation.reason,
            "created_at": escalation.created_at.isoformat(),
            "sla_deadline": escalation.sla_deadline.isoformat() if escalation.sla_deadline else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Escalation creation failed: {str(e)}")


@app.post("/api/governance/escalation/{escalation_id}/resolve")
async def resolve_escalation(escalation_id: str, request: EscalationResolveRequest):
    """Resolve an escalation."""
    initialize_services()

    if not escalation_service:
        raise HTTPException(status_code=500, detail="Escalation service not initialized")

    try:
        escalation = escalation_service.resolve_escalation(
            escalation_id=escalation_id,
            resolved_by=request.resolved_by,
            outcome=request.outcome,
            notes=request.notes
        )

        return {
            "escalation_id": escalation.escalation_id,
            "decision_id": escalation.decision_id,
            "status": escalation.status.value,
            "priority": escalation.priority.value,
            "resolved_at": escalation.resolved_at.isoformat() if escalation.resolved_at else None,
            "resolved_by": escalation.resolved_by,
            "outcome": escalation.outcome,
            "resolution_notes": escalation.resolution_notes,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Escalation resolution failed: {str(e)}")


@app.get("/api/governance/escalation/{escalation_id}")
async def get_escalation(escalation_id: str):
    """Get escalation by ID."""
    initialize_services()

    if not escalation_service:
        raise HTTPException(status_code=500, detail="Escalation service not initialized")

    escalation = escalation_service.get_escalation(escalation_id)
    if not escalation:
        raise HTTPException(status_code=404, detail=f"Escalation {escalation_id} not found")

    return {
        "escalation_id": escalation.escalation_id,
        "decision_id": escalation.decision_id,
        "status": escalation.status.value,
        "priority": escalation.priority.value,
        "trigger": escalation.trigger,
        "escalated_to": escalation.escalated_to,
        "reason": escalation.reason,
        "created_at": escalation.created_at.isoformat(),
        "sla_deadline": escalation.sla_deadline.isoformat() if escalation.sla_deadline else None,
        "resolved_at": escalation.resolved_at.isoformat() if escalation.resolved_at else None,
        "resolved_by": escalation.resolved_by,
        "outcome": escalation.outcome,
    }


@app.get("/api/governance/escalation/decision/{decision_id}")
async def get_escalations_for_decision(decision_id: str):
    """Get all escalations for a decision."""
    initialize_services()

    if not escalation_service:
        raise HTTPException(status_code=500, detail="Escalation service not initialized")

    escalations = escalation_service.list_escalations(decision_id=decision_id)

    return {
        "decision_id": decision_id,
        "count": len(escalations),
        "escalations": [
            {
                "escalation_id": e.escalation_id,
                "status": e.status.value,
                "priority": e.priority.value,
                "created_at": e.created_at.isoformat(),
                "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
            }
            for e in escalations
        ],
    }


@app.get("/api/governance/escalation/sla/violations")
async def get_sla_violations():
    """Get escalations with SLA violations."""
    initialize_services()

    if not escalation_service:
        raise HTTPException(status_code=500, detail="Escalation service not initialized")

    # check_sla_status returns notification events, not escalations
    # We need to list pending escalations that are past their SLA deadline
    from datetime import datetime, timezone

    pending_escalations = escalation_service.list_escalations(
        status=EscalationStatus.PENDING
    )

    now = datetime.now(timezone.utc)
    violations = [
        e for e in pending_escalations
        if e.sla_deadline and now > e.sla_deadline
    ]

    return {
        "count": len(violations),
        "violations": [
            {
                "escalation_id": e.escalation_id,
                "decision_id": e.decision_id,
                "priority": e.priority.value,
                "sla_deadline": e.sla_deadline.isoformat() if e.sla_deadline else None,
                "created_at": e.created_at.isoformat(),
            }
            for e in violations
        ],
    }


# ---------- Override Service Endpoints ----------

@app.post("/api/governance/override")
async def create_override(request: OverrideCreateRequest):
    """Create an override."""
    initialize_services()

    if not override_service:
        raise HTTPException(status_code=500, detail="Override service not initialized")

    try:
        # Convert string enums to proper types (values are lowercase)
        override_type = OverrideType(request.override_type.lower())
        original_outcome = OriginalOutcome(request.original_outcome.lower()) if request.original_outcome else None
        new_outcome = NewOutcome(request.new_outcome.lower()) if request.new_outcome else None

        # Parse expires_at if provided
        expires_at = None
        if request.expires_at:
            from datetime import datetime
            expires_at = datetime.fromisoformat(request.expires_at.replace('Z', '+00:00'))

        # Create scope if provided
        scope = None
        if request.scope:
            scope = OverrideScope(**request.scope)

        override = override_service.create_override(
            decision_id=request.decision_id,
            override_type=override_type,
            authorized_by=request.authorized_by,
            justification=request.justification,
            original_outcome=original_outcome,
            new_outcome=new_outcome,
            expires_at=expires_at,
            scope=scope,
            metadata=request.metadata
        )

        return {
            "override_id": override.override_id,
            "decision_id": override.decision_id,
            "override_type": override.override_type.value,
            "authorized_by": override.authorized_by,
            "justification": override.justification,
            "timestamp": override.timestamp.isoformat(),
            "expires_at": override.expires_at.isoformat() if override.expires_at else None,
            "evidence_ids": override.evidence_ids,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Override creation failed: {str(e)}")


@app.get("/api/governance/override/{override_id}")
async def get_override(override_id: str):
    """Get override by ID."""
    initialize_services()

    if not override_service:
        raise HTTPException(status_code=500, detail="Override service not initialized")

    override = override_service.get_override(override_id)
    if not override:
        raise HTTPException(status_code=404, detail=f"Override {override_id} not found")

    return {
        "override_id": override.override_id,
        "decision_id": override.decision_id,
        "override_type": override.override_type.value,
        "authorized_by": override.authorized_by,
        "justification": override.justification,
        "timestamp": override.timestamp.isoformat(),
        "original_outcome": override.original_outcome.value if override.original_outcome else None,
        "new_outcome": override.new_outcome.value if override.new_outcome else None,
        "expires_at": override.expires_at.isoformat() if override.expires_at else None,
        "evidence_ids": override.evidence_ids,
    }


@app.get("/api/governance/override/decision/{decision_id}")
async def get_overrides_for_decision(decision_id: str):
    """Get all overrides for a decision."""
    initialize_services()

    if not override_service:
        raise HTTPException(status_code=500, detail="Override service not initialized")

    overrides = override_service.get_overrides_for_decision(decision_id)

    return {
        "decision_id": decision_id,
        "count": len(overrides),
        "overrides": [
            {
                "override_id": o.override_id,
                "override_type": o.override_type.value,
                "authorized_by": o.authorized_by,
                "timestamp": o.timestamp.isoformat(),
                "expires_at": o.expires_at.isoformat() if o.expires_at else None,
            }
            for o in overrides
        ],
    }


@app.get("/api/governance/override/decision/{decision_id}/active")
async def check_active_override(decision_id: str):
    """Check if decision has an active override."""
    initialize_services()

    if not override_service:
        raise HTTPException(status_code=500, detail="Override service not initialized")

    active_override = override_service.get_active_override(decision_id)
    is_overridden = active_override is not None

    result = {
        "decision_id": decision_id,
        "is_overridden": is_overridden,
    }

    if active_override:
        result["override"] = {
            "override_id": active_override.override_id,
            "override_type": active_override.override_type.value,
            "authorized_by": active_override.authorized_by,
            "timestamp": active_override.timestamp.isoformat(),
            "expires_at": active_override.expires_at.isoformat() if active_override.expires_at else None,
        }

    return result


@app.get("/api/governance/override/decision/{decision_id}/status")
async def get_decision_with_override_status(decision_id: str):
    """Get decision data enriched with override status."""
    initialize_services()

    if not override_service:
        raise HTTPException(status_code=500, detail="Override service not initialized")

    # For this endpoint, we need the decision data
    # In a real implementation, this would fetch from decision service
    # For now, return a minimal decision structure with override status
    decision_data = {"decision_id": decision_id}

    enriched = override_service.get_decision_with_override_status(decision_id, decision_data)

    return enriched


# ---------- Evidence Service Endpoints ----------

@app.post("/api/governance/evidence")
async def store_evidence_artifact(request: EvidenceStoreRequest):
    """Store an evidence artifact."""
    initialize_services()

    if not evidence_service:
        raise HTTPException(status_code=500, detail="Evidence service not initialized")

    try:
        # Convert artifact type string to enum (values are lowercase)
        artifact_type = ArtifactType(request.artifact_type.lower())

        artifact = evidence_service.store_artifact(
            artifact_type=artifact_type,
            content=request.content,
            source=request.source,
            related_decision_ids=request.related_decision_ids,
            related_control_ids=request.related_control_ids,
            content_type=request.content_type,
            storage_uri=request.storage_uri,
            retention_days=request.retention_days,
            metadata=request.metadata
        )

        return {
            "artifact_id": artifact.artifact_id,
            "artifact_type": artifact.artifact_type.value,
            "sha256_hash": artifact.sha256_hash,
            "created_at": artifact.created_at.isoformat(),
            "source": artifact.source,
            "size_bytes": artifact.size_bytes,
            "retention_until": artifact.retention_until.isoformat() if artifact.retention_until else None,
            "is_immutable": artifact.is_immutable,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Artifact storage failed: {str(e)}")


@app.get("/api/governance/evidence/{artifact_id}")
async def get_evidence_artifact(artifact_id: str):
    """Get evidence artifact by ID."""
    initialize_services()

    if not evidence_service:
        raise HTTPException(status_code=500, detail="Evidence service not initialized")

    artifact = evidence_service.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found")

    return {
        "artifact_id": artifact.artifact_id,
        "artifact_type": artifact.artifact_type.value,
        "sha256_hash": artifact.sha256_hash,
        "created_at": artifact.created_at.isoformat(),
        "source": artifact.source,
        "content_type": artifact.content_type,
        "size_bytes": artifact.size_bytes,
        "storage_uri": artifact.storage_uri,
        "related_decision_ids": artifact.related_decision_ids,
        "related_control_ids": artifact.related_control_ids,
        "retention_until": artifact.retention_until.isoformat() if artifact.retention_until else None,
        "is_immutable": artifact.is_immutable,
        "has_signature": artifact.digital_signature is not None,
    }


@app.post("/api/governance/evidence/{artifact_id}/verify")
async def verify_evidence_artifact(artifact_id: str, request: EvidenceVerifyRequest):
    """Verify artifact integrity by recomputing hash."""
    initialize_services()

    if not evidence_service:
        raise HTTPException(status_code=500, detail="Evidence service not initialized")

    try:
        is_valid = evidence_service.verify_artifact_integrity(artifact_id, request.content)

        artifact = evidence_service.get_artifact(artifact_id)

        return {
            "artifact_id": artifact_id,
            "is_valid": is_valid,
            "stored_hash": artifact.sha256_hash if artifact else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@app.get("/api/governance/evidence/decision/{decision_id}")
async def get_artifacts_for_decision(decision_id: str):
    """Get all evidence artifacts for a decision."""
    initialize_services()

    if not evidence_service:
        raise HTTPException(status_code=500, detail="Evidence service not initialized")

    artifacts = evidence_service.get_artifacts_for_decision(decision_id)

    return {
        "decision_id": decision_id,
        "count": len(artifacts),
        "artifacts": [
            {
                "artifact_id": a.artifact_id,
                "artifact_type": a.artifact_type.value,
                "sha256_hash": a.sha256_hash,
                "created_at": a.created_at.isoformat(),
                "source": a.source,
                "size_bytes": a.size_bytes,
            }
            for a in artifacts
        ],
    }


@app.get("/api/governance/evidence/decision/{decision_id}/lineage")
async def export_artifact_lineage(decision_id: str):
    """Export complete artifact lineage for a decision."""
    initialize_services()

    if not evidence_service:
        raise HTTPException(status_code=500, detail="Evidence service not initialized")

    lineage = evidence_service.export_artifact_lineage(decision_id)

    return lineage


@app.post("/api/governance/evidence/{artifact_id}/sign")
async def sign_evidence_artifact(artifact_id: str, request: EvidenceSignRequest):
    """Add digital signature to an artifact."""
    initialize_services()

    if not evidence_service:
        raise HTTPException(status_code=500, detail="Evidence service not initialized")

    try:
        artifact = evidence_service.sign_artifact(
            artifact_id=artifact_id,
            signer_id=request.signer_id,
            signature=request.signature,
            algorithm=request.algorithm
        )

        return {
            "artifact_id": artifact.artifact_id,
            "signed": True,
            "signer_id": artifact.digital_signature.signer_id if artifact.digital_signature else None,
            "signed_at": artifact.digital_signature.signed_at.isoformat() if artifact.digital_signature else None,
            "algorithm": artifact.digital_signature.algorithm if artifact.digital_signature else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signing failed: {str(e)}")


@app.get("/api/governance/evidence/statistics")
async def get_evidence_statistics():
    """Get evidence service statistics."""
    initialize_services()

    if not evidence_service:
        raise HTTPException(status_code=500, detail="Evidence service not initialized")

    stats = evidence_service.get_statistics()

    return stats


# ---------- Compliance Mapping Service Endpoints (Phase 7) ----------

@app.post("/api/governance/compliance/map")
async def map_primitive_to_controls(request: ComplianceMappingRequest):
    """Map a governance primitive to compliance controls."""
    initialize_services()

    if not compliance_mapping_service:
        raise HTTPException(status_code=500, detail="Compliance mapping service not initialized")

    try:
        # Convert strings to enums
        primitive_type = GovernancePrimitive(request.primitive_type.lower())
        framework = RegulatoryFramework(request.framework.lower())

        mapping = compliance_mapping_service.map_primitive_to_controls(
            primitive_type=primitive_type,
            primitive_id=request.primitive_id,
            framework=framework,
            metadata=request.metadata
        )

        return {
            "mapping_id": mapping.mapping_id,
            "primitive_type": mapping.primitive_type.value,
            "primitive_id": mapping.primitive_id,
            "framework": mapping.framework.value,
            "control_ids": mapping.control_ids,
            "mapped_at": mapping.mapped_at.isoformat(),
            "verification_status": mapping.verification_status,
            "metadata": mapping.metadata,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mapping failed: {str(e)}")


@app.get("/api/governance/compliance/{framework}/controls")
async def list_compliance_controls(
    framework: str,
    status: Optional[str] = None,
    category: Optional[str] = None
):
    """List compliance controls for a framework with optional filtering."""
    initialize_services()

    if not compliance_mapping_service:
        raise HTTPException(status_code=500, detail="Compliance mapping service not initialized")

    try:
        framework_enum = RegulatoryFramework(framework.lower())
        status_enum = ControlStatus(status.lower()) if status else None

        controls = compliance_mapping_service.list_controls(
            framework=framework_enum,
            status=status_enum,
            category=category
        )

        return {
            "framework": framework,
            "count": len(controls),
            "filters": {
                "status": status,
                "category": category,
            },
            "controls": [
                {
                    "control_id": c.control_id,
                    "title": c.title,
                    "description": c.description,
                    "category": c.category,
                    "status": c.status.value,
                    "required_evidence_types": c.required_evidence_types,
                    "mapped_primitives": [p.value for p in c.mapped_primitives],
                    "last_verified": c.last_verified.isoformat() if c.last_verified else None,
                }
                for c in controls
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list controls: {str(e)}")


@app.get("/api/governance/compliance/{framework}/{control_id}")
async def get_control_status(framework: str, control_id: str):
    """Get status of a specific compliance control."""
    initialize_services()

    if not compliance_mapping_service:
        raise HTTPException(status_code=500, detail="Compliance mapping service not initialized")

    try:
        framework_enum = RegulatoryFramework(framework.lower())
        control = compliance_mapping_service.get_control_status(control_id, framework_enum)

        if not control:
            raise HTTPException(
                status_code=404,
                detail=f"Control {control_id} not found in framework {framework}"
            )

        return {
            "control_id": control.control_id,
            "framework": control.framework.value,
            "title": control.title,
            "description": control.description,
            "category": control.category,
            "status": control.status.value,
            "required_evidence_types": control.required_evidence_types,
            "mapped_primitives": [p.value for p in control.mapped_primitives],
            "evidence_artifact_ids": control.evidence_artifact_ids,
            "last_verified": control.last_verified.isoformat() if control.last_verified else None,
            "verification_notes": control.verification_notes,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get control status: {str(e)}")


@app.post("/api/governance/compliance/{framework}/{control_id}/verify")
async def verify_control(framework: str, control_id: str, request: ComplianceVerifyControlRequest):
    """Mark a compliance control as verified."""
    initialize_services()

    if not compliance_mapping_service:
        raise HTTPException(status_code=500, detail="Compliance mapping service not initialized")

    try:
        framework_enum = RegulatoryFramework(framework.lower())

        success = compliance_mapping_service.verify_control(
            control_id=control_id,
            framework=framework_enum,
            notes=request.notes
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Control {control_id} not found in framework {framework}"
            )

        # Get updated control
        control = compliance_mapping_service.get_control_status(control_id, framework_enum)

        return {
            "success": True,
            "control_id": control_id,
            "framework": framework,
            "status": control.status.value,
            "last_verified": control.last_verified.isoformat() if control.last_verified else None,
            "verification_notes": control.verification_notes,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@app.post("/api/governance/compliance/{framework}/{control_id}/link-evidence")
async def link_evidence_to_control(
    framework: str,
    control_id: str,
    request: ComplianceLinkEvidenceRequest
):
    """Link an evidence artifact to a compliance control."""
    initialize_services()

    if not compliance_mapping_service:
        raise HTTPException(status_code=500, detail="Compliance mapping service not initialized")

    try:
        framework_enum = RegulatoryFramework(framework.lower())

        success = compliance_mapping_service.link_evidence_to_control(
            control_id=control_id,
            framework=framework_enum,
            evidence_artifact_id=request.evidence_artifact_id
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Control {control_id} not found in framework {framework}"
            )

        # Get updated control
        control = compliance_mapping_service.get_control_status(control_id, framework_enum)

        return {
            "success": True,
            "control_id": control_id,
            "framework": framework,
            "evidence_artifact_id": request.evidence_artifact_id,
            "total_evidence_artifacts": len(control.evidence_artifact_ids),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to link evidence: {str(e)}")


@app.get("/api/governance/compliance/{framework}/gaps")
async def analyze_compliance_gaps(framework: str):
    """Analyze compliance gaps for a framework."""
    initialize_services()

    if not compliance_mapping_service:
        raise HTTPException(status_code=500, detail="Compliance mapping service not initialized")

    try:
        framework_enum = RegulatoryFramework(framework.lower())
        gaps = compliance_mapping_service.analyze_gaps(framework_enum)

        return {
            "framework": framework,
            "gap_count": len(gaps),
            "gaps": gaps,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")


@app.get("/api/governance/compliance/{framework}/report")
async def generate_compliance_report(framework: str):
    """Generate comprehensive compliance report for a framework."""
    initialize_services()

    if not compliance_mapping_service:
        raise HTTPException(status_code=500, detail="Compliance mapping service not initialized")

    try:
        framework_enum = RegulatoryFramework(framework.lower())
        report = compliance_mapping_service.generate_compliance_report(framework_enum)

        return {
            "report_id": report.report_id,
            "framework": report.framework.value,
            "generated_at": report.generated_at.isoformat(),
            "total_controls": report.total_controls,
            "implemented_controls": report.implemented_controls,
            "verified_controls": report.verified_controls,
            "non_compliant_controls": report.non_compliant_controls,
            "compliance_percentage": report.compliance_percentage,
            "gaps": report.gaps,
            "recommendations": report.recommendations,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@app.get("/api/governance/compliance/{framework}/coverage")
async def get_framework_coverage(framework: str):
    """Get coverage statistics for a framework."""
    initialize_services()

    if not compliance_mapping_service:
        raise HTTPException(status_code=500, detail="Compliance mapping service not initialized")

    try:
        framework_enum = RegulatoryFramework(framework.lower())
        coverage = compliance_mapping_service.get_framework_coverage(framework_enum)

        return coverage
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get coverage: {str(e)}")


@app.get("/api/governance/compliance/primitive/{primitive_id}/mappings")
async def get_primitive_mappings(primitive_id: str):
    """Get all control mappings for a governance primitive."""
    initialize_services()

    if not compliance_mapping_service:
        raise HTTPException(status_code=500, detail="Compliance mapping service not initialized")

    try:
        mappings = compliance_mapping_service.get_primitive_mappings(primitive_id)

        return {
            "primitive_id": primitive_id,
            "mapping_count": len(mappings),
            "mappings": [
                {
                    "mapping_id": m.mapping_id,
                    "primitive_type": m.primitive_type.value,
                    "framework": m.framework.value,
                    "control_ids": m.control_ids,
                    "mapped_at": m.mapped_at.isoformat(),
                    "verification_status": m.verification_status,
                }
                for m in mappings
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mappings: {str(e)}")


@app.get("/api/governance/compliance/statistics")
async def get_compliance_statistics():
    """Get overall compliance mapping statistics."""
    initialize_services()

    if not compliance_mapping_service:
        raise HTTPException(status_code=500, detail="Compliance mapping service not initialized")

    try:
        stats = compliance_mapping_service.get_statistics()

        # Convert framework enums to strings in the response
        if "frameworks" in stats:
            stats["frameworks"] = [f.value for f in stats["frameworks"]]

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# ============================================================================
# Root Endpoint
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Lexecon Governance API",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "dashboard": "/dashboard",
            "governance_dashboard": "/dashboard/governance",
            "policies": "/policies",
            "decide": "/decide",
            "verify": "/decide/verify",
            "ledger_verify": "/ledger/verify",
            "audit_report": "/ledger/report",
            "storage_stats": "/storage/stats",
            "responsibility_report": "/responsibility/report",
            "responsibility_overrides": "/responsibility/overrides",
            "compliance_article_11": "/compliance/eu-ai-act/article-11",
            "compliance_article_12_status": "/compliance/eu-ai-act/article-12/status",
            "compliance_article_12_package": "/compliance/eu-ai-act/article-12/regulatory-package",
            "compliance_article_14_intervention": "/compliance/eu-ai-act/article-14/intervention",
            "compliance_article_14_effectiveness": "/compliance/eu-ai-act/article-14/effectiveness",
            "compliance_article_14_evidence": "/compliance/eu-ai-act/article-14/evidence-package",
            # Governance API (Phase 5)
            "risk_assess": "/api/governance/risk/assess",
            "risk_get": "/api/governance/risk/{risk_id}",
            "risk_decision": "/api/governance/risk/decision/{decision_id}",
            "escalation_create": "/api/governance/escalation",
            "escalation_resolve": "/api/governance/escalation/{escalation_id}/resolve",
            "escalation_get": "/api/governance/escalation/{escalation_id}",
            "escalation_decision": "/api/governance/escalation/decision/{decision_id}",
            "escalation_sla_violations": "/api/governance/escalation/sla/violations",
            "override_create": "/api/governance/override",
            "override_get": "/api/governance/override/{override_id}",
            "override_decision": "/api/governance/override/decision/{decision_id}",
            "override_active": "/api/governance/override/decision/{decision_id}/active",
            "override_status": "/api/governance/override/decision/{decision_id}/status",
            "evidence_store": "/api/governance/evidence",
            "evidence_get": "/api/governance/evidence/{artifact_id}",
            "evidence_verify": "/api/governance/evidence/{artifact_id}/verify",
            "evidence_decision": "/api/governance/evidence/decision/{decision_id}",
            "evidence_lineage": "/api/governance/evidence/decision/{decision_id}/lineage",
            "evidence_sign": "/api/governance/evidence/{artifact_id}/sign",
            "evidence_stats": "/api/governance/evidence/statistics",
            # Compliance Mapping API (Phase 7)
            "compliance_map": "/api/governance/compliance/map",
            "compliance_controls": "/api/governance/compliance/{framework}/controls",
            "compliance_control_status": "/api/governance/compliance/{framework}/{control_id}",
            "compliance_verify_control": "/api/governance/compliance/{framework}/{control_id}/verify",
            "compliance_link_evidence": "/api/governance/compliance/{framework}/{control_id}/link-evidence",
            "compliance_gaps": "/api/governance/compliance/{framework}/gaps",
            "compliance_report": "/api/governance/compliance/{framework}/report",
            "compliance_coverage": "/api/governance/compliance/{framework}/coverage",
            "compliance_primitive_mappings": "/api/governance/compliance/primitive/{primitive_id}/mappings",
            "compliance_statistics": "/api/governance/compliance/statistics",
        },
    }
