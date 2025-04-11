# PowerShell script to run Ollama integration tests

# Parse arguments
param(
    [string]$hostName = "",
    [string]$port = "",
    [string]$model = "llama2",
    [string]$test = "all",
    [switch]$wait = $false,
    [switch]$verbose = $false,
    [switch]$help = $false
)

# Find the project root directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Get-Item $scriptDir).Parent.Parent.FullName

# Add the project root to PYTHONPATH
$env:PYTHONPATH = "$projectRoot;$env:PYTHONPATH"

# Show help if requested
if ($help) {
    Write-Host "Usage: .\run_tests.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -host HOST       Ollama server host (default: localhost or OLLAMA_HOST env var)"
    Write-Host "  -port PORT       Ollama server port (default: 11434 or OLLAMA_PORT env var)"
    Write-Host "  -model MODEL     Model to test (default: llama2)"
    Write-Host "  -test TEST       Which tests to run (all, connectivity, models, generation, embeddings)"
    Write-Host "  -wait            Wait for Ollama server to become available"
    Write-Host "  -verbose         Enable verbose output"
    Write-Host "  -help            Show this help message"
    exit 0
}

# Build the command
$cmd = "python $scriptDir\test_ollama.py"

if ($hostName -ne "") {
    $cmd = "$cmd --host $hostName"
}

if ($port -ne "") {
    $cmd = "$cmd --port $port"
}

if ($model -ne "") {
    $cmd = "$cmd --model $model"
}

if ($test -ne "") {
    $cmd = "$cmd --test $test"
}

if ($wait) {
    $cmd = "$cmd --wait-for-server"
}

if ($verbose) {
    $cmd = "$cmd --verbose"
}

# Run the tests
Write-Host "Running Ollama tests..."
Write-Host "Command: $cmd"
Write-Host ""

# Execute the command
Invoke-Expression $cmd

# Get the exit code
$exitCode = $LASTEXITCODE

# Exit with the same code
exit $exitCode
