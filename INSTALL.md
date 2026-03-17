# Nuitka Build System - Installation Guide

This document provides instructions for installing Nuitka and its dependencies for building the Fallout Dialogue Creator application.

## Prerequisites

### Python Requirements

- **Python 3.8 or higher** (Python 3.10+ recommended)
- **pip** (latest version)

Check your Python version:
```bash
python --version
pip --version
```

### Operating System Specific Requirements

#### Windows

1. **Microsoft Visual C++ Compiler** (required for compiling C extensions)
   - Install Visual Studio Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Select "Desktop development with C++" workload
   
   Or alternatively:
   
2. **MinGW-w64** (alternative to MSVC)
   - Download from: https://www.mingw-w64.org/
   - Add to PATH

#### Linux

```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install build-essential gcc g++

# Fedora
sudo dnf groupinstall "Development Tools"

# Arch Linux
sudo pacman -S base-devel
```

#### macOS

```bash
# Using Homebrew
brew install gcc

# Or install Xcode Command Line Tools
xcode-select --install
```

## Installing Nuitka

### Basic Installation

```bash
pip install nuitka
```

### Installation with Recommended Plugins

```bash
# Core Nuitka
pip install nuitka

# PyQt6 plugin (for this project)
pip install nuitka[PyQt6]

# All plugins
pip install nuitka[PyQt5,PyQt6,PySide2,PySide6,Flask,Django,etc]
```

### Verifying Installation

```bash
python -m nuitka --version
```

Expected output:
```
Nuitka 1.x.x
...
```

### Installing Additional Dependencies

This project requires:

```bash
# Core dependencies
pip install PyQt6

# Optional: for better optimization
pip install orderedset

# Optional: for better bytecode analysis  
pip install astor
```

## Compiler Configuration

### Windows - MSVC

Nuitka will automatically detect MSVC if installed. To specify a specific version:

```bash
python build.py --config build_config.json
# Edit paths.msvc_version in build_config.json
```

### Windows - MinGW

If using MinGW64, specify the path in `build_config.json`:

```json
{
    "paths": {
        "mingw64_dir": "C:/path/to/mingw64"
    }
}
```

### Linux - GCC

Nuitka uses GCC by default. To specify additional options:

```json
{
    "linux": {
        "gcc_options": ["-Wall", "-Wextra", "-O3"]
    }
}
```

### macOS - Clang

Nuitka uses Clang on macOS by default. No additional setup needed.

## Data Files and Resources

Ensure the following directories exist before building:

```
HEADERS/           # Required for dialogue parsing
plugins/           # Plugin system
```

If you have custom data files to include, add them to `build_config.json`:

```json
{
    "data_files": {
        "include": [
            {"source": "my_data", "destination": "my_data"}
        ]
    }
}
```

## Troubleshooting

### "Nuitka not found" error

```bash
# Ensure pip is up to date
pip install --upgrade pip

# Reinstall Nuitka
pip uninstall nuitka
pip install nuitka
```

### Compiler not found

- **Windows**: Ensure Visual Studio or MinGW is installed and in PATH
- **Linux**: Install build tools (`sudo apt-get install build-essential`)
- **macOS**: Install Xcode Command Line Tools

### Import errors during build

Add missing modules to `hidden_imports` in `build_config.json`:

```json
{
    "compilation": {
        "hidden_imports": [
            "missing_module_name"
        ]
    }
}
```

### Qt plugins not loading

Ensure Qt plugins are included in `build_config.json`:

```json
{
    "compilation": {
        "include_qt_plugins": ["sqldrivers", "imageformats", "platforms"]
    }
}
```

## Next Steps

Once Nuitka is installed, proceed to [BUILD.md](BUILD.md) for build instructions.
