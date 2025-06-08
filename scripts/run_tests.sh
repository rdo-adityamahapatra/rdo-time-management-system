#!/usr/bin/env bash
set -e

echo "Running tests..."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run linting
echo "Running linting checks..."
flake8 src tests --max-line-length=120
black --check src tests
isort --check-only src tests
mypy src

# Run security checks
echo "Running security checks..."
bandit -r src

# Run tests with coverage
echo "Running tests..."
pytest --cov=src --cov-report=html --cov-report=term-missing

echo "All tests passed!"
