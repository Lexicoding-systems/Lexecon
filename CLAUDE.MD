# CLAUDE.MD - Development Guide for AI Assistants

## Project Overview

**Lexecon** is a cryptographic governance protocol for AI systems providing enterprise-grade safety, compliance, and auditability. It's essentially "blockchain-grade governance without the blockchain" - using hash chains, digital signatures, and policy enforcement to create tamper-proof audit trails for AI decision-making.

### Core Purpose
- **Cryptographic Auditability**: Every AI action is signed, hashed, and chain-linked
- **Runtime Policy Enforcement**: Deny-by-default gating with capability-based authorization
- **Compliance Automation**: Built-in mappings for EU AI Act, GDPR, SOC 2, ISO 27001
- **Enterprise Security**: RBAC, digital signatures (Ed25519/RSA-4096), audit logging
- **Tamper-Evident Ledgers**: Hash-chained audit trails with integrity verification

## Project Structure

```
/home/user/Lexecon/
├── src/lexecon/              # Main source code
│   ├── policy/               # Policy engine (terms, relations, evaluation)
│   ├── decision/             # Decision service (policy evaluation & capability tokens)
│   ├── capability/           # Capability token system (scoped, time-limited auth)
│   ├── ledger/               # Cryptographic hash-chained ledger
│   ├── identity/             # Cryptographic signing (Ed25519)
│   ├── evidence/             # Immutable artifact storage
│   ├── security/             # Auth, RBAC, signatures, audit
│   ├── compliance/           # EU AI Act implementation (Articles 11, 12, 14)
│   ├── compliance_mapping/   # Regulatory framework mappings
│   ├── risk/                 # Risk assessment and tracking
│   ├── escalation/           # Human-in-the-loop oversight
│   ├── override/             # Executive override management
│   ├── responsibility/       # Chain of custody tracking
│   ├── audit_export/         # Compliance report generation
│   ├── observability/        # Logging, metrics, tracing, health checks
│   ├── storage/              # Database abstraction (SQLite/PostgreSQL)
│   ├── api/                  # FastAPI REST endpoints (30+)
│   ├── cli/                  # Command-line interface
│   └── tools/                # Utility functions
├── tests/                    # Test suite (824 tests, 69% coverage)
├── docs/                     # Documentation
├── examples/                 # Usage examples
├── deployment/               # Docker, Kubernetes configs
└── scripts/                  # Build and utility scripts
```

## Architecture & Key Concepts

### 1. Policy Engine (`src/lexecon/policy/`)
- **Terms**: Nodes in policy graph (actors, actions, resources, data classes)
- **Relations**: Edges defining permissions (permits, forbids, requires, implies)
- **Evaluation**: Deterministic graph traversal (no LLM in the loop)
- **Versioning**: Hash pinning for policy reproducibility

### 2. Decision Flow
```
Model Request → Decision Service → Policy Evaluation → Capability Token → Ledger Entry
```

### 3. Capability System
- Short-lived authorization tokens (configurable TTL)
- Scoped to single action/resource
- Bound to specific policy version
- Format: `cap_<id>_<action>_<scope>_exp<timestamp>`

### 4. Cryptographic Ledger
- Hash-chained entries (SHA-256)
- Ed25519 signatures on all events
- Tamper-evident: any modification breaks the chain
- Fast: 10,000+ entries/second

### 5. Compliance Mapping
Automatic mapping of governance primitives to regulatory controls:
- EU AI Act (Articles 9-17, 72)
- GDPR (Articles 5, 22, 25, 32, 35)
- SOC 2 (CC1-CC9)
- ISO 27001 (Controls A.5-A.18)

## Development Standards

### Code Style
- **Python Version**: 3.8+ (for maximum compatibility)
- **Formatter**: Black (line length: 100)
- **Linter**: Ruff + Flake8 (strict configuration)
- **Type Checker**: mypy (strict mode: `disallow_untyped_defs = true`)
- **Import Sorting**: isort (black profile)
- **Docstrings**: Google style (enforced by interrogate, 80% minimum)

### Testing Requirements
- **Framework**: pytest with pytest-cov and pytest-asyncio
- **Current Coverage**: 69% (target: 80%+)
- **Test Location**: `tests/` mirrors `src/lexecon/` structure
- **Coverage Command**: `pytest --cov=src/lexecon --cov-report=html`
- **Run Tests**: `pytest` or `make test`

### Modules at 100% Coverage
- `observability/logging.py`
- `observability/metrics.py`
- `observability/health.py`
- `evidence/append_only_store.py`
- `compliance_mapping/service.py`
- `policy/terms.py`
- `ledger/chain.py`
- `identity/signing.py`
- `capability/tokens.py`

### Pre-commit Hooks
The project uses pre-commit hooks (`.pre-commit-config.yaml`):
- black (formatting)
- ruff (linting)
- mypy (type checking)
- bandit (security scanning)
- secrets detection

## Common Development Workflows

### Setting Up Development Environment
```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run initial checks
make lint
make test
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/lexecon --cov-report=html

# Run specific test file
pytest tests/test_policy/test_engine.py

# Run specific test
pytest tests/test_policy/test_engine.py::test_policy_evaluation
```

### Code Quality Checks
```bash
# Format code
black src/ tests/

# Check linting
ruff check src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/

# Type checking
mypy src/

# Security scanning
bandit -r src/

# All quality checks
make lint
```

### Running the API Server
```bash
# Using CLI
lexecon serve

# Direct with uvicorn
uvicorn lexecon.api.main:app --reload

# With Docker
docker-compose up

# API docs available at: http://localhost:8000/docs
```

### CLI Commands
```bash
lexecon --version              # Show version
lexecon doctor                 # System diagnostics
lexecon init                   # Initialize configuration
lexecon policy validate        # Validate policy definitions
lexecon audit verify           # Verify ledger integrity
lexecon export audit           # Export audit reports
```

## Important Patterns & Conventions

### 1. Module Structure
Each module typically contains:
- `models.py` or `types.py`: Pydantic models and type definitions
- `service.py`: Main business logic class
- `storage.py`: Persistence layer (if needed)
- `__init__.py`: Public API exports

### 2. Error Handling
- Use custom exceptions from `lexecon.exceptions`
- Always log errors with context
- Include detailed error messages for auditability

### 3. Security Practices
- Never log sensitive data (keys, tokens, PII)
- Always validate inputs (Pydantic models)
- Use Ed25519 for signatures (fast, secure)
- Use RSA-4096 for compliance artifacts (regulatory requirement)
- Time-limit all capabilities (default: 5 minutes)

### 4. Audit Trail Requirements
Every governance action must:
1. Be recorded in the ledger
2. Have a digital signature
3. Include context for explainability
4. Be tamper-evident (hash-chained)

### 5. Pydantic Models
- All data structures use Pydantic v2
- Use `Field()` for validation and documentation
- Include examples in schema
- Use strict typing (no `Any` unless necessary)

### 6. API Endpoints
- Follow REST conventions
- Use proper HTTP status codes
- Include OpenAPI documentation
- Version endpoints when breaking changes occur
- All endpoints return JSON

## Key Files & Locations

### Configuration
- `pyproject.toml`: Project metadata, dependencies, tool configs
- `.env.example`: Environment variable template
- `docker-compose.yml`: Local development stack

### Documentation
- `README.md`: User-facing documentation (comprehensive)
- `CONTRIBUTING.md`: Contribution guidelines
- `SECURITY.md`: Security policies and reporting
- `ENTERPRISE_SECURITY_IMPLEMENTATION.md`: Enterprise security details

### Security
- `lexecon_keys/`: Cryptographic keys (gitignored)
- `.secrets.baseline`: Baseline for secret detection
- `setup_security.py`: Security initialization script

### Testing
- `tests/`: Mirror of `src/lexecon/` structure
- `tests/conftest.py`: Pytest fixtures (if exists)

### CI/CD
- `.github/workflows/ci.yml`: Main CI pipeline
- `.github/workflows/codeql.yml`: Security scanning

## Dependencies

### Core Runtime
- `fastapi>=0.109.0`: REST API framework
- `uvicorn[standard]>=0.27.0`: ASGI server
- `pydantic>=2.5.0`: Data validation
- `cryptography>=42.0.0`: Ed25519, RSA, SHA-256
- `click>=8.1.0`: CLI framework
- `pyyaml>=6.0`: Configuration files
- `requests>=2.31.0`: HTTP client

### Development Only
- `pytest`, `pytest-cov`, `pytest-asyncio`: Testing
- `black`, `ruff`, `flake8`: Code quality
- `mypy`: Type checking
- `bandit`: Security scanning
- `pre-commit`: Git hooks

## Testing Philosophy

### What to Test
1. **Policy evaluation logic**: Ensure correct permit/deny decisions
2. **Hash chain integrity**: Verify ledger tamper-evidence
3. **Signature verification**: Validate cryptographic operations
4. **Capability token lifecycle**: Minting, validation, expiration
5. **Compliance mappings**: Correct regulatory control associations
6. **API endpoints**: Request/response validation
7. **Error handling**: Edge cases and failure modes

### What NOT to Mock
- Cryptographic operations (test real Ed25519/SHA-256)
- Hash chain operations (test actual integrity)
- Policy evaluation (test deterministic logic)

### Use Fixtures For
- Test databases (SQLite in-memory)
- Sample policies and actors
- Mock external services (email, notifications)

## Common Issues & Solutions

### Issue: Import errors
**Solution**: Ensure you installed with `pip install -e ".[dev]"` from project root

### Issue: Tests failing with missing dependencies
**Solution**: Install dev dependencies: `pip install -e ".[dev]"`

### Issue: Pre-commit hooks failing
**Solution**: Run `pre-commit run --all-files` and fix issues, then commit

### Issue: Type checking errors
**Solution**: Check `mypy` errors carefully - this project uses strict typing

### Issue: Coverage below target
**Solution**: Add tests for uncovered modules (prioritize core governance logic)

## Git Workflow

### Current Branch
- Development branch: `claude/update-claude-md-42r3R`
- Main branch: (use for PRs when instructed)

### Commit Message Style
Look at recent commits for style:
```bash
git log --oneline -10
```

Typical format:
```
type: Brief description

More detailed explanation if needed.
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `perf`, `ci`

### Before Committing
1. Run `make lint` or `black src/ tests/ && ruff check src/ tests/`
2. Run `pytest` to ensure tests pass
3. Update tests if adding features
4. Update documentation if changing APIs

### Push Workflow
```bash
# Push to feature branch
git push -u origin claude/update-claude-md-42r3R

# Retry logic for network failures (exponential backoff: 2s, 4s, 8s, 16s)
```

## Regulatory Compliance Context

### EU AI Act Focus
- **Article 11**: Technical documentation (automated generation)
- **Article 12**: Record-keeping (automatic logging of all decisions)
- **Article 14**: Human oversight (escalation workflows)
- **Article 72**: Penalties for non-compliance (up to €30M or 6% revenue)

### Compliance Strategy
1. **By Design**: Governance primitives map directly to regulatory requirements
2. **Automated**: No manual compliance documentation needed
3. **Provable**: Cryptographic proof of governance actions
4. **Exportable**: Generate audit reports in regulatory formats

## Performance Considerations

### Target Metrics
- Decision latency: <50ms (p99)
- Ledger writes: 10,000+ entries/second
- API throughput: 10,000+ req/s (future goal)
- Storage: Efficient (SQLite for dev, PostgreSQL for prod)

### Optimization Guidelines
- Use async/await for I/O operations
- Batch ledger writes when possible
- Cache policy evaluations (with version pinning)
- Index database queries appropriately

## Security Considerations

### Threat Model
- **Adversarial prompts**: Models trying to bypass policies
- **Privilege escalation**: Actors attempting unauthorized actions
- **Audit tampering**: Attempts to modify historical records
- **Key compromise**: Protecting signing keys

### Security Measures
- Deny-by-default policy enforcement
- Cryptographic signatures on all decisions
- Hash-chained audit log (tamper-evident)
- Time-limited capabilities (reduce attack window)
- RBAC with hierarchical permissions

## When Adding New Features

### Checklist
1. **Design**: Does it fit the architecture?
2. **Policy**: Does it need policy evaluation?
3. **Audit**: Should it be logged?
4. **Compliance**: Map to regulatory requirements?
5. **Tests**: Add comprehensive tests (aim for 80%+ coverage)
6. **Docs**: Update API docs, README, and this file
7. **Types**: Full type annotations
8. **Security**: Review for vulnerabilities

### API Endpoint Template
```python
@router.post("/endpoint", response_model=ResponseModel)
async def endpoint_name(
    request: RequestModel,
    # Dependency injection for services
) -> ResponseModel:
    """
    Brief description.

    Args:
        request: Description

    Returns:
        Description

    Raises:
        HTTPException: When and why
    """
    # Implementation
    pass
```

## Resources & References

### Internal Documentation
- README.md: Comprehensive user guide
- CONTRIBUTING.md: Contribution process
- SECURITY.md: Security policies
- API Docs: http://localhost:8000/docs (when server running)

### External Standards
- EU AI Act: https://artificialintelligenceact.eu/
- GDPR: https://gdpr.eu/
- SOC 2: https://www.aicpa.org/soc
- ISO 27001: https://www.iso.org/isoiec-27001-information-security.html

### Technical References
- Ed25519: https://ed25519.cr.yp.to/
- FastAPI: https://fastapi.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/

## Current Project Status

### Completed (Phase 1-2)
- ✅ Policy engine with graph evaluation
- ✅ Decision service with capability tokens
- ✅ Cryptographic ledger with hash chaining
- ✅ Evidence management
- ✅ Risk management
- ✅ Escalation workflows
- ✅ Override management
- ✅ REST API (30+ endpoints)
- ✅ CLI tooling

### In Progress (Phase 3)
- 🚧 Automated compliance reporting
- 🚧 Real-time compliance dashboards
- 🚧 Export to regulatory formats (ESEF, XBRL)

### Planned (Phase 4-6)
- 📋 PostgreSQL production backend
- 📋 Horizontal scaling
- 📋 LangChain/OpenAI/Anthropic integrations
- 📋 Prompt injection detection

### Test Coverage Progress
- Current: 69%
- Target: 80%+
- Focus areas for improvement: API endpoints, storage layer, CLI commands

## Questions to Ask When Uncertain

1. **Is this change breaking?** → Requires version bump or migration
2. **Does this need audit logging?** → Probably yes (we audit everything)
3. **What regulatory control does this satisfy?** → Check compliance mapping
4. **Is this properly typed?** → mypy should pass
5. **Are there tests?** → Required for all new code
6. **Is it secure?** → Review threat model
7. **Is it documented?** → Update API docs and README

## Contact & Support

- Repository: https://github.com/Lexicoding-systems/Lexecon
- Issues: https://github.com/Lexicoding-systems/Lexecon/issues
- Email: Jacobporter@lexicoding.tech

---

**Last Updated**: 2026-01-05
**Claude Instructions**: When working on this project, prioritize security, auditability, and compliance. Every decision should be logged. Every action should be policy-checked. Every change should be tested. This is governance infrastructure - correctness is critical.
