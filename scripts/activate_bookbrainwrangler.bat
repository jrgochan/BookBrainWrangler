@echo off
rem Activate the BookBrainWrangler conda environment
rem This script uses absolute paths to ensure conda commands work correctly

set CONDA_ROOT=C:\ProgramData\anaconda3
set CONDA_SCRIPTS=%CONDA_ROOT%\Scripts
set ENV_PATH=%CONDA_ROOT%\envs\BookBrainWrangler

echo Activating BookBrainWrangler conda environment...
call "%CONDA_SCRIPTS%\activate.bat" "%ENV_PATH%"

echo.
echo Environment activated. You can now run the application.
echo Python Path: %ENV_PATH%\python.exe

echo.
echo To run the BookBrainWrangler app, use:
echo %ENV_PATH%\python.exe app.py

echo.
echo Python version in this environment:
"%ENV_PATH%\python.exe" --version
