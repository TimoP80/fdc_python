# Fallout Dialogue Creator – Qt Migration

This is a modern cross-platform rewrite of the Fallout Dialogue Creator using Qt (via PyQt6) instead of Delphi VCL.

---

## Architecture Overview

### Core Components

- **models/dialogue.py** – Data models for dialogue structures (migrated from `SharedDLGData.pas`)
- **core/settings.py** – Application settings management  
- **core/dialog_manager.py** – Business logic for dialogue operations  
- **core/fmf_parser.py** – FMF file format parser with progress reporting  
- **core/parse_worker.py** – Background worker thread for non-blocking FMF parsing  
- **core/scripting_engine.py** – Secure Python scripting engine with sandboxing  
- **core/plugin_system.py** – Plugin management system with hook-based architecture  
- **core/dialogue_testing_engine.py** – Comprehensive dialogue validation and flow testing (includes script validation)  
- **test_dialogue_engine.py** – Command-line testing tool for FMF files  
- **ui/main_window.py** – Main application window and UI (includes scripting interface)  
- **plugins/** – Directory for custom plugins (`example_plugin.py` included)

---

## Key Improvements Over Original

1. **Cross-Platform:** Runs on Windows, macOS, and Linux  
2. **Modern UI:** Clean, responsive interface with dark mode support  
3. **Better Performance:** Asynchronous operations, virtualized lists, background parsing  
4. **Maintainable Code:** Python with modern patterns (MVC, signals/slots)  
5. **Extensible:** Plugin system foundation and secure Python scripting engine  
6. **Responsive Parsing:** Progress indicators prevent UI freezing during large file operations  
7. **Advanced Scripting:** Safe Python execution for custom dialogue logic with sandboxing  

---

## Development Setup

### Prerequisites

- Python 3.8+
- PyQt6

### Installation

```bash
pip install PyQt6
```

Optional developer tools:

```bash
pip install -r dev_requirements.txt
```

*(See “Developer Workflow” below.)*

### Running

```bash
cd qt_migration
python main.py
```

---

## Migration Status

### Phase 1: Core Infrastructure ✅
- [x] Project structure setup  
- [x] Data models migrated from Delphi  
- [x] Basic Qt application skeleton  
- [x] Settings management  

### Phase 2: UI Components ✅
- [x] Main window with menu system  
- [x] Dialogue editor interface  
- [x] Node editing panels  
- [x] Modern UI components (toolbar, context menus, dialogs)  
- [x] Player option management  

### Phase 3: Advanced Features ⏳
- [x] File I/O for FMF format (with progress indicators)  
- [x] Secure Python scripting engine with sandboxing  
- [x] Script execution and validation  
- [x] Plugin system with hooks  
- [x] Dialogue testing engine  

### Phase 4: Polish and Optimization ⏳
- [ ] Dark mode  
- [ ] Performance optimizations  
- [ ] Cross-platform testing  
- [ ] Documentation  

---

## File Format Compatibility

The new implementation maintains full compatibility with the original FMF dialogue format. Parsing runs in background threads with progress feedback to prevent UI blocking.

---

## Architecture Decisions

### Qt vs Flutter
Qt was chosen over Flutter for:
- Mature desktop toolkit and native feel  
- Strong Python bindings (PyQt6 / PySide6)  
- C++ integration for performance-critical paths  

### Python Implementation
Python provides:
- Rapid development and iteration  
- Huge ecosystem for tooling and plugins  
- Cross-platform deployment options  
- Easier long-term maintenance than Delphi  

---

## 🧰 Developer Workflow

These steps significantly speed up development and testing.

### 🧩 Development Tools

Add a `dev_requirements.txt`:

```txt
watchfiles
black
isort
flake8
pytest
pytest-qt
mypy
pyinstaller
python-dotenv
```

Install with:

```bash
pip install -r dev_requirements.txt
```

---

### 🏗️ Common Tasks (Makefile or dev.sh)

Example `Makefile`:

```makefile
run:
	python main.py

format:
	black . && isort .

lint:
	flake8 .

test:
	pytest -q

watch:
	watchfiles "python main.py" .

build:
	pyinstaller main.spec
```

Run tasks easily:

```bash
make run
make watch
make format
make build
```

---

### 🔁 Auto-Reload During Development

Use the `watchfiles` library for hot reloads:

```python
# dev_runner.py
from watchfiles import run_process
import os

def start():
    os.system("python main.py")

if __name__ == '__main__':
    run_process('.', target=start)
```

```bash
python dev_runner.py
```

The app restarts automatically when you save `.py` or `.ui` files.

---

### 🧱 Dynamic UI Loading

For instant UI iteration without recompiling `.ui` files:

```python
# ui_loader.py
from PyQt6.QtUiTools import QUiLoader
from PyQt6.QtCore import QFile

def load_ui(path, parent=None):
    file = QFile(path)
    file.open(QFile.OpenModeFlag.ReadOnly)
    loader = QUiLoader()
    ui = loader.load(file, parent)
    file.close()
    return ui
```

Use in your main window:

```python
self.ui = load_ui("ui/main_window.ui", self)
```

---

### 🌗 Theme Preview

Preview dark mode easily:

```python
# main.py
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
import sys

def set_dark_mode(app):
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    app.setPalette(palette)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    if "--dark" in sys.argv:
        set_dark_mode(app)
    app.exec()
```

Run:

```bash
python main.py --dark
```

---

### 🧪 Testing

Run tests quickly:

```bash
pytest -q
```

Use `pytest-qt` for GUI tests and `pytest --maxfail=1 --disable-warnings -q` for rapid runs.

---

### 🧰 Logging and Environment Config

Use a `.env` file for environment settings:

```ini
APP_ENV=development
ENABLE_DEBUG_LOGS=true
```

```python
from dotenv import load_dotenv
import os, logging
load_dotenv()

if os.getenv("ENABLE_DEBUG_LOGS") == "true":
    logging.basicConfig(level=logging.DEBUG)
```

---

### 🔍 Pre-Commit Hooks

Install automatic code checks before committing:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

Then:

```bash
pip install pre-commit
pre-commit install
```

---

## 🧪 Testing and Validation

### Application Testing

Verify:
- UI loads correctly  
- Menus and actions work  
- FMF parsing doesn’t freeze UI  
- Large file performance  

### Dialogue Testing Engine

#### Features
- Structural validation  
- Link and reference checking  
- Flow simulation  
- Loop detection  
- Script validation and sandbox testing  

#### Usage

```bash
python test_dialogue_engine.py dialogue.fmf
python test_dialogue_engine.py --recursive ./dialogues/
python test_dialogue_engine.py --output results.txt dialogue.fmf
```

---

## ⚙️ Technical Implementation Details

### Background Parsing System
Uses a QThread-based `ParseWorker` for asynchronous parsing with progress signals and safe cleanup.

### Scripting Engine
Secure Python sandbox for dialogue logic:
- Sandboxed imports  
- Timeout & memory limits  
- AST validation  
- Context API for game data  

### Plugin System
Hook-based plugin architecture with isolated execution contexts.  
Supports UI, parser, scripting, and testing extensions.

---

## 🚀 Future Enhancements

- Dark mode UI polish  
- Cloud synchronization  
- Web-based version (Qt WebEngine)  
- Advanced dialogue analytics  
- AI-assisted dialogue creation  
- Multi-language support  

---

## ✅ Summary of New Additions

- `Makefile` or `dev.sh` for one-command tasks  
- Live reload via `watchfiles`  
- Dynamic `.ui` loading for rapid iteration  
- Dark mode flag for quick testing  
- `.env` configuration for debug/dev toggles  
- Structured logging  
- Pre-commit quality gates  
- Developer-friendly testing shortcuts  
