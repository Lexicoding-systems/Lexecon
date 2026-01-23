"""Response Verification Utilities

Tools for verifying governance decisions, capability tokens, and ledger entries.
"""

from datetime import datetime
from typing import Any, Dict, Optional

import requests


class GovernanceVerifier:
    """Verify governance responses and audit trail."""

    def __init__(self, governance_url: str = "http://localhost:8000"):
        """Initialize verifier.

        Args:
            governance_url: Base URL of Lexecon governance API
        """
        self.governance_url = governance_url.rstrip("/")

    def verify_decision(self, decision_response: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a decision response against the ledger.

        Args:
            decision_response: The decision response to verify

        Returns:
            Verification result with validity status
        """
        ledger_entry_hash = decision_response.get("ledger_entry_hash")

        if not ledger_entry_hash:
            return {
                "valid": False,
                "error": "No ledger entry hash in decision",
            }

        try:
            response = requests.post(
                f"{self.governance_url}/decide/verify",
                json=decision_response,
                timeout=5,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            return {
                "valid": False,
                "error": f"Verification failed: {e!s}",
            }

    def verify_ledger_integrity(self) -> Dict[str, Any]:
        """Verify the entire ledger chain integrity.

        Returns:
            Integrity verification result
        """
        try:
            response = requests.get(
                f"{self.governance_url}/ledger/verify",
                timeout=5,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            return {
                "valid": False,
                "error": f"Ledger verification failed: {e!s}",
            }

    def get_audit_report(self) -> Dict[str, Any]:
        """Get comprehensive audit report.

        Returns:
            Audit report with statistics and integrity check
        """
        try:
            response = requests.get(
                f"{self.governance_url}/ledger/report",
                timeout=5,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to retrieve audit report: {e!s}",
            }

    def verify_capability_token(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a capability token's validity.

        Args:
            token: The capability token to verify

        Returns:
            Verification result
        """
        # Check required fields
        required_fields = ["token_id", "scope", "expiry", "policy_version_hash"]
        missing = [f for f in required_fields if f not in token]

        if missing:
            return {
                "valid": False,
                "error": f"Missing required fields: {', '.join(missing)}",
            }

        # Check expiry
        try:
            expiry = datetime.fromisoformat(token["expiry"])
            if datetime.utcnow() >= expiry:
                return {
                    "valid": False,
                    "error": "Token has expired",
                    "expired_at": token["expiry"],
                }
        except ValueError as e:
            return {
                "valid": False,
                "error": f"Invalid expiry format: {e!s}",
            }

        # Check scope
        scope = token.get("scope", {})
        if not scope.get("action") or not scope.get("tool"):
            return {
                "valid": False,
                "error": "Token scope is incomplete",
            }

        return {
            "valid": True,
            "token_id": token["token_id"],
            "scope": scope,
            "time_remaining": (expiry - datetime.utcnow()).total_seconds(),
            "policy_version": token["policy_version_hash"],
        }

    def verify_policy_version(
        self,
        policy_hash: str,
        expected_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Verify policy version hash.

        Args:
            policy_hash: The policy hash to verify
            expected_hash: Optional expected hash to compare against

        Returns:
            Verification result
        """
        # Get current policy info
        try:
            response = requests.get(
                f"{self.governance_url}/policies",
                timeout=5,
            )
            response.raise_for_status()
            policy_info = response.json()

            current_hash = policy_info.get("policy_hash")

            result = {
                "current_policy_hash": current_hash,
                "provided_hash": policy_hash,
                "matches_current": current_hash == policy_hash,
            }

            if expected_hash:
                result["expected_hash"] = expected_hash
                result["matches_expected"] = policy_hash == expected_hash

            return result

        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to verify policy version: {e!s}",
            }


def verify_governance_response(
    response: Dict[str, Any],
    governance_url: str = "http://localhost:8000",
) -> bool:
    """Quick verification of a governance response.

    Args:
        response: The governance response to verify
        governance_url: Governance API URL

    Returns:
        True if response is valid, False otherwise
    """
    verifier = GovernanceVerifier(governance_url)

    # Verify decision if ledger entry exists
    if "ledger_entry_hash" in response:
        decision_verification = verifier.verify_decision(response)
        if not decision_verification.get("verified", False):
            return False

    # Verify capability token if present
    if "capability_token" in response:
        token_verification = verifier.verify_capability_token(response["capability_token"])
        if not token_verification.get("valid", False):
            return False

    return True


# Example usage
if __name__ == "__main__":
    verifier = GovernanceVerifier()

    # Verify ledger integrity
    print("=== Ledger Integrity Check ===")
    integrity = verifier.verify_ledger_integrity()
    print(f"Valid: {integrity.get('valid', False)}")
    print(f"Entries: {integrity.get('entries_verified', 0)}\n")

    # Get audit report
    print("=== Audit Report ===")
    report = verifier.get_audit_report()
    if "error" not in report:
        print(f"Total Entries: {report.get('total_entries', 0)}")
        print(f"Integrity: {report.get('integrity_valid', False)}")
        print(f"Event Types: {report.get('event_type_counts', {})}\n")

    # Example token verification
    print("=== Token Verification Example ===")
    example_token = {
        "token_id": "tok_example123",
        "scope": {"action": "search", "tool": "web_search"},
        "expiry": "2025-12-31T23:59:59",
        "policy_version_hash": "abc123...",
    }
    token_result = verifier.verify_capability_token(example_token)
    print(f"Valid: {token_result.get('valid', False)}")
    if token_result.get("valid"):
        print(f"Time Remaining: {token_result.get('time_remaining', 0):.0f} seconds")
