@echo off
:: run_all.bat
:: Runs the full fx_regime pipeline and deploys the brief.
:: Schedule this via Windows Task Scheduler at 17:30 NY (23:30 CET / next-day 05:00 IST)
:: to ensure latest.csv always reflects yesterday's close data.
::
:: Task Scheduler setup:
::   Action:  Start a program
::   Program: C:\Market Journey 2026\Code\fx_regime\run_all.bat
::   Start in: C:\Market Journey 2026\Code\fx_regime
::   Trigger: Daily at 17:30 (Eastern Time)

cd /d "%~dp0"

echo ============================================================
echo  G10 FX REGIME PIPELINE  --  %DATE% %TIME%
echo ============================================================

:: Activate virtual environment if present (adjust path as needed)
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [INFO] No venv found, using system Python
)

:: Run the full pipeline
python run_all.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Pipeline failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo.
echo ============================================================
echo  Pipeline complete  --  %DATE% %TIME%
echo ============================================================
