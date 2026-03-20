# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.1] - 2026-03-20

### Added
- **Player Option Conditions**: Full support for defining conditions on player dialogue options
  - [`core/fmf_parser.py`](core/fmf_parser.py): Added [`_parse_conditions()`](core/fmf_parser.py:605) and [`_write_conditions()`](core/fmf_parser.py:800) methods
  - Supports multiple condition types: CHECK_STAT, CHECK_SKILL, CHECK_MONEY, LOCAL_VARIABLE, GLOBAL_VARIABLE, CHECK_CUSTOM_CODE
  - Condition evaluation with AND/OR/NONE link operators
  - Full parsing and saving of conditions in FMF format

### Changed
- **About Dialog UI**: Resized to 16:9 aspect ratio with approximately 850px width
  - Changed from 520x550 to 850x479
  - Featured image increased by 50% (from 480x200 to 720x300)
  - Maintains proper aspect ratio and remains centered
- **SSL Exporter**: Enhanced condition generation for player options
  - [`core/ssl_exporter.py`](core/ssl_exporter.py): Added [`generate_option_conditions()`](core/ssl_exporter.py:295) in ConditionGenerator
  - Generates condition code for each player option based on defined conditions
- **Scripting Engine**: Improved condition evaluation for player options
  - Enhanced condition checking for stats, skills, caps, and variables
- **MSG Import/Export**: Updated message handling for dialogue export
- **FMF Parser**: Full read/write support for player option conditions

### Removed
- **SVN Metadata**: Removed deprecated .svn folders from HEADERS directory

## [2.3.0] - 2026-03-17

### Added
- **Nuitka Build System**: New Python-based build system for creating standalone executables
  - [`build.py`](build.py): Main build script with [`NuitkaBuilder`](build.py:36) class
    - Configurable via JSON configuration file
    - Support for onefile and standalone builds
    - Platform-specific options for Windows, Linux, and macOS
    - Debug, profile, and verbose modes
    - Automatic dependency detection and hidden imports
  - [`build_config.json`](build_config.json): Build configuration file
    - Application metadata (name, version, entry point)
    - Build options (output directory, onefile, standalone)
    - Compilation settings (optimization, LTO, Qt plugins)
    - Platform-specific configurations
  - [`BUILD.md`](BUILD.md): Comprehensive build documentation
    - Quick start guide
    - All command-line options explained
    - Configuration file reference
    - Build modes (onefile, standalone, torun)
    - Platform-specific builds (Windows MSVC/MinGW, Linux GCC, macOS)
    - Cross-compilation guide
    - Deployment scenarios
    - Troubleshooting section
  - [`INSTALL.md`](INSTALL.md): Installation guide for Nuitka and dependencies
    - Python requirements (3.8+)
    - OS-specific setup (Windows MSVC/MinGW, Linux, macOS)
    - Nuitka installation with PyQt6 plugin
    - Compiler configuration
    - Troubleshooting common issues
- **Fallout 2 MSG Parser**: New [`core/msg_parser.py`](core/msg_parser.py) for parsing Fallout 2 MSG files
  - [`Fallout2MsgParser`](core/msg_parser.py:81) class for three-field format `{id}{audiofile}{message}`
  - [`Fallout2MsgEntry`](core/msg_parser.py:26) dataclass for parsed entries
  - [`Fallout2MsgParseResult`](core/msg_parser.py:48) with error/warning tracking
  - Strict and non-strict parsing modes
  - Validates against four-field and alternative formats
  - Escape sequence handling (\n, \t, \\{, \\}, \\\\)
  - [`Fallout2FormatError`](core/msg_parser.py:73) exception for parse errors
- **MSG Parser Tests**: New [`test_msg_parser.py`](test_msg_parser.py) with comprehensive tests
  - Valid three-field format parsing
  - Four-field format rejection
  - Speaker format handling
  - Empty audiofile field handling
  - Comments and empty line skipping
  - Structured output verification
  - Strict mode exception testing
  - Escape sequence handling
- **Import Implementation**: Implemented DDF and MSG file import in [`ui/main_window.py`](ui/main_window.py)
  - [`on_import_ddf()`](ui/main_window.py:2626): Imports DDF files using [`DDFImporter`](core/ddf_importer.py)
  - [`on_import_msg()`](ui/main_window.py:2659): Imports MSG files using [`MSGImporter`](core/msg_importer.py)
  - Both methods now display file dialogs, parse files, and load dialogues into the editor
  - Proper error handling with user-friendly messages
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
- **Script Compilation**: Full script compilation functionality in [`ui/main_window.py`](ui/main_window.py:3094)
  - Generates SSL from dialogue and compiles with sslc.exe
  - Validates SSL before compilation
  - Proper error handling with detailed messages
  - Uses cp1252 encoding for Fallout 2 compatibility
- **Script Header Configuration**: New [`ScriptHeaderConfig`](core/ssl_exporter.py:42) class for header file management
  - Configurable header search paths with fallback support
  - Automatic header validation
  - Integration with application settings
- **Double-Click Editing**: Added double-click handlers for quick editing
  - Float nodes: [`on_float_node_double_clicked()`](ui/main_window.py:1006)
  - Skill checks: [`on_skill_check_double_clicked()`](ui/main_window.py:1209)
- **Fallout Header Files**: Added [`HEADERS/`](HEADERS/) directory with Fallout 2 header files
  - Complete set of .h files (define.h, command.h, scripts.h, etc.)
  - For SSL validation and compilation
- **Unit Tests**: Comprehensive test suite in [`test_import.py`](test_import.py) covering:
  - ImportResult and ImportTransaction functionality
  - DDF import (valid, empty, malformed, comments, multiple nodes, variables)
  - MSG import (valid, empty, malformed, escaped chars, speaker types, duplicates)
  - Import manager (format detection, batch import, directory import)
  - Edge cases (unicode, long messages, special characters, mixed encoding)
  - Progress reporting

### Fixed
- **Parse Worker Memory Leak** ([`core/dialog_manager.py`](core/dialog_manager.py:93)): Fixed memory leak by adding `wait()` call before `deleteLater()` to ensure worker thread finishes before cleanup
- **Node Selection Tracking** ([`core/dialog_manager.py`](core/dialog_manager.py:50,138)): Fixed `get_current_node()` returning None - added `_selected_node_index` attribute and `set_selected_node()` method for proper node selection
- **Plugin Security Warnings** ([`core/plugin_system.py`](core/plugin_system.py:193)): Added plugin trust tracking with `_trusted_plugins` dictionary and methods: `is_plugin_trusted()`, `set_plugin_trusted()`, `should_warn_about_plugin()`, `get_security_warning_message()`
- **Settings Default Value Handling** ([`core/settings.py`](core/settings.py:12)): Added `_DEFAULT_SENTINEL` to distinguish between "no default" and "default is None"
- **Import Before Definition** ([`ui/fallout_widgets.py`](ui/fallout_widgets.py:25)): Moved `from ui.fallout_theme import FalloutColors` to module level before class definitions
- **CRT Animation Timer** ([`ui/fallout_widgets.py`](ui/fallout_widgets.py:393)): Fixed CRT scanline timer always running - now starts in `showEvent()` and stops in `hideEvent()` for better performance
- **Division by Zero** ([`ui/fallout_widgets.py`](ui/fallout_widgets.py:260)): Added validation in `SpecialStatBar` to prevent division by zero when `max_value` is 0
- **Unused Import** ([`core/msg_exporter.py`](core/msg_exporter.py:19)): Moved `import re` from inside method to module level
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
