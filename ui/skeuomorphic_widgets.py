"""
Skeuomorphic Widget Components
Comprehensive set of skeuomorphic UI widgets with realistic materials, 
tactile feedback, and depth effects.

Features:
- Realistic buttons with tactile depression effects
- Textured sliders with grip details
- Ornate dropdown menus with depth and shadow
- Custom window chrome with frame materials
- Authentic progress indicators
- Tactile toggle switches
- Detailed scrollbars
- Full hover, active, and disabled states
"""

import math
import logging
from typing import Optional, Dict, Any, Tuple

from PyQt6.QtCore import (
    Qt, QSize, QRect, QRectF, QPointF, QPropertyAnimation, 
    QEasingCurve, QTimer, pyqtSignal, QByteArray
)
from PyQt6.QtGui import (
    QColor, QPainter, QPainterPath, QBrush, QPen, QLinearGradient,
    QRadialGradient, QConicalGradient, QPixmap, QImage, QFont, 
    QCursor, QPaintEvent, QEnterEvent
)
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QSlider, QComboBox, QScrollBar, 
    QProgressBar, QCheckBox, QRadioButton, QAbstractSpinBox,
    QLabel, QFrame, QScrollArea, QMenu, QMenuBar, QToolBar,
    QApplication, QGraphicsDropShadowEffect
)

from ui.skeuomorphic_theme import (
    get_current_skeuomorphic_theme, SkeuomorphicTheme,
    get_theme_manager, SkeuomorphicThemeManager
)

logger = logging.getLogger(__name__)


# =============================================================================
# SKEUOMORPHIC WIDGET BASE
# =============================================================================

class SkeuomorphicWidget(QWidget):
    """Base class for skeuomorphic widgets with material properties"""
    
    # Signals for state changes
    state_changed = pyqtSignal(str)  # 'hover', 'pressed', 'disabled', 'normal'
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._theme = get_current_skeuomorphic_theme()
        self._state = 'normal'  # normal, hover, pressed, disabled
        self._animation_duration = 150
        self._setup_widget()
        
    def _setup_widget(self):
        """Setup basic widget properties"""
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def set_theme(self, theme: SkeuomorphicTheme):
        """Set the theme for this widget"""
        self._theme = theme
        self.update()
        
    def get_theme(self) -> Optional[SkeuomorphicTheme]:
        """Get the current theme"""
        return self._theme
    
    def _get_state_color(self, state_colors: Dict[str, str]) -> QColor:
        """Get color based on current state"""
        if self._state == 'disabled':
            return QColor(state_colors.get('disabled', '#808080'))
        elif self._state == 'pressed':
            return QColor(state_colors.get('pressed', '#606060'))
        elif self._state == 'hover':
            return QColor(state_colors.get('hover', '#a0a0a0'))
        return QColor(state_colors.get('normal', '#808080'))
    
    def _update_state(self, new_state: str):
        """Update the widget state"""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self.state_changed.emit(new_state)
            self.update()
            
    def enterEvent(self, event: QEnterEvent):
        """Handle mouse enter"""
        if self.isEnabled():
            self._update_state('hover')
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handle mouse leave"""
        self._update_state('normal')
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if self.isEnabled():
            self._update_state('pressed')
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if self.isEnabled():
            self._update_state('hover' if self.rect().contains(event.pos()) else 'normal')
        super().mouseReleaseEvent(event)
        
    def paintEvent(self, event: QPaintEvent):
        """Override paint event for custom rendering"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._paint_skeuomorphic(painter)
        
    def _paint_skeuomorphic(self, painter: QPainter):
        """Paint the skeuomorphic appearance - override in subclasses"""
        pass


# =============================================================================
# SKEUOMORPHIC BUTTON
# =============================================================================

class SkeuomorphicButton(SkeuomorphicWidget):
    """
    Realistic button with tactile depression effects.
    Features embossed surface, beveled edges, and realistic shadow.
    """
    
    clicked = pyqtSignal()
    
    def __init__(
        self, 
        text: str = "", 
        icon: Optional[QPixmap] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._text = text
        self._icon = icon
        self._button_type = 'default'  # default, primary, success, danger
        self._depth_offset = 0
        self._shadow_intensity = 0.5
        self._animation = None
        self._setup_button()
        
    def _setup_button(self):
        """Setup button properties"""
        self.setMinimumSize(100, 40)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
    def set_text(self, text: str):
        """Set button text"""
        self._text = text
        self.update()
        
    def get_text(self) -> str:
        """Get button text"""
        return self._text
    
    def set_icon(self, icon: QPixmap):
        """Set button icon"""
        self._icon = icon
        self.update()
        
    def set_button_type(self, button_type: str):
        """Set button type (default, primary, success, danger)"""
        self._button_type = button_type
        self.update()
        
    def _paint_skeuomorphic(self, painter: QPainter):
        """Paint skeuomorphic button with depth effects"""
        if not self._theme:
            return
            
        colors = self._theme.get_colors()
        rect = self.rect()
        
        # Get dimensions for depth effects
        border_width = 3
        corner_radius = 8
        
        # Determine depth offset based on state
        if self._state == 'pressed':
            depth_offset = 2
            shadow_intensity = 0.2
        elif self._state == 'hover':
            depth_offset = 0
            shadow_intensity = 0.6
        else:
            depth_offset = 1
            shadow_intensity = 0.5
            
        # Background color based on state
        if self._state == 'disabled':
            bg_color = QColor(colors['button_disabled'])
            border_color = QColor(colors['border_disabled'])
        elif self._state == 'pressed':
            bg_color = QColor(colors['button_pressed'])
            border_color = QColor(colors['button_border_pressed'])
        elif self._state == 'hover':
            bg_color = QColor(colors['button_hover'])
            border_color = QColor(colors['button_border_hover'])
        else:
            bg_color = QColor(colors['button_background'])
            border_color = QColor(colors['button_border'])
            
        # Draw outer shadow
        self._paint_shadow(painter, rect, corner_radius, shadow_intensity)
        
        # Draw button body with gradient for depth
        self._paint_button_body(painter, rect, corner_radius, border_width, bg_color, depth_offset)
        
        # Draw border/bevel
        self._paint_button_border(painter, rect, corner_radius, border_width, border_color, depth_offset)
        
        # Draw highlight on top edge
        self._paint_button_highlight(painter, rect, corner_radius, border_width)
        
        # Draw text and icon
        self._paint_button_content(painter, rect, colors)
        
    def _paint_shadow(self, painter: QPainter, rect: QRect, corner_radius: int, intensity: float):
        """Paint realistic drop shadow"""
        shadow_rect = rect.adjusted(4, 4, -2, -2)
        
        # Create shadow gradient
        gradient = QRadialGradient(
            shadow_rect.center(),
            max(shadow_rect.width(), shadow_rect.height()) / 2
        )
        
        shadow_color = QColor(0, 0, 0, int(80 * intensity))
        gradient.setColorAt(0, shadow_color)
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(shadow_rect, corner_radius, corner_radius)
        
    def _paint_button_body(
        self, 
        painter: QPainter, 
        rect: QRect, 
        corner_radius: int, 
        border_width: int,
        bg_color: QColor,
        depth_offset: int
    ):
        """Paint button body with gradient for 3D effect"""
        inner_rect = rect.adjusted(border_width, border_width, -border_width, -border_width)
        inner_rect.translate(0, depth_offset)
        
        # Create gradient for 3D depth effect
        gradient = QLinearGradient(
            QPointF(0, rect.top()),
            QPointF(0, rect.bottom())
        )
        
        # Adjust colors for depth
        top_color = bg_color.lighter(110)
        bottom_color = bg_color.darker(110)
        
        gradient.setColorAt(0, top_color)
        gradient.setColorAt(0.5, bg_color)
        gradient.setColorAt(1, bottom_color)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(inner_rect, corner_radius - 1, corner_radius - 1)
        
    def _paint_button_border(
        self, 
        painter: QPainter, 
        rect: QRect, 
        corner_radius: int, 
        border_width: int,
        border_color: QColor,
        depth_offset: int
    ):
        """Paint button border with bevel effect"""
        # Outer border
        painter.setPen(QPen(border_color, border_width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), corner_radius, corner_radius)
        
        # Inner highlight (bevel effect)
        inner_rect = rect.adjusted(border_width + 1, border_width + 1, -border_width - 1, -border_width - 1)
        highlight_color = border_color.lighter(130)
        painter.setPen(QPen(highlight_color, 1))
        painter.drawRoundedRect(inner_rect, corner_radius - 2, corner_radius - 2)
        
    def _paint_button_highlight(self, painter: QPainter, rect: QRect, corner_radius: int, border_width: int):
        """Paint subtle highlight on top edge"""
        highlight_rect = QRectF(
            rect.left() + border_width + 2,
            rect.top() + border_width + 1,
            rect.width() - (border_width + 2) * 2,
            6
        )
        
        gradient = QLinearGradient(
            QPointF(0, highlight_rect.top()),
            QPointF(0, highlight_rect.bottom())
        )
        
        highlight_color = QColor(255, 255, 255, 60)
        gradient.setColorAt(0, highlight_color)
        gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        
        path = QPainterPath()
        path.addRoundedRect(highlight_rect, corner_radius - 2, corner_radius - 2)
        painter.drawPath(path)
        
    def _paint_button_content(self, painter: QPainter, rect: QRect, colors: Dict[str, str]):
        """Paint button text and icon"""
        # Text color based on state
        if self._state == 'disabled':
            text_color = QColor(colors['text_disabled'])
        else:
            text_color = QColor(colors['button_text'])
            
        # Draw text
        if self._text:
            font = QFont("Segoe UI", 10, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(text_color)
            
            text_rect = rect.adjusted(8, 0, -8, 0)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, self._text)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release and emit clicked signal"""
        if self.isEnabled() and self._state == 'pressed':
            self.clicked.emit()
            
        super().mouseReleaseEvent(event)


# =============================================================================
# SKEUOMORPHIC SLIDER
# =============================================================================

class SkeuomorphicSlider(SkeuomorphicWidget):
    """
    Textured slider with realistic grip and depth effects.
    Features brushed metal texture on thumb and groove with realistic shadows.
    """
    
    valueChanged = pyqtSignal(int)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._orientation = Qt.Orientation.Horizontal
        self._minimum = 0
        self._maximum = 100
        self._value = 50
        self._groove_height = 12
        self._thumb_width = 24
        self._thumb_height = 24
        self._tick_position = 0
        self._setup_slider()
        
    def _setup_slider(self):
        """Setup slider properties"""
        self.setMinimumHeight(30)
        if self._orientation == Qt.Orientation.Horizontal:
            self.setMinimumWidth(150)
            
    def set_orientation(self, orientation: Qt.Orientation):
        """Set slider orientation"""
        self._orientation = orientation
        self.update()
        
    def set_range(self, min_val: int, max_val: int):
        """Set slider range"""
        self._minimum = min_val
        self._maximum = max_val
        self._value = max(min(self._value, max_val), min_val)
        self.update()
        
    def set_value(self, value: int):
        """Set slider value"""
        self._value = max(self._minimum, min(self._maximum, value))
        self.valueChanged.emit(self._value)
        self.update()
        
    def value(self) -> int:
        """Get slider value"""
        return self._value
    
    def _paint_skeuomorphic(self, painter: QPainter):
        """Paint skeuomorphic slider with texture"""
        if not self._theme:
            return
            
        colors = self._theme.get_colors()
        
        if self._orientation == Qt.Orientation.Horizontal:
            self._paint_horizontal_slider(painter, colors)
        else:
            self._paint_vertical_slider(painter, colors)
            
    def _paint_horizontal_slider(self, painter: QPainter, colors: Dict[str, str]):
        """Paint horizontal slider"""
        rect = self.rect()
        groove_height = self._groove_height
        groove_y = (rect.height() - groove_height) // 2
        
        # Calculate thumb position
        thumb_x = self._calculate_thumb_position(rect.width() - self._thumb_width)
        thumb_rect = QRect(thumb_x, (rect.height() - self._thumb_height) // 2, 
                          self._thumb_width, self._thumb_height)
        
        # Draw groove track
        self._paint_groove(painter, QRect(0, groove_y, rect.width(), groove_height), colors, 'horizontal')
        
        # Draw filled portion
        self._paint_filled_groove(painter, QRect(0, groove_y, thumb_x + self._thumb_width // 2, groove_height), colors)
        
        # Draw thumb
        self._paint_thumb(painter, thumb_rect, colors)
        
    def _paint_vertical_slider(self, painter: QPainter, colors: Dict[str, str]):
        """Paint vertical slider"""
        rect = self.rect()
        groove_width = self._groove_height
        groove_x = (rect.width() - groove_width) // 2
        
        # Calculate thumb position
        thumb_y = self._calculate_thumb_position(rect.height() - self._thumb_height)
        thumb_rect = QRect((rect.width() - self._thumb_width) // 2, thumb_y,
                          self._thumb_width, self._thumb_height)
        
        # Draw groove track
        self._paint_groove(painter, QRect(groove_x, 0, groove_width, rect.height()), colors, 'vertical')
        
        # Draw filled portion
        self._paint_filled_groove(painter, QRect(groove_x, thumb_y + self._thumb_height // 2, groove_width, 
                                                rect.height() - thumb_y - self._thumb_height // 2), colors)
        
        # Draw thumb
        self._paint_thumb(painter, thumb_rect, colors)
        
    def _calculate_thumb_position(self, available_space: int) -> int:
        """Calculate thumb position based on value"""
        if self._maximum == self._minimum:
            return 0
        ratio = (self._value - self._minimum) / (self._maximum - self._minimum)
        return int(ratio * available_space)
        
    def _paint_groove(self, painter: QPainter, rect: QRect, colors: Dict[str, str], orientation: str):
        """Paint slider groove with 3D depth effect"""
        # Groove background (inset)
        groove_color = QColor(colors['slider_track'])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(groove_color))
        
        if orientation == 'horizontal':
            painter.drawRoundedRect(rect, 6, 6)
        else:
            painter.drawRoundedRect(rect, 6, 6)
            
        # Groove border
        border_color = QColor(colors['slider_track_border'])
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 6, 6)
        
        # Inner shadow (inset effect)
        inner_rect = rect.adjusted(2, 2, -2, -2)
        inner_shadow = QColor(0, 0, 0, 30)
        painter.setPen(QPen(inner_shadow, 2))
        painter.drawRoundedRect(inner_rect, 4, 4)
        
    def _paint_filled_groove(self, painter: QPainter, rect: QRect, colors: Dict[str, str]):
        """Paint the filled portion of the groove"""
        fill_color = QColor(colors['slider_filled'])
        
        # Create gradient for depth
        if rect.width() > 0:
            gradient = QLinearGradient(
                QPointF(rect.left(), rect.top()),
                QPointF(rect.left(), rect.bottom())
            )
            gradient.setColorAt(0, fill_color.lighter(120))
            gradient.setColorAt(0.5, fill_color)
            gradient.setColorAt(1, fill_color.darker(110))
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gradient))
            
            if rect.width() < rect.height():
                painter.drawRoundedRect(rect, 4, 4)
            else:
                painter.drawRoundedRect(rect, 4, 4)
                
    def _paint_thumb(self, painter: QPainter, rect: QRect, colors: Dict[str, str]):
        """Paint slider thumb with 3D depth and texture"""
        corner_radius = rect.width() // 2
        
        # Determine thumb colors based on state
        if self._state == 'disabled':
            thumb_color = QColor(colors['button_disabled'])
            border_color = QColor(colors['border_disabled'])
        elif self._state == 'pressed':
            thumb_color = QColor(colors['accent_dark'])
            border_color = QColor(colors['accent'])
        elif self._state == 'hover':
            thumb_color = QColor(colors['slider_thumb_hover'])
            border_color = QColor(colors['accent'])
        else:
            thumb_color = QColor(colors['slider_thumb'])
            border_color = QColor(colors['slider_thumb_border'])
            
        # Draw drop shadow
        shadow_rect = rect.adjusted(3, 3, -1, -1)
        shadow_color = QColor(0, 0, 0, 60)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shadow_color))
        painter.drawEllipse(shadow_rect)
        
        # Draw thumb body with gradient for 3D effect
        gradient = QRadialGradient(
            QPointF(rect.center().x(), rect.center().y() - rect.height() * 0.2),
            rect.width() / 2
        )
        gradient.setColorAt(0, thumb_color.lighter(130))
        gradient.setColorAt(0.7, thumb_color)
        gradient.setColorAt(1, thumb_color.darker(120))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(rect)
        
        # Draw border
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(rect.adjusted(1, 1, -1, -1))
        
        # Draw inner highlight (brushed metal effect)
        highlight_rect = rect.adjusted(3, 3, -3, -3)
        highlight_gradient = QLinearGradient(
            QPointF(highlight_rect.left(), highlight_rect.top()),
            QPointF(highlight_rect.right(), highlight_rect.top())
        )
        highlight_color = QColor(255, 255, 255, 40)
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, 0))
        highlight_gradient.setColorAt(0.3, highlight_color)
        highlight_gradient.setColorAt(0.7, highlight_color)
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(highlight_gradient))
        painter.drawEllipse(highlight_rect)
        
        # Draw center grip line
        center_color = QColor(0, 0, 0, 50)
        painter.setPen(QPen(center_color, 2))
        painter.drawLine(
            QPointF(rect.center().x() - 4, rect.center().y()),
            QPointF(rect.center().x() + 4, rect.center().y())
        )
        
    def mousePressEvent(self, event):
        """Handle mouse press on slider"""
        if self.isEnabled():
            self._update_value_from_position(event.pos())
            self._update_state('pressed')
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """Handle mouse move on slider"""
        if self.isEnabled() and self._state == 'pressed':
            self._update_value_from_position(event.pos())
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if self.isEnabled():
            self._update_state('hover' if self.rect().contains(event.pos()) else 'normal')
        super().mouseReleaseEvent(event)
        
    def _update_value_from_position(self, pos: QPointF):
        """Update value based on mouse position"""
        if self._orientation == Qt.Orientation.Horizontal:
            available = self.width() - self._thumb_width
            ratio = max(0, min(1, (pos.x() - self._thumb_width / 2) / available))
        else:
            available = self.height() - self._thumb_height
            ratio = max(0, min(1, (pos.y() - self._thumb_height / 2) / available))
            
        new_value = int(self._minimum + ratio * (self._maximum - self._minimum))
        
        if new_value != self._value:
            self._value = new_value
            self.valueChanged.emit(self._value)
            self.update()


# =============================================================================
# SKEUOMORPHIC PROGRESS BAR
# =============================================================================

class SkeuomorphicProgressBar(SkeuomorphicWidget):
    """
    Authentic progress indicator with realistic metallic appearance.
    Features embossed frame and smooth gradient fill.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._minimum = 0
        self._maximum = 100
        self._value = 0
        self._show_text = True
        self._indeterminate = False
        self._indeterminate_pos = 0
        
    def set_range(self, minimum: int, maximum: int):
        """Set progress range"""
        self._minimum = minimum
        self._maximum = maximum
        self.update()
        
    def set_value(self, value: int):
        """Set progress value"""
        self._value = max(self._minimum, min(self._maximum, value))
        self.update()
        
    def value(self) -> int:
        """Get progress value"""
        return self._value
        
    def set_indeterminate(self, indeterminate: bool):
        """Set indeterminate mode"""
        self._indeterminate = indeterminate
        if indeterminate:
            self._start_indeterminate_animation()
        else:
            self._stop_indeterminate_animation()
        self.update()
        
    def _start_indeterminate_animation(self):
        """Start indeterminate animation"""
        self._indeterminate_pos = 0
        
    def _stop_indeterminate_animation(self):
        """Stop indeterminate animation"""
        self._indeterminate_pos = 0
        
    def _paint_skeuomorphic(self, painter: QPainter):
        """Paint skeuomorphic progress bar"""
        if not self._theme:
            return
            
        colors = self._theme.get_colors()
        rect = self.rect()
        
        # Draw outer frame with embossed border
        self._paint_progress_frame(painter, rect, colors)
        
        # Draw progress fill
        self._paint_progress_fill(painter, rect, colors)
        
        # Draw text overlay
        if self._show_text and not self._indeterminate:
            self._paint_progress_text(painter, rect, colors)
            
    def _paint_progress_frame(self, painter: QPainter, rect: QRect, colors: Dict[str, str]):
        """Paint progress bar frame with embossed effect"""
        # Background
        bg_color = QColor(colors['progress_background'])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, 6, 6)
        
        # Outer border
        border_color = QColor(colors['progress_border'])
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 5, 5)
        
        # Inner highlight (embossed effect)
        inner_rect = rect.adjusted(3, 3, -3, -3)
        highlight_color = QColor(255, 255, 255, 20)
        painter.setPen(QPen(highlight_color, 1))
        painter.drawRoundedRect(inner_rect, 4, 4)
        
    def _paint_progress_fill(self, painter: QPainter, rect: QRect, colors: Dict[str, str]):
        """Paint progress fill with gradient"""
        border = 3
        fill_rect = rect.adjusted(border, border, -border, -border)
        
        if self._indeterminate:
            # Indeterminate animation
            width = fill_rect.width() * 0.4
            x = (fill_rect.width() * self._indeterminate_pos / 100) % (fill_rect.width() + width) - width
            fill_rect = QRect(int(fill_rect.x() + x), fill_rect.y(), int(width), fill_rect.height())
        else:
            # Calculate filled portion
            if self._maximum != self._minimum:
                ratio = (self._value - self._minimum) / (self._maximum - self._minimum)
                fill_width = int(fill_rect.width() * ratio)
                fill_rect = QRect(fill_rect.x(), fill_rect.y(), fill_width, fill_rect.height())
            else:
                return
                
        if fill_rect.width() <= 0:
            return
            
        # Create gradient for metallic look
        gradient = QLinearGradient(
            QPointF(fill_rect.left(), fill_rect.top()),
            QPointF(fill_rect.left(), fill_rect.bottom())
        )
        
        fill_color = QColor(colors['progress_fill'])
        gradient.setColorAt(0, fill_color.lighter(120))
        gradient.setColorAt(0.3, fill_color)
        gradient.setColorAt(0.5, fill_color.lighter(110))
        gradient.setColorAt(1, fill_color.darker(110))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(fill_rect, 3, 3)
        
        # Add shine highlight
        shine_rect = QRectF(fill_rect.x(), fill_rect.y() + 2, fill_rect.width(), fill_rect.height() * 0.3)
        shine_gradient = QLinearGradient(
            QPointF(0, shine_rect.top()),
            QPointF(0, shine_rect.bottom())
        )
        shine_gradient.setColorAt(0, QColor(255, 255, 255, 60))
        shine_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shine_gradient))
        painter.drawRoundedRect(shine_rect, 2, 2)
        
    def _paint_progress_text(self, painter: QPainter, rect: QRect, colors: Dict[str, str]):
        """Paint percentage text"""
        text_color = QColor(colors['text_primary'])
        
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(text_color)
        
        percentage = int((self._value - self._minimum) / (self._maximum - self._minimum) * 100) if self._maximum != self._minimum else 0
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{percentage}%")


# =============================================================================
# SKEUOMORPHIC TOGGLE SWITCH
# =============================================================================

class SkeuomorphicToggle(SkeuomorphicWidget):
    """
    Tactile toggle switch with realistic knob movement.
    Features smooth animation and 3D depth effect.
    """
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._checked = False
        self._track_width = 60
        self._track_height = 30
        self._knob_size = 24
        self._animation = None
        
    def setChecked(self, checked: bool):
        """Set toggle state"""
        if self._checked != checked:
            self._checked = checked
            self.toggled.emit(checked)
            self.update()
            
    def isChecked(self) -> bool:
        """Get toggle state"""
        return self._checked
        
    def toggle(self):
        """Toggle state"""
        self.setChecked(not self._checked)
        
    def _paint_skeuomorphic(self, painter: QPainter):
        """Paint skeuomorphic toggle switch"""
        if not self._theme:
            return
            
        colors = self._theme.get_colors()
        rect = self.rect()
        
        # Draw track
        self._paint_track(painter, rect, colors)
        
        # Draw knob
        self._paint_knob(painter, rect, colors)
        
    def _paint_track(self, painter: QPainter, rect: QRect, colors: Dict[str, str]):
        """Paint toggle track with 3D effect"""
        # Determine track colors based on state
        if self._checked:
            track_on = QColor(colors['accent'])
            track_border = QColor(colors['accent_dark'])
        else:
            track_on = QColor(colors['slider_track'])
            track_border = QColor(colors['slider_track_border'])
            
        # Draw track shadow
        shadow_rect = rect.adjusted(2, 2, -2, -2)
        shadow_color = QColor(0, 0, 0, 40)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shadow_color))
        painter.drawRoundedRect(shadow_rect, rect.height() // 2, rect.height() // 2)
        
        # Draw track background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(track_on))
        painter.drawRoundedRect(rect, rect.height() // 2, rect.height() // 2)
        
        # Draw track border
        painter.setPen(QPen(track_border, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), rect.height() // 2 - 1, rect.height() // 2 - 1)
        
    def _paint_knob(self, painter: QPainter, rect: QRect, colors: Dict[str, str]):
        """Paint toggle knob with 3D effect"""
        # Calculate knob position
        padding = 3
        knob_x = padding if not self._checked else rect.width() - self._knob_size - padding
        knob_rect = QRect(knob_x, (rect.height() - self._knob_size) // 2, 
                         self._knob_size, self._knob_size)
        
        # Determine knob colors based on state
        if self._state == 'pressed':
            knob_color = QColor(colors['accent_dark'])
        elif self._state == 'hover':
            knob_color = QColor(colors['accent_light'])
        else:
            knob_color = QColor(colors['button_background'])
            
        # Draw knob shadow
        shadow_rect = knob_rect.adjusted(2, 2, -1, -1)
        shadow_color = QColor(0, 0, 0, 50)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shadow_color))
        painter.drawEllipse(shadow_rect)
        
        # Draw knob body with gradient
        gradient = QRadialGradient(
            QPointF(knob_rect.center().x(), knob_rect.center().y() - knob_rect.height() * 0.2),
            knob_rect.width() / 2
        )
        gradient.setColorAt(0, knob_color.lighter(130))
        gradient.setColorAt(0.7, knob_color)
        gradient.setColorAt(1, knob_color.darker(120))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(knob_rect)
        
        # Draw knob border
        border_color = QColor(colors['button_border'])
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(knob_rect.adjusted(1, 1, -1, -1))
        
        # Draw knob highlight
        highlight_rect = knob_rect.adjusted(3, 3, -3, -3)
        highlight_gradient = QLinearGradient(
            QPointF(highlight_rect.left(), highlight_rect.top()),
            QPointF(highlight_rect.right(), highlight_rect.top())
        )
        highlight_color = QColor(255, 255, 255, 50)
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, 0))
        highlight_gradient.setColorAt(0.3, highlight_color)
        highlight_gradient.setColorAt(0.7, highlight_color)
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(highlight_gradient))
        painter.drawEllipse(highlight_rect)
        
    def mouseReleaseEvent(self, event):
        """Toggle on click"""
        if self.isEnabled() and self.rect().contains(event.pos()):
            self.toggle()
        super().mouseReleaseEvent(event)
        
    def minimumSizeHint(self) -> QSize:
        """Return minimum size"""
        return QSize(self._track_width, self._track_height)


# =============================================================================
# SKEUOMORPHIC SCROLLBAR
# =============================================================================

class SkeuomorphicScrollBar(SkeuomorphicWidget):
    """
    Detailed scrollbar with textured thumb and realistic shadows.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._orientation = Qt.Orientation.Vertical
        self._minimum = 0
        self._maximum = 100
        self._value = 0
        self._page_step = 10
        self._single_step = 1
        
    def set_orientation(self, orientation: Qt.Orientation):
        """Set scrollbar orientation"""
        self._orientation = orientation
        self.update()
        
    def set_range(self, minimum: int, maximum: int):
        """Set scrollbar range"""
        self._minimum = minimum
        self._maximum = maximum
        self._value = max(minimum, min(maximum, self._value))
        self.update()
        
    def set_value(self, value: int):
        """Set scrollbar value"""
        self._value = max(self._minimum, min(self._maximum, value))
        self.update()
        
    def value(self) -> int:
        """Get scrollbar value"""
        return self._value
        
    def _paint_skeuomorphic(self, painter: QPainter):
        """Paint skeuomorphic scrollbar"""
        if not self._theme:
            return
            
        colors = self._theme.get_colors()
        rect = self.rect()
        
        # Draw scrollbar track
        self._paint_scrollbar_track(painter, rect, colors)
        
        # Draw scrollbar thumb
        self._paint_scrollbar_thumb(painter, rect, colors)
        
    def _paint_scrollbar_track(self, painter: QPainter, rect: QRect, colors: Dict[str, str]):
        """Paint scrollbar track"""
        track_color = QColor(colors['scrollbar_background'])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(track_color))
        painter.drawRoundedRect(rect, 7, 7)
        
    def _paint_scrollbar_thumb(self, painter: QPainter, rect: QRect, colors: Dict[str, str]):
        """Paint scrollbar thumb with texture"""
        # Calculate thumb rect
        if self._maximum == self._minimum:
            thumb_rect = rect
        else:
            # Calculate thumb size and position based on viewport
            thumb_ratio = min(1.0, self._page_step / (self._maximum - self._minimum + 1))
            thumb_length = max(30, int(rect.height() * thumb_ratio))
            value_ratio = (self._value - self._minimum) / (self._maximum - self._minimum)
            thumb_y = int(value_ratio * (rect.height() - thumb_length))
            thumb_rect = QRect(0, thumb_y, rect.width(), thumb_length)
            
        # Determine thumb colors based on state
        if self._state == 'disabled':
            thumb_color = QColor(colors['button_disabled'])
        elif self._state == 'pressed':
            thumb_color = QColor(colors['accent_dark'])
        elif self._state == 'hover':
            thumb_color = QColor(colors['scrollbar_thumb_hover'])
        else:
            thumb_color = QColor(colors['scrollbar_thumb'])
            
        # Draw thumb shadow
        shadow_rect = thumb_rect.adjusted(1, 2, -1, -1)
        shadow_color = QColor(0, 0, 0, 40)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shadow_color))
        painter.drawRoundedRect(shadow_rect, 5, 5)
        
        # Draw thumb body
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(thumb_color))
        painter.drawRoundedRect(thumb_rect, 5, 5)
        
        # Draw thumb border
        border_color = QColor(colors['border'])
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(thumb_rect.adjusted(1, 1, -1, -1), 4, 4)
        
        # Draw thumb grip lines
        grip_color = QColor(0, 0, 0, 40)
        painter.setPen(QPen(grip_color, 2))
        
        center_x = thumb_rect.center().x()
        for i in range(-1, 2):
            y = thumb_rect.center().y() + i * 6
            painter.drawLine(
                QPointF(center_x - 6, y),
                QPointF(center_x + 6, y)
            )


# =============================================================================
# SKEUOMORPHIC PANEL
# =============================================================================

class SkeuomorphicPanel(QFrame):
    """
    Skeuomorphic panel with material depth and border effects.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._theme = get_current_skeuomorphic_theme()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
    def set_theme(self, theme: SkeuomorphicTheme):
        """Set panel theme"""
        self._theme = theme
        self.update()
        
    def paintEvent(self, event: QPaintEvent):
        """Paint skeuomorphic panel"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self._theme:
            super().paintEvent(event)
            return
            
        colors = self._theme.get_colors()
        rect = self.rect()
        
        # Draw panel background
        bg_color = QColor(colors['panel_background'])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, 6, 6)
        
        # Draw border
        border_color = QColor(colors['border'])
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 5, 5)
        
        # Draw inner highlight
        inner_rect = rect.adjusted(3, 3, -3, -3)
        highlight_color = QColor(255, 255, 255, 15)
        painter.setPen(QPen(highlight_color, 1))
        painter.drawRoundedRect(inner_rect, 4, 4)


# =============================================================================
# THEME SELECTOR WIDGET
# =============================================================================

class ThemeSelectorWidget(QWidget):
    """
    Widget for selecting skeuomorphic themes with visual preview.
    """
    
    themeSelected = pyqtSignal(str)  # Theme key
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._theme_manager = get_theme_manager()
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup theme selector UI"""
        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel("Select Theme")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Add theme buttons
        themes = self._theme_manager.get_available_themes()
        
        for key, name in themes.items():
            button = SkeuomorphicButton(name)
            button.clicked.connect(lambda checked, k=key: self._on_theme_selected(k))
            layout.addWidget(button)
            
    def _on_theme_selected(self, theme_key: str):
        """Handle theme selection"""
        self._theme_manager.set_theme(theme_key)
        self.themeSelected.emit(theme_key)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def apply_skeuomorphic_theme(app: QApplication, theme_key: str = 'mahogany'):
    """Apply skeuomorphic theme to application"""
    theme_manager = get_theme_manager()
    if theme_manager.set_theme(theme_key):
        theme_manager.apply_to_app(app)
        return True
    return False


def get_skeuomorphic_stylesheet(theme_key: str = 'mahogany') -> str:
    """Get stylesheet for a specific theme"""
    theme_manager = get_theme_manager()
    if theme_manager.set_theme(theme_key):
        return theme_manager.get_stylesheet()
    return ""