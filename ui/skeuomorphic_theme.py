"""
Skeuomorphic Theme System
Comprehensive skeuomorphic GUI design with realistic materials and depth effects.

Features:
- 5 sophisticated color themes (mahogany/brass, brushed steel/blue, ivory leather/gold, 
  carbon fiber/orange, vintage cream/copper)
- Realistic texturing and material depth effects
- Natural lighting and shadows
- Rich interactive elements with tactile feedback
- Hover, active, and disabled states for all components

Theme Palette:
1. Mahogany Wood with Brass Accents - Warm, rich wood grain with golden brass
2. Brushed Steel with Blue Indicators - Cool industrial metal with electric blue
3. Ivory Leather with Gold Trim - Elegant, luxurious leather with precious gold
4. Carbon Fiber with Orange Highlights - Modern racing aesthetic with fiery orange
5. Vintage Cream with Copper Hardware - Nostalgic warmth with antique copper
"""

import logging
from typing import Dict, Optional, Tuple, Any

from PyQt6.QtGui import (
    QColor, QPalette, QFont, QLinearGradient, QRadialGradient,
    QConicalGradient, QPainter, QPixmap, QImage, QBrush, QPen,
    QLinearGradient, QPainterPath
)
from PyQt6.QtCore import Qt, QSize, QRect, QRectF, QPointF
from PyQt6.QtWidgets import QApplication, QWidget

from ui.texture_system import TextureGenerator

logger = logging.getLogger(__name__)


# =============================================================================
# SKEUOMORPHIC THEME DEFINITIONS
# =============================================================================

class SkeuomorphicTheme:
    """Base class for skeuomorphic themes"""
    
    # Material types
    MATERIAL_WOOD = "wood"
    MATERIAL_METAL = "metal"
    MATERIAL_LEATHER = "leather"
    MATERIAL_GLASS = "glass"
    MATERIAL_CARBON = "carbon"
    MATERIAL_VINTAGE = "vintage"
    
    def __init__(self, theme_name: str, material_type: str):
        self.name = theme_name
        self.material_type = material_type
        self._cached_pixmaps: Dict[str, QPixmap] = {}
        self._cache_lock = False
        
    def get_colors(self) -> Dict[str, str]:
        """Get the color palette for this theme - must be implemented by subclasses"""
        raise NotImplementedError
        
    def get_fonts(self) -> Dict[str, QFont]:
        """Get the font definitions for this theme"""
        fonts = {}
        fonts['ui'] = self._create_ui_font()
        fonts['heading'] = self._create_heading_font()
        fonts['body'] = self._create_body_font()
        fonts['monospace'] = self._create_monospace_font()
        return fonts
    
    def _create_ui_font(self) -> QFont:
        font = QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        font.setBold(True)
        return font
    
    def _create_heading_font(self) -> QFont:
        font = QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(14)
        font.setBold(True)
        return font
    
    def _create_body_font(self) -> QFont:
        font = QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        font.setBold(False)
        return font
    
    def _create_monospace_font(self) -> QFont:
        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(10)
        return font
    
    def get_stylesheet(self) -> str:
        """Get the complete QSS stylesheet for this theme"""
        colors = self.get_colors()
        fonts = self.get_fonts()
        
        return f"""
            /* Base Widget Styles */
            QWidget {{
                background-color: {colors['background']};
                color: {colors['text_primary']};
                font-family: {fonts['ui'].family()};
                font-size: {fonts['ui'].pointSize()}pt;
            }}
            
            /* Main Window */
            QMainWindow {{
                background-color: {colors['background']};
            }}
            
            /* Panels */
            QFrame, QGroupBox {{
                background-color: {colors['panel_background']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
            }}
            
            QGroupBox::title {{
                color: {colors['text_primary']};
                font-weight: bold;
                padding: 4px 8px;
            }}
            
            /* Labels */
            QLabel {{
                color: {colors['text_primary']};
                background: transparent;
            }}
            
            QLabel[heading="true"] {{
                font-size: {fonts['heading'].pointSize()}pt;
                font-weight: bold;
                color: {colors['text_primary']};
            }}
            
            QLabel[secondary="true"] {{
                color: {colors['text_secondary']};
            }}
            
            /* Buttons - Base */
            QPushButton {{
                background-color: {colors['button_background']};
                color: {colors['button_text']};
                border: 2px solid {colors['button_border']};
                border-radius: 6px;
                padding: 8px 16px;
                min-height: 32px;
                font-weight: bold;
            }}
            
            /* Buttons - Hover */
            QPushButton:hover {{
                background-color: {colors['button_hover']};
                border-color: {colors['button_border_hover']};
            }}
            
            /* Buttons - Pressed/Active */
            QPushButton:pressed {{
                background-color: {colors['button_pressed']};
                border-color: {colors['button_border_pressed']};
            }}
            
            /* Buttons - Disabled */
            QPushButton:disabled {{
                background-color: {colors['button_disabled']};
                color: {colors['text_disabled']};
                border-color: {colors['border_disabled']};
            }}
            
            /* Text Inputs */
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {colors['input_background']};
                color: {colors['text_primary']};
                border: 2px solid {colors['input_border']};
                border-radius: 4px;
                padding: 6px 8px;
                selection-background-color: {colors['accent']};
                selection-color: {colors['text_on_accent']};
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border-color: {colors['accent']};
            }}
            
            QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
                background-color: {colors['input_disabled']};
                color: {colors['text_disabled']};
                border-color: {colors['border_disabled']};
            }}
            
            /* ComboBox / Dropdown */
            QComboBox {{
                background-color: {colors['input_background']};
                color: {colors['text_primary']};
                border: 2px solid {colors['input_border']};
                border-radius: 4px;
                padding: 6px 28px 6px 8px;
                min-height: 24px;
            }}
            
            QComboBox:hover {{
                border-color: {colors['accent']};
            }}
            
            QComboBox:focus {{
                border-color: {colors['accent']};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {colors['text_secondary']};
                margin-right: 8px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {colors['dropdown_background']};
                color: {colors['text_primary']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                selection-background-color: {colors['accent']};
                selection-color: {colors['text_on_accent']};
                padding: 4px;
            }}
            
            /* Sliders */
            QSlider::groove:horizontal {{
                background-color: {colors['slider_track']};
                height: 8px;
                border-radius: 4px;
                border: 1px solid {colors['slider_track_border']};
            }}
            
            QSlider::handle:horizontal {{
                background-color: {colors['slider_thumb']};
                border: 2px solid {colors['slider_thumb_border']};
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }}
            
            QSlider::handle:horizontal:hover {{
                background-color: {colors['slider_thumb_hover']};
            }}
            
            QSlider::sub-page:horizontal {{
                background-color: {colors['slider_filled']};
                border-radius: 4px;
            }}
            
            /* Scrollbars */
            QScrollBar:vertical {{
                background-color: {colors['scrollbar_background']};
                width: 14px;
                border-radius: 7px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {colors['scrollbar_thumb']};
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {colors['scrollbar_thumb_hover']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            
            QScrollBar:horizontal {{
                background-color: {colors['scrollbar_background']};
                height: 14px;
                border-radius: 7px;
                margin: 0;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {colors['scrollbar_thumb']};
                border-radius: 6px;
                min-width: 30px;
                margin: 2px;
            }}
            
            /* Checkboxes */
            QCheckBox {{
                color: {colors['text_primary']};
                spacing: 8px;
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {colors['checkbox_border']};
                border-radius: 3px;
                background-color: {colors['checkbox_background']};
            }}
            
            QCheckBox::indicator:hover {{
                border-color: {colors['accent']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {colors['accent']};
                border-color: {colors['accent']};
            }}
            
            /* Radio Buttons */
            QRadioButton {{
                color: {colors['text_primary']};
                spacing: 8px;
            }}
            
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {colors['checkbox_border']};
                border-radius: 9px;
                background-color: {colors['checkbox_background']};
            }}
            
            QRadioButton::indicator:hover {{
                border-color: {colors['accent']};
            }}
            
            QRadioButton::indicator:checked {{
                border-color: {colors['accent']};
            }}
            
            /* Progress Bar */
            QProgressBar {{
                background-color: {colors['progress_background']};
                border: 2px solid {colors['progress_border']};
                border-radius: 6px;
                text-align: center;
                color: {colors['text_primary']};
                font-weight: bold;
            }}
            
            QProgressBar::chunk {{
                background-color: {colors['progress_fill']};
                border-radius: 4px;
            }}
            
            /* Menu Bar */
            QMenuBar {{
                background-color: {colors['menubar_background']};
                color: {colors['text_primary']};
                border-bottom: 2px solid {colors['border']};
                padding: 2px;
            }}
            
            QMenuBar::item:selected {{
                background-color: {colors['accent']};
                color: {colors['text_on_accent']};
            }}
            
            /* Menus */
            QMenu {{
                background-color: {colors['dropdown_background']};
                color: {colors['text_primary']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 4px;
            }}
            
            QMenu::item:selected {{
                background-color: {colors['accent']};
                color: {colors['text_on_accent']};
            }}
            
            /* Tooltips */
            QToolTip {{
                background-color: {colors['tooltip_background']};
                color: {colors['tooltip_text']};
                border: 1px solid {colors['tooltip_border']};
                padding: 4px 8px;
                border-radius: 4px;
            }}
            
            /* Tabs */
            QTabWidget::pane {{
                border: 2px solid {colors['border']};
                border-radius: 4px;
                background-color: {colors['panel_background']};
            }}
            
            QTabBar::tab {{
                background-color: {colors['tab_background']};
                color: {colors['text_secondary']};
                border: 2px solid {colors['border']};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 16px;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {colors['panel_background']};
                color: {colors['text_primary']};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {colors['tab_hover']};
            }}
            
            /* Spin Box */
            QSpinBox, QDoubleSpinBox {{
                background-color: {colors['input_background']};
                color: {colors['text_primary']};
                border: 2px solid {colors['input_border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {colors['accent']};
            }}
            
            QSpinBox::up-button, QDoubleSpinBox::up-button {{
                border-left: 1px solid {colors['input_border']};
                background-color: {colors['button_background']};
            }}
            
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                border-left: 1px solid {colors['input_border']};
                background-color: {colors['button_background']};
            }}
            
            /* Dialogs */
            QDialog {{
                background-color: {colors['background']};
            }}
            
            /* List Widget */
            QListWidget {{
                background-color: {colors['input_background']};
                color: {colors['text_primary']};
                border: 2px solid {colors['input_border']};
                border-radius: 4px;
            }}
            
            QListWidget::item:selected {{
                background-color: {colors['accent']};
                color: {colors['text_on_accent']};
            }}
            
            QListWidget::item:hover {{
                background-color: {colors['button_hover']};
            }}
            
            /* Table Widget */
            QTableWidget {{
                background-color: {colors['input_background']};
                color: {colors['text_primary']};
                border: 2px solid {colors['input_border']};
                gridline-color: {colors['border']};
            }}
            
            QHeaderView::section {{
                background-color: {colors['panel_background']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                padding: 6px;
                font-weight: bold;
            }}
            
            /* Tree Widget */
            QTreeWidget {{
                background-color: {colors['input_background']};
                color: {colors['text_primary']};
                border: 2px solid {colors['input_border']};
            }}
            
            QTreeWidget::item:selected {{
                background-color: {colors['accent']};
                color: {colors['text_on_accent']};
            }}
        """
    
    def get_texture(self, texture_type: str, size: Tuple[int, int] = (256, 256)) -> QPixmap:
        """Get or generate a texture pixmap"""
        cache_key = f"{texture_type}_{size[0]}x{size[1]}"
        
        if cache_key in self._cached_pixmaps:
            return self._cached_pixmaps[cache_key]
        
        # Generate the texture based on type
        pixmap = self._generate_texture(texture_type, size[0], size[1])
        
        if not self._cache_lock:
            self._cached_pixmaps[cache_key] = pixmap
        
        return pixmap
    
    def _generate_texture(self, texture_type: str, width: int, height: int) -> QPixmap:
        """Generate texture based on theme and type"""
        raise NotImplementedError
    
    def clear_cache(self):
        """Clear cached textures"""
        self._cached_pixmaps.clear()


class MahoganyBrassTheme(SkeuomorphicTheme):
    """Warm mahogany wood with brass accents"""
    
    def __init__(self):
        super().__init__("Mahogany & Brass", self.MATERIAL_WOOD)
    
    def get_colors(self) -> Dict[str, str]:
        return {
            # Background colors
            'background': '#1a1210',
            'panel_background': '#2d1f17',
            'surface': '#3d2a1f',
            
            # Border colors
            'border': '#5c3d2e',
            'border_light': '#7a5240',
            'border_dark': '#3d2a1f',
            'border_disabled': '#2d1f17',
            
            # Text colors
            'text_primary': '#e8d4c0',
            'text_secondary': '#b8a080',
            'text_disabled': '#6a5a4a',
            'text_on_accent': '#1a1210',
            
            # Accent colors (Brass gold)
            'accent': '#c9a227',
            'accent_light': '#dbb840',
            'accent_dark': '#a68520',
            
            # Button colors
            'button_background': '#4a3020',
            'button_hover': '#5c3d2e',
            'button_pressed': '#3d2a1f',
            'button_border': '#6a4a35',
            'button_border_hover': '#c9a227',
            'button_border_pressed': '#8a6a45',
            'button_text': '#e8d4c0',
            'button_disabled': '#3d2a1f',
            
            # Input colors
            'input_background': '#2d1f17',
            'input_border': '#5c3d2e',
            'input_disabled': '#1a1210',
            
            # Dropdown colors
            'dropdown_background': '#2d1f17',
            
            # Slider colors
            'slider_track': '#3d2a1f',
            'slider_track_border': '#5c3d2e',
            'slider_thumb': '#c9a227',
            'slider_thumb_border': '#8a6a45',
            'slider_thumb_hover': '#dbb840',
            'slider_filled': '#c9a227',
            
            # Scrollbar colors
            'scrollbar_background': '#2d1f17',
            'scrollbar_thumb': '#5c3d2e',
            'scrollbar_thumb_hover': '#c9a227',
            
            # Checkbox colors
            'checkbox_background': '#2d1f17',
            'checkbox_border': '#5c3d2e',
            
            # Progress colors
            'progress_background': '#2d1f17',
            'progress_border': '#5c3d2e',
            'progress_fill': '#c9a227',
            
            # Menu colors
            'menubar_background': '#2d1f17',
            
            # Tab colors
            'tab_background': '#3d2a1f',
            'tab_hover': '#4a3020',
            
            # Tooltip colors
            'tooltip_background': '#2d1f17',
            'tooltip_text': '#e8d4c0',
            'tooltip_border': '#5c3d2e',
            
            # Special effects
            'highlight': '#c9a227',
            'shadow': '#0a0806',
            'glow': '#c9a22740',
        }
    
    def _generate_texture(self, texture_type: str, width: int, height: int) -> QPixmap:
        """Generate mahogany wood textures"""
        texture_map = {
            'wood': lambda: TextureGenerator.generate_wood_texture(width, height, 'walnut'),
            'wood_light': lambda: TextureGenerator.generate_wood_texture(width, height, 'oak'),
            'metal': lambda: TextureGenerator.generate_metal_texture(width, height, 'brass'),
            'leather': lambda: TextureGenerator.generate_leather_texture(width, height, 'brown'),
            'glass': lambda: TextureGenerator.generate_glass_texture(width, height, 'clear'),
            'panel': lambda: TextureGenerator.generate_wood_texture(width, height, 'walnut'),
        }
        
        if texture_type in texture_map:
            return texture_map[texture_type]()
        
        # Default to wood
        return TextureGenerator.generate_wood_texture(width, height, 'walnut')


class BrushedSteelBlueTheme(SkeuomorphicTheme):
    """Cool brushed steel with blue indicators"""
    
    def __init__(self):
        super().__init__("Brushed Steel & Blue", self.MATERIAL_METAL)
    
    def get_colors(self) -> Dict[str, str]:
        return {
            # Background colors
            'background': '#1a1d21',
            'panel_background': '#2a2f36',
            'surface': '#363c44',
            
            # Border colors
            'border': '#4a5058',
            'border_light': '#5a6068',
            'border_dark': '#1a1d21',
            'border_disabled': '#2a2f36',
            
            # Text colors
            'text_primary': '#e0e4e8',
            'text_secondary': '#9aa0a8',
            'text_disabled': '#5a6068',
            'text_on_accent': '#ffffff',
            
            # Accent colors (Electric Blue)
            'accent': '#3498db',
            'accent_light': '#5dade2',
            'accent_dark': '#2980b9',
            
            # Button colors
            'button_background': '#363c44',
            'button_hover': '#464c54',
            'button_pressed': '#2a2f36',
            'button_border': '#5a6068',
            'button_border_hover': '#3498db',
            'button_border_pressed': '#2980b9',
            'button_text': '#e0e4e8',
            'button_disabled': '#2a2f36',
            
            # Input colors
            'input_background': '#2a2f36',
            'input_border': '#4a5058',
            'input_disabled': '#1a1d21',
            
            # Dropdown colors
            'dropdown_background': '#2a2f36',
            
            # Slider colors
            'slider_track': '#2a2f36',
            'slider_track_border': '#4a5058',
            'slider_thumb': '#3498db',
            'slider_thumb_border': '#2980b9',
            'slider_thumb_hover': '#5dade2',
            'slider_filled': '#3498db',
            
            # Scrollbar colors
            'scrollbar_background': '#2a2f36',
            'scrollbar_thumb': '#4a5058',
            'scrollbar_thumb_hover': '#3498db',
            
            # Checkbox colors
            'checkbox_background': '#2a2f36',
            'checkbox_border': '#4a5058',
            
            # Progress colors
            'progress_background': '#2a2f36',
            'progress_border': '#4a5058',
            'progress_fill': '#3498db',
            
            # Menu colors
            'menubar_background': '#2a2f36',
            
            # Tab colors
            'tab_background': '#363c44',
            'tab_hover': '#464c54',
            
            # Tooltip colors
            'tooltip_background': '#2a2f36',
            'tooltip_text': '#e0e4e8',
            'tooltip_border': '#4a5058',
            
            # Special effects
            'highlight': '#3498db',
            'shadow': '#0a0c0e',
            'glow': '#3498db40',
        }
    
    def _generate_texture(self, texture_type: str, width: int, height: int) -> QPixmap:
        """Generate brushed steel textures"""
        texture_map = {
            'metal': lambda: TextureGenerator.generate_metal_texture(width, height, 'steel'),
            'metal_dark': lambda: TextureGenerator.generate_metal_texture(width, height, 'rust'),
            'metal_light': lambda: TextureGenerator.generate_metal_texture(width, height, 'copper'),
            'glass': lambda: TextureGenerator.generate_glass_texture(width, height, 'frosted'),
            'panel': lambda: TextureGenerator.generate_metal_texture(width, height, 'steel'),
            'carbon': lambda: TextureGenerator.generate_carbon_fiber_texture(width, height),
        }
        
        if texture_type in texture_map:
            return texture_map[texture_type]()
        
        return TextureGenerator.generate_metal_texture(width, height, 'steel')


class IvoryLeatherGoldTheme(SkeuomorphicTheme):
    """Elegant ivory leather with gold trim"""
    
    def __init__(self):
        super().__init__("Ivory Leather & Gold", self.MATERIAL_LEATHER)
    
    def get_colors(self) -> Dict[str, str]:
        return {
            # Background colors
            'background': '#1a1816',
            'panel_background': '#2d2a26',
            'surface': '#3d3832',
            
            # Border colors
            'border': '#5c554a',
            'border_light': '#7a756a',
            'border_dark': '#2d2a26',
            'border_disabled': '#3d3832',
            
            # Text colors
            'text_primary': '#f0e8d8',
            'text_secondary': '#b8a890',
            'text_disabled': '#6a6050',
            'text_on_accent': '#1a1816',
            
            # Accent colors (Gold)
            'accent': '#d4af37',
            'accent_light': '#e8c550',
            'accent_dark': '#b8952a',
            
            # Button colors
            'button_background': '#3d3832',
            'button_hover': '#4d4840',
            'button_pressed': '#2d2a26',
            'button_border': '#6a6050',
            'button_border_hover': '#d4af37',
            'button_border_pressed': '#a89030',
            'button_text': '#f0e8d8',
            'button_disabled': '#2d2a26',
            
            # Input colors
            'input_background': '#2d2a26',
            'input_border': '#5c554a',
            'input_disabled': '#1a1816',
            
            # Dropdown colors
            'dropdown_background': '#2d2a26',
            
            # Slider colors
            'slider_track': '#2d2a26',
            'slider_track_border': '#5c554a',
            'slider_thumb': '#d4af37',
            'slider_thumb_border': '#a89030',
            'slider_thumb_hover': '#e8c550',
            'slider_filled': '#d4af37',
            
            # Scrollbar colors
            'scrollbar_background': '#2d2a26',
            'scrollbar_thumb': '#5c554a',
            'scrollbar_thumb_hover': '#d4af37',
            
            # Checkbox colors
            'checkbox_background': '#2d2a26',
            'checkbox_border': '#5c554a',
            
            # Progress colors
            'progress_background': '#2d2a26',
            'progress_border': '#5c554a',
            'progress_fill': '#d4af37',
            
            # Menu colors
            'menubar_background': '#2d2a26',
            
            # Tab colors
            'tab_background': '#3d3832',
            'tab_hover': '#4d4840',
            
            # Tooltip colors
            'tooltip_background': '#2d2a26',
            'tooltip_text': '#f0e8d8',
            'tooltip_border': '#5c554a',
            
            # Special effects
            'highlight': '#d4af37',
            'shadow': '#0a0908',
            'glow': '#d4af3740',
        }
    
    def _generate_texture(self, texture_type: str, width: int, height: int) -> QPixmap:
        """Generate ivory leather textures"""
        texture_map = {
            'leather': lambda: TextureGenerator.generate_leather_texture(width, height, 'brown'),
            'leather_light': lambda: TextureGenerator.generate_leather_texture(width, height, 'brown'),
            'metal': lambda: TextureGenerator.generate_metal_texture(width, height, 'brass'),
            'glass': lambda: TextureGenerator.generate_glass_texture(width, height, 'frosted'),
            'panel': lambda: TextureGenerator.generate_leather_texture(width, height, 'brown'),
        }
        
        if texture_type in texture_map:
            return texture_map[texture_type]()
        
        return TextureGenerator.generate_leather_texture(width, height, 'brown')


class CarbonFiberOrangeTheme(SkeuomorphicTheme):
    """Modern carbon fiber with orange highlights"""
    
    def __init__(self):
        super().__init__("Carbon Fiber & Orange", self.MATERIAL_CARBON)
    
    def get_colors(self) -> Dict[str, str]:
        return {
            # Background colors
            'background': '#0d0d0d',
            'panel_background': '#1a1a1a',
            'surface': '#2a2a2a',
            
            # Border colors
            'border': '#3a3a3a',
            'border_light': '#4a4a4a',
            'border_dark': '#0d0d0d',
            'border_disabled': '#1a1a1a',
            
            # Text colors
            'text_primary': '#e8e8e8',
            'text_secondary': '#a0a0a0',
            'text_disabled': '#505050',
            'text_on_accent': '#0d0d0d',
            
            # Accent colors (Orange)
            'accent': '#e65c00',
            'accent_light': '#ff7a33',
            'accent_dark': '#cc4400',
            
            # Button colors
            'button_background': '#2a2a2a',
            'button_hover': '#3a3a3a',
            'button_pressed': '#1a1a1a',
            'button_border': '#4a4a4a',
            'button_border_hover': '#e65c00',
            'button_border_pressed': '#cc4400',
            'button_text': '#e8e8e8',
            'button_disabled': '#1a1a1a',
            
            # Input colors
            'input_background': '#1a1a1a',
            'input_border': '#3a3a3a',
            'input_disabled': '#0d0d0d',
            
            # Dropdown colors
            'dropdown_background': '#1a1a1a',
            
            # Slider colors
            'slider_track': '#1a1a1a',
            'slider_track_border': '#3a3a3a',
            'slider_thumb': '#e65c00',
            'slider_thumb_border': '#cc4400',
            'slider_thumb_hover': '#ff7a33',
            'slider_filled': '#e65c00',
            
            # Scrollbar colors
            'scrollbar_background': '#1a1a1a',
            'scrollbar_thumb': '#3a3a3a',
            'scrollbar_thumb_hover': '#e65c00',
            
            # Checkbox colors
            'checkbox_background': '#1a1a1a',
            'checkbox_border': '#3a3a3a',
            
            # Progress colors
            'progress_background': '#1a1a1a',
            'progress_border': '#3a3a3a',
            'progress_fill': '#e65c00',
            
            # Menu colors
            'menubar_background': '#1a1a1a',
            
            # Tab colors
            'tab_background': '#2a2a2a',
            'tab_hover': '#3a3a3a',
            
            # Tooltip colors
            'tooltip_background': '#1a1a1a',
            'tooltip_text': '#e8e8e8',
            'tooltip_border': '#3a3a3a',
            
            # Special effects
            'highlight': '#e65c00',
            'shadow': '#000000',
            'glow': '#e65c0040',
        }
    
    def _generate_texture(self, texture_type: str, width: int, height: int) -> QPixmap:
        """Generate carbon fiber textures"""
        texture_map = {
            'carbon': lambda: TextureGenerator.generate_carbon_fiber_texture(width, height),
            'carbon_clear': lambda: TextureGenerator.generate_carbon_fiber_texture(width, height, False),
            'metal': lambda: TextureGenerator.generate_metal_texture(width, height, 'steel'),
            'glass': lambda: TextureGenerator.generate_glass_texture(width, height, 'clear'),
            'panel': lambda: TextureGenerator.generate_carbon_fiber_texture(width, height),
        }
        
        if texture_type in texture_map:
            return texture_map[texture_type]()
        
        return TextureGenerator.generate_carbon_fiber_texture(width, height)


class VintageCreamCopperTheme(SkeuomorphicTheme):
    """Vintage cream with copper hardware"""
    
    def __init__(self):
        super().__init__("Vintage Cream & Copper", self.MATERIAL_VINTAGE)
    
    def get_colors(self) -> Dict[str, str]:
        return {
            # Background colors
            'background': '#1a1814',
            'panel_background': '#2d2820',
            'surface': '#3d3428',
            
            # Border colors
            'border': '#5c4a38',
            'border_light': '#7a6250',
            'border_dark': '#2d2820',
            'border_disabled': '#3d3428',
            
            # Text colors
            'text_primary': '#e8d8c0',
            'text_secondary': '#b8a080',
            'text_disabled': '#6a5a48',
            'text_on_accent': '#1a1814',
            
            # Accent colors (Copper)
            'accent': '#b87333',
            'accent_light': '#d49550',
            'accent_dark': '#9a5a28',
            
            # Button colors
            'button_background': '#3d3428',
            'button_hover': '#4d4438',
            'button_pressed': '#2d2820',
            'button_border': '#6a5a48',
            'button_border_hover': '#b87333',
            'button_border_pressed': '#9a5a28',
            'button_text': '#e8d8c0',
            'button_disabled': '#2d2820',
            
            # Input colors
            'input_background': '#2d2820',
            'input_border': '#5c4a38',
            'input_disabled': '#1a1814',
            
            # Dropdown colors
            'dropdown_background': '#2d2820',
            
            # Slider colors
            'slider_track': '#2d2820',
            'slider_track_border': '#5c4a38',
            'slider_thumb': '#b87333',
            'slider_thumb_border': '#9a5a28',
            'slider_thumb_hover': '#d49550',
            'slider_filled': '#b87333',
            
            # Scrollbar colors
            'scrollbar_background': '#2d2820',
            'scrollbar_thumb': '#5c4a38',
            'scrollbar_thumb_hover': '#b87333',
            
            # Checkbox colors
            'checkbox_background': '#2d2820',
            'checkbox_border': '#5c4a38',
            
            # Progress colors
            'progress_background': '#2d2820',
            'progress_border': '#5c4a38',
            'progress_fill': '#b87333',
            
            # Menu colors
            'menubar_background': '#2d2820',
            
            # Tab colors
            'tab_background': '#3d3428',
            'tab_hover': '#4d4438',
            
            # Tooltip colors
            'tooltip_background': '#2d2820',
            'tooltip_text': '#e8d8c0',
            'tooltip_border': '#5c4a38',
            
            # Special effects
            'highlight': '#b87333',
            'shadow': '#0a0908',
            'glow': '#b8733340',
        }
    
    def _generate_texture(self, texture_type: str, width: int, height: int) -> QPixmap:
        """Generate vintage cream textures"""
        texture_map = {
            'wood': lambda: TextureGenerator.generate_wood_texture(width, height, 'pine'),
            'wood_light': lambda: TextureGenerator.generate_wood_texture(width, height, 'oak'),
            'metal': lambda: TextureGenerator.generate_metal_texture(width, height, 'copper'),
            'leather': lambda: TextureGenerator.generate_leather_texture(width, height, 'brown'),
            'glass': lambda: TextureGenerator.generate_glass_texture(width, height, 'frosted'),
            'panel': lambda: TextureGenerator.generate_wood_texture(width, height, 'pine'),
        }
        
        if texture_type in texture_map:
            return texture_map[texture_type]()
        
        return TextureGenerator.generate_wood_texture(width, height, 'pine')


# =============================================================================
# THEME MANAGER
# =============================================================================

class SkeuomorphicThemeManager:
    """Manages skeuomorphic theme selection and application"""
    
    THEMES = {
        'mahogany': MahoganyBrassTheme,
        'steel': BrushedSteelBlueTheme,
        'ivory': IvoryLeatherGoldTheme,
        'carbon': CarbonFiberOrangeTheme,
        'vintage': VintageCreamCopperTheme,
    }
    
    THEME_DISPLAY_NAMES = {
        'mahogany': 'Mahogany & Brass',
        'steel': 'Brushed Steel & Blue',
        'ivory': 'Ivory Leather & Gold',
        'carbon': 'Carbon Fiber & Orange',
        'vintage': 'Vintage Cream & Copper',
    }
    
    def __init__(self):
        self._current_theme: Optional[SkeuomorphicTheme] = None
        self._current_theme_key: Optional[str] = None
        
    def set_theme(self, theme_key: str) -> bool:
        """Set the current theme by key"""
        if theme_key not in self.THEMES:
            logger.error(f"Unknown theme key: {theme_key}")
            return False
        
        try:
            self._current_theme = self.THEMES[theme_key]()
            self._current_theme_key = theme_key
            logger.info(f"Theme set to: {self.THEME_DISPLAY_NAMES.get(theme_key, theme_key)}")
            return True
        except Exception as e:
            logger.error(f"Failed to create theme: {e}")
            return False
    
    def get_current_theme(self) -> Optional[SkeuomorphicTheme]:
        """Get the current theme instance"""
        return self._current_theme
    
    def get_current_theme_key(self) -> Optional[str]:
        """Get the current theme key"""
        return self._current_theme_key
    
    def get_available_themes(self) -> Dict[str, str]:
        """Get all available themes with their display names"""
        return self.THEME_DISPLAY_NAMES.copy()
    
    def get_stylesheet(self) -> str:
        """Get the stylesheet for the current theme"""
        if self._current_theme:
            return self._current_theme.get_stylesheet()
        return ""
    
    def apply_to_app(self, app: QApplication):
        """Apply the current theme to the application"""
        stylesheet = self.get_stylesheet()
        if stylesheet:
            app.setStyleSheet(stylesheet)


# Global theme manager instance
_theme_manager = SkeuomorphicThemeManager()


def get_theme_manager() -> SkeuomorphicThemeManager:
    """Get the global theme manager"""
    return _theme_manager


def set_skeuomorphic_theme(theme_key: str) -> bool:
    """Convenience function to set the theme"""
    return _theme_manager.set_theme(theme_key)


def get_current_skeuomorphic_theme() -> Optional[SkeuomorphicTheme]:
    """Get the current theme"""
    return _theme_manager.get_current_theme()


def apply_skeuomorphic_theme(app: QApplication):
    """Apply the current theme to the application"""
    _theme_manager.apply_to_app(app)