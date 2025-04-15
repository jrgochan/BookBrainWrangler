$source = Get-Location
$staging = Join-Path $env:TEMP "project_staging_$(Get-Random)"
$zipPath = Join-Path $source "project.zip"

# Create a clean staging area
New-Item -ItemType Directory -Path $staging | Out-Null

# Copy files, excluding directories
robocopy $source $staging /E /XD .git .venv .cache __pycache__ models--sentence-transformers--all-MiniLM-L6-v2 /XF *.pyc *.pyo *.egg-info /NFL /NDL /NJH /NJS /NC /NS /NP

# Remove existing zip if present
if (Test-Path $zipPath) { Remove-Item $zipPath }

# Zip it
Compress-Archive -Path "$staging\*" -DestinationPath $zipPath

# Cleanup
Remove-Item -Recurse -Force $staging

Write-Host "✅ Project zipped to $zipPath"
