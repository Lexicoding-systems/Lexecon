# Audit Packet Specification

## Canonical Definition

An **Audit Packet** is a self-contained, cryptographically-verifiable bundle of governance evidence that captures the complete decision history, risk assessments, interventions, and compliance mappings for a defined scope and time period.

Audit Packets are the atomic unit of regulatory disclosure. They are designed to be:
- **Complete**: All referenced artifacts are included or have verifiable external references
- **Deterministic**: The same inputs produce byte-identical outputs
- **Immutable**: Content cannot be modified after generation without detection
- **Self-describing**: Metadata explains structure without external documentation

---

## Packet Structure

### Top-Level Schema

```
AuditPacket/
├── manifest.json           # Packet metadata and content index
├── checksum.sha256         # Root hash of all contents
├── evidence/               # EvidenceArtifact bundles
│   ├── {artifact_id}.json
│   └── {artifact_id}.json
├── decisions/              # Decision log entries
│   └── ledger_extract.json
├── risk/                   # Risk assessment records
│   └── assessments.json
├── escalations/            # Escalation records
│   └── escalations.json
├── overrides/              # Override records
│   └── overrides.json
├── compliance/             # Compliance mapping snapshots
│   ├── soc2.json
│   ├── iso27001.json
│   └── gdpr.json
└── statistics.json         # Aggregate counts and coverage metrics
```

### Manifest Schema

```json
{
  "packet_version": "1.0.0",
  "export_id": "exp_{unique_id}",
  "generated_at": "2026-01-04T12:00:00+00:00",
  "generator": {
    "system": "lexecon",
    "version": "0.1.0",
    "service": "AuditExportService"
  },
  "scope": {
    "type": "all | risk_only | escalation_only | ...",
    "start_date": "ISO8601 | null",
    "end_date": "ISO8601 | null",
    "include_deleted": false
  },
  "request": {
    "requester": "actor_id",
    "purpose": "stated_purpose",
    "requested_at": "ISO8601"
  },
  "contents": {
    "evidence_count": 42,
    "decision_count": 156,
    "risk_count": 23,
    "escalation_count": 8,
    "override_count": 3,
    "frameworks_included": ["soc2", "iso27001", "gdpr"]
  },
  "integrity": {
    "algorithm": "SHA-256",
    "root_checksum": "abc123...",
    "artifact_checksums": {
      "{artifact_id}": "def456...",
      "...": "..."
    }
  }
}
```

---

## Required Contents

### Mandatory Sections

Every Audit Packet MUST include:

| Section | Description | Empty Allowed |
|---------|-------------|---------------|
| `manifest.json` | Packet metadata | No |
| `checksum.sha256` | Root integrity hash | No |
| `statistics.json` | Aggregate metrics | No |

### Conditional Sections

Sections included based on scope and data availability:

| Section | Condition | Empty Representation |
|---------|-----------|---------------------|
| `evidence/` | Scope includes evidence | Empty directory |
| `decisions/` | Scope includes decisions | `{"entries": []}` |
| `risk/` | Scope includes risk | `{"assessments": []}` |
| `escalations/` | Scope includes escalations | `{"escalations": []}` |
| `overrides/` | Scope includes overrides | `{"overrides": []}` |
| `compliance/` | Scope includes compliance | Empty directory |

### Statistics Schema

```json
{
  "total_risks": 0,
  "total_escalations": 0,
  "total_overrides": 0,
  "total_evidence": 0,
  "total_decisions": 0,
  "total_mappings": 0,
  "total_controls": 0,
  "frameworks_covered": [],
  "date_range": {
    "earliest": "ISO8601 | null",
    "latest": "ISO8601 | null"
  },
  "export_size_bytes": 0
}
```

---

## Determinism Guarantees

### Reproducibility Contract

Given identical inputs, the audit export system guarantees:

1. **Byte-identical JSON output** when using the same:
   - Export request parameters
   - Source data snapshot
   - Export format (JSON)

2. **Semantic equivalence** across formats:
   - JSON, CSV, Markdown, HTML contain the same information
   - Only presentation differs

### Ordering Rules

To ensure determinism:

- **Evidence artifacts**: Ordered by `artifact_id` (lexicographic)
- **Decision entries**: Ordered by `timestamp` (chronological)
- **Risk assessments**: Ordered by `risk_id` (lexicographic)
- **Escalations**: Ordered by `created_at` (chronological)
- **Overrides**: Ordered by `timestamp` (chronological)
- **Compliance controls**: Ordered by `control_id` within each framework

### Timestamp Normalization

All timestamps in Audit Packets:
- Use ISO 8601 format
- Include timezone (UTC preferred)
- Normalize to microsecond precision
- Example: `2026-01-04T12:00:00.000000+00:00`

---

## Immutability Guarantees

### Hash Chain Integrity

```
┌─────────────────────────────────────────────────────────┐
│                    ROOT CHECKSUM                        │
│              SHA-256(manifest + all_content)            │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   evidence/   │   │  decisions/   │   │    risk/      │
│   checksum    │   │   checksum    │   │   checksum    │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  artifact_1   │   │   entry_1     │   │ assessment_1  │
│    hash       │   │    hash       │   │     hash      │
└───────────────┘   └───────────────┘   └───────────────┘
```

### Verification Algorithm

```python
def verify_packet_integrity(packet_path: str) -> bool:
    """Verify Audit Packet has not been tampered with."""

    # 1. Load manifest
    manifest = load_json(packet_path / "manifest.json")
    expected_root = manifest["integrity"]["root_checksum"]

    # 2. Compute actual checksum of all contents
    actual_root = compute_root_checksum(packet_path)

    # 3. Compare
    return constant_time_compare(expected_root, actual_root)

def compute_root_checksum(packet_path: str) -> str:
    """Compute deterministic root checksum."""
    hasher = hashlib.sha256()

    # Process files in deterministic order
    for file in sorted(packet_path.rglob("*")):
        if file.name != "checksum.sha256":
            hasher.update(file.read_bytes())

    return hasher.hexdigest()
```

### Tamper Detection

Any modification to packet contents results in:
1. Root checksum mismatch
2. Individual artifact checksum mismatch
3. Verification failure

---

## EvidenceArtifact Inclusion Rules

### Artifact Structure

Each EvidenceArtifact in `evidence/` follows:

```json
{
  "artifact_id": "evd_{type}_{unique_id}",
  "artifact_type": "decision_log | risk_assessment | escalation_record | override_record | signature",
  "sha256_hash": "computed_from_content",
  "created_at": "ISO8601",
  "source": "service_or_actor_id",
  "content_type": "application/json | text/plain | ...",
  "size_bytes": 1024,
  "related_decision_ids": ["dec_001", "dec_002"],
  "related_control_ids": ["CC6.1", "Art.32"],
  "is_immutable": true,
  "digital_signature": {
    "signer_id": "actor_id",
    "algorithm": "RSA-SHA256",
    "signature": "base64_encoded",
    "signed_at": "ISO8601"
  }
}
```

### Linkage Rules

1. **Decision Linkage**: Every artifact SHOULD reference at least one `decision_id`
2. **Control Linkage**: Artifacts used for compliance MUST reference `control_id`s
3. **Chain Linkage**: Artifacts MAY reference other artifacts via `related_artifact_ids`

### Inclusion Criteria

An EvidenceArtifact is included in an Audit Packet if:

```
INCLUDE artifact WHERE:
  (artifact.created_at >= scope.start_date OR scope.start_date IS NULL)
  AND (artifact.created_at <= scope.end_date OR scope.end_date IS NULL)
  AND (artifact.is_deleted = FALSE OR scope.include_deleted = TRUE)
  AND (
    scope.type = "all"
    OR (scope.type = "evidence_only")
    OR (scope.type = "risk_only" AND artifact.artifact_type = "risk_assessment")
    OR (scope.type = "escalation_only" AND artifact.artifact_type = "escalation_record")
    OR (scope.type = "override_only" AND artifact.artifact_type = "override_record")
  )
```

### External References

When an artifact references external content:

```json
{
  "artifact_id": "evd_external_ref_001",
  "content_reference": {
    "type": "external",
    "uri": "https://storage.example.com/blob/abc123",
    "sha256_at_reference_time": "computed_hash",
    "accessed_at": "ISO8601"
  }
}
```

External references preserve verifiability while managing packet size.

---

## Alignment and Evidence Coverage

### Coverage Matrix

The Audit Packet provides alignment evidence through explicit mapping:

```
┌────────────────────┬─────────────────────────────────────────────┐
│ Governance Domain  │ Evidence Coverage                           │
├────────────────────┼─────────────────────────────────────────────┤
│ Risk Assessment    │ risk/assessments.json → decision linkage    │
│ Human Oversight    │ escalations/*.json → intervention records   │
│ Override Control   │ overrides/*.json → authorization chains     │
│ Audit Trail        │ decisions/ledger_extract.json → full chain  │
│ Compliance Mapping │ compliance/*.json → control satisfaction    │
└────────────────────┴─────────────────────────────────────────────┘
```

### Alignment Assertions

An Audit Packet implicitly asserts:

1. **Traceability**: Every decision can be traced to its risk assessment, any escalations, and any overrides
2. **Completeness**: All governance events within the scope are captured
3. **Integrity**: All records are cryptographically linked and verifiable
4. **Accountability**: Every intervention has an identified actor

### Coverage Metrics

The `statistics.json` provides coverage assessment:

```json
{
  "coverage": {
    "decisions_with_risk_assessment": 0.95,
    "escalations_resolved": 0.88,
    "overrides_with_justification": 1.0,
    "controls_with_evidence": 0.67,
    "evidence_with_signatures": 0.42
  }
}
```

---

## Format Specifications

### JSON (Canonical)

- UTF-8 encoding
- 2-space indentation
- Sorted keys for determinism
- No trailing whitespace
- Single trailing newline

### CSV

- UTF-8 encoding with BOM
- Comma delimiter
- Double-quote escaping
- Header row required
- One section per table

### Markdown

- UTF-8 encoding
- ATX-style headers
- Fenced code blocks
- Tables for structured data
- Limited to first 10 items per section (with count summary)

### HTML

- UTF-8 encoding
- Valid HTML5
- Inline CSS (no external dependencies)
- Printable format
- Self-contained (no external resources)

---

## Versioning

### Packet Version

The `packet_version` field follows semantic versioning:

- **Major**: Breaking changes to structure
- **Minor**: New optional fields or sections
- **Patch**: Clarifications or bug fixes

### Backwards Compatibility

Consumers MUST:
- Accept packets with same major version
- Ignore unknown fields
- Handle missing optional fields gracefully

### Migration Path

When major version changes:
1. Document structural changes
2. Provide migration tooling
3. Support previous version for 2 release cycles

---

## Security Considerations

### Sensitive Data

Audit Packets MAY contain:
- Actor identifiers
- Decision justifications
- System configurations
- Risk scores

Audit Packets MUST NOT contain:
- Raw credentials
- Encryption keys
- Personal data beyond necessary identifiers

### Access Control

Audit Packet generation and access SHOULD:
- Require `VIEW_AUDIT_LOGS` permission
- Log all access attempts
- Support role-based filtering

### Retention

Audit Packets SHOULD:
- Be retained according to organizational policy
- Be stored with integrity verification
- Support secure deletion when retention expires
