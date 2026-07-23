@echo off
REM vault-graph install for Windows
REM Run as Administrator if needed
REM Usage: install.bat

echo vault-graph install
echo ===================

echo.
echo --- Package ---
cd /d "%~dp0"
pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo [!] pip install failed. Make sure Python 3.10+ and pip are in PATH.
    pause
    exit /b 1
)
echo [✓] vault-graph installed

echo.
echo --- Skills ---

if exist "%USERPROFILE%\.hermes" (
    mkdir "%USERPROFILE%\.hermes\skills\vault\vault-graph" 2>nul
    copy /Y "%~dp0skill.md" "%USERPROFILE%\.hermes\skills\vault\vault-graph\SKILL.md" >nul
    echo [✓] Hermes: skill installed
)

if exist "%USERPROFILE%\.trae" (
    mkdir "%USERPROFILE%\.trae\builtin_skills\vault-graph" 2>nul
    copy /Y "%~dp0skill.md" "%USERPROFILE%\.trae\builtin_skills\vault-graph\SKILL.md" >nul
    echo [✓] Trae: skill installed
)

echo.
echo vault-graph ready!
echo.
echo Commands:
echo   vault-graph build
echo   vault-graph god
echo   vault-graph search ^<term^>
echo   vault-graph explain ^<node^>
echo   vault-graph path "A" "B"
echo   vault-graph wtch
echo   vault-graph serve
echo.
echo First run: vault-graph build
echo.
pause
