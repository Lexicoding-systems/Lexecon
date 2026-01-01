# Lexecon Model Adapter Guide

**Complete guide to integrating AI models with Lexecon governance**

This guide provides detailed instructions, patterns, and examples for integrating various AI models with Lexecon. Whether you're working with OpenAI, Anthropic, open-source models, or building custom adapters, this guide has you covered.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Adapter Architecture](#adapter-architecture)
3. [OpenAI Integration](#openai-integration)
4. [Anthropic/Claude Integration](#anthropicclaude-integration)
5. [Open-Source Models](#open-source-models)
6. [Custom Adapter Development](#custom-adapter-development)
7. [Tool Calling Patterns](#tool-calling-patterns)
8. [Prompt Engineering](#prompt-engineering)
9. [Testing Strategies](#testing-strategies)
10. [Performance Optimization](#performance-optimization)
11. [Troubleshooting](#troubleshooting)
12. [Best Practices](#best-practices)

---

## Introduction

### What is a Model Adapter?

A model adapter is a bridge between an AI model's tool calling interface and Lexecon's governance system. It intercepts tool calls, requests decisions from Lexecon, and enforces the governance policy.

### Key Responsibilities

Model adapters must:
- **Intercept** tool call requests from the model
- **Extract** relevant context (actor, action, risk level, user intent)
- **Request** governance decisions from Lexecon
- **Enforce** policy decisions (allow/deny)
- **Attach** capability tokens to approved requests
- **Handle** denied requests gracefully
- **Log** all governance interactions

### When to Use Adapters

Use adapters when:
- Integrating commercial AI APIs (OpenAI, Anthropic, etc.)
- Working with agent frameworks (LangChain, LlamaIndex)
- Building custom AI applications with governance requirements
- Enforcing compliance policies on model behavior
- Creating audit trails for AI tool usage

---

## Adapter Architecture

### High-Level Flow

```
┌─────────────────┐
│   User Input    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   AI Model      │
│  (GPT-4, etc.)  │
└────────┬────────┘
         │ Tool Call Request
         ▼
┌─────────────────────────────────────────────────┐
│           MODEL ADAPTER (Your Code)             │
│  ┌────────────────────────────────────────┐    │
│  │ 1. Extract Context                      │    │
│  │    - actor, action, risk_level          │    │
│  │    - user_intent, data_classes          │    │
│  └────────┬───────────────────────────────┘    │
│           │                                      │
│           ▼                                      │
│  ┌────────────────────────────────────────┐    │
│  │ 2. Request Decision from Lexecon       │◄───┼──┐
│  └────────┬───────────────────────────────┘    │  │
│           │                                      │  │
│           ▼                                      │  │
│  ┌────────────────────────────────────────┐    │  │
│  │ 3. Enforce Policy                       │    │  │
│  │    - If allowed: attach token & execute │    │  │
│  │    - If denied: return error message    │    │  │
│  └────────┬───────────────────────────────┘    │  │
└───────────┼──────────────────────────────────────┘  │
            │                                          │
            ▼                                          │
┌─────────────────┐                                   │
│  Tool Execution │                                   │
│  (if allowed)   │                                   │
└────────┬────────┘                                   │
         │                                            │
         ▼                                            │
┌─────────────────┐                         ┌────────┴────────┐
│  Return Result  │                         │  Lexecon Node   │
│   to Model      │                         │  - Policy Engine │
└─────────────────┘                         │  - Decision Svc  │
                                            │  - Ledger        │
                                            └──────────────────┘
```

### Core Components

**1. Context Extractor**
```python
def extract_context(tool_call, conversation_history):
    """Extract governance-relevant context from model request."""
    return {
        "actor": "model",
        "proposed_action": f"Execute {tool_call['name']}",
        "tool": tool_call["name"],
        "user_intent": infer_intent(conversation_history),
        "risk_level": calculate_risk(tool_call),
        "data_classes": identify_data_classes(tool_call["arguments"])
    }
```

**2. Decision Service Client**
```python
from lexecon import LexeconClient

lexecon = LexeconClient(base_url="http://localhost:8000")

def request_decision(context):
    """Request governance decision from Lexecon."""
    return lexecon.decide(**context)
```

**3. Policy Enforcer**
```python
def enforce_decision(decision, tool_call):
    """Enforce the governance decision."""
    if decision.allowed:
        # Attach capability token
        tool_call["capability_token"] = decision.capability_token.token_id
        return execute_tool(tool_call)
    else:
        # Return denial message
        return {
            "error": "Tool call denied by governance policy",
            "reason": decision.reason,
            "policy_id": decision.policy_id
        }
```

---

## OpenAI Integration

### Basic Pattern

```python
from openai import OpenAI
from lexecon import LexeconClient

client = OpenAI()
lexecon = LexeconClient(base_url="http://localhost:8000")

def governed_chat_completion(messages, tools, user_intent="Unknown"):
    """OpenAI chat completion with Lexecon governance."""

    # Step 1: Get model's response with tool calls
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    # Step 2: If no tool calls, return immediately
    if not message.tool_calls:
        return message.content

    # Step 3: Process each tool call through governance
    tool_responses = []
    for tool_call in message.tool_calls:
        # Extract context
        context = {
            "actor": "gpt-4",
            "proposed_action": f"Execute {tool_call.function.name}",
            "tool": tool_call.function.name,
            "user_intent": user_intent,
            "risk_level": calculate_risk(tool_call.function.name),
        }

        # Request decision
        decision = lexecon.decide(**context)

        # Enforce decision
        if decision.allowed:
            # Execute tool with capability token
            result = execute_tool(
                tool_call.function.name,
                tool_call.function.arguments,
                capability_token=decision.capability_token.token_id
            )
            tool_responses.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_call.function.name,
                "content": json.dumps(result)
            })
        else:
            # Return denial
            tool_responses.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_call.function.name,
                "content": json.dumps({
                    "error": "Access denied",
                    "reason": decision.reason
                })
            })

    # Step 4: Send tool responses back to model
    messages.append(message)
    messages.extend(tool_responses)

    final_response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )

    return final_response.choices[0].message.content
```

### Advanced OpenAI Adapter

Create a reusable adapter class:

```python
from typing import List, Dict, Any, Optional
from openai import OpenAI
from lexecon import LexeconClient
import json

class GovernedOpenAIClient:
    """OpenAI client with integrated Lexecon governance."""

    def __init__(
        self,
        openai_api_key: str,
        lexecon_url: str = "http://localhost:8000",
        model: str = "gpt-4"
    ):
        self.openai = OpenAI(api_key=openai_api_key)
        self.lexecon = LexeconClient(base_url=lexecon_url)
        self.model = model
        self.conversation_history = []

    def chat(
        self,
        message: str,
        tools: Optional[List[Dict]] = None,
        user_intent: Optional[str] = None
    ) -> str:
        """Send a message with governance enforcement."""

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })

        # Infer intent if not provided
        if user_intent is None:
            user_intent = self._infer_intent()

        # Get model response
        response = self.openai.chat.completions.create(
            model=self.model,
            messages=self.conversation_history,
            tools=tools or [],
            tool_choice="auto"
        )

        assistant_message = response.choices[0].message

        # Handle tool calls
        if assistant_message.tool_calls:
            return self._process_tool_calls(
                assistant_message,
                user_intent
            )

        # No tool calls - return content
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message.content
        })
        return assistant_message.content

    def _process_tool_calls(
        self,
        assistant_message,
        user_intent: str
    ) -> str:
        """Process tool calls through governance."""

        # Add assistant message to history
        self.conversation_history.append(assistant_message)

        # Process each tool call
        for tool_call in assistant_message.tool_calls:
            # Calculate risk
            risk_level = self._calculate_risk(
                tool_call.function.name,
                tool_call.function.arguments
            )

            # Request governance decision
            decision = self.lexecon.decide(
                actor=self.model,
                proposed_action=f"Execute {tool_call.function.name}",
                tool=tool_call.function.name,
                user_intent=user_intent,
                risk_level=risk_level,
                data_classes=self._extract_data_classes(
                    tool_call.function.arguments
                )
            )

            # Execute or deny
            if decision.allowed:
                result = self._execute_tool(
                    tool_call.function.name,
                    tool_call.function.arguments,
                    decision.capability_token.token_id
                )
                content = json.dumps({"result": result})
            else:
                content = json.dumps({
                    "error": "Access denied",
                    "reason": decision.reason,
                    "policy_id": decision.policy_id
                })

            # Add tool response to history
            self.conversation_history.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_call.function.name,
                "content": content
            })

        # Get final response from model
        final_response = self.openai.chat.completions.create(
            model=self.model,
            messages=self.conversation_history
        )

        final_content = final_response.choices[0].message.content
        self.conversation_history.append({
            "role": "assistant",
            "content": final_content
        })

        return final_content

    def _infer_intent(self) -> str:
        """Infer user intent from conversation history."""
        if not self.conversation_history:
            return "Unknown"

        last_user_message = next(
            (msg["content"] for msg in reversed(self.conversation_history)
             if msg["role"] == "user"),
            "Unknown"
        )
        return last_user_message[:100]  # First 100 chars

    def _calculate_risk(self, tool_name: str, arguments: str) -> int:
        """Calculate risk level for tool call."""
        risk_map = {
            "web_search": 1,
            "read_file": 2,
            "write_file": 3,
            "execute_code": 4,
            "delete_file": 5,
        }
        return risk_map.get(tool_name, 3)  # Default medium risk

    def _extract_data_classes(self, arguments: str) -> List[str]:
        """Extract data classes from tool arguments."""
        # Simple implementation - extend as needed
        data_classes = []
        args = json.loads(arguments)

        if "email" in str(args).lower():
            data_classes.append("email")
        if "password" in str(args).lower():
            data_classes.append("credentials")
        if "ssn" in str(args).lower():
            data_classes.append("pii")

        return data_classes

    def _execute_tool(
        self,
        tool_name: str,
        arguments: str,
        capability_token: str
    ) -> Any:
        """Execute tool with capability token."""
        # This is where you'd call your actual tool implementations
        # Pass the capability token for verification
        args = json.loads(arguments)

        # Example tool routing
        if tool_name == "web_search":
            return web_search(args["query"], token=capability_token)
        elif tool_name == "read_file":
            return read_file(args["path"], token=capability_token)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
```

### Usage Example

```python
# Initialize governed client
client = GovernedOpenAIClient(
    openai_api_key="sk-...",
    lexecon_url="http://localhost:8000",
    model="gpt-4"
)

# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# Chat with governance
response = client.chat(
    message="What are the latest developments in AI governance?",
    tools=tools,
    user_intent="Research AI governance trends"
)

print(response)
```

---

## Anthropic/Claude Integration

### Basic Pattern

```python
import anthropic
from lexecon import LexeconClient

anthropic_client = anthropic.Anthropic()
lexecon = LexeconClient(base_url="http://localhost:8000")

def governed_claude_completion(messages, tools, user_intent="Unknown"):
    """Claude completion with Lexecon governance."""

    # Step 1: Get Claude's response
    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20250219",
        max_tokens=4096,
        messages=messages,
        tools=tools
    )

    # Step 2: Process tool use blocks
    if response.stop_reason == "tool_use":
        tool_results = []

        for content_block in response.content:
            if content_block.type == "tool_use":
                # Extract context
                context = {
                    "actor": "claude-3-5-sonnet",
                    "proposed_action": f"Execute {content_block.name}",
                    "tool": content_block.name,
                    "user_intent": user_intent,
                    "risk_level": calculate_risk(content_block.name),
                }

                # Request decision
                decision = lexecon.decide(**context)

                # Enforce decision
                if decision.allowed:
                    result = execute_tool(
                        content_block.name,
                        content_block.input,
                        capability_token=decision.capability_token.token_id
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": json.dumps(result)
                    })
                else:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": json.dumps({
                            "error": "Access denied",
                            "reason": decision.reason
                        }),
                        "is_error": True
                    })

        # Step 3: Continue conversation with tool results
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        final_response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20250219",
            max_tokens=4096,
            messages=messages
        )

        return final_response.content[0].text

    # No tool use
    return response.content[0].text
```

### Advanced Claude Adapter

```python
from typing import List, Dict, Any, Optional
import anthropic
from lexecon import LexeconClient
import json

class GovernedClaudeClient:
    """Claude client with integrated Lexecon governance."""

    def __init__(
        self,
        anthropic_api_key: str,
        lexecon_url: str = "http://localhost:8000",
        model: str = "claude-3-5-sonnet-20250219"
    ):
        self.anthropic = anthropic.Anthropic(api_key=anthropic_api_key)
        self.lexecon = LexeconClient(base_url=lexecon_url)
        self.model = model
        self.conversation_history = []

    def chat(
        self,
        message: str,
        tools: Optional[List[Dict]] = None,
        user_intent: Optional[str] = None,
        system: Optional[str] = None
    ) -> str:
        """Send a message with governance enforcement."""

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })

        # Infer intent if not provided
        if user_intent is None:
            user_intent = message[:100]

        # Create message with Claude
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system or "",
            messages=self.conversation_history,
            tools=tools or []
        )

        # Handle tool use
        if response.stop_reason == "tool_use":
            return self._process_tool_use(response, user_intent, system, tools)

        # No tool use - return text
        assistant_message = response.content[0].text
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        return assistant_message

    def _process_tool_use(
        self,
        response,
        user_intent: str,
        system: Optional[str],
        tools: List[Dict]
    ) -> str:
        """Process tool use blocks through governance."""

        # Add assistant message to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })

        # Process each tool use block
        tool_results = []
        for content_block in response.content:
            if content_block.type == "tool_use":
                # Calculate risk
                risk_level = self._calculate_risk(
                    content_block.name,
                    content_block.input
                )

                # Request governance decision
                decision = self.lexecon.decide(
                    actor=self.model,
                    proposed_action=f"Execute {content_block.name}",
                    tool=content_block.name,
                    user_intent=user_intent,
                    risk_level=risk_level,
                    data_classes=self._extract_data_classes(content_block.input)
                )

                # Execute or deny
                if decision.allowed:
                    try:
                        result = self._execute_tool(
                            content_block.name,
                            content_block.input,
                            decision.capability_token.token_id
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": json.dumps({"result": result})
                        })
                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": json.dumps({
                                "error": str(e)
                            }),
                            "is_error": True
                        })
                else:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": json.dumps({
                            "error": "Access denied by governance policy",
                            "reason": decision.reason,
                            "policy_id": decision.policy_id
                        }),
                        "is_error": True
                    })

        # Add tool results to history
        self.conversation_history.append({
            "role": "user",
            "content": tool_results
        })

        # Get final response
        final_response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system or "",
            messages=self.conversation_history,
            tools=tools or []
        )

        # Extract text response
        final_content = next(
            (block.text for block in final_response.content if hasattr(block, 'text')),
            ""
        )

        self.conversation_history.append({
            "role": "assistant",
            "content": final_content
        })

        return final_content

    def _calculate_risk(self, tool_name: str, tool_input: Dict) -> int:
        """Calculate risk level for tool use."""
        risk_map = {
            "web_search": 1,
            "read_file": 2,
            "write_file": 3,
            "execute_code": 4,
            "delete_file": 5,
        }
        return risk_map.get(tool_name, 3)

    def _extract_data_classes(self, tool_input: Dict) -> List[str]:
        """Extract data classes from tool input."""
        data_classes = []
        input_str = json.dumps(tool_input).lower()

        if "email" in input_str:
            data_classes.append("email")
        if "password" in input_str or "credential" in input_str:
            data_classes.append("credentials")
        if "ssn" in input_str or "social security" in input_str:
            data_classes.append("pii")

        return data_classes

    def _execute_tool(
        self,
        tool_name: str,
        tool_input: Dict,
        capability_token: str
    ) -> Any:
        """Execute tool with capability token."""
        # Route to actual tool implementations
        if tool_name == "web_search":
            return web_search(tool_input["query"], token=capability_token)
        elif tool_name == "read_file":
            return read_file(tool_input["path"], token=capability_token)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
```

### Usage Example

```python
# Initialize governed Claude client
client = GovernedClaudeClient(
    anthropic_api_key="sk-ant-...",
    lexecon_url="http://localhost:8000"
)

# Define tools (Anthropic format)
tools = [
    {
        "name": "web_search",
        "description": "Search the web for current information",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    }
]

# Chat with governance
response = client.chat(
    message="What's the latest news on AI safety regulations?",
    tools=tools,
    user_intent="Research AI safety regulations",
    system="You are a helpful AI assistant focused on AI governance research."
)

print(response)
```

---

## Open-Source Models

### LangChain Integration

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from lexecon import LexeconClient

class GovernedLangChainTool(Tool):
    """LangChain tool wrapper with Lexecon governance."""

    def __init__(
        self,
        name: str,
        description: str,
        func: callable,
        lexecon_client: LexeconClient,
        risk_level: int = 3
    ):
        self.lexecon = lexecon_client
        self.risk_level = risk_level
        self.original_func = func

        # Wrap function with governance
        def governed_func(input_str: str) -> str:
            # Request decision
            decision = self.lexecon.decide(
                actor="langchain-agent",
                proposed_action=f"Execute {name}",
                tool=name,
                user_intent=input_str[:100],
                risk_level=self.risk_level
            )

            if not decision.allowed:
                return f"Error: {decision.reason}"

            # Execute with token
            return self.original_func(input_str, decision.capability_token.token_id)

        super().__init__(
            name=name,
            description=description,
            func=governed_func
        )

# Example usage
lexecon = LexeconClient(base_url="http://localhost:8000")

# Create governed tools
tools = [
    GovernedLangChainTool(
        name="web_search",
        description="Search the web for information",
        func=lambda query, token: web_search_api(query, token),
        lexecon_client=lexecon,
        risk_level=1
    ),
    GovernedLangChainTool(
        name="read_file",
        description="Read a file from disk",
        func=lambda path, token: read_file_impl(path, token),
        lexecon_client=lexecon,
        risk_level=2
    )
]

# Create agent with governed tools
llm = ChatOpenAI(model="gpt-4")
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

# Use agent
result = agent_executor.invoke({
    "input": "Search for AI governance best practices and summarize"
})
```

### Llama / Local Model Integration

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from lexecon import LexeconClient
import json
import re

class GovernedLlamaAgent:
    """Local Llama model with Lexecon governance."""

    def __init__(
        self,
        model_name: str = "meta-llama/Llama-2-13b-chat-hf",
        lexecon_url: str = "http://localhost:8000"
    ):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            load_in_8bit=True
        )
        self.lexecon = LexeconClient(base_url=lexecon_url)
        self.tools_registry = {}

    def register_tool(self, name: str, func: callable, description: str, risk_level: int = 3):
        """Register a tool that can be called by the model."""
        self.tools_registry[name] = {
            "func": func,
            "description": description,
            "risk_level": risk_level
        }

    def generate(self, prompt: str, user_intent: str = None) -> str:
        """Generate response with tool calling support."""

        # Build system prompt with available tools
        tools_desc = "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.tools_registry.items()
        ])

        full_prompt = f"""You are a helpful AI assistant with access to these tools:
{tools_desc}

To use a tool, output: TOOL_CALL: tool_name(argument)

User: {prompt}
Assistant:"""

        # Generate response
        inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            do_sample=True
        )
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract assistant response
        assistant_response = response.split("Assistant:")[-1].strip()

        # Check for tool calls
        tool_pattern = r"TOOL_CALL:\s*(\w+)\(([^)]*)\)"
        matches = re.findall(tool_pattern, assistant_response)

        if matches:
            # Process tool calls
            for tool_name, argument in matches:
                if tool_name in self.tools_registry:
                    result = self._execute_governed_tool(
                        tool_name,
                        argument,
                        user_intent or prompt
                    )
                    # Replace tool call with result
                    assistant_response = assistant_response.replace(
                        f"TOOL_CALL: {tool_name}({argument})",
                        f"[Tool Result: {result}]"
                    )

        return assistant_response

    def _execute_governed_tool(
        self,
        tool_name: str,
        argument: str,
        user_intent: str
    ) -> str:
        """Execute tool through governance."""
        tool_info = self.tools_registry[tool_name]

        # Request decision
        decision = self.lexecon.decide(
            actor="llama-2-13b",
            proposed_action=f"Execute {tool_name}",
            tool=tool_name,
            user_intent=user_intent,
            risk_level=tool_info["risk_level"]
        )

        if not decision.allowed:
            return f"Error: Access denied - {decision.reason}"

        # Execute tool
        try:
            result = tool_info["func"](argument, decision.capability_token.token_id)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"

# Example usage
agent = GovernedLlamaAgent(
    model_name="meta-llama/Llama-2-13b-chat-hf",
    lexecon_url="http://localhost:8000"
)

# Register tools
agent.register_tool(
    name="web_search",
    func=lambda query, token: web_search_api(query, token),
    description="Search the web",
    risk_level=1
)

agent.register_tool(
    name="calculator",
    func=lambda expr, token: eval(expr),
    description="Calculate mathematical expressions",
    risk_level=1
)

# Generate with tool usage
response = agent.generate(
    "What is 25 * 47? Also search for the population of Tokyo.",
    user_intent="Math calculation and city information"
)
print(response)
```

---

## Custom Adapter Development

### Base Adapter Interface

Create a standard interface for all adapters:

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from lexecon import LexeconClient

@dataclass
class ToolCall:
    """Represents a tool call from a model."""
    id: str
    name: str
    arguments: Dict[str, Any]

@dataclass
class ToolResult:
    """Represents the result of a tool execution."""
    tool_call_id: str
    success: bool
    result: Any
    error: Optional[str] = None

class BaseGovernedAdapter(ABC):
    """Base class for all governed model adapters."""

    def __init__(
        self,
        model_name: str,
        lexecon_url: str = "http://localhost:8000"
    ):
        self.model_name = model_name
        self.lexecon = LexeconClient(base_url=lexecon_url)
        self.tools_registry = {}

    @abstractmethod
    def chat(self, message: str, **kwargs) -> str:
        """Send a message and get response."""
        pass

    @abstractmethod
    def _extract_tool_calls(self, response: Any) -> List[ToolCall]:
        """Extract tool calls from model response."""
        pass

    @abstractmethod
    def _format_tool_results(self, results: List[ToolResult]) -> Any:
        """Format tool results for model."""
        pass

    def register_tool(
        self,
        name: str,
        func: callable,
        description: str,
        risk_level: int = 3,
        data_classes: List[str] = None
    ):
        """Register a tool for use by the model."""
        self.tools_registry[name] = {
            "func": func,
            "description": description,
            "risk_level": risk_level,
            "data_classes": data_classes or []
        }

    def _process_tool_calls(
        self,
        tool_calls: List[ToolCall],
        user_intent: str
    ) -> List[ToolResult]:
        """Process tool calls through governance."""
        results = []

        for tool_call in tool_calls:
            if tool_call.name not in self.tools_registry:
                results.append(ToolResult(
                    tool_call_id=tool_call.id,
                    success=False,
                    result=None,
                    error=f"Unknown tool: {tool_call.name}"
                ))
                continue

            tool_info = self.tools_registry[tool_call.name]

            # Request governance decision
            decision = self.lexecon.decide(
                actor=self.model_name,
                proposed_action=f"Execute {tool_call.name}",
                tool=tool_call.name,
                user_intent=user_intent,
                risk_level=tool_info["risk_level"],
                data_classes=tool_info["data_classes"]
            )

            if not decision.allowed:
                results.append(ToolResult(
                    tool_call_id=tool_call.id,
                    success=False,
                    result=None,
                    error=f"Access denied: {decision.reason}"
                ))
                continue

            # Execute tool
            try:
                result = tool_info["func"](
                    **tool_call.arguments,
                    capability_token=decision.capability_token.token_id
                )
                results.append(ToolResult(
                    tool_call_id=tool_call.id,
                    success=True,
                    result=result,
                    error=None
                ))
            except Exception as e:
                results.append(ToolResult(
                    tool_call_id=tool_call.id,
                    success=False,
                    result=None,
                    error=str(e)
                ))

        return results

    def _calculate_risk(self, tool_name: str, arguments: Dict) -> int:
        """Calculate dynamic risk level based on tool and arguments."""
        if tool_name in self.tools_registry:
            base_risk = self.tools_registry[tool_name]["risk_level"]
        else:
            base_risk = 3

        # Adjust based on arguments
        sensitive_patterns = ["password", "secret", "key", "token", "credential"]
        args_str = str(arguments).lower()

        if any(pattern in args_str for pattern in sensitive_patterns):
            base_risk = min(5, base_risk + 1)

        return base_risk
```

### Example Custom Adapter

Implementing the base adapter for a custom model:

```python
class MyCustomModelAdapter(BaseGovernedAdapter):
    """Adapter for a custom AI model with governance."""

    def __init__(
        self,
        model_url: str,
        api_key: str,
        lexecon_url: str = "http://localhost:8000"
    ):
        super().__init__("my-custom-model", lexecon_url)
        self.model_url = model_url
        self.api_key = api_key
        self.conversation_history = []

    def chat(self, message: str, user_intent: str = None, **kwargs) -> str:
        """Send message and handle tool calls."""

        # Add message to history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })

        # Get model response
        response = self._call_model_api(
            messages=self.conversation_history,
            tools=self._format_tools()
        )

        # Extract tool calls
        tool_calls = self._extract_tool_calls(response)

        if not tool_calls:
            # No tool calls - return content
            self.conversation_history.append({
                "role": "assistant",
                "content": response["content"]
            })
            return response["content"]

        # Process tool calls through governance
        tool_results = self._process_tool_calls(
            tool_calls,
            user_intent or message
        )

        # Format results for model
        formatted_results = self._format_tool_results(tool_results)
        self.conversation_history.extend(formatted_results)

        # Get final response
        final_response = self._call_model_api(
            messages=self.conversation_history
        )

        return final_response["content"]

    def _call_model_api(self, messages: List[Dict], tools: List[Dict] = None) -> Dict:
        """Call the custom model API."""
        import requests

        response = requests.post(
            f"{self.model_url}/chat",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "messages": messages,
                "tools": tools or []
            }
        )
        response.raise_for_status()
        return response.json()

    def _extract_tool_calls(self, response: Dict) -> List[ToolCall]:
        """Extract tool calls from custom model response."""
        tool_calls = []

        if "tool_calls" in response:
            for tc in response["tool_calls"]:
                tool_calls.append(ToolCall(
                    id=tc["id"],
                    name=tc["name"],
                    arguments=tc["arguments"]
                ))

        return tool_calls

    def _format_tool_results(self, results: List[ToolResult]) -> List[Dict]:
        """Format tool results for custom model."""
        formatted = []

        for result in results:
            formatted.append({
                "role": "tool",
                "tool_call_id": result.tool_call_id,
                "content": result.result if result.success else result.error
            })

        return formatted

    def _format_tools(self) -> List[Dict]:
        """Format registered tools for custom model."""
        return [
            {
                "name": name,
                "description": info["description"]
            }
            for name, info in self.tools_registry.items()
        ]

# Usage
adapter = MyCustomModelAdapter(
    model_url="https://api.mymodel.com",
    api_key="my-api-key",
    lexecon_url="http://localhost:8000"
)

# Register tools
adapter.register_tool(
    name="web_search",
    func=web_search_func,
    description="Search the web",
    risk_level=1
)

# Chat
response = adapter.chat(
    "What's the weather in Tokyo?",
    user_intent="Get weather information"
)
```

---

## Tool Calling Patterns

### Pattern 1: Pre-Execution Gating (Recommended)

Request approval **before** executing the tool:

```python
def pre_execution_gating(tool_call):
    """Request approval before execution."""

    # Step 1: Request decision
    decision = lexecon.decide(
        actor="model",
        proposed_action=f"Execute {tool_call['name']}",
        tool=tool_call["name"],
        user_intent=get_user_intent(),
        risk_level=calculate_risk(tool_call)
    )

    # Step 2: Check approval
    if not decision.allowed:
        return {"error": decision.reason}

    # Step 3: Execute with token
    result = execute_tool(
        tool_call["name"],
        tool_call["arguments"],
        capability_token=decision.capability_token.token_id
    )

    return result
```

**Pros:**
- Prevents unauthorized actions
- Provides clear audit trail
- Token can be verified by tool

**Cons:**
- Adds latency (10-20ms per call)
- Requires network call to Lexecon

### Pattern 2: Post-Execution Auditing

Execute first, audit after (use only for low-risk tools):

```python
def post_execution_auditing(tool_call):
    """Execute then audit (low-risk only)."""

    # Step 1: Execute immediately
    result = execute_tool(
        tool_call["name"],
        tool_call["arguments"]
    )

    # Step 2: Audit asynchronously
    threading.Thread(
        target=audit_execution,
        args=(tool_call, result)
    ).start()

    return result

def audit_execution(tool_call, result):
    """Audit execution asynchronously."""
    lexecon.audit(
        actor="model",
        action=f"Executed {tool_call['name']}",
        tool=tool_call["name"],
        result=result,
        timestamp=time.time()
    )
```

**Pros:**
- No latency impact
- Good for read-only operations

**Cons:**
- Can't prevent unauthorized actions
- Less secure

### Pattern 3: Batch Approval

Request approval for multiple tools at once:

```python
def batch_approval(tool_calls):
    """Request approval for multiple tools."""

    # Step 1: Prepare batch request
    decisions_requests = [
        {
            "actor": "model",
            "proposed_action": f"Execute {tc['name']}",
            "tool": tc["name"],
            "user_intent": get_user_intent(),
            "risk_level": calculate_risk(tc)
        }
        for tc in tool_calls
    ]

    # Step 2: Batch request
    decisions = lexecon.decide_batch(decisions_requests)

    # Step 3: Execute approved tools
    results = []
    for tool_call, decision in zip(tool_calls, decisions):
        if decision.allowed:
            result = execute_tool(
                tool_call["name"],
                tool_call["arguments"],
                capability_token=decision.capability_token.token_id
            )
            results.append(result)
        else:
            results.append({"error": decision.reason})

    return results
```

**Pros:**
- Lower latency than individual requests
- Still prevents unauthorized actions

**Cons:**
- Requires batch API support
- All-or-nothing failure mode

### Pattern 4: Caching Decisions

Cache decisions for repeated tool calls:

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def cached_decision(tool_name, args_hash, user_intent):
    """Cache governance decisions."""
    return lexecon.decide(
        actor="model",
        proposed_action=f"Execute {tool_name}",
        tool=tool_name,
        user_intent=user_intent,
        risk_level=calculate_risk(tool_name)
    )

def cached_governance(tool_call, user_intent):
    """Use cached decisions when possible."""

    # Create cache key
    args_hash = hashlib.sha256(
        json.dumps(tool_call["arguments"], sort_keys=True).encode()
    ).hexdigest()[:16]

    # Get cached decision
    decision = cached_decision(
        tool_call["name"],
        args_hash,
        user_intent
    )

    if decision.allowed:
        return execute_tool(
            tool_call["name"],
            tool_call["arguments"],
            capability_token=decision.capability_token.token_id
        )
    else:
        return {"error": decision.reason}
```

**Pros:**
- Minimal latency for repeated calls
- Still maintains audit trail

**Cons:**
- Cache invalidation complexity
- Stale decisions possible

---

## Prompt Engineering

### System Prompts for Governed Models

Add governance awareness to system prompts:

```python
GOVERNANCE_SYSTEM_PROMPT = """You are a helpful AI assistant with access to various tools.

IMPORTANT GOVERNANCE RULES:
1. All tool calls go through a governance system that may deny requests
2. If a tool call is denied, respect the decision and inform the user
3. Do not attempt to circumvent denials by rephrasing or using alternative tools
4. When denied, explain the reason to the user clearly
5. Some tools have risk levels - prefer lower-risk alternatives when available

Available tools have these risk levels:
- Risk 1 (Low): web_search, calculator, weather
- Risk 2 (Medium): read_file, list_directory
- Risk 3 (High): write_file, send_email
- Risk 4 (Very High): execute_code, database_query
- Risk 5 (Critical): delete_file, system_command

Always consider user privacy and data security when using tools."""

# Use with models
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": GOVERNANCE_SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ],
    tools=tools
)
```

### Handling Denials Gracefully

Teach models to handle denials:

```python
DENIAL_HANDLING_PROMPT = """When a tool call is denied by the governance system:

1. DO NOT retry the same tool call
2. DO NOT try to work around the denial
3. DO explain the reason to the user
4. DO suggest alternatives if available

Example:
User: "Delete the old log files"
Tool: delete_file(path="/var/log/old.log")
Governance: DENIED - Deleting system files requires elevated privileges

Your response should be:
"I cannot delete those log files because the governance system requires elevated privileges for file deletion operations. Instead, I can:
1. Help you identify which files can be safely removed
2. Show you the disk space usage
3. Suggest running the deletion manually with proper permissions"
"""
```

### Risk-Aware Tool Selection

Guide models to choose appropriate risk levels:

```python
RISK_AWARE_PROMPT = """When selecting tools, consider the risk level:

LOW RISK (1-2): Prefer these when possible
- Reading public data
- Calculations
- Information retrieval

MEDIUM RISK (3): Use when necessary
- Reading user files
- Sending notifications
- Making API calls

HIGH RISK (4-5): Only when explicitly requested
- Writing/deleting files
- Executing code
- System operations

Always start with the lowest-risk approach that meets the user's need."""
```

---

## Testing Strategies

### Unit Testing Adapters

```python
import pytest
from unittest.mock import Mock, patch
from my_adapter import GovernedOpenAIClient

class TestGovernedAdapter:
    """Test suite for governed adapters."""

    @pytest.fixture
    def mock_lexecon(self):
        """Mock Lexecon client."""
        with patch('lexecon.LexeconClient') as mock:
            instance = mock.return_value
            instance.decide.return_value = Mock(
                allowed=True,
                reason="Test approval",
                capability_token=Mock(token_id="test-token-123"),
                policy_id="test-policy"
            )
            yield instance

    @pytest.fixture
    def adapter(self, mock_lexecon):
        """Create test adapter."""
        return GovernedOpenAIClient(
            openai_api_key="test-key",
            lexecon_url="http://test:8000"
        )

    def test_tool_call_allowed(self, adapter, mock_lexecon):
        """Test that allowed tool calls execute."""
        # Setup
        mock_lexecon.decide.return_value.allowed = True

        # Execute
        with patch.object(adapter, '_execute_tool', return_value="success"):
            result = adapter.chat(
                message="Search for AI governance",
                tools=[{"name": "web_search", "description": "Search"}]
            )

        # Verify
        assert mock_lexecon.decide.called
        assert "success" in result or result is not None

    def test_tool_call_denied(self, adapter, mock_lexecon):
        """Test that denied tool calls are blocked."""
        # Setup
        mock_lexecon.decide.return_value = Mock(
            allowed=False,
            reason="Policy violation",
            capability_token=None,
            policy_id="test-policy"
        )

        # Execute
        with patch.object(adapter, '_execute_tool') as mock_execute:
            result = adapter.chat(
                message="Delete system files",
                tools=[{"name": "delete_file", "description": "Delete"}]
            )

            # Verify tool was NOT executed
            mock_execute.assert_not_called()

    def test_risk_calculation(self, adapter):
        """Test risk level calculation."""
        assert adapter._calculate_risk("web_search", {}) == 1
        assert adapter._calculate_risk("write_file", {}) == 3
        assert adapter._calculate_risk("execute_code", {}) == 4
        assert adapter._calculate_risk("delete_file", {}) == 5

    def test_data_class_extraction(self, adapter):
        """Test data class identification."""
        classes = adapter._extract_data_classes(
            '{"email": "user@example.com", "query": "test"}'
        )
        assert "email" in classes
```

### Integration Testing

```python
import pytest
from lexecon import LexeconNode, PolicyEngine
from my_adapter import GovernedOpenAIClient

@pytest.fixture(scope="module")
def lexecon_node():
    """Start a real Lexecon node for testing."""
    node = LexeconNode(node_id="test-node")

    # Load test policy
    policy = PolicyEngine(mode="strict")
    policy.load_from_file("tests/fixtures/test_policy.json")
    node.load_policy(policy)

    # Start server
    server = node.start_server(port=18000)
    yield node
    server.shutdown()

@pytest.fixture
def adapter(lexecon_node):
    """Create adapter with real Lexecon instance."""
    return GovernedOpenAIClient(
        openai_api_key=os.environ["OPENAI_API_KEY"],
        lexecon_url="http://localhost:18000"
    )

def test_end_to_end_governance(adapter):
    """Test complete governance flow."""
    # Register test tool
    def test_tool(query, capability_token):
        assert capability_token is not None
        return f"Result for: {query}"

    adapter.register_tool(
        name="test_search",
        func=test_tool,
        description="Test search tool",
        risk_level=1
    )

    # Execute governed interaction
    response = adapter.chat(
        message="Use test_search to find information about governance",
        tools=[{
            "name": "test_search",
            "description": "Test search tool",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }],
        user_intent="Testing governance flow"
    )

    # Verify
    assert response is not None
    assert "Result for:" in response or len(response) > 0
```

### Load Testing

```python
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

def load_test_adapter(adapter, num_requests=100):
    """Load test adapter performance."""

    def single_request():
        start = time.time()
        try:
            adapter.chat(
                message="Search for test data",
                tools=[{
                    "name": "web_search",
                    "description": "Search"
                }]
            )
            return time.time() - start
        except Exception as e:
            return -1

    # Execute requests in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        latencies = list(executor.map(
            lambda _: single_request(),
            range(num_requests)
        ))

    # Calculate statistics
    successful = [l for l in latencies if l > 0]

    print(f"Total requests: {num_requests}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {num_requests - len(successful)}")
    print(f"Average latency: {sum(successful) / len(successful):.3f}s")
    print(f"Min latency: {min(successful):.3f}s")
    print(f"Max latency: {max(successful):.3f}s")

    return {
        "total": num_requests,
        "successful": len(successful),
        "avg_latency": sum(successful) / len(successful),
        "min_latency": min(successful),
        "max_latency": max(successful)
    }
```

---

## Performance Optimization

### Connection Pooling

```python
from lexecon import LexeconClient
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_pooled_client(lexecon_url: str, pool_size: int = 10):
    """Create Lexecon client with connection pooling."""

    # Create session with connection pooling
    session = requests.Session()

    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.1,
        status_forcelist=[429, 500, 502, 503, 504]
    )

    # Mount adapter with pooling
    adapter = HTTPAdapter(
        pool_connections=pool_size,
        pool_maxsize=pool_size,
        max_retries=retry_strategy
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Create client with custom session
    client = LexeconClient(base_url=lexecon_url)
    client.session = session

    return client
```

### Async Adapter Pattern

```python
import asyncio
import aiohttp
from typing import Dict, List

class AsyncGovernedAdapter:
    """Async adapter for high-performance applications."""

    def __init__(self, lexecon_url: str):
        self.lexecon_url = lexecon_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def decide_async(self, **kwargs) -> Dict:
        """Make async governance decision request."""
        async with self.session.post(
            f"{self.lexecon_url}/decide",
            json=kwargs
        ) as response:
            return await response.json()

    async def process_tool_calls_async(
        self,
        tool_calls: List[Dict],
        user_intent: str
    ) -> List[Dict]:
        """Process multiple tool calls concurrently."""

        # Create decision tasks
        decision_tasks = [
            self.decide_async(
                actor="model",
                proposed_action=f"Execute {tc['name']}",
                tool=tc["name"],
                user_intent=user_intent,
                risk_level=self._calculate_risk(tc)
            )
            for tc in tool_calls
        ]

        # Execute all decisions concurrently
        decisions = await asyncio.gather(*decision_tasks)

        # Process results
        results = []
        for tool_call, decision in zip(tool_calls, decisions):
            if decision["allowed"]:
                result = await self._execute_tool_async(
                    tool_call,
                    decision["capability_token"]["token_id"]
                )
                results.append(result)
            else:
                results.append({"error": decision["reason"]})

        return results

# Usage
async def main():
    async with AsyncGovernedAdapter("http://localhost:8000") as adapter:
        results = await adapter.process_tool_calls_async(
            tool_calls=[
                {"name": "web_search", "arguments": {"query": "AI"}},
                {"name": "web_search", "arguments": {"query": "governance"}}
            ],
            user_intent="Research AI governance"
        )
        print(results)

asyncio.run(main())
```

### Local Decision Caching

```python
from datetime import datetime, timedelta
from typing import Dict, Optional
import hashlib
import json

class CachedGovernanceAdapter:
    """Adapter with local decision caching."""

    def __init__(
        self,
        lexecon_client,
        cache_ttl: int = 300,  # 5 minutes
        max_cache_size: int = 1000
    ):
        self.lexecon = lexecon_client
        self.cache_ttl = cache_ttl
        self.max_cache_size = max_cache_size
        self.decision_cache: Dict[str, tuple] = {}

    def decide_with_cache(self, **kwargs) -> Dict:
        """Get decision with caching."""

        # Create cache key
        cache_key = self._create_cache_key(kwargs)

        # Check cache
        if cache_key in self.decision_cache:
            decision, timestamp = self.decision_cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return decision

        # Cache miss - make request
        decision = self.lexecon.decide(**kwargs)

        # Store in cache
        self.decision_cache[cache_key] = (decision, datetime.now())

        # Enforce cache size limit
        if len(self.decision_cache) > self.max_cache_size:
            # Remove oldest entries
            sorted_cache = sorted(
                self.decision_cache.items(),
                key=lambda x: x[1][1]
            )
            for key, _ in sorted_cache[:len(self.decision_cache) - self.max_cache_size]:
                del self.decision_cache[key]

        return decision

    def _create_cache_key(self, kwargs: Dict) -> str:
        """Create cache key from decision parameters."""
        # Only cache based on actor, tool, and risk_level
        # Don't include user_intent to get more cache hits
        key_data = {
            "actor": kwargs.get("actor"),
            "tool": kwargs.get("tool"),
            "risk_level": kwargs.get("risk_level")
        }
        key_json = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_json.encode()).hexdigest()[:16]
```

---

## Troubleshooting

### Common Issues

**Issue 1: "Connection refused" to Lexecon**

```python
# Solution: Check Lexecon server is running
import requests

try:
    response = requests.get("http://localhost:8000/health")
    print(f"Lexecon status: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("Lexecon server is not running!")
    print("Start with: lexecon server --node-id my-node")
```

**Issue 2: All decisions are denied**

```python
# Solution: Check policy mode and rules
from lexecon import LexeconClient

client = LexeconClient()
policy_info = client.get_policy_info()

print(f"Mode: {policy_info['mode']}")
print(f"Rules: {policy_info['rule_count']}")

# If mode is "strict", you need explicit allow rules
# If mode is "permissive", check deny rules
```

**Issue 3: Capability tokens not accepted**

```python
# Solution: Verify token format and expiration
def verify_token(token_id: str):
    """Verify capability token."""
    response = client.verify_token(token_id=token_id)

    if not response["valid"]:
        print(f"Token invalid: {response['reason']}")
        print(f"Expired: {response.get('expired', False)}")
        print(f"TTL: {response.get('ttl', 'N/A')}s")
    else:
        print("Token is valid")
```

**Issue 4: High latency**

```python
# Solution: Enable caching and connection pooling
from my_adapter import CachedGovernanceAdapter, create_pooled_client

# Use pooled client
lexecon = create_pooled_client(
    lexecon_url="http://localhost:8000",
    pool_size=20
)

# Add caching
cached_adapter = CachedGovernanceAdapter(
    lexecon_client=lexecon,
    cache_ttl=300,  # 5 minutes
    max_cache_size=1000
)
```

### Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("lexecon.adapter")

class DebugGovernedAdapter:
    """Adapter with extensive debug logging."""

    def decide_with_logging(self, **kwargs):
        """Make decision with debug logging."""
        logger.debug(f"Decision request: {kwargs}")

        start_time = time.time()
        decision = self.lexecon.decide(**kwargs)
        latency = time.time() - start_time

        logger.debug(f"Decision response: {decision}")
        logger.debug(f"Latency: {latency:.3f}s")

        if not decision.allowed:
            logger.warning(f"Decision denied: {decision.reason}")

        return decision
```

---

## Best Practices

### 1. Always Use Pre-Execution Gating

```python
# GOOD: Check before executing
decision = lexecon.decide(...)
if decision.allowed:
    result = execute_tool(...)

# BAD: Execute without checking
result = execute_tool(...)  # Could be unauthorized!
```

### 2. Provide Meaningful Context

```python
# GOOD: Rich context
decision = lexecon.decide(
    actor="gpt-4",
    proposed_action="Execute web_search to find AI governance regulations",
    tool="web_search",
    user_intent="User researching compliance requirements for healthcare AI",
    risk_level=1,
    data_classes=[]
)

# BAD: Minimal context
decision = lexecon.decide(
    actor="model",
    proposed_action="tool",
    tool="web_search",
    user_intent="unknown",
    risk_level=1
)
```

### 3. Handle Denials Gracefully

```python
# GOOD: Informative error handling
if not decision.allowed:
    return {
        "error": "This action is not permitted",
        "reason": decision.reason,
        "suggested_alternatives": [
            "Try using a lower-risk tool",
            "Request elevated permissions"
        ]
    }

# BAD: Silent failure
if not decision.allowed:
    return None
```

### 4. Implement Proper Error Recovery

```python
# GOOD: Retry with exponential backoff
def decide_with_retry(max_retries=3):
    for attempt in range(max_retries):
        try:
            return lexecon.decide(...)
        except requests.exceptions.ConnectionError:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

### 5. Monitor Adapter Performance

```python
# GOOD: Track metrics
from prometheus_client import Counter, Histogram

decisions_total = Counter(
    'governance_decisions_total',
    'Total governance decisions',
    ['allowed', 'tool']
)

decision_latency = Histogram(
    'governance_decision_latency_seconds',
    'Decision request latency'
)

def monitored_decide(**kwargs):
    with decision_latency.time():
        decision = lexecon.decide(**kwargs)

    decisions_total.labels(
        allowed=decision.allowed,
        tool=kwargs['tool']
    ).inc()

    return decision
```

### 6. Test Thoroughly

```python
# GOOD: Comprehensive test coverage
def test_adapter():
    # Test allowed case
    test_tool_call_allowed()

    # Test denied case
    test_tool_call_denied()

    # Test error handling
    test_lexecon_unavailable()

    # Test edge cases
    test_malformed_tool_call()
    test_invalid_capability_token()
```

---

## Conclusion

This guide covered comprehensive patterns for integrating AI models with Lexecon governance. Key takeaways:

1. **Use pre-execution gating** for security-critical operations
2. **Provide rich context** for better governance decisions
3. **Handle denials gracefully** with clear user feedback
4. **Optimize performance** with caching and connection pooling
5. **Test thoroughly** including edge cases and failures
6. **Monitor** adapter performance and governance decisions

For additional help:
- **Documentation**: https://lexecon.readthedocs.io
- **Examples**: See `examples/` directory
- **Issues**: https://github.com/Lexicoding-systems/Lexecon/issues

**Happy governing! 🛡️**
