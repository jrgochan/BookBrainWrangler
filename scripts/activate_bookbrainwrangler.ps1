# Activate the BookBrainWrangler conda environment
# This script uses absolute paths to ensure conda commands work correctly

# Define conda paths
$CONDA_ROOT = "C:\ProgramData\anaconda3"
$CONDA_SCRIPTS = "$CONDA_ROOT\Scripts"
$ENV_PATH = "$CONDA_ROOT\envs\BookBrainWrangler"

Write-Host "Activating BookBrainWrangler conda environment..." -ForegroundColor Cyan

# Activate the conda environment using absolute paths
& "$CONDA_SCRIPTS\activate.bat" "$ENV_PATH"

Write-Host "`nEnvironment activated. You can now run the application." -ForegroundColor Green
Write-Host "Python Path: $ENV_PATH\python.exe" -ForegroundColor Yellow

# Display a reminder about how to run the app
Write-Host "`nTo run the BookBrainWrangler app, use:" -ForegroundColor Cyan
Write-Host "$ENV_PATH\python.exe app.py" -ForegroundColor Yellow

# To check if the environment is properly activated
Write-Host "`nPython version in this environment:" -ForegroundColor Cyan
& "$ENV_PATH\python.exe" --version
