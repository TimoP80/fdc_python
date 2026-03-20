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
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
    QVBoxLayout, QHBoxLayout
)
from PyQt6.QtCore import (
    Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtSignal, QRect, QPoint, QMimeData
)
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient,
    QConicalGradient, QFont, QCursor, QEnterEvent,
    QPaintEvent, QResizeEvent, QShowEvent, QPixmap
)
import random
import math

# Import colors from theme module - must be before class definitions
from ui.fallout_theme import FalloutColors
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
        """Apply standard military-style button with skeuomorphic 3D effect"""
        colors = FalloutColors()
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #5a7a2a,
                    stop: 0.15 #4a6a1a,
                    stop: 0.4 #4a5d23,
                    stop: 0.6 #3d4f2a,
                    stop: 1 #2d3f1a
                );
                color: #d4c4a8;
                border: 3px outset #6b8e23;
                border-top-color: #8fa863;
                border-left-color: #8fa863;
                border-right-color: #3d4f2a;
                border-bottom-color: #3d4f2a;
                border-radius: 4px;
                padding: 8px 20px;
                font-family: Consolas;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #6b8e23,
                    stop: 0.15 #5a7a2a,
                    stop: 0.4 #556b2f,
                    stop: 0.6 #4a5d23,
                    stop: 1 #3d4f2a
                );
                color: #ffcc00;
                border: 3px outset #8fa863;
                border-top-color: #a8c878;
                border-left-color: #a8c878;
                border-right-color: #556b2f;
                border-bottom-color: #556b2f;
            }}
            QPushButton:pressed {{
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2d3f1a,
                    stop: 0.15 #3d4f2a,
                    stop: 0.4 #4a5d23,
                    stop: 0.6 #4a5d23,
                    stop: 1 #556b2f
                );
                color: #ffffff;
                border: 3px inset #3d4f2a;
                border-top-color: #2d3f1a;
                border-left-color: #2d3f1a;
                border-right-color: #6b8e23;
                border-bottom-color: #6b8e23;
            }}
            QPushButton:disabled {{
                background-color: #3a3a3a;
                color: #5c5c5c;
                border: 2px solid #3a3a3a;
            }}
        """)
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(4)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)
    
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
        if self._max_value == 0:
            self._max_value = 1  # Prevent division by zero
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
        
        # Scanline animation timer - will be started in showEvent
        self._scanline_offset = 0
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._update_scanline)
        self._animation_timer.setSingleShot(False)
        
        # Flicker settings
        self._flicker_enabled = True
        self._opacity = 1.0
    
    def showEvent(self, event):
        """Start animation when widget becomes visible"""
        super().showEvent(event)
        if not self._animation_timer.isActive():
            self._animation_timer.start(50)  # Update every 50ms
    
    def hideEvent(self, event):
        """Stop animation when widget becomes hidden"""
        super().hideEvent(event)
        if self._animation_timer.isActive():
            self._animation_timer.stop()
    
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
                        stop: 0 #4a4a48,
                        stop: 0.3 #5a5a58,
                        stop: 0.7 #3a3a38,
                        stop: 1 #2d2d2d
                    );
                    border: 3px outset #5c5c5c;
                    border-top-color: #6a6a6a;
                    border-left-color: #6a6a6a;
                    border-right-color: #4a4a4a;
                    border-bottom-color: #4a4a4a;
                    border-radius: 4px;
                }}
            """)
            # Add shadow effect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(8)
            shadow.setOffset(3, 3)
            shadow.setColor(QColor(0, 0, 0, 120))
            self.setGraphicsEffect(shadow)
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
                    border: 3px outset {colors.DARK_RUST};
                    border-top-color: #a04a1e;
                    border-left-color: #a04a1e;
                    border-right-color: #6b2a0e;
                    border-bottom-color: #6b2a0e;
                    border-radius: 4px;
                }}
            """)
            # Add shadow effect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(6)
            shadow.setOffset(2, 2)
            shadow.setColor(QColor(0, 0, 0, 100))
            self.setGraphicsEffect(shadow)
        elif self.panel_type == "pipboy":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.PIPBOY_SCREEN};
                    border: 2px outset {colors.DIM_GREEN};
                    border-top-color: {colors.BRIGHT_GREEN};
                    border-left-color: {colors.BRIGHT_GREEN};
                    border-right-color: #0a150a;
                    border-bottom-color: #0a150a;
                    border-radius: 4px;
                }}
            """)
        else:  # standard
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: qlineargradient(
                        x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #3a3a38,
                        stop: 1 #2a2a28
                    );
                    border: 3px outset #5c5c5c;
                    border-top-color: #6a6a6a;
                    border-left-color: #6a6a6a;
                    border-right-color: #4a4a4a;
                    border-bottom-color: #4a4a4a;
                    border-radius: 4px;
                }}
            """)
            # Add shadow effect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(6)
            shadow.setOffset(2, 2)
            shadow.setColor(QColor(0, 0, 0, 80))
            self.setGraphicsEffect(shadow)


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
# FADE ANIMATION SUPPORT
# =============================================================================

class FadeAnimationMixin:
    """
    Mixin class that provides smooth fade-in and fade-out transitions
    for form elements. Supports 300ms duration with ease-in-out timing
    and respects reduced motion accessibility preferences.
    """
    
    # Animation constants
    FADE_DURATION = 300  # milliseconds
    FADE_EASING = QEasingCurve.Type.InOutQuad
    
    def __init__(self):
        self._fade_opacity_effect: QGraphicsOpacityEffect = None
        self._fade_animation: QPropertyAnimation = None
        self._is_fading = False
        self._setup_fade_effects()
    
    def _setup_fade_effects(self):
        """Initialize the opacity effect for fade animations"""
        # Check for reduced motion preference
        self._reduced_motion = self._check_reduced_motion()
        
        # Create opacity effect
        self._fade_opacity_effect = QGraphicsOpacityEffect(self)
        self._fade_opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._fade_opacity_effect)
        
        # Create animation object
        self._fade_animation = QPropertyAnimation(
            self._fade_opacity_effect, b"opacity", self
        )
        self._fade_animation.setDuration(self.FADE_DURATION)
        self._fade_animation.setEasingCurve(self.FADE_EASING)
    
    @staticmethod
    def _check_reduced_motion() -> bool:
        """Check if user prefers reduced motion (accessibility)"""
        try:
            from PyQt6.QtCore import QSettings
            settings = QSettings("Qt", "PAFE")  # Qt Application Framework Environment
            # Check Qt's accessibility settings
            if settings.contains("Accessibility/ReduceMotion"):
                return settings.value("Accessibility/ReduceMotion", type=bool)
            # Also check system-level animation preference
            from PyQt6.QtGui import QGuiApplication
            return QGuiApplication.testAttribute(Qt.ApplicationAttribute.AA_DisableWindowActivation)
        except Exception:
            return False
    
    def fade_in(self, duration: int = None):
        """
        Fade in the widget (opacity: 0 -> 1)
        
        Args:
            duration: Optional custom duration in milliseconds. 
                     Uses default 300ms if not specified.
        """
        if self._reduced_motion:
            # Skip animation for reduced motion preference
            self._fade_opacity_effect.setOpacity(1.0)
            return
        
        if self._is_fading:
            self._fade_animation.stop()
        
        self._is_fading = True
        
        if duration is not None:
            self._fade_animation.setDuration(duration)
        else:
            self._fade_animation.setDuration(self.FADE_DURATION)
        
        self._fade_animation.setStartValue(0.0)
        self._fade_animation.setEndValue(1.0)
        
        self._fade_animation.finished.connect(lambda: setattr(self, '_is_fading', False))
        self._fade_animation.start()
    
    def fade_out(self, duration: int = None):
        """
        Fade out the widget (opacity: 1 -> 0)
        
        Args:
            duration: Optional custom duration in milliseconds.
                     Uses default 300ms if not specified.
        """
        if self._reduced_motion:
            # Skip animation for reduced motion preference
            self._fade_opacity_effect.setOpacity(0.0)
            return
        
        if self._is_fading:
            self._fade_animation.stop()
        
        self._is_fading = True
        
        if duration is not None:
            self._fade_animation.setDuration(duration)
        else:
            self._fade_animation.setDuration(self.FADE_DURATION)
        
        self._fade_animation.setStartValue(1.0)
        self._fade_animation.setEndValue(0.0)
        
        self._fade_animation.finished.connect(lambda: setattr(self, '_is_fading', False))
        self._fade_animation.start()
    
    def set_opacity(self, opacity: float):
        """Set the opacity directly without animation"""
        self._fade_opacity_effect.setOpacity(max(0.0, min(1.0, opacity)))
    
    def get_opacity(self) -> float:
        """Get the current opacity value"""
        return self._fade_opacity_effect.opacity()


class FadeLineEdit(QLineEdit, FadeAnimationMixin):
    """
    Line edit widget with fade-in/fade-out transitions.
    Fade-in triggers on focus, fade-out on blur.
    """
    
    def __init__(self, text: str = "", parent=None):
        QLineEdit.__init__(self, text, parent)
        FadeAnimationMixin.__init__(self)
        self.setText(text)
        self._setup_fade_connections()
    
    def _setup_fade_connections(self):
        """Connect focus events to fade animations"""
        # Note: We use timer to ensure widget is fully shown before fading in
        self.focusInEvent = self._on_focus_in
        self.focusOutEvent = self._on_focus_out
    
    def _on_focus_in(self, event):
        """Handle focus in - fade in"""
        QLineEdit.focusInEvent(self, event)
        # Fade in on focus
        self.fade_in()
    
    def _on_focus_out(self, event):
        """Handle focus out - fade out"""
        QLineEdit.focusOutEvent(self, event)
        # Fade out on blur
        self.fade_out()
    
    def showEvent(self, event):
        """Fade in when widget is first shown"""
        QLineEdit.showEvent(self, event)
        self.fade_in()


class FadeTextEdit(QTextEdit, FadeAnimationMixin):
    """
    Text edit widget with fade-in/fade-out transitions.
    Fade-in triggers on focus, fade-out on blur.
    """
    
    def __init__(self, text: str = "", parent=None):
        QTextEdit.__init__(self, text, parent)
        FadeAnimationMixin.__init__(self)
        self.setPlainText(text)
        self._setup_fade_connections()
    
    def _setup_fade_connections(self):
        """Connect focus events to fade animations"""
        self.focusInEvent = self._on_focus_in
        self.focusOutEvent = self._on_focus_out
    
    def _on_focus_in(self, event):
        """Handle focus in - fade in"""
        QTextEdit.focusInEvent(self, event)
        self.fade_in()
    
    def _on_focus_out(self, event):
        """Handle focus out - fade out"""
        QTextEdit.focusOutEvent(self, event)
        self.fade_out()
    
    def showEvent(self, event):
        """Fade in when widget is first shown"""
        QTextEdit.showEvent(self, event)
        self.fade_in()


class FadeLabel(QLabel, FadeAnimationMixin):
    """
    Label widget with fade-in/fade-out transitions.
    Useful for validation messages and status indicators.
    """
    
    def __init__(self, text: str = "", parent=None):
        QLabel.__init__(self, text, parent)
        FadeAnimationMixin.__init__(self)
        self.setText(text)
    
    def showEvent(self, event):
        """Fade in when label is shown (e.g., validation message appears)"""
        QLabel.showEvent(self, event)
        self.fade_in()
    
    def hideEvent(self, event):
        """Fade out when label is hidden"""
        self.fade_out()
        # Call parent hide after fade starts
        QLabel.hideEvent(self, event)


class FadeButton(FalloutButton, FadeAnimationMixin):
    """
    Button widget with fade-in/fade-out transitions.
    Fade effects trigger on hover/press and on show/hide.
    """
    
    def __init__(self, text: str = "", button_type: str = "standard", parent=None):
        FalloutButton.__init__(self, text, button_type, parent)
        FadeAnimationMixin.__init__(self)
    
    def showEvent(self, event):
        """Fade in when button is shown"""
        FalloutButton.showEvent(self, event)
        self.fade_in()
    
    def hideEvent(self, event):
        """Fade out when button is hidden"""
        self.fade_out()
        FalloutButton.hideEvent(self, event)


class FadeValidationMessage(QFrame, FadeAnimationMixin):
    """
    Validation/error message widget with fade transitions.
    Shows error or success messages with appropriate styling.
    """
    
    # Message types
    ERROR = "error"
    SUCCESS = "success"
    WARNING = "warning"
    INFO = "info"
    
    def __init__(self, message: str = "", message_type: str = "info", parent=None):
        QFrame.__init__(self, parent)
        FadeAnimationMixin.__init__(self)
        
        self._message_type = message_type
        self._message_label = QLabel(message, self)
        
        # Setup layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.addWidget(self._message_label)
        
        # Apply styling based on message type
        self._apply_message_style()
        
        # Initially hidden
        self.hide()
    
    def _apply_message_style(self):
        """Apply styling based on message type"""
        colors = FalloutColors()
        
        if self._message_type == self.ERROR:
            bg_color = "#3d2020"
            border_color = colors.STATUS_RED
            text_color = "#ff6666"
        elif self._message_type == self.SUCCESS:
            bg_color = "#203d20"
            border_color = "#33cc33"
            text_color = "#66ff66"
        elif self._message_type == self.WARNING:
            bg_color = "#3d3d20"
            border_color = colors.STATUS_YELLOW
            text_color = "#ffff66"
        else:  # INFO
            bg_color = "#20303d"
            border_color = "#3366cc"
            text_color = "#6699ff"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 4px;
            }}
            QLabel {{
                color: {text_color};
                font-family: Consolas;
                font-size: 9pt;
            }}
        """)
    
    def set_message(self, text: str, message_type: str = None):
        """Set the message text and optionally change message type"""
        if message_type is not None and message_type != self._message_type:
            self._message_type = message_type
            self._apply_message_style()
        
        self._message_label.setText(text)
    
    def show_message(self, text: str = None, message_type: str = None):
        """Show the message with fade-in animation"""
        if text is not None:
            self.set_message(text, message_type)
        self.show()
        self.fade_in()
    
    def hide_message(self):
        """Hide the message with fade-out animation"""
        self.fade_out()
        # Actually hide after animation completes
        QTimer.singleShot(self.FADE_DURATION, self.hide)


# =============================================================================
# ANIMATION EFFECTS
# =============================================================================

class FalloutAnimationHelper:
    """Helper class for Fallout-style animations"""
    
    # Animation constants for consistency
    FADE_DURATION = 300  # milliseconds
    FADE_EASING = QEasingCurve.Type.InOutQuad
    
    @staticmethod
    def create_fade_in_animation(target: QWidget, duration: int = None) -> QPropertyAnimation:
        """
        Create a fade-in animation (opacity: 0 -> 1)
        
        Args:
            target: The widget to animate
            duration: Animation duration in milliseconds (default: 300ms)
            
        Returns:
            QPropertyAnimation configured for fade-in
        """
        if duration is None:
            duration = FalloutAnimationHelper.FADE_DURATION
        
        # Check reduced motion preference
        if FalloutAnimationHelper._check_reduced_motion():
            opacity_effect = QGraphicsOpacityEffect(target)
            opacity_effect.setOpacity(1.0)
            target.setGraphicsEffect(opacity_effect)
            return None
        
        opacity_effect = QGraphicsOpacityEffect(target)
        target.setGraphicsEffect(opacity_effect)
        
        animation = QPropertyAnimation(opacity_effect, b"opacity", target)
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(FalloutAnimationHelper.FADE_EASING)
        
        return animation
    
    @staticmethod
    def create_fade_out_animation(target: QWidget, duration: int = None) -> QPropertyAnimation:
        """
        Create a fade-out animation (opacity: 1 -> 0)
        
        Args:
            target: The widget to animate
            duration: Animation duration in milliseconds (default: 300ms)
            
        Returns:
            QPropertyAnimation configured for fade-out
        """
        if duration is None:
            duration = FalloutAnimationHelper.FADE_DURATION
        
        # Check reduced motion preference
        if FalloutAnimationHelper._check_reduced_motion():
            opacity_effect = QGraphicsOpacityEffect(target)
            opacity_effect.setOpacity(0.0)
            target.setGraphicsEffect(opacity_effect)
            return None
        
        opacity_effect = QGraphicsOpacityEffect(target)
        target.setGraphicsEffect(opacity_effect)
        
        animation = QPropertyAnimation(opacity_effect, b"opacity", target)
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(FalloutAnimationHelper.FADE_EASING)
        
        return animation
    
    @staticmethod
    def _check_reduced_motion() -> bool:
        """Check if user prefers reduced motion (accessibility)"""
        try:
            # Check Qt accessibility settings
            from PyQt6.QtCore import QSettings
            settings = QSettings("Qt", "PAFE")
            if settings.contains("Accessibility/ReduceMotion"):
                return settings.value("Accessibility/ReduceMotion", type=bool)
            
            # Also check system accessibility
            from PyQt6.QtGui import QGuiApplication
            return QGuiApplication.testAttribute(Qt.ApplicationAttribute.AA_DisableWindowActivation)
        except Exception:
            return False
    
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
# TEXTURE-ENABLED WIDGETS
# =============================================================================

from ui.texture_system import (
    TextureGenerator, TextureStyle, TexturePainter, TextureCache
)


class TexturedFalloutButton(QPushButton):
    """
    Custom button with realistic texture materials and bump mapping.
    
    Supports multiple texture types:
    - wood: Oak, pine, or walnut wood grain
    - metal: Steel, copper, brass with scratches
    - rust: Worn, rusted metal surface
    - leather: Brown, tan, or dark leather
    - concrete: Gray concrete with cracks
    """
    
    def __init__(self, text: str = "", texture_type: str = "metal",
                 parent=None):
        super().__init__(text, parent)
        self._texture_type = texture_type
        self._texture_cache = {}
        self._normal_map_cache = {}
        self._is_pressed = False
        self._is_hovered = False
        
        # Get texture style
        self._style = self._get_style_for_type(texture_type)
        
        self._setup_button()
    
    def _get_style_for_type(self, tex_type: str) -> dict:
        """Get texture style configuration for button type"""
        styles = {
            "wood": TextureStyle.BUTTON_STANDARD,
            "metal": TextureStyle.BUTTON_METAL,
            "rust": TextureStyle.BUTTON_RUST,
            "leather": TextureStyle.BUTTON_LEATHER,
            "steel": {**TextureStyle.BUTTON_METAL, "metal_type": "steel"},
            "copper": {**TextureStyle.BUTTON_METAL, "metal_type": "copper"},
            "brass": {**TextureStyle.BUTTON_METAL, "metal_type": "brass"},
            "oak": {**TextureStyle.BUTTON_STANDARD, "wood_type": "oak"},
            "pine": {**TextureStyle.BUTTON_STANDARD, "wood_type": "pine"},
            "walnut": {**TextureStyle.BUTTON_STANDARD, "wood_type": "walnut"},
            "brown_leather": {**TextureStyle.BUTTON_LEATHER, "leather_type": "brown"},
            "tan_leather": {**TextureStyle.BUTTON_LEATHER, "leather_type": "tan"},
        }
        return styles.get(tex_type, TextureStyle.BUTTON_METAL)
    
    def _setup_button(self):
        """Setup button appearance"""
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(36)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Set base stylesheet (colors, fonts, etc.)
        self._apply_base_stylesheet()
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(6)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(shadow)
    
    def _apply_base_stylesheet(self):
        """Apply base QSS stylesheet for colors and fonts"""
        colors = FalloutColors()
        self.setStyleSheet(f"""
            QPushButton {{
                color: #d4c4a8;
                border: 3px outset #5c5c5c;
                border-radius: 4px;
                padding: 8px 20px;
                font-family: Consolas;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                color: #ffcc00;
                border: 3px outset #8fa863;
            }}
            QPushButton:pressed {{
                color: #ffffff;
                border: 3px inset #3d4f2a;
            }}
            QPushButton:disabled {{
                background-color: #3a3a3a;
                color: #5c5c5c;
                border: 2px solid #3a3a3a;
            }}
        """)
    
    def _generate_texture(self, width: int, height: int, 
                          variant: str = "normal") -> QPixmap:
        """Generate texture with caching"""
        cache_key = f"{self._texture_type}_{width}x{height}_{variant}"
        
        if cache_key not in self._texture_cache:
            # Generate texture based on type and variant
            tex_type = self._style.get("type", "metal")
            
            if tex_type == "wood":
                self._texture_cache[cache_key] = TextureGenerator.generate_wood_texture(
                    width, height,
                    wood_type=self._style.get("wood_type", "oak"),
                    scale=self._style.get("scale", 10.0),
                    seed=self._style.get("seed", 42) + (100 if variant == "hover" else 0)
                )
            elif tex_type == "metal":
                self._texture_cache[cache_key] = TextureGenerator.generate_metal_texture(
                    width, height,
                    metal_type=self._style.get("metal_type", "steel"),
                    scratches=self._style.get("scratches", True),
                    seed=self._style.get("seed", 42) + (100 if variant == "hover" else 0)
                )
            elif tex_type == "rust":
                intensity = self._style.get("intensity", 0.7)
                if variant == "hover":
                    intensity = min(1.0, intensity + 0.15)
                self._texture_cache[cache_key] = TextureGenerator.generate_rust_texture(
                    width, height,
                    intensity=intensity,
                    seed=self._style.get("seed", 42)
                )
            elif tex_type == "leather":
                self._texture_cache[cache_key] = TextureGenerator.generate_leather_texture(
                    width, height,
                    leather_type=self._style.get("leather_type", "brown"),
                    worn=self._style.get("worn", True),
                    seed=self._style.get("seed", 42) + (100 if variant == "hover" else 0)
                )
            elif tex_type == "concrete":
                self._texture_cache[cache_key] = TextureGenerator.generate_concrete_texture(
                    width, height,
                    dirty=self._style.get("dirty", True),
                    seed=self._style.get("seed", 42)
                )
            else:
                # Default metal
                self._texture_cache[cache_key] = TextureGenerator.generate_metal_texture(
                    width, height, metal_type="steel", scratches=True
                )
        
        return self._texture_cache[cache_key]
    
    def _get_normal_map(self, texture: QPixmap) -> QPixmap:
        """Get or generate normal map for bump effect"""
        cache_key = id(texture)
        
        if cache_key not in self._normal_map_cache:
            strength = self._style.get("bump_strength", 1.0)
            self._normal_map_cache[cache_key] = TextureGenerator.generate_normal_map(
                texture, strength
            )
        
        return self._normal_map_cache[cache_key]
    
    def enterEvent(self, event):
        """Handle mouse enter - show hover texture"""
        self._is_hovered = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave"""
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        self._is_pressed = True
        self.update()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self._is_pressed = False
        self.update()
        super().mouseReleaseEvent(event)
    
    def paintEvent(self, event: QPaintEvent):
        """Custom paint event with texture rendering"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Determine texture variant based on state
        if not self.isEnabled():
            # Disabled - use dimmed version
            variant = "disabled"
        elif self._is_pressed:
            variant = "pressed"
        elif self._is_hovered:
            variant = "hover"
        else:
            variant = "normal"
        
        # Generate texture
        texture = self._generate_texture(rect.width(), rect.height(), variant)
        
        if not texture.isNull():
            # Get normal map for bump effect
            normal_map = self._get_normal_map(texture)
            
            # Light position based on button state
            if self._is_pressed:
                light_pos = (rect.width() // 2, rect.height() // 2 + 20)
            elif self._is_hovered:
                light_pos = (rect.width() // 2, rect.height() // 3)
            else:
                light_pos = (rect.width() // 2, rect.height() // 4)
            
            # Paint with bump mapping
            TexturePainter.paint_bumpmapped(
                painter, rect, texture, normal_map, light_pos
            )
        else:
            # Fallback to solid color
            painter.fillRect(rect, QColor(80, 80, 80))
        
        # Draw border
        self._paint_border(painter, rect)
        
        # Draw text
        self._paint_text(painter, rect)
        
        painter.end()
    
    def _paint_border(self, painter: QPainter, rect: QRect):
        """Paint 3D border effect"""
        colors = FalloutColors()
        
        if self._is_pressed:
            # Pressed border (inset)
            border_color = QColor(colors.DARK_METAL)
            highlight_color = QColor(colors.PANEL_SHADOW)
            shadow_color = QColor(colors.OLIVE_DRAB)
        elif self._is_hovered:
            # Hover border
            border_color = QColor(colors.FALLOUT_YELLOW)
            highlight_color = QColor(colors.BRIGHT_YELLOW)
            shadow_color = QColor(colors.GOLD_YELLOW)
        else:
            # Normal border
            border_color = QColor(colors.PANEL_BORDER)
            highlight_color = QColor(colors.PANEL_HIGHLIGHT)
            shadow_color = QColor(colors.PANEL_SHADOW)
        
        # Draw border with 3D effect
        painter.setPen(border_color)
        painter.drawRect(rect.adjusted(1, 1, -2, -2))
        
        # Highlight (top and left)
        pen = QPen(highlight_color)
        pen.setWidth(1)
        painter.setPen(pen)
        
        if not self._is_pressed:
            # Top edge
            painter.drawLine(rect.left() + 2, rect.top() + 2,
                           rect.right() - 2, rect.top() + 2)
            # Left edge
            painter.drawLine(rect.left() + 2, rect.top() + 2,
                           rect.left() + 2, rect.bottom() - 2)
        
        # Shadow (bottom and right)
        pen = QPen(shadow_color)
        pen.setWidth(1)
        painter.setPen(pen)
        
        if not self._is_pressed:
            # Bottom edge
            painter.drawLine(rect.left() + 2, rect.bottom() - 2,
                           rect.right() - 2, rect.bottom() - 2)
            # Right edge
            painter.drawLine(rect.right() - 2, rect.top() + 2,
                           rect.right() - 2, rect.bottom() - 2)
    
    def _paint_text(self, painter: QPainter, rect: QRect):
        """Paint button text"""
        colors = FalloutColors()
        
        if not self.isEnabled():
            text_color = QColor(colors.TEXT_DIM)
        elif self._is_pressed:
            text_color = QColor(255, 255, 255)
        elif self._is_hovered:
            text_color = QColor(colors.FALLOUT_YELLOW)
        else:
            text_color = QColor(colors.TEXT_NORMAL)
        
        # Draw text centered
        painter.setPen(text_color)
        font = QFont("Consolas", 10, QFont.Weight.Bold)
        painter.setFont(font)
        
        text_rect = rect.adjusted(0, 0, 0, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text())
    
    def setTextureType(self, texture_type: str):
        """Change the texture type dynamically"""
        self._texture_type = texture_type
        self._style = self._get_style_for_type(texture_type)
        self._texture_cache.clear()
        self._normal_map_cache.clear()
        self.update()


class TexturedFalloutPanel(QFrame):
    """
    Panel with realistic texture materials and bump mapping.
    
    Supports multiple texture types similar to TexturedFalloutButton.
    """
    
    def __init__(self, texture_type: str = "metal", 
                 parent=None):
        super().__init__(parent)
        self._texture_type = texture_type
        self._texture_cache = {}
        self._normal_map_cache = {}
        
        # Get texture style
        self._style = self._get_style_for_type(texture_type)
        
        self._setup_panel()
    
    def _get_style_for_type(self, tex_type: str) -> dict:
        """Get texture style configuration for panel type"""
        styles = {
            "metal": TextureStyle.PANEL_STANDARD,
            "rust": TextureStyle.PANEL_RUST,
            "wood": TextureStyle.PANEL_WOOD,
            "concrete": {**TextureStyle.PANEL_WORN, "type": "concrete"},
            "steel": {**TextureStyle.PANEL_STANDARD, "metal_type": "steel"},
            "copper": {**TextureStyle.PANEL_STANDARD, "metal_type": "copper"},
            "brass": {**TextureStyle.PANEL_STANDARD, "metal_type": "brass"},
            "worn_metal": {**TextureStyle.PANEL_STANDARD, "scratches": True},
        }
        return styles.get(tex_type, TextureStyle.PANEL_STANDARD)
    
    def _setup_panel(self):
        """Setup panel appearance"""
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(3, 3)
        shadow.setColor(QColor(0, 0, 0, 140))
        self.setGraphicsEffect(shadow)
    
    def _generate_texture(self, width: int, height: int) -> QPixmap:
        """Generate texture with caching"""
        cache_key = f"{self._texture_type}_{width}x{height}"
        
        if cache_key not in self._texture_cache:
            tex_type = self._style.get("type", "metal")
            
            if tex_type == "wood":
                self._texture_cache[cache_key] = TextureGenerator.generate_wood_texture(
                    width, height,
                    wood_type=self._style.get("wood_type", "pine"),
                    scale=self._style.get("scale", 10.0),
                    seed=self._style.get("seed", 42)
                )
            elif tex_type == "metal":
                self._texture_cache[cache_key] = TextureGenerator.generate_metal_texture(
                    width, height,
                    metal_type=self._style.get("metal_type", "steel"),
                    scratches=self._style.get("scratches", False),
                    seed=self._style.get("seed", 42)
                )
            elif tex_type == "rust":
                self._texture_cache[cache_key] = TextureGenerator.generate_rust_texture(
                    width, height,
                    intensity=self._style.get("intensity", 0.6),
                    seed=self._style.get("seed", 42)
                )
            elif tex_type == "concrete":
                self._texture_cache[cache_key] = TextureGenerator.generate_concrete_texture(
                    width, height,
                    dirty=self._style.get("dirty", True),
                    seed=self._style.get("seed", 42)
                )
            else:
                self._texture_cache[cache_key] = TextureGenerator.generate_metal_texture(
                    width, height, metal_type="steel", scratches=False
                )
        
        return self._texture_cache[cache_key]
    
    def _get_normal_map(self, texture: QPixmap) -> QPixmap:
        """Get or generate normal map"""
        cache_key = id(texture)
        
        if cache_key not in self._normal_map_cache:
            strength = self._style.get("bump_strength", 0.6)
            self._normal_map_cache[cache_key] = TextureGenerator.generate_normal_map(
                texture, strength
            )
        
        return self._normal_map_cache[cache_key]
    
    def paintEvent(self, event: QPaintEvent):
        """Custom paint event with texture rendering"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Generate texture
        texture = self._generate_texture(rect.width(), rect.height())
        
        if not texture.isNull():
            normal_map = self._get_normal_map(texture)
            
            # Light from top
            light_pos = (rect.width() // 2, rect.height() // 6)
            
            TexturePainter.paint_bumpmapped(
                painter, rect, texture, normal_map, light_pos
            )
        else:
            painter.fillRect(rect, QColor(45, 45, 45))
        
        # Draw border
        self._paint_border(painter, rect)
        
        painter.end()
    
    def _paint_border(self, painter: QPainter, rect: QRect):
        """Paint 3D border effect"""
        colors = FalloutColors()
        
        # Outer border
        border_color = QColor(colors.PANEL_BORDER)
        painter.setPen(border_color)
        painter.drawRect(rect.adjusted(1, 1, -2, -2))
        
        # Highlight (top and left)
        highlight_color = QColor(colors.PANEL_HIGHLIGHT)
        pen = QPen(highlight_color)
        pen.setWidth(1)
        painter.setPen(pen)
        
        painter.drawLine(rect.left() + 2, rect.top() + 2,
                        rect.right() - 2, rect.top() + 2)
        painter.drawLine(rect.left() + 2, rect.top() + 2,
                        rect.left() + 2, rect.bottom() - 2)
        
        # Shadow (bottom and right)
        shadow_color = QColor(colors.PANEL_SHADOW)
        pen = QPen(shadow_color)
        pen.setWidth(1)
        painter.setPen(pen)
        
        painter.drawLine(rect.left() + 2, rect.bottom() - 2,
                        rect.right() - 2, rect.bottom() - 2)
        painter.drawLine(rect.right() - 2, rect.top() + 2,
                        rect.right() - 2, rect.bottom() - 2)
    
    def setTextureType(self, texture_type: str):
        """Change the texture type dynamically"""
        self._texture_type = texture_type
        self._style = self._get_style_for_type(texture_type)
        self._texture_cache.clear()
        self._normal_map_cache.clear()
        self.update()


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
    # Fade animation classes
    'FadeAnimationMixin',
    'FadeLineEdit',
    'FadeTextEdit',
    'FadeLabel',
    'FadeButton',
    'FadeValidationMessage',
    # Texture-enabled classes
    'TexturedFalloutButton',
    'TexturedFalloutPanel',
]
