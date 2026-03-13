# Fallout 2 Script Compilation Feature Plan

## Overview
Integrate the SSL (Fallout Scripting Language) compiler into the Fallout Dialogue Creator to enable compiling `.ssl` scripts to `.int` format.

## Compiler Location
- **Source**: `C:\CodeProjects\sslc_source`
- **Executable**: `C:\CodeProjects\sslc_source\Release\sslc.exe`
- **DLL**: `C:\CodeProjects\sslc_source\DLL\ScriptCompiler.dll`

## Compiler Command-Line Interface
Based on analyzing `compile.c`:

```
Usage: compile {switches} filename [filename [..]]
Switches:
  -w    Enable warnings
```

**Output**: Generates `.int` files from `.ssl` source files

## Implementation Tasks

### 1. Create SSL Compiler Integration Module
Create a new module `core/script_compiler.py` that:
- Wraps the `sslc.exe` command-line compiler
- Provides Python API for compilation
- Handles input/output paths
- Captures compiler errors and warnings

### 2. Define Compiler Interface
```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class CompileStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"

@dataclass
class CompileResult:
    status: CompileStatus
    input_file: Path
    output_file: Optional[Path]
    errors: List[str]
    warnings: List[str]

class ScriptCompiler:
    def __init__(self, compiler_path: Path = None):
        # Default to Release/sslc.exe in sslc_source
        self.compiler_path = compiler_path or DEFAULT_COMPILER_PATH
    
    def compile(self, ssl_file: Path) -> CompileResult:
        """Compile a single .ssl file to .int"""
        # Run: sslc.exe -w filename.ssl
        # Parse output for errors/warnings
        # Return CompileResult
    
    def compile_batch(self, ssl_files: List[Path]) -> List[CompileResult]:
        """Compile multiple .ssl files"""
```

### 3. Add UI Integration
- Add "Compile Script" menu item to File menu
- Add toolbar button for quick compilation
- Add compilation status to status bar

### 4. Handle Compilation Results
- Parse compiler output for errors/warnings
- Display errors in a dedicated output panel
- Navigate to error lines in SSL source

## File Structure Changes
```
core/
  script_compiler.py    (NEW - SSL compiler wrapper)
```

## Dependencies
- `subprocess` module for running compiler
- `pathlib` for path handling
- Existing logging infrastructure

## Testing Plan
1. Test with existing .ssl files
2. Test error handling for invalid syntax
3. Test UI integration

## Considerations
- The compiler is a Windows executable (C-based)
- May need to handle paths with spaces
- Compiler returns exit codes for success/failure
- Need to parse error messages to extract line numbers
