# Ensure script stops on error
$ErrorActionPreference = "Stop"

# Check if uv is installed
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv is not installed. Installing..."
    iwr -useb https://astral.sh/uv/install.ps1 | iex
}

# Create virtual environment if it doesn't exist
if (!(Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    uv venv
}
else {
    Write-Host "Virtual environment already exists"
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
.\.venv\Scripts\Activate.ps1

# Update pip and tools
Write-Host "Updating pip and tools..."
uv pip install --upgrade pip

# Compile requirements
Write-Host "Compiling requirements..."
uv pip compile requirements.in -o requirements.txt
uv pip compile requirements-dev.in -o requirements-dev.txt

# Install dependencies
Write-Host "Installing dependencies..."
uv pip install -r requirements-dev.txt

Write-Host "`n✨ Development environment setup complete! ✨"
Write-Host ""
Write-Host "To activate the virtual environment in new terminals, run:"
Write-Host ".\.venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "To deactivate, simply run:"
Write-Host "deactivate"
