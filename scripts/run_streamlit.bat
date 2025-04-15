@echo off
rem Run the BookBrainWrangler application with Streamlit
rem This script handles both activation and running the Streamlit app correctly

set CONDA_ROOT=C:\ProgramData\anaconda3
set CONDA_SCRIPTS=%CONDA_ROOT%\Scripts
set ENV_PATH=%CONDA_ROOT%\envs\BookBrainWrangler
set PROJECT_ROOT=%~dp0..

echo Starting BookBrainWrangler Streamlit application...
echo Project root: %PROJECT_ROOT%

rem Activate the conda environment and run Streamlit properly
rem First method - direct executable (commented out as it's not working)
rem call "%CONDA_SCRIPTS%\activate.bat" "%ENV_PATH%" && "%ENV_PATH%\Scripts\streamlit.exe" run "%PROJECT_ROOT%\app.py"

rem Alternative command using Python module approach (more reliable)
call "%CONDA_SCRIPTS%\activate.bat" "%ENV_PATH%" && "%ENV_PATH%\python.exe" -m streamlit run "%PROJECT_ROOT%\app.py"
