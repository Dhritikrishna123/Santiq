# Contributing to Santiq

Thank you for your interest in contributing to Santiq! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/Dhritikrishna123/Santiq
   cd santiq
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **pytest**: Testing

Run all checks:
```bash
black santiq tests
isort santiq tests
mypy santiq
pytest
```

## Testing

Write tests for all new functionality:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=santiq

# Run specific test file
pytest tests/test_core/test_engine.py
```

## Submitting Changes

1. Create a feature branch:

```bash
   git checkout -b feature/my-new-feature
   ```

2. Make your changes and add tests

3. Ensure all tests pass and code is formatted:

```bash
   black santiq tests
   isort santiq tests
   mypy santiq
   pytest
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "Add my new feature"
   ```

5. Push to your fork and create a pull request

## Plugin Development

See [Plugin Development Guide](docs/plugin-development.md) for detailed plugin development guidelines.

## Reporting Issues

When reporting issues, please include:
- Python version
- Santiq version
- Operating system
- Minimal reproduction case
- Full error traceback

## Community Guidelines

- Be respectful and inclusive
- Help others learn and grow
- Follow the code of conduct
- Document your contributions clearly

Thank you for contributing! 🚀
