# Installation

This guide covers various methods to install Lexecon on your system.

---

## Prerequisites

- **Python**: 3.8 or higher
- **pip**: Python package manager
- **Git**: For source installation

Check your Python version:
```bash
python --version
# or
python3 --version
```

---

## Installation Methods

### Method 1: Install from PyPI (Recommended)

Once published to PyPI, you can install Lexecon with:

```bash
pip install lexecon
```

For the latest pre-release version:
```bash
pip install --pre lexecon
```

### Method 2: Install from Source

Clone the repository and install:

```bash
# Clone the repository
git clone https://github.com/Lexicoding-systems/Lexecon.git
cd Lexecon

# Install in development mode
pip install -e .
```

Install with development dependencies:
```bash
pip install -e ".[dev]"
```

Install with documentation tools:
```bash
pip install -e ".[docs]"
```

Install everything:
```bash
pip install -e ".[dev,docs]"
```

### Method 3: Using Poetry

If you use Poetry for dependency management:

```bash
git clone https://github.com/Lexicoding-systems/Lexecon.git
cd Lexecon
poetry install
```

### Method 4: Using Docker

Pull and run the Docker image:

```bash
# Pull the latest image
docker pull lexecon/lexecon:latest

# Run the API server
docker run -p 8000:8000 lexecon/lexecon:latest

# Run with custom configuration
docker run -p 8000:8000 -v /path/to/config:/config lexecon/lexecon:latest
```

Build from source:
```bash
git clone https://github.com/Lexicoding-systems/Lexecon.git
cd Lexecon
docker build -t lexecon:local .
docker run -p 8000:8000 lexecon:local
```

---

## Verify Installation

After installation, verify that Lexecon is installed correctly:

```bash
# Check version
lexecon --version

# Run diagnostic check
lexecon doctor

# Display help
lexecon --help
```

Expected output:
```
lexecon, version 0.1.0
Python 3.8+ governance framework for AI systems
```

---

## Virtual Environment (Recommended)

It's recommended to use a virtual environment:

### Using venv

```bash
# Create virtual environment
python -m venv lexecon-env

# Activate (Linux/Mac)
source lexecon-env/bin/activate

# Activate (Windows)
lexecon-env\Scripts\activate

# Install Lexecon
pip install lexecon

# Deactivate when done
deactivate
```

### Using conda

```bash
# Create conda environment
conda create -n lexecon python=3.11

# Activate environment
conda activate lexecon

# Install Lexecon
pip install lexecon

# Deactivate when done
conda deactivate
```

---

## Dependencies

Lexecon requires the following dependencies:

**Core Dependencies:**
- `fastapi>=0.109.0` - Web framework
- `uvicorn[standard]>=0.27.0` - ASGI server
- `pydantic>=2.5.0` - Data validation
- `cryptography>=42.0.0` - Cryptographic operations
- `click>=8.1.0` - CLI framework
- `pyyaml>=6.0` - YAML parsing
- `requests>=2.31.0` - HTTP client

**Development Dependencies:**
- `pytest>=7.4.0` - Testing framework
- `pytest-cov>=4.1.0` - Code coverage
- `black>=23.12.0` - Code formatter
- `flake8>=7.0.0` - Linter
- `mypy>=1.8.0` - Type checker

These are automatically installed when you install Lexecon.

---

## Platform-Specific Notes

### Linux

No special requirements. Install using any method above.

### macOS

May need to install system dependencies:
```bash
# Install Xcode Command Line Tools
xcode-select --install
```

### Windows

1. Install Python from [python.org](https://www.python.org/downloads/)
2. Ensure Python is added to PATH
3. Use PowerShell or Command Prompt for installation

---

## Troubleshooting

### Python Version Issues

If you have multiple Python versions:
```bash
# Use specific version
python3.11 -m pip install lexecon
```

### Permission Errors

If you get permission errors:
```bash
# Install for current user only
pip install --user lexecon
```

### SSL Certificate Errors

If you encounter SSL errors:
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org lexecon
```

### Dependency Conflicts

Create a fresh virtual environment to avoid conflicts:
```bash
python -m venv fresh-env
source fresh-env/bin/activate
pip install lexecon
```

---

## Next Steps

After installation:
1. Read the [[Getting Started]] guide
2. Initialize your first governance node
3. Explore the [[API Reference]]
4. Check out [[Examples]]

---

## Upgrading

To upgrade to the latest version:

```bash
# From PyPI
pip install --upgrade lexecon

# From source
cd Lexecon
git pull origin main
pip install -e .
```

---

## Uninstalling

To remove Lexecon:

```bash
pip uninstall lexecon
```

To also remove configuration and data:
```bash
rm -rf ~/.lexecon
```
