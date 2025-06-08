#!/usr/bin/env bash
set -e

echo "Setting up development environment..."

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type commit-msg

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from .env.example"
else
    echo ".env file already exists, skipping..."
fi

echo "Setup complete! Don't forget to activate your virtual environment:"
echo "source venv/bin/activate"
echo ""
echo "You can now run:"
echo "  - pre-commit run --all-files  # Run all pre-commit hooks"
echo "  - ./scripts/run_tests.sh      # Run tests"
echo "  - docker-compose up --build   # Start with Docker"
