"""
Settings management for Fallout Dialogue Creator
"""

from PyQt6.QtCore import QSettings, QStandardPaths
from pathlib import Path

class Settings:
    """Application settings manager"""

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
            'msg_path': '',
            'headers_path': '',
            'check_updates': True,
            'cloned_node_format': 'Copy_of_{}',
        }

    def get(self, key: str, default=None):
        """Get setting value"""
        if default is None:
            default = self.defaults.get(key)
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