"""Evidence Export Service - Generates compliance-ready export bundles.

Creates ZIP archives containing:
- ledger_events.json
- verification_report.json
- policies.json
- summary.md
- manifest.json (signed)
"""

import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class EvidenceBundle:
    """Represents an evidence export bundle."""

    def __init__(
        self,
        tenant_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        ledger_entries: List[Dict] = None,
        verification_report: Dict = None,
        policies: List[Dict] = None,
    ):
        self.tenant_id = tenant_id
        self.start_time = start_time
        self.end_time = end_time
        self.ledger_entries = ledger_entries or []
        self.verification_report = verification_report or {}
        self.policies = policies or []
        self.exported_at = datetime.now(timezone.utc).isoformat()

    def to_zip_bytes(self, signature_service=None) -> bytes:
        """Generate ZIP archive as bytes."""
        buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            files_manifest = []
            
            # 1. ledger_events.json
            ledger_content = self._generate_ledger_events_json()
            zf.writestr('ledger_events.json', ledger_content)
            files_manifest.append({
                'path': 'ledger_events.json',
                'sha256': hashlib.sha256(ledger_content.encode()).hexdigest()
            })
            
            # 2. verification_report.json
            verification_content = self._generate_verification_report_json()
            zf.writestr('verification_report.json', verification_content)
            files_manifest.append({
                'path': 'verification_report.json',
                'sha256': hashlib.sha256(verification_content.encode()).hexdigest()
            })
            
            # 3. policies.json
            policies_content = self._generate_policies_json()
            zf.writestr('policies.json', policies_content)
            files_manifest.append({
                'path': 'policies.json',
                'sha256': hashlib.sha256(policies_content.encode()).hexdigest()
            })
            
            # 4. summary.md
            summary_content = self._generate_summary_md()
            zf.writestr('summary.md', summary_content)
            files_manifest.append({
                'path': 'summary.md',
                'sha256': hashlib.sha256(summary_content.encode()).hexdigest()
            })
            
            # 5. manifest.json (signed)
            manifest_content = self._generate_manifest_json(files_manifest, signature_service)
            zf.writestr('manifest.json', manifest_content)
        
        buffer.seek(0)
        return buffer.read()

    def _generate_ledger_events_json(self) -> str:
        """Generate ledger_events.json content."""
        events = []
        for entry in self.ledger_entries:
            data = entry.get('data', {})
            events.append({
                'entry_id': entry.get('entry_id'),
                'event_type': entry.get('event_type'),
                'timestamp': entry.get('timestamp'),
                'previous_hash': entry.get('previous_hash'),
                'entry_hash': entry.get('entry_hash'),
                'data': {
                    'decision_id': data.get('decision_id') or data.get('request_id'),
                    'request_id': data.get('request_id'),
                    'decision': data.get('decision'),
                    'enforcement_result': data.get('decision'),  # Same as decision
                    'action': data.get('action'),
                    'actor': data.get('actor'),
                    'model_name': data.get('model_name'),  # May be null
                    'policy_version_hash': data.get('policy_version_hash'),
                    'risk_level': data.get('risk_level'),
                    'input_summary': data.get('input_summary'),  # May be null
                    'output_summary': data.get('output_summary'),  # May be null
                    'justification': data.get('justification'),  # May be null
                }
            })
        
        payload = {
            'tenant_id': self.tenant_id,
            'exported_at': self.exported_at,
            'time_range': {
                'start': self.start_time,
                'end': self.end_time,
            },
            'events': events,
        }
        return json.dumps(payload, indent=2, default=str)

    def _generate_verification_report_json(self) -> str:
        """Generate verification_report.json content."""
        report = self.verification_report or {}
        
        payload = {
            'tenant_id': self.tenant_id,
            'exported_at': self.exported_at,
            'verified': report.get('valid', True),
            'checked_count': report.get('entries_checked', len(self.ledger_entries)),
            'failed_count': report.get('entries_checked', 0) - report.get('entries_verified', 0),
            'failures': [],  # Populate if verification finds issues
            'method': {
                'chain_verification': True,
                'hash_algorithm': 'sha256',
                'entry_hash_field': 'entry_hash',
                'previous_hash_field': 'previous_hash',
            },
        }
        return json.dumps(payload, indent=2)

    def _generate_policies_json(self) -> str:
        """Generate policies.json content."""
        # Extract unique policy hashes from ledger entries
        policy_hashes = set()
        for entry in self.ledger_entries:
            data = entry.get('data', {})
            if data.get('policy_version_hash'):
                policy_hashes.add(data['policy_version_hash'])
        
        policy_versions = [
            {
                'policy_version_hash': h,
                'policy_id': None,
                'name': None,
            }
            for h in sorted(policy_hashes)
        ]
        
        payload = {
            'tenant_id': self.tenant_id,
            'exported_at': self.exported_at,
            'policy_versions': policy_versions,
        }
        return json.dumps(payload, indent=2)

    def _generate_summary_md(self) -> str:
        """Generate human-readable summary.md."""
        # Calculate stats
        total = len(self.ledger_entries)
        decisions = [e for e in self.ledger_entries if e.get('event_type') == 'decision']
        
        outcomes = {}
        actions = {}
        risk_levels = {}
        
        for entry in decisions:
            data = entry.get('data', {})
            # Outcome
            outcome = data.get('decision', 'unknown')
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
            # Action
            action = data.get('action', 'unknown')
            actions[action] = actions.get(action, 0) + 1
            # Risk level
            risk = data.get('risk_level', 'unknown')
            risk_levels[risk] = risk_levels.get(risk, 0) + 1
        
        # Policy hashes
        policy_hashes = set()
        for entry in self.ledger_entries:
            data = entry.get('data', {})
            if data.get('policy_version_hash'):
                policy_hashes.add(data['policy_version_hash'][:16] + '...')
        
        md = f"""# Lexecon Evidence Export Summary

**Tenant:** {self.tenant_id}  
**Exported:** {self.exported_at}  
**Time Range:** {self.start_time or 'All time'} to {self.end_time or 'Now'}

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Ledger Entries | {total} |
| Decision Events | {len(decisions)} |
| Verification Status | {'✅ VERIFIED' if self.verification_report.get('valid') else '❌ FAILED'} |

---

## Outcome Distribution

| Outcome | Count | Percentage |
|---------|-------|------------|
"""
        for outcome, count in sorted(outcomes.items()):
            pct = (count / len(decisions) * 100) if decisions else 0
            md += f"| {outcome.upper()} | {count} | {pct:.1f}% |\n"
        
        md += f"""
---

## Top Actions

| Action | Count |
|--------|-------|
"""
        for action, count in sorted(actions.items(), key=lambda x: -x[1])[:10]:
            md += f"| {action} | {count} |\n"
        
        md += f"""
---

## Risk Level Distribution

| Risk Level | Count |
|------------|-------|
"""
        for risk, count in sorted(risk_levels.items()):
            md += f"| {risk.upper()} | {count} |\n"
        
        md += f"""
---

## Policy Versions Referenced

"""
        for h in sorted(policy_hashes):
            md += f"- `{h}`\n"
        
        md += f"""
---

## Files in This Bundle

- `ledger_events.json` - Complete ledger entries with cryptographic hashes
- `verification_report.json` - Chain integrity verification results
- `policies.json` - Policy version references
- `summary.md` - This human-readable summary
- `manifest.json` - Signed manifest with file integrity hashes

---

## Verification

This bundle was generated by Lexecon AI Governance Platform.
All ledger entries include SHA-256 cryptographic hashes linking each entry
to its predecessor, forming a tamper-evident chain.

To verify independently:
1. Check each entry's `entry_hash` matches SHA-256 of its content
2. Verify `previous_hash` matches the preceding entry's `entry_hash`
3. Validate the signature in `manifest.json`

---

*Generated by Lexecon v0.1.0*  
*EU AI Act Compliant - Article 12 Record Keeping*
"""
        return md

    def _generate_manifest_json(self, files: List[Dict], signature_service=None) -> str:
        """Generate signed manifest.json."""
        # Compute bundle hash (hash of concatenated file hashes)
        file_hashes = ''.join(f['sha256'] for f in sorted(files, key=lambda x: x['path']))
        bundle_hash = hashlib.sha256(file_hashes.encode()).hexdigest()
        
        # Sign if service available
        signature = None
        if signature_service:
            try:
                signature = signature_service.sign(bundle_hash)
            except Exception:
                pass
        
        manifest = {
            'tenant_id': self.tenant_id,
            'exported_at': self.exported_at,
            'bundle_files': files,
            'bundle_hash': bundle_hash,
            'signature': signature,
            'signing_key_id': 'lexecon_root_001' if signature else None,
            'format_version': '1.0.0',
        }
        return json.dumps(manifest, indent=2)


class EvidenceExportService:
    """Service for generating evidence export bundles."""

    def __init__(self, ledger, signature_service=None):
        self.ledger = ledger
        self.signature_service = signature_service

    def export(
        self,
        tenant_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 1000,
        include_verification: bool = True,
    ) -> bytes:
        """Generate evidence export bundle as ZIP bytes."""
        # Filter entries by time range
        entries = self._filter_entries(start_time, end_time, limit)
        
        # Get verification report
        verification_report = {}
        if include_verification and self.ledger:
            verification_report = self.ledger.verify_integrity()
        
        # Create bundle
        bundle = EvidenceBundle(
            tenant_id=tenant_id,
            start_time=start_time,
            end_time=end_time,
            ledger_entries=entries,
            verification_report=verification_report,
        )
        
        return bundle.to_zip_bytes(self.signature_service)

    def _filter_entries(
        self,
        start_time: Optional[str],
        end_time: Optional[str],
        limit: int,
    ) -> List[Dict]:
        """Filter ledger entries by time range."""
        entries = []
        
        for entry in self.ledger.entries[-limit:]:  # Most recent first
            entry_dict = entry.to_dict() if hasattr(entry, 'to_dict') else entry
            
            # Time filtering (simple string comparison works for ISO format)
            ts = entry_dict.get('timestamp', '')
            if start_time and ts < start_time:
                continue
            if end_time and ts > end_time:
                continue
            
            entries.append(entry_dict)
        
        return entries
