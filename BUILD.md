# Nuitka Build System - Build Guide

This document provides comprehensive documentation for building the Fallout Dialogue Creator application using the Nuitka build system.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Build Command Options](#build-command-options)
3. [Configuration File](#configuration-file)
4. [Build Modes](#build-modes)
5. [Platform-Specific Builds](#platform-specific-builds)
6. [Customization](#customization)
7. [Deployment Scenarios](#deployment-scenarios)
8. [Advanced Options](#advanced-options)

## Quick Start

### Basic Build

```bash
# Install dependencies
pip install nuitka PyQt6

# Run the build
python build.py
```

### Clean Build

```bash
# Clean previous build artifacts and rebuild
python build.py --clean
```

### Build with Debug Symbols

```bash
python build.py --debug
```

## Build Command Options

The build script supports the following command-line options:

| Option | Description |
|--------|-------------|
| `--config PATH` | Path to build configuration file (default: build_config.json) |
| `--clean` | Remove build artifacts before building |
| `--onefile` | Build as a single executable file |
| `--standalone` | Build as standalone distribution |
| `--directory DIR` | Output directory (default: dist) |
| `--target PLATFORM` | Target platform: windows, linux, darwin |
| `--debug` | Include debug symbols |
| `--profile` | Enable profiling support |
| `--verbose` | Enable verbose output |
| `--help` | Show all options |

### Examples

```bash
# Build for current platform
python build.py

# Build with custom output directory
python build.py --directory ./release

# Build as single file
python build.py --onefile

# Build with debug info
python build.py --debug --verbose

# Cross-compile for Windows on Linux
python build.py --target windows --onefile
```

## Configuration File

The `build_config.json` file controls all build aspects. Here's a complete reference:

### Application Section

```json
{
    "application": {
        "name": "Fallout Dialogue Creator",
        "version": "2.3.0",
        "main_entry": "main.py",
        "description": "Application description"
    }
}
```

### Build Section

```json
{
    "build": {
        "output_dir": "dist",
        "onefile": true,
        "torun": false,
        "standalone": true,
        "plugin_enabled": true,
        "plugin_name": "pyqt6"
    }
}
```

- `output_dir`: Directory for built files
- `onefile`: Create single executable (true/false)
- `standalone`: Create standalone distribution
- `plugin_enabled`: Enable Nuitka plugins
- `plugin_name`: Plugin to use (pyqt6, pyside6, etc.)

### Compilation Section

```json
{
    "compilation": {
        "optimization_level": 3,
        "language_standard": "c11",
        "show_progress": true,
        "verbose": false,
        "assume_yes_for_questions": true,
        "remove_output": true,
        "lto": "auto",
        "follow_imports": true,
        "include_qt_plugins": ["sqldrivers", "imageformats", "platforms"]
    }
}
```

- `optimization_level`: 0-3 (3 is highest)
- `language_standard`: C standard (c11, c17)
- `lto`: Link-time optimization (auto, yes, no)
- `include_qt_plugins`: Qt plugins to include

### Hidden Imports

Modules that are imported dynamically must be explicitly included:

```json
{
    "hidden_imports": [
        "PyQt6",
        "PyQt6.QtCore",
        "sqlite3",
        "encodings.utf_8"
    ]
}
```

### Data Files

Include additional files in the build:

```json
{
    "data_files": {
        "include": [
            {"source": "HEADERS", "destination": "HEADERS"},
            {"source": "plugins", "destination": "plugins"}
        ],
        "exclude_patterns": ["*.pyc", "__pycache__", "*.log"]
    }
}
```

## Build Modes

### Onefile Mode

Creates a single executable that contains everything:

```bash
python build.py --onefile
```

Output: `dist/Fallout Dialogue Creator.exe` (Windows)

**Pros:**
- Single file distribution
- Easy to share
- No installation required

**Cons:**
- Larger file size
- Slower startup (decompression)
- No partial updates

### Standalone Mode

Creates a directory with executable and all dependencies:

```bash
python build.py  # Default is standalone with onefile
```

Output: `dist/` directory with executable and DLLs

**Pros:**
- Faster startup
- Smaller total size than onefile
- Can update individual files

**Cons:**
- Multiple files to distribute

### Torun Mode

Creates a folder that can be run directly without installation:

```json
{
    "build": {
        "torun": true,
        "onefile": false
    }
}
```

## Platform-Specific Builds

### Windows

#### Using MSVC Compiler

```json
{
    "windows": {
        "msvc": "latest",
        "console": false
    }
}
```

#### Using MinGW

```json
{
    "windows": {
        "mingw64_dir": "C:/mingw64",
        "console": false
    }
}
```

#### Windows Build Options

- `--windows-console`: Show console window
- `--windows-disable-console`: Hide console (GUI app)
- `--windows-icon-from-ico`: Set application icon
- `--windows-product-name`: Product name
- `--windows-company-name`: Company name

### Linux

#### GCC Options

```json
{
    "linux": {
        "gcc_options": ["-Wall", "-Wextra", "-O3"]
    }
}
```

#### Linux Build Options

- `--linux-icon`: Set application icon
- `--linux-single-file`: Create single file

### macOS

#### Build Options

```json
{
    "macos": {
        "macos_min_version": "10.15",
        "macos_product_name": "Fallout Dialogue Creator"
    }
}
```

#### macOS Build Options

- `--macos-icon`: Set application icon (.icns)
- `--macos-min-version`: Minimum macOS version
- `--macos-product-name`: Product name

### Cross-Compilation

#### Linux to Windows

On Linux, you can cross-compile for Windows:

```bash
# Install MinGW
sudo apt-get install mingw-w64

# Build for Windows
python build.py --target windows
```

#### Windows to Linux

Cross-compilation from Windows to Linux is not supported. Use a Linux VM or CI/CD.

## Customization

### Adding Custom Hidden Imports

If you get `ModuleNotFoundError` at runtime, add the module to hidden imports:

```json
{
    "compilation": {
        "hidden_imports": [
            "your_module",
            "your_package.submodule"
        ]
    }
}
```

### Including Custom Data Files

```json
{
    "data_files": {
        "include": [
            {"source": "assets", "destination": "assets"},
            {"source": "config.json", "destination": "config.json"}
        ]
    }
}
```

### Custom Qt Plugins

```json
{
    "compilation": {
        "include_qt_plugins": [
            "sqldrivers",     # SQL database drivers
            "imageformats",   # Image format support
            "platforms",      # Platform themes
            "printsupport"    # Printing support
        ]
    }
}
```

### Custom Compiler Options

#### Windows (MSVC)

```json
{
    "paths": {
        "msvc_version": "latest"
    }
}
```

#### Linux (GCC)

```json
{
    "linux": {
        "gcc_options": [
            "-Wall",
            "-Wextra",
            "-O3",
            "-march=native"
        ]
    }
}
```

## Deployment Scenarios

### Scenario 1: Simple Distribution

Single executable for end users:

```bash
python build.py --onefile --clean
```

### Scenario 2: Professional Distribution

Standalone directory with all files:

```bash
python build.py --clean
```

Output in `dist/`:
- `Fallout Dialogue Creator/` (folder with all files)
- Can be packaged as ZIP or installer

### Scenario 3: Portable Application

Run from USB drive:

```bash
python build.py --onefile --directory ./portable
```

### Scenario 4: Development Build

With debug symbols and profiling:

```bash
python build.py --debug --profile --verbose
```

### Scenario 5: CI/CD Automated Build

```bash
#!/bin/bash
# Build script for CI

# Clean
python build.py --clean

# Build
python build.py --onefile

# Verify
if [ -f "dist/Fallout Dialogue Creator.exe" ]; then
    echo "Build successful!"
else
    echo "Build failed!"
    exit 1
fi
```

## Advanced Options

### Debug Symbols

```json
{
    "debug": {
        "generate_debug_symbols": true,
        "debug_profile": true,
        "profile": true
    }
}
```

Or via command line:
```bash
python build.py --debug
```

### Link-Time Optimization

```json
{
    "compilation": {
        "lto": "yes"
    }
}
```

### Python Paths

```json
{
    "paths": {
        "python_include": "/usr/include/python3.10",
        "python_library": "/usr/lib/libpython3.10.so",
        "cmake": "/usr/bin/cmake"
    }
}
```

### Environment Variables

Some options can be set via environment variables:

```bash
# Use specific Python
export PYTHON=/usr/bin/python3.10

# Use specific compiler
export CC=gcc-11
export CXX=g++-11

# Build
python build.py
```

## Troubleshooting

### Common Issues

#### 1. Missing Dependencies

```
Error: Failed to import 'some_module'
```

Solution: Add to `hidden_imports` in config.

#### 2. Qt Platform Plugin Error

```
qt.qpa.plugin: Could not load the Qt platform plugin "xcb"
```

Solution: Add `"platforms"` to `include_qt_plugins`.

#### 3. Large Executable Size

Solution:
- Use `--onefile` for compression
- Exclude unnecessary modules
- Use LTO (`"lto": "yes"`)

#### 4. Slow Build Time

Solution:
- Use `--remove-output=false` for incremental builds
- Ensure antivirus excludes build directories

### Getting Help

```bash
# Show Nuitka help
python -m nuitka --help

# Show verbose output
python build.py --verbose
```

## File Structure After Build

```
project/
├── build.py                 # Build script
├── build_config.json        # Build configuration
├── dist/                    # Build output
│   └── Fallout Dialogue Creator/
│       ├── Fallout Dialogue Creator.exe  # Main executable
│       └── ...             # Dependencies (if standalone)
└── ...
```

## Next Steps

- See [INSTALL.md](INSTALL.md) for installation prerequisites
- Review `build_config.json` for customization options
- Test the build with `python build.py --debug`
