::[Bat To Exe Converter]
::
::YAwzoRdxOk+EWAjk
::fBw5plQjdCyDJF6N4EolKidZWAODAGK5CbsP1O6r7ejU8HIfU689dI7Y0fqHI+9z
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSzk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSTk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+JeA==
::cxY6rQJ7JhzQF1fEqQJQ
::ZQ05rAF9IBncCkqN+0xwdVs0
::ZQ05rAF9IAHYFVzEqQJQ
::eg0/rx1wNQPfEVWB+kM9LVsJDGQ=
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCyDJF6N4EolKidZWAODAEaOIZQjz93S0P6CsVlMGucnfe8=
::YB416Ek+ZW8=
::
::
::978f952a14a936cc963da21a135fa983
@echo off
chcp 65001
setlocal enabledelayedexpansion

:: Check administrator privileges and auto-elevate
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Administrator privileges required, auto-elevating...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Set window title
title MTGA GUI Launcher (Administrator)

:: Set console color
color 0A

:: Get current script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo uv not installed, starting automatic installation...
    echo Installing uv via PowerShell, please wait...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if %ERRORLEVEL% neq 0 (
        echo uv installation failed, error code: %ERRORLEVEL%
        pause
        exit /b 1
    )
    echo uv installation successful!
    
    :: Refresh environment variables
    call refreshenv >nul 2>nul
    
    :: Check if uv is available again
    where uv >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo Warning: uv still not found after installation, please restart command prompt
        echo or manually add uv to PATH environment variable
        pause
        exit /b 1
    )
)

echo uv detected and ready

:: Set Python virtual environment paths
set "VENV_DIR=%SCRIPT_DIR%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"

:: Set OpenSSL path
set "OPENSSL_DIR=%SCRIPT_DIR%\openssl"

:: Check if virtual environment exists
if not exist "%VENV_PYTHON%" (
    echo Virtual environment does not exist, creating...
    
    :: Switch to script directory
    cd /d "%SCRIPT_DIR%"
    
    :: Install Python 3.13 using uv
    echo Installing Python 3.13...
    uv python install 3.13
    if %ERRORLEVEL% neq 0 (
        echo Python 3.13 installation failed
        pause
        exit /b 1
    )
    
    :: Create virtual environment
    echo Creating virtual environment...
    uv venv --python 3.13
    if %ERRORLEVEL% neq 0 (
        echo Virtual environment creation failed
        pause
        exit /b 1
    )
    
    :: Sync dependencies
    echo Syncing dependencies...
    uv sync
    if %ERRORLEVEL% neq 0 (
        echo Dependency sync failed
        pause
        exit /b 1
    )
    
    echo Virtual environment and dependencies installation completed!
)

:: Check if OpenSSL exists
if not exist "%OPENSSL_DIR%\openssl.exe" (
    echo Error: OpenSSL not found: %OPENSSL_DIR%\openssl.exe
    echo Please ensure OpenSSL is properly installed.
    pause
    exit /b 1
)

:: Check if main program exists
if not exist "%SCRIPT_DIR%\mtga_gui.py" (
    echo Error: Main program not found: %SCRIPT_DIR%\mtga_gui.py
    echo Please ensure program files are complete.
    pause
    exit /b 1
)

:: Set environment variables
set "PATH=%OPENSSL_DIR%;%PATH%"
set "PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%"

echo ====================================
echo MTGA GUI Launcher
echo ====================================
echo Starting program, please wait...

:: Switch to script directory and run program using uv (auto-uses virtual environment)
cd /d "%SCRIPT_DIR%"
uv run python "%SCRIPT_DIR%\mtga_gui.py"

:: If program exits abnormally, pause to display error information
if %ERRORLEVEL% neq 0 (
    echo.
    echo Program exited abnormally, error code: %ERRORLEVEL%
    pause
)

endlocal