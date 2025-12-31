"""
OpenAI adapter for Lexecon governance.

Integrates with OpenAI's function/tool calling API to govern tool executions.
"""

from typing import Dict, Any, Callable, Optional, List
import json

from .base import GovernanceAdapter, GovernanceError


class OpenAIGovernanceAdapter(GovernanceAdapter):
    """
    Adapter for OpenAI models with governance-gated tool execution.

    This adapter intercepts OpenAI function/tool calls and routes them
    through Lexecon governance before execution.
    """

    def __init__(
        self,
        governance_url: str = "http://localhost:8000",
        actor: str = "model",
        tools: Dict[str, Callable] = None
    ):
        """
        Initialize OpenAI governance adapter.

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
        execute_if_permitted: bool = True
    ) -> Dict[str, Any]:
        """
        Intercept and govern an OpenAI tool call.

        Args:
            tool_name: Name of the tool from function calling
            tool_args: Arguments from the function call
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
            risk_level=risk_level
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
                    "error": True,
                    "message": f"Tool '{tool_name}' not registered",
                    "decision": decision
                }

            try:
                result = tool_func(**tool_args)
            except Exception as e:
                return {
                    "error": True,
                    "message": f"Tool execution failed: {str(e)}",
                    "decision": decision
                }

        return self.wrap_response(decision, result)

    def wrap_response(
        self,
        decision: Dict[str, Any],
        result: Any = None
    ) -> Dict[str, Any]:
        """
        Wrap in OpenAI-compatible format.

        Returns a response suitable for OpenAI function call results.
        """
        if not self.is_permitted(decision):
            return {
                "role": "function",
                "content": json.dumps({
                    "status": "denied",
                    "reasoning": decision.get("reasoning"),
                    "policy_version": decision.get("policy_version_hash")
                }),
                "governance_decision": decision
            }

        return {
            "role": "function",
            "content": json.dumps({
                "status": "success",
                "result": result,
                "capability_token": decision.get("capability_token", {}).get("token_id"),
                "policy_version": decision.get("policy_version_hash")
            }),
            "governance_decision": decision
        }

    def process_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        user_intent: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Process multiple tool calls from OpenAI response.

        Args:
            tool_calls: List of tool_call objects from OpenAI
            user_intent: User's overall intent

        Returns:
            List of function call results with governance
        """
        results = []

        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            tool_name = function.get("name")
            tool_args = json.loads(function.get("arguments", "{}"))

            result = self.intercept_tool_call(
                tool_name=tool_name,
                tool_args=tool_args,
                user_intent=user_intent
            )

            # Add OpenAI-specific fields
            result["name"] = tool_name
            if "id" in tool_call:
                result["tool_call_id"] = tool_call["id"]

            results.append(result)

        return results

    def create_governed_completion(
        self,
        client,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        user_intent: str = "",
        **kwargs
    ):
        """
        Create a governed OpenAI chat completion.

        Automatically intercepts and governs any tool calls.

        Args:
            client: OpenAI client instance
            messages: Conversation messages
            tools: Tool definitions
            user_intent: User's intent for context
            **kwargs: Additional arguments for client.chat.completions.create

        Returns:
            Completion response with governed tool executions
        """
        # Make initial request
        response = client.chat.completions.create(
            messages=messages,
            tools=tools,
            **kwargs
        )

        message = response.choices[0].message

        # If no tool calls, return as-is
        if not message.tool_calls:
            return response

        # Process tool calls through governance
        tool_results = self.process_tool_calls(
            message.tool_calls,
            user_intent=user_intent
        )

        # Add results to conversation
        messages.append(message)
        for result in tool_results:
            messages.append({
                "role": "tool",
                "tool_call_id": result.get("tool_call_id"),
                "content": result.get("content")
            })

        # Get final response
        final_response = client.chat.completions.create(
            messages=messages,
            tools=tools,
            **kwargs
        )

        return final_response


# Example usage
if __name__ == "__main__":
    # Example tool function
    def search_web(query: str, max_results: int = 10):
        """Search the web for information."""
        return {"results": [f"Result for: {query}"], "count": max_results}

    # Create adapter
    adapter = OpenAIGovernanceAdapter(
        governance_url="http://localhost:8000"
    )

    # Register tools
    adapter.register_tool("search_web", search_web)

    # Intercept a tool call
    result = adapter.intercept_tool_call(
        tool_name="search_web",
        tool_args={"query": "AI governance", "max_results": 5},
        user_intent="Research AI safety frameworks"
    )

    print(json.dumps(result, indent=2))
