"""
SSL + MSG Export Plugin for Fallout Dialogue Creator

This plugin provides complete export functionality for Fallout 2 dialogue files:
- SSL script files with proper dialogue structure
- MSG message files with NPC dialogue text
- Integration with script compiler for validation
- Fallout 1 and Fallout 2 format support
- Export configuration dialog with options

The exported files are directly usable by the Fallout 2 engine.
"""

from core.plugin_system import PluginInterface, PluginType, PluginHooks, PluginInfo
from core.ssl_exporter import SSLExporter, ExportConfig, GameVersion, export_ssl
from core.msg_exporter import MSGExporter, export_msg, create_msg_filename
from core.script_compiler import ScriptCompiler, CompileResult
from core.settings import Settings
from pathlib import Path
import logging

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QLineEdit, QPushButton, QCheckBox, QGroupBox, QFileDialog,
    QMessageBox, QSpinBox, QDialogButtonBox, QTabWidget, QWidget,
    QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal

logger = logging.getLogger(__name__)


class ExportConfigDialog(QDialog):
    """Dialog for configuring export options"""
    
    config_changed = pyqtSignal(object)  # Emits ExportConfig
    
    def __init__(self, parent=None, current_config: ExportConfig = None):
        super().__init__(parent)
        self.setWindowTitle("Export Configuration")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        # Default config
        self.config = current_config or ExportConfig()
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Set up the UI components"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # General tab
        tabs.addTab(self._create_general_tab(), "General")
        
        # Paths tab
        tabs.addTab(self._create_paths_tab(), "Paths")
        
        # Advanced tab
        tabs.addTab(self._create_advanced_tab(), "Advanced")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _create_general_tab(self) -> QWidget:
        """Create general settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Game version
        version_group = QGroupBox("Game Version")
        version_layout = QVBoxLayout()
        
        self.version_combo = QComboBox()
        self.version_combo.addItem("Fallout 2", GameVersion.FALLOUT_2)
        self.version_combo.addItem("Fallout 1", GameVersion.FALLOUT_1)
        self.version_combo.setCurrentIndex(
            0 if self.config.game_version == GameVersion.FALLOUT_2 else 1
        )
        version_layout.addWidget(QLabel("Target Game:"))
        version_layout.addWidget(self.version_combo)
        version_group.setLayout(version_layout)
        layout.addWidget(version_group)
        
        # Script settings
        script_group = QGroupBox("Script Settings")
        script_layout = QVBoxLayout()
        
        self.script_number_edit = QLineEdit(self.config.script_number)
        script_layout.addWidget(QLabel("Script Number:"))
        script_layout.addWidget(self.script_number_edit)
        
        self.headers_path_edit = QLineEdit(self.config.headers_path)
        script_layout.addWidget(QLabel("Headers Path:"))
        script_layout.addWidget(self.headers_path_edit)
        
        script_group.setLayout(script_layout)
        layout.addWidget(script_group)
        
        # Output options
        output_group = QGroupBox("Output Options")
        output_layout = QVBoxLayout()
        
        self.separate_dirs_check = QCheckBox("Separate SSL/MSG directories")
        self.separate_dirs_check.setChecked(True)
        output_layout.addWidget(self.separate_dirs_check)
        
        self.open_after_export_check = QCheckBox("Open output folder after export")
        self.open_after_export_check.setChecked(False)
        output_layout.addWidget(self.open_after_export_check)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        layout.addStretch()
        return widget
    
    def _create_paths_tab(self) -> QWidget:
        """Create paths settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Output directory
        output_dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit(str(self.config.output_directory))
        output_dir_layout.addWidget(QLabel("Output Directory:"))
        output_dir_layout.addWidget(self.output_dir_edit, 1)
        
        output_dir_btn = QPushButton("Browse...")
        output_dir_btn.clicked.connect(self._browse_output_dir)
        output_dir_layout.addWidget(output_dir_btn)
        layout.addLayout(output_dir_layout)
        
        # Fallout data path (for MSG)
        fo2_dir_layout = QHBoxLayout()
        self.fo2_dir_edit = QLineEdit()
        fo2_dir_layout.addWidget(QLabel("Fallout 2 Data Path:"))
        fo2_dir_layout.addWidget(self.fo2_dir_edit, 1)
        
        fo2_dir_btn = QPushButton("Browse...")
        fo2_dir_btn.clicked.connect(self._browse_fo2_dir)
        fo2_dir_layout.addWidget(fo2_dir_btn)
        layout.addLayout(fo2_dir_layout)
        
        # Compiler path
        compiler_layout = QHBoxLayout()
        self.compiler_path_edit = QLineEdit()
        compiler_layout.addWidget(QLabel("Script Compiler:"))
        compiler_layout.addWidget(self.compiler_path_edit, 1)
        
        compiler_btn = QPushButton("Browse...")
        compiler_btn.clicked.connect(self._browse_compiler)
        compiler_layout.addWidget(compiler_btn)
        layout.addLayout(compiler_layout)
        
        layout.addStretch()
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """Create advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Validation options
        validation_group = QGroupBox("Validation")
        validation_layout = QVBoxLayout()
        
        self.validate_ssl_check = QCheckBox("Validate SSL syntax before export")
        self.validate_ssl_check.setChecked(True)
        validation_layout.addWidget(self.validate_ssl_check)
        
        self.compile_ssl_check = QCheckBox("Compile SSL after export")
        self.compile_ssl_check.setChecked(False)
        validation_layout.addWidget(self.compile_ssl_check)
        
        self.show_warnings_check = QCheckBox("Show warnings in output")
        self.show_warnings_check.setChecked(True)
        validation_layout.addWidget(self.show_warnings_check)
        
        validation_group.setLayout(validation_layout)
        layout.addWidget(validation_group)
        
        # Encoding options
        encoding_group = QGroupBox("Encoding")
        encoding_layout = QVBoxLayout()
        
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItem("CP1252 (Fallout 2)", "cp1252")
        self.encoding_combo.addItem("ISO-8859-1 (Fallout 1)", "iso8859-1")
        self.encoding_combo.addItem("UTF-8", "utf-8")
        encoding_layout.addWidget(QLabel("MSG File Encoding:"))
        encoding_layout.addWidget(self.encoding_combo)
        
        encoding_group.setLayout(encoding_layout)
        layout.addWidget(encoding_group)
        
        # Debug options
        debug_group = QGroupBox("Debug")
        debug_layout = QVBoxLayout()
        
        self.debug_comments_check = QCheckBox("Include debug comments in SSL")
        self.debug_comments_check.setChecked(True)
        debug_layout.addWidget(self.debug_comments_check)
        
        self.fo1_compat_check = QCheckBox("Fallout 1 compatibility mode")
        self.fo1_compat_check.setChecked(False)
        debug_layout.addWidget(self.fo1_compat_check)
        
        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)
        
        layout.addStretch()
        return widget
    
    def _browse_output_dir(self):
        """Browse for output directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory",
            self.output_dir_edit.text() or str(Path.cwd())
        )
        if directory:
            self.output_dir_edit.setText(directory)
    
    def _browse_fo2_dir(self):
        """Browse for Fallout 2 directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Fallout 2 Data Directory",
            self.fo2_dir_edit.text() or "C:\\Games\\Fallout2"
        )
        if directory:
            self.fo2_dir_edit.setText(directory)
    
    def _browse_compiler(self):
        """Browse for script compiler"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Script Compiler",
            self.compiler_path_edit.text() or "C:\\CodeProjects\\sslc_source\\Release",
            "Executables (*.exe);;All Files (*.*)"
        )
        if file_path:
            self.compiler_path_edit.setText(file_path)
    
    def _load_settings(self):
        """Load settings from application settings"""
        settings = Settings()
        
        # Load paths
        self.output_dir_edit.setText(
            settings.get('export_output_path', str(Path.cwd() / 'output'))
        )
        self.fo2_dir_edit.setText(
            settings.get('fo2_data_path', '')
        )
        
        compiler_path = settings.get_script_compiler_path()
        if compiler_path:
            self.compiler_path_edit.setText(str(compiler_path))
    
    def get_config(self) -> ExportConfig:
        """Get the current configuration"""
        
        # Get game version
        game_version = self.version_combo.currentData()
        
        # Get encoding
        encoding = self.encoding_combo.currentData()
        
        # Create config
        config = ExportConfig(
            game_version=game_version,
            output_directory=Path(self.output_dir_edit.text()),
            script_number=self.script_number_edit.text(),
            headers_path=self.headers_path_edit.text(),
            include_debug_comments=self.debug_comments_check.isChecked(),
            use_fallout1_compatibility=self.fo1_compat_check.isChecked(),
            encoding=encoding
        )
        
        return config


class SSLMSGExportPlugin(PluginInterface):
    """Main SSL + MSG Export Plugin for Fallout Dialogue Creator"""

    def __init__(self):
        super().__init__()
        self.plugin_info = PluginInfo(
            name="SSL MSG Export Plugin",
            version="2.1.0",
            description="Exports dialogue to Fallout 2 compatible SSL scripts and MSG message files with validation",
            author="Fallout Dialogue Creator Team",
            plugin_type=PluginType.EXPORT_EXTENSION
        )
        
        # UI references
        self.menu_action_export = None
        self.menu_action_export_ssl = None
        self.menu_action_export_msg = None
        self.menu_action_configure = None
        
        # Export settings
        self.config = ExportConfig()
        self.settings = Settings()
        
        # Compiler reference
        self.compiler = None
        
        # Last export results
        self.last_ssl_content = ""
        self.last_msg_content = ""
    
    def initialize(self, plugin_manager) -> bool:
        """Initialize the plugin"""
        logger.info("Initializing SSL + MSG Export Plugin")
        
        # Load settings
        self._load_settings()
        
        # Initialize compiler
        self._init_compiler()
        
        return True
    
    def _load_settings(self):
        """Load export settings from application settings"""
        
        # Output directory
        output_path = self.settings.get('export_output_path', '')
        if output_path:
            self.config.output_directory = Path(output_path)
        
        # Script number
        script_num = self.settings.get('default_script_number', '001')
        if script_num:
            self.config.script_number = script_num
        
        # Headers path
        headers_path = self.settings.get('headers_path', 'headers')
        if headers_path:
            self.config.headers_path = headers_path
    
    def _init_compiler(self):
        """Initialize the script compiler"""
        compiler_path = self.settings.get_script_compiler_path()
        
        if compiler_path and compiler_path.exists():
            header_paths = [
                Path(self.config.headers_path),
                Path(self.settings.get('headers_path', 'headers'))
            ]
            
            self.compiler = ScriptCompiler(compiler_path, header_paths)
            logger.info(f"Script compiler initialized: {compiler_path}")
        else:
            logger.warning("Script compiler not available")
    
    def activate(self) -> bool:
        """Activate the plugin"""
        logger.info("Activating SSL + MSG Export Plugin")
        return True

    def deactivate(self) -> bool:
        """Deactivate the plugin"""
        logger.info("Deactivating SSL + MSG Export Plugin")
        return True

    def get_hooks(self) -> dict:
        """Return hook functions"""
        return {
            PluginHooks.APP_STARTUP: [self.on_app_startup],
            PluginHooks.UI_MENU_BAR_CREATED: [self.on_menu_bar_created],
            PluginHooks.DIALOGUE_LOADED: [self.on_dialogue_loaded],
            PluginHooks.DIALOGUE_SAVED: [self.on_dialogue_saved],
        }

    def on_app_startup(self, app):
        """Called when application starts"""
        logger.info("SSL + MSG Export Plugin: Application startup")

    def on_menu_bar_created(self, menu_bar):
        """Called when menu bar is created - add configuration only (export is in File menu)"""
        logger.info("SSL + MSG Export Plugin: Adding configuration menu item")

        # Find the File menu
        file_menu = None
        for action in menu_bar.actions():
            if action.text() == "&File":
                file_menu = action.menu()
                break
        
        if not file_menu:
            # Try Tools menu
            for action in menu_bar.actions():
                if action.text() == "&Tools":
                    file_menu = action.menu()
                    break
        
        if not file_menu:
            # Create File menu if it doesn't exist
            file_menu = menu_bar.addMenu("&File")

        # Add configuration only (export functionality is in File → Export in main_window)
        file_menu.addSeparator()
        self.menu_action_configure = file_menu.addAction("Configure SSL/MSG Export...")
        self.menu_action_configure.triggered.connect(self.show_config_dialog)
    
    def on_dialogue_loaded(self, dialogue):
        """Called when a dialogue is loaded"""
        logger.info(f"SSL + MSG Export Plugin: Dialogue loaded - {dialogue.npcname}")
    
    def on_dialogue_saved(self, dialogue):
        """Called when a dialogue is saved"""
        logger.info(f"SSL + MSG Export Plugin: Dialogue saved - {dialogue.npcname}")
    
    def show_config_dialog(self):
        """Show the export configuration dialog"""
        dialog = ExportConfigDialog(None, self.config)
        
        if dialog.exec():
            self.config = dialog.get_config()
            logger.info("Export configuration updated")
    
    def get_dialog_manager(self):
        """Get the dialog manager instance"""
        from core.dialog_manager import DialogManager
        
        # Try to find it
        import gc
        for obj in gc.get_objects():
            if isinstance(obj, DialogManager):
                return obj
        
        return None
    
    def get_current_dialogue(self):
        """Get the currently loaded dialogue"""
        dialog_manager = self.get_dialog_manager()
        if dialog_manager:
            return dialog_manager.get_current_dialogue()
        return None
    
    def export_ssl_msg(self):
        """Export both SSL and MSG files"""
        try:
            dialogue = self.get_current_dialogue()
            if not dialogue:
                QMessageBox.warning(
                    None, "Export Error", "No dialogue loaded"
                )
                return
            
            # Show config dialog first
            dialog = ExportConfigDialog(None, self.config)
            if not dialog.exec():
                return
            
            self.config = dialog.get_config()
            
            # Create output directory
            output_dir = Path(self.config.output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filenames
            ssl_filename = self._get_ssl_filename(dialogue)
            msg_filename = create_msg_filename(dialogue)
            
            ssl_path = output_dir / ssl_filename
            msg_path = output_dir / msg_filename
            
            # Export SSL
            logger.info(f"Exporting SSL to: {ssl_path}")
            ssl_content, ssl_errors, ssl_warnings = self._export_ssl_internal(
                dialogue, ssl_path
            )
            
            if not ssl_content:
                QMessageBox.critical(
                    None, "SSL Export Failed",
                    f"Failed to export SSL:\n" + "\n".join(ssl_errors)
                )
                return
            
            # Export MSG
            logger.info(f"Exporting MSG to: {msg_path}")
            msg_content = export_msg(
                dialogue, 
                msg_path,
                encoding=self.config.encoding,
                is_fallout1=self.config.game_version.value == "fallout1"
            )
            
            # Show results
            self._show_export_results(
                dialogue,
                ssl_path, msg_path,
                ssl_errors, ssl_warnings,
                len(msg_content.split('\n'))
            )
            
        except Exception as e:
            logger.error(f"Error exporting SSL+MSG: {e}")
            QMessageBox.critical(
                None, "Export Error",
                f"Failed to export files:\n{str(e)}"
            )
    
    def export_ssl(self):
        """Export SSL script file only"""
        try:
            dialogue = self.get_current_dialogue()
            if not dialogue:
                QMessageBox.warning(
                    None, "Export Error", "No dialogue loaded"
                )
                return
            
            # Show config dialog first
            dialog = ExportConfigDialog(None, self.config)
            if not dialog.exec():
                return
            
            self.config = dialog.get_config()
            
            # Get output path
            output_dir = Path(self.config.output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            ssl_filename = self._get_ssl_filename(dialogue)
            ssl_path = output_dir / ssl_filename
            
            # Export SSL
            ssl_content, ssl_errors, ssl_warnings = self._export_ssl_internal(
                dialogue, ssl_path
            )
            
            if ssl_content:
                QMessageBox.information(
                    None, "Export Complete",
                    f"SSL script exported successfully!\n\n"
                    f"File: {ssl_path}\n"
                    f"Size: {len(ssl_content)} characters\n\n"
                    f"This file can be compiled with the Fallout 2 script compiler."
                )
            else:
                QMessageBox.critical(
                    None, "SSL Export Failed",
                    f"Failed to export SSL:\n" + "\n".join(ssl_errors)
                )
            
        except Exception as e:
            logger.error(f"Error exporting SSL: {e}")
            QMessageBox.critical(
                None, "Export Error",
                f"Failed to export SSL:\n{str(e)}"
            )
    
    def export_msg(self):
        """Export MSG message file only"""
        try:
            dialogue = self.get_current_dialogue()
            if not dialogue:
                QMessageBox.warning(
                    None, "Export Error", "No dialogue loaded"
                )
                return
            
            # Show config dialog first
            dialog = ExportConfigDialog(None, self.config)
            if not dialog.exec():
                return
            
            self.config = dialog.get_config()
            
            # Get output path
            output_dir = Path(self.config.output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            msg_filename = create_msg_filename(dialogue)
            msg_path = output_dir / msg_filename
            
            # Export MSG
            msg_content = export_msg(
                dialogue,
                msg_path,
                encoding=self.config.encoding,
                is_fallout1=self.config.game_version.value == "fallout1"
            )
            
            QMessageBox.information(
                None, "Export Complete",
                f"MSG file exported successfully!\n\n"
                f"File: {msg_path}\n"
                f"Entries: {len(msg_content.split(chr(10)))} lines\n\n"
                f"This file can be used by the Fallout 2 engine."
            )
            
        except Exception as e:
            logger.error(f"Error exporting MSG: {e}")
            QMessageBox.critical(
                None, "Export Error",
                f"Failed to export MSG:\n{str(e)}"
            )
    
    def _export_ssl_internal(self, dialogue, output_path: Path) -> tuple:
        """Internal SSL export with validation"""
        
        # Export SSL
        success, content, errors, warnings = export_ssl(
            dialogue,
            output_path,
            self.config,
            validate=True
        )
        
        if not success:
            return "", errors, warnings
        
        # Try to compile if compiler available
        if self.compiler and self.compiler.is_available():
            logger.info("Validating SSL with compiler...")
            result = self.compiler.compile(output_path)
            
            if not result.success:
                errors.extend(result.errors)
                warnings.extend(result.warnings)
            else:
                warnings.append("SSL syntax validation passed!")
        
        return content, errors, warnings
    
    def _get_ssl_filename(self, dialogue) -> str:
        """Generate SSL filename from dialogue"""
        name = dialogue.npcname.lower().replace(' ', '_').replace('-', '_')
        name = ''.join(c for c in name if c.isalnum() or c == '_')
        return f"{name}.ssl"
    
    def _show_export_results(
        self, dialogue, ssl_path: Path, msg_path: Path,
        ssl_errors: list, ssl_warnings: list, msg_line_count: int
    ):
        """Show export results dialog"""
        
        results = f"""Export completed!

SSL Script: {ssl_path.name}
  Size: {len(self.last_ssl_content)} characters

MSG Messages: {msg_path.name}
  Entries: {msg_line_count} lines

Output Directory: {ssl_path.parent}"""
        
        if ssl_errors:
            results += f"\n\nErrors:\n" + "\n".join(f"  - {e}" for e in ssl_errors)
        
        if ssl_warnings:
            results += f"\n\nWarnings:\n" + "\n".join(f"  - {w}" for w in ssl_warnings)
        
        results += "\n\nThe exported files are ready for use with the Fallout 2 engine."
        
        QMessageBox.information(None, "Export Complete", results)


# Plugin instantiation function
def create_plugin():
    """Create and return the plugin instance"""
    return SSLMSGExportPlugin()
