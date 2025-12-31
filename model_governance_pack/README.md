# Model Governance Pack

Integration resources for connecting foundation models to Lexecon governance.

## Contents

- **schemas/** - JSON schemas for requests and responses
- **adapters/** - Integration adapters for different model providers
- **prompts/** - System prompt templates for model configuration
- **examples/** - Example decision requests and model transcripts

## Quick Start

1. Review the JSON schemas to understand the request/response format
2. Use the appropriate adapter for your model provider (OpenAI, Anthropic, etc.)
3. Include the system prompt template in your model configuration
4. Route all tool calls through the Lexecon decision endpoint

## Integration Flow

```
User Request → Model → Lexecon Decision Endpoint → Policy Evaluation
                ↓                                            ↓
            Tool Call ← Capability Token ← Decision Response
```

## Supported Providers

- OpenAI (GPT-4, etc.)
- Anthropic (Claude)
- Custom providers (see adapter template)

## Documentation

See the main [Implementation Guide](../docs/IMPLEMENTATION_GUIDE.md) for detailed integration instructions.
