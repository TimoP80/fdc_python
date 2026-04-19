"""
AI Configuration Dialog - Settings for AI Dialogue System

This module provides the AIConfigurationDialog class for configuring
AI provider settings, model selection, creativity parameters, and persona.

Location: ui/ai_config_dialog.py
"""

import asyncio
import aiohttp
import logging
from typing import Optional, List

from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QSlider, QLineEdit, QPushButton,
    QGroupBox, QCheckBox, QTabWidget, QWidget, QFormLayout,
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIntValidator

from core.ai_dialogue_system import (
    ResponseCreativity, ResponseLength, FormalityTone
)
from core.ai_dialogue_manager import AIDialogueManager
from core.settings import Settings
from core.ollama_provider import OllamaCloudModel
from core.gemini_provider import GeminiModel

logger = logging.getLogger(__name__)


class AIConfigurationDialog(QDialog):
    """
    Dialog for configuring AI parameters.
    
    Allows configuration of:
    - Model selection (Ollama/Gemini/Custom)
    - Creativity level (slider)
    - Response length preferences
    - Persona configuration
    - API endpoints and keys
    """
    
    # Signal emitted when settings are applied
    settings_applied = pyqtSignal(dict)
    
    def __init__(
        self,
        ai_manager: Optional[AIDialogueManager] = None,
        settings: Optional[Settings] = None,
        parent=None
    ):
        """
        Initialize the AI Configuration Dialog.
        
        Args:
            ai_manager: The AIDialogueManager instance
            settings: The Settings instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.ai_manager = ai_manager
        self.settings = settings
        
        # Current settings
        self._settings = {
            "provider": "ollama",
            "model": "llama3.2:3b",
            "endpoint": "http://localhost:11434",
            "api_key": "",
            "creativity": "BALANCED",
            "length": "NORMAL",
            "formality": "NEUTRAL",
            "persona_name": "Assistant",
            "persona_traits": "helpful,friendly",
            "persona_style": "neutral",
            "suggestions_enabled": True,
            "sentiment_enabled": True,
            "improvement_enabled": True,
            "translation_enabled": False
        }
        
        self._init_ui()
        self._load_current_settings()
        
        logger.info("AI Configuration Dialog initialized")
    
    def _init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("AI Configuration")
        self.setMinimumSize(500, 450)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Tab widget for organized settings
        tab_widget = QTabWidget()
        
        # Tab 1: Provider Settings
        tab_widget.addTab(self._create_provider_tab(), "Provider")
        
        # Tab 2: Response Settings
        tab_widget.addTab(self._create_response_tab(), "Response")
        
        # Tab 3: Persona Settings
        tab_widget.addTab(self._create_persona_tab(), "Persona")
        
        # Tab 4: Features
        tab_widget.addTab(self._create_features_tab(), "Features")
        
        main_layout.addWidget(tab_widget)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Cancel
        )
        
        button_box.accepted.connect(self._on_accept)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)
        button_box.rejected.connect(self.reject)
        
        main_layout.addWidget(button_box)
    
    def _create_provider_tab(self) -> QWidget:
        """Create the provider settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Provider selection
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["ollama_cloud", "gemini", "ollama"])
        self.provider_combo.setCurrentText(self._settings["provider"])
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        layout.addRow("Provider:", self.provider_combo)
        
        # Model selection
        self.model_combo = QComboBox()
        self._on_provider_changed(self.provider_combo.currentText())
        self.model_combo.setCurrentText(self._settings["model"])
        layout.addRow("Model:", self.model_combo)
        
        # Endpoint
        self.endpoint_edit = QLineEdit(self._settings["endpoint"])
        layout.addRow("Endpoint:", self.endpoint_edit)
        
        # API Key
        self.api_key_edit = QLineEdit(self._settings["api_key"])
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("API Key:", self.api_key_edit)
        
        # Test connection button
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self._on_test_connection)
        layout.addRow("", test_btn)
        
        return widget
    
    def _create_response_tab(self) -> QWidget:
        """Create the response settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Creativity group
        creativity_group = QGroupBox("Creativity Level")
        creativity_layout = QVBoxLayout(creativity_group)
        
        self.creativity_slider = QSlider(Qt.Orientation.Horizontal)
        self.creativity_slider.setMinimum(0)
        self.creativity_slider.setMaximum(3)
        self.creativity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.creativity_slider.setTickInterval(1)
        
        creativity_labels = {
            0: "Precise (Most deterministic)",
            1: "Balanced (Default)",
            2: "Creative (More varied)",
            3: "Unconstrained (Maximum creativity)"
        }
        
        # Map setting to slider value
        creativity_map = {
            "PRECISE": 0,
            "BALANCED": 1,
            "CREATIVE": 2,
            "UNCONSTRAINED": 3
        }
        self.creativity_slider.setValue(creativity_map.get(self._settings["creativity"], 1))
        
        creativity_layout.addWidget(self.creativity_slider)
        
        # Labels for slider
        labels_layout = QHBoxLayout()
        for v, label in creativity_labels.items():
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 10px; color: #888;")
            labels_layout.addWidget(lbl)
        creativity_layout.addLayout(labels_layout)
        
        layout.addWidget(creativity_group)
        
        # Length group
        length_group = QGroupBox("Response Length")
        length_layout = QHBoxLayout(length_group)
        
        self.length_combo = QComboBox()
        self.length_combo.addItems(["Concise", "Normal", "Detailed", "Extended"])
        
        length_map = {
            "CONCISE": 0,
            "NORMAL": 1,
            "DETAILED": 2,
            "EXTENDED": 3
        }
        self.length_combo.setCurrentIndex(length_map.get(self._settings["length"], 1))
        
        length_layout.addWidget(self.length_combo)
        
        layout.addWidget(length_group)
        
        # Formality group
        formality_group = QGroupBox("Formality Tone")
        formality_layout = QHBoxLayout(formality_group)
        
        self.formality_combo = QComboBox()
        self.formality_combo.addItems(["Casual", "Neutral", "Formal", "Ceremonial"])
        
        formality_map = {
            "CASUAL": 0,
            "NEUTRAL": 1,
            "FORMAL": 2,
            "CEREMONIAL": 3
        }
        self.formality_combo.setCurrentIndex(formality_map.get(self._settings["formality"], 1))
        
        formality_layout.addWidget(self.formality_combo)
        
        layout.addWidget(formality_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_persona_tab(self) -> QWidget:
        """Create the persona settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Persona name
        self.persona_name_edit = QLineEdit(self._settings["persona_name"])
        layout.addRow("Name:", self.persona_name_edit)
        
        # Persona traits
        self.persona_traits_edit = QLineEdit(self._settings["persona_traits"])
        self.persona_traits_edit.setPlaceholderText("Comma-separated traits")
        layout.addRow("Traits:", self.persona_traits_edit)
        
        # Speaking style
        self.persona_style_combo = QComboBox()
        self.persona_style_combo.addItems([
            "neutral", "friendly", "formal", 
            "casual", "authoritative", "playful"
        ])
        self.persona_style_combo.setCurrentText(self._settings["persona_style"])
        layout.addRow("Style:", self.persona_style_combo)
        
        # Preset personas
        presets_group = QGroupBox("Preset Personas")
        presets_layout = QHBoxLayout(presets_group)
        
        preset_btn1 = QPushButton("Helpful Assistant")
        preset_btn1.clicked.connect(lambda: self._load_preset("helpful"))
        presets_layout.addWidget(preset_btn1)
        
        preset_btn2 = QPushButton("Game NPC")
        preset_btn2.clicked.connect(lambda: self._load_preset("npc"))
        presets_layout.addWidget(preset_btn2)
        
        preset_btn3 = QPushButton("Wasteland Guide")
        preset_btn3.clicked.connect(lambda: self._load_preset("wasteland"))
        presets_layout.addWidget(preset_btn3)
        
        layout.addRow("", presets_group)
        
        return widget
    
    def _create_features_tab(self) -> QWidget:
        """Create the features settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Feature toggles
        self.suggestions_check = QCheckBox("Enable dialogue suggestions")
        self.suggestions_check.setChecked(self._settings["suggestions_enabled"])
        layout.addWidget(self.suggestions_check)
        
        self.sentiment_check = QCheckBox("Enable sentiment analysis")
        self.sentiment_check.setChecked(self._settings["sentiment_enabled"])
        layout.addWidget(self.sentiment_check)
        
        self.improvement_check = QCheckBox("Enable text improvement")
        self.improvement_check.setChecked(self._settings["improvement_enabled"])
        layout.addWidget(self.improvement_check)
        
        self.translation_check = QCheckBox("Enable translation")
        self.translation_check.setChecked(self._settings["translation_enabled"])
        layout.addWidget(self.translation_check)
        
        layout.addStretch()
        
        return widget
    
    def _load_current_settings(self):
        """Load current settings from Settings object"""
        if self.settings:
            # Load AI provider settings
            self._settings["provider"] = self.settings.get_ai_provider()
            
            # Load API keys - try both provider types to handle migration
            self._settings["api_key"] = self.settings.get_ollama_cloud_api_key()
            if not self._settings["api_key"]:
                self._settings["api_key"] = self.settings.get_gemini_api_key()
            
            # Load model
            self._settings["model"] = self.settings.get_ollama_cloud_model()
            if not self._settings["model"]:
                self._settings["model"] = self.settings.get_gemini_model()
            
            # Load endpoint
            self._settings["endpoint"] = self.settings.get('ai_endpoint', 'http://localhost:11434')
            
            # Load creativity settings
            creativity = self.settings.get('ai_creativity', 'BALANCED')
            self._settings["creativity"] = creativity
            
            length = self.settings.get('ai_response_length', 'NORMAL')
            self._settings["length"] = length
            
            formality = self.settings.get('ai_formality', 'NEUTRAL')
            self._settings["formality"] = formality
            
            # Update UI components with loaded values
            self.provider_combo.setCurrentText(self._settings["provider"])
            self.model_combo.setCurrentText(self._settings["model"])
            self.endpoint_edit.setText(self._settings["endpoint"])
            self.api_key_edit.setText(self._settings["api_key"])
    
    def _load_preset(self, preset: str):
        """Load a preset persona configuration"""
        presets = {
            "helpful": {
                "name": "Helpful Assistant",
                "traits": "helpful,friendly,knowledgeable",
                "style": "friendly"
            },
            "npc": {
                "name": "NPC Character",
                "traits": "character,immersive,roleplay",
                "style": "neutral"
            },
            "wasteland": {
                "name": "Wasteland Guide",
                "traits": "survivalist,wary,experienced",
                "style": "casual"
            }
        }
        
        if preset in presets:
            p = presets[preset]
            self.persona_name_edit.setText(p["name"])
            self.persona_traits_edit.setText(p["traits"])
            self.persona_style_combo.setCurrentText(p["style"])
    
    def _on_provider_changed(self, provider: str):
        """Update model combo based on provider"""
        self.model_combo.clear()
        if provider == "ollama_cloud":
            self.model_combo.addItems([m.value for m in OllamaCloudModel])
        elif provider == "gemini":
            self.model_combo.addItems([m.value for m in GeminiModel])
        elif provider == "ollama":
            # Local Ollama might have any model, but we can provide some defaults
            self.model_combo.addItems(["llama3.2:3b", "llama3.2:1b", "gemma3:latest", "phi4:latest"])
        
        # Try to restore previous selection if valid for new provider
        if self._settings.get("model") in [self.model_combo.itemText(i) for i in range(self.model_combo.count())]:
            self.model_combo.setCurrentText(self._settings["model"])

    def _on_test_connection(self):
        """Test the connection to the AI provider"""
        provider = self.provider_combo.currentText()
        endpoint = self.endpoint_edit.text()
        api_key = self.api_key_edit.text()
        model = self.model_combo.currentText()
        
        # Disable button during test
        test_btn = self.sender()
        test_btn.setEnabled(False)
        test_btn.setText("Testing...")
        
        try:
            # Run test in asyncio
            result = asyncio.run(self._test_connection_async(provider, endpoint, api_key, model))
            
            if result["success"]:
                QMessageBox.information(
                    self,
                    "Connection Test Successful",
                    f"Successfully connected to {provider}!\n\n{result.get('message', '')}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Connection Test Failed",
                    f"Failed to connect to {provider}.\n\nError: {result.get('error', 'Unknown error')}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Test Error",
                f"An error occurred during testing:\n\n{str(e)}"
            )
        finally:
            # Re-enable button
            test_btn.setEnabled(True)
            test_btn.setText("Test Connection")
    
    async def _test_connection_async(self, provider: str, endpoint: str, api_key: str, model: str) -> dict:
        """Async connection test"""
        try:
            if provider == "ollama":
                return await self._test_ollama_connection(endpoint)
            elif provider == "ollama_cloud":
                return await self._test_ollama_cloud_connection(api_key, model)
            elif provider == "gemini":
                return await self._test_gemini_connection(api_key, model)
            else:
                return {"success": False, "error": f"Unknown provider: {provider}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_ollama_connection(self, endpoint: str) -> dict:
        """Test local Ollama connection"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test basic connectivity
                async with session.get(f"{endpoint}/api/tags", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get("models", [])
                        return {
                            "success": True,
                            "message": f"Connected successfully!\nFound {len(models)} model(s) available."
                        }
                    else:
                        return {"success": False, "error": f"HTTP {response.status}"}
        except aiohttp.ClientError as e:
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}
    
    async def _test_ollama_cloud_connection(self, api_key: str, model: str) -> dict:
        """Test Ollama Cloud connection per docs: https://docs.ollama.com/cloud"""
        if not api_key:
            return {"success": False, "error": "API key is required"}
        
        try:
            async with aiohttp.ClientSession() as session:
                # List cloud models using the documented endpoint
                headers = {"Authorization": f"Bearer {api_key}"}
                async with session.get(
                    "https://ollama.com/api/tags",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get("models", [])
                        cloud_models = [m for m in models if str(m.get("name", "")).endswith("-cloud")]
                        return {
                            "success": True,
                            "message": (
                                f"API key validated!\n"
                                f"Found {len(cloud_models)} cloud model(s) available."
                            )
                        }
                    elif response.status == 401:
                        return {"success": False, "error": "Invalid API key (401 Unauthorized)"}
                    elif response.status == 403:
                        return {"success": False, "error": "Access forbidden — check key permissions (403)"}
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"HTTP {response.status}: {error_text[:200]}"}
        except aiohttp.ClientError as e:
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}
    
    async def _test_gemini_connection(self, api_key: str, model: str) -> dict:
        """Test Gemini connection"""
        if not api_key:
            return {"success": False, "error": "API key is required"}
        
        try:
            from core.gemini_provider import GeminiConfig, GeminiClient
            
            config = GeminiConfig(api_key=api_key)
            client = GeminiClient(config)
            
            # Test with a simple request
            response = await client.generate("Hello", max_tokens=10)
            
            if response and len(response.strip()) > 0:
                return {
                    "success": True,
                    "message": "API key validated successfully!\nResponse received from Gemini."
                }
            else:
                return {"success": False, "error": "Empty response from API"}
                
        except Exception as e:
            error_msg = str(e)
            if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
                return {"success": False, "error": "Invalid API key"}
            elif "quota" in error_msg.lower():
                return {"success": False, "error": "Quota exceeded"}
            else:
                return {"success": False, "error": f"Connection error: {error_msg}"}
    
    def _on_accept(self):
        """Handle OK button click"""
        self._apply_settings()
        self.accept()
    
    def _on_apply(self):
        """Handle Apply button click"""
        self._apply_settings()
    
    def _apply_settings(self):
        """Apply the current settings"""
        # Gather settings from UI
        self._settings = {
            "provider": self.provider_combo.currentText(),
            "model": self.model_combo.currentText(),
            "endpoint": self.endpoint_edit.text(),
            "api_key": self.api_key_edit.text(),
            "creativity": self.creativity_slider.value(),
            "length": self.length_combo.currentIndex(),
            "formality": self.formality_combo.currentIndex(),
            "persona_name": self.persona_name_edit.text(),
            "persona_traits": self.persona_traits_edit.text(),
            "persona_style": self.persona_style_combo.currentText(),
            "suggestions_enabled": self.suggestions_check.isChecked(),
            "sentiment_enabled": self.sentiment_check.isChecked(),
            "improvement_enabled": self.improvement_check.isChecked(),
            "translation_enabled": self.translation_check.isChecked()
        }

        # Map slider value to setting name
        creativity_values = ["PRECISE", "BALANCED", "CREATIVE", "UNCONSTRAINED"]
        self._settings["creativity"] = creativity_values[self.creativity_slider.value()]

        length_values = ["CONCISE", "NORMAL", "DETAILED", "EXTENDED"]
        self._settings["length"] = length_values[self.length_combo.currentIndex()]

        formality_values = ["CASUAL", "NEUTRAL", "FORMAL", "CEREMONIAL"]
        self._settings["formality"] = formality_values[self.formality_combo.currentIndex()]

        # Save to Settings object for persistence
        if self.settings:
            provider = self._settings["provider"]
            api_key = self._settings["api_key"]
            model = self._settings["model"]

            # Save provider type
            self.settings.set_ai_provider(provider)

            # Save API key based on provider type
            if provider == "gemini":
                self.settings.set_gemini_api_key(api_key)
                self.settings.set_gemini_model(model)
            elif provider == "ollama_cloud":
                self.settings.set_ollama_cloud_api_key(api_key)
                self.settings.set_ollama_cloud_model(model)
            elif provider == "ollama":
                self.settings.set('ai_endpoint', self._settings["endpoint"])

            # Save creativity settings
            self.settings.set('ai_creativity', self._settings["creativity"])
            self.settings.set('ai_response_length', self._settings["length"])
            self.settings.set('ai_formality', self._settings["formality"])

            logger.info(f"AI settings saved: provider={provider}, model={model}")

        # Emit settings applied signal
        self.settings_applied.emit(self._settings)

        # Apply to AI manager if available
        if self.ai_manager:
            self._apply_to_ai_manager()

        logger.info("AI settings applied")
    
    def _apply_to_ai_manager(self):
        """Apply settings to the AI manager"""
        if self.ai_manager:
            self.ai_manager.reload_provider()
    
    def get_settings(self) -> dict:
        """Get the current settings dictionary"""
        return self._settings.copy()


# ============================================================================
# Factory function
# ============================================================================

def create_ai_config_dialog(
    ai_manager: Optional[AIDialogueManager] = None,
    settings: Optional[Settings] = None,
    parent=None
) -> AIConfigurationDialog:
    """
    Factory function to create an AI Configuration Dialog.
    
    Args:
        ai_manager: Optional AI manager
        settings: Optional Settings instance
        parent: Parent widget
        
    Returns:
        AIConfigurationDialog instance
    """
    return AIConfigurationDialog(ai_manager, settings, parent)