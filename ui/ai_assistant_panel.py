"""
AI Assistant Panel - GUI Component for AI Dialogue Assistance

This module provides the AIAssistantPanel class which is a PyQt6-based panel
for interacting with the AI assistant. It integrates with the Fallout-themed
UI of the Fallout Dialogue Creator.

Location: ui/ai_assistant_panel.py
"""

import logging
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QPushButton, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QTextCursor

from .fallout_widgets import TerminalTextEdit, FadeLineEdit, FalloutButton
from core.ai_dialogue_manager import AIDialogueManager

logger = logging.getLogger(__name__)


class AIAssistantPanel(QWidget):
    """
    UI panel for AI dialogue assistance.
    
    This panel provides a chat interface for interacting with the AI assistant,
    as well as quick suggestions and configuration access.
    
    Signals:
        suggestion_clicked (str): Emitted when a suggestion is clicked
        config_requested (): Emitted when user requests config dialog
    """
    
    suggestion_clicked = pyqtSignal(str)  # Suggestion text
    config_requested = pyqtSignal()       # Request to open config
    create_dialogue_requested = pyqtSignal(dict)  # Dict with dialogue data
    create_node_requested = pyqtSignal(dict)    # Dict with node data
    
    def __init__(self, parent=None):
        """
        Initialize the AI Assistant Panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.ai_manager: Optional[AIDialogueManager] = None
        
        # UI Components
        self.status_indicator: Optional[QLabel] = None
        self.chat_view: Optional[TerminalTextEdit] = None
        self.input_field: Optional[FadeLineEdit] = None
        self.send_button: Optional[FalloutButton] = None
        self.suggestion_list: Optional[QListWidget] = None
        self.config_button: Optional[FalloutButton] = None
        self.clear_button: Optional[FalloutButton] = None
        
        # State
        self._is_processing = False
        self._conversation_started = False
        
        self._init_ui()
        self._connect_signals()
        
        logger.info("AI Assistant Panel initialized")
    
    def _init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Status bar at top
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_indicator = QLabel("● Offline")
        self.status_indicator.setStyleSheet("""
            color: #888;
            font-size: 11px;
        """)
        status_layout.addWidget(self.status_indicator)
        
        status_layout.addStretch()
        
        self.config_button = FalloutButton("⚙", self)
        self.config_button.setToolTip("AI Configuration")
        self.config_button.setFixedSize(28, 28)
        self.config_button.clicked.connect(self._on_config_clicked)
        status_layout.addWidget(self.config_button)
        
        main_layout.addLayout(status_layout)
        
        # Chat view (scrollable)
        self.chat_view = TerminalTextEdit(self)
        self.chat_view.setReadOnly(True)
        self.chat_view.setMaximumHeight(200)
        self.chat_view.setStyleSheet("""
            TerminalTextEdit {
                background-color: #0a0a0a;
                border: 1px solid #00ff00;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        main_layout.addWidget(self.chat_view)
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        self.input_field = FadeLineEdit("", self)
        self.input_field.setPlaceholderText("Type a message...")
        self.input_field.setStyleSheet("""
            FadeLineEdit {
                background-color: #1a1a1a;
                border: 1px solid #00ff00;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                padding: 4px 8px;
            }
            FadeLineEdit:focus {
                border: 2px solid #00ff00;
            }
            FadeLineEdit:disabled {
                color: #666;
                border-color: #444;
            }
        """)
        self.input_field.returnPressed.connect(self._on_send_message)
        input_layout.addWidget(self.input_field, 1)
        
        self.send_button = FalloutButton("Send", self)
        self.send_button.clicked.connect(self._on_send_message)
        self.send_button.setEnabled(False)
        input_layout.addWidget(self.send_button)
        
        main_layout.addLayout(input_layout)
        
        # Suggestions section
        suggestions_label = QLabel("Suggestions:", self)
        suggestions_label.setStyleSheet("""
            color: #888;
            font-size: 11px;
            font-weight: bold;
        """)
        main_layout.addWidget(suggestions_label)
        
        self.suggestion_list = QListWidget(self)
        self.suggestion_list.setMaximumHeight(80)
        self.suggestion_list.setStyleSheet("""
            QListWidget {
                background-color: #0a0a0a;
                border: 1px solid #444;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:selected {
                background-color: #003300;
                color: #00ff00;
            }
            QListWidget::item:hover {
                background-color: #001100;
            }
        """)
        self.suggestion_list.itemClicked.connect(self._on_suggestion_clicked)
        main_layout.addWidget(self.suggestion_list)
        
        # Bottom buttons
        bottom_layout = QHBoxLayout()
        
        self.clear_button = FalloutButton("Clear Chat", self)
        self.clear_button.clicked.connect(self._on_clear_clicked)
        bottom_layout.addWidget(self.clear_button)
        
        bottom_layout.addStretch()
        
        main_layout.addLayout(bottom_layout)
        
        # Set minimum width
        self.setMinimumWidth(280)
    
    def _connect_signals(self):
        """Connect internal signals"""
        # Connections will be made when ai_manager is set
    
    def set_ai_manager(self, ai_manager: AIDialogueManager):
        """
        Set the AI manager and connect signals.
        
        Args:
            ai_manager: The AIDialogueManager instance
        """
        self.ai_manager = ai_manager
        
        # Connect AI manager signals
        if self.ai_manager:
            self.ai_manager.response_ready.connect(self._on_ai_response)
            self.ai_manager.suggestion_ready.connect(self._on_ai_suggestions)
            self.ai_manager.progress_update.connect(self._on_progress)
            self.ai_manager.error_occurred.connect(self._on_ai_error)
            self.ai_manager.status_changed.connect(self._on_status_changed)
            
            # Initialize status display with current state
            if hasattr(self.ai_manager, 'status'):
                self._on_status_changed(self.ai_manager.status)
        
        logger.debug("AI manager connected to panel")
    
    def _on_send_message(self):
        """Handle send button click or Enter key"""
        if not self.ai_manager or not self.input_field.text():
            return

        message = self.input_field.text().strip()
        if not message:
            return

        # Add user message to chat
        self._add_message("You", message, is_user=True)
        self.input_field.clear()

        # Check for special commands to create dialogue
        cmd_lower = message.lower().strip()

        if cmd_lower.startswith("create dialogue") or cmd_lower.startswith("new dialogue"):
            # Extract topic
            topic = message.replace("create dialogue", "").replace("new dialogue", "").strip()
            if topic:
                self._create_dialogue_topic(topic)
                return

        elif cmd_lower.startswith("add node") or cmd_lower.startswith("add npc"):
            topic = message.replace("add node", "").replace("add npc", "").strip()
            if topic:
                self._create_node(topic)
                return

        elif cmd_lower.startswith("add option"):
            option = message.replace("add option", "").strip()
            if option:
                self._create_player_option(option)
                return

        # Send to AI for regular chat
        self._is_processing = True
        self._update_input_state()

        self.ai_manager.generate_response(message)

    def _create_dialogue_topic(self, topic: str):
        """Create a new dialogue about a topic"""
        self._add_message("AI", f"Creating dialogue about '{topic}'...", is_user=False)
        self._is_processing = False
        self._update_input_state()

        # Emit signal with topic
        self.create_dialogue_requested.emit({
            "action": "create_dialogue",
            "topic": topic
        })
        self._add_message("System", f"Created new dialogue: {topic}", is_user=False)

    def _create_node(self, npc_text: str):
        """Create a new NPC dialogue node"""
        self._add_message("AI", f"Adding NPC node: '{npc_text}'...", is_user=False)
        self._is_processing = False
        self._update_input_state()

        # Emit signal
        self.create_node_requested.emit({
            "action": "create_node",
            "npc_text": npc_text
        })
        self._add_message("System", f"Added NPC node: {npc_text}", is_user=False)

    def _create_player_option(self, option_text: str):
        """Create a player option for current node"""
        self._add_message("AI", f"Adding option: '{option_text}'...", is_user=False)
        self._is_processing = False
        self._update_input_state()

        self.create_node_requested.emit({
            "action": "add_option",
            "option_text": option_text
        })
        self._add_message("System", f"Added option: {option_text}", is_user=False)
        
        logger.debug(f"Sent message: {message[:50]}...")
    
    def _on_ai_response(self, response: str):
        """Handle AI response"""
        self._is_processing = False
        self._update_input_state()
        
        if response:
            self._add_message("AI", response, is_user=False)
    
    def _on_ai_suggestions(self, suggestions: List[str]):
        """Handle AI suggestions"""
        self.suggestion_list.clear()
        for suggestion in suggestions:
            self.suggestion_list.addItem(suggestion)
    
    def _on_progress(self, progress: int, status: str):
        """Handle progress updates"""
        # Could update a progress indicator
        logger.debug(f"AI Progress: {progress}% - {status}")
    
    def _on_ai_error(self, error: str):
        """Handle AI errors"""
        self._is_processing = False
        self._update_input_state()
        
        self._add_message("Error", error, is_user=False)
        logger.error(f"AI error: {error}")
    
    def _on_status_changed(self, status: str):
        """Handle status changes"""
        status_text = status.capitalize()
        color = "#00ff00"  # Green for ready
        
        if status == "processing":
            color = "#ffff00"  # Yellow
            status_text = "Processing..."
        elif status == "offline":
            color = "#ff6666"  # Red
            status_text = "Offline"
        elif status == "error":
            color = "#ff0000"  # Red
            status_text = "Error"
        
        self.status_indicator.setText(f"● {status_text}")
        self.status_indicator.setStyleSheet(f"""
            color: {color};
            font-size: 11px;
        """)
    
    def _on_suggestion_clicked(self, item):
        """Handle suggestion list click"""
        suggestion = item.text()
        self.suggestion_clicked.emit(suggestion)
        logger.debug(f"Suggestion clicked: {suggestion[:50]}...")
    
    def _on_config_clicked(self):
        """Handle config button click"""
        self.config_requested.emit()
    
    def _on_clear_clicked(self):
        """Handle clear button click"""
        self.chat_view.clear()
        self.suggestion_list.clear()
        self._conversation_started = False
    
    def _add_message(self, sender: str, message: str, is_user: bool):
        """
        Add a message to the chat view.
        
        Args:
            sender: Message sender name
            message: Message text
            is_user: Whether this is a user message
        """
        # Format based on sender
        if is_user:
            prefix = ">>> "
            color = "#00ff00"  # Green
        else:
            prefix = "<<< "
            color = "#00ccff"  # Cyan/blue
        
        # Append to chat
        cursor = self.chat_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Add sender
        cursor.insertText(f"\n{prefix}{sender}:\n")
        
        # Add message with wrapping
        cursor.insertText(f"   {message}\n")
        
        # Scroll to bottom
        self.chat_view.setTextCursor(cursor)
        self.chat_view.ensureCursorVisible()
    
    def _update_input_state(self):
        """Update input field and button enabled states"""
        has_input = bool(self.input_field.text())
        self.send_button.setEnabled(bool(self.ai_manager) and not self._is_processing)
        self.input_field.setEnabled(bool(self.ai_manager) and not self._is_processing)
        
        if self._is_processing:
            self.input_field.setPlaceholderText("Processing...")
        else:
            self.input_field.setPlaceholderText("Type a message...")
    
    def request_suggestions(self, node_text: str):
        """
        Request AI suggestions for a dialogue node.
        
        Args:
            node_text: The NPC dialogue node text
        """
        if self.ai_manager:
            self.ai_manager.suggest_dialogue_options(node_text)
    
    def request_sentiment_analysis(self, text: str):
        """
        Request sentiment analysis for text.
        
        Args:
            text: Text to analyze
        """
        if self.ai_manager:
            self.ai_manager.analyze_sentiment(text)
    
    def request_text_improvement(self, text: str, improvement_type: str = "grammar"):
        """
        Request text improvement.
        
        Args:
            text: Text to improve
            improvement_type: Type of improvement
        """
        if self.ai_manager:
            self.ai_manager.improve_text(text, improvement_type)
    
    def append_system_message(self, message: str):
        """
        Append a system message to the chat.
        
        Args:
            message: System message text
        """
        self._add_message("System", message, is_user=False)


# ============================================================================
# Factory function
# ============================================================================

def create_ai_panel(parent=None, ai_manager: Optional[AIDialogueManager] = None) -> AIAssistantPanel:
    """
    Factory function to create an AI Assistant Panel.
    
    Args:
        parent: Parent widget
        ai_manager: Optional AI manager
        
    Returns:
        AIAssistantPanel instance
    """
    panel = AIAssistantPanel(parent)
    if ai_manager:
        panel.set_ai_manager(ai_manager)
    return panel