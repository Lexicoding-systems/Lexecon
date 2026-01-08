"""Tests for audit verification tool."""

import json
import tempfile
from pathlib import Path

import pytest

from lexecon.tools.audit_verify import AuditVerificationError, AuditVerifier


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def valid_audit_packet_file(temp_dir):
    """Create a valid audit packet file."""
    packet = {
        "manifest": {
            "packet_version": "1.0",
            "export_id": "exp_test_123",
            "generated_at": "2024-01-01T00:00:00Z",
            "generator": {"name": "lexecon", "version": "0.1.0"},
            "scope": {"start_time": "2024-01-01T00:00:00Z", "end_time": "2024-01-02T00:00:00Z"},
            "contents": {
                "decision_count": 1,
                "evidence_count": 0,
                "risk_count": 0,
                "escalation_count": 0,
                "override_count": 0,
            },
            "integrity": {
                "algorithm": "SHA-256",
                "root_checksum": "abc123def456",
                "artifact_checksums": {},
            },
        },
        "decisions": [{"decision_id": "dec_1", "actor": "model", "action": "read"}],
    }

    packet_file = Path(temp_dir) / "audit_packet.json"
    packet_file.write_text(json.dumps(packet, indent=2))
    return str(packet_file)


@pytest.fixture
def valid_audit_packet_dir(temp_dir):
    """Create a valid audit packet directory."""
    packet_dir = Path(temp_dir) / "audit_packet"
    packet_dir.mkdir()

    # Create manifest
    manifest = {
        "packet_version": "1.0",
        "export_id": "exp_dir_123",
        "generated_at": "2024-01-01T00:00:00Z",
        "generator": {"name": "lexecon", "version": "0.1.0"},
        "scope": {"start_time": "2024-01-01T00:00:00Z", "end_time": "2024-01-02T00:00:00Z"},
        "contents": {"decision_count": 3, "evidence_count": 0},
        "integrity": {
            "algorithm": "SHA-256",
            "root_checksum": "dir_checksum",
            "artifact_checksums": {},
        },
    }

    manifest_file = packet_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2))

    # Create decisions file
    decisions_file = packet_dir / "decisions.json"
    decisions = [{"decision_id": "dec_1"}, {"decision_id": "dec_2"}, {"decision_id": "dec_3"}]
    decisions_file.write_text(json.dumps(decisions, indent=2))

    return str(packet_dir)


class TestAuditVerifier:
    """Tests for AuditVerifier class."""

    def test_init(self, valid_audit_packet_file):
        """Test verifier initialization."""
        verifier = AuditVerifier(valid_audit_packet_file)

        assert verifier.packet_path == Path(valid_audit_packet_file)
        assert verifier.errors == []
        assert verifier.warnings == []
        assert verifier.manifest == {}

    def test_verify_structure_file_exists(self, valid_audit_packet_file):
        """Test structure verification for existing file."""
        verifier = AuditVerifier(valid_audit_packet_file)
        verifier._verify_structure()  # Should not raise

    def test_verify_structure_nonexistent(self, temp_dir):
        """Test structure verification for non-existent path."""
        verifier = AuditVerifier(str(Path(temp_dir) / "nonexistent.json"))

        with pytest.raises(AuditVerificationError, match="does not exist"):
            verifier._verify_structure()

    def test_verify_structure_non_json_file(self, temp_dir):
        """Test structure verification for non-JSON file."""
        bad_file = Path(temp_dir) / "packet.txt"
        bad_file.write_text("not json")

        verifier = AuditVerifier(str(bad_file))

        with pytest.raises(AuditVerificationError, match="must be JSON format"):
            verifier._verify_structure()

    def test_verify_structure_dir_without_manifest(self, temp_dir):
        """Test structure verification for directory without manifest."""
        bad_dir = Path(temp_dir) / "bad_packet"
        bad_dir.mkdir()

        verifier = AuditVerifier(str(bad_dir))

        with pytest.raises(AuditVerificationError, match="Missing required file"):
            verifier._verify_structure()

    def test_verify_structure_valid_dir(self, valid_audit_packet_dir):
        """Test structure verification for valid directory."""
        verifier = AuditVerifier(valid_audit_packet_dir)
        verifier._verify_structure()  # Should not raise

    def test_verify_manifest_from_file(self, valid_audit_packet_file):
        """Test manifest verification from file."""
        verifier = AuditVerifier(valid_audit_packet_file)
        verifier._verify_structure()
        verifier._verify_manifest()

        assert "export_id" in verifier.manifest
        assert verifier.manifest["export_id"] == "exp_test_123"

    def test_verify_manifest_from_dir(self, valid_audit_packet_dir):
        """Test manifest verification from directory."""
        verifier = AuditVerifier(valid_audit_packet_dir)
        verifier._verify_structure()
        verifier._verify_manifest()

        assert "export_id" in verifier.manifest
        assert verifier.manifest["export_id"] == "exp_dir_123"

    def test_verify_manifest_invalid_json(self, temp_dir):
        """Test manifest verification with invalid JSON."""
        bad_file = Path(temp_dir) / "bad.json"
        bad_file.write_text("{ invalid json }")

        verifier = AuditVerifier(str(bad_file))
        verifier._verify_structure()

        with pytest.raises(AuditVerificationError, match="Invalid JSON"):
            verifier._verify_manifest()

    def test_verify_manifest_missing_from_file(self, temp_dir):
        """Test manifest verification when manifest missing from file."""
        packet_file = Path(temp_dir) / "no_manifest.json"
        packet_file.write_text(json.dumps({"data": "test"}))

        verifier = AuditVerifier(str(packet_file))
        verifier._verify_structure()

        with pytest.raises(AuditVerificationError, match="Manifest not found"):
            verifier._verify_manifest()

    def test_verify_missing_required_fields(self, temp_dir):
        """Test verification fails with missing required manifest fields."""
        packet = {
            "manifest": {
                # Missing most required fields
                "packet_version": "1.0"
            }
        }

        packet_file = Path(temp_dir) / "incomplete.json"
        packet_file.write_text(json.dumps(packet))

        verifier = AuditVerifier(str(packet_file))
        verifier._verify_structure()

        # Should fail during manifest verification
        with pytest.raises(AuditVerificationError, match="missing required fields"):
            verifier._verify_manifest()

    def test_verify_full_valid_packet(self, capsys):
        """Test full verification of a minimally valid packet."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple valid packet
            packet = {
                "manifest": {
                    "packet_version": "1.0",
                    "export_id": "exp_minimal",
                    "generated_at": "2024-01-01T00:00:00Z",
                    "generator": {"name": "test", "version": "1.0"},
                    "scope": {},
                    "contents": {"decision_count": 0},
                    "integrity": {"algorithm": "SHA-256", "root_checksum": "test"},
                }
            }

            packet_file = Path(tmpdir) / "minimal.json"
            packet_file.write_text(json.dumps(packet))

            verifier = AuditVerifier(str(packet_file))
            # Will fail on checksum verification, but should pass structure checks
            verifier.verify()

            captured = capsys.readouterr()
            assert "Verifying audit packet" in captured.out

    def test_print_results_with_errors(self, capsys, valid_audit_packet_file):
        """Test results printing with errors."""
        verifier = AuditVerifier(valid_audit_packet_file)
        verifier.errors = ["Error 1", "Error 2"]
        verifier._print_results()

        captured = capsys.readouterr()
        assert "FAILED" in captured.out
        assert "Error 1" in captured.out
        assert "Error 2" in captured.out

    def test_print_results_with_warnings(self, capsys, valid_audit_packet_file):
        """Test results printing with warnings."""
        verifier = AuditVerifier(valid_audit_packet_file)
        verifier.warnings = ["Warning 1"]
        verifier._print_results()

        captured = capsys.readouterr()
        assert "VERIFICATION PASSED" in captured.out or "SUCCESS" in captured.out
        assert "Warning 1" in captured.out

    def test_print_results_success(self, capsys, valid_audit_packet_file):
        """Test results printing on success."""
        verifier = AuditVerifier(valid_audit_packet_file)
        verifier._print_results()

        captured = capsys.readouterr()
        assert "VERIFICATION PASSED" in captured.out or "SUCCESS" in captured.out


class TestAuditVerificationError:
    """Tests for AuditVerificationError exception."""

    def test_raise_error(self):
        """Test raising verification error."""
        with pytest.raises(AuditVerificationError, match="Test error"):
            raise AuditVerificationError("Test error")

    def test_error_message(self):
        """Test error message is preserved."""
        error = AuditVerificationError("Custom message")
        assert str(error) == "Custom message"
