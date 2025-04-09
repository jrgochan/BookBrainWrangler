# Fix Anaconda PATH Environment Variable
# Run this script as administrator for system-wide changes

# Define conda paths to add
$CONDA_ROOT = "C:\ProgramData\anaconda3"
$CONDA_SCRIPTS = "$CONDA_ROOT\Scripts"
$CONDA_LIBRARY_BIN = "$CONDA_ROOT\Library\bin"

$pathsToAdd = @(
    $CONDA_ROOT,
    $CONDA_SCRIPTS,
    $CONDA_LIBRARY_BIN
)

# Function to check if Anaconda installation exists at the specified path
function Test-AnacondaInstallation {
    $anacondaExists = Test-Path $CONDA_ROOT
    if (-not $anacondaExists) {
        Write-Host "Error: Anaconda installation not found at $CONDA_ROOT" -ForegroundColor Red
        Write-Host "Please update this script with the correct Anaconda installation path." -ForegroundColor Yellow
        exit 1
    }
}

# Function to check if a path is already in the PATH environment variable
function Test-PathInEnvironmentVariable {
    param (
        [string]$PathToCheck
    )
    
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    $pathsInEnv = $currentPath -split ";"
    
    foreach ($path in $pathsInEnv) {
        if ($path -eq $PathToCheck) {
            return $true
        }
    }
    
    return $false
}

# Main script execution
Write-Host "Checking Anaconda installation..." -ForegroundColor Cyan
Test-AnacondaInstallation

# Get current PATH
$currentUserPath = [Environment]::GetEnvironmentVariable("PATH", "User")

Write-Host "Current PATH:" -ForegroundColor Cyan
$currentUserPath -split ";" | ForEach-Object { Write-Host "  $_" }

# Add Anaconda paths to PATH if not already present
$pathsAdded = $false

foreach ($pathToAdd in $pathsToAdd) {
    if (Test-Path $pathToAdd) {
        if (-not (Test-PathInEnvironmentVariable $pathToAdd)) {
            $currentUserPath = "$currentUserPath;$pathToAdd"
            $pathsAdded = $true
            Write-Host "Adding to PATH: $pathToAdd" -ForegroundColor Green
        } else {
            Write-Host "Already in PATH: $pathToAdd" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Path does not exist: $pathToAdd" -ForegroundColor Red
    }
}

if ($pathsAdded) {
    # Update the PATH environment variable
    [Environment]::SetEnvironmentVariable("PATH", $currentUserPath, "User")
    Write-Host "`nPATH environment variable updated successfully!" -ForegroundColor Green
    Write-Host "Please restart your PowerShell/CMD windows for changes to take effect." -ForegroundColor Cyan
} else {
    Write-Host "`nNo changes needed. All required paths are already in your PATH environment variable." -ForegroundColor Cyan
}

# Display verification instructions
Write-Host "`nTo verify conda is working, open a new PowerShell window and type:" -ForegroundColor Cyan
Write-Host "conda --version" -ForegroundColor Yellow

# Offer to create a system-wide PATH update
$response = Read-Host "`nWould you like to add Anaconda to the system-wide PATH? (Y/N)"
if ($response -eq "Y" -or $response -eq "y") {
    # Check if running as administrator
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
    
    if ($isAdmin) {
        $currentSystemPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
        $pathsAdded = $false
        
        foreach ($pathToAdd in $pathsToAdd) {
            if ((Test-Path $pathToAdd) -and ($currentSystemPath -notlike "*$pathToAdd*")) {
                $currentSystemPath = "$currentSystemPath;$pathToAdd"
                $pathsAdded = $true
                Write-Host "Adding to system PATH: $pathToAdd" -ForegroundColor Green
            }
        }
        
        if ($pathsAdded) {
            [Environment]::SetEnvironmentVariable("PATH", $currentSystemPath, "Machine")
            Write-Host "System PATH updated successfully!" -ForegroundColor Green
        } else {
            Write-Host "No changes needed for system PATH." -ForegroundColor Cyan
        }
    } else {
        Write-Host "This script must be run as Administrator to modify system PATH." -ForegroundColor Red
        Write-Host "Please re-run this script as Administrator if you want to update system PATH." -ForegroundColor Yellow
    }
}

Write-Host "`nScript completed." -ForegroundColor Green
