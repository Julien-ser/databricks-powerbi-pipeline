# Contributing Guidelines

Thank you for considering contributing to the databricks-powerbi-pipeline project! This document outlines the process for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)

---

## Code of Conduct

This project adheres to a code of conduct adapted from the [Contributor Covenant](https://www.contributor-covenant.org/). By participating, you are expected to:

- Be respectful and inclusive
- Accept constructive feedback
- Focus on the best interests of the community
- Show empathy towards other contributors

---

## Getting Started

### 1. Fork the Repository

Click the "Fork" button on GitHub to create your own copy.

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR-USERNAME/databricks-powerbi-pipeline.git
cd databricks-powerbi-pipeline
```

### 3. Add Upstream Remote

```bash
git remote add upstream https://github.com/original-owner/databricks-powerbi-pipeline.git
```

### 4. Create a Virtual Environment (Optional)

Although the project is designed to run without venv, you may create one:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Install Pre-commit Hooks (Optional but Recommended)

```bash
pre-commit install
```

---

## Development Workflow

### 1. Pull Latest Changes

```bash
git checkout main
git pull upstream main
```

### 2. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

**Branch naming conventions:**
- `feature/` - New features
- `bugfix/` - Bug fixes
- `docs/` - Documentation improvements
- `refactor/` - Code refactoring without behavior change
- `test/` - Adding or fixing tests

### 3. Make Changes

- Write clean, readable code following [PEP 8](https://pep8.org/)
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### 4. Test Your Changes

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run all tests with coverage
pytest --cov=src tests/
```

### 5. Lint and Type Check

```bash
# Format code with black
black src/ tests/

# Check style with flake8
flake8 src/ tests/

# Type check with mypy
mypy src/
```

### 6. Commit Changes

```bash
git add .
git commit -m "Type: Short description"
```

**Commit message format:**
- `Type:` prefix as per Conventional Commits
- Keep subject line under 72 characters
- Add detailed body if needed

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Formatting changes (white space, etc.)
- `refactor:` - Code restructuring
- `test:` - Adding/fixing tests
- `chore:` - Build/infra changes

Example:
```
feat: add support for Unity Catalog catalog names

- Update parameters.json to include catalog field
- Modify notebooks to use catalog.schema.table format
- Add configuration validation
```

### 7. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

---

## Pull Request Process

### 1. Create a Pull Request

Go to the original repository on GitHub and click "New Pull Request".

- Choose your fork and branch
- Write a clear title and description
- Link to related issues with `Closes #123` or `Fixes #123`

### 2. PR Template

Include in your PR description:

```
## Summary
Brief description of changes.

## Changes
- Change 1
- Change 2

## Testing
How you tested these changes (unit tests, manual testing, etc.)

## Screenshots
If UI/Power BI changes, include screenshots

## Checklist
- [x] Tests added/updated
- [x] Documentation updated
- [x] Code follows style guidelines
- [x] Self-review completed
```

### 3. Review Process

- Maintainers will review your code
- Be responsive to feedback
- Make requested changes and push to your branch
- All CI checks must pass (tests, lint, type check)

### 4. Merge

Once approved:
- A maintainer will merge your PR
- You can delete your feature branch

---

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use `black` for formatting (max line length 88)
- Use type hints for function signatures
- Write docstrings for all public functions/classes (Google style)

**Example:**
```python
def process_data(input_path: str, output_path: str) -> bool:
    """
    Process input data and write to output.

    Args:
        input_path: Path to input file
        output_path: Path for output file

    Returns:
        True if successful, False otherwise

    Raises:
        FileNotFoundError: If input file does not exist
    """
    # Implementation here
    pass
```

### Logging

- Use the standard `logging` module
- Log at appropriate levels:
  - `DEBUG` - Detailed debugging information
  - `INFO` - General progress messages
  - `WARNING` - Recoverable issues
  - `ERROR` - Failures
- Use logger from `utils.py`:
  ```python
  from utils import logger
  logger.info("Processing complete")
  ```

### Error Handling

- Catch specific exceptions, not bare `except:`
- Log errors with context
- Return sensible defaults on failure
- Use simulation mode for optional dependencies

**Avoid:**
```python
try:
    do_something()
except:  # Don't do this
    pass
```

**Prefer:**
```python
try:
    do_something()
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    return False
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

---

## Testing

### Test Structure

```
tests/
├── unit/              # Unit tests (no external dependencies)
│   ├── test_utils.py
│   └── test_data_generation.py
└── integration/       # Integration tests (may use Databricks mock/fixture)
    └── test_integration.py
```

### Writing Tests

- Place tests in `tests/unit/` or `tests/integration/`
- Name files `test_*.py`
- Use pytest fixtures for common setup
- Aim for >80% code coverage

**Example test:**
```python
# tests/unit/test_new_feature.py
import pytest
from src.new_module import new_function

def test_new_function_success():
    """Test happy path."""
    result = new_function("input")
    assert result == "expected"

def test_new_function_failure():
    """Test error handling."""
    with pytest.raises(ValueError):
        new_function(None)
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/unit/test_utils.py

# Run with verbose output
pytest -v tests/

# Run tests matching pattern
pytest -k "test_deploy"
```

### Simulation Mode

Tests should work without Databricks credentials:

- If `databricks-sdk` is not installed, functions operate in simulation mode
- Use mocking for external calls: `@patch('databricks.sdk.WorkspaceClient')`
- Don't require real cluster for CI/CD

---

## Documentation

### Types of Documentation

1. **README.md** - Project overview and quick start
2. **TASKS.md** - Project roadmap
3. **docs/** - Detailed guides:
   - `architecture.md` - System design
   - `deployment.md` - Deployment steps
   - `powerbi-setup.md` - Power BI configuration
   - `api-reference.md` - Python module APIs
   - `configuration.md` - Configuration options
   - `monitoring.md` - Operations and monitoring
   - `data-dictionary.md` - Data model reference

### Updating Documentation

- When adding features, update relevant docs
- Keep code examples up-to-date
- Add "See Also" links between related docs
- Document breaking changes in CHANGELOG (if exists)

### Docstring Style

Use Google-style docstrings:

```python
def function(param1: str, param2: int) -> bool:
    """Short description.

    Longer description if needed.

    Args:
        param1: Description
        param2: Description

    Returns:
        Description of return value

    Raises:
        ValueError: When something invalid
    """
```

---

## Issue Reporting

### Bug Reports

Use the GitHub issue template or include:

1. **Environment**:
   - OS, Python version
   - Databricks runtime version (if applicable)
   - Power BI version (if applicable)

2. **Steps to Reproduce**:
   - Clear, numbered steps
   - Expected vs actual behavior

3. **Additional Info**:
   - Error messages and stack traces
   - Relevant logs (from `logs/pipeline.log`)
   - Screenshots if UI-related

### Feature Requests

- Describe the problem you're solving
- Outline proposed solution
- Consider if it aligns with project goals
- Be open to feedback and alternatives

---

## Review Criteria

Contributions are evaluated on:

- ✅ **Functionality**: Does it work as intended?
- ✅ **Tests**: Adequate test coverage?
- ✅ **Documentation**: Are changes documented?
- ✅ **Performance**: Any negative performance impact?
- ✅ **Security**: No secrets in code, proper error handling?
- ✅ **Style**: Follows coding standards?
- ✅ **Backwards Compatibility**: Breaking changes documented and justified?

---

## Recognition

Contributors will be:
- Listed in README.md (major contributions)
- Credited in release notes
- Thanked in project communications

---

## Questions?

Open an issue or reach out to maintainers. Check existing documentation first:

- [README.md](README.md) - Project overview
- [TASKS.md](TASKS.md) - Current priorities
- [docs/](docs/) - Detailed guides

Happy contributing! 🚀
