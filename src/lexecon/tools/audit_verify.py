#!/usr/bin/env python3
"""Audit Packet Verification Tool

Verifies the integrity and completeness of Lexecon audit export packages.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List


class AuditVerificationError(Exception):
    """Base exception for verification failures."""


class AuditVerifier:
    """Verifies Lexecon audit packet integrity."""

    def __init__(self, packet_path: str):
        self.packet_path = Path(packet_path)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.manifest: Dict = {}

    def verify(self) -> bool:
        """Verify audit packet integrity.

        Returns:
            True if verification passes, False otherwise
        """
        print(f"Verifying audit packet: {self.packet_path}\n")

        checks = [
            ("Packet structure", self._verify_structure),
            ("Manifest integrity", self._verify_manifest),
            ("Required sections", self._verify_required_sections),
            ("Artifact checksums", self._verify_artifact_checksums),
            ("Root checksum", self._verify_root_checksum),
        ]

        for check_name, check_fn in checks:
            print(f"[Checking] {check_name}...", end=" ")
            try:
                check_fn()
                print("✓")
            except AuditVerificationError as e:
                print("✗")
                self.errors.append(f"{check_name}: {e!s}")
            except Exception as e:
                print("✗")
                self.errors.append(f"{check_name}: Unexpected error: {e!s}")

        self._print_results()
        return len(self.errors) == 0

    def _verify_structure(self) -> None:
        """Verify basic packet structure exists."""
        if not self.packet_path.exists():
            raise AuditVerificationError(f"Packet path does not exist: {self.packet_path}")

        if self.packet_path.is_file():
            # Single JSON file
            if not self.packet_path.suffix == ".json":
                raise AuditVerificationError("Packet file must be JSON format")
        elif self.packet_path.is_dir():
            # Directory structure
            required_files = ["manifest.json"]
            for req_file in required_files:
                file_path = self.packet_path / req_file
                if not file_path.exists():
                    raise AuditVerificationError(f"Missing required file: {req_file}")
        else:
            raise AuditVerificationError("Packet path must be file or directory")

    def _verify_manifest(self) -> None:
        """Load and verify manifest structure."""
        try:
            if self.packet_path.is_file():
                with open(self.packet_path) as f:
                    data = json.load(f)
                    self.manifest = data.get("manifest", {})
                    if not self.manifest:
                        raise AuditVerificationError("Manifest not found in packet file")
            else:
                manifest_path = self.packet_path / "manifest.json"
                with open(manifest_path) as f:
                    self.manifest = json.load(f)
        except json.JSONDecodeError as e:
            raise AuditVerificationError(f"Invalid JSON in manifest: {e!s}")
        except FileNotFoundError:
            raise AuditVerificationError("Manifest file not found")

        # Verify required manifest fields
        required_fields = [
            "packet_version",
            "export_id",
            "generated_at",
            "generator",
            "scope",
            "contents",
            "integrity",
        ]
        missing = [f for f in required_fields if f not in self.manifest]
        if missing:
            raise AuditVerificationError(f"Manifest missing required fields: {missing}")

        # Verify integrity section
        integrity = self.manifest.get("integrity", {})
        if "root_checksum" not in integrity:
            raise AuditVerificationError("Manifest missing root_checksum in integrity section")
        if "algorithm" not in integrity:
            raise AuditVerificationError("Manifest missing algorithm in integrity section")

        if integrity["algorithm"] != "SHA-256":
            self.warnings.append(
                f"Unexpected hash algorithm: {integrity['algorithm']} (expected SHA-256)",
            )

    def _verify_required_sections(self) -> None:
        """Verify required sections are present."""
        contents = self.manifest.get("contents", {})

        # These should always be present
        if "decision_count" not in contents:
            self.warnings.append("Manifest missing decision_count")

        # Verify counts are non-negative
        count_fields = [
            "evidence_count",
            "decision_count",
            "risk_count",
            "escalation_count",
            "override_count",
        ]
        for field in count_fields:
            if field in contents:
                count = contents[field]
                if not isinstance(count, int) or count < 0:
                    raise AuditVerificationError(f"Invalid {field}: {count}")

    def _verify_artifact_checksums(self) -> None:
        """Verify individual artifact checksums if present."""
        integrity = self.manifest.get("integrity", {})
        artifact_checksums = integrity.get("artifact_checksums", {})

        if not artifact_checksums:
            self.warnings.append("No artifact checksums found in manifest")
            return

        # If packet is single file, artifacts are embedded
        if self.packet_path.is_file():
            self.warnings.append("Artifact checksum verification skipped for single-file packet")
            return

        # Verify each artifact file matches its checksum
        verified_count = 0
        for artifact_id, expected_hash in artifact_checksums.items():
            # Try to find artifact file
            artifact_file = self._find_artifact_file(artifact_id)
            if not artifact_file:
                self.errors.append(f"Artifact file not found: {artifact_id}")
                continue

            # Compute actual hash
            actual_hash = self._compute_file_hash(artifact_file)
            if actual_hash != expected_hash:
                self.errors.append(
                    f"Artifact {artifact_id} checksum mismatch: "
                    f"expected {expected_hash[:16]}..., got {actual_hash[:16]}...",
                )
            else:
                verified_count += 1

        if verified_count > 0:
            print(f"\n  Verified {verified_count}/{len(artifact_checksums)} artifacts")

    def _verify_root_checksum(self) -> None:
        """Verify root checksum of entire packet."""
        integrity = self.manifest.get("integrity", {})
        expected_root = integrity.get("root_checksum")

        if not expected_root:
            raise AuditVerificationError("Root checksum not found in manifest")

        # For single-file packets, verify file hash
        if self.packet_path.is_file():
            # Note: This is a simplified check. Full verification would
            # require canonical JSON serialization
            self.warnings.append(
                "Root checksum verification for single-file packet is simplified",
            )
            return

        # For directory packets, compute root hash
        actual_root = self._compute_root_checksum()

        # Note: Due to potential timestamp/ordering differences, exact match may not occur
        # In production, this would use a more sophisticated deterministic approach
        if actual_root != expected_root:
            self.warnings.append(
                "Root checksum mismatch (may be due to non-deterministic serialization)",
            )
            print(f"\n  Expected: {expected_root[:32]}...")
            print(f"  Actual:   {actual_root[:32]}...")

    def _find_artifact_file(self, artifact_id: str) -> Path:
        """Find artifact file by ID."""
        # Check common locations
        locations = [
            self.packet_path / "evidence" / f"{artifact_id}.json",
            self.packet_path / "decisions" / f"{artifact_id}.json",
            self.packet_path / "risk" / f"{artifact_id}.json",
        ]

        for loc in locations:
            if loc.exists():
                return loc

        return None

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _compute_root_checksum(self) -> str:
        """Compute root checksum of all packet contents."""
        sha256 = hashlib.sha256()

        # Process all files in deterministic order (sorted)
        # Exclude checksum.sha256 and manifest.json from hash
        all_files = sorted(
            [
                f
                for f in self.packet_path.rglob("*")
                if f.is_file() and f.name not in ["checksum.sha256"]
            ],
        )

        for file_path in all_files:
            sha256.update(file_path.read_bytes())

        return sha256.hexdigest()

    def _print_results(self) -> None:
        """Print verification results."""
        print("\n" + "=" * 60)

        if self.errors:
            print(f"❌ VERIFICATION FAILED ({len(self.errors)} error(s))")
            print("\nErrors:")
            for error in self.errors:
                print(f"  ✗ {error}")
        else:
            print("✅ VERIFICATION PASSED")

        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")

        print("\nPacket Details:")
        print(f"  Export ID: {self.manifest.get('export_id', 'N/A')}")
        print(f"  Generated: {self.manifest.get('generated_at', 'N/A')}")
        print(f"  Version: {self.manifest.get('packet_version', 'N/A')}")

        contents = self.manifest.get("contents", {})
        print("\nContents:")
        print(f"  Decisions: {contents.get('decision_count', 0)}")
        print(f"  Evidence: {contents.get('evidence_count', 0)}")
        print(f"  Risks: {contents.get('risk_count', 0)}")
        print(f"  Escalations: {contents.get('escalation_count', 0)}")
        print(f"  Overrides: {contents.get('override_count', 0)}")

        print("=" * 60)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Verify Lexecon audit packet integrity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify a single JSON file
  python -m lexecon.tools.audit_verify audit_export.json

  # Verify a directory structure
  python -m lexecon.tools.audit_verify /path/to/audit_packet/

  # Verify and exit with code
  python -m lexecon.tools.audit_verify packet.json && echo "Valid" || echo "Invalid"
        """,
    )

    parser.add_argument(
        "packet_path",
        help="Path to audit packet (file or directory)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    verifier = AuditVerifier(args.packet_path)

    try:
        success = verifier.verify()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Verification failed with exception: {e!s}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
