# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
