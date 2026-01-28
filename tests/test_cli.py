"""Tests for CLI commands."""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from lexecon.cli.main import cli


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def example_policy_file(temp_dir):
    """Create example policy file."""
    policy = {
        "mode": "strict",
        "terms": [
            {
                "term_id": "actor:model",
                "term_type": "actor",
                "label": "AI Model",
                "description": "AI model",
                "metadata": {},
            },
            {
                "term_id": "action:search",
                "term_type": "action",
                "label": "Search",
                "description": "Search action",
                "metadata": {},
            },
        ],
        "relations": [
            {
                "relation_id": "permits:actor:model:action:search",
                "relation_type": "permits",
                "source": "actor:model",
                "target": "action:search",
                "conditions": [],
                "metadata": {},
            },
        ],
    }

    policy_file = Path(temp_dir) / "policy.json"
    policy_file.write_text(json.dumps(policy, indent=2))
    return str(policy_file)


@pytest.fixture
def example_request_file(temp_dir):
    """Create example decision request file."""
    request = {
        "actor": "model",
        "proposed_action": "search",
        "tool": "web_search",
        "user_intent": "Research AI governance",
        "data_classes": [],
        "risk_level": 1,
        "context": {"query": "test"},
    }

    request_file = Path(temp_dir) / "request.json"
    request_file.write_text(json.dumps(request, indent=2))
    return str(request_file)


@pytest.fixture
def example_ledger_file(temp_dir):
    """Create example ledger file."""
    from lexecon.ledger.chain import LedgerChain

    ledger = LedgerChain()
    ledger.append("test_event", {"data": "test"})

    ledger_file = Path(temp_dir) / "ledger.json"
    ledger_file.write_text(json.dumps(ledger.to_dict(), indent=2))
    return str(ledger_file)


class TestCLIBasics:
    """Tests for basic CLI functionality."""

    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Lexecon - Lexical Governance Protocol" in result.output
        assert "Commands:" in result.output

    def test_cli_version(self, runner):
        """Test CLI version command."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestInitCommand:
    """Tests for init command."""

    def test_init_creates_node(self, runner, temp_dir):
        """Test init command creates node files."""
        result = runner.invoke(cli, ["init", "--node-id", "test-node", "--data-dir", temp_dir])

        assert result.exit_code == 0
        assert "Node 'test-node' initialized" in result.output

        # Check files were created
        data_path = Path(temp_dir)
        assert (data_path / "test-node.key").exists()
        assert (data_path / "test-node.pub").exists()
        assert (data_path / "test-node.json").exists()

        # Verify config content
        config_file = data_path / "test-node.json"
        config = json.loads(config_file.read_text())
        assert config["node_id"] == "test-node"
        assert "private_key_path" in config
        assert "public_key_path" in config
        assert "public_key_fingerprint" in config

    def test_init_without_node_id(self, runner):
        """Test init command without required node-id."""
        result = runner.invoke(cli, ["init"])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "Error" in result.output

    def test_init_custom_data_dir(self, runner, temp_dir):
        """Test init with custom data directory."""
        custom_dir = Path(temp_dir) / "custom"

        result = runner.invoke(
            cli, ["init", "--node-id", "custom-node", "--data-dir", str(custom_dir)],
        )

        assert result.exit_code == 0
        assert custom_dir.exists()
        assert (custom_dir / "custom-node.json").exists()


class TestDecideCommand:
    """Tests for decide command."""

    def test_decide_with_json_file(self, runner, example_request_file):
        """Test decide command with JSON file."""
        result = runner.invoke(cli, ["decide", "--json-file", example_request_file])

        assert result.exit_code == 0

        # Output should be valid JSON
        output = result.output
        decision = json.loads(output)
        assert "decision" in decision
        assert "reasoning" in decision
        assert "policy_version_hash" in decision

    def test_decide_with_cli_args(self, runner):
        """Test decide command with CLI arguments."""
        result = runner.invoke(
            cli,
            [
                "decide",
                "--actor",
                "model",
                "--action",
                "search",
                "--tool",
                "web_search",
                "--intent",
                "Test search",
            ],
        )

        assert result.exit_code == 0

        # Verify output is JSON
        decision = json.loads(result.output)
        assert "decision" in decision

    def test_decide_missing_args(self, runner):
        """Test decide without required arguments."""
        result = runner.invoke(cli, ["decide"])

        # Should fail - missing required args
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_decide_invalid_json_file(self, runner, temp_dir):
        """Test decide with invalid JSON file."""
        bad_file = Path(temp_dir) / "bad.json"
        bad_file.write_text("not valid json")

        result = runner.invoke(cli, ["decide", "--json-file", str(bad_file)])

        assert result.exit_code != 0

    def test_decide_nonexistent_file(self, runner):
        """Test decide with non-existent file."""
        result = runner.invoke(cli, ["decide", "--json-file", "/nonexistent/file.json"])

        assert result.exit_code != 0


class TestLoadPolicyCommand:
    """Tests for load-policy command."""

    def test_load_policy_success(self, runner, example_policy_file):
        """Test loading a valid policy."""
        result = runner.invoke(cli, ["load-policy", "--policy-file", example_policy_file])

        assert result.exit_code == 0
        assert "Policy loaded" in result.output
        assert "Terms:" in result.output
        assert "Relations:" in result.output
        assert "Policy hash:" in result.output

    def test_load_policy_missing_file(self, runner):
        """Test load-policy without file argument."""
        result = runner.invoke(cli, ["load-policy"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_load_policy_nonexistent_file(self, runner):
        """Test load-policy with non-existent file."""
        result = runner.invoke(cli, ["load-policy", "--policy-file", "/nonexistent/policy.json"])

        assert result.exit_code != 0

    def test_load_policy_invalid_json(self, runner, temp_dir):
        """Test load-policy with invalid JSON."""
        bad_file = Path(temp_dir) / "invalid.json"
        bad_file.write_text("{ invalid json")

        result = runner.invoke(cli, ["load-policy", "--policy-file", str(bad_file)])

        assert result.exit_code != 0

    def test_load_policy_empty_file(self, runner, temp_dir):
        """Test load-policy with empty policy."""
        empty_file = Path(temp_dir) / "empty.json"
        empty_file.write_text(json.dumps({"terms": [], "relations": []}))

        result = runner.invoke(cli, ["load-policy", "--policy-file", str(empty_file)])

        # Should succeed but with 0 terms/relations
        assert result.exit_code == 0
        assert "Terms: 0" in result.output
        assert "Relations: 0" in result.output


class TestVerifyLedgerCommand:
    """Tests for verify-ledger command."""

    def test_verify_ledger_valid(self, runner, example_ledger_file):
        """Test verifying a valid ledger."""
        result = runner.invoke(cli, ["verify-ledger", "--ledger-file", example_ledger_file])

        assert result.exit_code == 0
        assert "Ledger is valid" in result.output
        assert "Entries verified:" in result.output
        assert "Chain head:" in result.output

    def test_verify_ledger_missing_file(self, runner):
        """Test verify-ledger without file argument."""
        result = runner.invoke(cli, ["verify-ledger"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_verify_ledger_nonexistent_file(self, runner):
        """Test verify-ledger with non-existent file."""
        result = runner.invoke(cli, ["verify-ledger", "--ledger-file", "/nonexistent/ledger.json"])

        assert result.exit_code != 0

    def test_verify_ledger_invalid_json(self, runner, temp_dir):
        """Test verify-ledger with invalid JSON."""
        bad_file = Path(temp_dir) / "bad_ledger.json"
        bad_file.write_text("not json")

        result = runner.invoke(cli, ["verify-ledger", "--ledger-file", str(bad_file)])

        assert result.exit_code != 0

    def test_verify_ledger_tampered(self, runner, temp_dir):
        """Test verifying a tampered ledger that fails from_dict."""
        from lexecon.ledger.chain import LedgerChain

        # Create ledger
        ledger = LedgerChain()
        ledger.append("event1", {"data": 1})
        ledger.append("event2", {"data": 2})

        # Tamper with it
        ledger.entries[1].data["data"] = 999

        # Save tampered ledger
        ledger_file = Path(temp_dir) / "tampered.json"
        ledger_file.write_text(json.dumps(ledger.to_dict()))

        result = runner.invoke(cli, ["verify-ledger", "--ledger-file", str(ledger_file)])

        # Should fail (from_dict raises ValueError for tampering)
        assert result.exit_code == 1
        assert result.exception is not None

    def test_verify_ledger_validation_failed(self, runner, temp_dir, monkeypatch):
        """Test verify-ledger when verification fails (not from_dict)."""
        from lexecon.ledger.chain import LedgerChain

        # Create a valid ledger file
        ledger = LedgerChain()
        ledger.append("event1", {"data": 1})
        ledger_file = Path(temp_dir) / "ledger.json"
        ledger_file.write_text(json.dumps(ledger.to_dict()))

        # Mock verify_integrity to return failure
        def mock_verify(self):
            return {
                "valid": False,
                "error": "Simulated verification failure",
                "entries_checked": 0,
            }

        monkeypatch.setattr(LedgerChain, "verify_integrity", mock_verify)

        result = runner.invoke(cli, ["verify-ledger", "--ledger-file", str(ledger_file)])

        # Should fail with validation failed message
        assert result.exit_code == 1
        assert "validation failed" in result.output.lower() or "✗" in result.output
        assert "Error" in result.output or "error" in result.output.lower()


class TestServerCommand:
    """Tests for server command."""

    def test_server_help(self, runner):
        """Test server command help."""
        result = runner.invoke(cli, ["server", "--help"])
        assert result.exit_code == 0
        assert "Start the API server" in result.output
        assert "--port" in result.output
        assert "--host" in result.output

    def test_server_with_node_id(self, runner, monkeypatch):
        """Test server command with node ID."""
        import uvicorn

        # Mock uvicorn.run to avoid actually starting the server
        def mock_run(*args, **kwargs):
            pass

        monkeypatch.setattr(uvicorn, "run", mock_run)

        result = runner.invoke(cli, ["server", "--node-id", "test-node", "--port", "8080"])

        # Should output starting message and node ID
        assert "Starting Lexecon API server" in result.output
        assert "Node ID: test-node" in result.output
        assert result.exit_code == 0

    def test_server_without_node_id(self, runner, monkeypatch):
        """Test server command without node ID."""
        import uvicorn

        # Mock uvicorn.run
        def mock_run(*args, **kwargs):
            pass

        monkeypatch.setattr(uvicorn, "run", mock_run)

        result = runner.invoke(cli, ["server", "--port", "9000"])

        # Should output starting message but no node ID
        assert "Starting Lexecon API server" in result.output
        assert "Node ID:" not in result.output
        assert result.exit_code == 0

    # Note: We can't easily test the actual server startup in unit tests
    # as it would start a real server. Integration tests would handle that.


class TestCLIIntegration:
    """Integration tests for CLI workflows."""

    def test_full_workflow(self, runner, temp_dir, example_policy_file, example_request_file):
        """Test complete CLI workflow."""
        # 1. Initialize node
        result = runner.invoke(cli, ["init", "--node-id", "workflow-test", "--data-dir", temp_dir])
        assert result.exit_code == 0

        # 2. Load policy
        result = runner.invoke(cli, ["load-policy", "--policy-file", example_policy_file])
        assert result.exit_code == 0
        policy_hash = None
        for line in result.output.split("\n"):
            if "Policy hash:" in line:
                policy_hash = line.split(":")[-1].strip()
        assert policy_hash is not None

        # 3. Make decision
        result = runner.invoke(cli, ["decide", "--json-file", example_request_file])
        assert result.exit_code == 0
        decision = json.loads(result.output)
        assert "decision" in decision

    def test_init_and_verify_keys(self, runner, temp_dir):
        """Test that init creates valid key files."""
        result = runner.invoke(cli, ["init", "--node-id", "key-test", "--data-dir", temp_dir])
        assert result.exit_code == 0

        # Check key files exist and have content
        key_file = Path(temp_dir) / "key-test.key"
        pub_file = Path(temp_dir) / "key-test.pub"

        assert key_file.exists()
        assert pub_file.exists()

        # Keys should have content
        assert len(key_file.read_text()) > 0
        assert len(pub_file.read_text()) > 0

        # Keys should be PEM format
        key_content = key_file.read_text()
        pub_content = pub_file.read_text()

        assert "BEGIN PRIVATE KEY" in key_content
        assert "BEGIN PUBLIC KEY" in pub_content


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    def test_invalid_command(self, runner):
        """Test invalid command."""
        result = runner.invoke(cli, ["invalid-command"])
        assert result.exit_code != 0
        assert "Error" in result.output or "Usage" in result.output

    def test_decide_partial_args(self, runner):
        """Test decide with partial arguments."""
        # Provide some but not all required args
        result = runner.invoke(
            cli,
            [
                "decide",
                "--actor",
                "model",
                "--action",
                "search",
                # Missing --tool and --intent
            ],
        )
        assert result.exit_code != 0

    def test_init_duplicate_node(self, runner, temp_dir):
        """Test initializing same node twice."""
        # First init
        result1 = runner.invoke(cli, ["init", "--node-id", "dup-test", "--data-dir", temp_dir])
        assert result1.exit_code == 0

        # Second init (should overwrite or warn)
        result2 = runner.invoke(cli, ["init", "--node-id", "dup-test", "--data-dir", temp_dir])
        # Either succeeds (overwrite) or fails (file exists)
        # Both are acceptable behaviors
        assert result2.exit_code in [0, 1]


class TestCLIMainEntryPoint:
    """Tests for CLI main entry point."""

    def test_main_entry_point(self, runner):
        """Test that main entry point executes correctly."""
        # Test that the CLI can be invoked through the main entry point
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Lexecon" in result.output


class TestCLIOutput:
    """Tests for CLI output formatting."""

    def test_decide_json_output(self, runner, example_request_file):
        """Test decide outputs valid JSON."""
        result = runner.invoke(cli, ["decide", "--json-file", example_request_file])

        if result.exit_code == 0:
            # Should be parseable JSON
            data = json.loads(result.output)
            assert isinstance(data, dict)

    def test_load_policy_output_format(self, runner, example_policy_file):
        """Test load-policy output format."""
        result = runner.invoke(cli, ["load-policy", "--policy-file", example_policy_file])

        assert result.exit_code == 0
        # Check for expected output format markers
        assert "✓" in result.output or "Policy loaded" in result.output
        assert "Terms:" in result.output
        assert "Relations:" in result.output

    def test_verify_ledger_output_format(self, runner, example_ledger_file):
        """Test verify-ledger output format."""
        result = runner.invoke(cli, ["verify-ledger", "--ledger-file", example_ledger_file])

        assert result.exit_code == 0
        # Check for expected output format
        assert "✓" in result.output or "valid" in result.output.lower()
