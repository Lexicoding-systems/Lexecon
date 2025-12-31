# Contributing to Lexecon

Thank you for your interest in contributing to Lexecon! We welcome contributions from the community and are excited to work with you to make AI governance safer, more transparent, and more accessible.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Requirements](#testing-requirements)
- [Documentation Requirements](#documentation-requirements)
- [Review Process](#review-process)
- [Community Guidelines](#community-guidelines)
- [Recognition](#recognition)

---

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to conduct@lexicoding.systems.

### Our Pledge

We pledge to make participation in our project and our community a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behaviors include:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behaviors include:**
- The use of sexualized language or imagery
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate

---

## How Can I Contribute?

There are many ways to contribute to Lexecon:

### 🐛 Reporting Bugs

Before creating bug reports, please check the [existing issues](https://github.com/Lexicoding-systems/Lexecon/issues) to avoid duplicates.

**When filing a bug report, include:**
- A clear, descriptive title
- Exact steps to reproduce the problem
- Expected vs. actual behavior
- Screenshots or error messages (if applicable)
- Your environment (OS, Python version, Lexecon version)
- Any relevant configuration files

**Use this template:**
```markdown
## Bug Description
Brief description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.2]
- Lexecon: [e.g., 0.1.0]

## Additional Context
Any other relevant information
```

### ✨ Suggesting Enhancements

We welcome feature requests and enhancement suggestions!

**When suggesting an enhancement:**
- Use a clear, descriptive title
- Provide a detailed description of the proposed feature
- Explain why this enhancement would be useful
- Provide examples of how it would work
- Consider backwards compatibility

### 📝 Improving Documentation

Documentation improvements are always welcome:
- Fix typos or clarify existing documentation
- Add examples and tutorials
- Improve API documentation
- Translate documentation
- Create video tutorials or blog posts

### 💻 Code Contributions

We welcome code contributions for:
- Bug fixes
- New features
- Performance improvements
- Test coverage improvements
- Code refactoring

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- GitHub account
- Basic understanding of cryptography and AI governance (helpful but not required)

### Development Setup

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/Lexecon.git
   cd Lexecon
   ```

2. **Set up the upstream remote**
   ```bash
   git remote add upstream https://github.com/Lexicoding-systems/Lexecon.git
   ```

3. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

5. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

6. **Verify your setup**
   ```bash
   pytest
   make lint
   ```

### Project Structure Overview

```
Lexecon/
├── src/lexecon/          # Main package source code
│   ├── api/             # FastAPI server
│   ├── capability/      # Capability token system
│   ├── cli/             # Command-line interface
│   ├── decision/        # Decision service
│   ├── identity/        # Identity management
│   ├── ledger/          # Audit ledger
│   └── policy/          # Policy engine
├── tests/               # Test suite
├── docs/                # Documentation
├── examples/            # Example files
└── model_governance_pack/  # Model integration
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create a new branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test improvements
- `chore/` - Maintenance tasks

### 2. Make Your Changes

- Write clean, readable code
- Follow the coding standards (see below)
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### 3. Test Your Changes

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lexecon --cov-report=html

# Run specific tests
pytest tests/test_policy.py

# Run linters
make lint

# Format code
make format

# Type checking
make typecheck
```

### 4. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "feat: add new policy evaluation mode"
```

See [Commit Message Guidelines](#commit-message-guidelines) below.

### 5. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 6. Create a Pull Request

1. Go to your fork on GitHub
2. Click "New Pull Request"
3. Select your feature branch
4. Fill out the PR template
5. Submit the PR

---

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://peps.python.org/pep-0008/) with some modifications:

- **Line length**: 100 characters (not 79)
- **Formatting**: Use Black for automatic formatting
- **Import sorting**: Use isort
- **Type hints**: Required for all public functions
- **Docstrings**: Google style for all public modules, classes, and functions

### Code Formatting

```bash
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Or use make command
make format
```

### Type Hints

All public functions must include type hints:

```python
from typing import Optional, List, Dict

def evaluate_policy(
    actor: str,
    action: str,
    data_classes: List[str],
    risk_level: int = 1
) -> Dict[str, Any]:
    """
    Evaluate a policy decision.

    Args:
        actor: The actor making the request
        action: The action being requested
        data_classes: List of data classes involved
        risk_level: Risk level (1-5)

    Returns:
        Decision dictionary with allowed status and reasoning

    Raises:
        ValueError: If risk_level is not between 1 and 5
    """
    pass
```

### Docstring Format

Use Google-style docstrings:

```python
def mint_capability_token(
    action: str,
    scope: Dict[str, Any],
    ttl: int = 300
) -> CapabilityToken:
    """
    Mint a new capability token for an approved action.

    This function creates a cryptographically signed capability token
    that authorizes a specific action with a limited scope and time-to-live.

    Args:
        action: The action being authorized
        scope: Dictionary defining the scope of authorization
        ttl: Time-to-live in seconds (default: 300)

    Returns:
        A signed CapabilityToken object

    Raises:
        SigningError: If token signing fails
        ValueError: If ttl is negative or exceeds maximum

    Example:
        >>> token = mint_capability_token(
        ...     action="web_search",
        ...     scope={"query": "AI governance"},
        ...     ttl=600
        ... )
        >>> print(token.token_id)
        'tok_abc123...'
    """
    pass
```

### Naming Conventions

- **Classes**: PascalCase (e.g., `PolicyEngine`, `DecisionService`)
- **Functions/Methods**: snake_case (e.g., `evaluate_policy`, `mint_token`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_TTL`, `MAX_RISK_LEVEL`)
- **Private members**: Prefix with underscore (e.g., `_internal_helper`)

### Error Handling

- Use specific exception types
- Provide clear error messages
- Always include context in exceptions

```python
# Good
if risk_level < 1 or risk_level > 5:
    raise ValueError(
        f"Risk level must be between 1 and 5, got {risk_level}"
    )

# Bad
if risk_level < 1 or risk_level > 5:
    raise Exception("Invalid risk level")
```

### Testing Standards

- Write tests for all new functionality
- Maintain test coverage above 80%
- Use descriptive test names
- Follow the Arrange-Act-Assert pattern

```python
def test_strict_mode_denies_unknown_actions():
    """Test that strict mode denies actions not explicitly permitted."""
    # Arrange
    engine = PolicyEngine(mode="strict")

    # Act
    decision = engine.evaluate(
        actor="model",
        action="unknown_action",
        data_classes=[]
    )

    # Assert
    assert decision.allowed is False
    assert "not explicitly permitted" in decision.reason.lower()
```

---

## Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependency updates
- `ci`: CI/CD changes
- `build`: Build system changes

### Examples

```bash
# Simple feature
git commit -m "feat: add paranoid policy mode"

# Bug fix with scope
git commit -m "fix(ledger): prevent hash chain corruption on concurrent writes"

# Breaking change
git commit -m "feat!: change capability token format to include policy hash

BREAKING CHANGE: Capability tokens now require policy_version_hash field.
Existing tokens will need to be regenerated."

# Multi-line with body
git commit -m "refactor(policy): improve evaluation performance

- Cache compiled policy rules
- Use lazy evaluation for constraints
- Add performance benchmarks

Closes #123"
```

### Rules

- Use the imperative mood ("add feature" not "added feature")
- Don't capitalize the first letter of the subject
- No period at the end of the subject
- Limit subject line to 72 characters
- Wrap body at 72 characters
- Use the body to explain what and why (not how)

---

## Pull Request Process

### Before Submitting

- [ ] Code follows the style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (for significant changes)
- [ ] No merge conflicts with main branch

### PR Template

When creating a PR, fill out this template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Related Issues
Fixes #123
Relates to #456

## How Has This Been Tested?
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code in hard-to-understand areas
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally
- [ ] Any dependent changes have been merged and published

## Screenshots (if applicable)

## Additional Notes
```

### PR Size Guidelines

- Keep PRs focused and reasonably sized (< 500 lines when possible)
- Break large changes into multiple PRs
- Each PR should address a single concern

### Review Process

1. **Automated Checks**: CI/CD runs tests, linters, and security checks
2. **Peer Review**: At least one maintainer will review your PR
3. **Feedback**: Address review comments and push updates
4. **Approval**: Once approved, a maintainer will merge your PR

**Review timeline:**
- Small PRs (< 100 lines): 1-2 days
- Medium PRs (100-500 lines): 3-5 days
- Large PRs (> 500 lines): 5-7 days

---

## Testing Requirements

### Test Coverage

- Maintain overall test coverage above 80%
- New features must include tests
- Bug fixes must include regression tests

### Test Types

**Unit Tests** (`tests/unit/`)
```python
def test_policy_term_creation():
    """Test creating a policy term."""
    term = PolicyTerm.create_action("read", "Read action")
    assert term.type == "action"
    assert term.name == "read"
```

**Integration Tests** (`tests/integration/`)
```python
def test_decision_service_with_ledger():
    """Test decision service records to ledger."""
    service = DecisionService(ledger=ledger)
    decision = service.evaluate(...)
    assert ledger.get_entry(decision.ledger_entry_hash) is not None
```

**End-to-End Tests** (`tests/e2e/`)
```python
def test_full_governance_flow(client):
    """Test complete governance flow from request to token verification."""
    # Make decision request
    response = client.post("/decide", json=request_data)
    # Verify token
    token = response.json()["capability_token"]
    verify_response = client.post("/verify", json={"token": token})
    assert verify_response.json()["valid"] is True
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_policy.py

# Specific test
pytest tests/test_policy.py::test_strict_mode_denies_unknown_actions

# With coverage
pytest --cov=lexecon --cov-report=html

# Watch mode (requires pytest-watch)
ptw
```

---

## Documentation Requirements

### Code Documentation

- All public modules, classes, and functions must have docstrings
- Use Google-style docstrings
- Include examples for complex functionality

### User Documentation

When adding features, update:
- README.md (if it affects quick start or main features)
- Relevant docs in `docs/` directory
- API documentation (if adding API endpoints)
- CLI help text (if adding CLI commands)

### Examples

Provide working examples for new features in `examples/` directory.

---

## Review Process

### What Reviewers Look For

1. **Correctness**: Does the code do what it claims?
2. **Security**: Are there any security vulnerabilities?
3. **Performance**: Are there any performance concerns?
4. **Testing**: Are tests adequate and passing?
5. **Documentation**: Is documentation clear and complete?
6. **Style**: Does code follow style guidelines?
7. **Design**: Is the design clean and maintainable?

### Responding to Review Comments

- Be respectful and professional
- Ask for clarification if needed
- Explain your reasoning when disagreeing
- Make requested changes promptly
- Mark conversations as resolved when addressed

### After Approval

- Don't push new commits after approval (unless requested)
- Maintainers will merge using "Squash and merge" or "Rebase and merge"
- Delete your branch after merging

---

## Community Guidelines

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: General questions, ideas, showcase
- **Email**: contact@lexicoding.systems for private matters

### Getting Help

If you're stuck or have questions:
1. Check existing documentation
2. Search closed issues and discussions
3. Ask in GitHub Discussions
4. Tag relevant maintainers (don't overuse)

### Being a Good Community Member

- Be patient with responses (maintainers are volunteers)
- Help other contributors when you can
- Share your use cases and experiences
- Give credit to others' work
- Celebrate successes together

---

## Recognition

We value all contributions and recognize contributors in several ways:

### Contributors File

All contributors are listed in `CONTRIBUTORS.md`

### Release Notes

Significant contributions are mentioned in release notes

### Social Media

We highlight contributor work on our social media channels (with permission)

### Badges

Active contributors may receive special badges on our Discord/Slack

---

## Questions?

If you have questions about contributing:
- Check our [FAQ](README.md#faq)
- Ask in [GitHub Discussions](https://github.com/Lexicoding-systems/Lexecon/discussions)
- Email us at contribute@lexicoding.systems

---

## License

By contributing to Lexecon, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Lexecon and helping make AI governance safer and more transparent!

**Happy Coding!** 🚀
