# Update the BookBrainWrangler conda environment with all required packages
# This script uses absolute paths to ensure conda commands work correctly

# Define conda paths
$CONDA_ROOT = "C:\ProgramData\anaconda3"
$CONDA_SCRIPTS = "$CONDA_ROOT\Scripts"
$ENV_PATH = "$CONDA_ROOT\envs\BookBrainWrangler"
$PROJECT_ROOT = $PSScriptRoot | Split-Path -Parent

Write-Host "Updating BookBrainWrangler conda environment..." -ForegroundColor Cyan
Write-Host "Project root: $PROJECT_ROOT" -ForegroundColor Yellow

# Activate the conda environment using absolute paths first
& "$CONDA_SCRIPTS\activate.bat" "$ENV_PATH"

# Install core dependencies that were missing in the error messages
Write-Host "`nInstalling core dependencies..." -ForegroundColor Cyan
& "$ENV_PATH\python.exe" -m pip install colorama decorator pygments --no-warn-script-location

# Install all requirements from requirements.txt
Write-Host "`nInstalling/updating requirements from requirements.txt..." -ForegroundColor Cyan
& "$ENV_PATH\python.exe" -m pip install -r "$PROJECT_ROOT\requirements.txt" --no-warn-script-location

Write-Host "`nEnvironment update completed." -ForegroundColor Green
Write-Host "To activate the environment, run: .\scripts\activate_bookbrainwrangler.ps1" -ForegroundColor Yellow
Write-Host "To run the application, run: .\scripts\run_bookbrainwrangler.ps1" -ForegroundColor Yellow
