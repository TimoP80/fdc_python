#!/usr/bin/env python3
"""
Fallout Dialogue Creator - Qt Migration
Modern cross-platform rewrite of the Fallout dialogue editor
"""

import sys
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSplitter
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QIcon, QAction

from ui.main_window import MainWindow
from core.dialog_manager import DialogManager
from core.settings import Settings
from core.plugin_system import PluginHooks

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Fallout Dialogue Creator")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("FMF Tools")

    # Initialize core components
    settings = Settings()
    dialog_manager = DialogManager(settings)

    # Notify plugins of app startup
    dialog_manager.plugin_manager.call_hook(PluginHooks.APP_STARTUP, app)

    # Load plugins
    plugin_manager = dialog_manager.plugin_manager
    plugins_dir = Path(__file__).parent / "plugins"

    # Discover and load all available plugins
    discovered_plugins = plugin_manager.discover_plugins()
    logger.info(f"Discovered {len(discovered_plugins)} plugin(s) in {plugins_dir}")

    for plugin_info in discovered_plugins:
        logger.info(f"Loading plugin: {plugin_info.name} v{plugin_info.version} by {plugin_info.author}")
        try:
            # Find the plugin file
            plugin_file = None
            for py_file in plugins_dir.glob("*.py"):
                if py_file.stem.replace('_', '').lower() == plugin_info.name.replace(' ', '').lower():
                    plugin_file = py_file
                    break

            if plugin_file:
                success = plugin_manager.load_plugin(plugin_info.name.lower().replace(' ', '_'), plugin_file)
                if success:
                    logger.info(f"[SUCCESS] Successfully loaded plugin: {plugin_info.name}")
                else:
                    logger.error(f"[FAILED] Failed to load plugin: {plugin_info.name}")
            else:
                logger.warning(f"Could not find plugin file for: {plugin_info.name}")

        except Exception as e:
            logger.error(f"Error loading plugin {plugin_info.name}: {e}")

    # Log final plugin status
    active_plugins = plugin_manager.get_active_plugins()
    logger.info(f"Plugin loading complete. {len(active_plugins)} active plugin(s):")
    for name, plugin in active_plugins.items():
        logger.info(f"  - {name}: {plugin.info.description}")

    # Create main window
    window = MainWindow(dialog_manager, settings)

    # Notify plugins that main window is created
    dialog_manager.plugin_manager.call_hook(PluginHooks.UI_MAIN_WINDOW_CREATED, window)

    window.show()

    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()