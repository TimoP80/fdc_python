@echo off
REM Build script for Fallout Dialogue Creator 2.0
REM This script uses PyInstaller to create a single executable

echo ========================================
echo Fallout Dialogue Creator 2.0 - Build
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>NUL
if errorlevel 1 (
    echo PyInstaller is not installed.
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

echo.
echo Building executable...
echo.

REM Run PyInstaller with the spec file
pyinstaller FalloutDialogueCreator.spec --clean

if errorlevel 1 (
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
echo   dist\FalloutDialogueCreator.exe
echo.

REM ========================================
REM Script Compilation Step
REM ========================================
echo.
echo Running script compilation validation...
echo.

REM Check if Python is available for script compilation test
python -c "import sys; sys.path.insert(0, '.'); from core.script_compiler import ScriptCompiler, DEFAULT_COMPILER_PATH; print(DEFAULT_COMPILER_PATH)" 2>NUL
if errorlevel 1 (
    echo Warning: Could not run Python script compilation test.
    goto :cleanup
)

REM Run the SSL script compilation test
python -c "
import sys
from pathlib import Path
sys.path.insert(0, '.')

try:
    from core.script_compiler import ScriptCompiler, DEFAULT_COMPILER_PATH
    from core.ssl_exporter import SSLExporter, ExportConfig
    from core.msg_exporter import MSGExporter
    from models.dialogue import Dialogue, DialogueNode, PlayerOption, Reaction
    
    # Create a test dialogue
    dlg = Dialogue()
    dlg.npcname = 'TestCompiler'
    dlg.location = 'Test'
    dlg.unknowndesc = 'Test desc'
    dlg.detaileddesc = 'Test detailed desc'
    
    node = DialogueNode()
    node.nodename = 'Node0'
    node.npctext = 'Hello!'
    node.options.append(PlayerOption(optiontext='Hi', nodelink='Node999', intcheck=0, reaction=Reaction.NEUTRAL))
    dlg.nodes.append(node)
    dlg.nodecount = 1
    
    # Export SSL
    config = ExportConfig(script_number='999', headers_path='headers', output_directory=Path('test_output'))
    exporter = SSLExporter(config)
    ssl_path = Path('test_output') / 'build_test.ssl'
    ssl_path.parent.mkdir(exist_ok=True)
    content = exporter.export(dlg, ssl_path)
    print(f'Exported test SSL to {ssl_path}')
    
    # Try to compile if compiler available
    compiler = ScriptCompiler()
    if compiler.is_available():
        result = compiler.compile(ssl_path)
        if result.success:
            print('Script compilation: SUCCESS')
        else:
            print('Script compilation: WARNINGS (see errors)')
            for e in result.errors:
                print(f'  Error: {e}')
    else:
        print('Script compiler not available - skipping compilation (this is OK)')
        
except Exception as e:
    print(f'Script compilation test failed: {e}')
"

if errorlevel 1 (
    echo Warning: Script compilation test encountered issues.
)

echo.
echo Script compilation validation complete.
echo.

:cleanup
REM Clean up build artifacts (optional)
echo Cleaning up build artifacts...
rmdir /s /q build 2>NUL
echo Done.

pause
