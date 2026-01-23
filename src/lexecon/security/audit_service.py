"""Export Audit Logging Service.

Provides:
- Immutable audit trail of all export requests
- Tamper-evident hash chain
- Forensic investigation capabilities
- SIEM integration hooks
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ExportStatus(str, Enum):
    """Export request status."""
    PENDING = "pending"  # Awaiting approval
    APPROVED = "approved"  # Approved, generation in progress
    COMPLETED = "completed"  # Successfully generated and downloaded
    REJECTED = "rejected"  # Approval denied
    FAILED = "failed"  # Generation failed


class ApprovalStatus(str, Enum):
    """Approval status for multi-party authorization."""
    NOT_REQUIRED = "not_required"  # Auto-approved
    PENDING = "pending"  # Awaiting approval
    APPROVED = "approved"  # Approved by authorized user
    REJECTED = "rejected"  # Rejected by authorized user


@dataclass
class ExportRequest:
    """Export request audit record."""
    request_id: str
    user_id: str
    username: str
    user_email: str
    user_role: str

    # Request metadata (WHO/WHY/WHEN)
    purpose: str
    case_id: Optional[str]
    notes: Optional[str]
    requested_at: str

    # Configuration (WHAT)
    time_window: str
    formats: List[str]  # json, text, csv
    include_decisions: bool
    include_interventions: bool
    include_ledger: bool
    include_responsibility: bool

    # Legal attestation
    attestation_accepted: bool
    attestation_timestamp: str
    attestation_ip_address: Optional[str]

    # Approval workflow
    approval_status: ApprovalStatus
    approval_required: bool
    approved_by_user_id: Optional[str]
    approved_by_username: Optional[str]
    approved_at: Optional[str]
    rejection_reason: Optional[str]

    # Export status
    export_status: ExportStatus
    completed_at: Optional[str]
    packet_hashes: Optional[Dict[str, str]]  # format -> hash
    packet_size_bytes: Optional[int]

    # Audit chain
    previous_hash: str
    entry_hash: str

    # Metadata
    ip_address: Optional[str]
    user_agent: Optional[str]


class AuditService:
    """Export audit logging service with tamper-evident chain."""

    def __init__(self, db_path: str = "lexecon_export_audit.db"):
        """Initialize audit service."""
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize audit database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Export requests audit log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS export_requests (
                request_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                user_email TEXT NOT NULL,
                user_role TEXT NOT NULL,

                purpose TEXT NOT NULL,
                case_id TEXT,
                notes TEXT,
                requested_at TEXT NOT NULL,

                time_window TEXT NOT NULL,
                formats TEXT NOT NULL,
                include_decisions INTEGER NOT NULL,
                include_interventions INTEGER NOT NULL,
                include_ledger INTEGER NOT NULL,
                include_responsibility INTEGER NOT NULL,

                attestation_accepted INTEGER NOT NULL,
                attestation_timestamp TEXT NOT NULL,
                attestation_ip_address TEXT,

                approval_status TEXT NOT NULL,
                approval_required INTEGER NOT NULL,
                approved_by_user_id TEXT,
                approved_by_username TEXT,
                approved_at TEXT,
                rejection_reason TEXT,

                export_status TEXT NOT NULL,
                completed_at TEXT,
                packet_hashes TEXT,
                packet_size_bytes INTEGER,

                previous_hash TEXT NOT NULL,
                entry_hash TEXT NOT NULL,

                ip_address TEXT,
                user_agent TEXT
            )
        """)

        # Approval workflow table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approval_workflow (
                approval_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                reviewer_user_id TEXT NOT NULL,
                reviewer_username TEXT NOT NULL,
                action TEXT NOT NULL,
                reason TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (request_id) REFERENCES export_requests(request_id)
            )
        """)

        # Access attempts log (all API calls)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_log (
                log_id TEXT PRIMARY KEY,
                user_id TEXT,
                username TEXT,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def _compute_hash(self, data: Dict[str, Any]) -> str:
        """Compute SHA-256 hash of data."""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def _get_latest_hash(self) -> str:
        """Get hash of most recent export request."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT entry_hash
            FROM export_requests
            ORDER BY requested_at DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if row:
            return row[0]
        # Genesis hash
        return "0" * 64

    def log_export_request(
        self,
        request_id: str,
        user_id: str,
        username: str,
        user_email: str,
        user_role: str,
        purpose: str,
        case_id: Optional[str],
        notes: Optional[str],
        time_window: str,
        formats: List[str],
        include_decisions: bool,
        include_interventions: bool,
        include_ledger: bool,
        include_responsibility: bool,
        attestation_accepted: bool,
        attestation_ip_address: Optional[str],
        approval_required: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ExportRequest:
        """Log an export request to the audit trail.

        Returns ExportRequest with computed hash chain.
        """
        now = datetime.now(timezone.utc).isoformat()
        previous_hash = self._get_latest_hash()

        # Compute entry hash
        hash_data = {
            "request_id": request_id,
            "user_id": user_id,
            "purpose": purpose,
            "case_id": case_id,
            "requested_at": now,
            "time_window": time_window,
            "formats": sorted(formats),
            "attestation_accepted": attestation_accepted,
            "previous_hash": previous_hash,
        }
        entry_hash = self._compute_hash(hash_data)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO export_requests (
                request_id, user_id, username, user_email, user_role,
                purpose, case_id, notes, requested_at,
                time_window, formats, include_decisions, include_interventions,
                include_ledger, include_responsibility,
                attestation_accepted, attestation_timestamp, attestation_ip_address,
                approval_status, approval_required, approved_by_user_id,
                approved_by_username, approved_at, rejection_reason,
                export_status, completed_at, packet_hashes, packet_size_bytes,
                previous_hash, entry_hash, ip_address, user_agent
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            request_id, user_id, username, user_email, user_role,
            purpose, case_id, notes, now,
            time_window, json.dumps(formats),
            int(include_decisions), int(include_interventions),
            int(include_ledger), int(include_responsibility),
            int(attestation_accepted), now, attestation_ip_address,
            ApprovalStatus.PENDING.value if approval_required else ApprovalStatus.NOT_REQUIRED.value,
            int(approval_required), None, None, None, None,
            ExportStatus.PENDING.value if approval_required else ExportStatus.APPROVED.value,
            None, None, None,
            previous_hash, entry_hash, ip_address, user_agent,
        ))

        conn.commit()
        conn.close()

        return ExportRequest(
            request_id=request_id,
            user_id=user_id,
            username=username,
            user_email=user_email,
            user_role=user_role,
            purpose=purpose,
            case_id=case_id,
            notes=notes,
            requested_at=now,
            time_window=time_window,
            formats=formats,
            include_decisions=include_decisions,
            include_interventions=include_interventions,
            include_ledger=include_ledger,
            include_responsibility=include_responsibility,
            attestation_accepted=attestation_accepted,
            attestation_timestamp=now,
            attestation_ip_address=attestation_ip_address,
            approval_status=ApprovalStatus.PENDING if approval_required else ApprovalStatus.NOT_REQUIRED,
            approval_required=approval_required,
            approved_by_user_id=None,
            approved_by_username=None,
            approved_at=None,
            rejection_reason=None,
            export_status=ExportStatus.PENDING if approval_required else ExportStatus.APPROVED,
            completed_at=None,
            packet_hashes=None,
            packet_size_bytes=None,
            previous_hash=previous_hash,
            entry_hash=entry_hash,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def approve_export(
        self,
        request_id: str,
        approver_user_id: str,
        approver_username: str,
        reason: Optional[str] = None,
    ):
        """Approve an export request."""
        now = datetime.now(timezone.utc).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE export_requests
            SET approval_status = ?,
                approved_by_user_id = ?,
                approved_by_username = ?,
                approved_at = ?,
                export_status = ?
            WHERE request_id = ?
        """, (ApprovalStatus.APPROVED.value, approver_user_id, approver_username,
              now, ExportStatus.APPROVED.value, request_id))

        # Log approval action
        import secrets
        approval_id = f"approval_{secrets.token_hex(16)}"
        cursor.execute("""
            INSERT INTO approval_workflow (
                approval_id, request_id, reviewer_user_id, reviewer_username,
                action, reason, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (approval_id, request_id, approver_user_id, approver_username,
              "approved", reason, now))

        conn.commit()
        conn.close()

    def reject_export(
        self,
        request_id: str,
        reviewer_user_id: str,
        reviewer_username: str,
        reason: str,
    ):
        """Reject an export request."""
        now = datetime.now(timezone.utc).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE export_requests
            SET approval_status = ?,
                rejection_reason = ?,
                export_status = ?
            WHERE request_id = ?
        """, (ApprovalStatus.REJECTED.value, reason, ExportStatus.REJECTED.value, request_id))

        # Log rejection action
        import secrets
        approval_id = f"approval_{secrets.token_hex(16)}"
        cursor.execute("""
            INSERT INTO approval_workflow (
                approval_id, request_id, reviewer_user_id, reviewer_username,
                action, reason, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (approval_id, request_id, reviewer_user_id, reviewer_username,
              "rejected", reason, now))

        conn.commit()
        conn.close()

    def complete_export(
        self,
        request_id: str,
        packet_hashes: Dict[str, str],
        packet_size_bytes: int,
    ):
        """Mark export as completed."""
        now = datetime.now(timezone.utc).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE export_requests
            SET export_status = ?,
                completed_at = ?,
                packet_hashes = ?,
                packet_size_bytes = ?
            WHERE request_id = ?
        """, (ExportStatus.COMPLETED.value, now, json.dumps(packet_hashes),
              packet_size_bytes, request_id))

        conn.commit()
        conn.close()

    def fail_export(self, request_id: str, error_message: str):
        """Mark export as failed."""
        datetime.now(timezone.utc).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE export_requests
            SET export_status = ?,
                rejection_reason = ?
            WHERE request_id = ?
        """, (ExportStatus.FAILED.value, error_message, request_id))

        conn.commit()
        conn.close()

    def get_export_request(self, request_id: str) -> Optional[ExportRequest]:
        """Get export request by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM export_requests
            WHERE request_id = ?
        """, (request_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_export_request(row)

    def list_export_requests(
        self,
        user_id: Optional[str] = None,
        status: Optional[ExportStatus] = None,
        limit: int = 100,
    ) -> List[ExportRequest]:
        """List export requests with optional filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM export_requests WHERE 1=1"
        params = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if status:
            query += " AND export_status = ?"
            params.append(status.value)

        query += " ORDER BY requested_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        requests = []
        for row in cursor.fetchall():
            requests.append(self._row_to_export_request(row))

        conn.close()
        return requests

    def _row_to_export_request(self, row) -> ExportRequest:
        """Convert database row to ExportRequest."""
        packet_hashes = json.loads(row[27]) if row[27] else None

        return ExportRequest(
            request_id=row[0],
            user_id=row[1],
            username=row[2],
            user_email=row[3],
            user_role=row[4],
            purpose=row[5],
            case_id=row[6],
            notes=row[7],
            requested_at=row[8],
            time_window=row[9],
            formats=json.loads(row[10]),
            include_decisions=bool(row[11]),
            include_interventions=bool(row[12]),
            include_ledger=bool(row[13]),
            include_responsibility=bool(row[14]),
            attestation_accepted=bool(row[15]),
            attestation_timestamp=row[16],
            attestation_ip_address=row[17],
            approval_status=ApprovalStatus(row[18]),
            approval_required=bool(row[19]),
            approved_by_user_id=row[20],
            approved_by_username=row[21],
            approved_at=row[22],
            rejection_reason=row[23],
            export_status=ExportStatus(row[24]),
            completed_at=row[25],
            packet_hashes=packet_hashes,
            packet_size_bytes=row[28],
            previous_hash=row[29],
            entry_hash=row[30],
            ip_address=row[31],
            user_agent=row[32],
        )

    def log_access(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log API access for security monitoring."""
        import secrets
        log_id = f"log_{secrets.token_hex(16)}"
        timestamp = datetime.now(timezone.utc).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO access_log (
                log_id, user_id, username, endpoint, method,
                status_code, ip_address, user_agent, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (log_id, user_id, username, endpoint, method,
              status_code, ip_address, user_agent, timestamp))

        conn.commit()
        conn.close()

    def verify_audit_chain(self) -> Dict[str, Any]:
        """Verify integrity of audit chain."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT request_id, user_id, purpose, case_id, requested_at,
                   time_window, formats, attestation_accepted,
                   previous_hash, entry_hash
            FROM export_requests
            ORDER BY requested_at ASC
        """)

        valid = True
        invalid_entries = []
        prev_hash = "0" * 64

        for row in cursor.fetchall():
            request_id = row[0]
            stored_prev_hash = row[8]
            stored_entry_hash = row[9]

            # Verify previous hash links correctly
            if stored_prev_hash != prev_hash:
                valid = False
                invalid_entries.append({
                    "request_id": request_id,
                    "reason": "broken_chain",
                    "expected_prev_hash": prev_hash,
                    "actual_prev_hash": stored_prev_hash,
                })

            # Verify entry hash is correct
            hash_data = {
                "request_id": row[0],
                "user_id": row[1],
                "purpose": row[2],
                "case_id": row[3],
                "requested_at": row[4],
                "time_window": row[5],
                "formats": sorted(json.loads(row[6])),
                "attestation_accepted": bool(row[7]),
                "previous_hash": row[8],
            }
            computed_hash = self._compute_hash(hash_data)

            if computed_hash != stored_entry_hash:
                valid = False
                invalid_entries.append({
                    "request_id": request_id,
                    "reason": "hash_mismatch",
                    "expected_hash": computed_hash,
                    "actual_hash": stored_entry_hash,
                })

            prev_hash = stored_entry_hash

        conn.close()

        return {
            "valid": valid,
            "invalid_entries": invalid_entries,
            "message": "Audit chain is valid" if valid else f"Found {len(invalid_entries)} invalid entries",
        }
