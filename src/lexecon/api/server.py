"""
API Server - REST API for Lexecon governance system.

Provides endpoints for health checks, policy management, decision requests,
and audit operations.
"""

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from lexecon.decision.service import DecisionRequest, DecisionService
from lexecon.identity.signing import KeyManager
from lexecon.ledger.chain import LedgerChain
from lexecon.policy.engine import PolicyEngine, PolicyMode


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

# Global state (in production, use dependency injection)
policy_engine: Optional[PolicyEngine] = None
decision_service: Optional[DecisionService] = None
ledger: LedgerChain = LedgerChain()
key_manager: Optional[KeyManager] = None
node_id: str = str(uuid.uuid4())
startup_time: float = time.time()


def initialize_services():
    """Initialize services with default configuration."""
    global policy_engine, decision_service, key_manager

    if policy_engine is None:
        policy_engine = PolicyEngine(mode=PolicyMode.STRICT)

    if decision_service is None:
        decision_service = DecisionService(policy_engine=policy_engine)

    if key_manager is None:
        key_manager = KeyManager.generate()


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
        },
    }
