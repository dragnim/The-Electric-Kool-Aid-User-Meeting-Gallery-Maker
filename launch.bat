@echo off
setlocal

echo The Electric Kool-Aid User Meeting Gallery Maker
echo =================================================

:: Try py launcher first (recommended), then python
set PYTHON=
where py >nul 2>&1 && set PYTHON=py
if "%PYTHON%"=="" where python >nul 2>&1 && set PYTHON=python
if "%PYTHON%"=="" (
    echo.
    echo ERROR: Python not found.
    echo Please install Python 3.12 or later from https://python.org
    echo Make sure to tick "Add Python to PATH" during install.
    pause
    exit /b 1
)

:: Check version is 3.12+
%PYTHON% -c "import sys; exit(0 if sys.version_info >= (3,12) else 1)" 2>nul
if errorlevel 1 (
    echo.
    echo ERROR: Python 3.12 or later is required.
    echo Your version:
    %PYTHON% --version
    pause
    exit /b 1
)

:: Install / upgrade Pillow silently
echo Checking dependencies...
%PYTHON% -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo.
    echo WARNING: Dependency install failed. The app may not work correctly.
    pause
)

:: Launch the app
%PYTHON% the-electric-kool-aid-user-meeting-gallery-maker.py
