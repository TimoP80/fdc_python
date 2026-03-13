"""
Plugin Designer Module for Fallout Dialogue Creator

This module provides a visual drag-and-drop interface for building plugins
with pre-built components, workflow canvas, property editors, and automatic
code generation.

Features:
- Component palette with UI elements, logic blocks, and service connectors
- Visual workflow canvas for arranging and connecting components
- Property editors for configuring component settings
- Preview mode for testing plugin interfaces
- Automatic code generation
- Validation system
- Template libraries
- Undo/redo functionality
- Export/import capabilities
"""

import json
import uuid
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# Component Types and Definitions
# =============================================================================

class ComponentCategory(Enum):
    """Categories of components available in the designer"""
    UI_ELEMENT = auto()
    LOGIC_BLOCK = auto()
    SERVICE_CONNECTOR = auto()
    DATA_PROCESSOR = auto()
    EVENT_HANDLER = auto()


class PortType(Enum):
    """Types of connection ports"""
    INPUT = auto()
    OUTPUT = auto()
    BIDIRECTIONAL = auto()


class DataType(Enum):
    """Data types for ports"""
    ANY = auto()
    VOID = auto()
    BOOLEAN = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    DIALOGUE = auto()
    NODE = auto()
    LIST = auto()
    DICT = auto()
    CALLABLE = auto()


@dataclass
class PortDefinition:
    """Definition of an input/output port on a component"""
    id: str
    name: str
    data_type: DataType
    port_type: PortType
    description: str = ""
    default_value: Any = None
    required: bool = False
    
    def is_compatible_with(self, other: 'PortDefinition') -> bool:
        """Check if this port can connect to another port"""
        if self.data_type == DataType.ANY or other.data_type == DataType.ANY:
            return True
        return self.data_type == other.data_type


@dataclass
class ComponentDefinition:
    """Definition of a component type available in the palette"""
    id: str
    name: str
    category: ComponentCategory
    description: str
    icon: str  # Icon name for UI
    color: str  # Hex color code
    
    input_ports: List[PortDefinition] = field(default_factory=list)
    output_ports: List[PortDefinition] = field(default_factory=list)
    
    properties: Dict[str, Any] = field(default_factory=dict)
    property_schema: Dict[str, Dict] = field(default_factory=dict)
    
    code_template: str = ""  # Template for code generation
    default_width: int = 120
    default_height: int = 60


# =============================================================================
# Component Instances on the Canvas
# =============================================================================

@dataclass
class ComponentInstance:
    """An instance of a component placed on the canvas"""
    id: str
    definition_id: str
    x: float
    y: float
    width: float
    height: float
    properties: Dict[str, Any]
    label: str = ""
    
    # Connections
    input_connections: List[str] = field(default_factory=list)  # IDs of connected components
    output_connections: List[str] = field(default_factory=list)  # IDs of connected components
    
    def get_input_port(self, port_id: str) -> Optional[PortDefinition]:
        """Get input port definition"""
        from core.plugin_designer import COMPONENT_DEFINITIONS
        if self.definition_id in COMPONENT_DEFINITIONS:
            for port in COMPONENT_DEFINITIONS[self.definition_id].input_ports:
                if port.id == port_id:
                    return port
        return None
    
    def get_output_port(self, port_id: str) -> Optional[PortDefinition]:
        """Get output port definition"""
        from core.plugin_designer import COMPONENT_DEFINITIONS
        if self.definition_id in COMPONENT_DEFINITIONS:
            for port in COMPONENT_DEFINITIONS[self.definition_id].output_ports:
                if port.id == port_id:
                    return port
        return None


@dataclass
class Connection:
    """A connection between two components"""
    id: str
    source_component_id: str
    source_port_id: str
    target_component_id: str
    target_port_id: str


# =============================================================================
# Plugin Design Project
# =============================================================================

@dataclass
class PluginDesign:
    """A complete plugin design project"""
    id: str
    name: str
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    plugin_type: str = "ui_extension"
    
    components: List[ComponentInstance] = field(default_factory=list)
    connections: List[Connection] = field(default_factory=list)
    
    canvas_width: float = 4000
    canvas_height: float = 3000
    canvas_zoom: float = 1.0
    canvas_offset_x: float = 0
    canvas_offset_y: float = 0
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_component(self, component_id: str) -> Optional[ComponentInstance]:
        """Get a component by ID"""
        for comp in self.components:
            if comp.id == component_id:
                return comp
        return None
    
    def remove_component(self, component_id: str) -> bool:
        """Remove a component and its connections"""
        # Remove all connections involving this component
        self.connections = [
            c for c in self.connections 
            if c.source_component_id != component_id and c.target_component_id != component_id
        ]
        # Remove the component
        self.components = [c for c in self.components if c.id != component_id]
        return True
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the design for errors"""
        errors = []
        
        # Check for components with no connections
        for comp in self.components:
            has_input = any(c.target_component_id == comp.id for c in self.connections)
            has_output = any(c.source_component_id == comp.id for c in self.connections)
            
            # Check required input ports
            from core.plugin_designer import COMPONENT_DEFINITIONS
            if comp.definition_id in COMPONENT_DEFINITIONS:
                defn = COMPONENT_DEFINITIONS[comp.definition_id]
                for port in defn.input_ports:
                    if port.required:
                        has_connection_to_port = any(
                            c.target_component_id == comp.id and c.target_port_id == port.id 
                            for c in self.connections
                        )
                        if not has_connection_to_port:
                            errors.append(f"Component '{comp.label or comp.definition_id}' requires input on port '{port.name}'")
        
        return len(errors) == 0, errors


# =============================================================================
# Component Palette - Pre-built Components
# =============================================================================

def _create_component_definitions() -> Dict[str, ComponentDefinition]:
    """Create all pre-built component definitions"""
    definitions = {}
    
    # ==========================================================================
    # UI Elements
    # ==========================================================================
    
    definitions["menu_item"] = ComponentDefinition(
        id="menu_item",
        name="Menu Item",
        category=ComponentCategory.UI_ELEMENT,
        description="Adds a menu item to the application menu bar",
        icon="menu",
        color="#4A90D9",
        input_ports=[
            PortDefinition("on_click", "On Click", DataType.CALLABLE, PortType.INPUT, "Handler when item is clicked")
        ],
        output_ports=[
            PortDefinition("clicked", "Clicked", DataType.VOID, PortType.OUTPUT, "Signal when clicked")
        ],
        properties={
            "menu_path": "Tools",
            "item_text": "New Item",
            "shortcut": "",
            "separator": False
        },
        property_schema={
            "menu_path": {"type": "string", "label": "Menu Path", "description": "Path to menu (e.g., 'Tools/File')"},
            "item_text": {"type": "string", "label": "Item Text", "description": "Text displayed in menu"},
            "shortcut": {"type": "string", "label": "Shortcut", "description": "Keyboard shortcut (e.g., 'Ctrl+S')"},
            "separator": {"type": "boolean", "label": "Separator", "description": "Add separator before item"}
        },
        code_template='self.menu_action = menu_path.addAction("item_text")\n# Add shortcut if specified'
    )
    
    definitions["toolbar_button"] = ComponentDefinition(
        id="toolbar_button",
        name="Toolbar Button",
        category=ComponentCategory.UI_ELEMENT,
        description="Adds a button to the application toolbar",
        icon="toolbar",
        color="#5B90D9",
        input_ports=[
            PortDefinition("on_click", "On Click", DataType.CALLABLE, PortType.INPUT, "Handler when button is clicked")
        ],
        output_ports=[],
        properties={
            "toolbar_name": "main",
            "button_text": "",
            "icon": "",
            "tooltip": "",
            "checkable": False
        },
        property_schema={
            "toolbar_name": {"type": "string", "label": "Toolbar Name", "description": "Name of toolbar to add to"},
            "button_text": {"type": "string", "label": "Text", "description": "Button text"},
            "icon": {"type": "string", "label": "Icon", "description": "Icon path or name"},
            "tooltip": {"type": "string", "label": "Tooltip", "description": "Tooltip text"},
            "checkable": {"type": "boolean", "label": "Checkable", "description": "Button can be toggled"}
        },
        code_template='toolbar_action = toolbar_name.addAction("button_text")'
    )
    
    definitions["dialog"] = ComponentDefinition(
        id="dialog",
        name="Dialog Window",
        category=ComponentCategory.UI_ELEMENT,
        description="Creates a modal or modeless dialog window",
        icon="window",
        color="#6AA0D9",
        input_ports=[
            PortDefinition("on_show", "On Show", DataType.CALLABLE, PortType.INPUT, "Handler when dialog is shown"),
            PortDefinition("on_close", "On Close", DataType.CALLABLE, PortType.INPUT, "Handler when dialog is closed")
        ],
        output_ports=[
            PortDefinition("shown", "Shown", DataType.VOID, PortType.OUTPUT, "Signal when dialog is shown"),
            PortDefinition("closed", "Closed", DataType.VOID, PortType.OUTPUT, "Signal when dialog is closed")
        ],
        properties={
            "title": "Dialog",
            "width": 400,
            "height": 300,
            "modal": True,
            "resizable": True
        },
        property_schema={
            "title": {"type": "string", "label": "Title", "description": "Dialog window title"},
            "width": {"type": "integer", "label": "Width", "description": "Dialog width in pixels"},
            "height": {"type": "integer", "label": "Height", "description": "Dialog height in pixels"},
            "modal": {"type": "boolean", "label": "Modal", "description": "Show as modal dialog"},
            "resizable": {"type": "boolean", "label": "Resizable", "description": "Allow resizing"}
        },
        code_template='class ClassName(QDialog):\n    def __init__(self, parent=None):\n        super().__init__(parent)\n        self.setWindowTitle("title")'
    )
    
    definitions["widget"] = ComponentDefinition(
        id="widget",
        name="Custom Widget",
        category=ComponentCategory.UI_ELEMENT,
        description="Creates a custom Qt widget",
        icon="widget",
        color="#7AB0D9",
        input_ports=[],
        output_ports=[],
        properties={
            "class_name": "CustomWidget",
            "base_class": "QWidget",
            "width": 200,
            "height": 150
        },
        property_schema={
            "class_name": {"type": "string", "label": "Class Name", "description": "Python class name"},
            "base_class": {"type": "string", "label": "Base Class", "description": "Qt base class (QWidget, QFrame, etc.)"},
            "width": {"type": "integer", "label": "Width", "description": "Default width"},
            "height": {"type": "integer", "label": "Height", "description": "Default height"}
        },
        code_template='class ClassName(BaseClass):\n    def __init__(self, parent=None):\n        super().__init__(parent)\n        self.setMinimumSize(width, height)'
    )
    
    # ==========================================================================
    # Logic Blocks
    # ==========================================================================
    
    definitions["condition"] = ComponentDefinition(
        id="condition",
        name="Condition",
        category=ComponentCategory.LOGIC_BLOCK,
        description="Conditional branching based on a boolean expression",
        icon="branch",
        color="#D94A4A",
        input_ports=[
            PortDefinition("condition", "Condition", DataType.BOOLEAN, PortType.INPUT, "Boolean condition to evaluate", required=True)
        ],
        output_ports=[
            PortDefinition("true", "True", DataType.ANY, PortType.OUTPUT, "Output when condition is true"),
            PortDefinition("false", "False", DataType.ANY, PortType.OUTPUT, "Output when condition is false")
        ],
        properties={
            "expression": "",
            "operator": "==",
            "compare_value": ""
        },
        property_schema={
            "expression": {"type": "string", "label": "Expression", "description": "Python expression to evaluate"},
            "operator": {"type": "string", "label": "Operator", "description": "Comparison operator"},
            "compare_value": {"type": "string", "label": "Compare Value", "description": "Value to compare against"}
        },
        code_template='if condition:\n    # True branch\n    pass\nelse:\n    # False branch\n    pass'
    )
    
    definitions["loop"] = ComponentDefinition(
        id="loop",
        name="Loop",
        category=ComponentCategory.LOGIC_BLOCK,
        description="Iterates over a collection or repeats a certain number of times",
        icon="loop",
        color="#D96A4A",
        input_ports=[
            PortDefinition("iterable", "Iterable", DataType.LIST, PortType.INPUT, "Collection to iterate over"),
            PortDefinition("on_iteration", "On Iteration", DataType.CALLABLE, PortType.INPUT, "Called for each iteration")
        ],
        output_ports=[
            PortDefinition("item", "Item", DataType.ANY, PortType.OUTPUT, "Current item in iteration"),
            PortDefinition("index", "Index", DataType.INTEGER, PortType.OUTPUT, "Current index"),
            PortDefinition("complete", "Complete", DataType.VOID, PortType.OUTPUT, "Signal when loop completes")
        ],
        properties={
            "iterable_expression": "",
            "max_iterations": 10,
            "loop_type": "for"  # for, while
        },
        property_schema={
            "iterable_expression": {"type": "string", "label": "Iterable", "description": "Expression that returns a collection"},
            "max_iterations": {"type": "integer", "label": "Max Iterations", "description": "Maximum number of iterations"},
            "loop_type": {"type": "string", "label": "Loop Type", "description": "Type of loop (for/while)"}
        },
        code_template='for item in iterable_expression:\n    # Process item\n    pass'
    )
    
    definitions["function"] = ComponentDefinition(
        id="function",
        name="Function",
        category=ComponentCategory.LOGIC_BLOCK,
        description="Defines a reusable function",
        icon="function",
        color="#D98A4A",
        input_ports=[],
        output_ports=[
            PortDefinition("result", "Result", DataType.ANY, PortType.OUTPUT, "Function return value")
        ],
        properties={
            "function_name": "my_function",
            "parameters": "",
            "return_type": "None",
            "body": ""
        },
        property_schema={
            "function_name": {"type": "string", "label": "Function Name", "description": "Name of the function"},
            "parameters": {"type": "string", "label": "Parameters", "description": "Function parameters (e.g., 'self, value')"},
            "return_type": {"type": "string", "label": "Return Type", "description": "Return type annotation"},
            "body": {"type": "string", "label": "Body", "description": "Function body code"}
        },
        code_template='def function_name(parameters):\n    # Function body\n    pass'
    )
    
    definitions["variable"] = ComponentDefinition(
        id="variable",
        name="Variable",
        category=ComponentCategory.LOGIC_BLOCK,
        description="Stores and manages a variable value",
        icon="variable",
        color="#D9A04A",
        input_ports=[
            PortDefinition("set_value", "Set Value", DataType.ANY, PortType.INPUT, "New value to set")
        ],
        output_ports=[
            PortDefinition("value", "Value", DataType.ANY, PortType.OUTPUT, "Current value"),
            PortDefinition("changed", "Changed", DataType.ANY, PortType.OUTPUT, "Signal when value changes")
        ],
        properties={
            "variable_name": "my_variable",
            "default_value": "",
            "data_type": "any"
        },
        property_schema={
            "variable_name": {"type": "string", "label": "Variable Name", "description": "Name of the variable"},
            "default_value": {"type": "string", "label": "Default Value", "description": "Initial value"},
            "data_type": {"type": "string", "label": "Data Type", "description": "Type of the variable"}
        },
        code_template='self.variable_name = default_value'
    )
    
    # ==========================================================================
    # Service Connectors
    # ==========================================================================
    
    definitions["dialogue_hook"] = ComponentDefinition(
        id="dialogue_hook",
        name="Dialogue Hook",
        category=ComponentCategory.SERVICE_CONNECTOR,
        description="Responds to dialogue events",
        icon="hook",
        color="#4AD94A",
        input_ports=[],
        output_ports=[
            PortDefinition("dialogue", "Dialogue", DataType.DIALOGUE, PortType.OUTPUT, "The dialogue object")
        ],
        properties={
            "hook_type": "dialogue_loaded",  # dialogue_loaded, dialogue_saved, dialogue_modified
            "handler_name": "on_dialogue_event"
        },
        property_schema={
            "hook_type": {"type": "string", "label": "Hook Type", "description": "Type of dialogue event to listen for"},
            "handler_name": {"type": "string", "label": "Handler Name", "description": "Name of handler method"}
        },
        code_template='def on_dialogue_event(self, dialogue):\n    """Handle dialogue loaded event"""\n    pass'
    )
    
    definitions["node_hook"] = ComponentDefinition(
        id="node_hook",
        name="Node Hook",
        category=ComponentCategory.SERVICE_CONNECTOR,
        description="Responds to dialogue node events",
        icon="node",
        color="#5AD95A",
        input_ports=[],
        output_ports=[
            PortDefinition("node", "Node", DataType.NODE, PortType.OUTPUT, "The node object")
        ],
        properties={
            "hook_type": "node_created",  # node_created, node_modified, node_deleted
            "handler_name": "on_node_event"
        },
        property_schema={
            "hook_type": {"type": "string", "label": "Hook Type", "description": "Type of node event to listen for"},
            "handler_name": {"type": "string", "label": "Handler Name", "description": "Name of handler method"}
        },
        code_template='def on_node_event(self, node):\n    """Handle node created event"""\n    pass'
    )
    
    definitions["service_call"] = ComponentDefinition(
        id="service_call",
        name="Service Call",
        category=ComponentCategory.SERVICE_CONNECTOR,
        description="Calls an application service",
        icon="service",
        color="#4AD9D9",
        input_ports=[
            PortDefinition("input", "Input", DataType.ANY, PortType.INPUT, "Input data")
        ],
        output_ports=[
            PortDefinition("output", "Output", DataType.ANY, PortType.OUTPUT, "Service response")
        ],
        properties={
            "service_name": "",
            "method_name": "",
            "parameters": ""
        },
        property_schema={
            "service_name": {"type": "string", "label": "Service Name", "description": "Name of service to call"},
            "method_name": {"type": "string", "label": "Method Name", "description": "Method to call"},
            "parameters": {"type": "string", "label": "Parameters", "description": "Additional parameters"}
        },
        code_template='result = self.plugin_manager.call_service("service_name", "method_name")'
    )
    
    definitions["api_endpoint"] = ComponentDefinition(
        id="api_endpoint",
        name="API Endpoint",
        category=ComponentCategory.SERVICE_CONNECTOR,
        description="Exposes an HTTP API endpoint",
        icon="api",
        color="#4A8AD9",
        input_ports=[
            PortDefinition("request", "Request", DataType.DICT, PortType.INPUT, "HTTP request data")
        ],
        output_ports=[
            PortDefinition("response", "Response", DataType.DICT, PortType.OUTPUT, "HTTP response")
        ],
        properties={
            "path": "/api/endpoint",
            "method": "GET",  # GET, POST, PUT, DELETE
            "handler_name": "handle_api_request"
        },
        property_schema={
            "path": {"type": "string", "label": "Path", "description": "API endpoint path"},
            "method": {"type": "string", "label": "Method", "description": "HTTP method"},
            "handler_name": {"type": "string", "label": "Handler", "description": "Request handler method"}
        },
        code_template='def handle_api_request(self, request):\n    """Handle API request"""\n    return {"status": "success"}'
    )
    
    # ==========================================================================
    # Data Processors
    # ==========================================================================
    
    definitions["transform"] = ComponentDefinition(
        id="transform",
        name="Data Transform",
        category=ComponentCategory.DATA_PROCESSOR,
        description="Transforms input data using a function",
        icon="transform",
        color="#9A4AD9",
        input_ports=[
            PortDefinition("input", "Input", DataType.ANY, PortType.INPUT, "Input data", required=True)
        ],
        output_ports=[
            PortDefinition("output", "Output", DataType.ANY, PortType.OUTPUT, "Transformed output")
        ],
        properties={
            "transform_expression": "",
            "output_type": "any"
        },
        property_schema={
            "transform_expression": {"type": "string", "label": "Expression", "description": "Python expression to transform input"},
            "output_type": {"type": "string", "label": "Output Type", "description": "Expected output type"}
        },
        code_template='# Transform data\nresult = transform_expression'
    )
    
    definitions["filter"] = ComponentDefinition(
        id="filter",
        name="Filter",
        category=ComponentCategory.DATA_PROCESSOR,
        description="Filters data based on a condition",
        icon="filter",
        color="#8A4AD9",
        input_ports=[
            PortDefinition("input", "Input", DataType.LIST, PortType.INPUT, "Input list", required=True)
        ],
        output_ports=[
            PortDefinition("output", "Output", DataType.LIST, PortType.OUTPUT, "Filtered list")
        ],
        properties={
            "filter_expression": "item",
            "condition": ""
        },
        property_schema={
            "filter_expression": {"type": "string", "label": "Item Variable", "description": "Variable name for each item"},
            "condition": {"type": "string", "label": "Condition", "description": "Filter condition (e.g., 'item.active')"}
        },
        code_template='result = [item for item in input_data if condition]'
    )
    
    definitions["aggregator"] = ComponentDefinition(
        id="aggregator",
        name="Aggregator",
        category=ComponentCategory.DATA_PROCESSOR,
        description="Aggregates data (sum, count, average, etc.)",
        icon="aggregate",
        color="#7A4AD9",
        input_ports=[
            PortDefinition("input", "Input", DataType.LIST, PortType.INPUT, "Input list", required=True)
        ],
        output_ports=[
            PortDefinition("output", "Output", DataType.ANY, PortType.OUTPUT, "Aggregated result")
        ],
        properties={
            "aggregation_type": "sum",  # sum, count, average, min, max
            "key_expression": ""
        },
        property_schema={
            "aggregation_type": {"type": "string", "label": "Type", "description": "Aggregation type (sum, count, avg, min, max)"},
            "key_expression": {"type": "string", "label": "Key", "description": "Expression to extract key for aggregation"}
        },
        code_template='result = sum(input_data)'
    )
    
    # ==========================================================================
    # Event Handlers
    # ==========================================================================
    
    definitions["startup_handler"] = ComponentDefinition(
        id="startup_handler",
        name="Startup Handler",
        category=ComponentCategory.EVENT_HANDLER,
        description="Handles application startup event",
        icon="startup",
        color="#D9D94A",
        input_ports=[],
        output_ports=[
            PortDefinition("app", "App", DataType.ANY, PortType.OUTPUT, "Application instance")
        ],
        properties={
            "handler_name": "on_app_startup"
        },
        property_schema={
            "handler_name": {"type": "string", "label": "Handler Name", "description": "Name of handler method"}
        },
        code_template='def on_app_startup(self, app):\n    """Called when the application starts"""\n    pass'
    )
    
    definitions["shutdown_handler"] = ComponentDefinition(
        id="shutdown_handler",
        name="Shutdown Handler",
        category=ComponentCategory.EVENT_HANDLER,
        description="Handles application shutdown event",
        icon="shutdown",
        color="#D9C94A",
        input_ports=[],
        output_ports=[],
        properties={
            "handler_name": "on_app_shutdown"
        },
        property_schema={
            "handler_name": {"type": "string", "label": "Handler Name", "description": "Name of handler method"}
        },
        code_template='def on_app_shutdown(self):\n    """Called when the application shuts down"""\n    pass'
    )
    
    return definitions


# Global component definitions
COMPONENT_DEFINITIONS = _create_component_definitions()


# =============================================================================
# Template Library
# =============================================================================

@dataclass
class PluginTemplate:
    """A template for creating new plugins"""
    id: str
    name: str
    description: str
    category: str
    components: List[Dict]  # Initial components to add
    connections: List[Dict]  # Initial connections
    preview_image: str = ""


def get_template_library() -> List[PluginTemplate]:
    """Get the library of plugin templates"""
    return [
        PluginTemplate(
            id="basic_menu",
            name="Basic Menu Plugin",
            description="Adds a simple menu item with functionality",
            category="UI",
            components=[
                {"definition_id": "menu_item", "x": 100, "y": 100, "label": "Menu Item", "properties": {"item_text": "My Action"}},
                {"definition_id": "startup_handler", "x": 100, "y": 250, "label": "On Startup"}
            ],
            connections=[]
        ),
        PluginTemplate(
            id="dialog_processor",
            name="Dialogue Processor",
            description="Processes dialogue data when loaded",
            category="Dialogue",
            components=[
                {"definition_id": "dialogue_hook", "x": 100, "y": 100, "label": "On Dialogue Loaded", "properties": {"hook_type": "dialogue_loaded"}},
                {"definition_id": "transform", "x": 300, "y": 100, "label": "Process", "properties": {"transform_expression": "dialogue.npcname.upper()"}},
                {"definition_id": "variable", "x": 500, "y": 100, "label": "Store Result", "properties": {"variable_name": "current_npc"}}
            ],
            connections=[
                {"source": 0, "source_port": "dialogue", "target": 1, "target_port": "input"},
                {"source": 1, "source_port": "output", "target": 2, "target_port": "set_value"}
            ]
        ),
        PluginTemplate(
            id="export_extension",
            name="Export Extension",
            description="Adds custom export functionality",
            category="Export",
            components=[
                {"definition_id": "menu_item", "x": 100, "y": 100, "label": "Export", "properties": {"menu_path": "File", "item_text": "Export Custom..."}},
                {"definition_id": "dialog", "x": 300, "y": 100, "label": "Export Dialog", "properties": {"title": "Export", "width": 500, "height": 400}},
                {"definition_id": "dialogue_hook", "x": 100, "y": 250, "label": "Get Dialogue", "properties": {"hook_type": "dialogue_loaded"}}
            ],
            connections=[]
        ),
        PluginTemplate(
            id="node_validator",
            name="Node Validator",
            description="Validates dialogue nodes on creation",
            category="Validation",
            components=[
                {"definition_id": "node_hook", "x": 100, "y": 100, "label": "On Node Created", "properties": {"hook_type": "node_created"}},
                {"definition_id": "condition", "x": 300, "y": 100, "label": "Check Valid"},
                {"definition_id": "variable", "x": 500, "y": 50, "label": "Error Count", "properties": {"variable_name": "validation_errors", "default_value": "0"}}
            ],
            connections=[
                {"source": 0, "source_port": "node", "target": 1, "target_port": "condition"}
            ]
        ),
        PluginTemplate(
            id="batch_processor",
            name="Batch Dialogue Processor",
            description="Process multiple dialogues in batch",
            category="Processing",
            components=[
                {"definition_id": "menu_item", "x": 100, "y": 50, "label": "Batch Process", "properties": {"item_text": "Batch Process"}},
                {"definition_id": "loop", "x": 300, "y": 50, "label": "Process All", "properties": {"iterable_expression": "dialogues", "loop_type": "for"}},
                {"definition_id": "dialogue_hook", "x": 100, "y": 200, "label": "Load Dialogue", "properties": {"hook_type": "dialogue_loaded"}},
                {"definition_id": "aggregator", "x": 500, "y": 50, "label": "Count", "properties": {"aggregation_type": "count"}}
            ],
            connections=[]
        )
    ]


# =============================================================================
# Code Generator
# =============================================================================

class CodeGenerator:
    """Generates plugin code from a design"""
    
    def __init__(self, design: PluginDesign):
        self.design = design
    
    def generate(self) -> str:
        """Generate complete plugin code"""
        code_parts = []
        
        # Header
        code_parts.append(self._generate_header())
        
        # Imports
        code_parts.append(self._generate_imports())
        
        # Plugin class
        code_parts.append(self._generate_plugin_class())
        
        return '\n\n'.join(code_parts)
    
    def _generate_header(self) -> str:
        return f'''"""
Plugin: {self.design.name}

Version: {self.design.version}
Author: {self.design.author}
Description: {self.design.description}

Generated by Plugin Designer
"""
'''
    
    def _generate_imports(self) -> str:
        return '''from core.plugin_system import PluginInterface, PluginType, PluginHooks, PluginInfo
from PyQt6.QtWidgets import QDialog, QWidget, QVBoxLayout, QMenu, QAction
from PyQt6.QtGui import QIcon, QKeySequence
from PyQt6.QtCore import pyqtSignal
import logging

logger = logging.getLogger(__name__)
'''
    
    def _generate_plugin_class(self) -> str:
        lines = []
        
        # Class definition
        class_name = self._sanitize_class_name(self.design.name)
        lines.append(f"class {class_name}(PluginInterface):")
        lines.append(f'    """Plugin generated from design: {self.design.name}"""')
        lines.append("")
        lines.append("    def __init__(self):")
        lines.append("        super().__init__()")
        lines.append(f'        self.plugin_info = PluginInfo(')
        lines.append(f'            name="{self.design.name}",')
        lines.append(f'            version="{self.design.version}",')
        lines.append(f'            description="{self.design.description}",')
        lines.append(f'            author="{self.design.author}",')
        lines.append(f'            plugin_type=PluginType.{self._get_plugin_type_enum(self.design.plugin_type)}')
        lines.append('        )')
        
        # Add instance variables
        for comp in self.design.components:
            if comp.definition_id == "variable":
                var_name = comp.properties.get("variable_name", "var")
                default = comp.properties.get("default_value", "None")
                lines.append(f"        self.{var_name} = {default}")
        
        lines.append("")
        lines.append("    def initialize(self, plugin_manager):")
        lines.append('        """Initialize the plugin"""')
        lines.append(f'        logger.info("Initializing {self.design.name}")')
        lines.append("        return True")
        lines.append("")
        lines.append("    def activate(self):")
        lines.append('        """Activate the plugin"""')
        lines.append(f'        logger.info("Activating {self.design.name}")')
        lines.append("        return True")
        lines.append("")
        lines.append("    def deactivate(self):")
        lines.append('        """Deactivate the plugin"""')
        lines.append(f'        logger.info("Deactivating {self.design.name}")')
        lines.append("        return True")
        lines.append("")
        
        # Generate hooks
        hooks_code = self._generate_hooks()
        if hooks_code:
            lines.append(hooks_code)
        
        # Generate handler methods for components
        handlers_code = self._generate_handlers()
        if handlers_code:
            lines.append(handlers_code)
        
        # Get hooks method
        lines.append("")
        lines.append("    def get_hooks(self):")
        lines.append('        """Return hook functions"""')
        hooks_dict = self._generate_hooks_dict()
        lines.append(f"        return {hooks_dict}")
        
        return '\n'.join(lines)
    
    def _generate_hooks(self) -> str:
        """Generate hook handler methods"""
        lines = []
        
        for comp in self.design.components:
            if comp.definition_id == "dialogue_hook":
                handler_name = comp.properties.get("handler_name", "on_dialogue_event")
                hook_type = comp.properties.get("hook_type", "dialogue_loaded")
                lines.append(f"    def {handler_name}(self, dialogue):")
                lines.append(f'        """Handle {hook_type} event"""')
                lines.append(f'        logger.info(f"Dialogue event: {hook_type}")')
                lines.append(f'        # Process dialogue here')
                lines.append("        pass")
                lines.append("")
            
            elif comp.definition_id == "node_hook":
                handler_name = comp.properties.get("handler_name", "on_node_event")
                hook_type = comp.properties.get("hook_type", "node_created")
                lines.append(f"    def {handler_name}(self, node):")
                lines.append(f'        """Handle {hook_type} event"""')
                lines.append(f'        logger.info(f"Node event: {hook_type}")')
                lines.append(f'        # Process node here')
                lines.append("        pass")
                lines.append("")
            
            elif comp.definition_id == "menu_item":
                handler_name = comp.properties.get("handler_name", "on_menu_item_clicked")
                lines.append(f"    def {handler_name}(self):")
                lines.append('        """Handle menu item click"""')
                lines.append('        # Add your functionality here')
                lines.append("        pass")
                lines.append("")
            
            elif comp.definition_id == "startup_handler":
                handler_name = comp.properties.get("handler_name", "on_app_startup")
                lines.append(f"    def {handler_name}(self, app):")
                lines.append('        """Handle application startup"""')
                lines.append(f'        logger.info("Application started")')
                lines.append("        pass")
                lines.append("")
            
            elif comp.definition_id == "shutdown_handler":
                handler_name = comp.properties.get("handler_name", "on_app_shutdown")
                lines.append(f"    def {handler_name}(self):")
                lines.append('        """Handle application shutdown"""')
                lines.append(f'        logger.info("Application shutting down")')
                lines.append("        pass")
                lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_handlers(self) -> str:
        """Generate additional handler methods"""
        lines = []
        
        # Generate dialog classes for dialog components
        for comp in self.design.components:
            if comp.definition_id == "dialog":
                class_name = comp.properties.get("class_name", "CustomDialog")
                title = comp.properties.get("title", "Dialog")
                width = comp.properties.get("width", 400)
                height = comp.properties.get("height", 300)
                modal = comp.properties.get("modal", True)
                resizable = comp.properties.get("resizable", True)
                
                lines.append(f"class {class_name}(QDialog):")
                lines.append(f'    """Custom dialog generated from design"""')
                lines.append("")
                lines.append("    def __init__(self, parent=None):")
                lines.append("        super().__init__(parent)")
                lines.append(f'        self.setWindowTitle("{title}")')
                lines.append(f"        self.setMinimumSize({width}, {height})")
                if not resizable:
                    lines.append(f"        self.setFixedSize({width}, {height})")
                if modal:
                    lines.append("        self.setModal(True)")
                lines.append("        self.setup_ui()")
                lines.append("")
                lines.append("    def setup_ui(self):")
                lines.append("        layout = QVBoxLayout(self)")
                lines.append("        # Add your UI elements here")
                lines.append("        self.setLayout(layout)")
                lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_hooks_dict(self) -> str:
        """Generate the hooks dictionary"""
        hook_mappings = []
        
        for comp in self.design.components:
            if comp.definition_id == "dialogue_hook":
                hook_type = comp.properties.get("hook_type", "dialogue_loaded")
                handler_name = comp.properties.get("handler_name", "on_dialogue_event")
                hook_enum = self._get_hook_enum(hook_type)
                hook_mappings.append(f"            PluginHooks.{hook_enum}: [self.{handler_name}]")
            
            elif comp.definition_id == "node_hook":
                hook_type = comp.properties.get("hook_type", "node_created")
                handler_name = comp.properties.get("handler_name", "on_node_event")
                hook_enum = self._get_hook_enum(hook_type)
                hook_mappings.append(f"            PluginHooks.{hook_enum}: [self.{handler_name}]")
            
            elif comp.definition_id == "startup_handler":
                handler_name = comp.properties.get("handler_name", "on_app_startup")
                hook_mappings.append(f"            PluginHooks.APP_STARTUP: [self.{handler_name}]")
            
            elif comp.definition_id == "shutdown_handler":
                handler_name = comp.properties.get("handler_name", "on_app_shutdown")
                hook_mappings.append(f"            PluginHooks.APP_SHUTDOWN: [self.{handler_name}]")
        
        if hook_mappings:
            return "{\n" + ",\n".join(hook_mappings) + "\n        }"
        else:
            return "{}"
    
    def _get_plugin_type_enum(self, plugin_type: str) -> str:
        """Convert plugin type string to enum"""
        mapping = {
            "ui_extension": "UI_EXTENSION",
            "dialogue_processor": "DIALOGUE_PROCESSOR",
            "parser_extension": "PARSER_EXTENSION",
            "scripting_extension": "SCRIPTING_EXTENSION",
            "testing_extension": "TESTING_EXTENSION",
            "export_extension": "EXPORT_EXTENSION"
        }
        return mapping.get(plugin_type, "UI_EXTENSION")
    
    def _get_hook_enum(self, hook_type: str) -> str:
        """Convert hook type string to enum"""
        mapping = {
            "dialogue_loaded": "DIALOGUE_LOADED",
            "dialogue_saved": "DIALOGUE_SAVED",
            "dialogue_modified": "DIALOGUE_MODIFIED",
            "node_created": "NODE_CREATED",
            "node_modified": "NODE_MODIFIED",
            "node_deleted": "NODE_DELETED"
        }
        return mapping.get(hook_type, hook_type.upper())
    
    def _sanitize_class_name(self, name: str) -> str:
        """Sanitize name to be a valid Python class name"""
        # Remove special characters and capitalize words
        import re
        name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        return ''.join(word.capitalize() for word in name.split()) + 'Plugin'


# =============================================================================
# Undo/Redo System
# =============================================================================

@dataclass
class DesignAction:
    """An action that can be undone/redone"""
    action_type: str
    data: Dict[str, Any]
    inverse_data: Dict[str, Any]


class UndoRedoManager:
    """Manages undo/redo operations for the designer"""
    
    def __init__(self, max_history: int = 50):
        self.undo_stack: List[DesignAction] = []
        self.redo_stack: List[DesignAction] = []
        self.max_history = max_history
    
    def push_action(self, action: DesignAction):
        """Push a new action to the undo stack"""
        self.undo_stack.append(action)
        self.redo_stack.clear()  # Clear redo stack on new action
        
        # Limit history size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
    
    def undo(self, design: PluginDesign) -> bool:
        """Undo the last action"""
        if not self.undo_stack:
            return False
        
        action = self.undo_stack.pop()
        
        # Apply inverse action
        if action.action_type == "add_component":
            design.components = [c for c in design.components if c.id != action.data["component_id"]]
        
        elif action.action_type == "remove_component":
            comp_data = action.inverse_data["component"]
            comp = ComponentInstance(**comp_data)
            design.components.append(comp)
        
        elif action.action_type == "move_component":
            for comp in design.components:
                if comp.id == action.data["component_id"]:
                    comp.x = action.inverse_data["x"]
                    comp.y = action.inverse_data["y"]
                    break
        
        elif action.action_type == "update_property":
            for comp in design.components:
                if comp.id == action.data["component_id"]:
                    comp.properties[action.data["property"]] = action.inverse_data["old_value"]
                    break
        
        elif action.action_type == "add_connection":
            design.connections = [c for c in design.connections if c.id != action.data["connection_id"]]
        
        elif action.action_type == "remove_connection":
            conn_data = action.inverse_data["connection"]
            conn = Connection(**conn_data)
            design.connections.append(conn)
        
        self.redo_stack.append(action)
        return True
    
    def redo(self, design: PluginDesign) -> bool:
        """Redo the last undone action"""
        if not self.redo_stack:
            return False
        
        action = self.redo_stack.pop()
        
        # Apply action
        if action.action_type == "add_component":
            comp_data = action.data["component"]
            comp = ComponentInstance(**comp_data)
            design.components.append(comp)
        
        elif action.action_type == "remove_component":
            design.components = [c for c in design.components if c.id != action.data["component_id"]]
        
        elif action.action_type == "move_component":
            for comp in design.components:
                if comp.id == action.data["component_id"]:
                    comp.x = action.data["x"]
                    comp.y = action.data["y"]
                    break
        
        elif action.action_type == "update_property":
            for comp in design.components:
                if comp.id == action.data["component_id"]:
                    comp.properties[action.data["property"]] = action.data["new_value"]
                    break
        
        elif action.action_type == "add_connection":
            conn_data = action.data["connection"]
            conn = Connection(**conn_data)
            design.connections.append(conn)
        
        elif action.action_type == "remove_connection":
            design.connections = [c for c in design.connections if c.id != action.data["connection_id"]]
        
        self.undo_stack.append(action)
        return True
    
    def can_undo(self) -> bool:
        """Check if undo is available"""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available"""
        return len(self.redo_stack) > 0
    
    def clear(self):
        """Clear all history"""
        self.undo_stack.clear()
        self.redo_stack.clear()


# =============================================================================
# Import/Export Functions
# =============================================================================

def export_design(design: PluginDesign, file_path: Path) -> bool:
    """Export a design to a JSON file"""
    try:
        data = {
            "id": design.id,
            "name": design.name,
            "version": design.version,
            "author": design.author,
            "description": design.description,
            "plugin_type": design.plugin_type,
            "canvas": {
                "width": design.canvas_width,
                "height": design.canvas_height,
                "zoom": design.canvas_zoom,
                "offset_x": design.canvas_offset_x,
                "offset_y": design.canvas_offset_y
            },
            "components": [
                {
                    "id": c.id,
                    "definition_id": c.definition_id,
                    "x": c.x,
                    "y": c.y,
                    "width": c.width,
                    "height": c.height,
                    "label": c.label,
                    "properties": c.properties
                }
                for c in design.components
            ],
            "connections": [
                {
                    "id": c.id,
                    "source_component_id": c.source_component_id,
                    "source_port_id": c.source_port_id,
                    "target_component_id": c.target_component_id,
                    "target_port_id": c.target_port_id
                }
                for c in design.connections
            ],
            "metadata": design.metadata
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to export design: {e}")
        return False


def import_design(file_path: Path) -> Optional[PluginDesign]:
    """Import a design from a JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        design = PluginDesign(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Imported Plugin"),
            version=data.get("version", "1.0.0"),
            author=data.get("author", ""),
            description=data.get("description", ""),
            plugin_type=data.get("plugin_type", "ui_extension"),
            canvas_width=data.get("canvas", {}).get("width", 4000),
            canvas_height=data.get("canvas", {}).get("height", 3000),
            canvas_zoom=data.get("canvas", {}).get("zoom", 1.0),
            canvas_offset_x=data.get("canvas", {}).get("offset_x", 0),
            canvas_offset_y=data.get("canvas", {}).get("offset_y", 0),
            metadata=data.get("metadata", {})
        )
        
        # Load components
        for comp_data in data.get("components", []):
            comp = ComponentInstance(
                id=comp_data["id"],
                definition_id=comp_data["definition_id"],
                x=comp_data["x"],
                y=comp_data["y"],
                width=comp_data.get("width", 120),
                height=comp_data.get("height", 60),
                label=comp_data.get("label", ""),
                properties=comp_data.get("properties", {})
            )
            design.components.append(comp)
        
        # Load connections
        for conn_data in data.get("connections", []):
            conn = Connection(
                id=conn_data["id"],
                source_component_id=conn_data["source_component_id"],
                source_port_id=conn_data["source_port_id"],
                target_component_id=conn_data["target_component_id"],
                target_port_id=conn_data["target_port_id"]
            )
            design.connections.append(conn)
        
        return design
    
    except Exception as e:
        logger.error(f"Failed to import design: {e}")
        return None


def create_new_design(name: str = "New Plugin") -> PluginDesign:
    """Create a new empty design"""
    return PluginDesign(
        id=str(uuid.uuid4()),
        name=name,
        version="1.0.0",
        author="",
        description="",
        plugin_type="ui_extension"
    )


def apply_template(template: PluginTemplate, design: PluginDesign) -> PluginDesign:
    """Apply a template to a design"""
    design.name = template.name
    design.description = template.description
    
    # Add components from template
    id_mapping = {}  # Map template indices to actual IDs
    
    for i, comp_data in enumerate(template.components):
        comp = ComponentInstance(
            id=str(uuid.uuid4()),
            definition_id=comp_data["definition_id"],
            x=comp_data.get("x", 100 + i * 150),
            y=comp_data.get("y", 100),
            width=120,
            height=60,
            label=comp_data.get("label", ""),
            properties=comp_data.get("properties", {})
        )
        design.components.append(comp)
        id_mapping[i] = comp.id
    
    # Add connections from template
    for conn_data in template.connections:
        conn = Connection(
            id=str(uuid.uuid4()),
            source_component_id=id_mapping.get(conn_data["source"]),
            source_port_id=conn_data["source_port"],
            target_component_id=id_mapping.get(conn_data["target"]),
            target_port_id=conn_data["target_port"]
        )
        design.connections.append(conn)
    
    return design
