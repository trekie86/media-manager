#!/bin/bash

# Ensure script fails on any error
set -e

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Copy .env file from parent directory if it exists
if [ -f "../.env" ]; then
    echo "Copying .env file from parent directory..."
    cp "../.env" .
    echo "Note: If you update the parent .env file, you'll need to:"
    echo "  1. Either copy it manually to the backend folder"
    echo "  2. Or run this setup script again"
else
    echo "Warning: No .env file found in parent directory"
    echo "Please ensure you copy .env.example to .env and configure it"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
else
    echo "Virtual environment already exists"
fi

# Update pip and tools (within the virtual environment)
echo "Installing dependencies..."
.venv/bin/python -m pip install --upgrade pip
echo "Updating pip and tools..."
uv pip install --upgrade pip

# Compile requirements (within the virtual environment)
echo "Compiling requirements..."
uv pip compile requirements.in -o requirements.txt
uv pip compile requirements-dev.in -o requirements-dev.txt

# Install dependencies (within the virtual environment)
echo "Installing dependencies..."
uv pip install -r requirements-dev.txt

echo "✨ Development environment setup complete! ✨"
echo ""
echo "IMPORTANT: You need to activate the virtual environment to use it:"
echo "    source .venv/bin/activate"
echo ""
echo "After activation, you can:"
echo "1. Start the development server:"
echo "    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2. Or deactivate the environment when done:"
echo "    deactivate"
