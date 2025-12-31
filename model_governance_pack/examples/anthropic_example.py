"""
Example: Governed Anthropic (Claude) Integration

This example shows how to use Lexecon governance with Anthropic models.
"""

import os
from anthropic import Anthropic

# Import the governance adapter
import sys
sys.path.insert(0, "../adapters")
from anthropic_adapter import AnthropicGovernanceAdapter


# Define tool functions
def search_web(query: str, max_results: int = 10):
    """Search the web for information."""
    # Simulate web search
    return {
        "results": [
            {"title": f"Result about {query}", "url": "https://example.com/1"},
            {"title": f"More about {query}", "url": "https://example.com/2"}
        ],
        "count": max_results
    }


def read_file(filepath: str):
    """Read a file from the filesystem."""
    # Simulate file read
    return {
        "content": f"Contents of {filepath}",
        "size": 1024
    }


def execute_code(code: str, language: str = "python"):
    """Execute code in a sandbox."""
    # This would execute in actual sandbox
    return {
        "output": f"Executed {language} code",
        "status": "success"
    }


# Initialize Anthropic client
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Create governance adapter
adapter = AnthropicGovernanceAdapter(
    governance_url="http://localhost:8000",
    actor="model"
)

# Register tools with the adapter
adapter.register_tool("search_web", search_web)
adapter.register_tool("read_file", read_file)
adapter.register_tool("execute_code", execute_code)

# Define tools for Claude
tools = [
    {
        "name": "search_web",
        "description": "Search the web for information",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "read_file",
        "description": "Read a file from the filesystem",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Path to the file"
                }
            },
            "required": ["filepath"]
        }
    }
]


def main():
    """Run governed conversation."""
    print("=== Governed Anthropic Example ===\n")

    # Check governance health
    if not adapter.check_health():
        print("ERROR: Governance service is not available!")
        return

    print("✓ Governance service is healthy\n")

    # User message
    user_message = "Search for information about AI governance frameworks"

    messages = [
        {"role": "user", "content": user_message}
    ]

    # System prompt with governance instructions
    system_prompt = """You operate under Lexecon governance. All tool calls require approval.
If approved, you receive a capability token. If denied, explain the denial reason and suggest alternatives."""

    print(f"User: {user_message}\n")

    # Create governed message
    try:
        response = adapter.create_governed_message(
            client=client,
            messages=messages,
            tools=tools,
            user_intent="Research AI governance",
            model="claude-3-sonnet-20240229",
            max_tokens=500,
            system=system_prompt
        )

        # Extract text response
        text_content = [
            block.text for block in response.content
            if hasattr(block, "text")
        ]

        print(f"Assistant: {' '.join(text_content)}\n")

    except Exception as e:
        print(f"Error: {str(e)}")


def manual_tool_call_example():
    """Example of manually intercepting a tool call."""
    print("\n=== Manual Tool Call Example ===\n")

    # Simulate a tool call from Claude
    result = adapter.intercept_tool_call(
        tool_name="search_web",
        tool_args={"query": "AI safety", "max_results": 5},
        user_intent="Research AI safety best practices",
        risk_level=1
    )

    print("Governance Decision:")
    decision = result['governance_decision']
    print(f"  Status: {decision['decision']}")
    print(f"  Reasoning: {decision['reasoning']}")

    if decision['decision'] == 'permit':
        token = decision.get('capability_token', {})
        print(f"  Token ID: {token.get('token_id')}")
        print(f"  Expires: {token.get('expiry')}")
        print(f"  Ledger Entry: {decision.get('ledger_entry_hash', 'N/A')[:16]}...")
        print(f"\nTool Result Type: {result['type']}")
        print(f"Tool Result Content: {result['content'][:100]}...")
    else:
        print(f"\n❌ Tool call was denied")
        print(f"Response type: {result['type']}")
        print(f"Is error: {result.get('is_error', False)}")


def stream_example():
    """Example of handling streaming with governance."""
    print("\n=== Streaming Example ===\n")
    print("Note: Streaming requires collecting tool_use blocks before governance check")
    print("The adapter will need to buffer until complete tool_use is received.\n")

    # In practice, you would:
    # 1. Stream the response
    # 2. Detect and collect tool_use blocks
    # 3. Once complete, pass to adapter.process_tool_uses()
    # 4. Return tool_results
    # 5. Continue streaming the final response


if __name__ == "__main__":
    # Run manual example (doesn't require Anthropic API key)
    manual_tool_call_example()

    # Show streaming considerations
    stream_example()

    # Uncomment to run full Claude example (requires API key)
    # main()
