@echo off
echo Installing Arrow...
echo.

:: Get the full path to the executable
set ARROW_PATH=%~dp0dist

:: Check if the path is already in PATH
echo %PATH% | findstr /C:"%ARROW_PATH%" > nul
if %errorlevel% equ 0 (
    echo Arrow is already in your PATH.
) else (
    :: Add to PATH more safely using PowerShell
    powershell -Command "[Environment]::SetEnvironmentVariable('PATH', [Environment]::GetEnvironmentVariable('PATH', 'User') + ';%ARROW_PATH%', 'User')"
    echo Added Arrow to your PATH.
    echo You will need to restart your terminal for the changes to take effect.
)

echo.
echo You can now use 'arrow yourfile.ar' from any directory (after restarting your terminal).
echo.
pause
