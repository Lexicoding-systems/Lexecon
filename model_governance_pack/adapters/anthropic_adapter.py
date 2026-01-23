"""Anthropic (Claude) adapter for Lexecon governance.

Integrates with Anthropic's tool use API to govern tool executions.
"""

import json
from typing import Any, Callable, Dict, List, Optional

from .base import GovernanceAdapter


class AnthropicGovernanceAdapter(GovernanceAdapter):
    """Adapter for Anthropic (Claude) models with governance-gated tool execution.

    This adapter intercepts Claude tool use requests and routes them
    through Lexecon governance before execution.
    """

    def __init__(
        self,
        governance_url: str = "http://localhost:8000",
        actor: str = "model",
        tools: Optional[Dict[str, Callable]] = None,
    ):
        """Initialize Anthropic governance adapter.

        Args:
            governance_url: Lexecon governance API URL
            actor: Actor identifier
            tools: Dictionary mapping tool names to callable functions
        """
        super().__init__(governance_url, actor)
        self.tools = tools or {}

    def register_tool(self, name: str, function: Callable) -> None:
        """Register a tool function."""
        self.tools[name] = function

    def intercept_tool_call(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        user_intent: str = "",
        risk_level: int = 1,
        execute_if_permitted: bool = True,
    ) -> Dict[str, Any]:
        """Intercept and govern a Claude tool use request.

        Args:
            tool_name: Name of the tool from tool_use block
            tool_args: Input from the tool_use block
            user_intent: Context about user's intent
            risk_level: Risk level for this operation
            execute_if_permitted: Execute tool if governance permits

        Returns:
            Dict with governance decision and optional execution result
        """
        # Request governance decision
        decision = self.request_decision(
            tool_name=tool_name,
            tool_args=tool_args,
            user_intent=user_intent,
            risk_level=risk_level,
        )

        # If denied, return denial
        if not self.is_permitted(decision):
            return self.wrap_response(decision)

        # If permitted and execution requested, execute the tool
        result = None
        if execute_if_permitted:
            tool_func = self.tools.get(tool_name)
            if tool_func is None:
                return {
                    "type": "tool_result",
                    "is_error": True,
                    "content": f"Tool '{tool_name}' not registered",
                    "governance_decision": decision,
                }

            try:
                result = tool_func(**tool_args)
            except Exception as e:
                return {
                    "type": "tool_result",
                    "is_error": True,
                    "content": f"Tool execution failed: {e!s}",
                    "governance_decision": decision,
                }

        return self.wrap_response(decision, result)

    def wrap_response(
        self,
        decision: Dict[str, Any],
        result: Any = None,
    ) -> Dict[str, Any]:
        """Wrap in Anthropic tool_result format.

        Returns a response suitable for Claude tool_result blocks.
        """
        if not self.is_permitted(decision):
            return {
                "type": "tool_result",
                "is_error": True,
                "content": json.dumps({
                    "status": "denied",
                    "reasoning": decision.get("reasoning"),
                    "policy_version": decision.get("policy_version_hash"),
                    "ledger_entry": decision.get("ledger_entry_hash"),
                }),
                "governance_decision": decision,
            }

        return {
            "type": "tool_result",
            "content": json.dumps({
                "status": "success",
                "result": result,
                "capability_token": decision.get("capability_token", {}).get("token_id"),
                "policy_version": decision.get("policy_version_hash"),
                "ledger_entry": decision.get("ledger_entry_hash"),
            }),
            "governance_decision": decision,
        }

    def process_tool_uses(
        self,
        tool_uses: List[Dict[str, Any]],
        user_intent: str = "",
    ) -> List[Dict[str, Any]]:
        """Process multiple tool_use blocks from Claude response.

        Args:
            tool_uses: List of tool_use content blocks from Claude
            user_intent: User's overall intent

        Returns:
            List of tool_result blocks with governance
        """
        results = []

        for tool_use in tool_uses:
            if tool_use.get("type") != "tool_use":
                continue

            tool_name = tool_use.get("name")
            tool_args = tool_use.get("input", {})
            tool_id = tool_use.get("id")

            result = self.intercept_tool_call(
                tool_name=tool_name,
                tool_args=tool_args,
                user_intent=user_intent,
            )

            # Add Anthropic-specific fields
            result["tool_use_id"] = tool_id

            results.append(result)

        return results

    def create_governed_message(
        self,
        client,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        user_intent: str = "",
        **kwargs,
    ):
        """Create a governed Anthropic message.

        Automatically intercepts and governs any tool use requests.

        Args:
            client: Anthropic client instance
            messages: Conversation messages
            tools: Tool definitions
            user_intent: User's intent for context
            **kwargs: Additional arguments for client.messages.create

        Returns:
            Message response with governed tool executions
        """
        # Make initial request
        response = client.messages.create(
            messages=messages,
            tools=tools,
            **kwargs,
        )

        # Check for tool uses in response
        tool_uses = [
            block for block in response.content
            if getattr(block, "type", None) == "tool_use"
        ]

        # If no tool uses, return as-is
        if not tool_uses:
            return response

        # Process tool uses through governance
        tool_use_dicts = [
            {
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            }
            for block in tool_uses
        ]

        tool_results = self.process_tool_uses(
            tool_use_dicts,
            user_intent=user_intent,
        )

        # Add assistant message with tool uses
        messages.append({
            "role": "assistant",
            "content": response.content,
        })

        # Add tool results
        messages.append({
            "role": "user",
            "content": tool_results,
        })

        # Get final response
        return client.messages.create(
            messages=messages,
            tools=tools,
            **kwargs,
        )



# Example usage
if __name__ == "__main__":
    # Example tool function
    def search_web(query: str, max_results: int = 10):
        """Search the web for information."""
        return {"results": [f"Result for: {query}"], "count": max_results}

    # Create adapter
    adapter = AnthropicGovernanceAdapter(
        governance_url="http://localhost:8000",
    )

    # Register tools
    adapter.register_tool("search_web", search_web)

    # Intercept a tool call
    result = adapter.intercept_tool_call(
        tool_name="search_web",
        tool_args={"query": "AI governance", "max_results": 5},
        user_intent="Research AI safety frameworks",
    )

    print(json.dumps(result, indent=2))
