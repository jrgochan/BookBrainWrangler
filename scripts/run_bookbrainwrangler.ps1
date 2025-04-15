# Run the BookBrainWrangler application with Streamlit
# This script handles both activation and running the Streamlit app correctly

# Define conda paths
$CONDA_ROOT = "C:\ProgramData\anaconda3"
$CONDA_SCRIPTS = "$CONDA_ROOT\Scripts"
$ENV_PATH = "$CONDA_ROOT\envs\BookBrainWrangler"
$PROJECT_ROOT = $PSScriptRoot | Split-Path -Parent

Write-Host "Starting BookBrainWrangler application with Streamlit..." -ForegroundColor Cyan
Write-Host "Project root: $PROJECT_ROOT" -ForegroundColor Yellow

# Activate the conda environment and run Streamlit properly
& "$CONDA_SCRIPTS\activate.bat" "$ENV_PATH"
& "$ENV_PATH\python.exe" -m streamlit run "$PROJECT_ROOT\app.py"
