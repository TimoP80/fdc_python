@echo off
REM Build script for Fallout Dialogue Creator 2.0
REM Uses PyInstaller (tested and working with Qt)

echo ========================================
echo Fallout Dialogue Creator 2.0 - Build
echo ========================================
echo.

pyinstaller FalloutDialogueCreator.spec --clean

if %ERRORLEVEL% NEQ 0 (
    echo Build FAILED!
    pause
    exit /b 1
)

echo.
echo Build completed!
echo dist\FalloutDialogueCreator.exe
echo.

pause