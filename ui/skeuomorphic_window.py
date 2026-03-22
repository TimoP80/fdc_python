"""
Skeuomorphic Window Chrome
Custom window decorations with realistic frame materials.

Features:
- Custom title bar with material textures (wood, metal, leather)
- Realistic window borders with depth effects
- Custom window controls (minimize, maximize, close)
- Drag-to-move title bar
- Resizable window edges
"""

import logging
from typing import Optional, Tuple, Dict

from PyQt6.QtCore import (
    Qt, QSize, QRect, QRectF, QPointF, QPoint, 
    QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import (
    QColor, QPainter, QPainterPath, QBrush, QPen, QLinearGradient,
    QRadialGradient, QPixmap, QFont, QCursor, QPaintEvent, QEnterEvent,
    QMouseEvent, QResizeEvent
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QApplication, QFrame
)

from ui.skeuomorphic_theme import (
    get_current_skeuomorphic_theme, SkeuomorphicTheme,
    get_theme_manager
)

logger = logging.getLogger(__name__)


# =============================================================================
# WINDOW BUTTONS
# =============================================================================

class WindowButton(QPushButton):
    """Custom window control button with skeuomorphic style"""
    
    def __init__(self, button_type: str = "close", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._button_type = button_type
        self._theme = get_current_skeuomorphic_theme()
        self._hover_color = QColor(0, 0, 0, 0)
        self._setup_button()
        
    def _setup_button(self):
        """Setup button properties"""
        self.setFixedSize(46, 32)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMouseTracking(True)
        
    def set_theme(self, theme: SkeuomorphicTheme):
        """Set button theme"""
        self._theme = theme
        self.update()
        
    def paintEvent(self, event: QPaintEvent):
        """Paint button with skeuomorphic style"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self._theme:
            super().paintEvent(event)
            return
            
        colors = self._theme.get_colors()
        rect = self.rect()
        
        # Determine background color
        if not self.isEnabled():
            bg_color = QColor(0, 0, 0, 0)
        elif self._button_type == "close" and self._state == 'hover':
            # Red for close button hover
            bg_color = QColor(232, 65, 55, 200)
        elif self._state == 'hover':
            bg_color = QColor(255, 255, 255, 30)
        else:
            bg_color = QColor(0, 0, 0, 0)
            
        # Draw background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRect(rect)
        
        # Draw icon based on button type
        self._paint_icon(painter, rect, colors)
        
    def _paint_icon(self, painter: QPainter, rect: QRect, colors: Dict[str, str]):
        """Paint window control icon"""
        icon_color = QColor(200, 200, 200) if self.isEnabled() else QColor(100, 100, 100)
        
        pen = QPen(icon_color, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        center = rect.center()
        
        if self._button_type == "close":
            # X icon
            margin = 12
            painter.drawLine(
                QPoint(center.x() - margin, center.y() - margin),
                QPoint(center.x() + margin, center.y() + margin)
            )
            painter.drawLine(
                QPoint(center.x() + margin, center.y() - margin),
                QPoint(center.x() - margin, center.y() + margin)
            )
        elif self._button_type == "maximize":
            # Square icon
            margin = 10
            painter.drawRect(QRect(
                center.x() - margin, center.y() - margin,
                margin * 2, margin * 2
            ))
        elif self._button_type == "minimize":
            # Minus icon
            margin = 10
            painter.drawLine(
                QPoint(center.x() - margin, center.y()),
                QPoint(center.x() + margin, center.y())
            )
        elif self._button_type == "restore":
            # Two overlapping squares
            margin = 8
            # Bottom square
            painter.drawRect(QRect(
                center.x() - margin + 2, center.y() - margin,
                margin * 2, margin * 2
            ))
            # Top square
            painter.drawRect(QRect(
                center.x() - margin, center.y() - margin + 2,
                margin * 2, margin * 2
            ))
            
    def enterEvent(self, event: QEnterEvent):
        """Handle mouse enter"""
        self._state = 'hover'
        self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handle mouse leave"""
        self._state = 'normal'
        self.update()
        super().leaveEvent(event)


# =============================================================================
# TITLE BAR
# =============================================================================

class SkeuomorphicTitleBar(QWidget):
    """
    Custom title bar with skeuomorphic material textures.
    Supports drag-to-move and contains window controls.
    """
    
    # Signals
    closeClicked = pyqtSignal()
    maximizeClicked = pyqtSignal()
    minimizeClicked = pyqtSignal()
    windowTitleChanged = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._theme = get_current_skeuomorphic_theme()
        self._title = "Window"
        self._is_maximized = False
        self._drag_start_pos = QPoint()
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup title bar UI"""
        self.setFixedHeight(40)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Title label
        self._title_label = QLabel(self._title)
        self._title_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 11pt;
                font-weight: bold;
                padding-left: 10px;
            }
        """)
        layout.addWidget(self._title_label, 1)
        
        # Window buttons
        self._min_button = WindowButton("minimize", self)
        self._min_button.clicked.connect(self.minimizeClicked)
        
        self._max_button = WindowButton("maximize", self)
        self._max_button.clicked.connect(self._on_maximize_clicked)
        
        self._close_button = WindowButton("close", self)
        self._close_button.clicked.connect(self.closeClicked)
        
        layout.addWidget(self._min_button)
        layout.addWidget(self._max_button)
        layout.addWidget(self._close_button)
        
    def set_theme(self, theme: SkeuomorphicTheme):
        """Set title bar theme"""
        self._theme = theme
        self._update_button_themes()
        self.update()
        
    def _update_button_themes(self):
        """Update themes for all buttons"""
        if self._theme:
            self._min_button.set_theme(self._theme)
            self._max_button.set_theme(self._theme)
            self._close_button.set_theme(self._theme)
            
    def set_title(self, title: str):
        """Set window title"""
        self._title = title
        self._title_label.setText(title)
        self.windowTitleChanged.emit(title)
        
    def get_title(self) -> str:
        """Get window title"""
        return self._title
        
    def paintEvent(self, event: QPaintEvent):
        """Paint title bar with skeuomorphic texture"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self._theme:
            return
            
        colors = self._theme.get_colors()
        rect = self.rect()
        
        # Create gradient for title bar background
        gradient = QLinearGradient(
            QPointF(0, 0),
            QPointF(0, rect.height())
        )
        
        # Determine gradient colors based on material type
        if self._theme.material_type == 'wood':
            gradient.setColorAt(0, QColor(colors['surface']).lighter(110))
            gradient.setColorAt(0.5, QColor(colors['surface']))
            gradient.setColorAt(1, QColor(colors['surface']).darker(110))
        elif self._theme.material_type == 'metal':
            gradient.setColorAt(0, QColor('#404550'))
            gradient.setColorAt(0.5, QColor(colors['surface']))
            gradient.setColorAt(1, QColor('#252830'))
        else:
            gradient.setColorAt(0, QColor(colors['surface']).lighter(110))
            gradient.setColorAt(1, QColor(colors['surface']).darker(110))
            
        # Draw background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRect(rect)
        
        # Draw border at bottom
        border_color = QColor(colors['border']).darker(150)
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(
            QPoint(0, rect.height() - 1),
            QPoint(rect.width(), rect.height() - 1)
        )
        
        # Draw inner highlight
        highlight_color = QColor(255, 255, 255, 20)
        painter.setPen(QPen(highlight_color, 1))
        painter.drawLine(
            QPoint(0, 1),
            QPoint(rect.width(), 1)
        )
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for drag"""
        if event.button() == Qt.MouseButton.LeftButton:
            parent = self.parentWidget()
            if parent:
                self._drag_start_pos = event.globalPosition().toPoint()
                
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for drag"""
        if event.buttons() & Qt.MouseButton.LeftButton:
            parent = self.parentWidget()
            if parent and not self._is_maximized:
                delta = event.globalPosition().toPoint() - self._drag_start_pos
                parent.move(parent.pos() + delta)
                self._drag_start_pos = event.globalPosition().toPoint()
                
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double click for maximize/restore"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_maximize_clicked()
            
    def _on_maximize_clicked(self):
        """Toggle maximize state"""
        self._is_maximized = not self._is_maximized
        self.maximizeClicked.emit()
        
        # Update maximize button icon
        if self._is_maximized:
            self._max_button.setFixedSize(46, 32)
        else:
            self._max_button.setFixedSize(46, 32)


# =============================================================================
# CUSTOM WINDOW FRAME
# =============================================================================

class SkeuomorphicWindow(QWidget):
    """
    Custom skeuomorphic window with material-textured frame.
    
    Features:
    - Custom title bar with material texture
    - Realistic window border with depth effects
    - Window controls (minimize, maximize, close)
    - Draggable title bar
    - Resizable edges
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._theme = get_current_skeuomorphic_theme()
        self._border_width = 8
        self._setup_window()
        
    def _setup_window(self):
        """Setup window properties"""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Title bar
        self._title_bar = SkeuomorphicTitleBar(self)
        self._title_bar.closeClicked.connect(self.close)
        self._title_bar.maximizeClicked.connect(self._toggle_maximize)
        self._title_bar.minimizeClicked.connect(self.showMinimized)
        main_layout.addWidget(self._title_bar)
        
        # Content area with border
        self._content_frame = QFrame(self)
        self._content_frame.setFrameShape(QFrame.Shape.NoFrame)
        main_layout.addWidget(self._content_frame, 1)
        
        # Set minimum size
        self.setMinimumSize(400, 300)
        
    def set_theme(self, theme: SkeuomorphicTheme):
        """Set window theme"""
        self._theme = theme
        if self._title_bar:
            self._title_bar.set_theme(theme)
        self.update()
        
    def set_title(self, title: str):
        """Set window title"""
        if self._title_bar:
            self._title_bar.set_title(title)
        super().setWindowTitle(title)
        
    def setWidget(self, widget: QWidget):
        """Set the main content widget"""
        if self._content_frame:
            layout = QVBoxLayout(self._content_frame)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(widget)
            
    def _toggle_maximize(self):
        """Toggle maximize state"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
            
    def paintEvent(self, event: QPaintEvent):
        """Paint window frame with skeuomorphic border"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self._theme:
            return
            
        colors = self._theme.get_colors()
        rect = self.rect()
        
        # Draw outer border
        border_color = QColor(colors['border'])
        painter.setPen(QPen(border_color, self._border_width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect.adjusted(1, 1, -1, -1))
        
        # Draw inner border (highlight)
        inner_border = QColor(colors['border']).lighter(130)
        painter.setPen(QPen(inner_border, 1))
        painter.drawRect(rect.adjusted(3, 3, -3, -3))
        
    def resizeEvent(self, event: QResizeEvent):
        """Handle resize event"""
        super().resizeEvent(event)
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for resize or move"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            edge = self._get_edge(pos)
            
            if edge:
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_edge = edge
            else:
                super().mousePressEvent(event)
                
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for resize"""
        pos = event.position().toPoint()
        
        # Update cursor based on edge
        edge = self._get_edge(pos)
        if edge:
            cursor = self._get_resize_cursor(edge)
            self.setCursor(cursor)
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            
        # Handle resize
        if hasattr(self, '_resize_edge') and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            self._perform_resize(self._resize_edge, delta)
            self._resize_start_pos = event.globalPosition().toPoint()
            
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release"""
        if hasattr(self, '_resize_edge'):
            del self._resize_edge
        super().mouseReleaseEvent(event)
        
    def _get_edge(self, pos: QPoint) -> Optional[str]:
        """Get which edge the mouse is over"""
        rect = self.rect()
        edge_size = self._border_width
        
        left = pos.x() < edge_size
        right = pos.x() > rect.width() - edge_size
        top = pos.y() < edge_size
        bottom = pos.y() > rect.height() - edge_size
        
        edges = []
        if left: edges.append('left')
        if right: edges.append('right')
        if top: edges.append('top')
        if bottom: edges.append('bottom')
        
        return ''.join(edges) if edges else None
        
    def _get_resize_cursor(self, edge: str) -> QCursor:
        """Get cursor for resize edge"""
        cursors = {
            'left': Qt.CursorShape.SizeHorCursor,
            'right': Qt.CursorShape.SizeHorCursor,
            'top': Qt.CursorShape.SizeVerCursor,
            'bottom': Qt.CursorShape.SizeVerCursor,
            'topleft': Qt.CursorShape.SizeFDiagCursor,
            'topright': Qt.CursorShape.SizeBDiagCursor,
            'bottomleft': Qt.CursorShape.SizeBDiagCursor,
            'bottomright': Qt.CursorShape.SizeFDiagCursor,
        }
        return QCursor(cursors.get(edge, Qt.CursorShape.ArrowCursor))
        
    def _perform_resize(self, edge: str, delta: QPoint):
        """Perform resize operation"""
        geom = self.geometry()
        new_geom = QRect(geom)
        
        if 'left' in edge:
            new_geom.setLeft(geom.left() + delta.x())
        if 'right' in edge:
            new_geom.setRight(geom.right() + delta.x())
        if 'top' in edge:
            new_geom.setTop(geom.top() + delta.y())
        if 'bottom' in edge:
            new_geom.setBottom(geom.bottom() + delta.y())
            
        if new_geom.width() >= self.minimumWidth() and new_geom.height() >= self.minimumHeight():
            self.setGeometry(new_geom)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_skeuomorphic_window(
    title: str = "Window", 
    theme_key: str = 'mahogany',
    parent: Optional[QWidget] = None
) -> SkeuomorphicWindow:
    """Create a skeuomorphic window with specified theme"""
    window = SkeuomorphicWindow(parent)
    window.set_title(title)
    
    theme_manager = get_theme_manager()
    if theme_manager.set_theme(theme_key):
        theme = theme_manager.get_current_theme()
        if theme:
            window.set_theme(theme)
            
    return window