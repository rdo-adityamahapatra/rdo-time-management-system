#!/usr/bin/env bash
set -e

echo "Setting up RDO Time Management System development environment..."

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry is not installed. Please install Poetry first:"
    echo "curl -sSL https://install.python-poetry.org | python3 -"
    echo "or visit: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Install dependencies using Poetry
echo "Installing dependencies with Poetry..."
poetry install

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
poetry run pre-commit install
poetry run pre-commit install --hook-type commit-msg

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from .env.example"
else
    echo ".env file already exists, skipping..."
fi

echo "Setup complete! Your Poetry virtual environment is ready."
echo ""
echo "You can now run:"
echo "  - poetry run pre-commit run --all-files  # Run all pre-commit hooks"
echo "  - poetry run pytest                      # Run tests"
echo "  - ./scripts/run_tests.sh                 # Run tests with coverage"
echo "  - docker-compose up --build              # Start with Docker"
echo ""
echo "To activate the Poetry shell:"
echo "  poetry shell"
