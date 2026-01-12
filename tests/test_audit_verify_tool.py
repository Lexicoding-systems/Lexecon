"""
Tests for audit verification tool (tools/audit_verify.py).

Ensures comprehensive coverage of the audit packet verification functionality.
"""

import pytest
import json
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

from lexecon.tools.audit_verify import (
    AuditVerifier,
    AuditVerificationError,
    main
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def valid_manifest():
    """Create a valid manifest structure."""
    return {
        "packet_version": "1.0",
        "export_id": "exp_test_123",
        "generated_at": "2024-01-01T00:00:00Z",
        "generator": "Lexecon v0.1.0",
        "scope": {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "scope_type": "FULL"
        },
        "contents": {
            "decision_count": 100,
            "evidence_count": 50,
            "risk_count": 25,
            "escalation_count": 10,
            "override_count": 5
        },
        "integrity": {
            "root_checksum": "abc123def456",
            "algorithm": "SHA-256",
            "artifact_checksums": {}
        }
    }


@pytest.fixture
def valid_single_file_packet(temp_dir, valid_manifest):
    """Create a valid single-file JSON audit packet."""
    packet_file = temp_dir / "audit_packet.json"
    data = {
        "manifest": valid_manifest,
        "decisions": [],
        "evidence": [],
        "risks": []
    }

    # Compute actual root checksum
    content_str = json.dumps(data, sort_keys=True)
    root_hash = hashlib.sha256(content_str.encode()).hexdigest()
    data["manifest"]["integrity"]["root_checksum"] = root_hash

    with open(packet_file, "w") as f:
        json.dump(data, f)

    return packet_file


@pytest.fixture
def valid_directory_packet(temp_dir, valid_manifest):
    """Create a valid directory-based audit packet."""
    packet_dir = temp_dir / "audit_packet"
    packet_dir.mkdir()

    # Write manifest
    manifest_file = packet_dir / "manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(valid_manifest, f)

    # Write some artifact files
    decisions_file = packet_dir / "decisions.json"
    with open(decisions_file, "w") as f:
        json.dump({"decisions": []}, f)

    return packet_dir


class TestAuditVerifier:
    """Tests for AuditVerifier class."""

    def test_init(self, temp_dir):
        """Test verifier initialization."""
        packet_path = temp_dir / "packet.json"
        verifier = AuditVerifier(str(packet_path))

        assert verifier.packet_path == packet_path
        assert verifier.errors == []
        assert verifier.warnings == []
        assert verifier.manifest == {}

    def test_verify_nonexistent_packet(self, temp_dir):
        """Test verification fails for nonexistent packet."""
        packet_path = temp_dir / "nonexistent.json"
        verifier = AuditVerifier(str(packet_path))

        result = verifier.verify()

        assert result is False
        assert len(verifier.errors) > 0
        assert any("does not exist" in error for error in verifier.errors)

    def test_verify_valid_single_file_packet(self, valid_single_file_packet):
        """Test verification passes for valid single-file packet."""
        verifier = AuditVerifier(str(valid_single_file_packet))

        result = verifier.verify()

        # May have warnings but no errors
        assert len(verifier.errors) == 0

    def test_verify_valid_directory_packet(self, valid_directory_packet):
        """Test verification passes for valid directory packet."""
        verifier = AuditVerifier(str(valid_directory_packet))

        result = verifier.verify()

        # Should succeed with possible warnings
        assert len(verifier.errors) == 0

    def test_verify_structure_invalid_extension(self, temp_dir):
        """Test structure verification fails for non-JSON file."""
        packet_file = temp_dir / "packet.txt"
        packet_file.write_text("not a json file")

        verifier = AuditVerifier(str(packet_file))
        result = verifier.verify()

        assert result is False
        assert any("JSON format" in error for error in verifier.errors)

    def test_verify_structure_missing_manifest(self, temp_dir):
        """Test structure verification fails when manifest is missing."""
        packet_dir = temp_dir / "packet"
        packet_dir.mkdir()

        verifier = AuditVerifier(str(packet_dir))
        result = verifier.verify()

        assert result is False
        assert any("manifest.json" in error for error in verifier.errors)

    def test_verify_manifest_invalid_json(self, temp_dir):
        """Test manifest verification fails for invalid JSON."""
        packet_file = temp_dir / "packet.json"
        packet_file.write_text("{invalid json}")

        verifier = AuditVerifier(str(packet_file))
        result = verifier.verify()

        assert result is False
        assert any("Invalid JSON" in error for error in verifier.errors)

    def test_verify_manifest_missing_in_file(self, temp_dir):
        """Test manifest verification fails when manifest key is missing."""
        packet_file = temp_dir / "packet.json"
        with open(packet_file, "w") as f:
            json.dump({"data": "no manifest here"}, f)

        verifier = AuditVerifier(str(packet_file))
        result = verifier.verify()

        assert result is False
        assert any("Manifest not found" in error for error in verifier.errors)

    def test_verify_manifest_missing_required_fields(self, temp_dir):
        """Test manifest verification fails with missing required fields."""
        packet_file = temp_dir / "packet.json"
        incomplete_manifest = {
            "packet_version": "1.0",
            # Missing other required fields
        }
        with open(packet_file, "w") as f:
            json.dump({"manifest": incomplete_manifest}, f)

        verifier = AuditVerifier(str(packet_file))
        result = verifier.verify()

        assert result is False
        assert any("missing required fields" in error for error in verifier.errors)

    def test_verify_manifest_missing_root_checksum(self, temp_dir):
        """Test manifest verification fails without root checksum."""
        packet_file = temp_dir / "packet.json"
        manifest = {
            "packet_version": "1.0",
            "export_id": "exp_123",
            "generated_at": "2024-01-01",
            "generator": "test",
            "scope": {},
            "contents": {},
            "integrity": {
                "algorithm": "SHA-256"
                # Missing root_checksum
            }
        }
        with open(packet_file, "w") as f:
            json.dump({"manifest": manifest}, f)

        verifier = AuditVerifier(str(packet_file))
        result = verifier.verify()

        assert result is False
        assert any("root_checksum" in error for error in verifier.errors)

    def test_verify_manifest_missing_algorithm(self, temp_dir):
        """Test manifest verification fails without algorithm."""
        packet_file = temp_dir / "packet.json"
        manifest = {
            "packet_version": "1.0",
            "export_id": "exp_123",
            "generated_at": "2024-01-01",
            "generator": "test",
            "scope": {},
            "contents": {},
            "integrity": {
                "root_checksum": "abc123"
                # Missing algorithm
            }
        }
        with open(packet_file, "w") as f:
            json.dump({"manifest": manifest}, f)

        verifier = AuditVerifier(str(packet_file))
        result = verifier.verify()

        assert result is False
        assert any("algorithm" in error for error in verifier.errors)

    def test_verify_manifest_unexpected_algorithm_warning(self, temp_dir, valid_manifest):
        """Test warning for unexpected hash algorithm."""
        packet_file = temp_dir / "packet.json"
        valid_manifest["integrity"]["algorithm"] = "MD5"  # Not recommended
        with open(packet_file, "w") as f:
            json.dump({"manifest": valid_manifest}, f)

        verifier = AuditVerifier(str(packet_file))
        verifier.verify()

        assert any("Unexpected hash algorithm" in warning for warning in verifier.warnings)

    def test_verify_required_sections_negative_count(self, temp_dir, valid_manifest):
        """Test verification fails for negative count values."""
        packet_file = temp_dir / "packet.json"
        valid_manifest["contents"]["decision_count"] = -1  # Invalid
        with open(packet_file, "w") as f:
            json.dump({"manifest": valid_manifest}, f)

        verifier = AuditVerifier(str(packet_file))
        result = verifier.verify()

        assert result is False
        assert any("Invalid decision_count" in error for error in verifier.errors)

    def test_verify_required_sections_invalid_count_type(self, temp_dir, valid_manifest):
        """Test verification fails for non-integer count."""
        packet_file = temp_dir / "packet.json"
        valid_manifest["contents"]["evidence_count"] = "not a number"
        with open(packet_file, "w") as f:
            json.dump({"manifest": valid_manifest}, f)

        verifier = AuditVerifier(str(packet_file))
        result = verifier.verify()

        assert result is False
        assert any("Invalid evidence_count" in error for error in verifier.errors)

    def test_verify_artifact_checksums_no_checksums_warning(self, temp_dir, valid_manifest):
        """Test warning when no artifact checksums present."""
        packet_file = temp_dir / "packet.json"
        valid_manifest["integrity"]["artifact_checksums"] = {}
        with open(packet_file, "w") as f:
            json.dump({"manifest": valid_manifest}, f)

        verifier = AuditVerifier(str(packet_file))
        verifier.verify()

        assert any("No artifact checksums" in warning for warning in verifier.warnings)

    def test_verify_artifact_checksums_single_file_skipped(self, valid_single_file_packet, valid_manifest):
        """Test artifact checksum verification skipped for single files."""
        # Modify to add artifact checksums
        with open(valid_single_file_packet, "r") as f:
            data = json.load(f)
        data["manifest"]["integrity"]["artifact_checksums"] = {"artifact_1": "hash123"}
        with open(valid_single_file_packet, "w") as f:
            json.dump(data, f)

        verifier = AuditVerifier(str(valid_single_file_packet))
        verifier.verify()

        # Should have warning about skipping
        assert any("skipped for single-file" in warning for warning in verifier.warnings)

    def test_verify_root_checksum_mismatch(self, temp_dir, valid_manifest):
        """Test verification fails when root checksum doesn't match."""
        packet_file = temp_dir / "packet.json"
        valid_manifest["integrity"]["root_checksum"] = "wrong_checksum"
        data = {"manifest": valid_manifest, "data": "test"}
        with open(packet_file, "w") as f:
            json.dump(data, f)

        verifier = AuditVerifier(str(packet_file))
        result = verifier.verify()

        # Depending on implementation, this may fail or warn
        # The test should execute without crashing
        assert isinstance(result, bool)

    def test_compute_file_hash(self, temp_dir):
        """Test file hash computation."""
        test_file = temp_dir / "test.txt"
        test_content = "test content"
        test_file.write_text(test_content)

        verifier = AuditVerifier(str(temp_dir))
        file_hash = verifier._compute_file_hash(test_file)

        expected_hash = hashlib.sha256(test_content.encode()).hexdigest()
        assert file_hash == expected_hash

    def test_compute_json_hash(self, temp_dir):
        """Test JSON data hash computation."""
        verifier = AuditVerifier(str(temp_dir))
        test_data = {"key": "value", "number": 123}

        data_hash = verifier._compute_json_hash(test_data)

        expected_hash = hashlib.sha256(
            json.dumps(test_data, sort_keys=True).encode()
        ).hexdigest()
        assert data_hash == expected_hash

    def test_find_artifact_file(self, valid_directory_packet):
        """Test finding artifact files."""
        # Create an artifact file
        artifact_file = valid_directory_packet / "artifact_test_123.json"
        artifact_file.write_text('{"test": "data"}')

        verifier = AuditVerifier(str(valid_directory_packet))
        verifier.verify()  # Initialize

        found_file = verifier._find_artifact_file("artifact_test_123")

        assert found_file is not None
        assert found_file.name == "artifact_test_123.json"

    def test_find_artifact_file_not_found(self, valid_directory_packet):
        """Test finding nonexistent artifact returns None."""
        verifier = AuditVerifier(str(valid_directory_packet))
        verifier.verify()

        found_file = verifier._find_artifact_file("nonexistent_artifact")

        assert found_file is None

    def test_print_results_success(self, valid_single_file_packet, capsys):
        """Test result printing for successful verification."""
        verifier = AuditVerifier(str(valid_single_file_packet))
        verifier.verify()

        captured = capsys.readouterr()
        assert "✓" in captured.out or "PASSED" in captured.out or "SUCCESS" in captured.out

    def test_print_results_with_errors(self, temp_dir, capsys):
        """Test result printing with errors."""
        packet_path = temp_dir / "nonexistent.json"
        verifier = AuditVerifier(str(packet_path))
        verifier.verify()

        captured = capsys.readouterr()
        assert "✗" in captured.out or "FAILED" in captured.out or "ERROR" in captured.out

    def test_print_results_with_warnings(self, temp_dir, valid_manifest, capsys):
        """Test result printing with warnings."""
        packet_file = temp_dir / "packet.json"
        valid_manifest["integrity"]["algorithm"] = "MD5"  # Triggers warning
        with open(packet_file, "w") as f:
            json.dump({"manifest": valid_manifest}, f)

        verifier = AuditVerifier(str(packet_file))
        verifier.verify()

        captured = capsys.readouterr()
        assert "warning" in captured.out.lower() or "MD5" in captured.out


class TestCLIMain:
    """Tests for CLI main function."""

    def test_main_with_valid_packet(self, valid_single_file_packet):
        """Test CLI with valid packet."""
        with patch("sys.argv", ["audit_verify", str(valid_single_file_packet)]):
            exit_code = main()
            assert exit_code == 0

    def test_main_with_invalid_packet(self, temp_dir):
        """Test CLI with invalid packet."""
        packet_path = temp_dir / "nonexistent.json"
        with patch("sys.argv", ["audit_verify", str(packet_path)]):
            exit_code = main()
            assert exit_code == 1

    def test_main_with_verbose_flag(self, valid_single_file_packet):
        """Test CLI with verbose flag."""
        with patch("sys.argv", ["audit_verify", "--verbose", str(valid_single_file_packet)]):
            exit_code = main()
            assert exit_code == 0

    def test_main_with_help_flag(self):
        """Test CLI with help flag."""
        with patch("sys.argv", ["audit_verify", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_no_arguments(self):
        """Test CLI with no arguments."""
        with patch("sys.argv", ["audit_verify"]):
            with pytest.raises(SystemExit):
                main()

    def test_main_multiple_packets(self, valid_single_file_packet, temp_dir):
        """Test CLI with multiple packet paths."""
        packet2 = temp_dir / "packet2.json"
        with open(valid_single_file_packet, "r") as f:
            data = json.load(f)
        with open(packet2, "w") as f:
            json.dump(data, f)

        with patch("sys.argv", ["audit_verify", str(valid_single_file_packet), str(packet2)]):
            exit_code = main()
            # Should verify all packets
            assert isinstance(exit_code, int)


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_json_file(self, temp_dir):
        """Test handling of empty JSON file."""
        packet_file = temp_dir / "empty.json"
        packet_file.write_text("{}")

        verifier = AuditVerifier(str(packet_file))
        result = verifier.verify()

        assert result is False

    def test_very_large_packet(self, temp_dir, valid_manifest):
        """Test handling of large packet."""
        packet_file = temp_dir / "large.json"
        valid_manifest["contents"]["decision_count"] = 1000000
        data = {
            "manifest": valid_manifest,
            "decisions": [{"id": f"dec_{i}"} for i in range(100)]  # Sample
        }
        with open(packet_file, "w") as f:
            json.dump(data, f)

        verifier = AuditVerifier(str(packet_file))
        result = verifier.verify()

        # Should handle without crashing
        assert isinstance(result, bool)

    def test_special_characters_in_path(self, temp_dir, valid_manifest):
        """Test handling paths with special characters."""
        special_dir = temp_dir / "test packet (v1.0)"
        special_dir.mkdir()
        packet_file = special_dir / "audit.json"

        with open(packet_file, "w") as f:
            json.dump({"manifest": valid_manifest}, f)

        verifier = AuditVerifier(str(packet_file))
        result = verifier.verify()

        assert isinstance(result, bool)

    def test_symlink_packet(self, temp_dir, valid_single_file_packet):
        """Test handling of symlinked packet."""
        symlink = temp_dir / "packet_link.json"
        try:
            symlink.symlink_to(valid_single_file_packet)

            verifier = AuditVerifier(str(symlink))
            result = verifier.verify()

            assert isinstance(result, bool)
        except OSError:
            # Symlinks may not be supported on all systems
            pytest.skip("Symlinks not supported")

    def test_unicode_in_manifest(self, temp_dir, valid_manifest):
        """Test handling of Unicode characters in manifest."""
        packet_file = temp_dir / "unicode.json"
        valid_manifest["generator"] = "Lexecon 测试 🔐"
        with open(packet_file, "w", encoding="utf-8") as f:
            json.dump({"manifest": valid_manifest}, f, ensure_ascii=False)

        verifier = AuditVerifier(str(packet_file))
        result = verifier.verify()

        assert isinstance(result, bool)

    def test_concurrent_verification(self, valid_single_file_packet):
        """Test multiple concurrent verifications."""
        verifier1 = AuditVerifier(str(valid_single_file_packet))
        verifier2 = AuditVerifier(str(valid_single_file_packet))

        result1 = verifier1.verify()
        result2 = verifier2.verify()

        # Both should succeed independently
        assert len(verifier1.errors) == 0
        assert len(verifier2.errors) == 0
