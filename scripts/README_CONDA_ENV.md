# Conda Environment Management for BookBrainWrangler

This directory contains scripts to manage Conda environments for the BookBrainWrangler project. These scripts provide a consistent interface for creating, activating, updating, and removing conda environments across different operating systems.

## Available Scripts

- **conda_env.ps1**: For Windows users (PowerShell)
- **conda_env.sh**: For Linux/macOS users (Bash)

## Prerequisites

- [Anaconda](https://www.anaconda.com/download/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) must be installed and available in your system's PATH.

### Installing Conda

1. Download and install Anaconda or Miniconda:
   - [Anaconda](https://www.anaconda.com/download/) (full distribution with many packages)
   - [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (minimal installation, recommended)

2. During installation:
   - Choose "Install for all users" or "Install for just me"
   - **Important**: Select the option to "Add Anaconda/Miniconda to my PATH environment variable"
   - Select the option to "Register Anaconda/Miniconda as my default Python"

3. After installation, verify conda is in your PATH:
   - Open a new terminal/PowerShell window
   - Run `conda --version`
   - If you get a version number, conda is correctly installed
   - If you get an error, conda is not in your PATH

### Adding Conda to PATH Manually

If conda is installed but not in your PATH:

#### Windows:
1. Search for "Environment Variables" in Start menu
2. Click "Edit the system environment variables"
3. Click "Environment Variables"
4. Under "User variables" or "System variables", find "Path" and click "Edit"
5. Add the following paths (replace `Username` with your username):
   ```
   C:\Users\Username\anaconda3
   C:\Users\Username\anaconda3\Scripts
   C:\Users\Username\anaconda3\Library\bin
   ```
   (Or similar paths for Miniconda)
6. Click OK and close all windows
7. Open a new PowerShell window and try again

#### Linux/macOS:
1. Add the following to your `~/.bashrc` or `~/.zshrc`:
   ```bash
   export PATH="$HOME/miniconda3/bin:$PATH"
   ```
   (Or similar path for Anaconda)
2. Run `source ~/.bashrc` or `source ~/.zshrc`
3. Try running `conda --version` again

## Windows Usage (PowerShell)

```powershell
# Create a new conda environment with default settings
.\conda_env.ps1 -Action create

# Create a conda environment with custom name and Python version
.\conda_env.ps1 -Action create -EnvName custom_env -PythonVersion 3.9

# Get activation instructions
.\conda_env.ps1 -Action activate

# Update an existing environment with the latest requirements
.\conda_env.ps1 -Action update

# Show information about the environment
.\conda_env.ps1 -Action info

# Remove an environment
.\conda_env.ps1 -Action remove
```

## Linux/macOS Usage (Bash)

First, make the script executable if needed:

```bash
chmod +x scripts/conda_env.sh
```

Then use the script:

```bash
# Create a new conda environment with default settings
./conda_env.sh create

# Create a conda environment with custom name and Python version
./conda_env.sh create custom_env 3.9

# Get activation instructions (or directly activate if sourced)
./conda_env.sh activate
# OR for direct activation (modifies current shell)
source ./conda_env.sh activate

# Update an existing environment with the latest requirements
./conda_env.sh update

# Show information about the environment
./conda_env.sh info

# Remove an environment
./conda_env.sh remove
```

## Default Settings

- **Environment Name**: bookbrainwrangler
- **Python Version**: 3.10

## Notes

- These scripts will install all dependencies listed in the project's `requirements.txt` file.
- The activation in PowerShell requires running the suggested command manually, as scripts cannot modify the parent environment in PowerShell.
- For the Bash script, you can use `source ./conda_env.sh activate` to directly activate the environment in your current shell.

## Troubleshooting

### "Conda is not installed or not in PATH"

If you see this error when running the script:
```
Conda is not installed or not in PATH. Please install Conda first.
```

Follow these steps:
1. Verify conda is installed by locating the Anaconda/Miniconda folder on your system
2. Make sure conda is in your PATH (see "Adding Conda to PATH Manually" above)
3. Try running the script in a new terminal/PowerShell window after updating the PATH

### Environment Creation Fails

If environment creation fails:
1. Check for any error messages in the output
2. Make sure you have internet connectivity for package downloads
3. Try creating the environment with fewer packages first:
   ```
   conda create -n bookbrainwrangler python=3.10 -y
   ```
4. Then install packages in smaller groups

### Packages Not Found

If certain packages can't be found:
1. Try installing them from different channels:
   ```
   conda install -n bookbrainwrangler -c conda-forge [package-name]
   ```
2. Or use pip within the conda environment:
   ```
   conda activate bookbrainwrangler
   pip install [package-name]
   ```
