"""
Plugin Designer UI Components

This module provides the visual interface for the plugin designer including:
- Component palette with drag-and-drop
- Visual workflow canvas
- Property editors
- Preview mode
- Code preview
"""

import math
import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QScrollArea,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsLineItem, QLabel, QFrame, QGroupBox,
    QListWidget, QListWidgetItem, QStackedWidget, QDialog, QDialogButtonBox,
    QTextEdit, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QPushButton, QToolButton, QTabWidget, QGridLayout, QFormLayout,
    QSplitterHandle, QSizePolicy, QApplication
)

# Import fade animation widgets
from ui.fallout_widgets import FadeLineEdit, FadeTextEdit, FadeLabel, FadeButton
from PyQt6.QtCore import Qt, QPointF, QPoint, QRectF, pyqtSignal, QMimeData, QTimer, QSize
from PyQt6.QtGui import (
    QPen, QBrush, QColor, QFont, QPainter, QPainterPath, QCursor,
    QDrag, QKeyEvent, QMouseEvent, QFocusEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent,
    QSyntaxHighlighter, QTextCharFormat, QTextFormat
)

from core.plugin_designer import (
    PluginDesign, ComponentInstance, Connection, ComponentDefinition,
    ComponentCategory, PortDefinition, PortType, DataType, DesignAction,
    COMPONENT_DEFINITIONS, get_template_library, CodeGenerator,
    UndoRedoManager, export_design, import_design, create_new_design, apply_template
)

logger = logging.getLogger(__name__)


# =============================================================================
# Component Colors
# =============================================================================

COMPONENT_COLORS = {
    ComponentCategory.UI_ELEMENT: QColor(74, 144, 217),      # Blue
    ComponentCategory.LOGIC_BLOCK: QColor(217, 74, 74),     # Red
    ComponentCategory.SERVICE_CONNECTOR: QColor(74, 217, 74),  # Green
    ComponentCategory.DATA_PROCESSOR: QColor(154, 74, 217),  # Purple
    ComponentCategory.EVENT_HANDLER: QColor(217, 217, 74),  # Yellow
}


# =============================================================================
# Python Syntax Highlighter
# =============================================================================

class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """
    Python syntax highlighter for QTextEdit/QPlainTextEdit.
    Recognizes keywords, string literals, comments, decorators, function/class
    definitions, indentation-based blocks, built-in functions, and operators.
    """
    
    # Python keywords
    KEYWORDS = frozenset([
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
        'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
        'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
        'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try',
        'while', 'with', 'yield'
    ])
    
    # Python built-in functions
    BUILTINS = frozenset([
        'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
        'callable', 'chr', 'classmethod', 'compile', 'complex', 'delattr',
        'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec', 'filter',
        'float', 'format', 'frozenset', 'getattr', 'globals', 'hasattr',
        'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance', 'issubclass',
        'iter', 'len', 'list', 'locals', 'map', 'max', 'memoryview', 'min',
        'next', 'object', 'oct', 'open', 'ord', 'pow', 'print', 'property',
        'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice',
        'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple', 'type',
        'vars', 'zip', '__import__'
    ])
    
    # Python decorators
    DECORATORS = frozenset([
        'property', 'staticmethod', 'classmethod', 'abstractmethod',
        'override', 'cached_property', 'lru_cache', 'retry', 'timeout'
    ])
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._highlighting_rules = []
        self._setup_formatting_rules()
    
    def _setup_formatting_rules(self):
        """Set up the regex-based highlighting rules."""
        
        # Create color scheme
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor('#569CD6'))  # Blue
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor('#DCDCAA'))  # Yellow
        
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor('#C586C0'))  # Purple
        
        string_format = QTextCharFormat()
        string_format.setForeground(QColor('#CE9178'))  # Orange/Brown
        
        fstring_format = QTextCharFormat()
        fstring_format.setForeground(QColor('#CE9178'))  # Orange/Brown
        
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor('#6A9955'))  # Green
        comment_format.setFontItalic(True)
        
        docstring_format = QTextCharFormat()
        docstring_format.setForeground(QColor('#6A9955'))  # Green
        
        number_format = QTextCharFormat()
        number_format.setForeground(QColor('#B5CEA8'))  # Light Green
        
        function_def_format = QTextCharFormat()
        function_def_format.setForeground(QColor('#DCDCAA'))  # Yellow
        
        class_def_format = QTextCharFormat()
        class_def_format.setForeground(QColor('#4EC9B0'))  # Teal
        
        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor('#D4D4D4'))  # Light Gray
        
        self_Format = QTextCharFormat()
        self_Format.setForeground(QColor('#9CDCFE'))  # Light Blue
        
        # Build regex patterns
        
        # Decorators (@ decorator_name)
        self._highlighting_rules.append((
            re.compile(r'@\w+'),
            decorator_format
        ))
        
        # Single-line comments
        self._highlighting_rules.append((
            re.compile(r'#.*'),
            comment_format
        ))
        
        # Triple-quoted strings (docstrings) - must be before single quotes
        self._highlighting_rules.append((
            re.compile(r'"""[\s\S]*?"""'),
            docstring_format
        ))
        self._highlighting_rules.append((
            re.compile(r"'''[\s\S]*?'''"),
            docstring_format
        ))
        
        # f-strings with braces
        self._highlighting_rules.append((
            re.compile(r'f"(?:[^"\\]|\\.)*"'),
            fstring_format
        ))
        self._highlighting_rules.append((
            re.compile(r"f'(?:[^'\\]|\\.)*'"),
            fstring_format
        ))
        
        # Regular strings (double quotes)
        self._highlighting_rules.append((
            re.compile(r'"(?:[^"\\]|\\.)*"'),
            string_format
        ))
        
        # Regular strings (single quotes)
        self._highlighting_rules.append((
            re.compile(r"'(?:[^'\\]|\\.)*'"),
            string_format
        ))
        
        # Numbers (integers and floats)
        self._highlighting_rules.append((
            re.compile(r'\b\d+\.?\d*\b'),
            number_format
        ))
        
        # Hex numbers
        self._highlighting_rules.append((
            re.compile(r'\b0x[0-9a-fA-F]+\b'),
            number_format
        ))
        
        # self keyword
        self._highlighting_rules.append((
            re.compile(r'\bself\b'),
            self_Format
        ))
        
        # class definition
        self._highlighting_rules.append((
            re.compile(r'\bclass\s+\w+'),
            class_def_format
        ))
        
        # def function_name
        self._highlighting_rules.append((
            re.compile(r'\bdef\s+\w+'),
            function_def_format
        ))
        
        # Operators
        self._highlighting_rules.append((
            re.compile(r'[+\-*/%=<>!&|^~@:]+'),
            operator_format
        ))
        
        # Keywords (must be last to not match other patterns)
        for keyword in self.KEYWORDS:
            pattern = re.compile(r'\b' + keyword + r'\b')
            self._highlighting_rules.append((pattern, keyword_format))
        
        # Built-in functions (must be after keywords)
        for builtin in self.BUILTINS:
            pattern = re.compile(r'\b' + builtin + r'\b')
            self._highlighting_rules.append((pattern, builtin_format))
    
    def highlightBlock(self, text: str):
        """
        Apply syntax highlighting to the given block of text.
        
        This method is called by QSyntaxHighlighter for each text block.
        """
        # Handle indentation-based block detection
        self._highlight_indentation(text)
        
        # Apply all highlighting rules
        for pattern, fmt in self._highlighting_rules:
            iterator = pattern.finditer(text)
            for match in iterator:
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, fmt)
    
    def _highlight_indentation(self, text: str):
        """
        Highlight indentation to show block structure.
        """
        if not text:
            return
        
        # Check for leading whitespace
        indent_format = QTextCharFormat()
        indent_format.setForeground(QColor('#404040'))  # Dark gray
        
        # Count leading spaces
        indent_count = len(text) - len(text.lstrip())
        if indent_count > 0:
            self.setFormat(0, indent_count, indent_format)


# =============================================================================
# Graphics Items for Canvas
# =============================================================================

class PortItem(QGraphicsRectItem):
    """A port on a component for connections"""
    
    Z_PORT = 15  # Above component
    
    def __init__(self, port_def: PortDefinition, is_input: bool, parent=None):
        super().__init__(parent)
        self.port_def = port_def
        self.is_input = is_input
        self.connected = False
        
        # Set appearance
        self.setBrush(QBrush(QColor(200, 200, 200)))
        self.setPen(QPen(QColor(100, 100, 100), 1))
        self.setRect(-6, -6, 12, 12)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        
        # Set z-value to be above component
        self.setZValue(self.Z_PORT)
    
    def set_connected(self, connected: bool):
        """Update appearance based on connection status"""
        self.connected = connected
        if connected:
            self.setBrush(QBrush(QColor(100, 200, 100)))
        else:
            self.setBrush(QBrush(QColor(200, 200, 200))) 


class ComponentGraphicsItem(QGraphicsRectItem):
    """A component instance on the canvas"""
    
    # Z-values for proper layering
    Z_COMPONENT = 10
    Z_PORT = 15
    Z_CONNECTION = 5
    Z_SELECTION = 20
    
    # Custom signal for position changes
    position_changed = pyqtSignal(str)  # Emits component ID
    
    def __init__(self, component: ComponentInstance, definition: ComponentDefinition, parent=None):
        super().__init__(parent)
        self.component = component
        self.definition = definition
        
        # Set size
        width = component.width or definition.default_width
        height = component.height or definition.default_height
        self.setRect(0, 0, width, height)
        
        # Set appearance
        color = QColor(definition.color) if definition.color else COMPONENT_COLORS.get(definition.category, QColor(150, 150, 150))
        self.setBrush(QBrush(color.lighter(130)))
        self.setPen(QPen(color, 2))
        
        # Enable dragging
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        # Set z-value for proper layering (above connections, below selection)
        self.setZValue(self.Z_COMPONENT)
        
        # Create label
        self.label_item = QGraphicsTextItem(self)
        label_text = component.label or definition.name
        self.label_item.setPlainText(label_text)
        self.label_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.label_item.setDefaultTextColor(QColor(255, 255, 255))
        self.label_item.setPos(10, 5)
        self.label_item.setZValue(self.Z_COMPONENT + 1)  # Above component body
        
        # Create ports
        self.input_ports: List[PortItem] = []
        self.output_ports: List[PortItem] = []
        
        self._create_ports()
    
    def _create_ports(self):
        """Create port items"""
        # Input ports on left
        for i, port_def in enumerate(self.definition.input_ports):
            port = PortItem(port_def, True, self)
            port.setPos(-6, 30 + i * 25)
            self.input_ports.append(port)
        
        # Output ports on right
        for i, port_def in enumerate(self.definition.output_ports):
            port = PortItem(port_def, False, self)
            port.setPos(self.rect().width() - 6, 30 + i * 25)
            self.output_ports.append(port)
    
    def itemChange(self, change, value):
        """Handle item changes"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update component position in the data model
            new_pos = value
            self.component.x = new_pos.x()
            self.component.y = new_pos.y()
            
            # Update connected port positions if width changed
            self.update_port_positions()
            
            # Emit signal to notify listeners (canvas will update connections)
            self.position_changed.emit(self.component.id)
        
        return super().itemChange(change, value)
    
    def get_port_at_position(self, scene_pos: QPointF) -> Optional[Tuple[PortItem, bool]]:
        """Get port at scene position"""
        # Check input ports
        for port in self.input_ports:
            port_scene_pos = port.scenePos()
            if (port_scene_pos - scene_pos).manhattanLength() < 15:
                return port, True
        
        # Check output ports
        for port in self.output_ports:
            port_scene_pos = port.scenePos()
            if (port_scene_pos - scene_pos).manhattanLength() < 15:
                return port, False
        
        return None
    
    def update_port_positions(self):
        """Update port positions when size changes"""
        for i, port in enumerate(self.output_ports):
            port.setPos(self.rect().width() - 6, 30 + i * 25)


class ConnectionGraphicsItem(QGraphicsLineItem):
    """A connection line between components"""
    
    Z_CONNECTION = 5  # Below components
    
    def __init__(self, connection: Connection, source_item: ComponentGraphicsItem, 
                 target_item: ComponentGraphicsItem, parent=None):
        super().__init__(parent)
        self.connection = connection
        self.source_item = source_item
        self.target_item = target_item
        
        self.setPen(QPen(QColor(80, 80, 80), 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        # Set z-value to be below components
        self.setZValue(self.Z_CONNECTION)
        
        self._update_line()
    
    def _update_line(self):
        """Update line positions"""
        # Get port positions
        source_pos = self._get_port_position(self.source_item, self.connection.source_port_id, False)
        target_pos = self._get_port_position(self.target_item, self.connection.target_port_id, True)
        
        if source_pos and target_pos:
            self.setLine(source_pos.x(), source_pos.y(), target_pos.x(), target_pos.y())
    
    def _get_port_position(self, item: ComponentGraphicsItem, port_id: str, is_input: bool) -> Optional[QPointF]:
        """Get position of a port"""
        ports = item.input_ports if is_input else item.output_ports
        for port in ports:
            if port.port_def.id == port_id:
                return port.scenePos()
        return None
    
    def update_positions(self):
        """Update positions when connected items move"""
        self._update_line()


# =============================================================================
# Palette Panel
# =============================================================================

class DraggableListWidget(QListWidget):
    """Custom QListWidget that properly handles drag operations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
    
    def startDrag(self, action):
        """Override startDrag to emit the component ID"""
        items = self.selectedItems()
        if items:
            item = items[0]
            def_id = item.data(Qt.ItemDataRole.UserRole)
            if def_id:
                # Create MIME data
                mime_data = QMimeData()
                mime_data.setText(def_id)
                
                # Get the item's visual rect for proper hot spot
                rect = self.visualItemRect(item)
                # Center the hot spot on the item
                hot_spot = QPoint(rect.width() // 2, rect.height() // 2)
                
                # Create drag object
                drag = QDrag(self)
                drag.setMimeData(mime_data)
                drag.setHotSpot(hot_spot)
                
                # Create a visual representation (pixmap)
                pixmap = self.viewport().grab(rect)
                drag.setPixmap(pixmap)
                
                # Start drag - use MoveAction for dragging within app, CopyAction for cross-app
                drag.exec(Qt.DropAction.CopyAction)
                return
        
        super().startDrag(action)


class ComponentPalette(QWidget):
    """Panel showing available components"""
    
    component_dragged = pyqtSignal(str)  # Component definition ID
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title = QLabel("Component Palette")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)
        
        # Search box
        self.search_box = FadeLineEdit()
        self.search_box.setPlaceholderText("Search components...")
        self.search_box.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_box)
        
        # Component list by category
        self.component_lists: Dict[ComponentCategory, QListWidget] = {}
        
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        
        for category in ComponentCategory:
            list_widget = DraggableListWidget()
            list_widget.setAcceptDrops(False)
            list_widget.itemClicked.connect(self._on_item_clicked)
            self.component_lists[category] = list_widget
            
            # Create scroll area
            scroll = QScrollArea()
            scroll.setWidget(list_widget)
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
            tabs.addTab(scroll, category.name.replace("_", " "))
        
        layout.addWidget(tabs)
        
        self._populate_components()
    
    def _populate_components(self, filter_text: str = ""):
        """Populate component lists"""
        for category, list_widget in self.component_lists.items():
            list_widget.clear()
            
            for def_id, definition in COMPONENT_DEFINITIONS.items():
                if definition.category != category:
                    continue
                
                # Apply filter
                if filter_text and filter_text.lower() not in definition.name.lower():
                    continue
                
                item = QListWidgetItem(definition.name)
                item.setData(Qt.ItemDataRole.UserRole, def_id)
                item.setToolTip(definition.description)
                
                # Set color indicator
                color = COMPONENT_COLORS.get(category, QColor(150, 150, 150))
                item.setBackground(color.lighter(150))
                
                list_widget.addItem(item)
    
    def _on_search_changed(self, text: str):
        """Handle search text change"""
        self._populate_components(text)
    
    def _on_item_clicked(self, item: QListWidgetItem):
        """Handle item click - start drag"""
        def_id = item.data(Qt.ItemDataRole.UserRole)
        if def_id:
            self.component_dragged.emit(def_id)


# =============================================================================
# Template Panel
# =============================================================================

class TemplatePanel(QWidget):
    """Panel showing plugin templates"""
    
    template_selected = pyqtSignal(object)  # PluginTemplate
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.templates = get_template_library()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title = QLabel("Templates")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)
        
        # Template list
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget)
        
        self._populate_templates()
    
    def _populate_templates(self):
        """Populate template list"""
        for template in self.templates:
            item = QListWidgetItem(template.name)
            item.setData(Qt.ItemDataRole.UserRole, template)
            item.setToolTip(template.description)
            self.list_widget.addItem(item)
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle template selection"""
        template = item.data(Qt.ItemDataRole.UserRole)
        if template:
            self.template_selected.emit(template)


# =============================================================================
# Property Editor Panel
# =============================================================================

class PropertyEditor(QWidget):
    """Panel for editing component properties"""
    
    property_changed = pyqtSignal(str, str, object)  # component_id, property_name, new_value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_component: Optional[ComponentInstance] = None
        self.current_definition: Optional[ComponentDefinition] = None
        self.property_widgets: Dict[str, QWidget] = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        self.title = QLabel("Properties")
        self.title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.title)
        
        # Scroll area for properties
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.properties_widget = QWidget()
        self.properties_layout = QFormLayout(self.properties_widget)
        self.properties_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        
        scroll.setWidget(self.properties_widget)
        layout.addWidget(scroll)
        
        # Empty state
        self._show_empty_state()
    
    def _show_empty_state(self):
        """Show empty state message"""
        self.title.setText("Properties")
        # Clear existing widgets
        while self.properties_layout.count():
            item = self.properties_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        empty_label = QLabel("Select a component to edit its properties")
        empty_label.setStyleSheet("color: gray; font-style: italic;")
        self.properties_layout.addRow(empty_label)
        self.property_widgets.clear()
    
    def set_component(self, component: ComponentInstance, definition: ComponentDefinition):
        """Set the component to edit"""
        self.current_component = component
        self.current_definition = definition
        
        self.title.setText(f"Properties - {definition.name}")
        
        # Clear existing widgets
        while self.properties_layout.count():
            item = self.properties_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.property_widgets.clear()
        
        # Create property editors
        for prop_name, prop_schema in definition.property_schema.items():
            value = component.properties.get(prop_name, prop_schema.get("default", ""))
            
            widget = self._create_property_widget(prop_name, prop_schema, value)
            self.properties_layout.addRow(prop_schema.get("label", prop_name) + ":", widget)
            self.property_widgets[prop_name] = widget
        
        # Add component name/label field
        label_edit = FadeLineEdit(component.label)
        label_edit.textChanged.connect(lambda t: self._on_property_changed("label", t))
        self.properties_layout.addRow("Label:", label_edit)
        self.property_widgets["_label"] = label_edit
    
    def _create_property_widget(self, prop_name: str, schema: Dict, value: Any) -> QWidget:
        """Create appropriate widget for a property"""
        prop_type = schema.get("type", "string")
        
        if prop_type == "boolean":
            widget = QCheckBox()
            widget.setChecked(bool(value))
            widget.stateChanged.connect(lambda s: self._on_property_changed(prop_name, bool(s)))
            return widget
        
        elif prop_type == "integer":
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            widget.setValue(int(value) if value else 0)
            widget.valueChanged.connect(lambda v: self._on_property_changed(prop_name, v))
            return widget
        
        elif prop_type == "float":
            widget = QDoubleSpinBox()
            widget.setRange(-999999, 999999)
            widget.setValue(float(value) if value else 0.0)
            widget.valueChanged.connect(lambda v: self._on_property_changed(prop_name, v))
            return widget
        
        elif prop_type == "string":
            # Check if it's a select type
            if "options" in schema:
                widget = QComboBox()
                widget.addItems(schema["options"])
                if value in schema["options"]:
                    widget.setCurrentText(value)
                widget.currentTextChanged.connect(lambda t: self._on_property_changed(prop_name, t))
                return widget
            
            # Regular string - check if multi-line
            if schema.get("multiline", False):
                widget = FadeTextEdit()
                widget.setPlainText(str(value))
                widget.textChanged.connect(lambda: self._on_property_changed(prop_name, widget.toPlainText()))
                widget.setMaximumHeight(100)
                return widget
            
            widget = FadeLineEdit()
            widget.setText(str(value))
            widget.textChanged.connect(lambda t: self._on_property_changed(prop_name, t))
            return widget
        
        else:
            # Default to line edit
            widget = FadeLineEdit()
            widget.setText(str(value))
            widget.textChanged.connect(lambda t: self._on_property_changed(prop_name, t))
            return widget
    
    def _on_property_changed(self, prop_name: str, value: Any):
        """Handle property value change"""
        if self.current_component:
            if prop_name == "label":
                self.current_component.label = value
            else:
                self.current_component.properties[prop_name] = value
            self.property_changed.emit(self.current_component.id, prop_name, value)
    
    def clear(self):
        """Clear the property editor"""
        self.current_component = None
        self.current_definition = None
        self._show_empty_state()


# =============================================================================
# Workflow Canvas
# =============================================================================

class WorkflowCanvas(QGraphicsView):
    """Visual workflow canvas for arranging components"""
    
    component_selected = pyqtSignal(object)  # ComponentInstance
    component_moved = pyqtSignal(object, float, float)  # ComponentInstance, x, y
    component_double_clicked = pyqtSignal(object)  # ComponentInstance
    component_dropped = pyqtSignal(str, float, float)  # definition_id, x, y
    connection_created = pyqtSignal(object, object)  # Connection, success
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Configure view
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        # Scene settings
        self.scene.setSceneRect(-2000, -1500, 4000, 3000)
        self.scene.setBackgroundBrush(QBrush(QColor(45, 45, 48)))
        
        # Component management
        self.component_items: Dict[str, ComponentGraphicsItem] = {}
        self.connection_items: List[ConnectionGraphicsItem] = []
        
        # Interaction state
        self.drawing_connection = False
        self.connection_start: Optional[Tuple[ComponentGraphicsItem, bool]] = None
        self.connection_line: Optional[QGraphicsLineItem] = None
        
        # Selection
        self.current_selection: Optional[ComponentGraphicsItem] = None
        
        # Accept drops
        self.setAcceptDrops(True)
        
        # Grid
        self.show_grid = True
        self._draw_grid()
        
        # Connect signals
        self.scene.selectionChanged.connect(self._on_selection_changed)
    
    def _on_item_position_changed(self, item, change, value):
        """Handle item position changes - update connected lines"""
        if isinstance(item, ComponentGraphicsItem):
            # Update all connections connected to this component
            for conn_item in self.connection_items:
                if (conn_item.source_item == item or conn_item.target_item == item):
                    conn_item.update_positions()
    
    def _draw_grid(self):
        """Draw background grid"""
        if not self.show_grid:
            return
        
        # Grid is drawn in the background brush
        # For simplicity, we skip detailed grid drawing here
    
    def add_component(self, component: ComponentInstance, definition: ComponentDefinition) -> ComponentGraphicsItem:
        """Add a component to the canvas"""
        item = ComponentGraphicsItem(component, definition)
        item.setPos(component.x, component.y)
        
        self.scene.addItem(item)
        self.component_items[component.id] = item
        
        # Connect position change signal to update connections
        item.position_changed.connect(self._on_component_position_changed)
        
        return item
    
    def _on_component_position_changed(self, component_id: str):
        """Handle component position change - update connected lines"""
        # Look up the component item
        if component_id not in self.component_items:
            return
        item = self.component_items[component_id]
        
        # Update all connections connected to this component
        for conn_item in self.connection_items:
            if (conn_item.source_item == item or conn_item.target_item == item):
                conn_item.update_positions()
    
    def remove_component(self, component_id: str):
        """Remove a component from the canvas"""
        if component_id in self.component_items:
            item = self.component_items[component_id]
            
            # Remove associated connections
            self._remove_component_connections(component_id)
            
            self.scene.removeItem(item)
            del self.component_items[component_id]
    
    def _remove_component_connections(self, component_id: str):
        """Remove all connections involving a component"""
        to_remove = []
        for conn_item in self.connection_items:
            if (conn_item.connection.source_component_id == component_id or 
                conn_item.connection.target_component_id == component_id):
                to_remove.append(conn_item)
        
        for conn_item in to_remove:
            self.scene.removeItem(conn_item)
            self.connection_items.remove(conn_item)
    
    def add_connection(self, connection: Connection) -> Optional[ConnectionGraphicsItem]:
        """Add a connection to the canvas"""
        source_item = self.component_items.get(connection.source_component_id)
        target_item = self.component_items.get(connection.target_component_id)
        
        if not source_item or not target_item:
            return None
        
        item = ConnectionGraphicsItem(connection, source_item, target_item)
        self.scene.addItem(item)
        self.connection_items.append(item)
        
        # Update port connection status
        self._update_port_status(source_item, connection.source_port_id, False, True)
        self._update_port_status(target_item, connection.target_port_id, True, True)
        
        return item
    
    def remove_connection(self, connection_id: str):
        """Remove a connection from the canvas"""
        for conn_item in self.connection_items:
            if conn_item.connection.id == connection_id:
                # Update port status
                source_item = self.component_items.get(conn_item.connection.source_component_id)
                target_item = self.component_items.get(conn_item.connection.target_component_id)
                
                if source_item:
                    self._update_port_status(source_item, conn_item.connection.source_port_id, False, False)
                if target_item:
                    self._update_port_status(target_item, conn_item.connection.target_port_id, True, False)
                
                self.scene.removeItem(conn_item)
                self.connection_items.remove(conn_item)
                break
    
    def _update_port_status(self, item: ComponentGraphicsItem, port_id: str, is_input: bool, connected: bool):
        """Update port connection status"""
        ports = item.input_ports if is_input else item.output_ports
        for port in ports:
            if port.port_def.id == port_id:
                port.set_connected(connected)
                break
    
    def update_component_position(self, component_id: str, x: float, y: float):
        """Update component position"""
        if component_id in self.component_items:
            item = self.component_items[component_id]
            item.setPos(x, y)
            
            # Update connections
            for conn_item in self.connection_items:
                if (conn_item.source_item == item or conn_item.target_item == item):
                    conn_item.update_positions()
    
    def clear_canvas(self):
        """Clear all items from canvas"""
        self.scene.clear()
        self.component_items.clear()
        self.connection_items.clear()
    
    def _on_selection_changed(self):
        """Handle selection change"""
        selected = self.scene.selectedItems()
        
        if selected and isinstance(selected[0], ComponentGraphicsItem):
            item = selected[0]
            self.current_selection = item
            # Bring selected item to front
            item.setZValue(self.Z_SELECTION)
            self.component_selected.emit(item.component)
        else:
            # Reset z-values for previously selected items
            for item in self.component_items.values():
                item.setZValue(self.Z_COMPONENT)
            self.current_selection = None
            self.component_selected.emit(None)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press"""
        pos = self.mapToScene(event.pos())
        
        # Check if clicking on a port
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if we clicked on a component
            items = self.items(event.pos())
            for item in items:
                if isinstance(item, ComponentGraphicsItem):
                    port_info = item.get_port_at_position(pos)
                    if port_info:
                        port, is_input = port_info
                        self._start_connection_drawing(item, is_input, pos)
                        return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move"""
        if self.drawing_connection:
            pos = self.mapToScene(event.pos())
            if self.connection_line:
                line = self.connection_line.line()
                self.connection_line.setLine(line.x1(), line.y1(), pos.x(), pos.y())
            return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release"""
        if self.drawing_connection:
            self._finish_connection_drawing(event.pos())
            return
        
        super().mouseReleaseEvent(event)
    
    def _start_connection_drawing(self, item: ComponentGraphicsItem, is_input: bool, scene_pos: QPointF):
        """Start drawing a connection"""
        self.drawing_connection = True
        self.connection_start = (item, is_input)
        
        # Create temporary line
        port_pos = self._get_port_scene_pos(item, is_input)
        self.connection_line = self.scene.addLine(
            port_pos.x(), port_pos.y(), scene_pos.x(), scene_pos.y(),
            QPen(QColor(100, 100, 100), 2)
        )
    
    def _finish_connection_drawing(self, pos: QPointF):
        """Finish drawing a connection"""
        if not self.drawing_connection:
            return
        
        self.drawing_connection = False
        
        if self.connection_line:
            self.scene.removeItem(self.connection_line)
            self.connection_line = None
        
        # Check if we ended on a valid port
        scene_pos = self.mapToScene(pos)
        items = self.items(pos)
        
        target_item = None
        target_is_input = None
        
        for item in items:
            if isinstance(item, ComponentGraphicsItem):
                port_info = item.get_port_at_position(scene_pos)
                if port_info:
                    target_item, target_is_input = port_info
                    break
        
        if self.connection_start and target_item:
            source_item, source_is_input = self.connection_start
            
            # Validate connection
            if source_is_input != target_is_input:
                # Create connection
                from core.plugin_designer import Connection, uuid
                conn_id = str(uuid.uuid4())
                
                if source_is_input:
                    # Source is input, target is output - swap
                    connection = Connection(
                        id=conn_id,
                        source_component_id=target_item.component.id,
                        source_port_id=target_item.port_def.id if hasattr(target_item, 'port_def') else "",
                        target_component_id=source_item.component.id,
                        target_port_id=source_item.port_def.id if hasattr(source_item, 'port_def') else ""
                    )
                else:
                    connection = Connection(
                        id=conn_id,
                        source_component_id=source_item.component.id,
                        source_port_id="",  # Will be determined
                        target_component_id=target_item.component.id,
                        target_port_id=""
                    )
                
                # For now, just emit signal - actual connection creation handled by controller
                self.connection_created.emit(connection, True)
        
        self.connection_start = None
    
    def _get_port_scene_pos(self, item: ComponentGraphicsItem, is_input: bool) -> QPointF:
        """Get scene position for a port"""
        ports = item.input_ports if is_input else item.output_ports
        if ports:
            return ports[0].scenePos()
        return item.scenePos()
    
    def dragEnterEvent(self, event):
        """Handle drag enter"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            # Set drop indicator
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
    
    def dragMoveEvent(self, event):
        """Handle drag move"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave - restore cursor"""
        self.unsetCursor()
    
    def dropEvent(self, event):
        """Handle drop - add component to canvas"""
        self.unsetCursor()
        
        if event.mimeData().hasText():
            def_id = event.mimeData().text()
            
            # Get drop position in scene coordinates
            # Use mapToScene for proper coordinate transformation (handles zoom/pan)
            drop_pos = self.mapToScene(event.position().toPoint())
            
            # Log debug info
            logger.debug(f"Drop event: def_id={def_id}, widget_pos={event.position()}, scene_pos={drop_pos}")
            
            # Apply snapping to grid if enabled (optional)
            grid_size = 10
            snapped_x = round(drop_pos.x() / grid_size) * grid_size
            snapped_y = round(drop_pos.y() / grid_size) * grid_size
            
            # Emit signal to add component
            self.component_dropped.emit(def_id, snapped_x, snapped_y)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
    
    def wheelEvent(self, event):
        """Handle zoom with mouse wheel"""
        zoom_factor = 1.15
        
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1/zoom_factor, 1/zoom_factor)
    
    # ============================================================================
    # Debugging Methods
    # ============================================================================
    
    def debug_print_state(self):
        """Print debug information about the canvas state"""
        logger.debug(f"=== WorkflowCanvas Debug State ===")
        logger.debug(f"Components: {len(self.component_items)}")
        logger.debug(f"Connections: {len(self.connection_items)}")
        logger.debug(f"Zoom: {self.transform().m11():.2f}")
        logger.debug(f"Scene rect: {self.scene.sceneRect()}")
        
        for comp_id, item in self.component_items.items():
            logger.debug(f"  Component {comp_id}: pos=({item.x():.1f}, {item.y():.1f}), z={item.zValue()}")
    
    def debug_validate_drop_target(self, pos: QPointF) -> dict:
        """Validate and debug drop target position"""
        widget_pos = self.mapFromScene(pos)
        scene_pos = self.mapToScene(self.mapFromScene(pos))
        
        return {
            'scene_pos': (pos.x(), pos.y()),
            'widget_pos': (widget_pos.x(), widget_pos.y()),
            'mapped_scene_pos': (scene_pos.x(), scene_pos.y()),
            'transform': f"{self.transform().m11():.2f}"
        }


# =============================================================================
# Code Preview Panel
# =============================================================================

class CodePreviewPanel(QWidget):
    """Panel showing generated plugin code"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title = QLabel("Generated Code")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self._copy_code)
        toolbar.addWidget(self.copy_button)
        
        self.save_button = QPushButton("Save to File")
        self.save_button.clicked.connect(self._save_to_file)
        toolbar.addWidget(self.save_button)
        
        # Add syntax highlighting toggle
        self.highlight_checkbox = QCheckBox("Syntax Highlighting")
        self.highlight_checkbox.setChecked(True)
        self.highlight_checkbox.toggled.connect(self._toggle_highlighting)
        toolbar.addWidget(self.highlight_checkbox)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Code text edit
        self.code_edit = FadeTextEdit()
        self.code_edit.setReadOnly(True)
        self.code_edit.setFont(QFont("Courier New", 9))
        self.code_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
        """)
        layout.addWidget(self.code_edit)
        
        # Create Python syntax highlighter
        self.python_highlighter = PythonSyntaxHighlighter(self.code_edit.document())
    
    def _toggle_highlighting(self, enabled: bool):
        """Toggle syntax highlighting"""
        if enabled:
            # Re-apply the highlighter
            document = self.code_edit.document()
            self.python_highlighter.setDocument(document)
        else:
            # Clear highlighting by setting a null document
            self.python_highlighter.setDocument(None)
    
    def set_code(self, code: str):
        """Set the code to display"""
        self.code_edit.setPlainText(code)
    
    def _copy_code(self):
        """Copy code to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.code_edit.toPlainText())
    
    def _save_to_file(self):
        """Save code to file"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Plugin Code", "", "Python Files (*.py)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.code_edit.toPlainText())
            except Exception as e:
                logger.error(f"Failed to save code: {e}")


# =============================================================================
# Preview Panel
# =============================================================================

class PreviewPanel(QWidget):
    """Panel for previewing plugin interface"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preview_widget: Optional[QWidget] = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title = QLabel("Preview")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)
        
        # Preview area
        self.preview_area = QScrollArea()
        self.preview_area.setWidgetResizable(True)
        self.preview_area.setMinimumHeight(200)
        layout.addWidget(self.preview_area)
        
        # Placeholder
        placeholder = QLabel("Preview will show how your plugin UI elements will appear")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: gray; font-style: italic;")
        self.preview_area.setWidget(placeholder)
    
    def set_preview(self, components: List[ComponentInstance]):
        """Set preview based on components"""
        # Clear existing preview
        if self.preview_widget:
            self.preview_widget.deleteLater()
        
        # Create preview widget
        preview = QWidget()
        layout = QVBoxLayout(preview)
        
        # Preview UI elements
        for comp in components:
            if comp.definition_id == "menu_item":
                label = QLabel(f"[Menu] {comp.properties.get('item_text', 'Menu Item')}")
                label.setStyleSheet("padding: 5px; background: #4A90D9; color: white; border-radius: 3px;")
                layout.addWidget(label)
            
            elif comp.definition_id == "toolbar_button":
                label = QLabel(f"[Toolbar] {comp.properties.get('button_text', 'Button')}")
                label.setStyleSheet("padding: 5px; background: #5B90D9; color: white; border-radius: 3px;")
                layout.addWidget(label)
            
            elif comp.definition_id == "dialog":
                label = QLabel(f"[Dialog] {comp.properties.get('title', 'Dialog')}")
                label.setStyleSheet("padding: 5px; background: #6AA0D9; color: white; border-radius: 3px;")
                layout.addWidget(label)
        
        if not components:
            placeholder = QLabel("No UI components to preview")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: gray; font-style: italic;")
            layout.addWidget(placeholder)
        
        layout.addStretch()
        self.preview_widget = preview
        self.preview_area.setWidget(preview)


# =============================================================================
# Main Plugin Designer Window
# =============================================================================

class PluginDesignerWindow(QDialog):
    """Main plugin designer window"""
    
    def __init__(self, parent=None, existing_design: Optional[PluginDesign] = None):
        super().__init__(parent)
        
        self.design = existing_design or create_new_design("New Plugin")
        self.undo_manager = UndoRedoManager()
        
        self.setup_ui()
        self._update_title()
    
    def setup_ui(self):
        """Setup the UI"""
        self.setWindowTitle("Plugin Designer")
        self.setMinimumSize(1200, 800)
        
        # Main layout
        main_layout = QHBoxLayout(self)
        
        # Left panel - Palette and Templates
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Palette
        self.palette = ComponentPalette()
        left_layout.addWidget(self.palette, 2)
        
        # Templates
        self.templates = TemplatePanel()
        self.templates.template_selected.connect(self._on_template_selected)
        left_layout.addWidget(self.templates, 1)
        
        # Set width
        left_panel.setMaximumWidth(280)
        
        main_layout.addWidget(left_panel)
        
        # Center - Canvas and tabs
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = self._create_toolbar()
        center_layout.addWidget(toolbar)
        
        # Tab widget for canvas and code
        self.tabs = QTabWidget()
        
        # Canvas tab
        self.canvas = WorkflowCanvas()
        self.canvas.component_selected.connect(self._on_component_selected)
        self.canvas.component_double_clicked.connect(self._on_component_double_clicked)
        self.canvas.component_dropped.connect(self._on_component_dropped)
        self.tabs.addTab(self.canvas, "Design")
        
        # Code tab
        self.code_panel = CodePreviewPanel()
        self.tabs.addTab(self.code_panel, "Code")
        
        # Preview tab
        self.preview_panel = PreviewPanel()
        self.tabs.addTab(self.preview_panel, "Preview")
        
        center_layout.addWidget(self.tabs)
        
        main_layout.addWidget(center_widget, 1)
        
        # Right panel - Properties
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Properties
        self.property_editor = PropertyEditor()
        self.property_editor.property_changed.connect(self._on_property_changed)
        right_layout.addWidget(self.property_editor)
        
        # Validation results
        self.validation_group = QGroupBox("Validation")
        validation_layout = QVBoxLayout(self.validation_group)
        
        self.validation_label = QLabel("No errors")
        self.validation_label.setStyleSheet("color: green;")
        validation_layout.addWidget(self.validation_label)
        
        right_layout.addWidget(self.validation_group)
        
        # Set width
        right_panel.setMinimumWidth(280)
        
        main_layout.addWidget(right_panel)
        
        # Status bar
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
        # Load existing components
        self._load_components()
        
        # Update code
        self._update_code()
    
    def _create_toolbar(self) -> QWidget:
        """Create toolbar"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # New button
        new_btn = QPushButton("New")
        new_btn.clicked.connect(self._new_design)
        layout.addWidget(new_btn)
        
        # Open button
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self._open_design)
        layout.addWidget(open_btn)
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_design)
        layout.addWidget(save_btn)
        
        layout.addSpacing(20)
        
        # Undo/Redo
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.clicked.connect(self._undo)
        layout.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("Redo")
        self.redo_btn.clicked.connect(self._redo)
        layout.addWidget(self.redo_btn)
        
        layout.addSpacing(20)
        
        # Add component buttons
        add_btn = QPushButton("Add Component")
        add_btn.clicked.connect(self._show_add_component_menu)
        layout.addWidget(add_btn)
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_selected)
        layout.addWidget(delete_btn)
        
        # Validate button
        validate_btn = QPushButton("Validate")
        validate_btn.clicked.connect(self._validate_design)
        layout.addWidget(validate_btn)
        
        # Generate code button
        generate_btn = QPushButton("Generate Code")
        generate_btn.clicked.connect(self._update_code)
        layout.addWidget(generate_btn)
        
        layout.addStretch()
        
        # Export plugin button
        export_btn = QPushButton("Export Plugin")
        export_btn.setStyleSheet("background: #4A90D9; color: white; padding: 5px 15px;")
        export_btn.clicked.connect(self._export_plugin)
        layout.addWidget(export_btn)
        
        return toolbar
    
    def _update_title(self):
        """Update window title"""
        self.setWindowTitle(f"Plugin Designer - {self.design.name}")
    
    def _load_components(self):
        """Load components onto canvas"""
        for comp in self.design.components:
            definition = COMPONENT_DEFINITIONS.get(comp.definition_id)
            if definition:
                self.canvas.add_component(comp, definition)
    
    def _update_code(self):
        """Update generated code"""
        generator = CodeGenerator(self.design)
        code = generator.generate()
        self.code_panel.set_code(code)
        
        # Update preview
        ui_components = [c for c in self.design.components 
                        if c.definition_id in ["menu_item", "toolbar_button", "dialog"]]
        self.preview_panel.set_preview(ui_components)
    
    def _validate_design(self):
        """Validate the design"""
        valid, errors = self.design.validate()
        
        if valid:
            self.validation_label.setText("✓ Design is valid")
            self.validation_label.setStyleSheet("color: green;")
        else:
            error_text = "\n".join(f"• {e}" for e in errors)
            self.validation_label.setText(error_text)
            self.validation_label.setStyleSheet("color: red;")
    
    def _on_component_selected(self, component: Optional[ComponentInstance]):
        """Handle component selection"""
        if component:
            definition = COMPONENT_DEFINITIONS.get(component.definition_id)
            if definition:
                self.property_editor.set_component(component, definition)
        else:
            self.property_editor.clear()
    
    def _on_component_double_clicked(self, component: ComponentInstance):
        """Handle component double click"""
        # Could open a detailed editor
        pass
    
    def _on_component_dropped(self, definition_id: str, x: float, y: float):
        """Handle component dropped from palette"""
        definition = COMPONENT_DEFINITIONS.get(definition_id)
        if not definition:
            return
        
        from core.plugin_designer import ComponentInstance, uuid
        
        # Create new component
        component = ComponentInstance(
            id=str(uuid.uuid4()),
            definition_id=definition_id,
            x=x,
            y=y,
            width=definition.default_width,
            height=definition.default_height,
            label=definition.name,
            properties=definition.properties.copy()
        )
        
        # Record for undo
        action = DesignAction(
            action_type="add_component",
            data={"component_id": component.id, "component": {
                "id": component.id,
                "definition_id": component.definition_id,
                "x": component.x,
                "y": component.y,
                "width": component.width,
                "height": component.height,
                "label": component.label,
                "properties": component.properties
            }},
            inverse_data={"component_id": component.id}
        )
        self.undo_manager.push_action(action)
        
        # Add to design and canvas
        self.design.components.append(component)
        self.canvas.add_component(component, definition)
        
        # Update
        self._update_code()
        self._validate_design()
        self.status_label.setText(f"Added: {definition.name}")
    
    def _on_property_changed(self, component_id: str, prop_name: str, value: Any):
        """Handle property change"""
        # Record for undo
        component = self.design.get_component(component_id)
        if component:
            old_value = component.properties.get(prop_name)
            
            action = DesignAction(
                action_type="update_property",
                data={"component_id": component_id, "property": prop_name, "new_value": value},
                inverse_data={"component_id": component_id, "property": prop_name, "old_value": old_value}
            )
            self.undo_manager.push_action(action)
        
        # Update code
        self._update_code()
        
        # Validate
        self._validate_design()
    
    def _on_template_selected(self, template):
        """Handle template selection"""
        from core.plugin_designer import apply_template
        apply_template(template, self.design)
        
        # Reload canvas
        self.canvas.clear_canvas()
        self._load_components()
        
        self._update_code()
        self._validate_design()
        self._update_title()
    
    def _new_design(self):
        """Create new design"""
        self.design = create_new_design("New Plugin")
        self.canvas.clear_canvas()
        self.property_editor.clear()
        self._update_code()
        self._update_title()
        self.status_label.setText("New design created")
    
    def _open_design(self):
        """Open existing design"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Plugin Design", "", "Plugin Design Files (*.fdp)"
        )
        
        if file_path:
            design = import_design(Path(file_path))
            if design:
                self.design = design
                self.canvas.clear_canvas()
                self._load_components()
                self._update_code()
                self._validate_design()
                self._update_title()
                self.status_label.setText(f"Opened: {file_path}")
            else:
                self.status_label.setText("Failed to open design")
    
    def _save_design(self):
        """Save current design"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Plugin Design", f"{self.design.name}.fdp", "Plugin Design Files (*.fdp)"
        )
        
        if file_path:
            if export_design(self.design, Path(file_path)):
                self.status_label.setText(f"Saved: {file_path}")
            else:
                self.status_label.setText("Failed to save design")
    
    def _undo(self):
        """Undo last action"""
        if self.undo_manager.undo(self.design):
            # Reload canvas
            self.canvas.clear_canvas()
            self._load_components()
            self._update_code()
            self.status_label.setText("Undo")
    
    def _redo(self):
        """Redo last undone action"""
        if self.undo_manager.redo(self.design):
            # Reload canvas
            self.canvas.clear_canvas()
            self._load_components()
            self._update_code()
            self.status_label.setText("Redo")
    
    def _show_add_component_menu(self):
        """Show menu to add a component"""
        from PyQt6.QtWidgets import QMenu
        
        menu = QMenu(self)
        
        # Group by category
        for category in ComponentCategory:
            category_menu = menu.addMenu(category.name.replace("_", " "))
            
            for def_id, definition in COMPONENT_DEFINITIONS.items():
                if definition.category == category:
                    action = category_menu.addAction(definition.name)
                    action.triggered.connect(lambda checked, d=def_id: self._add_component(d))
        
        menu.exec_(self.mapToGlobal(self.sender().rect().center()))
    
    def _add_component(self, definition_id: str):
        """Add a component to the design"""
        definition = COMPONENT_DEFINITIONS.get(definition_id)
        if not definition:
            return
        
        from core.plugin_designer import ComponentInstance, uuid
        
        # Create new component
        component = ComponentInstance(
            id=str(uuid.uuid4()),
            definition_id=definition_id,
            x=100 + len(self.design.components) * 50,
            y=100 + len(self.design.components) * 30,
            width=definition.default_width,
            height=definition.default_height,
            label=definition.name,
            properties=definition.properties.copy()
        )
        
        # Record for undo
        action = DesignAction(
            action_type="add_component",
            data={"component_id": component.id, "component": {
                "id": component.id,
                "definition_id": component.definition_id,
                "x": component.x,
                "y": component.y,
                "width": component.width,
                "height": component.height,
                "label": component.label,
                "properties": component.properties
            }},
            inverse_data={"component_id": component.id}
        )
        self.undo_manager.push_action(action)
        
        # Add to design and canvas
        self.design.components.append(component)
        self.canvas.add_component(component, definition)
        
        # Update
        self._update_code()
        self._validate_design()
        self.status_label.setText(f"Added: {definition.name}")
    
    def _delete_selected(self):
        """Delete selected component"""
        selected = self.canvas.scene.selectedItems()
        if selected and isinstance(selected[0], ComponentGraphicsItem):
            item = selected[0]
            component_id = item.component.id
            
            # Record for undo
            action = DesignAction(
                action_type="remove_component",
                data={"component_id": component_id},
                inverse_data={"component_id": component_id, "component": {
                    "id": item.component.id,
                    "definition_id": item.component.definition_id,
                    "x": item.component.x,
                    "y": item.component.y,
                    "width": item.component.width,
                    "height": item.component.height,
                    "label": item.component.label,
                    "properties": item.component.properties
                }}
            )
            self.undo_manager.push_action(action)
            
            # Remove from design and canvas
            self.design.remove_component(component_id)
            self.canvas.remove_component(component_id)
            
            self.property_editor.clear()
            self._update_code()
            self._validate_design()
            self.status_label.setText("Component deleted")
    
    def _export_plugin(self):
        """Export as plugin file"""
        from PyQt6.QtWidgets import QFileDialog
        
        # Validate first
        valid, errors = self.design.validate()
        if not valid:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Validation Errors",
                "Please fix the following errors before exporting:\n\n" + "\n".join(errors)
            )
            return
        
        # Generate code
        generator = CodeGenerator(self.design)
        code = generator.generate()
        
        # Ask for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Plugin", f"{self.design.name}.py", "Python Files (*.py)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self, "Export Complete",
                    f"Plugin exported successfully to:\n{file_path}"
                )
                self.status_label.setText(f"Plugin exported: {file_path}")
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Export Error", f"Failed to export plugin:\n{str(e)}")


