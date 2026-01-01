# Lexecon - Lexical Governance Protocol

<div align="center">

[![CI](https://github.com/Lexicoding-systems/Lexecon/actions/workflows/ci.yml/badge.svg)](https://github.com/Lexicoding-systems/Lexecon/actions/workflows/ci.yml)
[![CodeQL](https://github.com/Lexicoding-systems/Lexecon/actions/workflows/codeql.yml/badge.svg)](https://github.com/Lexicoding-systems/Lexecon/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/Lexicoding-systems/Lexecon/branch/main/graph/badge.svg)](https://codecov.io/gh/Lexicoding-systems/Lexecon)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![OpenSSF Best Practices](https://www.bestpractices.coreinfrastructure.org/projects/9999/badge)](https://www.bestpractices.coreinfrastructure.org/projects/9999)
[![GitHub stars](https://img.shields.io/github/stars/Lexicoding-systems/Lexecon?style=social)](https://github.com/Lexicoding-systems/Lexecon/stargazers)

**A unified cryptographic governance system for AI safety, compliance, and auditability**

[Documentation](https://lexecon.readthedocs.io) | [Quick Start](#quick-start) | [API Reference](#api-reference) | [Contributing](#contributing)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
  - [CLI Commands](#cli-commands)
  - [API Endpoints](#api-endpoints)
  - [Python SDK](#python-sdk)
- [Policy System](#policy-system)
- [Model Integration](#model-integration)
- [System Invariants](#system-invariants)
- [Compliance & Standards](#compliance--standards)
- [Development](#development)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

---

## Overview

Lexecon provides a complete governance framework for AI systems by combining lexicoding-forward policy models with runtime gating and tamper-evident ledgers. It ensures that AI systems operate within defined boundaries, with every action being cryptographically auditable.

### What Makes Lexecon Different?

- **Deny-by-Default**: Safe defaults with explicit permission requirements
- **Cryptographic Guarantees**: Every decision is signed, hashed, and chain-linked
- **Runtime Enforcement**: Policies are enforced at execution time, not just checked
- **Model-Agnostic**: Works with any foundation model (OpenAI, Anthropic, open-source)
- **Compliance-Ready**: Built-in mapping to GDPR, EU AI Act, SOC 2

---

## Problem Statement

Modern AI systems face critical challenges:

1. **Uncontrolled Tool Usage**: Models can execute arbitrary tool calls without oversight
2. **Audit Gaps**: No tamper-proof record of what actions were taken and why
3. **Compliance Burden**: Manual mapping of AI behavior to regulatory requirements
4. **Policy Drift**: Policies become outdated or inconsistent with actual behavior
5. **Prompt Injection**: Adversarial inputs can bypass intent-based controls

**Lexecon solves these problems** by providing:
- Pre-execution gating for all tool calls
- Cryptographic audit trail with hash chaining
- Declarative policies that compile to executable constraints
- Injection-resistant evaluation framework

---

## Key Features

### 🔐 Lexicoding-Forward Policies
- Policy as lexicon (terms/nodes) + relations (edges)
- Compiles into executable constraints
- Version-controlled and hash-pinned

### ⚡ Runtime Gating
- Every tool call must pass through decision service
- Capability tokens for approved actions
- Expiry and scope enforcement

### 🔗 Cryptographic Auditability
- Ed25519 signatures on all decisions
- Hash-chained ledger entries
- Deterministic serialization
- Verification tooling included

### 🛡️ Capability Enforcement
- "Allowed" means cryptographically authorized
- Ephemeral tokens with limited scope
- Policy version binding

### 🤖 Model Integration Pack
- System prompts for governance-aware models
- JSON schemas for requests/responses
- Adapters for OpenAI and Anthropic APIs
- Example transcripts and test cases

### 🔴 Anti-Tamper Posture
- Injection resistance via structured evaluation
- Policy tamper detection
- Red team harness included

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Lexecon Protocol Stack                        │
├─────────────────────────────────────────────────────────────────┤
│  Model Integration Layer                                         │
│    • System Prompts & Instruction Templates                      │
│    • JSON Schema Definitions                                     │
│    • API Adapters (OpenAI, Anthropic, Generic)                   │
├─────────────────────────────────────────────────────────────────┤
│  Policy Engine (src/lexecon/policy/)                             │
│    • Lexicon: Terms (Actions, Data Classes, Actors)              │
│    • Relations: Permits, Forbids, Requires, Implies              │
│    • Constraints: Compile-time and Runtime Checks                │
│    • Evaluation: Deterministic Policy Resolution                 │
├─────────────────────────────────────────────────────────────────┤
│  Decision Service (src/lexecon/decision/)                        │
│    • Request Validation & Normalization                          │
│    • Policy Evaluation Pipeline                                  │
│    • Reason Trace Generation                                     │
│    • Capability Token Minting                                    │
├─────────────────────────────────────────────────────────────────┤
│  Capability System (src/lexecon/capability/)                     │
│    • Token Generation (Scoped, Time-Limited)                     │
│    • Token Verification & Validation                             │
│    • Policy Version Binding                                      │
├─────────────────────────────────────────────────────────────────┤
│  Cryptographic Ledger (src/lexecon/ledger/)                      │
│    • Event Recording with Hash Chains                            │
│    • Signature Generation & Verification                         │
│    • Audit Report Generation                                     │
│    • Integrity Verification                                      │
├─────────────────────────────────────────────────────────────────┤
│  Identity & Signing (src/lexecon/identity/)                      │
│    • Ed25519 Key Management                                      │
│    • Node Identity                                               │
│    • Key Storage & Retrieval                                     │
├─────────────────────────────────────────────────────────────────┤
│  API Layer (src/lexecon/api/)                                    │
│    • FastAPI Server                                              │
│    • REST Endpoints                                              │
│    • Request/Response Models                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | Purpose | Key Files |
|-----------|---------|-----------|
| **Policy Engine** | Evaluate governance rules | `policy/engine.py`, `policy/terms.py`, `policy/relations.py` |
| **Decision Service** | Gate tool calls and generate decisions | `decision/service.py`, `decision/models.py` |
| **Capability System** | Issue and verify authorization tokens | `capability/token.py`, `capability/verifier.py` |
| **Ledger** | Maintain tamper-proof audit log | `ledger/chain.py`, `ledger/events.py` |
| **Identity** | Manage cryptographic identities | `identity/keypair.py`, `identity/node.py` |
| **API** | HTTP interface for decision requests | `api/server.py`, `api/routes.py` |
| **CLI** | Command-line tooling | `cli/main.py`, `cli/commands/` |

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Method 1: Install from PyPI (Recommended)

```bash
pip install lexecon
```

### Method 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/Lexicoding-systems/Lexecon.git
cd Lexecon

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Method 3: Using Poetry

```bash
git clone https://github.com/Lexicoding-systems/Lexecon.git
cd Lexecon
poetry install
```

### Method 4: Using Docker

```bash
docker pull lexecon/lexecon:latest
docker run -p 8000:8000 lexecon/lexecon:latest
```

### Verify Installation

```bash
lexecon --version
lexecon doctor
```

---
" + README.md[6823:]