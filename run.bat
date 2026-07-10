@echo off
rem MathOCR source launcher for Windows by Bouronikos Christos <chrisbouronikos@gmail.com>.
rem Support development: https://paypal.me/christosbouronikos
rem
rem Double-click this file to start MathOCR from source. It makes sure Python is
rem installed, then hands over to scripts\launch.py. End users of the packaged
rem app (MathOCR-Setup.exe) do NOT need this.

setlocal
cd /d "%~dp0"

rem Find an existing Python (the py launcher or python on PATH).
set "PY_CMD="
where py >nul 2>&1 && set "PY_CMD=py -3"
if not defined PY_CMD (
    where python >nul 2>&1 && set "PY_CMD=python"
)

if not defined PY_CMD (
    echo Python was not found. Installing Python 3.11...
    where winget >nul 2>&1
    if %errorlevel%==0 (
        winget install -e --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
        set "PY_CMD=py -3"
    ) else (
        echo Please install Python 3.11 from https://www.python.org/downloads/ and run this file again.
        pause
        exit /b 1
    )
)

echo Note: install Tesseract with the Greek "ell" language data
echo (https://github.com/UB-Mannheim/tesseract/wiki) to read page text.
echo Math recognition works without it.

%PY_CMD% scripts\launch.py %*
pause
