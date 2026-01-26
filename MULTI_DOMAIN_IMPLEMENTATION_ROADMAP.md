# [ARCHIVED] Multi-Domain Implementation Roadmap

**Status:** MOVED TO LEXECON V2.0 (SEPARATE REPOSITORY)

**Project Structure:**
- **Lexecon v1.0** (this repository): Enterprise AI Governance
  - Focus: Production-ready, SOC 2 certified, GDPR compliant
  - Timeline: Complete Phases 5-8 (CI/CD, Monitoring, Compliance, Optimization)
  - Target: Single-domain (AI) governance at enterprise scale

- **Lexecon v2.0** (future separate repository): Universal Governance Protocol
  - Focus: Multi-domain expansion (Finance, Healthcare, Defense, Supply Chain, Energy)
  - Architecture: Domain plugin system, DomainRegistry, universal decision service
  - Roadmap: This document (20 weeks, 7 phases)
  - Constraints: Built on top of production-ready v1.0 infrastructure

**Why Separate Repositories?**
1. **Clear scope:** v1.0 is AI governance with enterprise guarantees
2. **Independent release cycles:** v1.0 doesn't block v2.0 domain expansion
3. **Architecture isolation:** v2.0 builds new domain layer on proven v1.0 foundation
4. **Team scalability:** v1.0 team maintains product; v2.0 team builds universal protocol

**Migration Path for v1.0 → v2.0:**
- v1.0 clients use `GET /health`, `POST /decisions/request` (AI domain hardcoded)
- v2.0 clients use `GET /api/v1/{domain}/decisions/request` (domain parameter)
- v1.0 API remains unchanged for backward compatibility during transition
- Domain="ai" is default for v1.0 clients

---

## Decision

This roadmap is **frozen as reference documentation** for future v2.0 project initiation. All active work redirects to Issue #25: Enterprise Readiness Plan (Lexecon v1.0 completion).

---

## ✅ Completed Foundation Work

**Status:** Core infrastructure hardened and production-ready (Commits: 7d3f961, 6832358, ed9adbd, 38b5bab, 232fc3b, 55afdef)

### Security Hardening
- ✅ **Extended Input Validation** - All API models (DecisionRequestModel, InterventionModel, OverrideCreateRequest, ExportRequestModel) now have 30+ Pydantic field validators with defense-in-depth pattern
- ✅ **SQL Injection Prevention** - Whitelist validation on audit export endpoints (time_window enum, formats deduplication, RFC 5321 email validation)
- ✅ **Rate Limiter DoS Protection** - Token bucket algorithm with LRU eviction, aggressive cleanup, memory-safe cardinality limits
- ✅ **Auth Schema Alignment** - Password expiration, MFA fields, session validation, proper error handling

### Observability Infrastructure
- ✅ **Production-Grade Tracing** - W3C Trace Context, OTLP export (Jaeger/Datadog compatible), async-safe context propagation
- ✅ **Metrics & Cardinality Management** - Prometheus integration with hash-based label aggregation, no memory exhaustion risk
- ✅ **Error Tracking** - Structured error handling with context enrichment, automatic anomaly detection
- ✅ **Health Checks** - Comprehensive endpoint health monitoring with dependency checks
- ✅ **Circuit Breakers** - Failure isolation, exponential backoff, dependency health tracking

### Async/Await Refactoring
- ✅ **AsyncAuthService** - Non-blocking auth operations using asyncio.to_thread(), 12 async methods, event loop safe
- ✅ **Concurrent Auth** - 7 endpoints refactored to use async patterns (login, logout, user management, password ops)
- ✅ **Backward Compatibility** - Parallel sync/async instances, no breaking changes

### Test Coverage
- ✅ 38+ validation test cases (all passing)
- ✅ 8 async concurrency tests (all passing)
- ✅ Integration tests for rate limiting, error propagation, ledger recording
- ✅ Zero breaking changes to existing APIs

**Impact on Multi-Domain Timeline:** Foundation is 2-3 weeks ahead of original Phase 1 estimate. This enables accelerated domain plugin development and reduces risk of performance/security issues during multi-domain expansion.

---

## 🏗️ Phase 1: Core Refactoring (Week 1-4)

**Foundation Status:** Security hardening complete. Phase 1 can focus on domain abstraction without blocking on infrastructure concerns.

### 1.1: Extract Domain-Agnostic Primitives

**Current State:**
- Policy engine is domain-agnostic ✅
- Decision service is AI-focused ❌
- Compliance mapping is hardcoded for EU AI Act/GDPR ❌
- Actor/action types assume AI context ❌
- Security hardening complete ✅ (validation, rate limiting, async, tracing)

**Target State:**
- All core services are domain-agnostic
- Domain-specific logic moved to plugins
- Actor/action types are configurable
- Maintain production-grade observability and security across all domains

**Implementation:**

```python
# NEW: src/lexecon/core/domain.py

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class GovernanceDomain(str, Enum):
    """Supported governance domains."""
    AI = "ai"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    DEFENSE = "defense"
    AUTOMOTIVE = "automotive"
    SUPPLY_CHAIN = "supply_chain"
    ENERGY = "energy"
    GENERAL = "general"  # Catch-all for custom domains


class ActorType(BaseModel):
    """Actor type definition."""
    type_id: str  # e.g., "act_trading_algo", "act_ai_agent"
    category: str  # "human", "ai", "system", "robot"
    label: str
    description: str
    metadata: Dict[str, Any] = {}


class ActionType(BaseModel):
    """Action type definition."""
    type_id: str  # e.g., "axn_place_order", "axn_execute_tool"
    category: str  # "read", "write", "execute", "delete", "transmit"
    label: str
    description: str
    risk_level: int = 1  # 1-5
    requires_human_approval: bool = False
    metadata: Dict[str, Any] = {}


class ResourceType(BaseModel):
    """Resource type definition."""
    type_id: str  # e.g., "res_phi", "res_security"
    category: str  # "data", "infrastructure", "financial_instrument"
    label: str
    description: str
    sensitivity: str = "public"  # public, internal, confidential, secret
    metadata: Dict[str, Any] = {}


class DomainConfig(BaseModel):
    """Configuration for a governance domain."""
    domain: GovernanceDomain
    display_name: str
    description: str

    # Domain-specific types
    actor_types: List[ActorType]
    action_types: List[ActionType]
    resource_types: List[ResourceType]

    # Compliance frameworks applicable to this domain
    compliance_frameworks: List[str]  # ["MIFID_II", "HIPAA", "EU_AI_ACT"]

    # Domain-specific risk models
    risk_models: List[str]

    # Policy templates
    policy_templates: List[Dict[str, Any]]

    # Domain-specific constraints
    constraints: Dict[str, Any] = {}

    # Metadata
    metadata: Dict[str, Any] = {}


class DomainRegistry:
    """Registry of all supported governance domains."""

    def __init__(self):
        self._domains: Dict[GovernanceDomain, DomainConfig] = {}

    def register_domain(self, config: DomainConfig) -> None:
        """Register a domain configuration."""
        self._domains[config.domain] = config

    def get_domain(self, domain: GovernanceDomain) -> Optional[DomainConfig]:
        """Get domain configuration."""
        return self._domains.get(domain)

    def list_domains(self) -> List[DomainConfig]:
        """List all registered domains."""
        return list(self._domains.values())

    def get_actor_type(self, domain: GovernanceDomain, type_id: str) -> Optional[ActorType]:
        """Get actor type definition."""
        config = self.get_domain(domain)
        if not config:
            return None
        for actor_type in config.actor_types:
            if actor_type.type_id == type_id:
                return actor_type
        return None

    def get_action_type(self, domain: GovernanceDomain, type_id: str) -> Optional[ActionType]:
        """Get action type definition."""
        config = self.get_domain(domain)
        if not config:
            return None
        for action_type in config.action_types:
            if action_type.type_id == type_id:
                return action_type
        return None


# Global domain registry
domain_registry = DomainRegistry()
```

**Migration Path:**
1. Create `core/domain.py` with domain abstraction
2. Refactor `decision/service.py` to accept domain parameter
3. Move AI-specific types to `domains/ai/config.py`
4. Update API to accept `domain` parameter (default: "ai" for backward compatibility)

---

### 1.2: Refactor Decision Service

**Current State:**
```python
# decision/service.py - AI-focused
class DecisionService:
    def evaluate_request(self, request: DecisionRequest) -> DecisionResponse:
        # Assumes AI context
        ...
```

**Target State:**
```python
# NEW: core/decision_service.py - Domain-agnostic

from lexecon.core.domain import GovernanceDomain, DomainRegistry

class UniversalDecisionService:
    """
    Universal decision service supporting multiple domains.

    Backward compatible with existing DecisionService API.
    """

    def __init__(
        self,
        policy_engine: PolicyEngine,
        domain: GovernanceDomain = GovernanceDomain.AI,
        domain_registry: DomainRegistry = None,
        ledger = None,
        identity = None,
    ):
        self.policy_engine = policy_engine
        self.domain = domain
        self.domain_registry = domain_registry or domain_registry
        self.ledger = ledger
        self.identity = identity

        # Load domain configuration
        self.domain_config = self.domain_registry.get_domain(domain)
        if not self.domain_config:
            raise ValueError(f"Domain {domain} not registered")

    def evaluate_request(
        self,
        request: Union[DecisionRequest, Dict[str, Any]]
    ) -> DecisionResponse:
        """
        Evaluate decision request (universal interface).

        Accepts:
        - Legacy DecisionRequest (for backward compatibility)
        - Dict with universal fields (domain-agnostic)
        """
        # Normalize to universal format
        if isinstance(request, DecisionRequest):
            # Legacy format - convert to universal
            actor = request.actor
            action = request.proposed_action
            resource = None
            context = request.context
        else:
            # Universal format
            actor = request.get("actor")
            action = request.get("action")
            resource = request.get("resource")
            context = request.get("context", {})

        # Validate actor/action types for domain
        self._validate_types(actor, action, resource)

        # Evaluate against policy
        decision = self.policy_engine.evaluate(
            actor=actor,
            action=action,
            resource=resource,
            context=context
        )

        # Domain-specific processing
        decision = self._apply_domain_rules(decision, actor, action, context)

        # Generate capability token if approved
        token = None
        if decision.allowed:
            token = self._mint_token(actor, action, resource, decision)

        # Map to compliance controls
        compliance_mappings = self._map_to_compliance(decision)

        # Record in ledger
        ledger_hash = None
        if self.ledger:
            ledger_entry = self.ledger.append(
                event_type=f"{self.domain.value}_decision",
                data={
                    "domain": self.domain.value,
                    "actor": actor,
                    "action": action,
                    "resource": resource,
                    "decision": decision.allowed,
                    "reason": decision.reason,
                    "compliance": compliance_mappings,
                    "context": context
                }
            )
            ledger_hash = ledger_entry.entry_hash

        # Build response
        return DecisionResponse(
            request_id=request.get("request_id") if isinstance(request, dict) else request.request_id,
            decision="permit" if decision.allowed else "deny",
            reasoning=decision.reason,
            policy_version_hash=decision.policy_version_hash,
            capability_token=token,
            ledger_entry_hash=ledger_hash,
            compliance_mappings=compliance_mappings
        )

    def _validate_types(self, actor: str, action: str, resource: Optional[str]):
        """Validate that actor/action/resource types are valid for domain."""
        # Check actor type
        if actor and not actor.startswith("act_"):
            # Legacy format - allow for backward compatibility
            return

        actor_type_id = actor.split(":")[0] if ":" in actor else actor
        action_type_id = action.split(":")[0] if ":" in action else action

        # Validate against domain config
        actor_type = self.domain_registry.get_actor_type(self.domain, actor_type_id)
        action_type = self.domain_registry.get_action_type(self.domain, action_type_id)

        if not actor_type:
            raise ValueError(f"Invalid actor type for domain {self.domain}: {actor_type_id}")

        if not action_type:
            raise ValueError(f"Invalid action type for domain {self.domain}: {action_type_id}")

    def _apply_domain_rules(self, decision, actor, action, context):
        """Apply domain-specific rules and constraints."""
        # Hook for domain plugins to modify decision
        # E.g., finance domain might check position limits
        # Healthcare domain might check patient consent
        return decision

    def _map_to_compliance(self, decision) -> List[Dict[str, Any]]:
        """Map decision to compliance frameworks for this domain."""
        mappings = []

        for framework in self.domain_config.compliance_frameworks:
            # Use compliance_mapping service to map primitives to controls
            mapping = compliance_service.map_primitive_to_controls(
                primitive_type="DECISION_LOGGING",
                primitive_id=decision.get("decision_id", "unknown"),
                framework=framework
            )
            mappings.append({
                "framework": framework,
                "controls": mapping.control_ids,
                "status": "compliant" if decision.allowed else "denied"
            })

        return mappings
```

**Migration Steps:**
1. Create `core/decision_service.py` with `UniversalDecisionService`
2. Keep `decision/service.py` as wrapper for backward compatibility
3. Update API to use `UniversalDecisionService` internally
4. Add domain parameter to all API endpoints (default: "ai")

---

### 1.3: Create Domain Plugin System

**NEW: Domain Plugin Architecture**

```python
# NEW: core/plugin.py

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class DomainPlugin(ABC):
    """
    Base class for domain plugins.

    Plugins can extend Lexecon with domain-specific:
    - Actor/action/resource types
    - Risk models
    - Compliance mappings
    - Policy templates
    - Custom validation logic
    """

    def __init__(self, config: DomainConfig):
        self.config = config

    @abstractmethod
    def get_domain_config(self) -> DomainConfig:
        """Return domain configuration."""
        pass

    def validate_decision_request(
        self,
        actor: str,
        action: str,
        resource: Optional[str],
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Validate decision request for domain-specific constraints.

        Returns:
            None if valid, error message if invalid
        """
        return None

    def enrich_decision_context(
        self,
        actor: str,
        action: str,
        resource: Optional[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich context with domain-specific data.

        E.g., finance plugin might add market data, risk scores
        """
        return context

    def post_decision_hook(
        self,
        decision: DecisionResponse,
        actor: str,
        action: str,
        context: Dict[str, Any]
    ) -> None:
        """
        Hook called after decision is made.

        E.g., send alerts, update external systems
        """
        pass

    def get_policy_templates(self) -> List[Dict[str, Any]]:
        """Return pre-built policy templates for this domain."""
        return self.config.policy_templates

    def get_compliance_mappings(self) -> Dict[str, Any]:
        """Return compliance framework mappings."""
        return {}


class PluginRegistry:
    """Registry for domain plugins."""

    def __init__(self):
        self._plugins: Dict[GovernanceDomain, DomainPlugin] = {}

    def register_plugin(self, domain: GovernanceDomain, plugin: DomainPlugin) -> None:
        """Register a domain plugin."""
        self._plugins[domain] = plugin

        # Also register domain config in domain registry
        domain_registry.register_domain(plugin.get_domain_config())

    def get_plugin(self, domain: GovernanceDomain) -> Optional[DomainPlugin]:
        """Get plugin for domain."""
        return self._plugins.get(domain)


# Global plugin registry
plugin_registry = PluginRegistry()
```

---

## 🔌 Phase 2: Domain Plugin Implementation (Week 5-8)

### 2.1: AI Domain Plugin (Baseline)

**Extract existing AI logic into plugin:**

```python
# NEW: domains/ai/plugin.py

from lexecon.core.plugin import DomainPlugin
from lexecon.core.domain import DomainConfig, GovernanceDomain, ActorType, ActionType

class AIDomainPlugin(DomainPlugin):
    """Plugin for AI governance domain."""

    def get_domain_config(self) -> DomainConfig:
        return DomainConfig(
            domain=GovernanceDomain.AI,
            display_name="AI Governance",
            description="Governance for AI systems, LLMs, and autonomous agents",

            actor_types=[
                ActorType(
                    type_id="act_ai_agent",
                    category="ai",
                    label="AI Agent",
                    description="Autonomous AI agent or LLM",
                    metadata={"requires_human_oversight": True}
                ),
                ActorType(
                    type_id="act_human_user",
                    category="human",
                    label="Human User",
                    description="Human user interacting with AI",
                    metadata={}
                ),
                ActorType(
                    type_id="act_system_service",
                    category="system",
                    label="System Service",
                    description="Backend system or service",
                    metadata={}
                ),
            ],

            action_types=[
                ActionType(
                    type_id="axn_execute_tool",
                    category="execute",
                    label="Execute Tool",
                    description="AI agent executing a tool or function",
                    risk_level=3,
                    requires_human_approval=False
                ),
                ActionType(
                    type_id="axn_read_data",
                    category="read",
                    label="Read Data",
                    description="Read sensitive data",
                    risk_level=2
                ),
                ActionType(
                    type_id="axn_write_data",
                    category="write",
                    label="Write Data",
                    description="Modify or create data",
                    risk_level=3
                ),
                ActionType(
                    type_id="axn_delete_data",
                    category="delete",
                    label="Delete Data",
                    description="Delete data permanently",
                    risk_level=4,
                    requires_human_approval=True
                ),
            ],

            resource_types=[
                ResourceType(
                    type_id="res_database",
                    category="data",
                    label="Database",
                    description="Database system",
                    sensitivity="confidential"
                ),
                ResourceType(
                    type_id="res_api",
                    category="infrastructure",
                    label="API Endpoint",
                    description="External API",
                    sensitivity="public"
                ),
            ],

            compliance_frameworks=[
                "EU_AI_ACT",
                "GDPR",
                "SOC2",
                "ISO_27001"
            ],

            risk_models=[
                "ai_safety",
                "prompt_injection",
                "data_leakage",
                "model_bias"
            ],

            policy_templates=[
                {
                    "name": "deny_by_default",
                    "description": "Deny all actions unless explicitly permitted",
                    "mode": "strict"
                },
                {
                    "name": "high_risk_human_oversight",
                    "description": "Require human approval for high-risk actions",
                    "escalation_rules": {"risk_level": 4}
                }
            ]
        )


# Register AI plugin
plugin_registry.register_plugin(GovernanceDomain.AI, AIDomainPlugin())
```

### 2.2: Finance Domain Plugin

```python
# NEW: domains/finance/plugin.py

from lexecon.core.plugin import DomainPlugin
from lexecon.core.domain import DomainConfig, GovernanceDomain, ActorType, ActionType

class FinanceDomainPlugin(DomainPlugin):
    """Plugin for financial services governance."""

    def get_domain_config(self) -> DomainConfig:
        return DomainConfig(
            domain=GovernanceDomain.FINANCE,
            display_name="Financial Services Governance",
            description="Governance for algorithmic trading, risk management, and financial automation",

            actor_types=[
                ActorType(
                    type_id="act_trading_algo",
                    category="ai",
                    label="Trading Algorithm",
                    description="Automated trading system",
                    metadata={"requires_risk_checks": True}
                ),
                ActorType(
                    type_id="act_portfolio_manager",
                    category="human",
                    label="Portfolio Manager",
                    description="Human portfolio manager",
                    metadata={}
                ),
                ActorType(
                    type_id="act_risk_system",
                    category="system",
                    label="Risk Management System",
                    description="Automated risk monitoring",
                    metadata={}
                ),
            ],

            action_types=[
                ActionType(
                    type_id="axn_place_order",
                    category="execute",
                    label="Place Order",
                    description="Execute trading order",
                    risk_level=3,
                    requires_human_approval=False,
                    metadata={"max_order_value": 10_000_000}
                ),
                ActionType(
                    type_id="axn_cancel_order",
                    category="delete",
                    label="Cancel Order",
                    description="Cancel pending order",
                    risk_level=2
                ),
                ActionType(
                    type_id="axn_rebalance_portfolio",
                    category="execute",
                    label="Rebalance Portfolio",
                    description="Rebalance asset allocation",
                    risk_level=4,
                    requires_human_approval=True
                ),
            ],

            resource_types=[
                ResourceType(
                    type_id="res_security",
                    category="financial_instrument",
                    label="Security",
                    description="Stock, bond, or other security",
                    sensitivity="confidential"
                ),
                ResourceType(
                    type_id="res_account",
                    category="financial_account",
                    label="Trading Account",
                    description="Customer trading account",
                    sensitivity="secret"
                ),
            ],

            compliance_frameworks=[
                "MIFID_II",
                "SEC_RULE_613",
                "DODD_FRANK",
                "BASEL_III"
            ],

            risk_models=[
                "market_risk",
                "credit_risk",
                "operational_risk",
                "liquidity_risk",
                "flash_crash_prevention"
            ],

            policy_templates=[
                {
                    "name": "prevent_flash_crash",
                    "description": "Prevent large orders in short time windows",
                    "constraints": {
                        "max_order_value_per_minute": 10_000_000,
                        "requires_circuit_breaker": True
                    }
                },
                {
                    "name": "position_limits",
                    "description": "Enforce position size limits",
                    "constraints": {
                        "max_position_percentage": 0.05  # 5% of portfolio
                    }
                }
            ]
        )

    def validate_decision_request(
        self,
        actor: str,
        action: str,
        resource: Optional[str],
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Validate finance-specific constraints."""
        # Check order value limits
        if action == "axn_place_order":
            order_value = context.get("order_value", 0)
            if order_value > 10_000_000:
                return "Order value exceeds limit ($10M), requires human approval"

        # Check market hours
        import datetime
        now = datetime.datetime.now()
        if now.hour < 9 or now.hour >= 16:
            if action == "axn_place_order":
                return "Trading outside market hours not permitted"

        return None


# Register finance plugin
plugin_registry.register_plugin(GovernanceDomain.FINANCE, FinanceDomainPlugin())
```

### 2.3: Healthcare Domain Plugin

```python
# NEW: domains/healthcare/plugin.py

class HealthcareDomainPlugin(DomainPlugin):
    """Plugin for healthcare governance."""

    def get_domain_config(self) -> DomainConfig:
        return DomainConfig(
            domain=GovernanceDomain.HEALTHCARE,
            display_name="Healthcare Governance",
            description="Governance for clinical decision support, PHI access, and medical AI",

            actor_types=[
                ActorType(
                    type_id="act_cdss",
                    category="ai",
                    label="Clinical Decision Support System",
                    description="AI system for medical diagnosis/treatment",
                    metadata={"requires_physician_oversight": True}
                ),
                ActorType(
                    type_id="act_physician",
                    category="human",
                    label="Physician",
                    description="Licensed medical doctor",
                    metadata={"license_required": True}
                ),
            ],

            action_types=[
                ActionType(
                    type_id="axn_access_phi",
                    category="read",
                    label="Access PHI",
                    description="Access protected health information",
                    risk_level=4,
                    requires_human_approval=False,
                    metadata={"requires_patient_consent": True}
                ),
                ActionType(
                    type_id="axn_recommend_treatment",
                    category="execute",
                    label="Recommend Treatment",
                    description="AI recommending medical treatment",
                    risk_level=5,
                    requires_human_approval=True
                ),
                ActionType(
                    type_id="axn_prescribe_medication",
                    category="execute",
                    label="Prescribe Medication",
                    description="Generate prescription",
                    risk_level=5,
                    requires_human_approval=True
                ),
            ],

            compliance_frameworks=[
                "HIPAA",
                "FDA_21_CFR_PART_11",
                "GDPR",
                "ISO_13485"
            ],

            risk_models=[
                "medical_malpractice",
                "phi_breach",
                "diagnostic_error",
                "treatment_harm"
            ],

            policy_templates=[
                {
                    "name": "hipaa_minimum_necessary",
                    "description": "Enforce HIPAA minimum necessary standard",
                    "constraints": {
                        "require_patient_consent": True,
                        "require_medical_purpose": True,
                        "audit_all_access": True
                    }
                }
            ]
        )

    def validate_decision_request(
        self,
        actor: str,
        action: str,
        resource: Optional[str],
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Validate healthcare-specific constraints."""
        # Check patient consent for PHI access
        if action == "axn_access_phi":
            if not context.get("patient_consent"):
                return "Patient consent required for PHI access (HIPAA)"

        # Check physician oversight for clinical decisions
        if action in ["axn_recommend_treatment", "axn_prescribe_medication"]:
            if not context.get("physician_id"):
                return "Physician oversight required for clinical decisions"

        return None


# Register healthcare plugin
plugin_registry.register_plugin(GovernanceDomain.HEALTHCARE, HealthcareDomainPlugin())
```

---

## 🌐 Phase 3: API Updates (Week 9-10)

### 3.1: Update API Endpoints to Support Domains

**Before (AI-only):**
```python
@app.post("/decisions/request")
async def request_decision(request: DecisionRequest):
    response = decision_service.evaluate_request(request)
    return response.to_dict()
```

**After (Multi-domain):**
```python
@app.post("/api/v1/{domain}/decisions/request")
async def request_decision(
    domain: str,
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Request a governance decision.

    Supports multiple domains:
    - /api/v1/ai/decisions/request
    - /api/v1/finance/decisions/request
    - /api/v1/healthcare/decisions/request
    """
    # Validate domain
    try:
        gov_domain = GovernanceDomain(domain)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")

    # Get domain plugin
    plugin = plugin_registry.get_plugin(gov_domain)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Domain not supported: {domain}")

    # Validate request using plugin
    validation_error = plugin.validate_decision_request(
        actor=request.get("actor"),
        action=request.get("action"),
        resource=request.get("resource"),
        context=request.get("context", {})
    )
    if validation_error:
        raise HTTPException(status_code=400, detail=validation_error)

    # Enrich context using plugin
    context = plugin.enrich_decision_context(
        actor=request.get("actor"),
        action=request.get("action"),
        resource=request.get("resource"),
        context=request.get("context", {})
    )
    request["context"] = context

    # Create domain-specific decision service
    decision_service = UniversalDecisionService(
        policy_engine=policy_engine,
        domain=gov_domain,
        ledger=ledger,
        identity=identity
    )

    # Evaluate request
    response = decision_service.evaluate_request(request)

    # Post-decision hook
    plugin.post_decision_hook(
        decision=response,
        actor=request.get("actor"),
        action=request.get("action"),
        context=request.get("context", {})
    )

    return response.to_dict()


# Backward compatibility endpoint
@app.post("/decisions/request")
async def request_decision_legacy(request: DecisionRequest):
    """Legacy AI governance endpoint (backward compatible)."""
    # Route to AI domain
    return await request_decision(
        domain="ai",
        request=request.to_dict()
    )
```

### 3.2: Add Domain Discovery Endpoints

```python
@app.get("/api/v1/domains")
async def list_domains():
    """List all supported governance domains."""
    domains = domain_registry.list_domains()
    return [
        {
            "domain": d.domain.value,
            "display_name": d.display_name,
            "description": d.description,
            "compliance_frameworks": d.compliance_frameworks,
            "actor_types": [a.type_id for a in d.actor_types],
            "action_types": [a.type_id for a in d.action_types]
        }
        for d in domains
    ]


@app.get("/api/v1/{domain}/config")
async def get_domain_config(domain: str):
    """Get detailed configuration for a domain."""
    try:
        gov_domain = GovernanceDomain(domain)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")

    config = domain_registry.get_domain(gov_domain)
    if not config:
        raise HTTPException(status_code=404, detail=f"Domain not found: {domain}")

    return config.model_dump()


@app.get("/api/v1/{domain}/policy-templates")
async def get_policy_templates(domain: str):
    """Get pre-built policy templates for a domain."""
    try:
        gov_domain = GovernanceDomain(domain)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")

    plugin = plugin_registry.get_plugin(gov_domain)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Domain not supported: {domain}")

    return plugin.get_policy_templates()
```

---

## 📚 Phase 4: Documentation & Examples (Week 11-12)

### 4.1: Domain Plugin Developer Guide

Create `docs/DOMAIN_PLUGIN_GUIDE.md`:

```markdown
# How to Create a Lexecon Domain Plugin

## Overview

Domain plugins extend Lexecon to support new governance domains (e.g., finance, healthcare, defense).

## Quick Start

1. Create plugin file: `domains/<your_domain>/plugin.py`
2. Implement `DomainPlugin` interface
3. Register plugin in `domains/__init__.py`
4. Write tests in `tests/domains/test_<your_domain>.py`

## Example: Custom Logistics Domain

```python
from lexecon.core.plugin import DomainPlugin
from lexecon.core.domain import DomainConfig, GovernanceDomain

class LogisticsDomainPlugin(DomainPlugin):
    def get_domain_config(self) -> DomainConfig:
        return DomainConfig(
            domain=GovernanceDomain.GENERAL,  # Or add new enum value
            display_name="Logistics Governance",
            actor_types=[...],
            action_types=[...],
            compliance_frameworks=["ISO_28000"]
        )

# Register
plugin_registry.register_plugin(GovernanceDomain.GENERAL, LogisticsDomainPlugin())
```

...
```

### 4.2: Example Implementations

Create `examples/domains/` with working examples:

```
examples/
  domains/
    finance_example.py      # Algorithmic trading governance
    healthcare_example.py   # Clinical decision support
    defense_example.py      # Autonomous weapons oversight
    autonomous_vehicle_example.py
```

---

## 🧪 Phase 5: Testing & Validation (Week 13-14)

### 5.1: Domain Plugin Tests

```python
# tests/domains/test_finance_plugin.py

import pytest
from lexecon.domains.finance.plugin import FinanceDomainPlugin
from lexecon.core.decision_service import UniversalDecisionService

class TestFinanceDomain:
    def test_trading_order_allowed(self):
        """Test that valid trading order is approved."""
        plugin = FinanceDomainPlugin()
        service = UniversalDecisionService(
            policy_engine=create_finance_policy(),
            domain=GovernanceDomain.FINANCE
        )

        decision = service.evaluate_request({
            "actor": "act_trading_algo:momentum_v3",
            "action": "axn_place_order",
            "resource": "res_security:AAPL",
            "context": {
                "order_value": 500_000,
                "risk_score": 0.3
            }
        })

        assert decision.decision == "permit"
        assert "MIFID_II" in [m["framework"] for m in decision.compliance_mappings]

    def test_large_order_denied(self):
        """Test that orders exceeding limits are denied."""
        plugin = FinanceDomainPlugin()

        error = plugin.validate_decision_request(
            actor="act_trading_algo:momentum_v3",
            action="axn_place_order",
            resource="res_security:AAPL",
            context={"order_value": 20_000_000}  # Exceeds $10M limit
        )

        assert error is not None
        assert "exceeds limit" in error
```

### 5.2: Integration Tests

```python
# tests/integration/test_multi_domain.py

def test_ai_and_finance_domains_coexist():
    """Test that multiple domains can run simultaneously."""
    # AI decision
    ai_decision = UniversalDecisionService(
        domain=GovernanceDomain.AI
    ).evaluate_request({
        "actor": "act_ai_agent:gpt4",
        "action": "axn_execute_tool",
        ...
    })

    # Finance decision
    finance_decision = UniversalDecisionService(
        domain=GovernanceDomain.FINANCE
    ).evaluate_request({
        "actor": "act_trading_algo:algo1",
        "action": "axn_place_order",
        ...
    })

    # Both should have different compliance mappings
    assert any("EU_AI_ACT" in str(m) for m in ai_decision.compliance_mappings)
    assert any("MIFID_II" in str(m) for m in finance_decision.compliance_mappings)
```

---

## 📦 Phase 6: Packaging & Distribution (Week 15-16)

### 6.1: Modular Installation

Update `pyproject.toml` to support domain-specific extras:

```toml
[project.optional-dependencies]
# Core (AI domain included)
core = [
    "fastapi>=0.104.0",
    "cryptography>=41.0.0",
    ...
]

# Domain-specific extras
finance = [
    "lexecon[core]",
    "pandas>=2.0.0",
    "numpy>=1.24.0"
]

healthcare = [
    "lexecon[core]",
    "fhir-resources>=0.6.0"
]

defense = [
    "lexecon[core]",
    ...
]

# Install all domains
all-domains = [
    "lexecon[finance]",
    "lexecon[healthcare]",
    "lexecon[defense]"
]
```

Usage:
```bash
# Just AI governance (default)
pip install lexecon

# AI + Finance
pip install lexecon[finance]

# All domains
pip install lexecon[all-domains]
```

### 6.2: CLI Updates

```bash
# Initialize with domain
lexecon init --domain=finance

# List available domains
lexecon domains list

# Get domain info
lexecon domains info finance

# Load policy template for domain
lexecon policy load --domain=finance --template=prevent_flash_crash

# Validate domain-specific policy
lexecon policy validate --domain=healthcare policy.yaml
```

---

## 🚀 Phase 7: Launch Strategy (Week 17-20)

### 7.1: Soft Launch (Week 17-18)
- Release v2.0.0-beta with multi-domain support
- Invite current customers to test
- Gather feedback on API

### 7.2: Public Launch (Week 19)
- Blog post: "Introducing Universal Governance Protocol"
- Update README, docs, website
- Launch domain marketplace (community plugins)

### 7.3: Marketing Push (Week 20)
- Announce on HN, Reddit, LinkedIn
- Partner announcements (AWS, Azure)
- Publish domain case studies

---

## 📊 Success Metrics

### Technical Metrics
- ✅ 80%+ test coverage maintained across all domains
- ✅ All domains pass integration tests
- ✅ API backward compatibility verified
- ✅ Performance: <100ms decision latency per domain

### Business Metrics
- ✅ 2+ non-AI domains with pilot customers (finance, healthcare)
- ✅ 10+ community-contributed domain plugins
- ✅ 5,000+ GitHub stars
- ✅ 100+ production deployments

### Developer Adoption
- ✅ 1,000+ npm/pip downloads of domain plugins
- ✅ 50+ "Powered by Lexecon" integrations
- ✅ 20+ blog posts/tutorials from community

---

## 🛡️ Risk Mitigation

### Risk 1: Breaking Changes
**Mitigation:**
- Maintain v1 API alongside v2
- Comprehensive migration guide
- Automated migration tool

### Risk 2: Performance Degradation
**Mitigation:**
- Benchmark each domain
- Optimize hot paths
- Lazy-load domain configs

### Risk 3: Community Adoption
**Mitigation:**
- Extensive documentation
- Video tutorials
- Office hours for plugin developers

---

## 📅 Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1: Core Refactoring | 4 weeks | Domain-agnostic architecture |
| Phase 2: Domain Plugins | 4 weeks | AI, Finance, Healthcare plugins |
| Phase 3: API Updates | 2 weeks | Multi-domain API endpoints |
| Phase 4: Documentation | 2 weeks | Developer guides, examples |
| Phase 5: Testing | 2 weeks | Comprehensive test suite |
| Phase 6: Packaging | 2 weeks | Modular distribution |
| Phase 7: Launch | 4 weeks | Public release, marketing |
| **TOTAL** | **20 weeks** | **Universal Governance Protocol** |

---

## 🎯 Next Immediate Actions

**Starting Point:** Foundation work complete. Phase 1 begins with domain abstraction.

1. **This Week (Immediate):**
   - Create `src/lexecon/core/domain.py` with DomainRegistry, GovernanceDomain enum
   - Create `src/lexecon/core/plugin.py` with DomainPlugin base class
   - Extract AI-specific types into `src/lexecon/domains/ai/config.py`
   - Write domain plugin RFC (incorporate feedback from 3 P1 blocker commits)

2. **Next Week:**
   - Implement `UniversalDecisionService` in `src/lexecon/core/decision_service.py`
   - Create FinanceDomainPlugin (first non-AI domain pilot)
   - Update `/api/v1/{domain}/decisions/request` endpoint
   - Verify no regression in existing AI domain functionality

3. **Following Week:**
   - Add domain-specific validation hooks (finance order limits, healthcare PHI checks)
   - Integration tests for multi-domain coexistence
   - Update documentation with domain plugin examples
   - Prepare v2.0.0-beta release

**Acceleration Opportunity:** With observability, security, and async infrastructure proven in production, domain plugin development can proceed without infrastructure blockers. Estimated Phase 1 completion: 2-3 weeks vs original 4 weeks.

---

**The foundation is solid. Domain abstraction is next. Let's build the universal governance protocol.** 🚀
