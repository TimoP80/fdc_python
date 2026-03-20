#!/usr/bin/env python3
"""
Fallout Dialogue Creator - Qt Migration
Modern cross-platform rewrite of the Fallout dialogue editor
"""

__version__ = "2.3.0"

import sys
import logging
import os
import io
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Fix StreamHandler encoding for Windows console
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler):
        try:
            handler.stream.reconfigure(encoding='utf-8')
        except (AttributeError, io.UnsupportedOperation):
            # Fallback: use a wrapper that handles encoding errors
            original_write = handler.stream.write
            def safe_write(text):
                try:
                    original_write(text)
                except UnicodeEncodeError:
                    # Replace problematic characters with ASCII alternatives
                    safe_text = text.encode('ascii', 'replace').decode('ascii')
                    original_write(safe_text)
            handler.stream.write = safe_write
logger = logging.getLogger(__name__)

# Add the current directory to Python path for imports
# In frozen mode, we need to handle paths differently
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running as PyInstaller bundle - _MEIPASS contains the extracted files
    base_path = Path(sys._MEIPASS)
else:
    # Running in development
    base_path = Path(__file__).parent

sys.path.insert(0, str(base_path))

from core.dialog_manager import DialogManager
from core.settings import Settings
from core.plugin_system import PluginHooks

def create_splash_pixmap():
    """Create a Fallout-themed splash screen pixmap"""
    # Create splash screen image
    width, height = 500, 350
    pixmap = QPixmap(width, height)
    
    # Fill with dark background
    pixmap.fill(QColor(0x1a, 0x1a, 0x1a))
    
    # Create painter for custom drawing
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Draw border frame
    painter.setPen(QColor(0x5c, 0x5c, 0x5c))
    painter.drawRect(0, 0, width - 1, height - 1)
    painter.setPen(QColor(0x3d, 0x4f, 0x2a))
    painter.drawRect(2, 2, width - 5, height - 5)
    
    # Draw title - Fallout Yellow
    title_font = QFont("Consolas", 24, QFont.Weight.Bold)
    painter.setFont(title_font)
    painter.setPen(QColor(0xff, 0xcc, 0x00))
    title_rect = pixmap.rect().adjusted(0, 40, 0, -200)
    painter.drawText(title_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "FALLOUT")
    
    # Draw subtitle
    subtitle_font = QFont("Consolas", 16, QFont.Weight.Bold)
    painter.setFont(subtitle_font)
    painter.setPen(QColor(0x6b, 0x8e, 0x23))
    subtitle_rect = pixmap.rect().adjusted(0, 80, 0, -160)
    painter.drawText(subtitle_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "Dialogue Creator")
    
    # Draw version
    version_font = QFont("Consolas", 11)
    painter.setFont(version_font)
    painter.setPen(QColor(0xc4, 0xb9, 0x98))
    version_rect = pixmap.rect().adjusted(0, 115, 0, -130)
    painter.drawText(version_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "Version 2.3.0")
    
    # Draw decorative line
    painter.setPen(QColor(0xb7, 0x41, 0x0e))
    painter.drawLine(50, 150, width - 50, 150)
    
    # Draw loading text
    loading_font = QFont("Courier New", 10)
    painter.setFont(loading_font)
    painter.setPen(QColor(0x33, 0xff, 0x33))
    loading_rect = pixmap.rect().adjusted(0, 170, 0, -80)
    painter.drawText(loading_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "Initializing...")
    
    # Draw bottom credit text
    credit_font = QFont("Courier New", 9)
    painter.setFont(credit_font)
    painter.setPen(QColor(0x8b, 0x8b, 0x7a))
    credit_rect = pixmap.rect().adjusted(0, 280, 0, -30)
    painter.drawText(credit_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "A FMF Tools Production")
    
    # Draw progress bar background
    bar_x, bar_y = 80, 240
    bar_width, bar_height = 340, 20
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(0x2a, 0x2a, 0x28))
    painter.drawRect(bar_x, bar_y, bar_width, bar_height)
    painter.setPen(QColor(0x5c, 0x5c, 0x5c))
    painter.drawRect(bar_x, bar_y, bar_width, bar_height)
    
    # Draw progress bar (indeterminate)
    painter.setBrush(QColor(0x6b, 0x8e, 0x23))
    progress_width = int(bar_width * 0.3)
    progress_x = int((bar_width - progress_width) / 2)
    painter.drawRect(bar_x + progress_x, bar_y + 2, progress_width, bar_height - 4)
    
    painter.end()
    
    return pixmap


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Import MainWindow after QApplication is created to ensure
    # texture generation works properly (texture_system needs QApplication)
    from ui.main_window import MainWindow

    # Set application properties
    app.setApplicationName("Fallout Dialogue Creator")
    app.setApplicationVersion("2.3.0")
    app.setOrganizationName("FMF Tools")

    # Apply Fallout 2 theme before creating any widgets
    from ui.fallout_theme import FalloutUIHelpers
    FalloutUIHelpers.apply_theme(app)

    # Create and show splash screen
    splash_pixmap = create_splash_pixmap()
    splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
    splash.show()
    
    # Force Qt to process events to ensure splash is displayed
    app.processEvents()

    # Initialize core components
    settings = Settings()
    dialog_manager = DialogManager(settings)

    # Notify plugins of app startup
    dialog_manager.plugin_manager.call_hook(PluginHooks.APP_STARTUP, app)

    # Load plugins
    plugin_manager = dialog_manager.plugin_manager
    
    # Use the correct plugins directory based on whether we're frozen or in development
    # The plugin_manager already handles this internally, but we log it for debugging
    plugins_dir = base_path / "plugins"
    logger.info(f"Looking for plugins in: {plugins_dir}")

    # Discover and load all available plugins
    discovered_plugins = plugin_manager.discover_plugins()
    logger.info(f"Discovered {len(discovered_plugins)} plugin(s) in {plugins_dir}")

    for plugin_info in discovered_plugins:
        logger.info(f"Loading plugin: {plugin_info.name} v{plugin_info.version} by {plugin_info.author}")
        try:
            # Find the plugin file - improved matching logic
            plugin_file = None
            plugin_name_normalized = plugin_info.name.lower().replace(' ', '').replace('_', '').replace("'", "")
            
            for py_file in plugins_dir.glob("*.py"):
                # Skip __init__.py and example plugin template
                if py_file.stem in ('__init__', 'example_plugin'):
                    continue
                    
                stem_normalized = py_file.stem.lower()
                # Try exact match first, then normalized match
                if (stem_normalized == plugin_name_normalized or
                    stem_normalized.replace('_', '') == plugin_name_normalized or
                    plugin_name_normalized in stem_normalized or
                    stem_normalized in plugin_name_normalized):
                    plugin_file = py_file
                    break

            # Skip template/example plugins that are intentionally not loaded
            if plugin_info.name in ('Example Plugin',):
                logger.info(f"[SKIPPED] Skipping template plugin: {plugin_info.name}")
            elif plugin_file:
                # Use normalized plugin name for loading
                plugin_key = plugin_info.name.lower().replace(' ', '_').replace('-', '_')
                success = plugin_manager.load_plugin(plugin_key, plugin_file)
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
    
    # Preload textures BEFORE showing window
    # This ensures textures are ready when the window is displayed
    from ui.texture_system import TextureCache
    TextureCache.preload_common_textures()

    # Notify plugins that main window is created
    dialog_manager.plugin_manager.call_hook(PluginHooks.UI_MAIN_WINDOW_CREATED, window)

    # Show window after textures are preloaded
    window.show()

    # Close splash screen after main window is displayed
    splash.finish(window)

    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()