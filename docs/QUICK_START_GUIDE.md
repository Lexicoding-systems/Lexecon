# Quick Start Guide for New Contributors

Welcome to Lexecon! This guide will help you get up and running quickly.

## Prerequisites

- Python 3.8 or higher
- Git
- GitHub account

## Setup (5 minutes)

### 1. Clone and Install

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Lexecon.git
cd Lexecon

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### 2. Install Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Test hooks (optional)
pre-commit run --all-files
```

Now pre-commit will automatically:
- Format code with black and isort
- Run linters (ruff, flake8, mypy)
- Check for secrets and security issues
- Validate commit messages

### 3. Verify Installation

```bash
# Run tests
pytest

# Run linters
make lint

# Format code
make format
```

## Development Workflow

### Making Changes

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make your changes
# ...

# Pre-commit runs automatically on commit
git add .
git commit -m "feat: add my feature"

# Push and create PR
git push origin feature/my-feature
```

### Manual Quality Checks

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lexecon

# Run specific test file
pytest tests/test_policy.py

# Run linters
ruff check src/  # Fast comprehensive linting
flake8 src/      # Traditional linting
mypy src/        # Type checking

# Format code
black src/ tests/
isort src/ tests/

# Or use make commands
make test
make lint
make format
```

## New Tools Overview

### Ruff - Fast Python Linter

**What it is**: Modern, fast linter that replaces flake8, pylint, isort, and more.

**Usage**:
```bash
# Check code
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Format code (alternative to black)
ruff format src/
```

**Benefits**:
- 10-100x faster than traditional linters
- Combines multiple tools into one
- Auto-fixes most issues
- Configured in `pyproject.toml`

### Pre-commit Hooks

**What it is**: Git hooks that run checks before commits.

**What runs automatically**:
1. File checks (trailing whitespace, merge conflicts)
2. Code formatting (black, isort, ruff)
3. Linting (flake8, ruff)
4. Type checking (mypy)
5. Security checks (bandit, detect-secrets)
6. Commit message validation

**Skip hooks** (emergency only):
```bash
git commit --no-verify
```

**Update hooks**:
```bash
pre-commit autoupdate
```

### Example Policy Templates

**Where**: `examples/policies/`

**Available templates**:
- `gdpr_compliance_policy.json` - GDPR compliance
- `hipaa_healthcare_policy.json` - HIPAA healthcare
- `financial_services_policy.json` - Financial/PCI-DSS
- `enterprise_general_policy.json` - General enterprise

**Try them**:
```bash
# Start server
lexecon server --node-id test-node

# Load policy
lexecon policy load --file examples/policies/gdpr_compliance_policy.json

# Test decision
lexecon decide \
  --actor ai_model \
  --action "Process user data" \
  --data-class personal_data \
  --risk-level 3
```

## Common Tasks

### Run Specific Tests

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Test with verbose output
pytest -v

# Test and show print statements
pytest -s

# Test with coverage report
pytest --cov=lexecon --cov-report=html
open htmlcov/index.html
```

### Fix Linting Issues

```bash
# Auto-fix with ruff (fastest)
ruff check --fix src/ tests/

# Format imports
isort src/ tests/

# Format code
black src/ tests/

# Check remaining issues
ruff check src/
flake8 src/
mypy src/
```

### Update Dependencies

```bash
# Update pre-commit hooks
pre-commit autoupdate

# Update Python packages
pip install --upgrade pip
pip install --upgrade -e ".[dev]"
```

## Troubleshooting

### Pre-commit hooks failing

**Problem**: Hooks fail on commit

**Solutions**:
```bash
# Run hooks manually to see details
pre-commit run --all-files

# Fix formatting issues
make format

# Update hooks
pre-commit autoupdate

# Skip hooks (last resort)
git commit --no-verify
```

### Import errors

**Problem**: `ModuleNotFoundError`

**Solutions**:
```bash
# Reinstall in development mode
pip install -e ".[dev]"

# Check installation
pip list | grep lexecon
```

### Tests failing

**Problem**: Tests fail locally

**Solutions**:
```bash
# Run specific failing test
pytest tests/path/to/test.py::test_name -v

# Check test dependencies
pip install -e ".[dev]"

# Clear pytest cache
rm -rf .pytest_cache
pytest
```

### Ruff vs Flake8 conflicts

**Problem**: Different linting results

**Solution**: Ruff is primary; flake8 kept for compatibility. Follow ruff recommendations:
```bash
ruff check --fix src/
```

## Next Steps

1. **Read Documentation**
   - [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
   - [BRANCH_PROTECTION_SETUP.md](BRANCH_PROTECTION_SETUP.md) - Security setup
   - [README.md](../README.md) - Full documentation

2. **Try Example Policies**
   - Load and test policy templates
   - Modify for your use case
   - Write tests for custom policies

3. **Pick an Issue**
   - Check [Issues](https://github.com/Lexicoding-systems/Lexecon/issues)
   - Look for `good first issue` label
   - Ask questions in issues or discussions

4. **Join Community**
   - [GitHub Discussions](https://github.com/Lexicoding-systems/Lexecon/discussions)
   - Email: jacobporter@lexicoding.tech

## Quick Reference

### Common Commands

| Task | Command |
|------|--------|
| Run tests | `pytest` or `make test` |
| Run linters | `ruff check src/` or `make lint` |
| Format code | `black src/` or `make format` |
| Type check | `mypy src/` |
| Run pre-commit | `pre-commit run --all-files` |
| Start server | `lexecon server --node-id test` |
| Load policy | `lexecon policy load --file path.json` |

### Commit Message Format

```
<type>(<scope>): <subject>

Types: feat, fix, docs, style, refactor, test, chore
Example: feat(policy): add GDPR compliance template
```

## Questions?

- Check [FAQ](../README.md#faq)
- Search [Issues](https://github.com/Lexicoding-systems/Lexecon/issues)
- Ask in [Discussions](https://github.com/Lexicoding-systems/Lexecon/discussions)
- Email: jacobporter@lexicoding.tech

Happy coding! 🚀
