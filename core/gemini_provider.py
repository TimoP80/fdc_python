"""
Google Gemini 3 Flash Provider for AI Dialogue System

This module provides integration with Google Gemini 3 Flash for:
- Intent recognition and NLU
- Sentiment analysis
- Translation
- Response generation

Features:
- Async API support
- Rate limiting
- Error handling with fallbacks
- Configurable model parameters
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
import hashlib
import re

import aiohttp

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class GeminiModel(Enum):
    """Available Gemini models"""
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_2_0_FLASH_LITE = "gemini-2.0-flash-lite"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_5_FLASH_8B = "gemini-1.5-flash-8b"


@dataclass
class GeminiConfig:
    """Configuration for Gemini API"""
    api_key: str = ""
    model: GeminiModel = GeminiModel.GEMINI_2_0_FLASH
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 30
    # Rate limiting
    requests_per_minute: int = 15
    requests_per_day: int = 1500
    # Model parameters
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 2048
    
    def __post_init__(self):
        # Load API key from environment if not set
        if not self.api_key:
            self.api_key = os.environ.get("GEMINI_API_KEY", "")


# ============================================================================
# Rate Limiter
# ============================================================================

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, requests_per_minute: int = 15, requests_per_day: int = 1500):
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        
        # Track request times
        self.minute_window: deque = deque()
        self.day_window: deque = deque()
        
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Acquire permission to make a request"""
        async with self._lock:
            now = time.time()
            
            # Clean old entries from minute window
            minute_ago = now - 60
            while self.minute_window and self.minute_window[0] < minute_ago:
                self.minute_window.popleft()
            
            # Clean old entries from day window
            day_ago = now - 86400
            while self.day_window and self.day_window[0] < day_ago:
                self.day_window.popleft()
            
            # Check limits
            if len(self.minute_window) >= self.requests_per_minute:
                wait_time = 60 - (now - self.minute_window[0])
                logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
                return False
            
            if len(self.day_window) >= self.requests_per_day:
                logger.error("Daily rate limit reached")
                return False
            
            # Record this request
            self.minute_window.append(now)
            self.day_window.append(now)
            
            return True
    
    async def wait_for_slot(self, max_wait: float = 60.0) -> bool:
        """Wait for rate limit slot"""
        start = time.time()
        while time.time() - start < max_wait:
            if await self.acquire():
                return True
            await asyncio.sleep(1)
        return False


# ============================================================================
# Gemini API Client
# ============================================================================

class GeminiClient:
    """Async client for Gemini API"""
    
    def __init__(self, config: GeminiConfig):
        self.config = config
        self.rate_limiter = RateLimiter(
            config.requests_per_minute,
            config.requests_per_day
        )
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self):
        """Close the session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _build_url(self, endpoint: str) -> str:
        """Build API URL"""
        return f"{self.config.base_url}/models/{self.config.model.value}:{endpoint}?key={self.config.api_key}"
    
    async def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        retries: int = 0
    ) -> Dict[str, Any]:
        """Make API request with retry logic"""
        url = self._build_url(endpoint)
        
        # Acquire rate limit slot
        if not await self.rate_limiter.wait_for_slot():
            raise Exception("Rate limit timeout")
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    # Rate limited - retry with backoff
                    if retries < self.config.max_retries:
                        await asyncio.sleep(self.config.retry_delay * (2 ** retries))
                        return await self._make_request(endpoint, payload, retries + 1)
                    raise Exception("Rate limit exceeded")
                elif response.status == 403:
                    raise Exception("API key invalid or insufficient permissions")
                elif response.status == 400:
                    error_text = await response.text()
                    raise Exception(f"Bad request: {error_text}")
                else:
                    raise Exception(f"API error: {response.status}")
                    
        except aiohttp.ClientError as e:
            if retries < self.config.max_retries:
                await asyncio.sleep(self.config.retry_delay * (2 ** retries))
                return await self._make_request(endpoint, payload, retries + 1)
            raise Exception(f"Network error: {str(e)}")
    
    async def generate_content(
        self,
        contents: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
        generation_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate content using Gemini"""
        
        payload = {
            "contents": contents,
            "generationConfig": generation_config or {
                "temperature": self.config.temperature,
                "topP": self.config.top_p,
                "topK": self.config.top_k,
                "maxOutputTokens": self.config.max_output_tokens,
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {
                "role": "system",
                "parts": [{"text": system_instruction}]
            }
        
        result = await self._make_request("generateContent", payload)
        
        # Parse response
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                parts = candidate["content"]["parts"]
                if parts:
                    return parts[0].get("text", "")
        
        # Check for safety or other issues
        if "promptFeedback" in result:
            feedback = result["promptFeedback"]
            if "blockReason" in feedback:
                raise Exception(f"Content blocked: {feedback['blockReason']}")
        
        return ""
    
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        payload = {
            "contents": [{"role": "user", "parts": [{"text": text}]}]
        }
        
        result = await self._make_request("countTokens", payload)
        return result.get("totalTokens", 0)


# ============================================================================
# Intent and Sentiment Analysis Prompts
# ============================================================================

INTENT_ANALYSIS_PROMPT = """Analyze the following user message and identify:
1. The primary intent (greeting, farewell, question, request, complaint, praise, confusion, clarification, information, unknown)
2. Any specific topics mentioned
3. Entities mentioned (person names, locations, numbers, dates)

Respond in JSON format:
{
    "intent": "intent_name",
    "confidence": 0.0-1.0,
    "topics": ["topic1", "topic2"],
    "entities": {"type": "value"}
}

User message: {message}"""

SENTIMENT_ANALYSIS_PROMPT = """Analyze the sentiment of the following text.
Respond in JSON format with:
- sentiment: "very_negative", "negative", "neutral", "positive", "very_positive"
- score: -1.0 to 1.0
- emotions: list of emotions detected

Text: {text}"""

TRANSLATION_PROMPT = """Translate the following text from {source_lang} to {target_lang}.
Respond with just the translation, nothing else.

Text: {text}"""

KNOWLEDGE_QUERY_PROMPT = """Based on the following knowledge base entries, answer the user's question.
If the knowledge base doesn't contain relevant information, say so.

Knowledge Base:
{knowledge}

User Question: {question}

Provide a helpful answer based on the knowledge base."""


# ============================================================================
# Gemini Provider Implementation
# ============================================================================

class GeminiProvider:
    """
    Google Gemini 3 Flash provider for the AI Dialogue System.
    
    Provides NLU, sentiment analysis, translation, and response generation
    using Google's Gemini API.
    """
    
    def __init__(self, config: Optional[GeminiConfig] = None):
        self.config = config or GeminiConfig()
        self.client: Optional[GeminiClient] = None
        self._initialized = False
        self._fallback_provider = None
        
        # Default system instruction
        self.system_instruction = """You are an AI assistant for the Fallout Dialogue Creator application.
You help users create dialogue for Fallout 1/2 games.
Be helpful, friendly, and knowledgeable about game mechanics.
Respond in a conversational manner."""
    
    @property
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self._initialized and self.client is not None
    
    async def initialize(self):
        """Initialize the provider"""
        if self._initialized:
            return
        
        if not self.config.api_key:
            logger.warning("No Gemini API key provided, using fallback mode")
            self._initialized = False
            return
        
        try:
            self.client = GeminiClient(self.config)
            # Test connection with a simple request
            await self.client.count_tokens("test")
            self._initialized = True
            logger.info("Gemini provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini provider: {e}")
            self._initialized = False
    
    async def shutdown(self):
        """Shutdown the provider"""
        if self.client:
            await self.client.close()
        self._initialized = False
    
    def set_fallback_provider(self, provider):
        """Set fallback provider for when Gemini is unavailable"""
        self._fallback_provider = provider
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from response text"""
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return {}
    
    # ========================================================================
    # NLU Methods
    # ========================================================================
    
    async def recognize_intent(
        self,
        text: str,
        context: Optional[Any] = None
    ) -> Tuple[str, float, Dict[str, Any], List[str]]:
        """
        Recognize user intent using Gemini.
        
        Returns:
            Tuple of (intent_type, confidence, entities, topics)
        """
        if not self.is_available:
            if self._fallback_provider:
                intent = await self._fallback_provider.recognize_intent(text, context)
                return (intent.type.value, intent.confidence, intent.entities, intent.extracted_topics)
            return ("unknown", 0.0, {}, [])
        
        try:
            prompt = INTENT_ANALYSIS_PROMPT.format(message=text)
            
            response = await self.client.generate_content(
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
                system_instruction="You are a helpful intent analysis assistant. Always respond with valid JSON."
            )
            
            parsed = self._parse_json_response(response)
            
            intent = parsed.get("intent", "unknown")
            confidence = float(parsed.get("confidence", 0.5))
            entities = parsed.get("entities", {})
            topics = parsed.get("topics", [])
            
            return (intent, confidence, entities, topics)
            
        except Exception as e:
            logger.error(f"Intent recognition error: {e}")
            if self._fallback_provider:
                intent = await self._fallback_provider.recognize_intent(text, context)
                return (intent.type.value, intent.confidence, intent.entities, intent.extracted_topics)
            return ("unknown", 0.0, {}, [])
    
    async def analyze_sentiment(
        self,
        text: str
    ) -> Tuple[str, float]:
        """
        Analyze sentiment using Gemini.
        
        Returns:
            Tuple of (sentiment_type, score)
        """
        if not self.is_available:
            if self._fallback_provider:
                return self._fallback_provider.analyze_sentiment(text)
            return ("neutral", 0.0)
        
        try:
            prompt = SENTIMENT_ANALYSIS_PROMPT.format(text=text)
            
            response = await self.client.generate_content(
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
                system_instruction="You are a helpful sentiment analysis assistant. Always respond with valid JSON."
            )
            
            parsed = self._parse_json_response(response)
            
            sentiment = parsed.get("sentiment", "neutral")
            score = float(parsed.get("score", 0.0))
            
            return (sentiment, score)
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            if self._fallback_provider:
                return self._fallback_provider.analyze_sentiment(text)
            return ("neutral", 0.0)
    
    # ========================================================================
    # Translation Methods
    # ========================================================================
    
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """Translate text using Gemini"""
        if not self.is_available:
            if self._fallback_provider:
                return self._fallback_provider.translate(text, source_lang, target_lang).translated_text
            return text
        
        try:
            prompt = TRANSLATION_PROMPT.format(
                source_lang=source_lang,
                target_lang=target_lang,
                text=text
            )
            
            response = await self.client.generate_content(
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
                system_instruction="You are a translation assistant. Provide only the translation, no explanations."
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            if self._fallback_provider:
                return self._fallback_provider.translate(text, source_lang, target_lang).translated_text
            return text
    
    async def detect_language(self, text: str) -> str:
        """Detect language of text"""
        if not self.is_available:
            if self._fallback_provider:
                return self._fallback_provider.detect_language(text)
            return "en"
        
        # Simple language detection via prompt
        prompt = f"What language is this text? Respond with just the 2-letter language code.\n\nText: {text[:200]}"
        
        try:
            response = await self.client.generate_content(
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
                system_instruction="You are a language detection assistant."
            )
            
            return response.strip().lower()[:2]
            
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return "en"
    
    # ========================================================================
    # Response Generation
    # ========================================================================
    
    async def generate_response(
        self,
        prompt: str,
        context: Any,
        config: Dict[str, Any],
        persona: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate response using Gemini.
        
        Returns:
            Dict with text, confidence, reasoning, sentiment
        """
        if not self.is_available:
            if self._fallback_provider:
                return await self._fallback_provider.generate_response(prompt, context, config, persona)
            return {
                "text": "I'm sorry, the AI service is currently unavailable.",
                "confidence": 0.0,
                "reasoning": "Fallback: Gemini provider not available"
            }
        
        try:
            # Build conversation history
            history_parts = []
            if context and hasattr(context, 'messages'):
                for msg in context.messages[-6:]:  # Last 6 messages
                    role = "model" if msg.role == "assistant" else "user"
                    history_parts.append({
                        "role": role,
                        "parts": [{"text": msg.content[:500]}]  # Truncate long messages
                    })
            
            # Build system instruction from persona
            system_instr = self._build_system_instruction(persona)
            
            # Generation config
            generation_config = {
                "temperature": config.get("temperature", 0.7),
                "topP": config.get("top_p", 0.95),
                "topK": config.get("top_k", 40),
                "maxOutputTokens": config.get("max_tokens", 2048),
            }
            
            # Build contents
            contents = history_parts + [{"role": "user", "parts": [{"text": prompt}]}]
            
            response = await self.client.generate_content(
                contents=contents,
                system_instruction=system_instr,
                generation_config=generation_config
            )
            
            return {
                "text": response,
                "confidence": 0.8,  # Gemini doesn't provide confidence
                "reasoning": "Generated via Gemini API"
            }
            
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            if self._fallback_provider:
                return await self._fallback_provider.generate_response(prompt, context, config, persona)
            return {
                "text": "I apologize, but I encountered an error. Please try again.",
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}"
            }
    
    def _build_system_instruction(self, persona: Dict[str, Any]) -> str:
        """Build system instruction from persona"""
        parts = [
            "You are a helpful AI assistant.",
        ]
        
        if persona.get("name"):
            parts.append(f"Your name is {persona['name']}.")
        
        if persona.get("description"):
            parts.append(persona["description"])
        
        if persona.get("traits"):
            parts.append(f"Your traits: {', '.join(persona['traits'])}.")
        
        # Add speaking style
        style = persona.get("speaking_style", "neutral")
        if style == "friendly":
            parts.append("Speak in a friendly, conversational tone.")
        elif style == "formal":
            parts.append("Speak in a formal, professional manner.")
        elif style == "casual":
            parts.append("Speak in a casual, relaxed manner.")
        
        # Add expertise
        if persona.get("expertise_areas"):
            parts.append(f"Your areas of expertise include: {', '.join(persona['expertise_areas'])}.")
        
        return " ".join(parts)


# ============================================================================
# Async Context Manager Support
# ============================================================================

class GeminiProviderAsync:
    """Async context manager for Gemini provider"""
    
    def __init__(self, config: Optional[GeminiConfig] = None):
        self.config = config
        self.provider: Optional[GeminiProvider] = None
    
    async def __aenter__(self):
        self.provider = GeminiProvider(self.config)
        await self.provider.initialize()
        return self.provider
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.provider:
            await self.provider.shutdown()
        if self.provider and self.provider.client:
            await self.provider.client.close()


# ============================================================================
# Factory Function
# ============================================================================

def create_gemini_provider(
    api_key: Optional[str] = None,
    model: GeminiModel = GeminiModel.GEMINI_2_0_FLASH,
    **kwargs
) -> GeminiProvider:
    """
    Create a Gemini provider instance.
    
    Args:
        api_key: Google API key (or set GEMINI_API_KEY env var)
        model: Gemini model to use
        **kwargs: Additional configuration options
    
    Returns:
        GeminiProvider instance
    """
    config = GeminiConfig(
        api_key=api_key or "",
        model=model,
        **{k: v for k, v in kwargs.items() if k in GeminiConfig.__dataclass_fields__}
    )
    
    return GeminiProvider(config)


async def create_gemini_provider_async(
    api_key: Optional[str] = None,
    model: GeminiModel = GeminiModel.GEMINI_2_0_FLASH,
    **kwargs
) -> GeminiProvider:
    """
    Create and initialize a Gemini provider asynchronously.
    
    Args:
        api_key: Google API key (or set GEMINI_API_KEY env var)
        model: Gemini model to use
        **kwargs: Additional configuration options
    
    Returns:
        Initialized GeminiProvider instance
    """
    provider = create_gemini_provider(api_key, model, **kwargs)
    await provider.initialize()
    return provider
