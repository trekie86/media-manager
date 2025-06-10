#!/bin/bash

# Ensure script fails on any error
set -e

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Update pip and tools
echo "Updating pip and tools..."
uv pip install --upgrade pip

# Compile requirements
echo "Compiling requirements..."
uv pip compile requirements.in -o requirements.txt
uv pip compile requirements-dev.in -o requirements-dev.txt

# Install dependencies
echo "Installing dependencies..."
uv pip install -r requirements-dev.txt

echo "✨ Development environment setup complete! ✨"
echo ""
echo "To activate the virtual environment in new terminals, run:"
echo "source .venv/bin/activate"
echo ""
echo "To deactivate, simply run:"
echo "deactivate"
