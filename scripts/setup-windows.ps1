# Windows Setup Script for Book Knowledge AI
# Run this script as Administrator in PowerShell

Write-Host "===== Book Knowledge AI - Windows Setup ====="
Write-Host "This script will set up the development environment for Book Knowledge AI."

# Check Python version
try {
    $pythonVersion = python --version
    Write-Host "Found $pythonVersion"
} catch {
    Write-Host "Python not found. Please install Python 3.8 or higher."
    exit 1
}

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
} else {
    Write-Host "Virtual environment already exists."
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
& .\venv\Scripts\Activate.ps1

Write-Host "Setup complete!"
Write-Host "See windows-setup-guide.txt for next steps."