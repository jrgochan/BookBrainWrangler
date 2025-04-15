# Conda Activation Guide for BookBrainWrangler

This guide explains how to properly activate and use the conda environment for the BookBrainWrangler project, especially when encountering PATH issues.

## Understanding the Issue

The error `conda: The term 'conda' is not recognized...` occurs when:
1. Conda is installed but not in your system PATH
2. You're trying to use conda commands directly in PowerShell or Command Prompt

This is a common issue on Windows systems where conda was installed without adding it to the PATH environment variable.

## Solution: Using the Activation Scripts

Several scripts have been provided to work around PATH issues:

### Activation Scripts

1. **PowerShell Script**:
   ```powershell
   .\scripts\activate_bookbrainwrangler.ps1
   ```

2. **Batch Script** (for Command Prompt):
   ```
   scripts\activate_bookbrainwrangler.bat
   ```

These scripts use absolute paths to conda executables, so they work regardless of your PATH settings.

### Run Scripts (Activation + App Launch)

For a one-step solution that both activates the environment and runs the application:

1. **PowerShell Script**:
   ```powershell
   .\scripts\run_bookbrainwrangler.ps1
   ```

2. **Batch Script** (for Command Prompt):
   ```
   scripts\run_bookbrainwrangler.bat
   ```

## Permanent Fix: Adding Conda to PATH

### Automated Fix (Recommended)

Use the provided scripts to automatically add Conda to your PATH:

1. **PowerShell Script**:
   ```powershell
   .\scripts\fix_anaconda_path.ps1
   ```

2. **Batch Script** (for Command Prompt):
   ```
   scripts\fix_anaconda_path.bat
   ```

These scripts will:
- Check if Anaconda is installed at the expected location
- Add the necessary Conda paths to your user PATH
- Provide an option to add to system-wide PATH (requires running as Administrator)

### Manual Fix

If you prefer to manually add conda to your system PATH:

1. Search for "Environment Variables" in Start menu
2. Click "Edit the system environment variables"
3. Click "Environment Variables"
4. Under "User variables" or "System variables", find "Path" and click "Edit"
5. Add the following paths:
   ```
   C:\ProgramData\anaconda3
   C:\ProgramData\anaconda3\Scripts
   C:\ProgramData\anaconda3\Library\bin
   ```
6. Click OK and close all windows
7. Open a new PowerShell or Command Prompt window

After adding conda to your PATH, you should be able to use conda commands directly:
```
conda activate BookBrainWrangler
```

## Direct Environment Usage

If you prefer not to modify your PATH, you can directly use the Python executable from the conda environment:

```powershell
C:\ProgramData\anaconda3\envs\BookBrainWrangler\python.exe app.py
```

This bypasses the need for conda activation entirely.

## Notes

- The environment name is "BookBrainWrangler" (with uppercase 'B's)
- The Anaconda installation is located at C:\ProgramData\anaconda3
- These scripts assume these paths are correct - modify if your installation differs
