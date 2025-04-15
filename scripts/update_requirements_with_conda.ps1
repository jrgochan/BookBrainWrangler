# Update requirements.txt using conda to ensure latest compatible versions
# This script identifies packages in requirements.txt and updates them with conda-compatible versions

# Define conda paths
$CONDA_ROOT = "C:\ProgramData\anaconda3"
$CONDA_SCRIPTS = "$CONDA_ROOT\Scripts"
$ENV_PATH = "$CONDA_ROOT\envs\BookBrainWrangler"
$PROJECT_ROOT = $PSScriptRoot | Split-Path -Parent

Write-Host "Updating requirements.txt with latest conda-compatible versions..." -ForegroundColor Cyan
Write-Host "Project root: $PROJECT_ROOT" -ForegroundColor Yellow

# Create a temporary directory for the process
$TempDir = Join-Path $env:TEMP "requirements_update"
if (Test-Path $TempDir) {
    Remove-Item -Path $TempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $TempDir | Out-Null

# Copy the current requirements to a temporary file for processing
$CurrentRequirements = Join-Path $PROJECT_ROOT "requirements.txt"
$TempRequirements = Join-Path $TempDir "current_requirements.txt"
Copy-Item -Path $CurrentRequirements -Destination $TempRequirements

# Read the current requirements, ignoring comments and empty lines
$Packages = @()
Get-Content $TempRequirements | ForEach-Object {
    $Line = $_.Trim()
    if ($Line -and -not $Line.StartsWith("#")) {
        # Extract package name by splitting on any version specifier
        $PackageName = $Line -split '[=<>~!]' | Select-Object -First 1
        $Packages += $PackageName.Trim()
    }
}

# Activate the conda environment using absolute paths
Write-Host "`nActivating conda environment..." -ForegroundColor Cyan
& "$CONDA_SCRIPTS\activate.bat" "$ENV_PATH"

# Create a new requirements.txt file with updated versions
$UpdatedRequirements = Join-Path $TempDir "updated_requirements.txt"
Set-Content -Path $UpdatedRequirements -Value "# Updated requirements $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"

# Categories from the original requirements file
Add-Content -Path $UpdatedRequirements -Value "# Core requirements"

# Process each package to find the latest compatible version
foreach ($Package in $Packages) {
    Write-Host "Checking latest compatible version for: $Package" -ForegroundColor Yellow
    
    try {
        # Use conda to get package info
        $CondaInfo = & "$CONDA_ROOT\Scripts\conda.exe" search $Package --json | ConvertFrom-Json
        
        if ($CondaInfo.error) {
            Write-Host "  - Error from conda for $Package. Using pip to check version." -ForegroundColor Red
            $PipInfo = & "$ENV_PATH\python.exe" -m pip show $Package 2>$null
            
            if ($PipInfo) {
                $VersionLine = ($PipInfo | Select-String "Version:") -split ":" | Select-Object -Last 1
                $LatestVersion = $VersionLine.Trim()
                Write-Host "  - Found pip version: $LatestVersion" -ForegroundColor Green
                Add-Content -Path $UpdatedRequirements -Value "$Package>=$LatestVersion"
            } else {
                Write-Host "  - Package not found with pip. Keeping original specification." -ForegroundColor Yellow
                # Extract original line from requirements.txt
                $OriginalLine = Get-Content $TempRequirements | Where-Object { $_ -match "^$Package" } | Select-Object -First 1
                if ($OriginalLine) {
                    Add-Content -Path $UpdatedRequirements -Value $OriginalLine
                } else {
                    Add-Content -Path $UpdatedRequirements -Value "$Package"
                }
            }
        } else {
            # Get the latest version from conda
            $LatestPackage = $CondaInfo | Where-Object { $_.name -eq $Package } | 
                            Sort-Object -Property {[version]::new($_.version)} -Descending | 
                            Select-Object -First 1
            
            if ($LatestPackage) {
                $LatestVersion = $LatestPackage.version
                Write-Host "  - Found conda version: $LatestVersion" -ForegroundColor Green
                Add-Content -Path $UpdatedRequirements -Value "$Package>=$LatestVersion"
            } else {
                Write-Host "  - No conda version found. Checking pip..." -ForegroundColor Yellow
                $PipInfo = & "$ENV_PATH\python.exe" -m pip show $Package 2>$null
                
                if ($PipInfo) {
                    $VersionLine = ($PipInfo | Select-String "Version:") -split ":" | Select-Object -Last 1
                    $LatestVersion = $VersionLine.Trim()
                    Write-Host "  - Found pip version: $LatestVersion" -ForegroundColor Green
                    Add-Content -Path $UpdatedRequirements -Value "$Package>=$LatestVersion"
                } else {
                    Write-Host "  - Package not found. Keeping original specification." -ForegroundColor Yellow
                    # Extract original line from requirements.txt
                    $OriginalLine = Get-Content $TempRequirements | Where-Object { $_ -match "^$Package" } | Select-Object -First 1
                    if ($OriginalLine) {
                        Add-Content -Path $UpdatedRequirements -Value $OriginalLine
                    } else {
                        Add-Content -Path $UpdatedRequirements -Value "$Package"
                    }
                }
            }
        }
    } catch {
        Write-Host "  - Error processing package $Package. Keeping original specification." -ForegroundColor Red
        Write-Host "    $_" -ForegroundColor Red
        # Extract original line from requirements.txt
        $OriginalLine = Get-Content $TempRequirements | Where-Object { $_ -match "^$Package" } | Select-Object -First 1
        if ($OriginalLine) {
            Add-Content -Path $UpdatedRequirements -Value $OriginalLine
        } else {
            Add-Content -Path $UpdatedRequirements -Value "$Package"
        }
    }
}

# Add any important comments or categorization from the original file
Add-Content -Path $UpdatedRequirements -Value "`n# Specific package constraints"
Add-Content -Path $UpdatedRequirements -Value "chromadb==0.4.18  # Specific version to avoid conflicts"
Add-Content -Path $UpdatedRequirements -Value "langchain-chroma==0.1.4  # Compatible with chromadb 0.4.18"

# Ensure backward compatibility by preserving any explicit version constraints
Write-Host "`nPreserving explicit version constraints..." -ForegroundColor Cyan
$ExplicitConstraints = Get-Content $TempRequirements | Where-Object { $_ -match "==\d" }
foreach ($Constraint in $ExplicitConstraints) {
    $PackageName = ($Constraint -split '==')[0].Trim()
    # Only add if it's not the preserved chromadb or langchain-chroma
    if ($PackageName -ne "chromadb" -and $PackageName -ne "langchain-chroma") {
        # Check if already added to updated requirements
        $AlreadyAdded = Get-Content $UpdatedRequirements | Where-Object { $_ -match "^$PackageName" }
        if (-not $AlreadyAdded) {
            Add-Content -Path $UpdatedRequirements -Value $Constraint
        }
    }
}

# Copy the updated requirements back to the project
Write-Host "`nUpdating requirements.txt with new versions..." -ForegroundColor Cyan
Copy-Item -Path $UpdatedRequirements -Destination $CurrentRequirements -Force

# Clean up
Remove-Item -Path $TempDir -Recurse -Force

Write-Host "`nrequirements.txt has been updated with the latest compatible versions!" -ForegroundColor Green
Write-Host "You can now update your conda environment with:" -ForegroundColor Yellow
Write-Host "  .\scripts\update_bookbrainwrangler_env.ps1" -ForegroundColor Yellow
