"""
Diagram widget for visual dialogue editing
Significantly improved for better readability and visual organization
"""

import math
import logging
from typing import Dict, List, Optional, Tuple

from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsLineItem, QGraphicsPolygonItem, QMenu,
    QGraphicsSceneMouseEvent, QGraphicsSceneContextMenuEvent, QWidget
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import (
    QPen, QBrush, QColor, QFont, QPainter, QPolygonF, QLinearGradient,
    QRadialGradient, QPainterPath, QCursor, QPixmap, QTransform
)

from models.dialogue import Dialogue, DialogueNode, PlayerOption, Reaction, FloatMessage, FloatNode, FloatMessageType, SkillCheck

logger = logging.getLogger(__name__)


# Color scheme constants for consistent styling
class DiagramColors:
    """Color scheme for diagram elements"""
    # Node colors by type
    NODE_START = QColor(34, 139, 34)      # Forest green - starting nodes (WTG)
    NODE_REGULAR = QColor(70, 130, 180)     # Steel blue - regular nodes
    NODE_HIDDEN = QColor(128, 128, 128)     # Gray - hidden nodes
    NODE_SKILLCHECK = QColor(255, 140, 0)   # Dark orange - nodes with skill checks
    NODE_SELECTED = QColor(255, 215, 0)     # Gold - selected node
    
    # Gradient colors (lighter variants for gradients)
    NODE_START_LIGHT = QColor(144, 238, 144)
    NODE_REGULAR_LIGHT = QColor(176, 224, 230)
    NODE_HIDDEN_LIGHT = QColor(211, 211, 211)
    NODE_SKILLCHECK_LIGHT = QColor(255, 200, 100)
    
    # Arrow colors by reaction type
    ARROW_NEUTRAL = QColor(100, 100, 100)   # Gray
    ARROW_GOOD = QColor(34, 139, 34)        # Green
    ARROW_BAD = QColor(178, 34, 34)         # Firebrick red
    
    # Background
    GRID_COLOR = QColor(220, 220, 220)
    BACKGROUND = QColor(250, 250, 252)
    
    # Text colors
    TEXT_PRIMARY = QColor(50, 50, 50)
    TEXT_SECONDARY = QColor(100, 100, 100)
    TEXT_ON_DARK = QColor(255, 255, 255)
    
    # Float message colors
    FLOAT_NPC = QColor(0, 255, 0)         # Terminal green - NPC dialogue
    FLOAT_PLAYER = QColor(0, 191, 255)     # Deep sky blue - player response
    FLOAT_SYSTEM = QColor(255, 165, 0)    # Orange - system notification
    FLOAT_CONDITION = QColor(255, 105, 180)  # Hot pink - condition check
    FLOAT_SKILL = QColor(255, 215, 0)     # Gold - skill check


class DiagramWidget(QGraphicsView):
    """Main diagram widget for visual dialogue editing with improved layout"""

    # Zoom limits
    ZOOM_MIN = 0.1  # Minimum zoom factor
    ZOOM_MAX = 5.0  # Maximum zoom factor
    ZOOM_STEP = 1.15  # Zoom step for mouse wheel

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Configure view with high-quality rendering
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        # Set resize anchor for smooth zooming

        # Scene settings - larger area
        self.scene.setSceneRect(-8000, -6000, 16000, 12000)
        self.scene.setBackgroundBrush(QBrush(DiagramColors.BACKGROUND))

        # Node and arrow management
        self.node_items: Dict[str, NodeItem] = {}
        self.arrow_items: List[CurvedArrowItem] = []
        self.grid_item: Optional[GridItem] = None

        # Interaction state
        self.selected_node: Optional[NodeItem] = None
        self.drag_start_pos: Optional[QPointF] = None

        # Layout settings (will be calculated dynamically)
        self.base_spacing_x = 400
        self.base_spacing_y = 280
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Add subtle grid background
        self.add_background_grid()

    def add_background_grid(self):
        """Add a subtle background grid for alignment"""
        self.grid_item = GridItem()
        self.scene.addItem(self.grid_item)
        self.grid_item.setZValue(-100)  # Send to back

    def set_dialogue(self, dialogue: Dialogue):
        """Update diagram with dialogue data"""
        self.clear_diagram()
        if not dialogue:
            return

        logger.info(f"Rendering dialogue with {dialogue.nodecount} nodes")

        # Create node items with improved styling
        for node in dialogue.nodes:
            node_item = NodeItem(node)
            self.node_items[node.nodename] = node_item
            self.scene.addItem(node_item)

        # Create curved arrow items for connections
        for node in dialogue.nodes:
            for option in node.options:
                if option.nodelink and option.nodelink in self.node_items:
                    source_item = self.node_items[node.nodename]
                    target_item = self.node_items[option.nodelink]
                    arrow = CurvedArrowItem(source_item, target_item, option)
                    self.arrow_items.append(arrow)
                    self.scene.addItem(arrow)

        # Calculate optimal spacing and layout
        self.calculate_adaptive_spacing()
        
        # Auto-layout nodes with improved algorithm
        self.auto_layout_nodes()
        
        # Center view on the diagram
        QTimer.singleShot(50, self.fit_to_view_with_margin)

    def clear_diagram(self):
        """Clear all diagram items"""
        self.scene.clear()
        self.node_items.clear()
        self.arrow_items.clear()
        # Re-add grid
        self.add_background_grid()

    def calculate_adaptive_spacing(self):
        """Calculate spacing based on node content and density"""
        if not self.node_items:
            return
            
        # Calculate average text length
        total_text_len = 0
        max_options = 0
        has_skillchecks = False
        
        for node_item in self.node_items.values():
            total_text_len += len(node_item.node.npctext)
            max_options = max(max_options, len(node_item.node.options))
            if node_item.node.skillchecks:
                has_skillchecks = True
        
        avg_text_len = total_text_len / len(self.node_items) if self.node_items else 0
        
        # Adjust spacing based on content
        # More text = wider nodes = need more spacing
        text_factor = min(2.0, max(1.0, avg_text_len / 100))
        options_factor = 1.0 + (max_options - 1) * 0.1
        
        self.base_spacing_x = int(380 * text_factor * options_factor)
        self.base_spacing_y = int(260 + max_options * 20)
        
        # Minimum spacing constraints
        self.base_spacing_x = max(350, self.base_spacing_x)
        self.base_spacing_y = max(240, self.base_spacing_y)
        
        logger.debug(f"Adaptive spacing: {self.base_spacing_x}x{self.base_spacing_y}")

    def auto_layout_nodes(self):
        """Automatically position nodes in a hierarchical layout with improved algorithm"""
        if not self.node_items:
            return

        logger.info(f"Auto-layouting {len(self.node_items)} nodes")

        # Build connection graph
        connections: Dict[str, List[str]] = {}
        incoming_count: Dict[str, int] = {}
        outgoing_count: Dict[str, int] = {}
        
        for node_name in self.node_items:
            connections[node_name] = []
            incoming_count[node_name] = 0
            outgoing_count[node_name] = 0

        # Analyze connections
        for node in self.node_items.values():
            for option in node.node.options:
                if option.nodelink and option.nodelink in self.node_items:
                    connections[node.node.nodename].append(option.nodelink)
                    incoming_count[option.nodelink] += 1
                    outgoing_count[node.node.nodename] += 1

        # Find root nodes (nodes with no incoming connections)
        root_nodes = [name for name, count in incoming_count.items() if count == 0]

        # If no clear roots, use nodes with most outgoing as roots
        if not root_nodes:
            max_out = max(outgoing_count.values()) if outgoing_count else 0
            root_nodes = [name for name, count in outgoing_count.items() if count == max_out]

        # If still no roots, use all nodes
        if not root_nodes:
            root_nodes = list(self.node_items.keys())

        # Assign levels using improved topological sort
        levels: Dict[str, int] = {}
        self._assign_levels_recursive(root_nodes, connections, levels, set(), set(), 0)

        # Handle any remaining nodes (cycles or disconnected)
        for node_name in self.node_items:
            if node_name not in levels:
                levels[node_name] = 0

        # Group nodes by level
        level_groups: Dict[int, List[str]] = {}
        for node_name, level in levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(node_name)

        # Sort nodes within each level to minimize edge crossings
        for level in level_groups:
            level_groups[level] = self._sort_level_by_connectivity(
                level_groups[level], connections, incoming_count
            )

        # Position nodes by level with improved spacing
        max_level = max(levels.values()) if levels else 0
        
        # Calculate vertical centering
        total_height = (max_level + 1) * self.base_spacing_y
        start_y = -total_height / 2 + self.base_spacing_y / 2

        for level, node_names in level_groups.items():
            # Calculate centered horizontal position
            level_width = len(node_names) * self.base_spacing_x
            start_x = -level_width / 2 + self.base_spacing_x / 2

            for i, node_name in enumerate(node_names):
                x = start_x + i * self.base_spacing_x
                y = start_y + level * self.base_spacing_y
                self.node_items[node_name].setPos(x, y)

        # Update arrows after positioning
        for arrow in self.arrow_items:
            arrow.update_position()
            
        # Update grid to cover the diagram area
        if self.grid_item:
            self.grid_item.update_bounds(self.node_items.values())

    def _assign_levels_recursive(
        self, 
        nodes: List[str], 
        connections: Dict[str, List[str]], 
        levels: Dict[str, int],
        visited: set,
        temp_visited: set,
        current_level: int
    ):
        """Recursively assign levels to nodes"""
        for node_name in nodes:
            if node_name in temp_visited:
                continue  # Cycle detected
            if node_name in visited:
                continue
                
            temp_visited.add(node_name)
            
            # Level is the maximum of current level and any child's level + 1
            max_child_level = current_level
            if node_name in connections:
                for child in connections[node_name]:
                    if child not in levels:
                        self._assign_levels_recursive(
                            [child], connections, levels, visited, temp_visited, current_level + 1
                        )
                    if child in levels:
                        max_child_level = max(max_child_level, levels[child] + 1)
            
            levels[node_name] = max_child_level
            visited.add(node_name)
            temp_visited.remove(node_name)

    def _sort_level_by_connectivity(
        self, 
        nodes: List[str], 
        connections: Dict[str, List[str]],
        incoming_count: Dict[str, int]
    ) -> List[str]:
        """Sort nodes within a level to minimize edge crossings"""
        # Sort by number of connections (nodes with more connections in the middle)
        return sorted(
            nodes, 
            key=lambda x: (
                -len(connections.get(x, [])),
                incoming_count.get(x, 0)
            )
        )

    def fit_to_view_with_margin(self):
        """Fit all items in view with margin"""
        if not self.node_items:
            return
            
        # Get bounding rect with some padding
        items = list(self.node_items.values())
        if not items:
            return
            
        min_x = min(item.pos().x() for item in items) - 200
        max_x = max(item.pos().x() for item in items) + 200
        min_y = min(item.pos().y() for item in items) - 200
        max_y = max(item.pos().y() for item in items) + 200
        
        rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        self.scale(0.92, 0.92)  # Add some margin

    def show_context_menu(self, position):
        """Show context menu for diagram"""
        menu = QMenu(self)

        # Add node action
        add_node_action = menu.addAction("Add Node")
        add_node_action.triggered.connect(self.add_node_at_position)

        menu.addSeparator()

        # Zoom actions
        zoom_in_action = menu.addAction("Zoom In")
        zoom_in_action.triggered.connect(self.zoom_in)

        zoom_out_action = menu.addAction("Zoom Out")
        zoom_out_action.triggered.connect(self.zoom_out)

        fit_action = menu.addAction("Fit to View")
        fit_action.triggered.connect(self.fit_to_view_with_margin)

        menu.addSeparator()
        
        # Toggle grid
        grid_action = menu.addAction("Toggle Grid")
        grid_action.triggered.connect(self.toggle_grid)
        
        # Layout options
        relayout_action = menu.addAction("Re-layout")
        relayout_action.triggered.connect(lambda: self.auto_layout_nodes())

        menu.exec(self.mapToGlobal(position))
        
    def toggle_grid(self):
        """Toggle grid visibility"""
        if self.grid_item:
            self.grid_item.setVisible(not self.grid_item.isVisible())

    def add_node_at_position(self):
        """Add a new node at mouse position"""
        pass

    def zoom_in(self):
        """Zoom in the view"""
        if self.transform().m11() < self.ZOOM_MAX:
            self.scale(self.ZOOM_STEP, self.ZOOM_STEP)

    def zoom_out(self):
        """Zoom out the view"""
        if self.transform().m11() > self.ZOOM_MIN:
            self.scale(1/self.ZOOM_STEP, 1/self.ZOOM_STEP)

    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.resetTransform()
        self.scale(1.0, 1.0)

    def fit_to_view(self):
        """Fit all items in view"""
        if self.scene.items():
            self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.scale(0.9, 0.9)

    def wheelEvent(self, event):
        """Handle mouse wheel for zooming - centers on mouse cursor position"""
        # Get the current zoom level
        current_zoom = self.transform().m11()
        
        # Determine zoom direction
        zoom_in = event.angleDelta().y() > 0
        
        # Calculate the new zoom factor
        if zoom_in:
            new_zoom = current_zoom * self.ZOOM_STEP
            if new_zoom > self.ZOOM_MAX:
                return  # Don't zoom beyond maximum
        else:
            new_zoom = current_zoom / self.ZOOM_STEP
            if new_zoom < self.ZOOM_MIN:
                return  # Don't zoom beyond minimum
        
        # Get the mouse position in scene coordinates before scaling
        mouse_pos = self.mapToScene(event.position().toPoint())
        
        # Calculate the offset from the viewport center
        viewport_center = self.viewport().rect().center()
        viewport_center_scene = self.mapToScene(viewport_center)
        
        # Scale the view
        if zoom_in:
            self.scale(self.ZOOM_STEP, self.ZOOM_STEP)
        else:
            self.scale(1/self.ZOOM_STEP, 1/self.ZOOM_STEP)
        
        # After scaling, adjust the scroll position to keep the point under mouse fixed
        # This is handled automatically by AnchorUnderMouse, but let's ensure smooth behavior
        self.centerOn(mouse_pos)


class GridItem(QGraphicsRectItem):
    """Background grid for diagram alignment"""
    
    def __init__(self):
        super().__init__()
        self.grid_size = 50
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setBrush(QBrush(DiagramColors.BACKGROUND))
        self.setZValue(-100)
        
    def update_bounds(self, nodes):
        """Update grid to cover the diagram area"""
        if not nodes:
            return
            
        min_x = min(node.pos().x() for node in nodes) - 1000
        max_x = max(node.pos().x() for node in nodes) + 1000
        min_y = min(node.pos().y() for node in nodes) - 1000
        max_y = max(node.pos().y() for node in nodes) + 1000
        
        self.setRect(min_x, min_y, max_x - min_x, max_y - min_y)
        
    def paint(self, painter, option, widget=None):
        """Paint the grid"""
        rect = self.rect()
        painter.fillRect(rect, DiagramColors.BACKGROUND)
        
        # Draw grid lines
        pen = QPen(DiagramColors.GRID_COLOR)
        pen.setWidth(1)
        painter.setPen(pen)
        
        # Vertical lines
        x = rect.left()
        while x <= rect.right():
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += self.grid_size
            
        # Horizontal lines
        y = rect.top()
        while y <= rect.bottom():
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += self.grid_size


class NodeItem(QGraphicsRectItem):
    """Graphics item representing a dialogue node with enhanced styling"""

    # Class-level cache for node dimensions
    MARGIN = 20
    MIN_WIDTH = 180
    MAX_WIDTH = 320
    MIN_HEIGHT = 90
    BASE_HEIGHT = 70
    
    def __init__(self, node: DialogueNode):
        super().__init__()
        self.node = node
        
        # Calculate optimal dimensions based on content
        self._calculate_dimensions()
        
        # Set rectangle
        self.setRect(0, 0, self.width, self.height)
        
        # Set appearance with gradient based on node type
        self.setBrush(self._create_gradient_brush())
        self.setPen(self._create_pen())
        
        # Make selectable and movable
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        
        # Add visual elements
        self._create_title_text()
        self._create_npc_text()
        self._create_badges()
        
        # Connection points (on the edges)
        self._update_connection_points()
        
    def _calculate_dimensions(self):
        """Calculate optimal node dimensions based on content"""
        # Width based on NPC text length
        text_len = len(self.node.npctext)
        self.width = self.MIN_WIDTH + min(100, text_len // 10)
        self.width = min(self.MAX_WIDTH, self.width)
        
        # Height based on options and skill checks
        option_count = len(self.node.options)
        self.height = self.BASE_HEIGHT + option_count * 12 + (30 if self.node.skillchecks else 0)
        self.height = max(self.MIN_HEIGHT, self.height)
        
        # Ensure we have enough height for text
        self.height = max(self.height, 100)
        
    def _create_gradient_brush(self) -> QBrush:
        """Create gradient brush based on node type"""
        # Determine node type
        if self.node.is_wtg:
            base_color = DiagramColors.NODE_START
            light_color = DiagramColors.NODE_START_LIGHT
        elif self.node.hidden:
            base_color = DiagramColors.NODE_HIDDEN
            light_color = DiagramColors.NODE_HIDDEN_LIGHT
        elif self.node.skillchecks:
            base_color = DiagramColors.NODE_SKILLCHECK
            light_color = DiagramColors.NODE_SKILLCHECK_LIGHT
        else:
            base_color = DiagramColors.NODE_REGULAR
            light_color = DiagramColors.NODE_REGULAR_LIGHT
            
        # Create gradient from light to base (top to bottom)
        gradient = QLinearGradient(0, 0, 0, self.height)
        gradient.setColorAt(0, light_color)
        gradient.setColorAt(0.4, base_color)
        gradient.setColorAt(1, base_color.darker(120))
        
        return QBrush(gradient)
        
    def _create_pen(self) -> QPen:
        """Create pen with rounded corners effect"""
        if self.node.is_wtg:
            color = DiagramColors.NODE_START.darker(150)
        elif self.node.hidden:
            color = DiagramColors.NODE_HIDDEN.darker(150)
        elif self.node.skillchecks:
            color = DiagramColors.NODE_SKILLCHECK.darker(150)
        else:
            color = DiagramColors.NODE_REGULAR.darker(150)
            
        pen = QPen(color, 2)
        return pen
        
    def _create_title_text(self):
        """Create formatted title text"""
        # Title with node type indicator
        title_text = self.node.nodename
        if self.node.is_wtg:
            title_text = "► " + title_text
        if self.node.hidden:
            title_text = "◂ " + title_text
            
        self.title_text = QGraphicsTextItem(title_text, self)
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        self.title_text.setFont(font)
        self.title_text.setDefaultTextColor(DiagramColors.TEXT_ON_DARK)
        self.title_text.setPos(self.MARGIN, self.MARGIN)
        
    def _create_npc_text(self):
        """Create NPC text with proper wrapping"""
        # Truncate text for display
        max_chars = int((self.width - self.MARGIN * 2) / 7) * 3
        display_text = self.node.npctext[:max_chars]
        if len(self.node.npctext) > max_chars:
            display_text += "..."
            
        self.npc_text = QGraphicsTextItem(display_text, self)
        font = QFont("Segoe UI", 8)
        self.npc_text.setFont(font)
        self.npc_text.setDefaultTextColor(DiagramColors.TEXT_ON_DARK)
        self.npc_text.setOpacity(0.9)
        self.npc_text.setPos(self.MARGIN, self.MARGIN + 22)
        
        # Set text width constraint
        self.npc_text.setTextWidth(self.width - self.MARGIN * 2)
        
    def _create_badges(self):
        """Create badges showing node information"""
        badge_y = self.height - 18
        
        # Options count badge
        option_count = len(self.node.options)
        if option_count > 0:
            self.options_badge = QGraphicsTextItem(f"▸ {option_count} options", self)
            font = QFont("Segoe UI", 7)
            self.options_badge.setFont(font)
            self.options_badge.setDefaultTextColor(DiagramColors.TEXT_ON_DARK)
            self.options_badge.setOpacity(0.8)
            self.options_badge.setPos(self.MARGIN, badge_y)
            
        # Skill checks badge
        if self.node.skillchecks:
            skill_count = len(self.node.skillchecks)
            self.skill_badge = QGraphicsTextItem(f"★ {skill_count} checks", self)
            font = QFont("Segoe UI", 7, QFont.Weight.Bold)
            self.skill_badge.setFont(font)
            self.skill_badge.setDefaultTextColor(DiagramColors.TEXT_ON_DARK.lighter(150))
            self.skill_badge.setOpacity(0.9)
            
            # Position after options badge if exists
            if option_count > 0:
                self.skill_badge.setPos(self.MARGIN + 70, badge_y)
            else:
                self.skill_badge.setPos(self.MARGIN, badge_y)
                
    def _update_connection_points(self):
        """Update connection points based on node size"""
        self.connection_points = {
            'top': QPointF(self.width / 2, 0),
            'bottom': QPointF(self.width / 2, self.height),
            'left': QPointF(0, self.height / 2),
            'right': QPointF(self.width, self.height / 2)
        }
        
    def itemChange(self, change, value):
        """Handle item changes"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Update connected arrows when node moves
            for arrow in self.scene().items():
                if isinstance(arrow, CurvedArrowItem) and (arrow.source_item == self or arrow.target_item == self):
                    arrow.update_position()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            # Update appearance when selected
            if value:
                self.setPen(QPen(DiagramColors.NODE_SELECTED, 3))
            else:
                self.setPen(self._create_pen())
                
        return super().itemChange(change, value)
        
    def get_connection_point(self, direction: str) -> QPointF:
        """Get connection point for arrows"""
        base_point = self.connection_points.get(direction, QPointF(self.width / 2, self.height / 2))
        return self.pos() + base_point


class CurvedArrowItem(QGraphicsLineItem):
    """Graphics item representing a curved connection between nodes with reaction-based coloring"""

    def __init__(self, source_item: NodeItem, target_item: NodeItem, option: PlayerOption):
        super().__init__()
        self.source_item = source_item
        self.target_item = target_item
        self.option = option
        
        # Set appearance based on reaction type
        self.setPen(self._create_pen())
        self.setZValue(-1)  # Draw behind nodes
        
        # Create improved arrow head
        self.arrow_head = QGraphicsPolygonItem(self)
        self._create_arrow_head()
        
        # Curve control points
        self.control_points: List[QPointF] = []
        
        # Initial position update
        self.update_position()

    def _create_pen(self) -> QPen:
        """Create pen based on reaction type"""
        if self.option.reaction == Reaction.GOOD:
            color = DiagramColors.ARROW_GOOD
        elif self.option.reaction == Reaction.BAD:
            color = DiagramColors.ARROW_BAD
        else:
            color = DiagramColors.ARROW_NEUTRAL
            
        pen = QPen(color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        return pen
        
    def _create_arrow_head(self):
        """Create improved arrow head"""
        arrow_size = 12
        arrow_points = QPolygonF([
            QPointF(0, 0),
            QPointF(-arrow_size, -arrow_size / 2),
            QPointF(-arrow_size, arrow_size / 2)
        ])
        self.arrow_head.setPolygon(arrow_points)
        self.arrow_head.setBrush(QBrush(self.pen().color()))
        self.arrow_head.setPen(QPen(Qt.PenStyle.NoPen))

    def update_position(self):
        """Update arrow position with bezier curve"""
        source_pos = self.source_item.get_connection_point('right')
        target_pos = self.target_item.get_connection_point('left')
        
        # Calculate control points for bezier curve
        dx = target_pos.x() - source_pos.x()
        dy = target_pos.y() - source_pos.y()
        
        # Curve intensity based on distance
        curve_intensity = min(abs(dx) * 0.4, 150)
        
        # Control points for smooth curve
        cp1 = QPointF(source_pos.x() + curve_intensity, source_pos.y())
        cp2 = QPointF(target_pos.x() - curve_intensity, target_pos.y())
        
        # Store for paint
        self.control_points = [source_pos, cp1, cp2, target_pos]
        
        # Draw the curve
        path = QPainterPath(source_pos)
        path.cubicTo(cp1, cp2, target_pos)
        
        # Get the last point for arrow head
        self.setLine(source_pos.x(), source_pos.y(), target_pos.x(), target_pos.y())
        
        # Position arrow head at target
        angle = math.atan2(target_pos.y() - cp2.y(), target_pos.x() - cp2.x())
        arrow_pos = target_pos - QPointF(math.cos(angle) * 12, math.sin(angle) * 12)
        self.arrow_head.setPos(arrow_pos)
        self.arrow_head.setRotation(angle * 180 / math.pi + 180)
        
        # Add option text label
        self._update_label(source_pos, target_pos, cp1, cp2)
        
    def _update_label(self, start: QPointF, end: QPointF, cp1: QPointF, cp2: QPointF):
        """Update or create label for the arrow"""
        if not hasattr(self, 'label_item'):
            self.label_item = QGraphicsTextItem(self.option.optiontext[:25], self)
            font = QFont("Segoe UI", 7)
            self.label_item.setFont(font)
            self.label_item.setDefaultTextColor(DiagramColors.TEXT_SECONDARY)
            
        # Update text
        display_text = self.option.optiontext[:25]
        if len(self.option.optiontext) > 25:
            display_text += "..."
        self.label_item.setPlainText(display_text)
        
        # Position at curve midpoint
        # Approximate bezier midpoint
        t = 0.5
        mx = (1-t)**3 * start.x() + 3*(1-t)**2 * t * cp1.x() + 3*(1-t) * t**2 * cp2.x() + t**3 * end.x()
        my = (1-t)**3 * start.y() + 3*(1-t)**2 * t * cp1.y() + 3*(1-t) * t**2 * cp2.y() + t**3 * end.y()
        
        label_rect = self.label_item.boundingRect()
        self.label_item.setPos(mx - label_rect.width() / 2, my - label_rect.height() / 2 - 8)
        
    def paint(self, painter, option, widget=None):
        """Paint curved arrow instead of straight line"""
        if len(self.control_points) < 4:
            return
            
        source, cp1, cp2, target = self.control_points
        
        # Draw bezier curve
        path = QPainterPath(source)
        path.cubicTo(cp1, cp2, target)
        
        painter.setPen(self.pen())
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        
        # Draw arrow head manually (already positioned in update_position())
        # Don't call super().paint() as it would draw the straight line too
