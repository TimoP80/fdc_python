"""
Diagram widget for visual dialogue editing
"""

import math
import logging
from typing import Dict, List, Optional, Tuple

from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsLineItem, QGraphicsPolygonItem, QMenu,
    QGraphicsSceneMouseEvent, QGraphicsSceneContextMenuEvent
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QObject
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPolygonF

from models.dialogue import Dialogue, DialogueNode

logger = logging.getLogger(__name__)


class DiagramWidget(QGraphicsView):
    """Main diagram widget for visual dialogue editing"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Configure view
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Scene settings
        self.scene.setSceneRect(-5000, -5000, 10000, 10000)

        # Node management
        self.node_items: Dict[str, NodeItem] = {}
        self.arrow_items: List[ArrowItem] = []

        # Interaction state
        self.selected_node: Optional[NodeItem] = None
        self.drag_start_pos: Optional[QPointF] = None

        # Enable context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def set_dialogue(self, dialogue: Dialogue):
        """Update diagram with dialogue data"""
        self.clear_diagram()
        if not dialogue:
            return

        # Create node items
        for node in dialogue.nodes:
            node_item = NodeItem(node)
            self.node_items[node.nodename] = node_item
            self.scene.addItem(node_item)

        # Create arrow items for connections
        for node in dialogue.nodes:
            for option in node.options:
                if option.nodelink and option.nodelink in self.node_items:
                    source_item = self.node_items[node.nodename]
                    target_item = self.node_items[option.nodelink]
                    arrow = ArrowItem(source_item, target_item, option.optiontext)
                    self.arrow_items.append(arrow)
                    self.scene.addItem(arrow)

        # Auto-layout nodes
        self.auto_layout_nodes()

    def clear_diagram(self):
        """Clear all diagram items"""
        self.scene.clear()
        self.node_items.clear()
        self.arrow_items.clear()

    def auto_layout_nodes(self):
        """Automatically position nodes in a hierarchical layout"""
        if not self.node_items:
            return

        logger.info(f"Auto-layouting {len(self.node_items)} nodes using hierarchical layout")

        # Build connection graph
        connections = {}
        incoming_count = {}
        for node_name in self.node_items:
            connections[node_name] = []
            incoming_count[node_name] = 0

        for node in self.node_items.values():
            for option in node.node.options:
                if option.nodelink and option.nodelink in self.node_items:
                    connections[node.node.nodename].append(option.nodelink)
                    incoming_count[option.nodelink] += 1

        # Find root nodes (nodes with no incoming connections)
        root_nodes = [name for name, count in incoming_count.items() if count == 0]

        # If no clear roots, use all nodes as potential roots
        if not root_nodes:
            root_nodes = list(self.node_items.keys())

        logger.debug(f"Root nodes: {root_nodes}")

        # Assign levels using topological sort
        levels = {}
        visited = set()
        temp_visited = set()

        def assign_level(node_name, level=0):
            if node_name in temp_visited:
                return  # Cycle detected, skip
            if node_name in visited:
                return

            temp_visited.add(node_name)
            max_child_level = level

            for child in connections[node_name]:
                assign_level(child, level + 1)
                if child in levels:
                    max_child_level = max(max_child_level, levels[child] + 1)

            levels[node_name] = max_child_level
            visited.add(node_name)
            temp_visited.remove(node_name)

        # Assign levels starting from roots
        for root in root_nodes:
            assign_level(root, 0)

        # Handle any remaining nodes (cycles or disconnected)
        for node_name in self.node_items:
            if node_name not in levels:
                levels[node_name] = 0

        # Group nodes by level
        level_groups = {}
        for node_name, level in levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(node_name)

        # Position nodes by level
        spacing_x = 350
        spacing_y = 250

        max_level = max(levels.values()) if levels else 0
        start_y = -max_level * spacing_y / 2

        for level, node_names in level_groups.items():
            # Sort nodes within level to minimize crossings (simple heuristic)
            node_names.sort(key=lambda x: len(connections[x]))

            level_width = len(node_names) * spacing_x
            start_x = -level_width / 2

            for i, node_name in enumerate(node_names):
                x = start_x + i * spacing_x
                y = start_y + level * spacing_y
                self.node_items[node_name].setPos(x, y)
                logger.debug(f"Node {node_name} at level {level}, position ({x:.1f}, {y:.1f})")

        # Update arrows after positioning
        logger.debug("Updating arrow positions after hierarchical layout")
        for arrow in self.arrow_items:
            arrow.update_position()

    def show_context_menu(self, position):
        """Show context menu for diagram"""
        menu = QMenu(self)

        # Add node action
        add_node_action = menu.addAction("Add Node")
        add_node_action.triggered.connect(self.add_node_at_position)

        # Zoom actions
        menu.addSeparator()
        zoom_in_action = menu.addAction("Zoom In")
        zoom_in_action.triggered.connect(self.zoom_in)

        zoom_out_action = menu.addAction("Zoom Out")
        zoom_out_action.triggered.connect(self.zoom_out)

        fit_action = menu.addAction("Fit to View")
        fit_action.triggered.connect(self.fit_to_view)

        menu.exec(self.mapToGlobal(position))

    def add_node_at_position(self):
        """Add a new node at mouse position"""
        # This will be connected to dialog manager later
        pass

    def zoom_in(self):
        """Zoom in the view"""
        self.scale(1.2, 1.2)

    def zoom_out(self):
        """Zoom out the view"""
        self.scale(1/1.2, 1/1.2)

    def fit_to_view(self):
        """Fit all items in view"""
        if self.scene.items():
            self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.scale(0.9, 0.9)  # Add some margin

    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoom_factor = 1.15
            if event.angleDelta().y() < 0:
                zoom_factor = 1 / zoom_factor
            self.scale(zoom_factor, zoom_factor)
        else:
            super().wheelEvent(event)


class NodeItem(QGraphicsRectItem):
    """Graphics item representing a dialogue node"""

    def __init__(self, node: DialogueNode):
        super().__init__()
        self.node = node

        # Set appearance
        self.setRect(-100, -50, 200, 100)
        self.setBrush(QBrush(QColor(240, 240, 255)))
        self.setPen(QPen(QColor(100, 100, 150), 2))

        # Make selectable and movable
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        # Add text items
        self.title_text = QGraphicsTextItem(self.node.nodename, self)
        self.title_text.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.title_text.setPos(-90, -40)

        self.npc_text = QGraphicsTextItem(self.node.npctext[:50] + "..." if len(self.node.npctext) > 50 else self.node.npctext, self)
        self.npc_text.setFont(QFont("Arial", 8))
        self.npc_text.setPos(-90, -20)

        # Connection points
        self.connection_points = {
            'top': QPointF(0, -50),
            'bottom': QPointF(0, 50),
            'left': QPointF(-100, 0),
            'right': QPointF(100, 0)
        }

    def itemChange(self, change, value):
        """Handle item changes"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Update connected arrows when node moves
            for arrow in self.scene().items():
                if isinstance(arrow, ArrowItem) and (arrow.source_item == self or arrow.target_item == self):
                    arrow.update_position()
        return super().itemChange(change, value)

    def get_connection_point(self, direction: str) -> QPointF:
        """Get connection point for arrows"""
        return self.pos() + self.connection_points.get(direction, QPointF(0, 0))


class ArrowItem(QGraphicsLineItem):
    """Graphics item representing a connection between nodes"""

    def __init__(self, source_item: NodeItem, target_item: NodeItem, label: str = ""):
        super().__init__()
        self.source_item = source_item
        self.target_item = target_item
        self.label = label

        # Set appearance
        self.setPen(QPen(QColor(100, 100, 100), 2))

        # Create arrow head
        self.arrow_head = QGraphicsPolygonItem(self)
        arrow_points = QPolygonF([
            QPointF(0, 0),
            QPointF(-10, -5),
            QPointF(-10, 5)
        ])
        self.arrow_head.setPolygon(arrow_points)
        self.arrow_head.setBrush(QBrush(QColor(100, 100, 100)))
        self.arrow_head.setPen(QPen(Qt.PenStyle.NoPen))

        # Create label
        self.label_item = QGraphicsTextItem(label, self)
        self.label_item.setFont(QFont("Arial", 8))
        self.label_item.setDefaultTextColor(QColor(100, 100, 100))

        # Initial position update
        self.update_position()

    def update_position(self):
        """Update arrow position based on node positions"""
        source_pos = self.source_item.get_connection_point('right')
        target_pos = self.target_item.get_connection_point('left')

        logger.debug(f"Arrow from {self.source_item.node.nodename} to {self.target_item.node.nodename}")
        logger.debug(f"Source pos: ({source_pos.x():.1f}, {source_pos.y():.1f})")
        logger.debug(f"Target pos: ({target_pos.x():.1f}, {target_pos.y():.1f})")

        # Check for potential issues
        dx = target_pos.x() - source_pos.x()
        dy = target_pos.y() - source_pos.y()
        distance = math.sqrt(dx*dx + dy*dy)
        logger.debug(f"Distance: {distance:.1f}, dx: {dx:.1f}, dy: {dy:.1f}")

        if abs(dx) < 50 and abs(dy) < 50:
            logger.warning(f"Arrow too short or overlapping: {self.source_item.node.nodename} -> {self.target_item.node.nodename}")

        # Set line
        self.setLine(source_pos.x(), source_pos.y(), target_pos.x(), target_pos.y())

        # Position arrow head
        angle = math.atan2(target_pos.y() - source_pos.y(), target_pos.x() - source_pos.x())
        arrow_pos = target_pos - QPointF(math.cos(angle) * 10, math.sin(angle) * 10)
        self.arrow_head.setPos(arrow_pos)
        self.arrow_head.setRotation(angle * 180 / math.pi)

        # Position label
        mid_point = (source_pos + target_pos) / 2
        self.label_item.setPos(mid_point - QPointF(self.label_item.boundingRect().width() / 2, 10))