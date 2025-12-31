"""
Example: Governed OpenAI Integration

This example shows how to use Lexecon governance with OpenAI models.
"""

import os
from openai import OpenAI

# Import the governance adapter
import sys
sys.path.insert(0, "../adapters")
from openai_adapter import OpenAIGovernanceAdapter


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


# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Create governance adapter
adapter = OpenAIGovernanceAdapter(
    governance_url="http://localhost:8000",
    actor="model"
)

# Register tools with the adapter
adapter.register_tool("search_web", search_web)
adapter.register_tool("read_file", read_file)
adapter.register_tool("execute_code", execute_code)

# Define tools for OpenAI
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information",
            "parameters": {
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
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the filesystem",
            "parameters": {
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
    }
]


def main():
    """Run governed conversation."""
    print("=== Governed OpenAI Example ===\n")

    # Check governance health
    if not adapter.check_health():
        print("ERROR: Governance service is not available!")
        return

    print("✓ Governance service is healthy\n")

    # User message
    user_message = "Search for information about AI governance frameworks"

    messages = [
        {"role": "system", "content": "You operate under Lexecon governance. All tool calls require approval."},
        {"role": "user", "content": user_message}
    ]

    print(f"User: {user_message}\n")

    # Create governed completion
    try:
        response = adapter.create_governed_completion(
            client=client,
            messages=messages,
            tools=tools,
            user_intent="Research AI governance",
            model="gpt-4",
            max_tokens=500
        )

        print(f"Assistant: {response.choices[0].message.content}\n")

    except Exception as e:
        print(f"Error: {str(e)}")


def manual_tool_call_example():
    """Example of manually intercepting a tool call."""
    print("\n=== Manual Tool Call Example ===\n")

    # Simulate a tool call from the model
    result = adapter.intercept_tool_call(
        tool_name="search_web",
        tool_args={"query": "AI safety", "max_results": 5},
        user_intent="Research AI safety best practices",
        risk_level=1
    )

    print("Governance Decision:")
    print(f"  Status: {result['governance_decision']['decision']}")
    print(f"  Reasoning: {result['governance_decision']['reasoning']}")

    if result['governance_decision']['decision'] == 'permit':
        token = result['governance_decision'].get('capability_token', {})
        print(f"  Token ID: {token.get('token_id')}")
        print(f"  Expires: {token.get('expiry')}")
        print(f"\nTool Result: {result['content']}")
    else:
        print(f"\n❌ Tool call was denied")


if __name__ == "__main__":
    # Run manual example (doesn't require OpenAI API key)
    manual_tool_call_example()

    # Uncomment to run full OpenAI example (requires API key)
    # main()
