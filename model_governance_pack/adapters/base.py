"""
Base adapter for model governance integration.

Provides the interface for connecting foundation models to Lexecon governance.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import requests
from datetime import datetime


class GovernanceAdapter(ABC):
    """
    Base class for model governance adapters.

    Adapters intercept tool calls and route them through Lexecon governance
    before allowing execution.
    """

    def __init__(self, governance_url: str = "http://localhost:8000", actor: str = "model"):
        """
        Initialize the governance adapter.

        Args:
            governance_url: Base URL of Lexecon governance API
            actor: Actor identifier (e.g., 'model', 'assistant')
        """
        self.governance_url = governance_url.rstrip("/")
        self.actor = actor
        self.capability_tokens: Dict[str, Dict[str, Any]] = {}

    def check_health(self) -> bool:
        """Check if governance service is available."""
        try:
            response = requests.get(f"{self.governance_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def request_decision(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        user_intent: str,
        data_classes: List[str] = None,
        risk_level: int = 1
    ) -> Dict[str, Any]:
        """
        Request governance decision for a tool call.

        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            user_intent: User's intent/purpose for this action
            data_classes: Data classifications involved
            risk_level: Risk level (1=low, 5=critical)

        Returns:
            Decision response with permit/deny and capability token
        """
        request_payload = {
            "actor": self.actor,
            "proposed_action": tool_name,
            "tool": tool_name,
            "user_intent": user_intent,
            "data_classes": data_classes or [],
            "risk_level": risk_level,
            "requested_output_type": "tool_action",
            "policy_mode": "strict",
            "context": tool_args
        }

        try:
            response = requests.post(
                f"{self.governance_url}/decide",
                json=request_payload,
                timeout=10
            )
            response.raise_for_status()
            decision = response.json()

            # Store capability token if granted
            if decision.get("capability_token"):
                token = decision["capability_token"]
                self.capability_tokens[token["token_id"]] = token

            return decision

        except requests.exceptions.RequestException as e:
            # Fail-safe: deny by default if governance service unavailable
            return {
                "decision": "deny",
                "reasoning": f"Governance service error: {str(e)}",
                "error": True
            }

    def is_permitted(self, decision: Dict[str, Any]) -> bool:
        """Check if decision permits the action."""
        return decision.get("decision") == "permit" and not decision.get("error")

    def get_capability_token(self, decision: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract capability token from decision."""
        return decision.get("capability_token")

    def verify_token(self, token_id: str, action: str, tool: str) -> bool:
        """
        Verify a capability token is valid for the action.

        Args:
            token_id: Token identifier
            action: Action to perform
            tool: Tool to use

        Returns:
            True if token is valid and authorizes the action
        """
        token = self.capability_tokens.get(token_id)
        if not token:
            return False

        # Check expiry
        expiry = datetime.fromisoformat(token["expiry"])
        if datetime.utcnow() >= expiry:
            # Token expired, remove it
            del self.capability_tokens[token_id]
            return False

        # Check scope
        scope = token.get("scope", {})
        return scope.get("action") == action and scope.get("tool") == tool

    @abstractmethod
    def intercept_tool_call(self, tool_name: str, tool_args: Dict[str, Any], **kwargs) -> Any:
        """
        Intercept and govern a tool call.

        Must be implemented by provider-specific adapters.

        Args:
            tool_name: Name of the tool being called
            tool_args: Arguments for the tool
            **kwargs: Provider-specific parameters

        Returns:
            Result of tool execution or denial message
        """
        pass

    @abstractmethod
    def wrap_response(self, decision: Dict[str, Any], result: Any = None) -> Dict[str, Any]:
        """
        Wrap execution result in provider-specific format.

        Args:
            decision: Governance decision
            result: Tool execution result (if permitted)

        Returns:
            Provider-specific response format
        """
        pass


class GovernanceError(Exception):
    """Exception raised when governance denies an action."""

    def __init__(self, decision: Dict[str, Any]):
        self.decision = decision
        self.reasoning = decision.get("reasoning", "Action denied by governance")
        super().__init__(self.reasoning)
