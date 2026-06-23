@echo off
setlocal

echo [1/3] Checking PyInstaller...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo     Installing PyInstaller...
    python -m pip install --upgrade pyinstaller
)

echo [2/3] Building Astra Ducunt web launcher...
python -m PyInstaller --clean AstraDucunt-web.spec

if errorlevel 1 (
    echo.
    echo Build failed. Check the error above.
    pause
    exit /b 1
)

echo [3/3] Done.
echo     Output: dist\AstraDucunt.exe
echo.
pause
