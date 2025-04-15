@echo off
REM Fix Anaconda PATH Environment Variable
REM Run this script as administrator for system-wide changes

echo Fixing Anaconda PATH Environment Variable...

REM Define conda paths to add
set CONDA_ROOT=C:\ProgramData\anaconda3
set CONDA_SCRIPTS=%CONDA_ROOT%\Scripts
set CONDA_LIBRARY_BIN=%CONDA_ROOT%\Library\bin

REM Check if Anaconda installation exists
if not exist "%CONDA_ROOT%" (
    echo Error: Anaconda installation not found at %CONDA_ROOT%
    echo Please update this script with the correct Anaconda installation path.
    exit /b 1
)

echo Checking Anaconda installation...
echo Found Anaconda at: %CONDA_ROOT%

REM Add Anaconda paths to PATH if not already present
echo.
echo Adding Anaconda paths to user PATH...

REM Get current PATH to check if paths are already included
set "OLD_PATH=%PATH%"

REM Create a temporary script to update PATH environment variable
echo @echo off > "%TEMP%\update_path.bat"
echo setx PATH "%%PATH%%;%CONDA_ROOT%;%CONDA_SCRIPTS%;%CONDA_LIBRARY_BIN%" >> "%TEMP%\update_path.bat"

REM Check if paths are already in PATH to avoid duplication
echo %PATH% | findstr /C:"%CONDA_ROOT%" > nul
if errorlevel 1 (
    echo Adding: %CONDA_ROOT%
) else (
    echo Already in PATH: %CONDA_ROOT%
)

echo %PATH% | findstr /C:"%CONDA_SCRIPTS%" > nul
if errorlevel 1 (
    echo Adding: %CONDA_SCRIPTS%
) else (
    echo Already in PATH: %CONDA_SCRIPTS%
)

echo %PATH% | findstr /C:"%CONDA_LIBRARY_BIN%" > nul
if errorlevel 1 (
    echo Adding: %CONDA_LIBRARY_BIN%
) else (
    echo Already in PATH: %CONDA_LIBRARY_BIN%
)

REM Execute the temporary script to update PATH
call "%TEMP%\update_path.bat"
del "%TEMP%\update_path.bat"

echo.
echo PATH environment variable updated successfully!
echo Please restart your command prompt windows for changes to take effect.

echo.
echo To verify conda is working, open a new command prompt and type:
echo conda --version

echo.
echo Script completed.
echo.
echo Would you like to add Anaconda to the system-wide PATH? (Y/N)
set /p RESPONSE=

if /i "%RESPONSE%"=="Y" (
    echo.
    echo To add Anaconda to the system-wide PATH, please run this script as Administrator.
    echo Right-click on this script and select "Run as administrator".
)

pause
