"""
Fallout 2 Custom UI Components
Advanced UI widgets with authentic Fallout 2 styling including:
- Custom buttons with retro pixel-art styling
- Stat bars resembling SPECIAL system displays
- CRT scanline effects and flickering
- Weathered rust textures and borders
- Terminal-style dialog boxes
"""

from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QTextEdit, 
    QListWidget, QTreeWidget, QProgressBar, QFrame,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtSignal, QRect, QPoint, QMimeData
)
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient, 
    QConicalGradient, QFont, QCursor, QEnterEvent,
    QPaintEvent, QResizeEvent, QShowEvent
)
import random
import math


# =============================================================================
# FALLOUT BUTTONS
# =============================================================================

class FalloutButton(QPushButton):
    """Custom button with Fallout 2 styling"""
    
    def __init__(self, text: str = "", button_type: str = "standard", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self._hover_animation = None
        self._setup_button()
    
    def _setup_button(self):
        """Setup button appearance based on type"""
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(32)
        
        # Apply type-specific styling
        if self.button_type == "rust":
            self._apply_rust_style()
        elif self.button_type == "terminal":
            self._apply_terminal_style()
        elif self.button_type == "danger":
            self._apply_danger_style()
        else:
            self._apply_standard_style()
    
    def _apply_standard_style(self):
        """Apply standard military-style button"""
        colors = FalloutColors()
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {colors.OLIVE_DRAB},
                    stop: 0.5 {colors.DARK_OLIVE_GREEN},
                    stop: 1 {colors.MILITARY_GREEN}
                );
                color: {colors.TEXT_NORMAL};
                border: 3px outset {colors.PANEL_BORDER};
                border-radius: 4px;
                padding: 8px 20px;
                font-family: Consolas;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {colors.FADED_GREEN},
                    stop: 0.5 {colors.OLIVE_DRAB},
                    stop: 1 {colors.DARK_OLIVE_GREEN}
                );
                color: {colors.FALLOUT_YELLOW};
                border: 3px solid {colors.RUST_ORANGE};
            }}
            QPushButton:pressed {{
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {colors.MILITARY_GREEN},
                    stop: 0.5 {colors.DARK_OLIVE_GREEN},
                    stop: 1 {colors.OLIVE_DRAB}
                );
                border: 3px inset {colors.PANEL_BORDER};
            }}
            QPushButton:disabled {{
                background-color: {colors.DARK_METAL};
                color: {colors.TEXT_DIM};
                border: 2px solid {colors.DARK_METAL};
            }}
        """)
    
    def _apply_rust_style(self):
        """Apply rusty metal button style"""
        colors = FalloutColors()
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {colors.COPPER_RUST},
                    stop: 0.3 {colors.RUST_BROWN},
                    stop: 0.7 {colors.BURNISHED_BROWN},
                    stop: 1 {colors.RUST_ORANGE}
                );
                color: {colors.TEXT_NORMAL};
                border: 3px outset {colors.DARK_RUST};
                border-radius: 4px;
                padding: 8px 20px;
                font-family: Consolas;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {colors.RUST_ORANGE},
                    stop: 0.5 {colors.COPPER_RUST},
                    stop: 1 {colors.RUST_BROWN}
                );
                color: {colors.FALLOUT_YELLOW};
                border: 3px solid {colors.FALLOUT_YELLOW};
            }}
            QPushButton:pressed {{
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {colors.DARK_RUST},
                    stop: 0.5 {colors.RUST_ORANGE},
                    stop: 1 {colors.COPPER_RUST}
                );
                border: 3px inset {colors.DARK_RUST};
            }}
        """)
    
    def _apply_terminal_style(self):
        """Apply Pip-Boy terminal button style"""
        colors = FalloutColors()
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.PIPBOY_SCREEN};
                color: {colors.TERMINAL_GREEN};
                border: 2px solid {colors.DIM_GREEN};
                border-radius: 2px;
                padding: 6px 16px;
                font-family: Consolas;
                font-size: 11pt;
            }}
            QPushButton:hover {{
                background-color: #1a2a1a;
                color: {colors.BRIGHT_GREEN};
                border: 2px solid {colors.TERMINAL_GREEN};
            }}
            QPushButton:pressed {{
                background-color: #0a150a;
                color: {colors.DIM_GREEN};
            }}
        """)
    
    def _apply_danger_style(self):
        """Apply danger/delete button style"""
        colors = FalloutColors()
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {colors.DARK_RUST},
                    stop: 0.5 {colors.RUST_ORANGE},
                    stop: 1 {colors.DARK_RUST}
                );
                color: {colors.TEXT_BRIGHT};
                border: 3px outset {colors.RUST_ORANGE};
                border-radius: 4px;
                padding: 8px 20px;
                font-family: Consolas;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {colors.STATUS_RED},
                    stop: 0.5 {colors.DARK_RUST},
                    stop: 1 {colors.RUST_ORANGE}
                );
                color: {colors.FALLOUT_YELLOW};
                border: 3px solid {colors.FALLOUT_YELLOW};
            }}
            QPushButton:pressed {{
                border: 3px inset {colors.STATUS_RED};
            }}
        """)


class FalloutIconButton(FalloutButton):
    """Small icon button for toolbars"""
    
    def __init__(self, icon_text: str = "●", parent=None):
        super().__init__(icon_text, "standard", parent)
        self.setFixedSize(28, 28)
        self.setStyleSheet(self.styleSheet() + """
            QPushButton {
                padding: 4px;
                min-width: 24px;
                min-height: 24px;
            }
        """)


# Import colors from theme module
from ui.fallout_theme import FalloutColors


# =============================================================================
# SPECIAL STAT BAR WIDGET
# =============================================================================

class SpecialStatBar(QFrame):
    """SPECIAL stat bar like in Fallout"""
    
    valueChanged = pyqtSignal(int)
    
    def __init__(self, stat_name: str = "S", current_value: int = 5, 
                 max_value: int = 10, parent=None):
        super().__init__(parent)
        self.stat_name = stat_name
        self._current_value = current_value
        self._max_value = max_value
        self.setMinimumHeight(24)
        self.setMinimumWidth(160)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(4)
        shadow.setOffset(1, 1)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)
    
    def value(self) -> int:
        return self._current_value
    
    def setValue(self, value: int):
        self._current_value = max(0, min(value, self._max_value))
        self.valueChanged.emit(self._current_value)
        self.update()
    
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        colors = FalloutColors()
        rect = self.rect()
        
        # Background (inset look)
        bg_color = QColor(colors.DARK_SLATE)
        painter.fillRect(rect, bg_color)
        
        # Draw inset border
        pen = QPen(QColor(colors.DARK_METAL))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(rect.adjusted(1, 1, -2, -2))
        
        # Calculate bar dimensions
        bar_x = 4
        bar_y = 4
        bar_width = rect.width() - 8
        bar_height = rect.height() - 8
        
        # Determine color based on value
        if self._current_value <= 2:
            bar_color = QColor(colors.STATUS_RED)
        elif self._current_value <= 5:
            bar_color = QColor(colors.STATUS_ORANGE)
        else:
            bar_color = QColor(colors.FALLOUT_YELLOW)
        
        # Draw filled portion
        fill_width = int(bar_width * (self._current_value / self._max_value))
        
        # Create gradient for filled portion
        gradient = QLinearGradient(bar_x, bar_y, bar_x, bar_y + bar_height)
        gradient.setColorAt(0, bar_color.lighter(120))
        gradient.setColorAt(0.5, bar_color)
        gradient.setColorAt(1, bar_color.darker(120))
        
        filled_rect = QRect(bar_x, bar_y, fill_width, bar_height)
        painter.fillRect(filled_rect, gradient)
        
        # Draw stat letter
        font = QFont("Consolas", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(colors.TEXT_NORMAL))
        
        # Position stat letter
        letter_rect = QRect(bar_x, bar_y, 20, bar_height)
        painter.drawText(letter_rect, Qt.AlignmentFlag.AlignCenter, self.stat_name)
        
        # Draw value number
        painter.setPen(bar_color)
        value_rect = QRect(bar_x + bar_width - 20, bar_y, 20, bar_height)
        painter.drawText(value_rect, Qt.AlignmentFlag.AlignCenter, str(self._current_value))


class FalloutProgressBar(QProgressBar):
    """Styled progress bar with Fallout aesthetics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._apply_fallout_style()
    
    def _apply_fallout_style(self):
        colors = FalloutColors()
        self.setStyleSheet(f"""
            QProgressBar {{
                background-color: {colors.DARK_SLATE};
                border: 2px inset {colors.DARK_METAL};
                border-radius: 4px;
                text-align: center;
                color: {colors.TEXT_NORMAL};
                font-family: Consolas;
                font-weight: bold;
                font-size: 10pt;
            }}
            QProgressBar::chunk {{
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {colors.DARK_OLIVE_GREEN},
                    stop: 0.5 {colors.OLIVE_DRAB},
                    stop: 1 {colors.DARK_OLIVE_GREEN}
                );
                border-radius: 2px;
            }}
        """)


# =============================================================================
# CRT EFFECT WIDGETS
# =============================================================================

class CRTScanlineOverlay(QFrame):
    """Widget that adds CRT scanline effect to any widget it overlays"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        # Scanline animation timer
        self._scanline_offset = 0
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._update_scanline)
        self._animation_timer.start(50)  # Update every 50ms
        
        # Flicker settings
        self._flicker_enabled = True
        self._opacity = 1.0
    
    def _update_scanline(self):
        self._scanline_offset = (self._scanline_offset + 1) % 4
        self.update()
    
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        colors = FalloutColors()
        rect = self.rect()
        
        # Draw scanlines
        painter.setPen(QColor(0, 0, 0, 30))
        for y in range(0, rect.height(), 4):
            if (y // 4 + self._scanline_offset) % 2 == 0:
                painter.drawLine(0, y, rect.width(), y)
        
        # Add subtle vignette effect
        gradient = QLinearGradient(
            rect.topLeft(), rect.center()
        )
        gradient.setColorAt(0, QColor(0, 0, 0, 0))
        gradient.setColorAt(0.5, QColor(0, 0, 0, 40))
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(rect, gradient)
        
        # Subtle screen flicker
        if self._flicker_enabled:
            flicker_opacity = random.uniform(0.97, 1.0)
            painter.setOpacity(flicker_opacity)


class FlickeringLabel(QLabel):
    """Label with subtle CRT flicker effect"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._flicker_timer = QTimer(self)
        self._flicker_timer.timeout.connect(self._flicker)
        self._flicker_timer.start(100)
        self._visible = True
    
    def _flicker(self):
        # Subtle flicker effect
        if random.random() < 0.02:  # 2% chance of flicker per tick
            self._visible = not self._visible
            self.setVisible(self._visible)
            QTimer.singleShot(50, lambda: self.setVisible(True))


# =============================================================================
# WEATHERED PANELS
# =============================================================================

class FalloutPanel(QFrame):
    """Base panel with Fallout styling"""
    
    def __init__(self, panel_type: str = "standard", parent=None):
        super().__init__(parent)
        self.panel_type = panel_type
        self._apply_panel_style()
    
    def _apply_panel_style(self):
        colors = FalloutColors()
        
        if self.panel_type == "metal":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: qlineargradient(
                        x1: 0, y1: 0, x2: 1, y2: 1,
                        stop: 0 {colors.DARK_METAL},
                        stop: 0.3 {colors.PANEL_HIGHLIGHT},
                        stop: 0.7 {colors.DARK_METAL},
                        stop: 1 {colors.CHARCOAL}
                    );
                    border: 3px outset {colors.PANEL_BORDER};
                    border-radius: 4px;
                }}
            """)
        elif self.panel_type == "rust":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: qlineargradient(
                        x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 {colors.WOOD_BROWN},
                        stop: 0.3 {colors.RUST_BROWN},
                        stop: 0.6 {colors.COPPER_RUST},
                        stop: 1 {colors.WOOD_BROWN}
                    );
                    border: 3px solid {colors.DARK_RUST};
                    border-radius: 4px;
                }}
            """)
        elif self.panel_type == "pipboy":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.PIPBOY_SCREEN};
                    border: 2px solid {colors.DIM_GREEN};
                    border-radius: 4px;
                }}
            """)
        else:  # standard
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.PANEL_BACKGROUND};
                    border: 3px solid {colors.PANEL_BORDER};
                    border-radius: 4px;
                }}
            """)


class WornMetalPanel(FalloutPanel):
    """Panel with worn metal texture effect"""
    
    def __init__(self, parent=None):
        super().__init__("metal", parent)
    
    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        
        # Add scratches and wear marks
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        colors = FalloutColors()
        
        # Draw random scratch marks
        painter.setPen(QColor(colors.DARK_SLATE))
        for i in range(5):
            x1 = random.randint(0, self.width())
            y1 = random.randint(0, self.height())
            x2 = x1 + random.randint(-30, 30)
            y2 = y1 + random.randint(-30, 30)
            painter.drawLine(x1, y1, x2, y2)


class RustyBorderFrame(QFrame):
    """Frame with rusty, corroded border effect"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {FalloutColors.PANEL_BACKGROUND};
                border: 3px outset {FalloutColors.RUST_ORANGE};
                border-radius: 4px;
            }}
        """)


# =============================================================================
# TERMINAL-STYLE WIDGETS
# =============================================================================

class TerminalTextEdit(QTextEdit):
    """Text edit with Pip-Boy terminal styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._apply_terminal_style()
    
    def _apply_terminal_style(self):
        colors = FalloutColors()
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors.PIPBOY_SCREEN};
                color: {colors.TERMINAL_GREEN};
                border: 2px solid {colors.DIM_GREEN};
                border-radius: 4px;
                font-family: Consolas;
                font-size: 11pt;
                selection-background-color: {colors.DIM_GREEN};
                selection-color: {colors.BRIGHT_GREEN};
            }}
            QTextEdit:focus {{
                border: 2px solid {colors.TERMINAL_GREEN};
            }}
        """)


class TerminalLabel(QLabel):
    """Label with terminal text styling"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        colors = FalloutColors()
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {colors.PIPBOY_SCREEN};
                color: {colors.TERMINAL_GREEN};
                border: 1px solid {colors.DIM_GREEN};
                border-radius: 2px;
                padding: 4px 8px;
                font-family: Consolas;
                font-size: 10pt;
            }}
        """)


class FalloutTreeWidget(QTreeWidget):
    """Tree widget with Fallout styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._apply_fallout_style()
    
    def _apply_fallout_style(self):
        colors = FalloutColors()
        self.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {colors.CHARCOAL};
                color: {colors.TEXT_NORMAL};
                border: 2px solid {colors.PANEL_BORDER};
                border-radius: 2px;
                padding: 4px;
                font-family: Consolas;
                font-size: 10pt;
                outline: 0;
            }}
            QTreeWidget::item:selected {{
                background-color: {colors.OLIVE_DRAB};
                color: {colors.FALLOUT_YELLOW};
            }}
            QTreeWidget::item:hover {{
                background-color: {colors.DARK_METAL};
                color: {colors.TEXT_BRIGHT};
            }}
            QTreeWidget::branch {{
                background-color: transparent;
            }}
        """)


class FalloutListWidget(QListWidget):
    """List widget with Fallout styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._apply_fallout_style()
    
    def _apply_fallout_style(self):
        colors = FalloutColors()
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {colors.CHARCOAL};
                color: {colors.TEXT_NORMAL};
                border: 2px solid {colors.PANEL_BORDER};
                border-radius: 2px;
                padding: 4px;
                font-family: Consolas;
                font-size: 10pt;
                outline: 0;
            }}
            QListWidget::item:selected {{
                background-color: {colors.OLIVE_DRAB};
                color: {colors.FALLOUT_YELLOW};
                border: 1px solid {colors.RUST_ORANGE};
            }}
            QListWidget::item:hover {{
                background-color: {colors.DARK_METAL};
                color: {colors.TEXT_BRIGHT};
            }}
        """)


# =============================================================================
# DIALOG COMPONENTS
# =============================================================================

class FalloutDialogFrame(QFrame):
    """Frame for dialog boxes with Fallout styling"""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self._setup_dialog_style()
    
    def _setup_dialog_style(self):
        colors = FalloutColors()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.DARK_SLATE};
                border: 4px outset {colors.PANEL_BORDER};
                border-radius: 6px;
            }}
        """)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(3, 3)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.setGraphicsEffect(shadow)
    
    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        
        # Draw corner decorations
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = FalloutColors()
        
        # Draw rivets in corners
        rivet_color = QColor(colors.PANEL_BORDER)
        painter.setPen(rivet_color)
        painter.setBrush(QBrush(rivet_color))
        
        # Corner positions
        corners = [
            (15, 15),
            (self.width() - 15, 15),
            (15, self.height() - 15),
            (self.width() - 15, self.height() - 15)
        ]
        
        for x, y in corners:
            painter.drawEllipse(QPoint(x, y), 4, 4)


class TypewriterLabel(QLabel):
    """Label that displays text with typewriter font"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        colors = FalloutColors()
        self.setStyleSheet(f"""
            QLabel {{
                background-color: transparent;
                color: {colors.TEXT_NORMAL};
                font-family: 'Courier New', Consolas;
                font-size: 11pt;
                padding: 4px;
            }}
        """)


# =============================================================================
# ANIMATION EFFECTS
# =============================================================================

class FalloutAnimationHelper:
    """Helper class for Fallout-style animations"""
    
    @staticmethod
    def create_flicker_animation(target: QWidget, duration: int = 5000) -> QPropertyAnimation:
        """Create a subtle flicker animation"""
        opacity_effect = QGraphicsOpacityEffect(target)
        target.setGraphicsEffect(opacity_effect)
        
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        
        # Create flicker keyframes
        key_values = [
            (0.0, 1.0),
            (0.9, 1.0),
            (0.92, 0.9),
            (0.94, 1.0),
            (0.97, 0.95),
            (0.98, 1.0),
            (1.0, 1.0)
        ]
        
        for time, value in key_values:
            animation.setKeyValueAt(time, value)
        
        animation.setEasingCurve(QEasingCurve.Type.Linear)
        return animation
    
    @staticmethod
    def create_glitch_animation(target: QWidget) -> QPropertyAnimation:
        """Create occasional glitch offset animation"""
        animation = QPropertyAnimation(target, b"pos")
        animation.setDuration(100)
        animation.setLoopCount(1)
        
        # Random offset
        offset_x = random.randint(-3, 3)
        offset_y = random.randint(-3, 3)
        
        animation.setKeyValueAt(0.0, target.pos())
        animation.setKeyValueAt(0.5, target.pos() + QPoint(offset_x, offset_y))
        animation.setKeyValueAt(1.0, target.pos())
        
        return animation


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'FalloutButton',
    'FalloutIconButton',
    'SpecialStatBar',
    'FalloutProgressBar',
    'CRTScanlineOverlay',
    'FlickeringLabel',
    'FalloutPanel',
    'WornMetalPanel',
    'RustyBorderFrame',
    'TerminalTextEdit',
    'TerminalLabel',
    'FalloutTreeWidget',
    'FalloutListWidget',
    'FalloutDialogFrame',
    'TypewriterLabel',
    'FalloutAnimationHelper',
]
