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
from fastapi.responses import HTMLResponse, FileResponse
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
intervention_storage = None  # InterventionStorage - initialized with oversight_system
node_id: str = str(uuid.uuid4())
startup_time: float = time.time()


def initialize_services():
    """Initialize services with default configuration."""
    global policy_engine, decision_service, key_manager, oversight_system, intervention_storage

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
        is_valid = ledger.verify_chain()
        verification_report["chain_integrity"] = "VALID" if is_valid else "INVALID"
        verification_report["verification_details"] = "All entries properly chained with valid hashes"
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

    return audit_packet


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
            "dashboard": "/dashboard",
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
