#!/usr/bin/env python3
"""SQLite to PostgreSQL Migration Script.

Migrates all Lexecon databases from SQLite to PostgreSQL.
Supports: lexecon_auth.db, lexecon_ledger.db, lexecon_responsibility.db
"""

import asyncio
import os
import sqlite3
import sys
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


class SQLiteToPostgresMigrator:
    """Migrator for SQLite to PostgreSQL."""

    def __init__(self, sqlite_path: str, postgres_url: str):
        """Initialize migrator.

        Args:
            sqlite_path: Path to SQLite database
            postgres_url: PostgreSQL connection URL
        """
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url.replace("postgresql://", "postgresql+asyncpg://")

        # Connect to SQLite
        self.sqlite_conn = sqlite3.connect(sqlite_path)
        self.sqlite_cursor = self.sqlite_conn.cursor()

        print(f"✓ Connected to SQLite: {sqlite_path}")
        print(f"✓ Target PostgreSQL: {postgres_url.split('@')[1] if '@' in postgres_url else postgres_url}")

    def get_tables(self) -> List[str]:
        """Get all table names from SQLite."""
        self.sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        return [row[0] for row in self.sqlite_cursor.fetchall()]

    def get_table_schema(self, table: str) -> List[Dict[str, Any]]:
        """Get table schema."""
        self.sqlite_cursor.execute(f"PRAGMA table_info({table})")
        columns = []
        for row in self.sqlite_cursor.fetchall():
            columns.append({
                "cid": row[0],
                "name": row[1],
                "type": row[2],
                "notnull": row[3],
                "default": row[4],
                "pk": row[5],
            })
        return columns

    def sqlite_type_to_postgres(self, sqlite_type: str) -> str:
        """Convert SQLite type to PostgreSQL type."""
        type_lower = sqlite_type.lower()

        if "int" in type_lower:
            return "INTEGER"
        if "char" in type_lower or "text" in type_lower or "clob" in type_lower:
            return "TEXT"
        if "blob" in type_lower:
            return "BYTEA"
        if "real" in type_lower or "float" in type_lower or "double" in type_lower:
            return "REAL"
        if "numeric" in type_lower or "decimal" in type_lower:
            return "NUMERIC"
        if "boolean" in type_lower:
            return "BOOLEAN"
        if "datetime" in type_lower:
            return "TIMESTAMP"
        return "TEXT"  # Default fallback

    async def create_postgres_table(self, table: str, schema: List[Dict[str, Any]]):
        """Create table in PostgreSQL."""
        columns_sql = []
        pks = []

        for col in schema:
            col_name = col["name"]
            col_type = self.sqlite_type_to_postgres(col["type"])
            constraints = []

            if col["pk"]:
                pks.append(col_name)

            if col["notnull"]:
                constraints.append("NOT NULL")

            if col["default"] is not None:
                constraints.append(f"DEFAULT {col['default']}")

            col_def = f"{col_name} {col_type} {' '.join(constraints)}".strip()
            columns_sql.append(col_def)

        if pks:
            columns_sql.append(f"PRIMARY KEY ({', '.join(pks)})")

        create_sql = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(columns_sql)})"

        engine = create_async_engine(self.postgres_url)
        async with engine.connect() as conn:
            await conn.execute(text(create_sql))
            await conn.commit()

        await engine.dispose()
        print(f"  ✓ Created table: {table}")

    async def migrate_table_data(self, table: str, schema: List[Dict[str, Any]]):
        """Migrate data from SQLite to PostgreSQL."""
        # Get column names
        col_names = [col["name"] for col in schema]

        # Fetch all data from SQLite
        self.sqlite_cursor.execute(f"SELECT {', '.join(col_names)} FROM {table}")
        rows = self.sqlite_cursor.fetchall()

        if not rows:
            print(f"  - No data to migrate for {table}")
            return

        # Build INSERT statements
        placeholders = ", ".join([f":{col}" for col in col_names])
        insert_sql = f"INSERT INTO {table} ({', '.join(col_names)}) VALUES ({placeholders})"

        # Insert into PostgreSQL
        engine = create_async_engine(self.postgres_url)
        async with engine.connect() as conn:
            for row in rows:
                data = dict(zip(col_names, row))
                await conn.execute(text(insert_sql), data)

            await conn.commit()

        await engine.dispose()
        print(f"  ✓ Migrated {len(rows)} rows to {table}")

    async def migrate(self) -> Dict[str, Any]:
        """Run full migration."""
        result = {
            "source": self.sqlite_path,
            "target": self.postgres_url,
            "tables": [],
        }

        try:
            # Get tables
            tables = self.get_tables()
            print(f"\nFound {len(tables)} tables to migrate:")

            for table in tables:
                print(f"\nMigrating table: {table}")

                # Get schema
                schema = self.get_table_schema(table)

                # Create table in PostgreSQL
                await self.create_postgres_table(table, schema)

                # Migrate data
                await self.migrate_table_data(table, schema)

                result["tables"].append({
                    "name": table,
                    "columns": len(schema),
                    "migrated": True,
                })

            result["success"] = True
            print("\n✓ Migration completed successfully!")

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            print(f"\n✗ Migration failed: {e}")
            raise

        finally:
            self.sqlite_conn.close()

        return result


async def migrate_all_databases(postgres_url: str):
    """Migrate all Lexecon databases."""
    databases = [
        ("lexecon_auth.db", "authentication"),
        ("lexecon_ledger.db", "ledger"),
        ("lexecon_responsibility.db", "responsibility"),
    ]

    results = {}

    for db_file, db_name in databases:
        if os.path.exists(db_file):
            print(f"\n{'='*60}")
            print(f"Migrating {db_name} database: {db_file}")
            print(f"{'='*60}")

            migrator = SQLiteToPostgresMigrator(db_file, postgres_url)
            results[db_name] = await migrator.migrate()
        else:
            print(f"Skipping {db_file} (not found)")
            results[db_name] = {"skipped": True}

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python migrate_sqlite_to_postgres.py <postgres_url>")
        print("Example: python migrate_sqlite_to_postgres.py postgresql://user:pass@localhost/lexecon")
        sys.exit(1)

    postgres_url = sys.argv[1]

    print("Lexecon SQLite → PostgreSQL Migration")
    print("=" * 60)

    async def main():
        results = await migrate_all_databases(postgres_url)

        print("\n" + "=" * 60)
        print("Migration Summary")
        print("=" * 60)

        for db_name, result in results.items():
            if result.get("skipped"):
                print(f"{db_name}: Skipped (not found)")
            elif result.get("success"):
                tables = result.get("tables", [])
                print(f"{db_name}: ✓ Success ({len(tables)} tables)")
            else:
                print(f"{db_name}: ✗ Failed - {result.get('error', 'Unknown error')}")

    asyncio.run(main())
