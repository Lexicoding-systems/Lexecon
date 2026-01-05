# API Versioning & Stability Policy

## Purpose

This document defines the versioning, compatibility, and deprecation policies for Lexecon's REST API. It ensures predictable API evolution while enabling necessary improvements.

---

## Versioning Scheme

Lexecon follows **semantic versioning (semver)** for API versions: `MAJOR.MINOR.PATCH`

### Version Components

**MAJOR**: Breaking changes to API contracts
- Changed endpoint paths
- Removed required fields
- Changed field types or constraints
- Removed endpoints
- Changed error response structure

**MINOR**: Backward-compatible additions
- New endpoints
- New optional fields in requests/responses
- New enum values
- New query parameters (optional)
- Expanded response data (additional fields)

**PATCH**: Bug fixes and clarifications
- Documentation corrections
- Bug fixes that restore intended behavior
- Internal refactoring with no API impact
- Performance improvements

---

## Current API Version

**Version**: `v1.0.0`

**Status**: Active development (pre-stable)

**Stability Commitment**: Until version `v1.0.0` is formally released, MINOR version increments may include breaking changes. This allows for rapid iteration during initial development.

**Path to Stability**: Version `v1.0.0` will be released when:
1. All Phase 1-11 deliverables complete
2. API contracts stable for 2 consecutive months
3. At least 1 production deployment validated
4. Security assessment completed

---

## API Contract Source of Truth

API contracts are derived from canonical JSON schemas:

```
/model_governance_pack/schemas/*.json  ← SOURCE OF TRUTH
         ↓
/model_governance_pack/models/*.py     ← Pydantic bindings (validated lossless)
         ↓
/src/lexecon/api/server.py             ← FastAPI endpoints (use Pydantic models)
```

### Contract Validation

Changes to API contracts MUST:
1. Update JSON schema first
2. Regenerate/update Pydantic models
3. Verify lossless binding (no information loss)
4. Update endpoint implementations
5. Add/update tests
6. Update documentation

---

## Backward Compatibility Rules

### Breaking Changes (Require MAJOR Version Increment)

❌ **Prohibited in MINOR/PATCH releases**:
- Removing endpoints
- Removing required fields from requests
- Removing fields from responses (even optional ones)
- Changing field types (e.g., string → number)
- Changing field constraints (e.g., max_length: 100 → 50)
- Renaming fields
- Changing enum values
- Changing error status codes for existing errors
- Changing authentication/authorization requirements

### Allowed Changes (MINOR Version)

✅ **Permitted in MINOR releases**:
- Adding new endpoints
- Adding optional fields to requests
- Adding new fields to responses
- Adding new enum values (if additive)
- Adding new query parameters (optional)
- Expanding allowed value ranges (e.g., max_length: 50 → 100)
- Adding new optional headers

### Allowed Changes (PATCH Version)

✅ **Permitted in PATCH releases**:
- Bug fixes that restore documented behavior
- Performance improvements with no API impact
- Documentation clarifications
- Internal refactoring
- Dependency updates (if no API impact)

---

## Deprecation Policy

### Deprecation Process

When an API feature must be removed or changed incompatibly:

1. **Announce Deprecation** (Version N):
   - Add deprecation notice to API documentation
   - Return `Deprecated: true` header on affected endpoints
   - Provide migration guide with alternative

2. **Deprecation Period** (Versions N+1, N+2):
   - Feature remains functional but marked deprecated
   - Warnings logged when deprecated features used
   - Migration guide actively promoted

3. **Removal** (Version N+3, MAJOR increment):
   - Feature removed in next MAJOR version
   - Breaking change documented in changelog
   - Migration guide required before release

### Minimum Deprecation Timeline

- **Endpoints**: 2 MINOR versions or 6 months (whichever is longer)
- **Fields**: 2 MINOR versions or 6 months
- **Enum values**: 1 MINOR version or 3 months (if rarely used)
- **Query parameters**: 2 MINOR versions or 6 months

### Example Deprecation

```
v1.5.0: Announce deprecation of /legacy/risk-assess
        Recommend /risk/assess instead
        Both endpoints functional

v1.6.0: /legacy/risk-assess still works, warnings logged
        Migration guide published

v1.7.0: /legacy/risk-assess still works, deprecation reinforced

v2.0.0: /legacy/risk-assess removed
        Only /risk/assess available
```

---

## API Evolution Examples

### Adding Optional Field (MINOR)

**Before (v1.2.0)**:
```json
POST /risk/assess
{
  "decision_id": "dec_001",
  "risk_factors": {...}
}
```

**After (v1.3.0)**:
```json
POST /risk/assess
{
  "decision_id": "dec_001",
  "risk_factors": {...},
  "metadata": {          ← NEW: optional field
    "source": "api_v2"
  }
}
```

✅ **Backward compatible**: Clients not sending `metadata` still work.

---

### Adding Response Field (MINOR)

**Before (v1.2.0)**:
```json
GET /risk/{risk_id}
Response:
{
  "risk_id": "risk_001",
  "aggregate_risk_score": 0.75
}
```

**After (v1.3.0)**:
```json
GET /risk/{risk_id}
Response:
{
  "risk_id": "risk_001",
  "aggregate_risk_score": 0.75,
  "recommendation": "ESCALATE"  ← NEW: additional field
}
```

✅ **Backward compatible**: Clients ignoring `recommendation` still work.

---

### Changing Field Type (MAJOR)

**Before (v1.x)**:
```json
{
  "escalation_level": "L2"  ← string
}
```

**After (v2.0.0)**:
```json
{
  "escalation_level": 2     ← number
}
```

❌ **Breaking change**: Requires MAJOR version increment.

---

## Versioning in API Paths

### Current Approach (Single Version)

All endpoints currently at implicit `v1`:
```
POST /risk/assess
POST /escalations/
GET /audit-export/exports
```

### Future Approach (Explicit Versioning)

When multiple versions must coexist:
```
POST /v1/risk/assess
POST /v2/risk/assess  ← new version
```

Version included in path, not header or query parameter.

---

## Client Compatibility Expectations

### What Clients Should Expect

✅ **Safe Assumptions**:
- Existing endpoints will not be removed without deprecation notice
- Existing required fields will not be removed
- Existing field types will not change (within MAJOR version)
- New optional fields may appear in responses

❌ **Unsafe Assumptions**:
- Response will never include additional fields (must ignore unknown fields)
- Field order will remain constant (JSON is unordered)
- Error messages will remain exactly the same
- Internal IDs will follow exact format forever (only guarantee pattern compliance)

### Client Implementation Guidelines

**Robust Clients Should**:
1. Ignore unknown fields in responses
2. Not depend on field order
3. Validate required fields only
4. Handle new enum values gracefully (unknown value handling)
5. Parse error responses by status code, not message text

**Example Robust Parsing**:
```python
# ✅ Good: Ignore unknown fields
response = {"risk_id": "risk_001", "new_field": "value"}
risk_id = response["risk_id"]  # Works even with new fields

# ❌ Bad: Strict parsing
assert set(response.keys()) == {"risk_id"}  # Breaks when new field added
```

---

## Schema Change Process

### 1. Propose Change
- Open issue describing change and rationale
- Indicate MAJOR/MINOR/PATCH classification
- Provide migration guide if breaking

### 2. Update Schema
- Modify JSON schema in `/model_governance_pack/schemas/`
- Ensure schema is valid JSON Schema Draft 7
- Add version comment or changelog entry

### 3. Update Models
- Regenerate or manually update Pydantic models
- Verify lossless binding (round-trip test: schema → model → dict → schema)
- Run model validation tests

### 4. Update Endpoints
- Modify FastAPI endpoint implementations
- Update request/response models
- Add/update endpoint tests

### 5. Update Documentation
- Update API documentation
- Update changelog
- Add migration guide if breaking
- Update version in relevant files

### 6. Release
- Increment version according to semver
- Tag release in version control
- Publish changelog
- Notify API consumers (if applicable)

---

## Error Response Stability

### Error Response Format (Stable)

```json
{
  "error": "Error message",
  "detail": "Additional context",
  "status_code": 400
}
```

This format is **stable** and will not change within MAJOR version.

### Status Codes (Stable)

| Code | Meaning | Stability |
|------|---------|-----------|
| 200 | Success | Stable |
| 201 | Created | Stable |
| 400 | Bad Request (validation error) | Stable |
| 401 | Unauthorized | Stable |
| 403 | Forbidden | Stable |
| 404 | Not Found | Stable |
| 409 | Conflict | Stable |
| 422 | Unprocessable Entity (schema violation) | Stable |
| 500 | Internal Server Error | Stable |

**Guarantee**: Status codes for existing error conditions will not change within MAJOR version.

### Error Messages (Unstable)

⚠ **Warning**: Error message text (`error` and `detail` fields) may change in MINOR/PATCH releases. Clients should not parse error messages; use status codes and error types.

---

## Webhook Stability

Webhook payloads follow the same versioning policy as API responses:
- Schema is source of truth
- New fields may be added (MINOR)
- Existing fields will not be removed (requires MAJOR)
- Webhook consumers must ignore unknown fields

---

## Testing & Validation

### Contract Tests

API contract tests MUST verify:
- Request validation (all required fields, type correctness)
- Response structure (presence of documented fields)
- Error responses (correct status codes)
- Schema compliance (validate against JSON schema)

### Compatibility Tests

Before releasing MINOR/PATCH version:
- Run full test suite from previous MINOR version
- Verify no breaking changes detected
- Test with sample client code from previous version

---

## Version Lifecycle

### Development → Stable

**Pre-v1.0.0**: Rapid iteration, breaking changes in MINOR versions allowed.

**v1.0.0+**: Strict semver adherence, breaking changes only in MAJOR.

### Support Policy

**Active Versions**: Latest MAJOR.MINOR receives full support (bug fixes, security updates).

**Previous MAJOR**: Supported for 12 months after new MAJOR release (security fixes only).

**Older MAJOR**: Unsupported; users encouraged to migrate.

---

## Questions & Clarifications

**Q: What if a bug fix requires breaking change?**
A: If restoring documented behavior, PATCH is appropriate. If changing documented behavior, MAJOR is required.

**Q: Can I add a required field?**
A: No, not in MINOR/PATCH. Adding required fields is a MAJOR breaking change. Add as optional first, then require in next MAJOR.

**Q: Can I change an enum by adding a value?**
A: Yes, in MINOR. But document that clients should handle unknown enum values gracefully.

**Q: What if schema and API disagree?**
A: Schema is source of truth. API must be updated to match schema.

---

## Changelog Location

API changes documented in:
- `CHANGELOG.md` (root of repository)
- Release notes (GitHub releases)
- API documentation (inline version notes)

---

## Version History

- **v0.1.0** (2026-01-04): Initial API versioning policy
  - Defined semver scheme
  - Established schema-first approach
  - Documented deprecation policy
