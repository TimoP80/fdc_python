@echo off
REM Build script for Fallout Dialogue Creator 2.0 using Nuitka
REM Creates a faster, compiled executable

echo ========================================
echo Fallout Dialogue Creator 2.0 - Build
echo ========================================
echo.

REM Check if Nuitka is installed
python -c "import nuitka" 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Nuitka is not installed.
    echo Installing Nuitka...
    pip install nuitka
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install Nuitka.
        pause
        exit /b 1
    )
)

echo.
echo Building executable with Nuitka...
echo This may take a few minutes.
echo.

REM Run Nuitka compilation
REM --standalone: Creates a standalone distribution
REM --onefile: Creates a single executable
REM --enable-console: Shows console window (remove for GUI-only)
REM --remove-output: Removes previous build output
REM --follow-imports: Follow all imports to include them
python -m nuitka ^
    --standalone ^
    --onefile ^
    --enable-console ^
    --remove-output ^
    --follow-imports ^
    --assume-font-for-metrics ^
    --disable-integer-overflow-check ^
    --disable-string-overflow-check ^
    --disable-lint-write ^
    --windows-disable-right-click ^
    --windows-company-name="Fallout Modding" ^
    --windows-product-name="Fallout Dialogue Creator" ^
    --windows-file-version="2.5.0" ^
    --windows-product-version="2.5.0.0" ^
    main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Build FAILED!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo The executable is located in:
echo   main.dist\FalloutDialogueCreator.exe
echo.

REM Clean up build folder
echo Cleaning up...
rmdir /s /q build 2>NUL
echo Done.

pause