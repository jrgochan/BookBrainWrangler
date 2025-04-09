<#
.SYNOPSIS
    Manage a conda environment for the BookBrainWrangler project.

.DESCRIPTION
    This script provides functions to create, activate, update, and remove
    a conda environment for the BookBrainWrangler project.

.PARAMETER Action
    The action to perform: create, activate, update, or remove.

.PARAMETER EnvName
    The name of the conda environment. Default is "bookbrainwrangler".

.PARAMETER PythonVersion
    The Python version to use. Default is "3.10".

.EXAMPLE
    .\conda_env.ps1 -Action create
    Create the conda environment with default settings.

.EXAMPLE
    .\conda_env.ps1 -Action activate
    Activate the conda environment.

.EXAMPLE
    .\conda_env.ps1 -Action update
    Update the conda environment with the latest requirements.

.EXAMPLE
    .\conda_env.ps1 -Action remove
    Remove the conda environment.

.EXAMPLE
    .\conda_env.ps1 -Action create -EnvName custom_env -PythonVersion 3.9
    Create a conda environment with custom name and Python version.
#>

param (
    [Parameter(Mandatory=$true)]
    [ValidateSet("create", "activate", "update", "remove", "info")]
    [string]$Action,
    
    [Parameter(Mandatory=$false)]
    [string]$EnvName = "bookbrainwrangler",
    
    [Parameter(Mandatory=$false)]
    [string]$PythonVersion = "3.10"
)

# Function to check if conda is installed
function Test-CondaInstalled {
    try {
        $condaInfo = conda info
        return $true
    } catch {
        Write-Host "Conda is not installed or not in PATH. Please install Conda first." -ForegroundColor Red
        return $false
    }
}

# Function to check if the environment exists
function Test-CondaEnvExists {
    param (
        [string]$EnvName
    )
    
    $envList = conda env list
    return $envList -match "\b$EnvName\b"
}

# Function to create the conda environment
function New-CondaEnvironment {
    param (
        [string]$EnvName,
        [string]$PythonVersion
    )
    
    if (Test-CondaEnvExists -EnvName $EnvName) {
        Write-Host "Environment '$EnvName' already exists. Use 'update' to update it." -ForegroundColor Yellow
        return
    }
    
    Write-Host "Creating conda environment '$EnvName' with Python $PythonVersion..." -ForegroundColor Cyan
    
    # Create the environment with Python
    conda create -n $EnvName python=$PythonVersion -y
    
    if (-not $?) {
        Write-Host "Failed to create conda environment." -ForegroundColor Red
        return
    }
    
    # Install requirements
    Write-Host "Installing requirements..." -ForegroundColor Cyan
    conda run -n $EnvName pip install -r (Join-Path (Get-Location) "requirements.txt")
    
    if ($?) {
        Write-Host "Conda environment '$EnvName' created successfully." -ForegroundColor Green
        Write-Host "To activate the environment, run: .\conda_env.ps1 -Action activate" -ForegroundColor Cyan
    } else {
        Write-Host "Failed to install requirements." -ForegroundColor Red
    }
}

# Function to activate the conda environment
function Enter-CondaEnvironment {
    param (
        [string]$EnvName
    )
    
    if (-not (Test-CondaEnvExists -EnvName $EnvName)) {
        Write-Host "Environment '$EnvName' does not exist. Create it first with 'create' action." -ForegroundColor Yellow
        return
    }
    
    Write-Host "Activating conda environment '$EnvName'..." -ForegroundColor Cyan
    Write-Host "Run the following command in your shell:" -ForegroundColor Green
    Write-Host "conda activate $EnvName" -ForegroundColor Yellow
    
    # Note: Direct activation doesn't work in scripts, so we instruct the user
    Write-Host "Note: You need to manually run this command as PowerShell scripts cannot modify the parent environment." -ForegroundColor Cyan
}

# Function to update the conda environment
function Update-CondaEnvironment {
    param (
        [string]$EnvName
    )
    
    if (-not (Test-CondaEnvExists -EnvName $EnvName)) {
        Write-Host "Environment '$EnvName' does not exist. Create it first with 'create' action." -ForegroundColor Yellow
        return
    }
    
    Write-Host "Updating conda environment '$EnvName'..." -ForegroundColor Cyan
    
    # Update Python packages from requirements.txt
    conda run -n $EnvName pip install -r (Join-Path (Get-Location) "requirements.txt") --upgrade
    
    if ($?) {
        Write-Host "Conda environment '$EnvName' updated successfully." -ForegroundColor Green
    } else {
        Write-Host "Failed to update environment." -ForegroundColor Red
    }
}

# Function to remove the conda environment
function Remove-CondaEnvironment {
    param (
        [string]$EnvName
    )
    
    if (-not (Test-CondaEnvExists -EnvName $EnvName)) {
        Write-Host "Environment '$EnvName' does not exist." -ForegroundColor Yellow
        return
    }
    
    Write-Host "Removing conda environment '$EnvName'..." -ForegroundColor Cyan
    
    $confirmation = Read-Host "Are you sure you want to remove the environment '$EnvName'? (y/n)"
    if ($confirmation -eq 'y') {
        conda env remove -n $EnvName -y
        
        if ($?) {
            Write-Host "Conda environment '$EnvName' removed successfully." -ForegroundColor Green
        } else {
            Write-Host "Failed to remove environment." -ForegroundColor Red
        }
    } else {
        Write-Host "Operation cancelled." -ForegroundColor Yellow
    }
}

# Function to show environment information
function Get-CondaEnvironmentInfo {
    param (
        [string]$EnvName
    )
    
    if (-not (Test-CondaEnvExists -EnvName $EnvName)) {
        Write-Host "Environment '$EnvName' does not exist." -ForegroundColor Yellow
        return
    }
    
    Write-Host "Information about conda environment '$EnvName':" -ForegroundColor Cyan
    conda env list | Select-String $EnvName
    Write-Host "`nInstalled packages:" -ForegroundColor Cyan
    conda run -n $EnvName pip list
}

# Main script execution
if (-not (Test-CondaInstalled)) {
    exit 1
}

switch ($Action) {
    "create" {
        New-CondaEnvironment -EnvName $EnvName -PythonVersion $PythonVersion
    }
    "activate" {
        Enter-CondaEnvironment -EnvName $EnvName
    }
    "update" {
        Update-CondaEnvironment -EnvName $EnvName
    }
    "remove" {
        Remove-CondaEnvironment -EnvName $EnvName
    }
    "info" {
        Get-CondaEnvironmentInfo -EnvName $EnvName
    }
}
