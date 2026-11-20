# Contributing to OpsPilot AI

Thank you for your interest in contributing!

## Development Setup

1. Clone the repository
2. Create a virtual environment
3. `pip install -r backend/requirements.txt`
4. `pip install pytest httpx`
5. Run tests: `pytest tests/`

## Pull Request Process

1. Create a feature branch
2. Ensure all tests pass
3. Add tests for new functionality
4. Update documentation if needed
5. Open a PR with a clear description

## Code Standards

- Follow deterministic safety patterns for any action that has real-world side effects
- All sensitive operations must have audit trails
- Prefer structured outputs and validation
- Keep human approval gates for financial or irreversible actions
