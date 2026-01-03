"""
API Server - REST API for Lexecon governance system.

Provides endpoints for health checks, policy management, decision requests,
and audit operations.
"""

import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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
node_id: str = str(uuid.uuid4())
startup_time: float = time.time()


def initialize_services():
    """Initialize services with default configuration."""
    global policy_engine, decision_service, key_manager, oversight_system

    if policy_engine is None:
        policy_engine = PolicyEngine(mode=PolicyMode.STRICT)

    if decision_service is None:
        decision_service = DecisionService(policy_engine=policy_engine)

    if key_manager is None:
        key_manager = KeyManager.generate()

    # Initialize oversight system after key_manager is available
    if oversight_system is None:
        from lexecon.compliance.eu_ai_act.article_14_oversight import HumanOversightEvidence
        oversight_system = HumanOversightEvidence(key_manager=key_manager)


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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Lexecon Governance API",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "status": "/status",
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
        },
    }
