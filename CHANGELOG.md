# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0] - 2026-03-17

### Added
- **Import Feature**: New robust import system for loading DDF and MSG files
  - [`core/import_base.py`](core/import_base.py): Base infrastructure with:
    - [`ImportResult`](core/import_base.py:30) class for tracking success/errors/warnings
    - [`ImportTransaction`](core/import_base.py:100) class for atomic imports with rollback
    - [`ImportProgressReporter`](core/import_base.py:185) for thread-safe progress reporting
    - [`ImportValidator`](core/import_base.py:225) base class for validation
  - [`core/ddf_importer.py`](core/ddf_importer.py): DDF file parser with:
    - Full parsing of DDF sections (metadata, description proc, nodes, variables)
    - Player options with conditions and skill checks
    - Validation with duplicate detection and link verification
    - Batch import with progress reporting
  - [`core/msg_importer.py`](core/msg_importer.py): MSG file parser with:
    - Fallout 1/2 MSG format support (`{ID}{Speaker}{Message}`)
    - Male/female text variants
    - Speaker type detection (NPC, Player, System, Description)
    - Escaped character handling
    - Fallout 2 extended format support via [`Fallout2MSGImporter`](core/msg_importer.py:380)
  - [`core/import_manager.py`](core/import_manager.py): Unified import API with:
    - Auto-format detection based on file extension and content
    - Single file and batch import
    - Directory scanning for bulk imports
    - Convenience functions: [`import_dialogue_file()`](core/import_manager.py:215), [`import_dialogue_files()`](core/import_manager.py:232), [`import_from_directory()`](core/import_manager.py:247)
- **Unit Tests**: Comprehensive test suite in [`test_import.py`](test_import.py) covering:
  - ImportResult and ImportTransaction functionality
  - DDF import (valid, empty, malformed, comments, multiple nodes, variables)
  - MSG import (valid, empty, malformed, escaped chars, speaker types, duplicates)
  - Import manager (format detection, batch import, directory import)
  - Edge cases (unicode, long messages, special characters, mixed encoding)
  - Progress reporting

### Fixed
- **DDF Importer**: Fixed Condition class initialization - added required arguments for dataclass fields
- **MSG Importer**: Fixed empty file handling - now returns dialogue with defaults instead of None

### Changed
- **PyInstaller Spec**: Added new import modules to hidden imports:
  - `core.ddf_importer`
  - `core.msg_importer`
  - `core.import_manager`
  - `core.import_base`

## [2.2.0] - 2026-03-13

### Added
- **Update Checker Module**: New [`core/update_checker.py`](core/update_checker.py) module for automatic update detection
  - Checks GitHub releases for new versions
  - Configurable update checking with skip option
  - Downloads and installs updates with progress tracking
  - Background thread for non-blocking checks
- **Update Checker Settings**: Added to [`core/settings.py`](core/settings.py)
  - `last_update_check` timestamp tracking
  - `skipped_version` for user-skipped versions
  - Helper methods: `get_last_update_check()`, `set_last_update_check()`, `get_skipped_version()`, `set_skipped_version()`, `should_check_updates()`
- **File → Export Menu**: Centralized export functionality in main window
  - Export SSL Script
  - Export MSG Messages
  - Export SSL + MSG (combined)
  - Configure SSL/MSG Export
- **Test Plugin Example**: Added [`plugins/timbor_s_test_plugin.py`](plugins/timbor_s_test_plugin.py) as a reference plugin implementation

### Fixed
- **QPoint Import**: Fixed import in [`ui/plugin_designer.py`](ui/plugin_designer.py) - added `QPoint` to PyQt6.QtCore imports
- **Export Menu Duplication**: Removed duplicate export menu items from plugins
  - Export functionality now centralized in File menu
  - Plugins retain only configuration options

### Changed
- **Enhanced UI Theme**: Improved [`ui/fallout_theme.py`](ui/fallout_theme.py) with:
  - Better button gradients with 3D outset/inset border effects
  - Improved focus states with distinct color borders
  - Enhanced line edit and text edit styling with inset borders
  - Better group box appearance with gradient backgrounds
  - Improved dialog styling
- **Plugin Export Behavior**: Updated export plugins
  - [`plugins/export_plugin.py`](plugins/export_plugin.py): Removed export menu items (now in File → Export)
  - [`plugins/ssl_msg_export_plugin.py`](plugins/ssl_msg_export_plugin.py): Export moved to File → Export, retained only configuration
- **README**: Fixed year (2024 → 2026) and added comprehensive HTML README

## [2.1.1] - 2026-03-13

### Added
- **Plugin system security documentation**: Added security warning to `core/plugin_system.py` explaining that plugins have full Python execution privileges

### Fixed
- **Empty script compiler path validation**: Fixed `Settings.validate_script_compiler_path()` to return True for empty paths (meaning "use default")
- **Import functions cleaned up**: Removed unnecessary file dialogs from `on_import_ddf()` and `on_import_msg()` since they were not used
- **Improved TODO messages**: Updated placeholder implementations to be more explicit about what's not implemented
- **dialog_manager.py documentation**: Added better docstring explaining `get_current_node()` requires UI integration

### Changed
- **Export plugin docstring**: Fixed typo (`w"""` → `"""`)

## [2.1.0] - 2026-03-13

### Added
- **ScriptHeaderConfig class**: New configuration class for managing Fallout 2 script header files (.h)
  - Configurable header search paths with fallback support
  - Factory methods: `from_settings()` and `with_defaults()`
  - Validation methods: `find_header()` and `validate()`
  - Default paths for Fallout 1 and Fallout 2
- **ExportConfig header management**: Added `header_config` field and methods:
  - `get_header_config()`: Returns the ScriptHeaderConfig
  - `get_headers_path_string()`: Backward-compatible method for string path
- **Script compilation step in build pipeline**: Added validation step to `build.bat` that:
  - Creates test SSL files
  - Compiles using sslc.exe when available
  - Reports success/warnings appropriately

### Fixed
- **SSL/MSG Export Crash**: Fixed PyQt6 API usage in `ssl_msg_export_plugin.py`
  - Changed `layout.addWidget()` to `layout.addLayout()` for QHBoxLayout objects
  - This was causing crashes when exporting to SSL and MSG formats

### Changed
- **SSLExporter**: Now uses configurable header paths from ExportConfig
- **Plugin Version**: Updated SSL MSG Export Plugin to version 2.1.0

## [2.0.0] - 2025-10-29

### Added
- Initial release of Fallout Dialogue Creator 2.0
- Qt6-based GUI with Fallout 2 theming
- FMF file parsing for dialogue data
- Plugin system for extensibility
- SSL and MSG export functionality
- Script compiler integration
- Dialogue testing engine

### Known Issues
- See GitHub Issues for current known issues
