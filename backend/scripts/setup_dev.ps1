# Ensure script stops on error
$ErrorActionPreference = "Stop"

# Check if uv is installed
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv is not installed. Installing..."
    iwr -useb https://astral.sh/uv/install.ps1 | iex
}

# Copy .env file from parent directory if it exists
if (Test-Path "../.env") {
    Write-Host "Copying .env file from parent directory..."
    Copy-Item "../.env" .
    Write-Host "Note: If you update the parent .env file, you'll need to:"
    Write-Host "  1. Either copy it manually to the backend folder"
    Write-Host "  2. Or run this setup script again"
}
else {
    Write-Host "Warning: No .env file found in parent directory"
    Write-Host "Please ensure you copy .env.example to .env and configure it"
}

# Create virtual environment if it doesn't exist
if (!(Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    uv venv
}
else {
    Write-Host "Virtual environment already exists"
}

# Update pip and tools (within the virtual environment)
Write-Host "Installing dependencies..."
.\.venv\Scripts\python.exe -m pip install --upgrade pip

# Compile requirements (within the virtual environment)
Write-Host "Compiling requirements..."
uv.exe pip compile requirements.in -o requirements.txt
uv.exe pip compile requirements-dev.in -o requirements-dev.txt

# Install dependencies (within the virtual environment)
Write-Host "Installing dependencies..."
uv.exe pip install -r requirements-dev.txt

Write-Host "`n✨ Development environment setup complete! ✨"
Write-Host ""
Write-Host "IMPORTANT: You need to activate the virtual environment to use it:"
Write-Host "    .\.venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "After activation, you can:"
Write-Host "1. Start the development server:"
Write-Host "    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Write-Host ""
Write-Host "2. Or deactivate the environment when done:"
Write-Host "    deactivate"
