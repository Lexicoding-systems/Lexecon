"""Usage Tracking Service - Enforces tier limits and tracks metered usage.

Free tier limits:
- 200 decisions per day per tenant
- 10 exports per month per tenant

Admin override available via LEXECON_BYPASS_LIMITS env var.
"""

import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Tuple


# Tier limits (hardcoded for speed, can be DB-driven later)
FREE_DECISIONS_PER_DAY = 200
FREE_EXPORTS_PER_MONTH = 10

# Admin override from env
BYPASS_LIMITS = os.getenv("LEXECON_BYPASS_LIMITS", "false").lower() in ("true", "1", "yes")


class UsageService:
    """Tracks and enforces usage limits per tenant."""

    def __init__(self, db_path: str = "lexecon_usage.db"):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self) -> None:
        """Initialize usage tracking tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Daily decisions counter
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tenant_usage_daily (
                    tenant_id TEXT NOT NULL,
                    day TEXT NOT NULL,  -- YYYY-MM-DD
                    decisions_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (tenant_id, day)
                )
            """)
            
            # Monthly exports counter
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tenant_usage_monthly (
                    tenant_id TEXT NOT NULL,
                    month TEXT NOT NULL,  -- YYYY-MM
                    exports_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (tenant_id, month)
                )
            """)
            
            conn.commit()

    def _get_today(self) -> str:
        """Get current date as YYYY-MM-DD."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _get_this_month(self) -> str:
        """Get current month as YYYY-MM."""
        return datetime.now(timezone.utc).strftime("%Y-%m")

    def increment_decisions(self, tenant_id: str) -> Tuple[bool, dict]:
        """Increment daily decision counter.
        
        Returns:
            (success, metadata) - success=False if limit exceeded
        """
        if BYPASS_LIMITS:
            return True, {"bypass": True}
        
        day = self._get_today()
        
        with sqlite3.connect(self.db_path) as conn:
            # Get or create counter
            cursor = conn.execute(
                "SELECT decisions_count FROM tenant_usage_daily WHERE tenant_id = ? AND day = ?",
                (tenant_id, day)
            )
            row = cursor.fetchone()
            
            if row is None:
                # First decision today
                conn.execute(
                    "INSERT INTO tenant_usage_daily (tenant_id, day, decisions_count) VALUES (?, ?, 1)",
                    (tenant_id, day)
                )
                current_count = 1
            else:
                current_count = row[0]
                if current_count >= FREE_DECISIONS_PER_DAY:
                    # Limit exceeded
                    return False, {
                        "code": "PLAN_LIMIT",
                        "metric": "decisions_per_day",
                        "limit": FREE_DECISIONS_PER_DAY,
                        "current": current_count,
                        "tenant_id": tenant_id,
                    }
                
                # Increment
                conn.execute(
                    "UPDATE tenant_usage_daily SET decisions_count = decisions_count + 1, updated_at = CURRENT_TIMESTAMP WHERE tenant_id = ? AND day = ?",
                    (tenant_id, day)
                )
                current_count += 1
            
            conn.commit()
        
        return True, {
            "current": current_count,
            "limit": FREE_DECISIONS_PER_DAY,
            "remaining": FREE_DECISIONS_PER_DAY - current_count,
        }

    def increment_exports(self, tenant_id: str) -> Tuple[bool, dict]:
        """Increment monthly export counter.
        
        Returns:
            (success, metadata) - success=False if limit exceeded
        """
        if BYPASS_LIMITS:
            return True, {"bypass": True}
        
        month = self._get_this_month()
        
        with sqlite3.connect(self.db_path) as conn:
            # Get or create counter
            cursor = conn.execute(
                "SELECT exports_count FROM tenant_usage_monthly WHERE tenant_id = ? AND month = ?",
                (tenant_id, month)
            )
            row = cursor.fetchone()
            
            if row is None:
                # First export this month
                conn.execute(
                    "INSERT INTO tenant_usage_monthly (tenant_id, month, exports_count) VALUES (?, ?, 1)",
                    (tenant_id, month)
                )
                current_count = 1
            else:
                current_count = row[0]
                if current_count >= FREE_EXPORTS_PER_MONTH:
                    # Limit exceeded
                    return False, {
                        "code": "PLAN_LIMIT",
                        "metric": "exports_per_month",
                        "limit": FREE_EXPORTS_PER_MONTH,
                        "current": current_count,
                        "tenant_id": tenant_id,
                    }
                
                # Increment
                conn.execute(
                    "UPDATE tenant_usage_monthly SET exports_count = exports_count + 1, updated_at = CURRENT_TIMESTAMP WHERE tenant_id = ? AND month = ?",
                    (tenant_id, month)
                )
                current_count += 1
            
            conn.commit()
        
        return True, {
            "current": current_count,
            "limit": FREE_EXPORTS_PER_MONTH,
            "remaining": FREE_EXPORTS_PER_MONTH - current_count,
        }

    def get_usage(self, tenant_id: str) -> dict:
        """Get current usage for a tenant."""
        day = self._get_today()
        month = self._get_this_month()
        
        with sqlite3.connect(self.db_path) as conn:
            # Daily decisions
            cursor = conn.execute(
                "SELECT decisions_count FROM tenant_usage_daily WHERE tenant_id = ? AND day = ?",
                (tenant_id, day)
            )
            row = cursor.fetchone()
            decisions_today = row[0] if row else 0
            
            # Monthly exports
            cursor = conn.execute(
                "SELECT exports_count FROM tenant_usage_monthly WHERE tenant_id = ? AND month = ?",
                (tenant_id, month)
            )
            row = cursor.fetchone()
            exports_this_month = row[0] if row else 0
        
        return {
            "tenant_id": tenant_id,
            "decisions": {
                "today": decisions_today,
                "limit": FREE_DECISIONS_PER_DAY,
                "remaining": FREE_DECISIONS_PER_DAY - decisions_today,
            },
            "exports": {
                "this_month": exports_this_month,
                "limit": FREE_EXPORTS_PER_MONTH,
                "remaining": FREE_EXPORTS_PER_MONTH - exports_this_month,
            },
            "bypass_enabled": BYPASS_LIMITS,
        }

    def can_create_decision(self, tenant_id: str) -> Tuple[bool, dict]:
        """Check if tenant can create a decision (without incrementing)."""
        if BYPASS_LIMITS:
            return True, {"bypass": True}
        
        day = self._get_today()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT decisions_count FROM tenant_usage_daily WHERE tenant_id = ? AND day = ?",
                (tenant_id, day)
            )
            row = cursor.fetchone()
            current_count = row[0] if row else 0
        
        if current_count >= FREE_DECISIONS_PER_DAY:
            return False, {
                "code": "PLAN_LIMIT",
                "metric": "decisions_per_day",
                "limit": FREE_DECISIONS_PER_DAY,
                "current": current_count,
                "tenant_id": tenant_id,
            }
        
        return True, {
            "current": current_count,
            "limit": FREE_DECISIONS_PER_DAY,
            "remaining": FREE_DECISIONS_PER_DAY - current_count,
        }

    def can_export(self, tenant_id: str) -> Tuple[bool, dict]:
        """Check if tenant can export (without incrementing)."""
        if BYPASS_LIMITS:
            return True, {"bypass": True}
        
        month = self._get_this_month()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT exports_count FROM tenant_usage_monthly WHERE tenant_id = ? AND month = ?",
                (tenant_id, month)
            )
            row = cursor.fetchone()
            current_count = row[0] if row else 0
        
        if current_count >= FREE_EXPORTS_PER_MONTH:
            return False, {
                "code": "PLAN_LIMIT",
                "metric": "exports_per_month",
                "limit": FREE_EXPORTS_PER_MONTH,
                "current": current_count,
                "tenant_id": tenant_id,
            }
        
        return True, {
            "current": current_count,
            "limit": FREE_EXPORTS_PER_MONTH,
            "remaining": FREE_EXPORTS_PER_MONTH - current_count,
        }
