@echo off
:: This batch file will run Arrow programs without needing to modify your PATH
:: Usage: run-arrow.bat your_program.ar

set SCRIPT_DIR=%~dp0
set ARROW_EXE=%SCRIPT_DIR%dist\arrow.exe

if "%~1"=="" (
    echo Usage: %~nx0 your_program.ar
    echo.
    echo Please provide an Arrow program file (.ar) as an argument.
    exit /b 1
)

if not exist "%ARROW_EXE%" (
    echo Error: Arrow executable not found at %ARROW_EXE%
    echo Please make sure you've built the executable using PyInstaller.
    exit /b 1
)

if not exist "%~1" (
    echo Error: File "%~1" not found.
    exit /b 1
)

:: Run the Arrow program
"%ARROW_EXE%" "%~1"
