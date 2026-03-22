"""
Theme Manager for Fallout Dialogue Creator
Manages theme discovery, loading, switching, and persistence
"""

import logging
import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, QFileSystemWatcher
from PyQt6.QtGui import QColor, QPalette, QFont

from core.settings import Settings

logger = logging.getLogger(__name__)


class ThemeCategory(Enum):
    """Theme categorization for filtering"""
    FALLOUT = "fallout"
    SKEUOMORPHIC = "skeuomorphic"
    MODERN = "modern"
    DARK = "dark"
    LIGHT = "light"
    COLORFUL = "colorful"
    CUSTOM = "custom"


class ThemeError(Exception):
    """Base exception for theme-related errors"""
    pass


class ThemeLoadError(ThemeError):
    """Error loading a theme file"""
    pass


class ThemeValidationError(ThemeError):
    """Theme validation failed"""
    pass


class ThemeMissingError(ThemeError):
    """Theme file is missing"""
    pass


@dataclass
class Theme:
    """
    Theme data model with validation and error handling
    """
    id: str
    name: str
    category: ThemeCategory = ThemeCategory.FALLOUT
    author: str = "Unknown"
    version: str = "1.0.0"
    description: str = ""
    
    # Color definitions
    primary_color: str = "#6b8e23"
    secondary_color: str = "#b7410e"
    background_color: str = "#1a1a1a"
    text_color: str = "#c4b998"
    accent_color: str = "#ffcc00"
    border_color: str = "#5c5c5c"
    highlight_color: str = "#33ff33"
    
    # Additional colors
    panel_background: str = "#2a2a28"
    panel_border: str = "#5c5c5c"
    terminal_green: str = "#33ff33"
    warning_color: str = "#cc3333"
    
    # File path
    file_path: Optional[Path] = None
    
    # Preview data (for thumbnails)
    preview_colors: List[str] = field(default_factory=list)
    
    # Metadata
    is_builtin: bool = False
    is_compatible: bool = True
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate theme after initialization"""
        self._validate()
    
    def _validate(self):
        """Validate theme data"""
        if not self.id:
            raise ThemeValidationError("Theme ID cannot be empty")
        if not self.name:
            raise ThemeValidationError("Theme name cannot be empty")
        
        # Validate hex colors
        for color_name in ['primary_color', 'secondary_color', 'background_color', 
                          'text_color', 'accent_color', 'border_color', 'highlight_color',
                          'panel_background', 'panel_border', 'terminal_green', 'warning_color']:
            color_value = getattr(self, color_name, None)
            if color_value and not self._is_valid_hex(color_value):
                logger.warning(f"Invalid hex color for {color_name}: {color_value}")
        
        # Generate preview colors if not set
        if not self.preview_colors:
            self.preview_colors = [
                self.primary_color,
                self.secondary_color,
                self.background_color,
                self.accent_color
            ]
    
    @staticmethod
    def _is_valid_hex(color: str) -> bool:
        """Check if color is valid hex format"""
        if not color:
            return False
        color = color.strip('#')
        return len(color) == 6 and all(c in '0123456789abcdefABCDEF' for c in color)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert theme to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.value,
            'author': self.author,
            'version': self.version,
            'description': self.description,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'background_color': self.background_color,
            'text_color': self.text_color,
            'accent_color': self.accent_color,
            'border_color': self.border_color,
            'highlight_color': self.highlight_color,
            'panel_background': self.panel_background,
            'panel_border': self.panel_border,
            'terminal_green': self.terminal_green,
            'warning_color': self.warning_color,
            'preview_colors': self.preview_colors,
            'is_builtin': self.is_builtin,
            'is_compatible': self.is_compatible,
            'file_path': str(self.file_path) if self.file_path else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Theme':
        """Create theme from dictionary"""
        # Handle category
        category = ThemeCategory.FALLOUT
        if 'category' in data:
            try:
                category = ThemeCategory(data['category'])
            except ValueError:
                logger.warning(f"Unknown theme category: {data['category']}")
        
        # Handle file_path
        file_path = None
        if data.get('file_path'):
            file_path = Path(data['file_path'])
        
        return cls(
            id=data.get('id', ''),
            name=data.get('name', 'Unnamed Theme'),
            category=category,
            author=data.get('author', 'Unknown'),
            version=data.get('version', '1.0.0'),
            description=data.get('description', ''),
            primary_color=data.get('primary_color', '#6b8e23'),
            secondary_color=data.get('secondary_color', '#b7410e'),
            background_color=data.get('background_color', '#1a1a1a'),
            text_color=data.get('text_color', '#c4b998'),
            accent_color=data.get('accent_color', '#ffcc00'),
            border_color=data.get('border_color', '#5c5c5c'),
            highlight_color=data.get('highlight_color', '#33ff33'),
            panel_background=data.get('panel_background', '#2a2a28'),
            panel_border=data.get('panel_border', '#5c5c5c'),
            terminal_green=data.get('terminal_green', '#33ff33'),
            warning_color=data.get('warning_color', '#cc3333'),
            preview_colors=data.get('preview_colors', []),
            file_path=file_path,
            is_builtin=data.get('is_builtin', False),
            is_compatible=data.get('is_compatible', True)
        )
    
    @classmethod
    def from_file(cls, file_path: Path) -> 'Theme':
        """Load theme from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            theme = cls.from_dict(data)
            theme.file_path = file_path
            return theme
            
        except FileNotFoundError:
            raise ThemeMissingError(f"Theme file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ThemeLoadError(f"Invalid JSON in theme file: {e}")
        except Exception as e:
            raise ThemeLoadError(f"Error loading theme: {e}")
    
    def save_to_file(self, file_path: Optional[Path] = None):
        """Save theme to JSON file"""
        path = file_path or self.file_path
        if not path:
            raise ThemeError("No file path specified")
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=4)
        
        self.file_path = path


class ThemeManager(QObject):
    """
    Theme Manager - handles theme discovery, loading, switching, and persistence
    """
    
    # Signals
    theme_changed = pyqtSignal(str)  # Emitted when active theme changes
    themes_updated = pyqtSignal()    # Emitted when theme list is updated
    theme_error = pyqtSignal(str)    # Emitted on theme error
    
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self._themes: Dict[str, Theme] = {}
        self._active_theme_id: Optional[str] = None
        self._file_watcher: Optional[QFileSystemWatcher] = None
        self._themes_directory: Optional[Path] = None
        self._custom_apply_callback: Optional[Callable] = None
        
        # Initialize built-in themes
        self._register_builtin_themes()
        
        # Setup themes directory
        self._setup_themes_directory()
        
        # Load saved theme preference
        self._load_saved_theme()
        
        # Setup file watcher for auto-detection
        self._setup_file_watcher()
    
    def _register_builtin_themes(self):
        """Register built-in themes"""
        # Fallout theme (default)
        fallout_theme = Theme(
            id="fallout",
            name="Fallout 2",
            category=ThemeCategory.FALLOUT,
            author="FMF Tools",
            version="2.3.0",
            description="Authentic Fallout 2 post-apocalyptic aesthetic",
            primary_color="#6b8e23",
            secondary_color="#b7410e",
            background_color="#1a1a1a",
            text_color="#c4b998",
            accent_color="#ffcc00",
            border_color="#5c5c5c",
            highlight_color="#33ff33",
            panel_background="#2a2a28",
            panel_border="#5c5c5c",
            terminal_green="#33ff33",
            warning_color="#cc3333",
            is_builtin=True
        )
        self._themes[fallout_theme.id] = fallout_theme
        
        # Skeuomorphic theme
        skeuomorphic_theme = Theme(
            id="skeuomorphic",
            name="Skeuomorphic",
            category=ThemeCategory.SKEUOMORPHIC,
            author="FMF Tools",
            version="2.3.0",
            description="Classic skeuomorphic design with depth and texture",
            primary_color="#4a90d9",
            secondary_color="#d4a017",
            background_color="#e8e8e8",
            text_color="#333333",
            accent_color="#0078d7",
            border_color="#aaaaaa",
            highlight_color="#0078d7",
            panel_background="#f0f0f0",
            panel_border="#cccccc",
            terminal_green="#00aa00",
            warning_color="#cc0000",
            is_builtin=True
        )
        self._themes[skeuomorphic_theme.id] = skeuomorphic_theme
        
        # Dark theme
        dark_theme = Theme(
            id="dark",
            name="Dark Mode",
            category=ThemeCategory.DARK,
            author="FMF Tools",
            version="2.3.0",
            description="Modern dark theme for low-light environments",
            primary_color="#3a3a3a",
            secondary_color="#6b8e23",
            background_color="#1e1e1e",
            text_color="#d4d4d4",
            accent_color="#569cd6",
            border_color="#3a3a3a",
            highlight_color="#4ec9b0",
            panel_background="#252526",
            panel_border="#3a3a3a",
            terminal_green="#6a9955",
            warning_color="#f44747",
            is_builtin=True
        )
        self._themes[dark_theme.id] = dark_theme
        
        # Light theme
        light_theme = Theme(
            id="light",
            name="Light Mode",
            category=ThemeCategory.LIGHT,
            author="FMF Tools",
            version="2.3.0",
            description="Clean light theme for daytime use",
            primary_color="#007acc",
            secondary_color="#e51400",
            background_color="#ffffff",
            text_color="#333333",
            accent_color="#0078d7",
            border_color="#cccccc",
            highlight_color="#001080",
            panel_background="#f3f3f3",
            panel_border="#e1e1e1",
            terminal_green="#008000",
            warning_color="#e51400",
            is_builtin=True
        )
        self._themes[light_theme.id] = light_theme
        
        # Midnight theme
        midnight_theme = Theme(
            id="midnight",
            name="Midnight",
            category=ThemeCategory.DARK,
            author="FMF Tools",
            version="2.3.0",
            description="Deep blue-black theme with neon accents",
            primary_color="#1e3a5f",
            secondary_color="#ff6b6b",
            background_color="#0a0e17",
            text_color="#a0a0a0",
            accent_color="#00d4ff",
            border_color="#1e3a5f",
            highlight_color="#00d4ff",
            panel_background="#0d1526",
            panel_border="#1e3a5f",
            terminal_green="#00ff88",
            warning_color="#ff4757",
            is_builtin=True
        )
        self._themes[midnight_theme.id] = midnight_theme
        
        # Matrix theme
        matrix_theme = Theme(
            id="matrix",
            name="Matrix",
            category=ThemeCategory.COLORFUL,
            author="FMF Tools",
            version="2.3.0",
            description="Classic green-on-black terminal aesthetic",
            primary_color="#00ff00",
            secondary_color="#008800",
            background_color="#000000",
            text_color="#00ff00",
            accent_color="#00ff00",
            border_color="#003300",
            highlight_color="#00ff00",
            panel_background="#001100",
            panel_border="#003300",
            terminal_green="#00ff00",
            warning_color="#ff0000",
            is_builtin=True
        )
        self._themes[matrix_theme.id] = matrix_theme
        
        logger.info(f"Registered {len(self._themes)} built-in themes")
    
    def _setup_themes_directory(self):
        """Setup the themes directory for custom themes"""
        base_path = self.settings.get_base_path()
        self._themes_directory = base_path / "themes"
        self._themes_directory.mkdir(parents=True, exist_ok=True)
        
        # Create default theme file for customization
        default_theme_file = self._themes_directory / "custom_theme.json"
        if not default_theme_file.exists():
            # Create a sample custom theme
            custom_theme = Theme(
                id="custom",
                name="Custom Theme",
                category=ThemeCategory.CUSTOM,
                author="User",
                version="1.0.0",
                description="User-created custom theme"
            )
            custom_theme.save_to_file(default_theme_file)
        
        # Scan for custom themes
        self._scan_custom_themes()
    
    def _scan_custom_themes(self):
        """Scan for custom themes in the themes directory"""
        if not self._themes_directory:
            return
        
        for theme_file in self._themes_directory.glob("*.json"):
            try:
                theme = Theme.from_file(theme_file)
                # Only add if not already registered (custom themes override)
                if theme.id not in self._themes or theme.id == "custom":
                    self._themes[theme.id] = theme
                    logger.info(f"Loaded custom theme: {theme.name} from {theme_file}")
            except ThemeError as e:
                logger.error(f"Error loading theme {theme_file}: {e}")
                # Create a placeholder theme with error state
                error_theme = Theme(
                    id=theme_file.stem,
                    name=theme_file.stem,
                    category=ThemeCategory.CUSTOM,
                    is_compatible=False,
                    error_message=str(e)
                )
                self._themes[error_theme.id] = error_theme
            except Exception as e:
                logger.error(f"Unexpected error loading theme {theme_file}: {e}")
        
        self.themes_updated.emit()
    
    def _setup_file_watcher(self):
        """Setup file system watcher for automatic theme detection"""
        if not self._themes_directory:
            return
        
        self._file_watcher = QFileSystemWatcher()
        self._file_watcher.addPath(str(self._themes_directory))
        self._file_watcher.fileChanged.connect(self._on_theme_directory_changed)
        logger.info(f"Watching themes directory: {self._themes_directory}")
    
    def _on_theme_directory_changed(self, path: str):
        """Handle changes to the themes directory"""
        logger.info(f"Theme directory changed: {path}")
        # Debounce: wait a bit before rescanning
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, self.refresh_themes)
    
    def _load_saved_theme(self):
        """Load the saved theme preference"""
        saved_theme_id = self.settings.get('theme', 'fallout')
        if saved_theme_id in self._themes:
            self._active_theme_id = saved_theme_id
            logger.info(f"Loaded saved theme: {saved_theme_id}")
        else:
            self._active_theme_id = 'fallout'
            logger.warning(f"Saved theme '{saved_theme_id}' not found, using default")
    
    def get_themes(self) -> List[Theme]:
        """Get all available themes"""
        return list(self._themes.values())
    
    def get_theme(self, theme_id: str) -> Optional[Theme]:
        """Get a specific theme by ID"""
        return self._themes.get(theme_id)
    
    def get_active_theme(self) -> Optional[Theme]:
        """Get the currently active theme"""
        if self._active_theme_id:
            return self._themes.get(self._active_theme_id)
        return None
    
    def get_active_theme_id(self) -> Optional[str]:
        """Get the ID of the currently active theme"""
        return self._active_theme_id
    
    def set_active_theme(self, theme_id: str) -> bool:
        """Set the active theme"""
        if theme_id not in self._themes:
            logger.error(f"Theme not found: {theme_id}")
            self.theme_error.emit(f"Theme not found: {theme_id}")
            return False
        
        theme = self._themes[theme_id]
        
        # Check if theme is compatible
        if not theme.is_compatible:
            error_msg = theme.error_message or "Theme is not compatible"
            logger.error(f"Cannot activate theme {theme_id}: {error_msg}")
            self.theme_error.emit(error_msg)
            return False
        
        # Save to settings
        self.settings.set('theme', theme_id)
        self._active_theme_id = theme_id
        
        # Apply theme
        self._apply_theme(theme)
        
        # Emit signal
        self.theme_changed.emit(theme_id)
        logger.info(f"Activated theme: {theme.name}")
        return True
    
    def _apply_theme(self, theme: Theme):
        """Apply theme to the application"""
        # Use custom callback if set
        if self._custom_apply_callback:
            self._custom_apply_callback(theme)
        else:
            # Default: apply Fallout theme
            self._apply_fallout_style(theme)
    
    def _apply_fallout_style(self, theme: Theme):
        """Apply theme using Fallout style system"""
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if not app:
                return
            
            # Apply palette
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor(theme.background_color))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(theme.text_color))
            palette.setColor(QPalette.ColorRole.Base, QColor(theme.panel_background))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(theme.background_color))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(theme.panel_background))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(theme.text_color))
            palette.setColor(QPalette.ColorRole.Text, QColor(theme.text_color))
            palette.setColor(QPalette.ColorRole.Button, QColor(theme.panel_background))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme.text_color))
            palette.setColor(QPalette.ColorRole.BrightText, QColor(theme.highlight_color))
            palette.setColor(QPalette.ColorRole.Link, QColor(theme.accent_color))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(theme.primary_color))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(theme.text_color))
            
            app.setPalette(palette)
            
            # Apply stylesheet
            stylesheet = f"""
                QMainWindow {{
                    background-color: {theme.background_color};
                    color: {theme.text_color};
                }}
                QWidget {{
                    background-color: {theme.background_color};
                    color: {theme.text_color};
                }}
                QMenuBar {{
                    background-color: {theme.panel_background};
                    color: {theme.text_color};
                    border-bottom: 2px solid {theme.border_color};
                }}
                QMenuBar::item:selected {{
                    background-color: {theme.primary_color};
                    color: {theme.accent_color};
                }}
                QMenu {{
                    background-color: {theme.panel_background};
                    color: {theme.text_color};
                    border: 2px solid {theme.border_color};
                }}
                QMenu::item:selected {{
                    background-color: {theme.primary_color};
                    color: {theme.accent_color};
                }}
                QPushButton {{
                    background-color: {theme.panel_background};
                    color: {theme.text_color};
                    border: 2px solid {theme.border_color};
                    padding: 6px 12px;
                }}
                QPushButton:hover {{
                    background-color: {theme.primary_color};
                    color: {theme.accent_color};
                }}
                QPushButton:pressed {{
                    background-color: {theme.secondary_color};
                }}
                QLineEdit, QTextEdit, QPlainTextEdit {{
                    background-color: {theme.panel_background};
                    color: {theme.text_color};
                    border: 2px solid {theme.border_color};
                }}
                QTreeWidget, QListWidget {{
                    background-color: {theme.panel_background};
                    color: {theme.text_color};
                    border: 2px solid {theme.border_color};
                }}
                QLabel {{
                    color: {theme.text_color};
                }}
                QStatusBar {{
                    background-color: {theme.panel_background};
                    color: {theme.text_color};
                }}
                QTabWidget::pane {{
                    border: 2px solid {theme.border_color};
                    background-color: {theme.background_color};
                }}
                QTabBar::tab {{
                    background-color: {theme.panel_background};
                    color: {theme.text_color};
                    border: 2px solid {theme.border_color};
                    padding: 6px 12px;
                }}
                QTabBar::tab:selected {{
                    background-color: {theme.primary_color};
                    color: {theme.accent_color};
                }}
                QScrollBar:vertical {{
                    background-color: {theme.panel_background};
                    border: 1px solid {theme.border_color};
                }}
                QScrollBar::handle:vertical {{
                    background-color: {theme.primary_color};
                }}
                QScrollBar:horizontal {{
                    background-color: {theme.panel_background};
                    border: 1px solid {theme.border_color};
                }}
                QScrollBar::handle:horizontal {{
                    background-color: {theme.primary_color};
                }}
            """
            app.setStyleSheet(stylesheet)
            
            logger.info(f"Applied theme stylesheet: {theme.name}")
            
        except Exception as e:
            logger.error(f"Error applying theme: {e}")
            self.theme_error.emit(f"Error applying theme: {e}")
    
    def set_custom_apply_callback(self, callback: Callable[[Theme], None]):
        """Set a custom callback for applying themes"""
        self._custom_apply_callback = callback
    
    def filter_themes(self, category: Optional[ThemeCategory] = None, 
                      search_text: str = "") -> List[Theme]:
        """Filter themes by category and/or search text"""
        themes = self.get_themes()
        
        if category:
            themes = [t for t in themes if t.category == category]
        
        if search_text:
            search_lower = search_text.lower()
            themes = [t for t in themes if 
                     search_lower in t.name.lower() or 
                     search_lower in t.description.lower() or
                     search_lower in t.author.lower()]
        
        return themes
    
    def get_categories(self) -> List[ThemeCategory]:
        """Get all available theme categories"""
        categories = set()
        for theme in self._themes.values():
            categories.add(theme.category)
        return sorted(categories, key=lambda c: c.value)
    
    def refresh_themes(self):
        """Refresh the theme list - reloads all themes"""
        logger.info("Refreshing theme list...")
        
        # Re-register built-in themes
        self._themes.clear()
        self._register_builtin_themes()
        
        # Rescan custom themes
        self._scan_custom_themes()
        
        # Ensure active theme still exists
        if self._active_theme_id not in self._themes:
            self._active_theme_id = 'fallout'
            self.set_active_theme(self._active_theme_id)
        
        self.themes_updated.emit()
        logger.info(f"Theme refresh complete. Total themes: {len(self._themes)}")
    
    def create_theme(self, name: str, category: ThemeCategory = ThemeCategory.CUSTOM,
                     **colors) -> Theme:
        """Create a new custom theme"""
        theme_id = name.lower().replace(' ', '_').replace('-', '_')
        
        # Ensure unique ID
        base_id = theme_id
        counter = 1
        while theme_id in self._themes:
            theme_id = f"{base_id}_{counter}"
            counter += 1
        
        theme = Theme(
            id=theme_id,
            name=name,
            category=category,
            author="User",
            version="1.0.0",
            description="User-created custom theme",
            **colors
        )
        
        # Save to file
        if self._themes_directory:
            theme_file = self._themes_directory / f"{theme_id}.json"
            theme.save_to_file(theme_file)
        
        # Add to registry
        self._themes[theme.id] = theme
        self.themes_updated.emit()
        
        return theme
    
    def delete_theme(self, theme_id: str) -> bool:
        """Delete a custom theme"""
        if theme_id not in self._themes:
            return False
        
        theme = self._themes[theme_id]
        
        # Don't allow deleting built-in themes
        if theme.is_builtin:
            logger.warning(f"Cannot delete built-in theme: {theme_id}")
            return False
        
        # Delete file if exists
        if theme.file_path and theme.file_path.exists():
            try:
                theme.file_path.unlink()
            except Exception as e:
                logger.error(f"Error deleting theme file: {e}")
        
        # Remove from registry
        del self._themes[theme_id]
        
        # If this was the active theme, switch to default
        if self._active_theme_id == theme_id:
            self.set_active_theme('fallout')
        
        self.themes_updated.emit()
        return True
    
    def get_themes_directory(self) -> Optional[Path]:
        """Get the themes directory path"""
        return self._themes_directory


# Singleton instance
_theme_manager_instance: Optional[ThemeManager] = None


def get_theme_manager(settings: Settings) -> ThemeManager:
    """Get or create the theme manager singleton"""
    global _theme_manager_instance
    if _theme_manager_instance is None:
        _theme_manager_instance = ThemeManager(settings)
    return _theme_manager_instance
