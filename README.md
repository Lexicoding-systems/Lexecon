# Lexecon - Universal Governance Protocol

<div align="center">

[![CI](https://github.com/Lexicoding-systems/Lexecon/actions/workflows/ci.yml/badge.svg)](https://github.com/Lexicoding-systems/Lexecon/actions/workflows/ci.yml)
[![CodeQL](https://github.com/Lexicoding-systems/Lexecon/actions/workflows/codeql.yml/badge.svg)](https://github.com/Lexicoding-systems/Lexecon/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/Lexicoding-systems/Lexecon/branch/main/graph/badge.svg)](https://codecov.io/gh/Lexicoding-systems/Lexecon)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Test Coverage](https://img.shields.io/badge/coverage-69%25-yellow.svg)](https://github.com/Lexicoding-systems/Lexecon)
[![GitHub stars](https://img.shields.io/github/stars/Lexicoding-systems/Lexecon?style=social)](https://github.com/Lexicoding-systems/Lexecon/stargazers)

**The universal governance protocol for autonomous systems**

*Enterprise-grade cryptographic governance for AI, finance, healthcare, automotive, and beyond.*

[Developer Dashboard](./launch_dashboard.sh) • [Quick Start](#quick-start) • [Features](#core-capabilities) • [Roadmap](#roadmap) • [Contributing](#contributing)

</div>

---

## 🎯 What is Lexecon?

Lexecon is a **universal governance protocol** that provides:

- **🔐 Cryptographically Auditable Decision-Making**: Every autonomous action is signed, hashed, and chain-linked
- **⚡ Runtime Policy Enforcement**: Deny-by-default gating with capability-based authorization
- **📋 Compliance Automation**: Built-in mappings for EU AI Act, MIFID II, HIPAA, SOC 2, GDPR, ISO 27001
- **🛡️ Enterprise Security**: RBAC, MFA, OIDC, rate limiting, digital signatures (Ed25519/RSA-4096)
- **🔗 Tamper-Evident Ledgers**: Hash-chained audit trails with integrity verification
- **🌐 Domain-Agnostic**: Works with AI, trading algorithms, autonomous vehicles, IoT, and more

Think of it as **blockchain-grade governance**—without the blockchain—for any autonomous system.

---

## 🚀 Why Lexecon?

### The Problem

Modern autonomous systems face critical governance challenges:

| Challenge | Impact | Regulatory Risk |
|-----------|--------|-----------------|
| **Uncontrolled Autonomous Actions** | Systems execute without oversight | High |
| **No Audit Trail** | Can't prove what decisions were made or why | Critical |
| **Compliance Burden** | Manual mapping to regulations (AI Act, MIFID II, HIPAA) | Very High |
| **Policy Drift** | Policies become outdated, inconsistent | Medium |
| **Prompt Injection / Rogue Actors** | Adversarial inputs bypass controls | High |

### The Solution

Lexecon provides **cryptographic proof of governance**:

```python
# Before Lexecon: Hope and pray
ai_agent.execute("delete_production_database")  # 😱
trading_algo.place_order(value=10000000)  # 😱

# With Lexecon: Cryptographically enforced
decision = governance.request_decision(
    actor="act_ai_agent:gpt4",
    action="database:delete",
    context={"environment": "production"}
)
# ❌ DENIED - Cryptographically signed audit trail created
```

---

## 🌐 Multi-Domain Governance

Lexecon is **evolving from AI governance to the universal governance protocol** for autonomous systems:

### Supported Governance Domains

| Domain | Use Cases | Regulations | Status |
|--------|-----------|-------------|--------|
| **🤖 AI/ML** | LLMs, autonomous agents, computer vision | EU AI Act, GDPR, SOC 2 | ✅ **Complete** (Phases 1-2) |
| **💰 Finance** | Algorithmic trading, risk management | MIFID II, Basel III, SOC 2 | 📋 Phase 4 |
| **🏥 Healthcare** | Diagnostic AI, patient data analysis | HIPAA, FDA 21 CFR Part 11 | 📋 Phase 4 |
| **🚗 Automotive** | Autonomous vehicles, advanced driver assistance | ISO 26262, UNECE WP.29 | 📋 Phase 4 |
| **📦 Supply Chain** | Logistics optimization, ESG tracking | ESG standards, conflict minerals | 🔮 Future |
| **⚡ Energy** | Smart grid management, predictive maintenance | NERC CIP, IEC 62351 | 🔮 Future |

**Key Insight**: The same governance primitives (decisions, policies, audit trails) work across *all* domains. Lexecon is the universal protocol layer.

[Read Multi-Domain Roadmap](./MULTI_DOMAIN_IMPLEMENTATION_ROADMAP.md)
[Read Universal Governance Vision](./MULTI_DOMAIN_GOVERNANCE_VISION.md)

---

## 💻 Developer Workspace & IP Vault

### Personal Engineering Dashboard

Launch your secure workspace to track development and protect intellectual property:

```bash
./launch_dashboard.sh
```

**Features**:
- 🔐 **Cryptographic IP Registry**: 5 patentable innovations documented with timestamps
- 📈 **Development Timeline**: Complete history from Jan 1, 2026 inception
- 📊 **Project Metrics**: Real-time tracking of coverage, tests, progress
- 📋 **Tamper-Evident Audit Trail**: Every action signed and logged
- 🎯 **Sprint Planning**: Current task tracking and goal management

### Personal Vault

Secure vault for engineering notes, code snippets, and IP protection:

```bash
./launch_vault.sh
```

[Read Dashboard Guide](./DASHBOARD_GUIDE.md) | [Read Vault Quickstart](./VAULT_QUICKSTART.md)

---

## 🏆 Building the Universal Standard

Lexecon is positioned to become the **HTTP of governance**—the unavoidable standard for autonomous systems.

### Our Vision

**From AI governance tool → Universal governance protocol → Industry standard**

### Strategic Pillars

1. **📐 Formal Protocol Specification** (In Progress)
   - Standardized governance primitives
   - Technology Compatibility Kit (TCK)
   - Reference implementations (Python, Rust, Go)

2. **🏛️ Standards Body Engagement** (Ongoing)
   - **NIST AI RMF**: Reference implementation
   - **IEEE**: Submit PAR for governance protocol standard
   - **OWASP**: Primary defense for Top 10 LLM
   - **ISO**: Align with ISO 42001 (AI management systems)

3. **🌐 Multi-Domain Ecosystem** (Launching Phase 4)
   - Domain-specific plugins (finance, healthcare, automotive)
   - 50+ regulatory framework mappings
   - Governance Exchange (GEX) marketplace

4. **👥 Certified Developer Community**
   - Certified Lexecon Governance Engineer (LCGE)
   - Training programs and certifications
   - 10,000+ certified engineers goal

5. **🏢 Enterprise Alliance**
   - Fortune 500 founding members
   - Board seats and governance participation
   - Co-marketing and case studies

[Read Standard-Setting Strategy](./STANDARD_SETTING_STRATEGY.md)

---

## 🏗️ Core Capabilities

### 1. **Policy Engine** (`src/lexecon/policy/`)
Graph-based policy evaluation system.

**Features**:
- ✅ Declarative policy language (terms + relations)
- ✅ Compile-time validation and runtime evaluation
- ✅ Policy versioning with hash pinning
- ✅ Deterministic evaluation (no LLM in the loop)

**Example**:
```python
from lexecon.policy import PolicyEngine, PolicyTerm, PolicyRelation

engine = PolicyEngine()

# Define terms (nodes in policy graph)
read_action = PolicyTerm.create_action("read", "Read Data")
user_actor = PolicyTerm.create_actor("user", "Standard User")

# Define relations (edges in policy graph)
engine.add_relation(PolicyRelation.permits(user_actor, read_action))

# Evaluate
result = engine.evaluate(actor="user", action="read")  # ✅ Permitted
```

### 2. **Decision Service** (`src/lexecon/decision/`)
Real-time policy evaluation and capability token issuance.

**Flow**:
```
Request → Decision Service → Policy Evaluation → Token Issuance → Ledger Recording
```

### 3. **Capability System** (`src/lexecon/capability/`)
Short-lived authorization tokens for approved actions.

**Features**:
- ✅ Scoped permissions (single action or resource)
- ✅ Time-limited validity (configurable TTL)
- ✅ Policy version binding
- ✅ Cryptographic verification

### 4. **Cryptographic Ledger** (`src/lexecon/ledger/`)
Tamper-evident audit log using hash chaining.

**Properties**:
- 🔒 **Tamper-Evident**: Any modification breaks the chain
- 🔍 **Auditable**: Complete forensic trail
- ⚡ **Fast**: 10,000+ entries/second
- 📦 **Portable**: Export to JSON/SQLite

### 5. **Enterprise Security** (`src/lexecon/security/`)
Comprehensive security infrastructure.

**Components**:
- ✅ **Authentication**: RBAC with hierarchical permissions
- ✅ **Digital Signatures**: Ed25519 (speed) + RSA-4096 (compliance)
- ✅ **MFA**: TOTP and SMS support
- ✅ **OIDC**: Enterprise SSO integration
- ✅ **Rate Limiting**: Configurable policies with middleware
- ✅ **Audit Logging**: Comprehensive security event tracking
- ✅ **Secrets Management**: Encrypted storage and rotation
- ✅ **Database Encryption**: Transparent data encryption

### 6. **Compliance Mapping** (`src/lexecon/compliance_mapping/`)
Automated mapping of governance primitives to regulatory controls.

**Supported Frameworks**:
- **EU AI Act** (Articles 9-17, 72)
- **GDPR** (Articles 5, 22, 25, 32, 35)
- **SOC 2** (CC1-CC9, Trust Service Criteria)
- **ISO 27001** (Controls A.5-A.18)
- **HIPAA** (Privacy & Security Rules)
- **MIFID II** (Financial instruments)

### 7. **Multi-Domain Adapters**
Plug-and-play adapters for different autonomous systems.

**Available**:
- 🤖 **LangChain**: Automatic tool call interception
- 🤖 **OpenAI**: Function calling integration
- 🤖 **Anthropic**: Tool use integration
- ☁️ **AWS Bedrock**: Cloud model governance
- ☁️ **Azure OpenAI**: Enterprise model deployment

---

## 📊 Current Status

**Phase 3: Advanced Compliance** 🚧 **IN PROGRESS** (80% → 100% by Jan 31)

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| **Test Coverage** | 69% | 80%+ | 🚧 In Progress |
| **Tests Passing** | 824 / 824 | 824+ | ✅ Perfect |
| **Phase 3 Complete** | 80% | 100% | 🚧 On Track |
| **API Endpoints** | 30+ | 35+ | ✅ Complete |
| **Documentation** | 85KB | 100KB+ | ✅ Complete |

### Sprint Focus (Week of Jan 13-17)
1. **Automated Compliance Reporting**: PDF/XBRL export
2. **Real-Time Dashboards**: WebSocket integration
3. **Test Coverage**: 69% → 80%+
4. **Security Tests**: API hardening

[View Detailed Task List](./TASKS_NEXT_2_WEEKS.md)

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/Lexicoding-systems/Lexecon.git
cd Lexecon

# Install with dev dependencies
pip install -e ".[dev]"

# Verify installation
lexecon --version
lexecon doctor
```

### 1. Launch Developer Dashboard

```bash
./launch_dashboard.sh
# Opens: http://localhost:8002/ENGINEER_DASHBOARD.html
```

### 2. Start the API Server

```bash
lexecon serve
# Server: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 3. Make Your First Decision

```bash
# CLI
lexecon decision request \
  --actor "ai_agent:research_assistant" \
  --action "web_search" \
  --context '{"purpose": "research"}'
```

```python
# Python
import requests

response = requests.post("http://localhost:8000/decisions/request", json={
    "actor": "act_human_user:alice",
    "action": "database:read",
    "context": {"environment": "staging"}
})

decision = response.json()
print(f"Decision: {decision['outcome']}")  # "allowed" or "denied"
print(f"Reason: {decision['reason']}")
```

### 4. Verify Ledger Integrity

```bash
lexecon audit verify
# ✅ Ledger integrity verified
# ✅ 1,234 entries checked
# ✅ Chain intact from genesis to head
```

---

## 📚 Documentation

### Technical Documentation
- **[Technical Deep Dive](./TECHNICAL_DEEP_DIVE_ANALYSIS.md)**: Architecture & codebase analysis (19KB)
- **[Multi-Domain Implementation Roadmap](./MULTI_DOMAIN_IMPLEMENTATION_ROADMAP.md)**: Path to universal protocol
- **[Governance Vision](./MULTI_DOMAIN_GOVERNANCE_VISION.md)**: Long-term strategy

### Developer Resources
- **[Personal Engineer Dashboard](./PERSONAL_ENGINEER_DASHBOARD.md)**: Workspace specification (30KB)
- **[Dashboard Guide](./DASHBOARD_GUIDE.md)**: Using the developer dashboard (16KB)
- **[Vault Quickstart](./VAULT_QUICKSTART.md)**: IP protection with personal vault
- **[Task Planning](./TASKS_NEXT_2_WEEKS.md)**: Current sprint tasks (15KB)

### Strategic Documents
- **[Standard-Setting Strategy](./STANDARD_SETTING_STRATEGY.md)**: Roadmap to become universal standard (21KB)
- **[Pitch Materials](./PITCH_DECK.md)**: Investor presentation deck
- **[Investor FAQ](./INVESTOR_FAQ.md)**: Frequently asked questions

Total Documentation: **~150KB** of comprehensive guides

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/Lexicoding-systems/Lexecon.git
cd Lexecon

# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linters
black src/ tests/
ruff check src/ tests/

# Run type checker
mypy src/
```

### Areas for Contribution

- 🧪 **Test coverage**: Help us reach 80%+ (currently 69%)
- 🌍 **Multi-domain**: Build adapters for new domains
- 📚 **Documentation**: Examples and tutorials
- 🔌 **Model integrations**: New AI model adapters
- 🚀 **Performance**: Optimizations for 10K+ req/s

---

## 🌟 Why Choose Lexecon?

| Feature | Lexecon | Traditional Approaches |
|---------|---------|----------------------|
| **Audit Trail** | Cryptographically tamper-proof | Mutable logs, easy to alter |
| **Policy Enforcement** | Runtime gating, deny-by-default | Post-hoc analysis, hope-based |
| **Compliance** | Automated mapping, multi-framework | Manual processes, expensive |
| **Transparency** | Every decision explained | Black-box decisions |
| **Security** | Ed25519 + RSA-4096 + MFA + OIDC | Often none |
| **Standard** | Universal protocol positioning | Proprietary solutions |
| **Ecosystem** | GEX marketplace, certification | Isolated tools |

---

## 📞 Support & Community

- **Documentation**: [https://lexecon.readthedocs.io](https://lexecon.readthedocs.io) (coming soon)
- **Issues**: [GitHub Issues](https://github.com/Lexicoding-systems/Lexecon/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Lexicoding-systems/Lexecon/discussions)
- **Email**: [Jacobporter@lexicoding.tech](mailto:Jacobporter@lexicoding.tech)

---

<div align="center">

**Lexecon** - *Governance you can prove*

[![Star on GitHub](https://img.shields.io/github/stars/Lexicoding-systems/Lexecon?style=social)](https://github.com/Lexicoding-systems/Lexecon/stargazers)

[Get Started](#quick-start) • [View Roadmap](#roadmap) • [Contribute](#contributing)

</div>
