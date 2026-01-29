"""Persistent Storage for Responsibility Records

Stores responsibility tracking data in SQLite for long-term accountability
and EU AI Act compliance (Article 14 - 10 year retention).
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List

from .tracker import DecisionMaker, ResponsibilityLevel, ResponsibilityRecord


class ResponsibilityStorage:
    """Persistent storage for responsibility records using SQLite.

    Ensures accountability data survives system restarts and is
    available for long-term audits and legal proceedings.
    """

    def __init__(self, db_path: str = "lexecon_responsibility.db"):
        """Initialize storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Create tables and indexes if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create responsibility_records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS responsibility_records (
                record_id TEXT PRIMARY KEY,
                decision_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                decision_maker TEXT NOT NULL,
                responsible_party TEXT NOT NULL,
                role TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                confidence REAL NOT NULL,
                responsibility_level TEXT NOT NULL,
                delegated_from TEXT,
                escalated_to TEXT,
                override_ai INTEGER NOT NULL,
                ai_recommendation TEXT,
                review_required INTEGER NOT NULL,
                reviewed_by TEXT,
                reviewed_at TEXT,
                liability_accepted INTEGER NOT NULL,
                liability_signature TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # Create indexes for efficient querying
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decision_id
            ON responsibility_records(decision_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_responsible_party
            ON responsibility_records(responsible_party)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decision_maker
            ON responsibility_records(decision_maker)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON responsibility_records(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_override_ai
            ON responsibility_records(override_ai)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_review_required
            ON responsibility_records(review_required, reviewed_by)
        """)

        conn.commit()
        conn.close()

    def save_record(self, record: ResponsibilityRecord) -> None:
        """Save a single responsibility record.

        Args:
            record: ResponsibilityRecord to save
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO responsibility_records (
                record_id, decision_id, timestamp, decision_maker,
                responsible_party, role, reasoning, confidence,
                responsibility_level, delegated_from, escalated_to,
                override_ai, ai_recommendation, review_required,
                reviewed_by, reviewed_at, liability_accepted,
                liability_signature, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.record_id,
            record.decision_id,
            record.timestamp,
            record.decision_maker.value,
            record.responsible_party,
            record.role,
            record.reasoning,
            record.confidence,
            record.responsibility_level.value,
            record.delegated_from,
            record.escalated_to,
            1 if record.override_ai else 0,
            record.ai_recommendation,
            1 if record.review_required else 0,
            record.reviewed_by,
            record.reviewed_at,
            1 if record.liability_accepted else 0,
            record.liability_signature,
            datetime.utcnow().isoformat(),
        ))

        conn.commit()
        conn.close()

    def load_all_records(self) -> List[ResponsibilityRecord]:
        """Load all responsibility records in chronological order.

        Returns:
            List of ResponsibilityRecord objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                record_id, decision_id, timestamp, decision_maker,
                responsible_party, role, reasoning, confidence,
                responsibility_level, delegated_from, escalated_to,
                override_ai, ai_recommendation, review_required,
                reviewed_by, reviewed_at, liability_accepted,
                liability_signature
            FROM responsibility_records
            ORDER BY timestamp ASC
        """)

        records = []
        for row in cursor.fetchall():
            record = ResponsibilityRecord(
                record_id=row[0],
                decision_id=row[1],
                timestamp=row[2],
                decision_maker=DecisionMaker(row[3]),
                responsible_party=row[4],
                role=row[5],
                reasoning=row[6],
                confidence=row[7],
                responsibility_level=ResponsibilityLevel(row[8]),
                delegated_from=row[9],
                escalated_to=row[10],
                override_ai=bool(row[11]),
                ai_recommendation=row[12],
                review_required=bool(row[13]),
                reviewed_by=row[14],
                reviewed_at=row[15],
                liability_accepted=bool(row[16]),
                liability_signature=row[17],
            )
            records.append(record)

        conn.close()
        return records

    def update_record(self, record_id: str, **updates) -> bool:
        """Update specific fields of a responsibility record.

        Args:
            record_id: ID of record to update
            **updates: Fields to update

        Returns:
            True if record was updated, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build UPDATE query from provided fields
        # Use explicit field mapping to prevent SQL injection
        VALID_UPDATE_FIELDS = {
            "reviewed_by": "reviewed_by = ?",
            "reviewed_at": "reviewed_at = ?",
        }
        update_fields = []
        values = []

        for key, value in updates.items():
            if key in VALID_UPDATE_FIELDS:
                update_fields.append(VALID_UPDATE_FIELDS[key])
                values.append(value)

        if not update_fields:
            conn.close()
            return False

        values.append(record_id)
        query = f"""
            UPDATE responsibility_records
            SET {', '.join(update_fields)}
            WHERE record_id = ?
        """  # nosec

        cursor.execute(query, values)
        success = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return success

    def get_statistics(self) -> dict:
        """Get storage statistics.

        Returns:
            Dict with storage statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total records
        cursor.execute("SELECT COUNT(*) FROM responsibility_records")
        total_records = cursor.fetchone()[0]

        # Database size
        db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0

        # Oldest record
        cursor.execute("""
            SELECT MIN(timestamp) FROM responsibility_records
        """)
        oldest = cursor.fetchone()[0]

        # Newest record
        cursor.execute("""
            SELECT MAX(timestamp) FROM responsibility_records
        """)
        newest = cursor.fetchone()[0]

        # By decision maker
        cursor.execute("""
            SELECT decision_maker, COUNT(*)
            FROM responsibility_records
            GROUP BY decision_maker
        """)
        by_maker = {row[0]: row[1] for row in cursor.fetchall()}

        # Override count
        cursor.execute("""
            SELECT COUNT(*) FROM responsibility_records WHERE override_ai = 1
        """)
        overrides = cursor.fetchone()[0]

        conn.close()

        return {
            "database_path": self.db_path,
            "database_size_bytes": db_size,
            "total_records": total_records,
            "oldest_record": oldest,
            "newest_record": newest,
            "by_decision_maker": by_maker,
            "override_count": overrides,
        }

    def get_by_decision_id(self, decision_id: str) -> List[ResponsibilityRecord]:
        """Get all responsibility records for a specific decision.

        Args:
            decision_id: Decision ID to query

        Returns:
            List of ResponsibilityRecord objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                record_id, decision_id, timestamp, decision_maker,
                responsible_party, role, reasoning, confidence,
                responsibility_level, delegated_from, escalated_to,
                override_ai, ai_recommendation, review_required,
                reviewed_by, reviewed_at, liability_accepted,
                liability_signature
            FROM responsibility_records
            WHERE decision_id = ?
            ORDER BY timestamp ASC
        """, (decision_id,))

        records = []
        for row in cursor.fetchall():
            record = ResponsibilityRecord(
                record_id=row[0],
                decision_id=row[1],
                timestamp=row[2],
                decision_maker=DecisionMaker(row[3]),
                responsible_party=row[4],
                role=row[5],
                reasoning=row[6],
                confidence=row[7],
                responsibility_level=ResponsibilityLevel(row[8]),
                delegated_from=row[9],
                escalated_to=row[10],
                override_ai=bool(row[11]),
                ai_recommendation=row[12],
                review_required=bool(row[13]),
                reviewed_by=row[14],
                reviewed_at=row[15],
                liability_accepted=bool(row[16]),
                liability_signature=row[17],
            )
            records.append(record)

        conn.close()
        return records
