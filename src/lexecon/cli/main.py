"""
CLI - Command-line interface for Lexecon.

Provides commands for initializing nodes, starting servers, and making decisions.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click
import uvicorn

from lexecon.decision.service import DecisionRequest, DecisionService
from lexecon.identity.signing import KeyManager
from lexecon.ledger.chain import LedgerChain
from lexecon.policy.engine import PolicyEngine, PolicyMode


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Lexecon - Lexical Governance Protocol"""
    pass


@cli.command()
@click.option("--node-id", required=True, help="Node identifier")
@click.option("--data-dir", default=".lexecon", help="Data directory")
def init(node_id: str, data_dir: str):
    """Initialize a Lexecon node."""
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    # Generate keys
    key_manager = KeyManager.generate()
    private_key_path = data_path / f"{node_id}.key"
    public_key_path = data_path / f"{node_id}.pub"

    key_manager.save_keys(private_key_path, public_key_path)

    # Create config
    config = {
        "node_id": node_id,
        "private_key_path": str(private_key_path),
        "public_key_path": str(public_key_path),
        "public_key_fingerprint": key_manager.get_public_key_fingerprint(),
    }

    config_path = data_path / f"{node_id}.json"
    config_path.write_text(json.dumps(config, indent=2))

    click.echo(f"✓ Node '{node_id}' initialized")
    click.echo(f"  Data directory: {data_path.absolute()}")
    click.echo(f"  Config: {config_path}")
    click.echo(f"  Public key fingerprint: {config['public_key_fingerprint']}")


@cli.command()
@click.option("--node-id", help="Node identifier")
@click.option("--port", default=8000, help="Port to listen on")
@click.option("--host", default="0.0.0.0", help="Host to bind to")
def server(node_id: Optional[str], port: int, host: str):
    """Start the API server."""
    click.echo(f"Starting Lexecon API server on {host}:{port}")

    if node_id:
        click.echo(f"Node ID: {node_id}")

    # Start server
    uvicorn.run("lexecon.api.server:app", host=host, port=port, log_level="info")


@cli.command()
@click.option("--json-file", type=click.Path(exists=True), help="JSON file with decision request")
@click.option("--actor", help="Actor requesting action")
@click.option("--action", help="Proposed action")
@click.option("--tool", help="Tool to use")
@click.option("--intent", help="User intent")
def decide(
    json_file: Optional[str],
    actor: Optional[str],
    action: Optional[str],
    tool: Optional[str],
    intent: Optional[str],
):
    """Make a governance decision."""

    # Load request from file or CLI args
    if json_file:
        with open(json_file) as f:
            request_data = json.load(f)
    elif all([actor, action, tool, intent]):
        request_data = {
            "actor": actor,
            "proposed_action": action,
            "tool": tool,
            "user_intent": intent,
        }
    else:
        click.echo(
            "Error: Provide either --json or all of (--actor, --action, --tool, --intent)", err=True
        )
        sys.exit(1)

    # Create services
    policy_engine = PolicyEngine(mode=PolicyMode.STRICT)
    decision_service = DecisionService(policy_engine=policy_engine)

    # Create request
    request = DecisionRequest(
        actor=request_data["actor"],
        proposed_action=request_data["proposed_action"],
        tool=request_data["tool"],
        user_intent=request_data["user_intent"],
        data_classes=request_data.get("data_classes", []),
        risk_level=request_data.get("risk_level", 1),
        context=request_data.get("context", {}),
    )

    # Evaluate
    response = decision_service.evaluate_request(request)

    # Output
    click.echo(json.dumps(response.to_dict(), indent=2))


@cli.command()
@click.option("--policy-file", required=True, type=click.Path(exists=True), help="Policy JSON file")
def load_policy(policy_file: str):
    """Load a policy from file."""
    with open(policy_file) as f:
        policy_data = json.load(f)

    engine = PolicyEngine()
    engine.load_policy(policy_data)

    click.echo("✓ Policy loaded")
    click.echo(f"  Terms: {len(engine.terms)}")
    click.echo(f"  Relations: {len(engine.relations)}")
    click.echo(f"  Policy hash: {engine.get_policy_hash()}")


@cli.command()
@click.option("--ledger-file", required=True, type=click.Path(exists=True), help="Ledger JSON file")
def verify_ledger(ledger_file: str):
    """Verify ledger integrity."""
    with open(ledger_file) as f:
        ledger_data = json.load(f)

    ledger = LedgerChain.from_dict(ledger_data)
    result = ledger.verify_integrity()

    if result["valid"]:
        click.echo("✓ Ledger is valid")
        click.echo(f"  Entries verified: {result['entries_verified']}")
        click.echo(f"  Chain head: {result['chain_head_hash']}")
    else:
        click.echo("✗ Ledger validation failed", err=True)
        click.echo(f"  Error: {result['error']}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
