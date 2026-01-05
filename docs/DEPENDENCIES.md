# Dependencies

## Purpose

This document lists Lexecon's runtime and development dependencies. It serves as a lightweight Software Bill of Materials (SBOM) for security review and compliance purposes.

---

## Runtime Dependencies

### Core Dependencies

| Package | Version | Purpose | License |
|---------|---------|---------|---------|
| Python | >=3.8 | Runtime environment | PSF |
| FastAPI | >=0.104.0 | REST API framework | MIT |
| Pydantic | >=2.0.0 | Data validation | MIT |
| uvicorn | >=0.24.0 | ASGI server | BSD-3-Clause |

### Optional Dependencies

| Package | Version | Purpose | License |
|---------|---------|---------|---------|
| model-governance-pack | local | Canonical governance models | Apache-2.0 |

---

## Development Dependencies

### Testing

| Package | Version | Purpose | License |
|---------|---------|---------|---------|
| pytest | >=7.4.0 | Test framework | MIT |
| pytest-asyncio | >=0.21.0 | Async test support | Apache-2.0 |
| pytest-cov | >=4.1.0 | Coverage reporting | MIT |

### Code Quality

| Package | Version | Purpose | License |
|---------|---------|---------|---------|
| black | >=23.0.0 | Code formatting | MIT |
| ruff | >=0.1.0 | Linting | MIT |
| mypy | >=1.5.0 | Type checking | MIT |

---

## Standard Library Usage

Lexecon makes extensive use of Python's standard library:

- `hashlib`: SHA-256 hashing for integrity verification
- `json`: JSON serialization/deserialization
- `datetime`: Timestamp handling
- `uuid`: Unique ID generation
- `typing`: Type annotations
- `pathlib`: File path operations
- `argparse`: CLI argument parsing

---

## Dependency Rationale

### FastAPI
- Industry-standard async REST framework
- Built-in OpenAPI documentation
- Excellent performance characteristics
- Strong type safety with Pydantic integration

### Pydantic v2
- Lossless binding to JSON schemas
- Runtime validation ensures contract compliance
- Performance improvements over v1
- Source of truth: `/model_governance_pack/schemas/*.json`

### Uvicorn
- High-performance ASGI server
- Production-ready
- Widely deployed and maintained

### Pytest
- De facto standard for Python testing
- Excellent fixture system
- Strong async support
- Comprehensive plugin ecosystem

---

## Security Considerations

### Dependency Updates

**Current Policy**: Manual dependency updates reviewed before application.

**Recommendation** for production:
1. Monitor security advisories for all dependencies
2. Subscribe to GitHub security alerts
3. Use automated scanning (e.g., Dependabot, Snyk)
4. Test updates in staging before production deployment
5. Maintain update log for audit purposes

### Known Vulnerabilities

As of 2026-01-04:
- No known critical vulnerabilities in runtime dependencies
- Regular scanning recommended

### Supply Chain Verification

**Current**:
- Dependencies installed from PyPI
- No signature verification

**Recommended for production**:
- Pin exact dependency versions
- Verify package hashes
- Use private PyPI mirror for controlled updates
- Consider using pip-compile for lock files

---

## Installation

### Minimal Installation (Runtime Only)

```bash
pip install fastapi uvicorn pydantic
```

### Development Installation (All Dependencies)

```bash
# Clone repository
git clone https://github.com/Lexicoding-systems/Lexecon.git
cd Lexecon

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Dependency Lock File

**Recommendation**: Generate and commit a lock file for reproducible builds:

```bash
# Generate requirements lock file
pip-compile pyproject.toml -o requirements.txt

# Install from lock file
pip install -r requirements.txt
```

---

## Dependency Graph

```
lexecon
├── fastapi (REST API)
│   ├── pydantic (validation)
│   ├── starlette (ASGI framework)
│   └── typing-extensions (type hints)
├── uvicorn (ASGI server)
│   ├── click (CLI)
│   ├── h11 (HTTP/1.1)
│   └── watchfiles (dev auto-reload)
└── model-governance-pack (local)
    └── pydantic (validation)
```

---

## Transitive Dependencies

Lexecon has minimal transitive dependencies due to careful selection of core packages. FastAPI and Pydantic are the primary sources of transitive dependencies.

**Key Transitive Dependencies**:
- `starlette`: ASGI framework (FastAPI dependency)
- `typing-extensions`: Backport of typing features
- `anyio`: Async abstraction layer
- `sniffio`: Async library detection

---

## Update Policy

### Major Version Updates

**Process**:
1. Review changelog for breaking changes
2. Update code to accommodate API changes
3. Run full test suite
4. Update documentation if API changes affect users
5. Create migration guide if necessary

**Timeline**: Evaluate major updates quarterly.

### Minor/Patch Updates

**Process**:
1. Review changelog for bug fixes and features
2. Run test suite
3. Deploy to staging
4. Monitor for regressions

**Timeline**: Apply security patches within 1 week; other updates monthly.

---

## Alternative Implementations

### Minimal Dependency Version

For environments with strict dependency constraints, Lexecon core can run with only:
- Python 3.8+ standard library
- Pydantic for validation

This excludes:
- REST API (FastAPI/Uvicorn)
- Development tools (pytest, coverage)
- CLI enhancements

---

## Compliance Notes

### License Compatibility

All dependencies use permissive licenses (MIT, BSD, Apache-2.0, PSF) compatible with Apache-2.0 project license.

### SBOM Generation

For formal SBOM generation (e.g., SPDX, CycloneDX):

```bash
# Install SBOM tool
pip install cyclonedx-bom

# Generate CycloneDX SBOM
cyclonedx-py -o sbom.json

# Or use pip-licenses
pip install pip-licenses
pip-licenses --format=json --output-file=licenses.json
```

---

## Contact

For dependency-related questions:
- Security issues: See `docs/SECURITY_POSTURE.md`
- General questions: https://github.com/Lexicoding-systems/Lexecon/issues

---

## Version History

- **2026-01-04**: Initial dependency documentation
  - Listed core runtime dependencies (FastAPI, Pydantic, Uvicorn)
  - Listed development dependencies (pytest, black, ruff, mypy)
  - Documented update policy and security considerations
