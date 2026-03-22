"""
GUI Texture Applicator System
Automatically applies procedurally generated textures to all GUI elements.

Features:
- Automatic texture mapping based on widget type
- State-based textures (normal, hover, pressed, disabled)
- Visual hierarchy support (parent panels vs child elements)
- Performance optimization through caching and lazy loading
- Seamless integration with existing Fallout widgets
"""

import logging
import sys
from typing import Dict, Optional, Tuple, Any, List, Type
from enum import Enum, auto
import threading

from PyQt6.QtWidgets import (
    QWidget, QPushButton, QFrame, QLabel, QLineEdit, QTextEdit,
    QListWidget, QTreeWidget, QTabWidget, QScrollArea, QGroupBox,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QRadioButton,
    QSlider, QProgressBar, QToolButton, QMenu, QMenuBar, QStatusBar,
    QToolBar, QSplitter, QStackedWidget, QDial, QApplication
)
from PyQt6.QtCore import Qt, QEvent, QObject, QRect, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QPainter, QPixmap, QImage, QColor, QBrush, QPalette, QFont,
    QEnterEvent, QPaintEvent, QResizeEvent, QMouseEvent
)

from ui.texture_system import (
    TextureGenerator, TextureStyle, TextureCache, TexturePainter,
    ResolutionVariant, _ensure_qapplication, SolidColorPainter
)


# =============================================================================
# VISUAL HIERARCHY LEVELS
# =============================================================================

class HierarchyLevel(Enum):
    """Visual hierarchy levels for texture mapping"""
    BACKGROUND = auto()      # Main window backgrounds
    CONTAINER = auto()       # Panels, frames, group boxes
    CONTROL = auto()         # Buttons, inputs, lists
    INDICATOR = auto()       # Progress bars, sliders
    DECORATION = auto()      # Borders, separators


class WidgetState(Enum):
    """Widget states for texture mapping"""
    NORMAL = auto()
    HOVER = auto()
    PRESSED = auto()
    DISABLED = auto()
    FOCUSED = auto()
    SELECTED = auto()


# =============================================================================
# TEXTURE MAPPING CONFIGURATION
# =============================================================================

class TextureMapping:
    """
    Maps widget types to texture styles.
    Each widget type can have different textures for different states.
    """
    
    # Flat mode colors - solid colors for minimalist UI (no textures)
    FLAT_COLORS: Dict[str, Dict[WidgetState, Tuple[int, int, int]]] = {
        "QPushButton": {
            WidgetState.NORMAL: (74, 93, 35),       # #4a5d23 - muddy green
            WidgetState.HOVER: (85, 107, 47),        # #556b2f - olive drab
            WidgetState.PRESSED: (61, 79, 42),      # #3d4f2a - military green
            WidgetState.DISABLED: (58, 58, 58),     # #3a3a3a - dark gray
        },
        "QToolButton": {
            WidgetState.NORMAL: (74, 93, 35),
            WidgetState.HOVER: (85, 107, 47),
            WidgetState.PRESSED: (61, 79, 42),
        },
        "QFrame": {
            WidgetState.NORMAL: (42, 42, 42),
        },
        "QGroupBox": {
            WidgetState.NORMAL: (42, 42, 40),
        },
        "QWidget": {
            WidgetState.NORMAL: (26, 26, 26),
        },
        "QMainWindow": {
            WidgetState.NORMAL: (26, 26, 26),
        },
        "QLineEdit": {
            WidgetState.NORMAL: (26, 26, 26),
            WidgetState.FOCUSED: (34, 34, 34),
        },
        "QTextEdit": {
            WidgetState.NORMAL: (26, 26, 26),
        },
        "QPlainTextEdit": {
            WidgetState.NORMAL: (26, 26, 26),
        },
        "QListWidget": {
            WidgetState.NORMAL: (45, 45, 45),
            WidgetState.SELECTED: (85, 107, 47),
        },
        "QTreeWidget": {
            WidgetState.NORMAL: (45, 45, 45),
            WidgetState.SELECTED: (85, 107, 47),
        },
        "QComboBox": {
            WidgetState.NORMAL: (45, 45, 45),
            WidgetState.HOVER: (58, 58, 58),
        },
        "QSpinBox": {
            WidgetState.NORMAL: (45, 45, 45),
        },
        "QDoubleSpinBox": {
            WidgetState.NORMAL: (45, 45, 45),
        },
        "QProgressBar": {
            WidgetState.NORMAL: (107, 142, 35),
        },
        "QSlider": {
            WidgetState.NORMAL: (85, 107, 47),
        },
        "QCheckBox": {
            WidgetState.NORMAL: (45, 45, 45),
        },
        "QRadioButton": {
            WidgetState.NORMAL: (45, 45, 45),
        },
        "QTabWidget": {
            WidgetState.NORMAL: (42, 42, 40),
        },
        "QTabBar": {
            WidgetState.NORMAL: (58, 58, 58),
            WidgetState.SELECTED: (42, 42, 40),
        },
        "QToolBar": {
            WidgetState.NORMAL: (58, 58, 58),
        },
        "QMenuBar": {
            WidgetState.NORMAL: (45, 45, 45),
            WidgetState.HOVER: (85, 107, 47),
        },
        "QMenu": {
            WidgetState.NORMAL: (42, 42, 40),
            WidgetState.HOVER: (85, 107, 47),
        },
        "QStatusBar": {
            WidgetState.NORMAL: (45, 45, 45),
        },
        "QSplitter": {
            WidgetState.NORMAL: (92, 92, 92),
        },
    }
    
    # Default texture styles - EMPTY to disable procedural textures
    # Use FLAT_COLORS for solid color minimalist UI
    DEFAULT_MAPPINGS: Dict[str, Dict[WidgetState, Dict]] = {
        # Background/Container widgets
        "QMainWindow": {
            WidgetState.NORMAL: {"type": "gradient", "gradient_type": "dark", "direction": "vertical", "grain": 0.03},
            WidgetState.HOVER: {"type": "gradient", "gradient_type": "dark", "direction": "vertical", "grain": 0.03},
        },
        "QWidget": {
            WidgetState.NORMAL: {"type": "gradient", "gradient_type": "dark", "direction": "vertical", "grain": 0.03},
        },
        "QFrame": {
            WidgetState.NORMAL: {"type": "metal", "metal_type": "steel", "scratches": False, "bump_strength": 0.6},
            WidgetState.HOVER: {"type": "metal", "metal_type": "steel", "scratches": True, "bump_strength": 0.7},
        },
        "QGroupBox": {
            WidgetState.NORMAL: {"type": "metal", "metal_type": "steel", "scratches": False, "bump_strength": 0.5},
            WidgetState.HOVER: {"type": "metal", "metal_type": "copper", "scratches": True, "bump_strength": 0.6},
        },
        
        # Control widgets
        "QPushButton": {
            WidgetState.NORMAL: {"type": "wood", "wood_type": "oak", "scale": 12.0, "bump_strength": 0.8},
            WidgetState.HOVER: {"type": "wood", "wood_type": "oak", "scale": 10.0, "bump_strength": 1.0},
            WidgetState.PRESSED: {"type": "wood", "wood_type": "pine", "scale": 14.0, "bump_strength": 0.6},
            WidgetState.DISABLED: {"type": "concrete", "dirty": False, "bump_strength": 0.2},
        },
        "QToolButton": {
            WidgetState.NORMAL: {"type": "metal", "metal_type": "steel", "scratches": True, "bump_strength": 0.7},
            WidgetState.HOVER: {"type": "metal", "metal_type": "copper", "scratches": True, "bump_strength": 0.9},
            WidgetState.PRESSED: {"type": "metal", "metal_type": "rust", "scratches": True, "bump_strength": 0.5},
        },
        
        # Input widgets
        "QLineEdit": {
            WidgetState.NORMAL: {"type": "concrete", "dirty": True, "bump_strength": 0.4},
            WidgetState.HOVER: {"type": "concrete", "dirty": True, "bump_strength": 0.5},
            WidgetState.FOCUSED: {"type": "concrete", "dirty": False, "bump_strength": 0.6},
            WidgetState.DISABLED: {"type": "concrete", "dirty": False, "bump_strength": 0.2},
        },
        "QTextEdit": {
            WidgetState.NORMAL: {"type": "concrete", "dirty": True, "bump_strength": 0.4},
            WidgetState.FOCUSED: {"type": "concrete", "dirty": False, "bump_strength": 0.5},
        },
        "QPlainTextEdit": {
            WidgetState.NORMAL: {"type": "concrete", "dirty": True, "bump_strength": 0.4},
            WidgetState.FOCUSED: {"type": "concrete", "dirty": False, "bump_strength": 0.5},
        },
        
        # Selection widgets
        "QListWidget": {
            WidgetState.NORMAL: {"type": "metal", "metal_type": "steel", "scratches": False, "bump_strength": 0.5},
            WidgetState.SELECTED: {"type": "metal", "metal_type": "copper", "scratches": True, "bump_strength": 0.7},
        },
        "QTreeWidget": {
            WidgetState.NORMAL: {"type": "metal", "metal_type": "steel", "scratches": False, "bump_strength": 0.5},
            WidgetState.SELECTED: {"type": "metal", "metal_type": "copper", "scratches": True, "bump_strength": 0.7},
        },
        "QComboBox": {
            WidgetState.NORMAL: {"type": "leather", "leather_type": "brown", "worn": True, "bump_strength": 0.6},
            WidgetState.HOVER: {"type": "leather", "leather_type": "brown", "worn": False, "bump_strength": 0.8},
            WidgetState.DISABLED: {"type": "leather", "leather_type": "brown", "worn": True, "bump_strength": 0.3},
        },
        
        # Value widgets
        "QSpinBox": {
            WidgetState.NORMAL: {"type": "plastic", "plastic_type": "black", "glossy": True, "bump_strength": 0.5},
            WidgetState.HOVER: {"type": "plastic", "plastic_type": "blue", "glossy": True, "bump_strength": 0.6},
            WidgetState.FOCUSED: {"type": "plastic", "plastic_type": "green", "glossy": True, "bump_strength": 0.7},
        },
        "QDoubleSpinBox": {
            WidgetState.NORMAL: {"type": "plastic", "plastic_type": "black", "glossy": True, "bump_strength": 0.5},
        },
        "QSlider": {
            WidgetState.NORMAL: {"type": "metal", "metal_type": "steel", "scratches": True, "bump_strength": 0.4},
        },
        "QProgressBar": {
            WidgetState.NORMAL: {"type": "metal", "metal_type": "rust", "intensity": 0.6, "bump_strength": 0.5},
        },
        
        # Toggle widgets
        "QCheckBox": {
            WidgetState.NORMAL: {"type": "leather", "leather_type": "brown", "worn": True, "bump_strength": 0.4},
            WidgetState.HOVER: {"type": "leather", "leather_type": "brown", "worn": False, "bump_strength": 0.6},
        },
        "QRadioButton": {
            WidgetState.NORMAL: {"type": "leather", "leather_type": "brown", "worn": True, "bump_strength": 0.4},
            WidgetState.HOVER: {"type": "leather", "leather_type": "brown", "worn": False, "bump_strength": 0.6},
        },
        
        # Navigation widgets
        "QTabWidget": {
            WidgetState.NORMAL: {"type": "metal", "metal_type": "steel", "scratches": False, "bump_strength": 0.5},
        },
        "QTabBar": {
            WidgetState.NORMAL: {"type": "metal", "metal_type": "steel", "scratches": True, "bump_strength": 0.5},
            WidgetState.SELECTED: {"type": "metal", "metal_type": "copper", "scratches": True, "bump_strength": 0.7},
        },
        "QToolBar": {
            WidgetState.NORMAL: {"type": "metal", "metal_type": "steel", "scratches": True, "bump_strength": 0.6},
        },
        "QMenuBar": {
            WidgetState.NORMAL: {"type": "metal", "metal_type": "steel", "scratches": True, "bump_strength": 0.5},
            WidgetState.HOVER: {"type": "metal", "metal_type": "copper", "scratches": True, "bump_strength": 0.7},
        },
        "QMenu": {
            WidgetState.NORMAL: {"type": "leather", "leather_type": "brown", "worn": True, "bump_strength": 0.5},
            WidgetState.HOVER: {"type": "leather", "leather_type": "dark", "worn": False, "bump_strength": 0.7},
        },
        
        # Status widgets
        "QStatusBar": {
            WidgetState.NORMAL: {"type": "metal", "metal_type": "rust", "intensity": 0.5, "bump_strength": 0.4},
        },
        
        # Splitter
        "QSplitter": {
            WidgetState.NORMAL: {"type": "metal", "metal_type": "steel", "scratches": False, "bump_strength": 0.3},
        },
        
        # Custom Fallout widgets
        "FalloutButton": {
            WidgetState.NORMAL: {"type": "wood", "wood_type": "oak", "scale": 12.0, "bump_strength": 0.8},
            WidgetState.HOVER: {"type": "wood", "wood_type": "oak", "scale": 10.0, "bump_strength": 1.0},
            WidgetState.PRESSED: {"type": "wood", "wood_type": "pine", "scale": 14.0, "bump_strength": 0.6},
            WidgetState.DISABLED: {"type": "concrete", "dirty": False, "bump_strength": 0.2},
        },
        "FalloutPanel": {
            WidgetState.NORMAL: {"type": "metal", "metal_type": "steel", "scratches": True, "bump_strength": 0.6},
            WidgetState.HOVER: {"type": "metal", "metal_type": "copper", "scratches": True, "bump_strength": 0.8},
        },
        "WornMetalPanel": {
            WidgetState.NORMAL: {"type": "rust", "intensity": 0.7, "bump_strength": 0.7},
            WidgetState.HOVER: {"type": "rust", "intensity": 0.8, "bump_strength": 0.9},
        },
        "TexturedFalloutButton": {
            WidgetState.NORMAL: {"type": "leather", "leather_type": "brown", "worn": True, "bump_strength": 0.8},
            WidgetState.HOVER: {"type": "leather", "leather_type": "brown", "worn": False, "bump_strength": 1.0},
            WidgetState.PRESSED: {"type": "leather", "leather_type": "dark", "worn": True, "bump_strength": 0.6},
        },
        "TexturedFalloutPanel": {
            WidgetState.NORMAL: {"type": "carbon", "clear_coat": True, "bump_strength": 0.7},
            WidgetState.HOVER: {"type": "carbon", "clear_coat": True, "bump_strength": 0.9},
        },
    }
    
    # Texture sizes by widget type (increased for better quality)
    TEXTURE_SIZES: Dict[str, Tuple[int, int]] = {
        "QPushButton": (256, 128),
        "QToolButton": (192, 96),
        "QFrame": (256, 256),
        "QGroupBox": (256, 256),
        "QLineEdit": (256, 64),
        "QTextEdit": (256, 256),
        "QListWidget": (256, 256),
        "QTreeWidget": (256, 256),
        "QComboBox": (200, 56),
        "QSpinBox": (160, 48),
        "QTabWidget": (256, 256),
        "QMenuBar": (256, 48),
        "QMenu": (200, 48),
        "QStatusBar": (256, 40),
        "QToolBar": (128, 64),
        "QProgressBar": (200, 40),
        "QSlider": (160, 48),
        "QCheckBox": (32, 32),
        "QRadioButton": (32, 32),
        "FalloutButton": (256, 128),
        "FalloutPanel": (256, 256),
        "WornMetalPanel": (256, 256),
        "TexturedFalloutButton": (256, 128),
        "TexturedFalloutPanel": (128, 128),
        # Default sizes
        "default": (64, 64),
    }


# =============================================================================
# TEXTURED WIDGET MIXIN
# =============================================================================

class TexturedWidgetMixin:
    """
    Mixin class that provides texture rendering capabilities.
    Add this mixin to any QWidget subclass to enable procedural textures.
    """
    
    # Class-level attribute to track if mixin is initialized
    _texture_initialized = False
    
    def __init__(self):
        self._texture_enabled = True
        self._current_state = WidgetState.NORMAL
        self._texture_cache: Dict[WidgetState, QPixmap] = {}
        self._hierarchy_level = HierarchyLevel.CONTROL
        self._texture_seed = hash(self.__class__.__name__) % 10000
        self._texture_tiling = True
        self._normal_map_enabled = False
        self._hover_animation_progress = 0.0
        
    def set_texture_enabled(self, enabled: bool):
        """Enable or disable texture rendering"""
        self._texture_enabled = enabled
        if enabled:
            self._regenerate_textures()
            self.update()
        else:
            self.update()
    
    def is_texture_enabled(self) -> bool:
        """Check if texture rendering is enabled"""
        return self._texture_enabled
    
    def set_hierarchy_level(self, level: HierarchyLevel):
        """Set the visual hierarchy level"""
        self._hierarchy_level = level
        self._regenerate_textures()
        self.update()
    
    def get_hierarchy_level(self) -> HierarchyLevel:
        """Get the current hierarchy level"""
        return self._hierarchy_level
    
    def set_texture_seed(self, seed: int):
        """Set the random seed for texture generation"""
        self._texture_seed = seed
        self._regenerate_textures()
        self.update()
    
    def set_texture_tiling(self, tiled: bool):
        """Enable or disable texture tiling"""
        self._texture_tiling = tiled
        self.update()
    
    def _get_widget_state(self) -> WidgetState:
        """Determine the current widget state"""
        # Check if widget is enabled
        if hasattr(self, 'isEnabled'):
            if not self.isEnabled():
                return WidgetState.DISABLED
        
        # Check if widget has focus
        if hasattr(self, 'hasFocus'):
            if self.hasFocus():
                return WidgetState.FOCUSED
        
        # Default to normal
        return WidgetState.NORMAL
    
    def _regenerate_textures(self):
        """Regenerate all state textures"""
        self._texture_cache.clear()
        widget_class = self.__class__.__name__
        
        # Get mapping for this widget type
        mapping = TextureMapping.DEFAULT_MAPPINGS.get(widget_class, {})
        
        for state, style in mapping.items():
            size = TextureMapping.TEXTURE_SIZES.get(widget_class, TextureMapping.TEXTURE_SIZES["default"])
            texture = self._generate_texture(size[0], size[1], style)
            self._texture_cache[state] = texture
    
    def _generate_texture(self, width: int, height: int, style: Dict) -> QPixmap:
        """Generate a texture based on style dict"""
        if not _ensure_qapplication():
            return QPixmap()
        
        try:
            tex_type = style.get("type", "metal")
            seed = self._texture_seed
            
            if tex_type == "wood":
                return TextureGenerator.generate_wood_texture(
                    width, height,
                    wood_type=style.get("wood_type", "oak"),
                    scale=style.get("scale", 8.0),
                    seed=seed
                )
            elif tex_type == "metal":
                return TextureGenerator.generate_metal_texture(
                    width, height,
                    metal_type=style.get("metal_type", "steel"),
                    scratches=style.get("scratches", True),
                    seed=seed
                )
            elif tex_type == "rust":
                return TextureGenerator.generate_rust_texture(
                    width, height,
                    intensity=style.get("intensity", 0.7),
                    seed=seed
                )
            elif tex_type == "leather":
                return TextureGenerator.generate_leather_texture(
                    width, height,
                    leather_type=style.get("leather_type", "brown"),
                    worn=style.get("worn", True),
                    seed=seed
                )
            elif tex_type == "concrete":
                return TextureGenerator.generate_concrete_texture(
                    width, height,
                    dirty=style.get("dirty", True),
                    seed=seed
                )
            elif tex_type == "plastic":
                return TextureGenerator.generate_plastic_texture(
                    width, height,
                    plastic_type=style.get("plastic_type", "white"),
                    glossy=style.get("glossy", True),
                    seed=seed
                )
            elif tex_type == "glass":
                return TextureGenerator.generate_glass_texture(
                    width, height,
                    glass_type=style.get("glass_type", "clear"),
                    frosted=style.get("frosted", False),
                    seed=seed
                )
            elif tex_type == "carbon":
                return TextureGenerator.generate_carbon_fiber_texture(
                    width, height,
                    clear_coat=style.get("clear_coat", True),
                    seed=seed
                )
            elif tex_type == "fabric":
                return TextureGenerator.generate_fabric_texture(
                    width, height,
                    fabric_type=style.get("fabric_type", "canvas"),
                    seed=seed
                )
            elif tex_type == "gradient":
                return TextureGenerator.generate_gradient_texture(
                    width, height,
                    gradient_type=style.get("gradient_type", "dark"),
                    direction=style.get("direction", "vertical"),
                    grain=style.get("grain", 0.05),
                    seed=seed
                )
            elif tex_type == "holographic":
                return TextureGenerator.generate_holographic_texture(
                    width, height,
                    holo_type=style.get("holo_type", "rainbow"),
                    intensity=style.get("intensity", 0.7),
                    seed=seed
                )
            elif tex_type == "tech":
                return TextureGenerator.generate_tech_pattern(
                    width, height,
                    pattern_type=style.get("pattern_type", "circuit"),
                    color_scheme=style.get("color_scheme", "green"),
                    glow=style.get("glow", True),
                    seed=seed
                )
            elif tex_type == "neumorphic":
                return TextureGenerator.generate_neumorphic_texture(
                    width, height,
                    style=style.get("style", "light"),
                    convex=style.get("convex", True),
                    seed=seed
                )
            elif tex_type == "highcontrast":
                return TextureGenerator.generate_high_contrast_texture(
                    width, height,
                    style=style.get("style", "dark"),
                    seed=seed
                )
            elif tex_type == "darkmode":
                return TextureGenerator.generate_dark_mode_texture(
                    width, height,
                    accent_color=style.get("accent_color"),
                    seed=seed
                )
            
            # Default fallback
            return TextureGenerator.generate_metal_texture(width, height, seed=seed)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error generating texture: {e}")
            return QPixmap()
    
    def _paint_texture(self, painter: QPainter, rect: QRect):
        """Paint the texture onto the widget"""
        if not self._texture_enabled:
            return
        
        # Get current state
        state = self._get_widget_state()
        
        # Try to get texture for current state
        texture = self._texture_cache.get(state)
        
        # Fall back to normal state if current state not available
        if texture is None or texture.isNull():
            texture = self._texture_cache.get(WidgetState.NORMAL)
        
        # If still no texture, generate it
        if texture is None or texture.isNull():
            widget_class = self.__class__.__name__
            mapping = TextureMapping.DEFAULT_MAPPINGS.get(widget_class, {})
            style = mapping.get(WidgetState.NORMAL, {"type": "metal"})
            size = TextureMapping.TEXTURE_SIZES.get(widget_class, TextureMapping.TEXTURE_SIZES["default"])
            texture = self._generate_texture(size[0], size[1], style)
            self._texture_cache[WidgetState.NORMAL] = texture
        
        if texture and not texture.isNull():
            if self._texture_tiling:
                TexturePainter.paint_texture(painter, rect, texture, tiled=True, scaled=False)
            else:
                # Stretch to fit
                scaled = texture.scaled(rect.size(), Qt.AspectRatioMode.IgnoreAspectRatio, 
                                      Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(rect, scaled)


# =============================================================================
# GUI TEXTURE APPLICATOR
# =============================================================================

class GUITextureApplicator(QObject):
    """
    Central system for automatically applying textures to all GUI elements.
    Monitors widget events and updates textures accordingly.
    """
    
    # Singleton instance
    _instance = None
    _lock = threading.Lock()
    
    # Signals
    texture_applied = pyqtSignal(str, str)  # widget_class, texture_type
    state_changed = pyqtSignal(str, object)  # widget, new_state
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        super().__init__()
        self._initialized = True
        
        self._enabled = True
        self._auto_apply = True
        self._tracked_widgets: List[QWidget] = []
        self._widget_states: Dict[int, WidgetState] = {}
        self._texture_settings: Dict[str, Dict] = {}
        self._hierarchy_overrides: Dict[int, HierarchyLevel] = {}
        
        # Performance settings
        self._lazy_texture_generation = True
        self._texture_resolution = ResolutionVariant.HD
        self._max_cached_textures = 500
        
        # Background generation thread
        self._generation_thread = None
        self._pending_generations: List[Tuple[QWidget, Dict]] = []
        
        # Event filters
        self._hover_filters: Dict[int, QObject] = {}
        
        logging.getLogger(__name__).info("GUI Texture Applicator initialized")
    
    def enable(self, enabled: bool = True):
        """Enable or disable the texture applicator"""
        self._enabled = enabled
        if enabled:
            self._apply_to_all_widgets()
        else:
            self._remove_from_all_widgets()
    
    def is_enabled(self) -> bool:
        """Check if the applicator is enabled"""
        return self._enabled
    
    def set_auto_apply(self, auto: bool):
        """Enable or disable automatic application to new widgets"""
        self._auto_apply = auto
    
    def set_texture_resolution(self, resolution: int):
        """Set the texture resolution (64, 128, 256, 512)"""
        self._texture_resolution = resolution
        # Regenerate all textures
        if self._enabled:
            self._apply_to_all_widgets()
    
    def apply_to_widget(self, widget: QWidget, custom_style: Optional[Dict] = None):
        """Apply textures to a specific widget"""
        if not self._enabled:
            return
        
        # Store widget in tracked list
        if widget not in self._tracked_widgets:
            self._tracked_widgets.append(widget)
        
        # Install event filter for state tracking
        widget_id = id(widget)
        if widget_id not in self._hover_filters:
            filter = TextureEventFilter(self, widget)
            widget.installEventFilter(filter)
            self._hover_filters[widget_id] = filter
        
        # Set custom style if provided
        if custom_style:
            self._texture_settings[widget_id] = custom_style
        
        # Force update
        widget.update()
    
    def remove_from_widget(self, widget: QWidget):
        """Remove texture application from a widget"""
        widget_id = id(widget)
        
        # Remove from tracked list
        if widget in self._tracked_widgets:
            self._tracked_widgets.remove(widget)
        
        # Remove event filter
        if widget_id in self._hover_filters:
            widget.removeEventFilter(self._hover_filters[widget_id])
            del self._hover_filters[widget_id]
        
        # Remove from settings
        if widget_id in self._texture_settings:
            del self._texture_settings[widget_id]
        
        # Force update
        widget.update()
    
    def set_hierarchy_level_for_widget(self, widget: QWidget, level: HierarchyLevel):
        """Override hierarchy level for a specific widget"""
        self._hierarchy_overrides[id(widget)] = level
    
    def _apply_to_all_widgets(self):
        """Apply textures to all existing widgets"""
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if not app:
            return
        
        # Get all widgets
        all_widgets = app.allWidgets()
        
        for widget in all_widgets:
            if self._should_apply_to_widget(widget):
                self.apply_to_widget(widget)
    
    def _remove_from_all_widgets(self):
        """Remove textures from all tracked widgets"""
        for widget in self._tracked_widgets.copy():
            self.remove_from_widget(widget)
    
    def _should_apply_to_widget(self, widget: QWidget) -> bool:
        """Check if textures should be applied to this widget"""
        # Skip some special widgets
        class_name = widget.__class__.__name__
        
        # Skip these widget types
        skip_types = [
            "QLayout", "QSpacerItem", "QSizePolicy",
            "QAbstractItemView", "QHeaderView"
        ]
        
        if class_name in skip_types:
            return False
        
        # Skip widgets without visual representation
        if hasattr(widget, "isHidden") and widget.isHidden():
            return False
        
        return True
    
    def get_widget_state(self, widget: QWidget) -> WidgetState:
        """Get the current state of a widget"""
        widget_id = id(widget)
        return self._widget_states.get(widget_id, WidgetState.NORMAL)
    
    def update_widget_state(self, widget: QWidget, state: WidgetState):
        """Update the state of a widget and regenerate textures if needed"""
        widget_id = id(widget)
        old_state = self._widget_states.get(widget_id)
        
        self._widget_states[widget_id] = state
        
        # Emit state changed signal
        self.state_changed.emit(widget.__class__.__name__, state)
        
        # Regenerate texture if state changed
        if old_state != state:
            widget.update()
    
    def clear_cache(self):
        """Clear all texture caches"""
        TextureCache.clear()
        self._texture_settings.clear()
        self._widget_states.clear()
        
        # Force all widgets to regenerate textures
        for widget in self._tracked_widgets:
            widget.update()


# =============================================================================
# EVENT FILTER FOR STATE TRACKING
# =============================================================================

class TextureEventFilter(QObject):
    """Event filter for tracking widget state changes"""
    
    def __init__(self, applicator: GUITextureApplicator, widget: QWidget):
        super().__init__(widget)
        self._applicator = applicator
        self._widget = widget
        self._hovered = False
        self._pressed = False
    
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj != self._widget:
            return False
        
        event_type = event.type()
        
        # Track hover state
        if event_type == QEvent.Type.Enter:
            self._hovered = True
            self._update_state()
            return False
        
        elif event_type == QEvent.Type.Leave:
            self._hovered = False
            self._update_state()
            return False
        
        # Track press state for buttons
        if event_type == QEvent.Type.MouseButtonPress:
            self._pressed = True
            self._update_state()
            return False
        
        elif event_type == QEvent.Type.MouseButtonRelease:
            self._pressed = False
            self._update_state()
            return False
        
        # Track focus state
        elif event_type == QEvent.Type.FocusIn:
            self._update_state()
            return False
        
        elif event_type == QEvent.Type.FocusOut:
            self._update_state()
            return False
        
        # Handle resize for texture regeneration
        elif event_type == QEvent.Type.Resize:
            # Lazy regeneration on resize
            if hasattr(self._widget, '_regenerate_textures'):
                self._widget._regenerate_textures()
        
        return False
    
    def _update_state(self):
        """Update the widget state based on current conditions"""
        # Determine state
        if not self._widget.isEnabled():
            state = WidgetState.DISABLED
        elif self._pressed:
            state = WidgetState.PRESSED
        elif self._hovered:
            state = WidgetState.HOVER
        elif self._widget.hasFocus():
            state = WidgetState.FOCUSED
        else:
            state = WidgetState.NORMAL
        
        # Update applicator
        self._applicator.update_widget_state(self._widget, state)


# =============================================================================
# AUTO-APPLY DECORATOR/FUNCTION
# =============================================================================

def apply_textures_to_widget(widget: QWidget, style: Optional[Dict] = None):
    """
    Convenience function to apply textures to a widget.
    
    Args:
        widget: The widget to apply textures to
        style: Optional custom style dictionary
    """
    applicator = GUITextureApplicator()
    applicator.apply_to_widget(widget, style)


def remove_textures_from_widget(widget: QWidget):
    """Convenience function to remove textures from a widget"""
    applicator = GUITextureApplicator()
    applicator.remove_from_widget(widget)


def enable_texture_system(enabled: bool = True):
    """Enable or disable the entire texture system"""
    applicator = GUITextureApplicator()
    applicator.enable(enabled)


# =============================================================================
# TEXTURED WIDGET FACTORY
# =============================================================================

class TexturedWidgetFactory:
    """
    Factory class for creating widgets with textures pre-applied.
    Use this instead of directly creating widgets when you want textures.
    """
    
    @staticmethod
    def create_button(text: str = "", style: str = "standard", parent: QWidget = None) -> QPushButton:
        """Create a textured push button"""
        button = QPushButton(text, parent)
        
        # Apply appropriate style
        applicator = GUITextureApplicator()
        applicator.apply_to_widget(button)
        
        return button
    
    @staticmethod
    def create_frame(style: str = "standard", parent: QWidget = None) -> QFrame:
        """Create a textured frame"""
        frame = QFrame(parent)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        applicator = GUITextureApplicator()
        applicator.apply_to_widget(frame)
        
        return frame
    
    @staticmethod
    def create_line_edit(placeholder: str = "", parent: QWidget = None) -> QLineEdit:
        """Create a textured line edit"""
        edit = QLineEdit(parent)
        if placeholder:
            edit.setPlaceholderText(placeholder)
        
        applicator = GUITextureApplicator()
        applicator.apply_to_widget(edit)
        
        return edit
    
    @staticmethod
    def create_text_edit(parent: QWidget = None) -> QTextEdit:
        """Create a textured text edit"""
        edit = QTextEdit(parent)
        
        applicator = GUITextureApplicator()
        applicator.apply_to_widget(edit)
        
        return edit
    
    @staticmethod
    def create_list_widget(parent: QWidget = None) -> QListWidget:
        """Create a textured list widget"""
        widget = QListWidget(parent)
        
        applicator = GUITextureApplicator()
        applicator.apply_to_widget(widget)
        
        return widget
    
    @staticmethod
    def create_tree_widget(parent: QWidget = None) -> QTreeWidget:
        """Create a textured tree widget"""
        widget = QTreeWidget(parent)
        
        applicator = GUITextureApplicator()
        applicator.apply_to_widget(widget)
        
        return widget
    
    @staticmethod
    def create_combo_box(parent: QWidget = None) -> QComboBox:
        """Create a textured combo box"""
        combo = QComboBox(parent)
        
        applicator = GUITextureApplicator()
        applicator.apply_to_widget(combo)
        
        return combo
    
    @staticmethod
    def create_group_box(title: str = "", parent: QWidget = None) -> QGroupBox:
        """Create a textured group box"""
        group = QGroupBox(title, parent)
        
        applicator = GUITextureApplicator()
        applicator.apply_to_widget(group)
        
        return group
    
    @staticmethod
    def create_tab_widget(parent: QWidget = None) -> QTabWidget:
        """Create a textured tab widget"""
        tabs = QTabWidget(parent)
        
        applicator = GUITextureApplicator()
        applicator.apply_to_widget(tabs)
        
        return tabs
    
    @staticmethod
    def create_scroll_area(parent: QWidget = None) -> QScrollArea:
        """Create a textured scroll area"""
        area = QScrollArea(parent)
        
        applicator = GUITextureApplicator()
        applicator.apply_to_widget(area)
        
        return area
    
    @staticmethod
    def create_spin_box(parent: QWidget = None) -> QSpinBox:
        """Create a textured spin box"""
        spin = QSpinBox(parent)
        
        applicator = GUITextureApplicator()
        applicator.apply_to_widget(spin)
        
        return spin


# =============================================================================
# INTEGRATION HELPER
# =============================================================================

class TextureIntegration:
    """
    Helper class to integrate texture system with existing applications.
    Call integrate_with_app() at application startup.
    """
    
    @staticmethod
    def integrate_with_app(app, auto_apply: bool = True):
        """
        Integrate the texture system with a QApplication.
        Call this after QApplication is created but before showing windows.
        
        Args:
            app: QApplication instance
            auto_apply: Whether to automatically apply textures to all widgets
        """
        applicator = GUITextureApplicator()
        
        if auto_apply:
            # Wait for widgets to be created, then apply
            QTimer.singleShot(100, lambda: applicator.enable(True))
        
        logging.getLogger(__name__).info("Texture system integrated with application")
    
    @staticmethod
    def create_textured_window(base_class):
        """
        Decorator to create a textured window class.
        
        Usage:
            @TextureIntegration.create_textured_window
            class MyWindow(QMainWindow):
                ...
        """
        class TexturedWindow(base_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._setup_textures()
            
            def _setup_textures(self):
                applicator = GUITextureApplicator()
                applicator.apply_to_widget(self)
        
        return TexturedWindow


# =============================================================================
# STANDALONE TEXTURED WIDGET CLASSES
# =============================================================================

class TexturedFrame(QFrame):
    """A QFrame with automatic procedural textures"""
    
    def __init__(self, parent: QWidget = None, texture_style: str = "metal"):
        super().__init__(parent)
        
        # Apply mixin methods
        self._texture_enabled = True
        self._current_state = WidgetState.NORMAL
        self._texture_cache: Dict[WidgetState, QPixmap] = {}
        self._hierarchy_level = HierarchyLevel.CONTAINER
        self._texture_seed = hash("TexturedFrame") % 10000
        self._texture_tiling = True
        
        # Apply custom style
        self._texture_style = texture_style
        self._regenerate_textures()
        
        # Install event filter
        self._event_filter = TextureEventFilter(GUITextureApplicator(), self)
        self.installEventFilter(self._event_filter)
    
    def _regenerate_textures(self):
        """Regenerate textures for all states"""
        self._texture_cache.clear()
        
        style = TextureMapping.DEFAULT_MAPPINGS.get("QFrame", {}).get(
            WidgetState.NORMAL, {"type": "metal"}
        )
        style = dict(style)  # Copy
        style["type"] = self._texture_style
        
        size = TextureMapping.TEXTURE_SIZES.get("QFrame", (128, 128))
        texture = self._generate_texture(size[0], size[1], style)
        self._texture_cache[WidgetState.NORMAL] = texture
    
    def _generate_texture(self, width: int, height: int, style: Dict) -> QPixmap:
        """Generate texture based on style"""
        if not _ensure_qapplication():
            return QPixmap()
        
        try:
            from ui.texture_system import TextureGenerator
            
            tex_type = style.get("type", "metal")
            seed = self._texture_seed
            
            if tex_type == "wood":
                return TextureGenerator.generate_wood_texture(
                    width, height, wood_type=style.get("wood_type", "oak"),
                    scale=style.get("scale", 8.0), seed=seed
                )
            elif tex_type == "metal":
                return TextureGenerator.generate_metal_texture(
                    width, height, metal_type=style.get("metal_type", "steel"),
                    scratches=style.get("scratches", True), seed=seed
                )
            elif tex_type == "rust":
                return TextureGenerator.generate_rust_texture(
                    width, height, intensity=style.get("intensity", 0.7), seed=seed
                )
            elif tex_type == "leather":
                return TextureGenerator.generate_leather_texture(
                    width, height, leather_type=style.get("leather_type", "brown"),
                    worn=style.get("worn", True), seed=seed
                )
            elif tex_type == "concrete":
                return TextureGenerator.generate_concrete_texture(
                    width, height, dirty=style.get("dirty", True), seed=seed
                )
            elif tex_type == "plastic":
                return TextureGenerator.generate_plastic_texture(
                    width, height, plastic_type=style.get("plastic_type", "white"),
                    glossy=style.get("glossy", True), seed=seed
                )
            elif tex_type == "carbon":
                return TextureGenerator.generate_carbon_fiber_texture(
                    width, height, clear_coat=style.get("clear_coat", True), seed=seed
                )
            elif tex_type == "gradient":
                return TextureGenerator.generate_gradient_texture(
                    width, height, gradient_type=style.get("gradient_type", "dark"),
                    direction=style.get("direction", "vertical"),
                    grain=style.get("grain", 0.05), seed=seed
                )
            
            return TextureGenerator.generate_metal_texture(width, height, seed=seed)
        except Exception as e:
            logging.getLogger(__name__).error(f"Error generating texture: {e}")
            return QPixmap()
    
    def paintEvent(self, event: QPaintEvent):
        """Paint the texture"""
        painter = QPainter(self)
        rect = self.rect()
        
        # Get texture
        texture = self._texture_cache.get(WidgetState.NORMAL)
        
        if texture and not texture.isNull():
            if self._texture_tiling:
                TexturePainter.paint_texture(painter, rect, texture, tiled=True, scaled=False)
            else:
                scaled = texture.scaled(rect.size(), Qt.AspectRatioMode.IgnoreAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(rect, scaled)
        
        painter.end()
        
        # Call parent paint
        super().paintEvent(event)


class TexturedButton(QPushButton):
    """A QPushButton with automatic procedural textures for all states"""
    
    def __init__(self, text: str = "", parent: QWidget = None, texture_style: str = "wood"):
        super().__init__(text, parent)
        
        # Initialize texture cache
        self._texture_cache: Dict[WidgetState, QPixmap] = {}
        self._texture_seed = hash("TexturedButton") % 10000
        self._texture_style = texture_style
        self._texture_tiling = False  # Buttons usually don't tile
        
        # Track state
        self._hovered = False
        self._pressed = False
        
        # Generate textures for all states
        self._regenerate_textures()
        
        # Install event filter
        self._event_filter = TextureEventFilter(GUITextureApplicator(), self)
        self.installEventFilter(self._event_filter)
    
    def _regenerate_textures(self):
        """Regenerate textures for all button states"""
        self._texture_cache.clear()
        
        mapping = TextureMapping.DEFAULT_MAPPINGS.get("QPushButton", {})
        
        for state in [WidgetState.NORMAL, WidgetState.HOVER, WidgetState.PRESSED, WidgetState.DISABLED]:
            style = mapping.get(state, {"type": "wood"})
            style = dict(style)  # Copy to avoid modifying original
            
            # Apply custom style type
            style["type"] = self._get_type_for_state(state)
            
            size = TextureMapping.TEXTURE_SIZES.get("QPushButton", (64, 32))
            texture = self._generate_texture(size[0], size[1], style)
            self._texture_cache[state] = texture
    
    def _get_type_for_state(self, state: WidgetState) -> str:
        """Get texture type for state"""
        types = {
            WidgetState.NORMAL: self._texture_style,
            WidgetState.HOVER: self._texture_style,
            WidgetState.PRESSED: "wood",  # Pressed always looks like pressed wood
            WidgetState.DISABLED: "concrete",
        }
        return types.get(state, self._texture_style)
    
    def _generate_texture(self, width: int, height: int, style: Dict) -> QPixmap:
        """Generate texture based on style"""
        if not _ensure_qapplication():
            return QPixmap()
        
        try:
            from ui.texture_system import TextureGenerator
            
            tex_type = style.get("type", "metal")
            seed = self._texture_seed
            
            generators = {
                "wood": lambda: TextureGenerator.generate_wood_texture(
                    width, height, wood_type=style.get("wood_type", "oak"),
                    scale=style.get("scale", 12.0), seed=seed
                ),
                "metal": lambda: TextureGenerator.generate_metal_texture(
                    width, height, metal_type=style.get("metal_type", "steel"),
                    scratches=style.get("scratches", True), seed=seed
                ),
                "rust": lambda: TextureGenerator.generate_rust_texture(
                    width, height, intensity=style.get("intensity", 0.7), seed=seed
                ),
                "leather": lambda: TextureGenerator.generate_leather_texture(
                    width, height, leather_type=style.get("leather_type", "brown"),
                    worn=style.get("worn", True), seed=seed
                ),
                "concrete": lambda: TextureGenerator.generate_concrete_texture(
                    width, height, dirty=style.get("dirty", False), seed=seed
                ),
                "plastic": lambda: TextureGenerator.generate_plastic_texture(
                    width, height, plastic_type=style.get("plastic_type", "white"),
                    glossy=style.get("glossy", True), seed=seed
                ),
            }
            
            generator = generators.get(tex_type)
            if generator:
                return generator()
            
            return TextureGenerator.generate_metal_texture(width, height, seed=seed)
        except Exception as e:
            logging.getLogger(__name__).error(f"Error generating texture: {e}")
            return QPixmap()
    
    def _get_current_state(self) -> WidgetState:
        """Get the current button state"""
        if not self.isEnabled():
            return WidgetState.DISABLED
        elif self._pressed:
            return WidgetState.PRESSED
        elif self._hovered:
            return WidgetState.HOVER
        elif self.hasFocus():
            return WidgetState.FOCUSED
        return WidgetState.NORMAL
    
    def paintEvent(self, event: QPaintEvent):
        """Paint the button with texture"""
        painter = QPainter(self)
        rect = self.rect()
        
        # Get texture for current state
        state = self._get_current_state()
        texture = self._texture_cache.get(state)
        
        # Fallback to normal
        if texture is None or texture.isNull():
            texture = self._texture_cache.get(WidgetState.NORMAL)
        
        # Draw texture
        if texture and not texture.isNull():
            scaled = texture.scaled(rect.size(), Qt.AspectRatioMode.IgnoreAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(rect, scaled)
        
        painter.end()
        
        # Draw text on top
        super().paintEvent(event)
    
    def enterEvent(self, event: QEvent):
        """Handle mouse enter"""
        self._hovered = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event: QEvent):
        """Handle mouse leave"""
        self._hovered = False
        self.update()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press"""
        self._pressed = True
        self.update()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release"""
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)


# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_texture_system():
    """Initialize the texture system"""
    # Create singleton
    applicator = GUITextureApplicator()
    
    return applicator


# =============================================================================
# TEXTURE STYLESHEET GENERATOR
# =============================================================================

class TextureStylesheetGenerator:
    """
    Generates Qt Style Sheets with procedural textures for widgets.
    Uses border-image to apply generated textures.
    """
    
    # Texture file paths (relative to assets folder)
    TEXTURE_PATHS = {
        # Buttons
        ("QPushButton", WidgetState.NORMAL): "buttons/wood_oak.png",
        ("QPushButton", WidgetState.HOVER): "buttons/leather_brown.png",
        ("QPushButton", WidgetState.PRESSED): "buttons/metal_copper.png",
        ("QPushButton", WidgetState.DISABLED): "buttons/plastic_black.png",
        
        # Frames/Panels
        ("QFrame", WidgetState.NORMAL): "panels/metal_steel.png",
        ("QFrame", WidgetState.HOVER): "panels/metal_copper.png",
        ("QGroupBox", WidgetState.NORMAL): "panels/metal_steel.png",
        
        # Input widgets
        ("QLineEdit", WidgetState.NORMAL): "panels/concrete_dirty.png",
        ("QLineEdit", WidgetState.FOCUSED): "panels/metal_steel.png",
        ("QTextEdit", WidgetState.NORMAL): "panels/concrete_dirty.png",
        
        # Lists
        ("QListWidget", WidgetState.NORMAL): "panels/metal_steel.png",
        ("QTreeWidget", WidgetState.NORMAL): "panels/metal_steel.png",
        
        # Combo boxes
        ("QComboBox", WidgetState.NORMAL): "panels/leather_brown.png",
        
        # Menus
        ("QMenuBar", WidgetState.NORMAL): "panels/metal_steel.png",
        ("QMenu", WidgetState.NORMAL): "panels/leather_brown.png",
        
        # Toolbars
        ("QToolBar", WidgetState.NORMAL): "borders/metal_steel_h.png",
        
        # Status bar
        ("QStatusBar", WidgetState.NORMAL): "panels/metal_rust.png",
    }
    
    # Border sizes for different widgets
    BORDER_SIZES = {
        "QPushButton": "3",
        "QFrame": "4",
        "QGroupBox": "3",
        "QLineEdit": "2",
        "QTextEdit": "2",
        "QListWidget": "2",
        "QTreeWidget": "2",
        "QComboBox": "2",
    }
    
    @classmethod
    def get_texture_path(cls, widget_class: str, state: WidgetState = WidgetState.NORMAL) -> Optional[str]:
        """Get the texture path for a widget type and state"""
        return cls.TEXTURE_PATHS.get((widget_class, state))
    
    @classmethod
    def generate_stylesheet(cls, widget_class: str) -> str:
        """Generate a stylesheet with textures for a widget class"""
        # Get normal state texture
        normal_texture = cls.get_texture_path(widget_class, WidgetState.NORMAL)
        
        if not normal_texture:
            return ""  # No texture for this widget
        
        border_size = cls.BORDER_SIZES.get(widget_class, "2")
        
        # Build stylesheet with border-image
        # Using absolute path from application directory
        # Always quote URLs for safety with spaces
        normal_url = f'"{normal_texture}"' if ' ' in normal_texture else normal_texture
        stylesheet = f"""
            {widget_class} {{
                border-image: url({normal_url}) {border_size} {border_size} {border_size} {border_size} stretch;
            }}
        """
        
        # Add hover state if available
        hover_texture = cls.get_texture_path(widget_class, WidgetState.HOVER)
        if hover_texture:
            hover_url = f'"{hover_texture}"' if ' ' in hover_texture else hover_texture
            stylesheet += f"""
            {widget_class}:hover {{
                border-image: url({hover_url}) {border_size} {border_size} {border_size} {border_size} stretch;
            }}
        """
        
        # Add pressed state if available
        pressed_texture = cls.get_texture_path(widget_class, WidgetState.PRESSED)
        if pressed_texture:
            pressed_url = f'"{pressed_texture}"' if ' ' in pressed_texture else pressed_texture
            stylesheet += f"""
            {widget_class}:pressed {{
                border-image: url({pressed_url}) {border_size} {border_size} {border_size} {border_size} stretch;
            }}
        """
        
        # Add disabled state if available
        disabled_texture = cls.get_texture_path(widget_class, WidgetState.DISABLED)
        if disabled_texture:
            disabled_url = f'"{disabled_texture}"' if ' ' in disabled_texture else disabled_texture
            stylesheet += f"""
            {widget_class}:disabled {{
                border-image: url({disabled_url}) {border_size} {border_size} {border_size} {border_size} stretch;
            }}
        """
        
        return stylesheet
    
    @classmethod
    def apply_to_widget(cls, widget: QWidget):
        """Apply texture stylesheet to a widget"""
        widget_class = widget.__class__.__name__
        stylesheet = cls.generate_stylesheet(widget_class)
        
        if stylesheet:
            widget.setStyleSheet(stylesheet)
    
    @classmethod
    def apply_global_stylesheet(cls, assets_dir: str = "assets") -> str:
        """Generate a global stylesheet for all widget types"""
        stylesheet = ""
        
        for widget_class in cls.BORDER_SIZES.keys():
            widget_sheet = cls._generate_stylesheet_with_base(widget_class, assets_dir)
            if widget_sheet:
                stylesheet += widget_sheet + "\n"
        
        return stylesheet
    
    @classmethod
    def _generate_stylesheet_with_base(cls, widget_class: str, assets_dir: str) -> str:
        """Generate stylesheet with specific assets directory"""
        normal_texture = cls.get_texture_path(widget_class, WidgetState.NORMAL)
        
        if not normal_texture:
            return ""
        
        border_size = cls.BORDER_SIZES.get(widget_class, "2")
        
        # Build full path - use forward slashes for Qt compatibility and quote if contains spaces
        # Convert backslashes to forward slashes for URL compatibility
        assets_dir_normalized = assets_dir.replace('\\', '/')
        needs_quotes = ' ' in assets_dir or ' ' in normal_texture
        normal_full = f'"{assets_dir_normalized}/{normal_texture}"' if needs_quotes else f"{assets_dir_normalized}/{normal_texture}"
        
        stylesheet = f"""
            {widget_class} {{
                border-image: url({normal_full}) {border_size} {border_size} {border_size} {border_size} stretch;
            }}
        """
        
        # Add hover state
        hover_texture = cls.get_texture_path(widget_class, WidgetState.HOVER)
        if hover_texture:
            hover_full = f'"{assets_dir_normalized}/{hover_texture}"' if ' ' in assets_dir or ' ' in hover_texture else f"{assets_dir_normalized}/{hover_texture}"
            stylesheet += f"""
            {widget_class}:hover {{
                border-image: url({hover_full}) {border_size} {border_size} {border_size} {border_size} stretch;
            }}
        """
        
        # Add pressed state
        pressed_texture = cls.get_texture_path(widget_class, WidgetState.PRESSED)
        if pressed_texture:
            pressed_full = f'"{assets_dir_normalized}/{pressed_texture}"' if ' ' in assets_dir or ' ' in pressed_texture else f"{assets_dir_normalized}/{pressed_texture}"
            stylesheet += f"""
            {widget_class}:pressed {{
                border-image: url({pressed_full}) {border_size} {border_size} {border_size} {border_size} stretch;
            }}
        """
        
        # Add disabled state
        disabled_texture = cls.get_texture_path(widget_class, WidgetState.DISABLED)
        if disabled_texture:
            disabled_full = f'"{assets_dir_normalized}/{disabled_texture}"' if ' ' in assets_dir or ' ' in disabled_texture else f"{assets_dir_normalized}/{disabled_texture}"
            stylesheet += f"""
            {widget_class}:disabled {{
                border-image: url({disabled_full}) {border_size} {border_size} {border_size} {border_size} stretch;
            }}
        """
        
        return stylesheet


def apply_texture_stylesheets(app: QApplication):
    """
    Apply texture stylesheets to the application.
    Call this after creating QApplication but before showing windows.
    """
    from pathlib import Path
    import os
    
    # Get the assets directory - use absolute path
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS)
    else:
        # In development, go from ui/ -> project root
        base_path = Path(__file__).parent.parent.parent
    
    assets_dir = base_path / "assets"
    
    # If not found at parent.parent.parent, try parent.parent
    if not assets_dir.exists():
        base_path = Path(__file__).parent.parent
        assets_dir = base_path / "assets"
    
    assets_dir_str = str(assets_dir.resolve())
    
    logging.getLogger(__name__).info(f"Base path: {base_path}")
    logging.getLogger(__name__).info(f"Assets directory: {assets_dir_str}")
    logging.getLogger(__name__).info(f"Assets exists: {assets_dir.exists()}")
    
    # List some texture files
    if assets_dir.exists():
        button_dir = assets_dir / "buttons"
        if button_dir.exists():
            btn_files = list(button_dir.glob("*.png"))
            logging.getLogger(__name__).info(f"Button textures: {[f.name for f in btn_files]}")
    
    # Check if assets directory exists
    if not assets_dir.exists():
        logging.getLogger(__name__).warning(f"Assets directory not found: {assets_dir}")
        # Generate textures using generate_gui_textures.py
        try:
            from generate_gui_textures import generate_fast_textures
            logging.getLogger(__name__).info("Generating textures...")
            generate_fast_textures()
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to generate textures: {e}")
            return
    
    # Generate the global stylesheet with absolute path
    stylesheet = TextureStylesheetGenerator.apply_global_stylesheet(assets_dir_str)
    
    if stylesheet:
        # Get current stylesheet and append textures
        current = app.styleSheet()
        app.setStyleSheet(current + "\n" + stylesheet)
        logging.getLogger(__name__).info("Texture stylesheets applied")
        # Log a sample of the generated stylesheet for debugging
        sample = stylesheet[:500] if len(stylesheet) > 500 else stylesheet
        logging.getLogger(__name__).debug(f"Sample stylesheet: {sample}")
    else:
        logging.getLogger(__name__).warning("No texture stylesheets generated")
