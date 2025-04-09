@echo off
rem Update the BookBrainWrangler conda environment with all required packages
rem This script uses absolute paths to ensure conda commands work correctly

set CONDA_ROOT=C:\ProgramData\anaconda3
set CONDA_SCRIPTS=%CONDA_ROOT%\Scripts
set ENV_PATH=%CONDA_ROOT%\envs\BookBrainWrangler
set PROJECT_ROOT=%~dp0..

echo Updating BookBrainWrangler conda environment...
echo Project root: %PROJECT_ROOT%

rem Activate the conda environment using absolute paths first
call "%CONDA_SCRIPTS%\activate.bat" "%ENV_PATH%"

rem Install core dependencies that were missing in the error messages
echo.
echo Installing core dependencies...
"%ENV_PATH%\python.exe" -m pip install colorama decorator pygments --no-warn-script-location

rem Install all requirements from requirements.txt
echo.
echo Installing/updating requirements from requirements.txt...
"%ENV_PATH%\python.exe" -m pip install -r "%PROJECT_ROOT%\requirements.txt" --no-warn-script-location

echo.
echo Environment update completed.
echo To activate the environment, run: scripts\activate_bookbrainwrangler.bat
echo To run the application, run: scripts\run_bookbrainwrangler.bat
