"""
Settings management for Fallout Dialogue Creator
"""

from PyQt6.QtCore import QSettings, QStandardPaths
from pathlib import Path
from typing import Optional, Tuple

class Settings:
    """Application settings manager"""

    # Sentinel value to distinguish between 'no default' and 'default is None'
    _DEFAULT_SENTINEL = object()

    def __init__(self):
        self.settings = QSettings("FMF Tools", "Fallout Dialogue Creator")

        # Default values
        self.defaults = {
            'font_size': 10,
            'font_family': 'Segoe UI',
            'theme': 'system',  # system, light, dark
            'auto_save': False,
            'auto_save_interval': 300000,  # 5 minutes in ms
            'debug_mode': False,
            'show_last_dialogue': True,
            'evaluate_conditions': True,
            'evaluate_skill_checks': True,
            'num_skill_simulations': 20,
            'default_smart_int': 4,
            'default_dumb_int': -3,
            'runtime_dlg_editing': False,
            'auto_remap_nodes': False,
            'plugin_compat_warnings': False,
            'fo2_data_path': '',
            'ssl_path': '',
            'script_compiler_path': '',
            'msg_path': '',
            'headers_path': '',
            'check_updates': True,
            'last_update_check': '',  # ISO timestamp of last check
            'skipped_version': '',  # Version user chose to skip
            'cloned_node_format': 'Copy_of_{}',
        }

    def get(self, key: str, default=_DEFAULT_SENTINEL):
        """Get setting value"""
        if default is Settings._DEFAULT_SENTINEL:
            default = self.defaults.get(key, None)
        return self.settings.value(key, default)

    def set(self, key: str, value):
        """Set setting value"""
        self.settings.setValue(key, value)
        self.settings.sync()

    def get_base_path(self) -> Path:
        """Get application base path"""
        return Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation)) / "FMFDLG"

    def get_dialogue_path(self) -> Path:
        """Get default dialogue files path"""
        return self.get_base_path() / "dialogue"

    def get_plugins_path(self) -> Path:
        """Get plugins directory"""
        return self.get_base_path() / "plugins"

    def get_history_path(self) -> Path:
        """Get dialogue history path"""
        return self.get_dialogue_path() / "history"

    def ensure_directories(self):
        """Ensure all required directories exist"""
        dirs = [
            self.get_base_path(),
            self.get_dialogue_path(),
            self.get_plugins_path(),
            self.get_history_path(),
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    def get_script_compiler_path(self) -> Optional[Path]:
        """
        Get the configured script compiler path.
        
        Returns:
            Path to the compiler if configured and valid, None otherwise.
        """
        from core.script_compiler import DEFAULT_COMPILER_PATH
        
        # Get user-configured path
        configured_path = self.get('script_compiler_path', '')
        
        if configured_path:
            path = Path(configured_path)
            if path.exists() and path.is_file():
                return path
        
        # Fall back to default
        if DEFAULT_COMPILER_PATH.exists():
            return DEFAULT_COMPILER_PATH
        
        return None

    def validate_script_compiler_path(self, path: str) -> Tuple[bool, str]:
        """
        Validate a script compiler path.
        
        Args:
            path: The path string to validate.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        # Empty path means use default compiler
        if not path:
            return True, "Using default compiler (leave empty to use default)"
        
        file_path = Path(path)
        
        if not file_path.exists():
            return False, f"File does not exist: {path}"
        
        if not file_path.is_file():
            return False, f"Path is not a file: {path}"
        
        # Check if file is executable (has proper extension)
        if file_path.suffix.lower() not in ['.exe', '.bat', '.cmd', '.com']:
            return False, f"File does not appear to be an executable: {path}"
        
        return True, ""
    
    # Update checker helper methods
    def get_last_update_check(self) -> Optional[str]:
        """Get last update check timestamp"""
        return self.get('last_update_check', '')
    
    def set_last_update_check(self, timestamp: str):
        """Set last update check timestamp"""
        self.set('last_update_check', timestamp)
    
    def get_skipped_version(self) -> str:
        """Get the version user chose to skip"""
        return self.get('skipped_version', '')
    
    def set_skipped_version(self, version: str):
        """Set the version user chose to skip"""
        self.set('skipped_version', version)
    
    def should_check_updates(self) -> bool:
        """Check if automatic update checking is enabled"""
        return self.get('check_updates', True)