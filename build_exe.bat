@echo off
REM ========================================================================
REM  단일 exe 빌드 스크립트 (관리자=당신 PC 에서만 실행)
REM  - 친구는 Python/Java 불필요. 이 배치로 만든 exe 하나만 받으면 됩니다.
REM ========================================================================
setlocal

echo [1/3] PyInstaller 설치 확인...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo     PyInstaller 가 없어 설치합니다...
    python -m pip install --upgrade pyinstaller
)

echo [2/3] 빌드 시작...
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "ModInstaller" ^
    --clean ^
    installer.py

if errorlevel 1 (
    echo.
    echo 빌드 실패. 위 메시지를 확인하세요.
    pause
    exit /b 1
)

echo [3/3] 완료!
echo     결과물: dist\ModInstaller.exe
echo     이 exe 를 친구에게 직접 전달하세요 (GitHub 에는 올리지 않음).
echo.
pause
