"""Ledger Persistence - SQLite storage for audit trail

Maintains cryptographic integrity while providing persistent storage.
Critical for EU AI Act Article 12 compliance (10-year retention).
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from lexecon.ledger.chain import LedgerEntry


class LedgerStorage:
    """Persistent storage for audit ledger using SQLite.

    Features:
    - Automatic saving on each append
    - Cryptographic chain integrity preserved
    - Query by event type, date range, etc.
    - Thread-safe operations
    """

    def __init__(self, db_path: str = "lexecon_ledger.db"):
        """Initialize storage with SQLite database."""
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Main ledger entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ledger_entries (
                entry_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                data TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                entry_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Create indexes separately (SQLite syntax)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_event_type ON ledger_entries(event_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON ledger_entries(timestamp)
        """)

        # Metadata table for chain verification
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ledger_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def save_entry(self, entry: LedgerEntry) -> None:
        """Save a single ledger entry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO ledger_entries
                (entry_id, event_type, timestamp, data, previous_hash, entry_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.entry_id,
                entry.event_type,
                entry.timestamp,
                json.dumps(entry.data),
                entry.previous_hash,
                entry.entry_hash,
                datetime.utcnow().isoformat(),
            ))

            # Update metadata with latest hash
            cursor.execute("""
                INSERT OR REPLACE INTO ledger_metadata (key, value, updated_at)
                VALUES ('latest_hash', ?, ?)
            """, (entry.entry_hash, datetime.utcnow().isoformat()))

            conn.commit()
        finally:
            conn.close()

    def load_all_entries(self) -> List[LedgerEntry]:
        """Load all ledger entries in chronological order."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT entry_id, event_type, timestamp, data, previous_hash, entry_hash
                FROM ledger_entries
                ORDER BY timestamp ASC
            """)

            entries = []
            for row in cursor.fetchall():
                stored_hash = row[5]

                # Create entry (which will calculate hash)
                entry = LedgerEntry(
                    entry_id=row[0],
                    event_type=row[1],
                    timestamp=row[2],
                    data=json.loads(row[3]),
                    previous_hash=row[4],
                )

                # Verify stored hash matches calculated hash
                if entry.entry_hash != stored_hash:
                    raise ValueError(f"Hash mismatch for entry {entry.entry_id}: stored={stored_hash}, calculated={entry.entry_hash}")

                entries.append(entry)

            return entries
        finally:
            conn.close()

    def get_entries_by_type(self, event_type: str) -> List[LedgerEntry]:
        """Get all entries of a specific event type."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT entry_id, event_type, timestamp, data, previous_hash, entry_hash
                FROM ledger_entries
                WHERE event_type = ?
                ORDER BY timestamp ASC
            """, (event_type,))

            entries = []
            for row in cursor.fetchall():
                stored_hash = row[5]

                entry = LedgerEntry(
                    entry_id=row[0],
                    event_type=row[1],
                    timestamp=row[2],
                    data=json.loads(row[3]),
                    previous_hash=row[4],
                )

                # Verify hash integrity
                if entry.entry_hash != stored_hash:
                    raise ValueError(f"Hash mismatch for entry {entry.entry_id}")

                entries.append(entry)

            return entries
        finally:
            conn.close()

    def get_entry_count(self) -> int:
        """Get total number of entries."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM ledger_entries")
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_latest_hash(self) -> Optional[str]:
        """Get the latest entry hash from metadata."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT value FROM ledger_metadata WHERE key = 'latest_hash'
            """)
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            conn.close()

    def verify_chain_integrity(self) -> bool:
        """Verify the entire chain's cryptographic integrity."""
        entries = self.load_all_entries()

        if not entries:
            return True

        # Verify each entry's hash
        for i, entry in enumerate(entries):
            calculated_hash = entry.calculate_hash()
            if calculated_hash != entry.entry_hash:
                return False

            # Verify chain linkage
            if i > 0 and entry.previous_hash != entries[i - 1].entry_hash:
                return False

        return True

    def export_to_json(self, output_path: str) -> None:
        """Export entire ledger to JSON file."""
        entries = self.load_all_entries()

        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "total_entries": len(entries),
            "entries": [entry.to_dict() for entry in entries],
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_statistics(self) -> dict:
        """Get storage statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Total entries
            cursor.execute("SELECT COUNT(*) FROM ledger_entries")
            total = cursor.fetchone()[0]

            # Entries by type
            cursor.execute("""
                SELECT event_type, COUNT(*)
                FROM ledger_entries
                GROUP BY event_type
            """)
            by_type = dict(cursor.fetchall())

            # Date range
            cursor.execute("""
                SELECT MIN(timestamp), MAX(timestamp)
                FROM ledger_entries
            """)
            date_range = cursor.fetchone()

            # Database file size
            db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0

            return {
                "total_entries": total,
                "entries_by_type": by_type,
                "oldest_entry": date_range[0],
                "newest_entry": date_range[1],
                "database_size_bytes": db_size,
                "database_path": self.db_path,
                "chain_integrity": self.verify_chain_integrity(),
            }
        finally:
            conn.close()
