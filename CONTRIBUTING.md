# Contributing to Barcode Central

Thank you for your interest in contributing to Barcode Central! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, gender, gender identity and expression, sexual orientation, disability, personal appearance, body size, race, ethnicity, age, religion, or nationality.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Harassment, trolling, or discriminatory comments
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Basic understanding of Flask and web development
- Familiarity with ZPL (Zebra Programming Language) is helpful

### Setting Up Development Environment

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/yourusername/barcode-central.git
   cd barcode-central
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Run tests**
   ```bash
   ./run_tests.sh
   ```

## Development Process

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Workflow

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following our coding standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   ./run_tests.sh
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Go to GitHub and create a PR
   - Fill out the PR template
   - Link any related issues

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- **Line length**: 100 characters (not 79)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Single quotes for strings, double quotes for docstrings
- **Imports**: Grouped and sorted (standard library, third-party, local)

### Code Organization

```python
"""
Module docstring explaining purpose
"""
import standard_library
import third_party

from local_module import something

# Constants
CONSTANT_NAME = 'value'

# Classes
class MyClass:
    """Class docstring"""
    
    def __init__(self):
        """Constructor docstring"""
        pass
    
    def method(self):
        """Method docstring"""
        pass

# Functions
def my_function():
    """Function docstring"""
    pass
```

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is invalid
    """
    pass
```

### Naming Conventions

- **Variables**: `snake_case`
- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

### Error Handling

```python
try:
    # Risky operation
    result = do_something()
except SpecificException as e:
    logger.error(f"Error doing something: {e}")
    # Handle error appropriately
    return False, str(e)
```

## Testing Requirements

### Test Coverage

- Aim for >80% code coverage
- All new features must include tests
- Bug fixes should include regression tests

### Test Types

1. **Unit Tests** - Test individual functions/methods
2. **API Tests** - Test API endpoints
3. **Integration Tests** - Test complete workflows

### Writing Tests

```python
import pytest

class TestFeature:
    """Tests for feature"""
    
    def test_success_case(self):
        """Test successful operation"""
        result = my_function('valid_input')
        assert result is True
    
    def test_error_case(self):
        """Test error handling"""
        with pytest.raises(ValueError):
            my_function('invalid_input')
```

### Running Tests

```bash
# Run all tests
./run_tests.sh

# Run specific test file
pytest tests/test_specific.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_file.py::TestClass::test_method
```

## Documentation

### Code Documentation

- All modules, classes, and functions must have docstrings
- Complex logic should have inline comments
- Use type hints where appropriate

### User Documentation

When adding features, update:
- `API.md` - API endpoint documentation
- `USER_GUIDE.md` - User-facing instructions
- `DEVELOPER_GUIDE.md` - Developer information
- `README.md` - If it affects setup or usage

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(templates): add template validation endpoint

Add new endpoint to validate ZPL template syntax before saving.
Includes validation for both ZPL structure and Jinja2 syntax.

Closes #123
```

```
fix(printer): handle connection timeout gracefully

Previously, connection timeouts would crash the application.
Now they return a proper error message to the user.

Fixes #456
```

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages follow conventions
- [ ] No merge conflicts with main branch

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Code follows style guide
```

### Review Process

1. Automated tests must pass
2. At least one maintainer review required
3. All review comments must be addressed
4. PR must be up to date with main branch

### After Approval

- Maintainer will merge using "Squash and merge"
- Delete your feature branch after merge

## Reporting Bugs

### Before Reporting

1. Check existing issues
2. Try latest version
3. Gather relevant information

### Bug Report Template

```markdown
**Description**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.9.5]
- Barcode Central version: [e.g., 1.0.0]

**Additional Context**
Screenshots, logs, etc.
```

## Suggesting Features

### Feature Request Template

```markdown
**Problem Statement**
What problem does this solve?

**Proposed Solution**
How should it work?

**Alternatives Considered**
Other approaches you've thought about

**Additional Context**
Mockups, examples, etc.
```

## Development Tips

### Debugging

```python
# Use logging instead of print
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

### Testing Locally

```bash
# Run in development mode
export FLASK_DEBUG=1
python app.py

# Test with Docker
docker-compose up --build

# Check logs
tail -f logs/app.log
```

### Common Issues

**Import errors:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**Test failures:**
```bash
# Clear cache and rerun
pytest --cache-clear
```

## Questions?

- Check [Developer Guide](DEVELOPER_GUIDE.md)
- Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- Open a discussion on GitHub
- Contact maintainers

## Recognition

Contributors will be recognized in:
- `CONTRIBUTORS.md` file
- Release notes
- Project README

Thank you for contributing to Barcode Central! 🎉