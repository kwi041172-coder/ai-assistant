@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    py -m venv .venv
    if errorlevel 1 (
        echo Failed to create the Python virtual environment.
        exit /b 1
    )
)

if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env" >nul
    echo Created backend\.env. Add your OpenAI API key, then run run.bat again.
    exit /b 1
)

"%PYTHON%" -m pip install -r backend\requirements.txt
if errorlevel 1 (
    echo Backend dependency installation failed.
    exit /b 1
)

"%PYTHON%" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
exit /b %errorlevel%
