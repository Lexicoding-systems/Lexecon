# Audit Packet Verification

## Purpose

This document describes how to verify the integrity and completeness of Lexecon audit export packages using the included CLI verification tool.

---

## Overview

Lexecon audit packages include cryptographic checksums that allow independent verification of:
- Package integrity (no tampering since generation)
- Artifact completeness (all referenced items present)
- Manifest validity (required sections exist)
- Hash chain integrity (artifacts match declared checksums)

The verification tool (`audit_verify.py`) provides automated checking of these properties.

---

## Installation

The verification tool is included with Lexecon:

```bash
# If Lexecon is installed
python -m lexecon.tools.audit_verify --help

# Or run directly from source
python src/lexecon/tools/audit_verify.py --help
```

**Dependencies**: Python 3.8+, standard library only (no external dependencies required for verification).

---

## Usage

### Basic Verification

```bash
# Verify a single JSON file
python -m lexecon.tools.audit_verify audit_export.json

# Verify a directory structure
python -m lexecon.tools.audit_verify /path/to/audit_packet/
```

### Verbose Mode

```bash
python -m lexecon.tools.audit_verify -v audit_export.json
```

Enables verbose output with full stack traces on errors.

---

## Example Output

### Successful Verification

```
Verifying audit packet: audit_export_2026-01-04.json

[Checking] Packet structure... ✓
[Checking] Manifest integrity... ✓
[Checking] Required sections... ✓
[Checking] Artifact checksums... ✓
  Verified 42/42 artifacts
[Checking] Root checksum... ✓

============================================================
✅ VERIFICATION PASSED

Packet Details:
  Export ID: exp_a1b2c3d4e5f6
  Generated: 2026-01-04T12:00:00+00:00
  Version: 1.0.0

Contents:
  Decisions: 156
  Evidence: 42
  Risks: 23
  Escalations: 8
  Overrides: 3
============================================================
```

**Exit Code**: `0` (success)

---

### Failed Verification

```
Verifying audit packet: tampered_packet.json

[Checking] Packet structure... ✓
[Checking] Manifest integrity... ✓
[Checking] Required sections... ✓
[Checking] Artifact checksums... ✗
[Checking] Root checksum... ✗

============================================================
❌ VERIFICATION FAILED (2 error(s))

Errors:
  ✗ Artifact checksums: Artifact evd_abc123 checksum mismatch
  ✗ Root checksum: Root checksum does not match expected value

Warnings (1):
  ⚠ Some artifacts may have been modified

Packet Details:
  Export ID: exp_tampered_001
  Generated: 2026-01-04T10:00:00+00:00
  Version: 1.0.0

Contents:
  Decisions: 100
  Evidence: 30
  Risks: 15
  Escalations: 5
  Overrides: 2
============================================================
```

**Exit Code**: `1` (verification failed)

---

## Verification Checks

### 1. Packet Structure

**Checks**:
- Packet path exists
- If file: has `.json` extension
- If directory: contains `manifest.json`

**Failure Conditions**:
- Path does not exist
- Non-JSON file provided
- Missing required files

---

### 2. Manifest Integrity

**Checks**:
- Manifest is valid JSON
- Contains required top-level fields:
  - `packet_version`
  - `export_id`
  - `generated_at`
  - `generator`
  - `scope`
  - `contents`
  - `integrity`
- Integrity section includes `root_checksum` and `algorithm`

**Failure Conditions**:
- Invalid JSON syntax
- Missing required fields
- Malformed integrity section

---

### 3. Required Sections

**Checks**:
- `contents` section includes count fields
- Counts are non-negative integers

**Failure Conditions**:
- Invalid count values (negative, non-numeric)
- Missing critical count fields

---

### 4. Artifact Checksums

**Checks** (for directory-based packets):
- Each artifact listed in `manifest.integrity.artifact_checksums` exists
- Artifact file hash matches declared checksum

**Skipped For**:
- Single-file JSON packets (artifacts embedded)

**Failure Conditions**:
- Referenced artifact file not found
- Computed hash does not match declared hash

---

### 5. Root Checksum

**Checks**:
- Root checksum exists in manifest
- Computed root hash matches declared value

**Limitations**:
- Single-file packets use simplified verification
- Directory packets compute hash over all files in deterministic order
- Non-deterministic JSON serialization may cause false warnings

**Failure Conditions**:
- Root checksum missing
- Computed hash mismatch (potential tampering)

---

## Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | All checks passed |
| 1 | Verification Failed | One or more checks failed |
| 2 | Exception | Unexpected error during verification |

---

## Use in Automated Systems

### CI/CD Pipeline

```bash
#!/bin/bash
# Verify audit package before uploading to compliance storage

python -m lexecon.tools.audit_verify "$AUDIT_PACKAGE" || {
  echo "❌ Audit package verification failed"
  exit 1
}

echo "✅ Audit package verified, proceeding with upload"
aws s3 cp "$AUDIT_PACKAGE" s3://compliance-bucket/
```

---

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Verify any audit packages being committed
for file in $(git diff --cached --name-only | grep 'audit.*\.json$'); do
  python -m lexecon.tools.audit_verify "$file" || {
    echo "❌ Cannot commit unverified audit package: $file"
    exit 1
  }
done
```

---

### Periodic Verification

```bash
#!/bin/bash
# Cron job to verify stored audit packages

find /compliance/audit_packages -name '*.json' | while read -r package; do
  echo "Verifying: $package"
  python -m lexecon.tools.audit_verify "$package" || {
    echo "⚠ ALERT: Package integrity compromised: $package"
    # Send alert to security team
  }
done
```

---

## What Verification Proves

### ✅ Verification Passes

**Demonstrates**:
- Package has not been modified since generation
- All referenced artifacts are present
- Manifest structure is valid
- Hash chain is intact

**Does NOT Prove**:
- Content is accurate (only that it hasn't changed)
- Original generation was correct
- Data collection was complete

---

### ❌ Verification Fails

**Indicates**:
- Potential tampering with package contents
- Corruption during storage/transfer
- Incomplete package (missing artifacts)
- Invalid package structure

**Next Steps**:
1. Do not rely on package for audit purposes
2. Investigate cause of failure
3. Regenerate package from source system
4. Review storage/transfer mechanisms

---

## Limitations

### Current Limitations

1. **Timestamp Sensitivity**: Root checksum may show warnings if JSON serialization is non-deterministic
2. **Embedded Artifacts**: Single-file packets have simplified verification
3. **Semantic Validation**: Tool verifies structure, not semantic correctness
4. **Schema Validation**: Does not validate against JSON schemas (assumes valid generation)

### Out of Scope

The verification tool **does not**:
- Validate business logic or data accuracy
- Check compliance mapping correctness
- Verify external references (URIs in artifacts)
- Authenticate the generator
- Verify actor identities in records

---

## Troubleshooting

### "Root checksum mismatch" Warning

**Cause**: Non-deterministic JSON serialization or file ordering.

**Resolution**: This is often a false positive. Verify individual artifact checksums pass. If all artifacts verify, root mismatch may be due to serialization differences.

**When to Worry**: If artifact checksums also fail, indicates genuine tampering.

---

### "Artifact file not found"

**Cause**: Incomplete package or incorrect directory structure.

**Resolution**:
1. Verify package was completely extracted/downloaded
2. Check file permissions
3. Regenerate package if corruption suspected

---

### "Invalid JSON in manifest"

**Cause**: Corrupted file or encoding issue.

**Resolution**:
1. Check file is complete (compare size to expected)
2. Verify UTF-8 encoding
3. Try opening in text editor to inspect
4. Regenerate if corrupted

---

## Advanced Usage

### Programmatic Verification

```python
from lexecon.tools.audit_verify import AuditVerifier

verifier = AuditVerifier("audit_export.json")
success = verifier.verify()

if success:
    print("Package verified")
    print(f"Export ID: {verifier.manifest['export_id']}")
else:
    print(f"Verification failed: {verifier.errors}")
```

---

### Custom Checks

Extend `AuditVerifier` class for organization-specific checks:

```python
from lexecon.tools.audit_verify import AuditVerifier

class CustomVerifier(AuditVerifier):
    def _verify_organization_policy(self):
        """Custom check for org policy compliance."""
        contents = self.manifest.get("contents", {})

        # Require minimum evidence count
        if contents.get("evidence_count", 0) < 10:
            raise AuditVerificationError(
                "Insufficient evidence (org policy: min 10)"
            )

        # Check for specific frameworks
        frameworks = contents.get("frameworks_included", [])
        if "soc2" not in frameworks:
            self.warnings.append("SOC 2 framework not included")

verifier = CustomVerifier("audit_export.json")
verifier.verify()
```

---

## Best Practices

### For Audit Package Recipients

1. **Verify immediately upon receipt** before processing
2. **Store verification results** alongside package
3. **Re-verify periodically** to detect storage corruption
4. **Automate verification** in intake pipelines
5. **Document failed verifications** for incident response

### For Audit Package Generators

1. **Verify after generation** before distribution
2. **Include verification instructions** with package
3. **Provide verification tool** to recipients
4. **Document known limitations** in package metadata
5. **Test verification** against corrupted samples

---

## Security Considerations

### Verification Tool Trust

The verification tool itself must be trusted:
- Obtain from official Lexecon repository
- Verify tool source code if required
- Run in isolated environment if suspicious of package
- Use read-only access to packet files

### Verification is Necessary but Not Sufficient

Verification proves package integrity, but organizations should:
- Authenticate package source
- Validate generation authority
- Review substantive content
- Cross-reference with source systems
- Maintain chain of custody documentation

---

## Related Documentation

- `docs/AUDIT_PACKET_SPEC.md`: Audit package structure and integrity model
- `docs/DEMO_SCRIPT.md`: Step 4 includes export generation and verification
- `docs/ENTERPRISE_READINESS_GAPS.md`: Future enhancements to verification

---

## Version History

- **v0.1.0** (2026-01-04): Initial audit verification tool and documentation
  - Basic integrity checks
  - Manifest validation
  - Artifact checksum verification
  - Root checksum verification (with limitations)
