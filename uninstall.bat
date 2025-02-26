@echo off
echo Uninstalling Arrow from PATH...
echo.

:: Get the full path to the executable
set ARROW_PATH=%~dp0dist

:: Check if the path is in PATH
echo %PATH% | findstr /C:"%ARROW_PATH%" > nul
if %errorlevel% equ 0 (
    :: Remove from PATH using PowerShell
    powershell -Command "$path = [Environment]::GetEnvironmentVariable('PATH', 'User'); $path = $path -replace '%ARROW_PATH%;?', ''; [Environment]::SetEnvironmentVariable('PATH', $path, 'User')"
    echo Removed Arrow from your PATH.
    echo You will need to restart your terminal for the changes to take effect.
) else (
    echo Arrow is not in your PATH.
)

echo.
echo You can still use Arrow by using the run-arrow.bat script:
echo   run-arrow.bat yourfile.ar
echo.
pause
