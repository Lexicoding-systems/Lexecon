"""
Persistent Storage for EU AI Act Compliance Records

Stores Article 14 human oversight interventions in SQLite for
10-year retention as required by EU AI Act Article 12.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .article_14_oversight import HumanIntervention, InterventionType, OversightRole


class InterventionStorage:
    """
    Persistent storage for Article 14 human oversight interventions.

    Ensures intervention records survive system restarts and are
    available for long-term compliance audits.
    """

    def __init__(self, db_path: str = "lexecon_interventions.db"):
        """
        Initialize storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Create tables and indexes if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create interventions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS interventions (
                intervention_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                intervention_type TEXT NOT NULL,
                ai_recommendation TEXT NOT NULL,
                ai_confidence REAL NOT NULL,
                human_decision TEXT NOT NULL,
                human_role TEXT NOT NULL,
                reason TEXT NOT NULL,
                request_context TEXT NOT NULL,
                signature TEXT,
                response_time_ms INTEGER,
                created_at TEXT NOT NULL
            )
        """
        )

        # Create indexes for efficient querying
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON interventions(timestamp)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_intervention_type
            ON interventions(intervention_type)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_human_role
            ON interventions(human_role)
        """
        )

        conn.commit()
        conn.close()

    def save_intervention(self, intervention: HumanIntervention) -> None:
        """
        Save a single intervention record.

        Args:
            intervention: HumanIntervention to save
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO interventions (
                intervention_id, timestamp, intervention_type,
                ai_recommendation, ai_confidence, human_decision,
                human_role, reason, request_context, signature,
                response_time_ms, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                intervention.intervention_id,
                intervention.timestamp,
                intervention.intervention_type.value,
                json.dumps(intervention.ai_recommendation),
                intervention.ai_confidence,
                json.dumps(intervention.human_decision),
                intervention.human_role.value,
                intervention.reason,
                json.dumps(intervention.request_context),
                intervention.signature,
                intervention.response_time_ms,
                datetime.utcnow().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

    def load_all_interventions(self) -> List[HumanIntervention]:
        """
        Load all intervention records in chronological order.

        Returns:
            List of HumanIntervention objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                intervention_id, timestamp, intervention_type,
                ai_recommendation, ai_confidence, human_decision,
                human_role, reason, request_context, signature,
                response_time_ms
            FROM interventions
            ORDER BY timestamp ASC
        """
        )

        interventions = []
        for row in cursor.fetchall():
            intervention = HumanIntervention(
                intervention_id=row[0],
                timestamp=row[1],
                intervention_type=InterventionType(row[2]),
                ai_recommendation=json.loads(row[3]),
                ai_confidence=row[4],
                human_decision=json.loads(row[5]),
                human_role=OversightRole(row[6]),
                reason=row[7],
                request_context=json.loads(row[8]),
                signature=row[9],
                response_time_ms=row[10],
            )
            interventions.append(intervention)

        conn.close()
        return interventions

    def get_by_timerange(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> List[HumanIntervention]:
        """
        Get interventions within a time range.

        Args:
            start_date: ISO format start date (inclusive)
            end_date: ISO format end date (inclusive)

        Returns:
            List of HumanIntervention objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT
                intervention_id, timestamp, intervention_type,
                ai_recommendation, ai_confidence, human_decision,
                human_role, reason, request_context, signature,
                response_time_ms
            FROM interventions
            WHERE 1=1
        """
        params = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)

        query += " ORDER BY timestamp ASC"

        cursor.execute(query, params)

        interventions = []
        for row in cursor.fetchall():
            intervention = HumanIntervention(
                intervention_id=row[0],
                timestamp=row[1],
                intervention_type=InterventionType(row[2]),
                ai_recommendation=json.loads(row[3]),
                ai_confidence=row[4],
                human_decision=json.loads(row[5]),
                human_role=OversightRole(row[6]),
                reason=row[7],
                request_context=json.loads(row[8]),
                signature=row[9],
                response_time_ms=row[10],
            )
            interventions.append(intervention)

        conn.close()
        return interventions

    def get_statistics(self) -> dict:
        """
        Get storage statistics.

        Returns:
            Dict with storage statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total interventions
        cursor.execute("SELECT COUNT(*) FROM interventions")
        total = cursor.fetchone()[0]

        # Database size
        db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0

        # Oldest intervention
        cursor.execute("SELECT MIN(timestamp) FROM interventions")
        oldest = cursor.fetchone()[0]

        # Newest intervention
        cursor.execute("SELECT MAX(timestamp) FROM interventions")
        newest = cursor.fetchone()[0]

        # By intervention type
        cursor.execute(
            """
            SELECT intervention_type, COUNT(*)
            FROM interventions
            GROUP BY intervention_type
        """
        )
        by_type = {row[0]: row[1] for row in cursor.fetchall()}

        # By human role
        cursor.execute(
            """
            SELECT human_role, COUNT(*)
            FROM interventions
            GROUP BY human_role
        """
        )
        by_role = {row[0]: row[1] for row in cursor.fetchall()}

        # Override count
        cursor.execute(
            """
            SELECT COUNT(*) FROM interventions
            WHERE intervention_type = 'override'
        """
        )
        overrides = cursor.fetchone()[0]

        conn.close()

        return {
            "database_path": self.db_path,
            "database_size_bytes": db_size,
            "total_interventions": total,
            "oldest_intervention": oldest,
            "newest_intervention": newest,
            "by_intervention_type": by_type,
            "by_human_role": by_role,
            "override_count": overrides,
            "override_rate": (overrides / total * 100) if total > 0 else 0,
        }

    def count_interventions(self) -> int:
        """Get total count of interventions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM interventions")
        count = cursor.fetchone()[0]
        conn.close()
        return count
