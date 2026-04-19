"""
AI Dialogue Manager - Coordinator between GUI and AI System

This module provides the AIDialogueManager class which serves as the central
coordinator between the GUI and the AIDialogueSystem. It handles:
- Thread-safe request queuing
- Signal/Slot communication with PyQt6
- Conversation context management
- Response caching
- Error handling and recovery

Location: core/ai_dialogue_manager.py
"""

import logging
import threading
import queue
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Callable

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer, Qt
from PyQt6.QtWidgets import QApplication

from .ai_dialogue_system import (
    AIDialogueSystem,
    ResponseConfig,
    Persona,
    ResponseCreativity,
    ResponseLength,
    FormalityTone,
    SentimentType,
    GeneratedResponse,
    configure_ai_system_from_settings
)
from .settings import Settings
from .ollama_provider import OllamaCloudModel


# ============================================================================
# Exception Classes
# ============================================================================

class AIProviderError(Exception):
    """Exception raised when an AI provider encounters an error"""
    pass


class AIRequestError(Exception):
    """Exception raised for AI request-related errors"""
    pass

logger = logging.getLogger(__name__)


# ============================================================================
# Request Types
# ============================================================================

class AIRequestType(Enum):
    """Types of AI requests"""
    GENERATE_DIALOGUE = 1
    ANALYZE_SENTIMENT = 2
    SUGGEST_RESPONSES = 3
    TRANSLATE_TEXT = 4
    IMPROVE_TEXT = 5
    CHAT = 6


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class AIRequest:
    """Represents an AI processing request"""
    request_id: str
    request_type: AIRequestType
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    config: Optional[ResponseConfig] = None
    persona: Optional[Persona] = None
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 0
    retry_count: int = 0
    
    @staticmethod
    def create(request_type: AIRequestType, prompt: str, 
               context: Optional[Dict] = None,
               config: Optional[ResponseConfig] = None,
               persona: Optional[Persona] = None,
               priority: int = 0) -> 'AIRequest':
        """Factory method to create a new request with generated ID"""
        timestamp = str(time.time())
        request_id = hashlib.md5(timestamp.encode()).hexdigest()[:12]
        return AIRequest(
            request_id=request_id,
            request_type=request_type,
            prompt=prompt,
            context=context or {},
            config=config,
            persona=persona,
            priority=priority
        )


@dataclass
class AIResponse:
    """Represents an AI processing response"""
    request_id: str
    success: bool
    response_text: str = ""
    suggestions: List[str] = field(default_factory=list)
    sentiment: Optional[SentimentType] = None
    confidence: float = 0.0
    processing_time_ms: int = 0
    error_message: Optional[str] = None


@dataclass 
class ConversationContext:
    """Context for AI-assisted dialogue editing"""
    dialogue_id: str = ""
    current_node_id: str = ""
    previous_nodes: List[str] = field(default_factory=list)
    npc_name: str = ""
    npc_persona: Optional[Persona] = None
    player_options: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)


# ============================================================================
# Background Thread with Separate Event Loop
# ============================================================================

class AIQueueProcessor(QObject):
    """Processes AI requests in a background thread with its own event loop"""

    request_completed = pyqtSignal(AIResponse)
    progress_update = pyqtSignal(int, str)

    def __init__(self, ai_system: AIDialogueSystem, parent=None):
        super().__init__(parent)
        self.ai_system = ai_system
        self.request_queue: queue.Queue = queue.Queue()
        self._is_running = False
        self._thread = None

    def start(self):
        """Start the background thread"""
        self._is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("AI processor thread started")

    def stop(self):
        """Stop the processor"""
        self._is_running = False
        if self._thread:
            self.request_queue.put(None)  # Signal to exit
            self._thread.join(timeout=2)
        logger.info("AI processor thread stopped")

    def add_request(self, request: AIRequest):
        """Add a request to the queue"""
        self.request_queue.put(request)

    def _run_loop(self):
        """Run event loop in background thread"""
        import asyncio

        logger.debug("Starting event loop in background thread")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while self._is_running:
            try:
                request = self.request_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            logger.debug(f"Got request: {request.request_id}")
            if request is None:
                break

            try:
                logger.debug("Running async process...")
                response = loop.run_until_complete(
                    self._process_one(request))
                logger.debug(f"Got response: {response.response_text[:50] if response.success else 'error'}")
                self.request_completed.emit(response)
            except Exception as e:
                logger.error(f"Queue error: {e}")
                self.request_completed.emit(AIResponse(
                    request_id=request.request_id,
                    success=False,
                    error_message=str(e)))

        loop.close()
        logger.debug("Event loop closed")

    async def _process_one(self, request: AIRequest):
        """Process single request async"""
        start_time = time.time()
        self.progress_update.emit(10, "Processing...")

        try:
            if request.request_type == AIRequestType.CHAT:
                response = await self.ai_system.process_message_async(
                    message=request.prompt,
                    conversation_id=request.context.get('conversation_id', 'default'),
                    config=request.config,
                    persona=request.persona
                )
                return AIResponse(
                    request_id=request.request_id,
                    success=True,
                    response_text=response.text if response else ""
                )

            elif request.request_type == AIRequestType.SUGGEST_RESPONSES:
                node_text = request.context.get('node_text', '')
                prompt = f"Generate 4 short player responses for: {node_text}"

                response = await self.ai_system.process_message_async(
                    message=prompt,
                    conversation_id=request.context.get('conversation_id', 'default'),
                    config=request.config,
                    persona=request.persona
                )

                lines = response.text.strip().split('\n') if response else []
                suggestions = []
                for l in lines:
                    l = l.strip()
                    l = l.lstrip('0123456789.).*- ')
                    if l:
                        suggestions.append(l)
                suggestions = suggestions[:4]

                return AIResponse(
                    request_id=request.request_id,
                    success=True,
                    suggestions=suggestions
                )

            elif request.request_type == AIRequestType.SENTIMENT:
                result = await self.ai_system.analyze_sentiment_async(request.prompt)
                return AIResponse(
                    request_id=request.request_id,
                    success=True,
                    response_text=result.text,
                    sentiment=result.sentiment,
                    confidence=result.confidence
                )

            return AIResponse(
                request_id=request.request_id,
                success=False,
                error_message=f"Unknown type: {request.request_type}"
            )

        except Exception as e:
            logger.error(f"Request error: {e}")
            return AIResponse(
                request_id=request.request_id,
                success=False,
                error_message=str(e),
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
    
    def _process_request(self, request: AIRequest) -> AIResponse:
        """Process a single AI request"""
        start_time = time.time()
        
        try:
            self.progress_update.emit(10, "Processing request...")
            
            if request.request_type == AIRequestType.CHAT:
                # Handle chat messages
                response = self._handle_chat(request)
            elif request.request_type == AIRequestType.SUGGEST_RESPONSES:
                response = self._handle_suggestions(request)
            elif request.request_type == AIRequestType.ANALYZE_SENTIMENT:
                response = self._handle_sentiment(request)
            elif request.request_type == AIRequestType.IMPROVE_TEXT:
                response = self._handle_improve_text(request)
            elif request.request_type == AIRequestType.TRANSLATE_TEXT:
                response = self._handle_translate(request)
            else:
                response = self._handle_chat(request)
                
            processing_time = int((time.time() - start_time) * 1000)
            response.processing_time_ms = processing_time
            
            self.progress_update.emit(100, "Complete")
            return response
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"Request processing error: {e}")
            return AIResponse(
                request_id=request.request_id,
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time
            )
    
    def _handle_chat(self, request: AIRequest) -> AIResponse:
        """Handle chat/generate response requests"""
        config = request.config or ResponseConfig()

        try:
            logger.debug(f"_handle_chat: processing '{request.prompt[:30]}'")

            response = self.ai_system.process_message(
                message=request.prompt,
                conversation_id=request.context.get('conversation_id', 'default'),
                config=config,
                persona=request.persona
            )
            logger.debug(f"_handle_chat: got response type={type(response)}")

            # Unwrap if needed
            if hasattr(response, '__await__'):
                # It's a coroutine - this shouldn't happen with sync-only call
                response_text = "System not properly configured"
            else:
                response_text = response.text if response else ""

            return AIResponse(
                request_id=request.request_id,
                success=True,
                response_text=response_text
            )
        except AIProviderError as e:
            return AIResponse(
                request_id=request.request_id,
                success=False,
                error_message=f"Provider error: {str(e)}"
            )
    
    def _handle_suggestions(self, request: AIRequest) -> AIResponse:
        """Handle suggestion generation requests"""
        # Build context for suggestions
        node_text = request.context.get('node_text', '')
        npc_name = request.context.get('npc_name', 'NPC')
        
        # Create a prompt for generating suggestions
        prompt = f"""Generate 4 possible player response options for this NPC dialogue:
        
NPC: {node_text}

Provide 4 short, varied responses a player could choose. Keep them concise (1-2 sentences)."""
        
        try:
            response = self.ai_system.process_message(
                message=prompt,
                conversation_id=request.context.get('conversation_id', 'default'),
                config=request.config
            )
            
            # Parse suggestions from response
            suggestions = self._parse_suggestions(response.text if response else "")
            
            return AIResponse(
                request_id=request.request_id,
                success=True,
                suggestions=suggestions
            )
        except Exception as e:
            return AIResponse(
                request_id=request.request_id,
                success=False,
                error_message=str(e)
            )
    
    def _parse_suggestions(self, text: str) -> List[str]:
        """Parse suggestions from generated text"""
        lines = text.strip().split('\n')
        suggestions = []
        for line in lines:
            line = line.strip()
            # Remove numbering like "1.", "2.", "-", "*"
            line = line.lstrip('0123456789.).*- ')
            if line and len(line) < 200:
                suggestions.append(line)
        return suggestions[:4]  # Limit to 4
    
    def _handle_sentiment(self, request: AIRequest) -> AIResponse:
        """Handle sentiment analysis requests"""
        try:
            result = self.ai_system.analyze_sentiment(request.prompt)
            
            return AIResponse(
                request_id=request.request_id,
                success=True,
                response_text=result.text,
                sentiment=result.sentiment,
                confidence=result.confidence
            )
        except Exception as e:
            return AIResponse(
                request_id=request.request_id,
                success=False,
                error_message=str(e)
            )
    
    def _handle_improve_text(self, request: AIRequest) -> AIResponse:
        """Handle text improvement requests"""
        improvement_type = request.context.get('improvement_type', 'grammar')
        
        prompt = f"""Improve this dialogue text for {improvement_type}:

{request.prompt}

Provide the improved version."""
        
        try:
            response = self.ai_system.process_message(
                message=prompt,
                conversation_id=request.context.get('conversation_id', 'default'),
                config=request.config
            )
            
            return AIResponse(
                request_id=request.request_id,
                success=True,
                response_text=response.text if response else ""
            )
        except Exception as e:
            return AIResponse(
                request_id=request.request_id,
                success=False,
                error_message=str(e)
            )
    
    def _handle_translate(self, request: AIRequest) -> AIResponse:
        """Handle translation requests"""
        target_lang = request.context.get('target_language', 'en')
        
        try:
            result = self.ai_system.translate_text(
                text=request.prompt,
                target_language=target_lang
            )
            
            return AIResponse(
                request_id=request.request_id,
                success=True,
                response_text=result.translated_text if result else ""
            )
        except Exception as e:
            return AIResponse(
                request_id=request.request_id,
                success=False,
                error_message=str(e)
            )


# ============================================================================
# Main Manager Class
# ============================================================================

class AIDialogueManager(QObject):
    """
    Manages AI dialogue operations and GUI integration
    
    This class serves as the central coordinator between the GUI and the AI system.
    It extends QObject to provide thread-safe signals/slots for PyQt6 integration.
    
    Signals:
        response_ready (str): AI response text
        suggestion_ready (list): List of suggestions
        progress_update (int, str): Progress percentage, status
        error_occurred (str): Error message
        status_changed (str): Status update
    """
    
    # Signals for GUI updates
    response_ready = pyqtSignal(str)           # AI response text
    suggestion_ready = pyqtSignal(list)        # List of suggestions
    progress_update = pyqtSignal(int, str)     # Progress percentage, status
    error_occurred = pyqtSignal(str)          # Error message
    status_changed = pyqtSignal(str)           # Status update
    
    # Status constants
    STATUS_INITIALIZED = "initialized"
    STATUS_READY = "ready"
    STATUS_PROCESSING = "processing"
    STATUS_OFFLINE = "offline"
    STATUS_ERROR = "error"
    
    def __init__(
        self,
        settings: Settings,
        dialog_manager: Optional[Any] = None
    ):
        """
        Initialize the AI Dialogue Manager.

        Args:
            settings: Application settings for configuration
            dialog_manager: Optional dialog manager for state sync
        """
        super().__init__()

        self.settings = settings
        self.dialog_manager = dialog_manager
        self.status = self.STATUS_INITIALIZED

        # Initialize AI system
        self.ai_system = AIDialogueSystem(settings)

        # Create main thread async processor
        self.processor = AIQueueProcessor(self.ai_system, self)
        self.processor.request_completed.connect(self._on_response_ready)
        self.processor.progress_update.connect(self._on_progress)

        # Response cache
        self._response_cache: Dict[str, AIResponse] = {}
        self._cache_max_size = 100

        # Conversation management
        self._conversations: Dict[str, ConversationContext] = {}
        self._current_conversation_id: Optional[str] = None

        # Default config
        self._default_config = ResponseConfig(
            creativity=ResponseCreativity.BALANCED,
            length=ResponseLength.NORMAL,
            formality=FormalityTone.NEUTRAL
        )

        # Default persona
        self._default_persona = Persona()

        # Status check timer
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._check_ai_status)

        logger.info("AIDialogueManager initialized")

    def start(self):
        """Start the AI manager and processor"""
        # Configure the system with settings BEFORE starting processor
        configure_ai_system_from_settings(self.ai_system, self.settings)

        self.processor.start()

        # Do initial status check to determine if online/offline
        self._check_ai_status()

        # Start periodic status checks
        self._status_timer.start(30000)  # Check every 30 seconds

        logger.info("AIDialogueManager started")
    
    def stop(self):
        """Stop the AI manager and processor"""
        self._status_timer.stop()
        self.processor.stop()

        self.status = self.STATUS_INITIALIZED
        self.status_changed.emit(self.status)

        logger.info("AIDialogueManager stopped")
    
    def set_dialog_manager(self, dialog_manager: Any):
        """Set the dialog manager for state synchronization"""
        self.dialog_manager = dialog_manager
    # =========================================================================
    # Core Methods
    # =========================================================================
    
    def generate_response(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        config: Optional[ResponseConfig] = None,
        persona: Optional[Persona] = None
    ) -> None:
        """
        Generate an AI response to the given prompt.
        
        This method is asynchronous - the response will be emitted via the
        response_ready signal.
        
        Args:
            prompt: User input prompt
            conversation_id: Optional conversation context ID
            config: Response generation configuration
            persona: Character persona to use
        """
        self.status = self.STATUS_PROCESSING
        self.status_changed.emit(self.status)
        
        # Build context
        context = {}
        if conversation_id:
            context['conversation_id'] = conversation_id
        elif self._current_conversation_id:
            context['conversation_id'] = self._current_conversation_id
            
        # Check cache
        cache_key = self._get_cache_key(prompt, context)
        if cache_key in self._response_cache:
            cached = self._response_cache[cache_key]
            self.response_ready.emit(cached.response_text)
            self.status = self.STATUS_READY
            self.status_changed.emit(self.status)
            return
        
        # Create and queue request to processor
        request = AIRequest.create(
            request_type=AIRequestType.CHAT,
            prompt=prompt,
            context=context,
            config=config or self._default_config,
            persona=persona or self._default_persona
        )

        self.processor.add_request(request)
        logger.debug(f"Added chat request: {request.request_id}")
    
    def suggest_dialogue_options(
        self,
        node_text: str,
        num_suggestions: int = 4
    ) -> None:
        """
        Generate suggested player response options.
        
        This method is asynchronous - suggestions will be emitted via the
        suggestion_ready signal.
        
        Args:
            node_text: The NPC dialogue node text
            num_suggestions: Number of options to generate
        """
        self.status = self.STATUS_PROCESSING
        self.status_changed.emit(self.status)
        
        # Build context
        context = {
            'node_text': node_text,
            'npc_name': self._get_current_npc_name()
        }
        if self._current_conversation_id:
            context['conversation_id'] = self._current_conversation_id
        
        request = AIRequest.create(
            request_type=AIRequestType.SUGGEST_RESPONSES,
            prompt="",
            context=context,
            config=self._default_config
        )
        
        self.processor.add_request(request)
        logger.debug(f"Added suggestion request: {request.request_id}")
    
    def analyze_sentiment(self, text: str) -> None:
        """
        Analyze the sentiment of text.
        
        This method is asynchronous - results will be emitted via the
        response_ready signal.
        
        Args:
            text: Text to analyze
        """
        self.status = self.STATUS_PROCESSING
        self.status_changed.emit(self.status)
        
        request = AIRequest.create(
            request_type=AIRequestType.ANALYZE_SENTIMENT,
            prompt=text
        )
        
        self.processor.add_request(request)
        logger.debug(f"Added sentiment request: {request.request_id}")
    
    def improve_text(
        self,
        text: str,
        improvement_type: str = "grammar"
    ) -> None:
        """
        Improve dialogue text.
        
        This method is asynchronous - results will be emitted via the
        response_ready signal.
        
        Args:
            text: Text to improve
            improvement_type: Type of improvement (grammar/tonality/fluency)
        """
        self.status = self.STATUS_PROCESSING
        self.status_changed.emit(self.status)
        
        context = {'improvement_type': improvement_type}
        
        request = AIRequest.create(
            request_type=AIRequestType.IMPROVE_TEXT,
            prompt=text,
            context=context,
            config=self._default_config
        )
        
        self.processor.add_request(request)
        logger.debug(f"Added improve text request: {request.request_id}")
    
    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: str = "en"
    ) -> None:
        """
        Translate dialogue text.
        
        This method is asynchronous - results will be emitted via the
        response_ready signal.
        
        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code
        """
        self.status = self.STATUS_PROCESSING
        self.status_changed.emit(self.status)
        
        context = {
            'target_language': target_language,
            'source_language': source_language
        }
        
        request = AIRequest.create(
            request_type=AIRequestType.TRANSLATE_TEXT,
            prompt=text,
            context=context,
            config=self._default_config
        )
        
        self.processor.add_request(request)
        logger.debug(f"Added translation request: {request.request_id}")
    
    # =========================================================================
    # Configuration Methods
    # =========================================================================
    
    def set_provider(self, provider_type: str, config: Dict):
        """Set the AI provider (ollama/gemini/local)"""
        # Kept for compatibility, but preferences are now handled by reload_provider
        logger.info(f"Setting AI provider: {provider_type}")
    
    def reload_provider(self):
        """Reload the AI provider from current settings."""
        logger.info("Reloading AI provider configuration from settings")
        configure_ai_system_from_settings(self.ai_system, self.settings)
    
    def get_available_models(self) -> List[str]:
        """Get list of available AI models"""
        # Return cloud models from OllamaCloudModel enum
        return [model.value for model in OllamaCloudModel]
    
    def set_persona(self, persona: Persona):
        """Set the character persona for generation"""
        self._default_persona = persona
        
    def set_config(self, config: ResponseConfig):
        """Set the default response configuration"""
        self._default_config = config
    
    def get_conversation_history(self, conversation_id: str) -> List[str]:
        """Get conversation history for context"""
        # This would return the conversation history
        return []
    
    def create_conversation(self) -> str:
        """Create a new conversation and return its ID"""
        conv_id = self.ai_system.create_conversation()
        self._current_conversation_id = conv_id
        
        # Create context
        context = ConversationContext(dialogue_id=conv_id)
        self._conversations[conv_id] = context
        
        return conv_id
    
    def set_current_conversation(self, conversation_id: str):
        """Set the current active conversation"""
        self._current_conversation_id = conversation_id
        
    # =========================================================================
    # Private Methods
    # =========================================================================
    
    def _on_response_ready(self, response: AIResponse):
        """Handle response from worker thread"""
        logger.debug(f"_on_response_ready: success={response.success}, text={response.response_text[:30] if response.response_text else 'empty'}")
        
        if response.success:
            if response.suggestions:
                logger.debug("_on_response_ready: emitting suggestion_ready")
                self.suggestion_ready.emit(response.suggestions)
            else:
                logger.debug(f"_on_response_ready: emitting response_ready with: {response.response_text[:30]}...")
                self.response_ready.emit(response.response_text)
            
            # Cache successful responses
            if response.response_text:
                cache_key = self._get_cache_key_from_response(response)
                self._add_to_cache(cache_key, response)
        else:
            logger.debug(f"_on_response_ready: emitting error_occurred")
            self.error_occurred.emit(response.error_message or "Unknown error")
        
        # Always reset status to ready after response
        self.status = self.STATUS_READY
        self.status_changed.emit(self.status)
    
    def _on_progress(self, progress: int, status: str):
        """Handle progress updates from worker"""
        self.progress_update.emit(progress, status)
    
    def _check_ai_status(self):
        """Periodically check AI provider status"""
        try:
            ai_system = self.ai_system
            if ai_system and hasattr(ai_system, '_providers_available'):
                providers = ai_system._providers_available
                any_available = any(providers.values())
                
                if not any_available:
                    new_status = self.STATUS_OFFLINE
                else:
                    new_status = self.STATUS_READY
                
                if new_status != self.status:
                    self.status = new_status
                    self.status_changed.emit(self.status)
                    logger.debug(f"AI status check: {new_status}")
        except Exception as e:
            logger.warning(f"Status check failed: {e}")
            if self.status != self.STATUS_ERROR:
                self.status = self.STATUS_ERROR
                self.status_changed.emit(self.status)
    
    def _get_cache_key(self, prompt: str, context: Dict) -> str:
        """Generate cache key for a request"""
        key_data = f"{prompt}:{str(context)}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    def _get_cache_key_from_response(self, response: AIResponse) -> str:
        """Get cache key from response"""
        return response.request_id[:16]
    
    def _add_to_cache(self, key: str, response: AIResponse):
        """Add response to cache"""
        if len(self._response_cache) >= self._cache_max_size:
            # Remove oldest entry
            oldest = next(iter(self._response_cache))
            del self._response_cache[oldest]
            
        self._response_cache[key] = response
    
    def _get_current_npc_name(self) -> str:
        """Get the current NPC name from dialog manager"""
        if self.dialog_manager and self.dialog_manager.current_dialogue:
            return self.dialog_manager.current_dialogue.npcname or "NPC"
        return "NPC"


# ============================================================================
# Convenience Functions
# ============================================================================

def create_default_config(
    creativity: ResponseCreativity = ResponseCreativity.BALANCED,
    length: ResponseLength = ResponseLength.NORMAL,
    formality: FormalityTone = FormalityTone.NEUTRAL
) -> ResponseConfig:
    """Create a default response configuration"""
    return ResponseConfig(
        creativity=creativity,
        length=length,
        formality=formality,
        max_tokens=500,
        temperature=0.7
    )


def create_default_persona(
    name: str = "Assistant",
    traits: List[str] = None
) -> Persona:
    """Create a default persona"""
    return Persona(
        name=name,
        traits=traits or ["helpful", "friendly"],
        speaking_style="neutral"
    )