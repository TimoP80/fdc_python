"""
OllamaCloud Provider for AI Dialogue System

This module provides integration with OllamaCloud for:
- Intent recognition and NLU
- Sentiment analysis
- Translation
- Response generation

Features:
- Async API support
- Circuit breaker pattern for fault tolerance
- Automatic retry with exponential backoff
- Connection pooling
- Health checks
- Rate limiting
- Comprehensive error handling with fallbacks
- Resilient response parsing

OllamaCloud provides free tier access to various LLM models.
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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

class OllamaCloudModel(Enum):
    """Available Ollama Cloud models (https://ollama.com/search?c=cloud)"""
    # Cloud models (require cloud subscription)
    GPT_OSS_32B = "gpt-oss:32b-cloud"
    GPT_OSS_120B = "gpt-oss:120b-cloud"
    LLAMA_3_3_70B = "llama3.3:70b-cloud"
    LLAMA_3_1_405B = "llama3.1:405b-cloud"
    MISTRAL_SMALL = "mistral-small3.1:24b-cloud"
    GEMMA_3_27B = "gemma3:27b-cloud"
    QWEN_2_5_72B = "qwen2.5:72b-cloud"
    # Regular models (available with API key)
    GEMMA4_31B = "gemma4:31b"
    LLAMA3_2_3B = "llama3.2:3b"
    QWEN2_5_72B = "qwen2.5:72b"
    MISTRAL_LARGE = "mistral-large-3:675b"


@dataclass
class OllamaCloudConfig:
    """Configuration for Ollama Cloud API (https://docs.ollama.com/cloud)"""
    api_key: str = ""
    base_url: str = "https://ollama.com"
    model: OllamaCloudModel = OllamaCloudModel.GPT_OSS_32B
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_max_delay: float = 30.0
    # Timeout settings
    connect_timeout: float = 10.0
    read_timeout: float = 60.0
    # Rate limiting
    requests_per_minute: int = 20
    requests_per_hour: int = 100
    # Circuit breaker
    circuit_breaker_threshold: int = 5  # failures before opening
    circuit_breaker_timeout: float = 30.0  # seconds before half-open
    # Model parameters
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    max_tokens: int = 2048
    # Connection pooling
    max_connections: int = 10
    max_keepalive_connections: int = 5
    
    def __post_init__(self):
        # Load API key from environment if not set
        # Official env var per docs: OLLAMA_API_KEY
        if not self.api_key:
            self.api_key = os.environ.get("OLLAMA_API_KEY", "")
        
        # Validate base URL
        if not self.base_url.startswith(("http://", "https://")):
            self.base_url = "https://" + self.base_url


# ============================================================================
# Circuit Breaker Pattern
# ============================================================================

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance.
    
    Prevents cascading failures by failing fast when a service is unhealthy.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()
        
        # Statistics
        self._total_calls = 0
        self._successful_calls = 0
        self._failed_calls = 0
        
        logger.info(
            f"CircuitBreaker initialized: threshold={failure_threshold}, "
            f"timeout={recovery_timeout}s"
        )
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        return self._state
    
    @property
    def is_available(self) -> bool:
        """Check if circuit allows requests"""
        return self._state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "state": self._state.value,
            "total_calls": self._total_calls,
            "successful_calls": self._successful_calls,
            "failed_calls": self._failed_calls,
            "failure_count": self._failure_count,
            "failure_rate": self._failed_calls / max(self._total_calls, 1)
        }
    
    async def can_execute(self) -> bool:
        """Check if a request can be executed"""
        async with self._lock:
            self._total_calls += 1
            
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if self._last_failure_time and \
                   time.time() - self._last_failure_time >= self.recovery_timeout:
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                else:
                    self._failed_calls += 1
                    return False
            
            if self._state == CircuitState.HALF_OPEN:
                # Limit calls in half-open state
                if self._half_open_calls >= self.half_open_max_calls:
                    self._failed_calls += 1
                    return False
                self._half_open_calls += 1
            
            return True
    
    async def record_success(self):
        """Record a successful call"""
        async with self._lock:
            self._successful_calls += 1
            
            if self._state == CircuitState.HALF_OPEN:
                # Successful call in half-open state - close circuit
                logger.info("Circuit breaker CLOSED after successful recovery")
                self._state = CircuitState.CLOSED
                self._failure_count = 0
            
            # Reset failure count on success in closed state
            if self._state == CircuitState.CLOSED:
                self._failure_count = 0
    
    async def record_failure(self):
        """Record a failed call"""
        async with self._lock:
            self._failed_calls += 1
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                # Failed call in half-open - reopen circuit
                logger.warning("Circuit breaker re-OPENED after failed recovery attempt")
                self._state = CircuitState.OPEN
            
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    logger.warning(
                        f"Circuit breaker OPEN after {self._failure_count} failures"
                    )
                    self._state = CircuitState.OPEN
    
    async def reset(self):
        """Manually reset the circuit breaker"""
        async with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            self._half_open_calls = 0
            logger.info("Circuit breaker manually reset")


# ============================================================================
# Rate Limiter
# ============================================================================

class OllamaRateLimiter:
    """Token bucket rate limiter with minute and hour windows"""
    
    def __init__(self, requests_per_minute: int = 20, requests_per_hour: int = 100):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Track request times
        self._minute_window: deque = deque()
        self._hour_window: deque = deque()
        
        self._lock = asyncio.Lock()
        
        # Statistics
        self._total_requests = 0
        self._throttled_requests = 0
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            "requests_per_minute": self.requests_per_minute,
            "requests_per_hour": self.requests_per_hour,
            "current_minute_count": len(self._minute_window),
            "current_hour_count": len(self._hour_window),
            "total_requests": self._total_requests,
            "throttled_requests": self._throttled_requests
        }
    
    async def acquire(self) -> bool:
        """Acquire permission to make a request"""
        async with self._lock:
            now = time.time()
            self._total_requests += 1
            
            # Clean old entries from minute window
            minute_ago = now - 60
            while self._minute_window and self._minute_window[0] < minute_ago:
                self._minute_window.popleft()
            
            # Clean old entries from hour window
            hour_ago = now - 3600
            while self._hour_window and self._hour_window[0] < hour_ago:
                self._hour_window.popleft()
            
            # Check limits
            if len(self._minute_window) >= self.requests_per_minute:
                self._throttled_requests += 1
                wait_time = 60 - (now - self._minute_window[0])
                logger.warning(
                    f"Rate limit (minute) reached, waiting {wait_time:.1f}s"
                )
                return False
            
            if len(self._hour_window) >= self.requests_per_hour:
                self._throttled_requests += 1
                logger.error("Rate limit (hour) reached")
                return False
            
            # Record this request
            self._minute_window.append(now)
            self._hour_window.append(now)
            
            return True
    
    async def wait_for_slot(self, max_wait: float = 60.0) -> bool:
        """Wait for rate limit slot"""
        start = time.time()
        while time.time() - start < max_wait:
            if await self.acquire():
                return True
            # Adaptive sleep based on how full the buckets are
            await asyncio.sleep(1)
        
        logger.error(f"Rate limit wait timeout after {max_wait}s")
        return False


# ============================================================================
# Health Check
# ============================================================================

class HealthChecker:
    """Health check for OllamaCloud service"""
    
    def __init__(self, client: 'OllamaCloudClient'):
        self._client = client
        self._last_check_time: Optional[float] = None
        self._last_health_status: bool = False
        self._check_interval: float = 60.0  # Check every 60 seconds
        self._lock = asyncio.Lock()
        
        # Health history
        self._health_history: deque = deque(maxlen=10)
    
    @property
    def is_healthy(self) -> bool:
        """Get last known health status"""
        return self._last_health_status
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get health check statistics"""
        return {
            "last_check_time": self._last_check_time,
            "last_health_status": self._last_health_status,
            "check_interval": self._check_interval,
            "health_history": list(self._health_history)
        }
    
    async def check_health(self, force: bool = False) -> bool:
        """Perform health check"""
        async with self._lock:
            now = time.time()
            
            # Skip if checked recently (unless forced)
            if not force and self._last_check_time:
                if now - self._last_check_time < self._check_interval:
                    return self._last_health_status
            
            try:
                # Try a simple API call to check health
                response = await self._client.generate_content(
                    [{"role": "user", "parts": [{"text": "ping"}]}],
                    max_tokens=1
                )
                # If we get any response, service is healthy
                self._last_health_status = bool(response)
                logger.debug(f"Health check: {'healthy' if self._last_health_status else 'unhealthy'}")
            except Exception as e:
                logger.warning(f"Health check failed: {e}")
                self._last_health_status = False
            
            self._last_check_time = now
            self._health_history.append({
                "timestamp": now,
                "healthy": self._last_health_status
            })
            
            return self._last_health_status


# ============================================================================
# OllamaCloud API Client
# ============================================================================

class OllamaCloudClient:
    """Async client for OllamaCloud API"""
    
    def __init__(self, config: OllamaCloudConfig):
        self.config = config
        self.rate_limiter = OllamaRateLimiter(
            config.requests_per_minute,
            config.requests_per_hour
        )
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.circuit_breaker_threshold,
            recovery_timeout=config.circuit_breaker_timeout
        )
        self._session: Optional[aiohttp.ClientSession] = None
        self._health_checker: Optional[HealthChecker] = None
        
        # Request/response logging
        self._request_log: deque = deque(maxlen=100)
        
        logger.info(f"OllamaCloudClient initialized: {config.base_url}")
    
    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create session with connection pooling"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(
                connect=self.config.connect_timeout,
                total=self.config.read_timeout
            )
            connector = aiohttp.TCPConnector(
                limit=self.config.max_connections,
                limit_per_host=self.config.max_keepalive_connections,
                keepalive_timeout=30
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            )
            logger.debug("Created new aiohttp session with connection pooling")
        return self._session
    
    @property
    def health_checker(self) -> HealthChecker:
        """Get or create health checker"""
        if self._health_checker is None:
            self._health_checker = HealthChecker(self)
        return self._health_checker
    
    async def close(self):
        """Close the session"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("Closed OllamaCloud client session")
    
    def _build_url(self, endpoint: str) -> str:
        """Build API URL"""
        base = self.config.base_url.rstrip('/')
        return f"{base}/{endpoint.lstrip('/')}"
    
    def _get_headers(self) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "FalloutDialogueCreator/2.0"
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers
    
    async def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        retries: int = 0
    ) -> Dict[str, Any]:
        """Make API request with circuit breaker and retry logic"""
        
        # Check circuit breaker
        if not await self.circuit_breaker.can_execute():
            raise Exception(
                f"Circuit breaker OPEN - request rejected. "
                f"State: {self.circuit_breaker.state.value}"
            )
        
        # Acquire rate limit slot
        if not await self.rate_limiter.wait_for_slot():
            raise Exception("Rate limit timeout")
        
        url = self._build_url(endpoint)
        request_time = time.time()
        
        # Log request
        self._request_log.append({
            "timestamp": request_time,
            "endpoint": endpoint,
            "retries": retries
        })
        
        try:
            async with self.session.post(
                url,
                json=payload,
                headers=self._get_headers()
            ) as response:
                response_time = time.time() - request_time
                
                if response.status == 200:
                    result = await response.json()
                    await self.circuit_breaker.record_success()
                    logger.debug(
                        f"Request successful: {endpoint} "
                        f"(took {response_time:.2f}s)"
                    )
                    return result
                
                elif response.status == 429:
                    # Rate limited - retry with backoff
                    await self.circuit_breaker.record_failure()
                    if retries < self.config.max_retries:
                        delay = min(
                            self.config.retry_delay * (2 ** retries),
                            self.config.retry_max_delay
                        )
                        logger.warning(
                            f"Rate limited, retrying in {delay:.1f}s "
                            f"(attempt {retries + 1}/{self.config.max_retries})"
                        )
                        await asyncio.sleep(delay)
                        return await self._make_request(endpoint, payload, retries + 1)
                    raise Exception("Rate limit exceeded after retries")
                
                elif response.status == 401:
                    await self.circuit_breaker.record_failure()
                    raise Exception("API key invalid or unauthorized")
                
                elif response.status == 403:
                    await self.circuit_breaker.record_failure()
                    raise Exception("API key lacks required permissions")
                
                elif response.status == 400:
                    error_text = await response.text()
                    raise Exception(f"Bad request: {error_text}")
                
                elif response.status >= 500:
                    # Server error - retry
                    await self.circuit_breaker.record_failure()
                    if retries < self.config.max_retries:
                        delay = min(
                            self.config.retry_delay * (2 ** retries),
                            self.config.retry_max_delay
                        )
                        logger.warning(
                            f"Server error {response.status}, retrying in "
                            f"{delay:.1f}s (attempt {retries + 1}/{self.config.max_retries})"
                        )
                        await asyncio.sleep(delay)
                        return await self._make_request(endpoint, payload, retries + 1)
                    raise Exception(f"Server error: {response.status}")
                
                else:
                    await self.circuit_breaker.record_failure()
                    raise Exception(f"API error: {response.status}")
                    
        except aiohttp.ClientError as e:
            await self.circuit_breaker.record_failure()
            if retries < self.config.max_retries:
                delay = min(
                    self.config.retry_delay * (2 ** retries),
                    self.config.retry_max_delay
                )
                logger.warning(
                    f"Network error: {e}, retrying in {delay:.1f}s "
                    f"(attempt {retries + 1}/{self.config.max_retries})"
                )
                await asyncio.sleep(delay)
                return await self._make_request(endpoint, payload, retries + 1)
            raise Exception(f"Network error after retries: {str(e)}")
        
        except asyncio.TimeoutError:
            await self.circuit_breaker.record_failure()
            if retries < self.config.max_retries:
                delay = min(
                    self.config.retry_delay * (2 ** retries),
                    self.config.retry_max_delay
                )
                logger.warning(
                    f"Request timeout, retrying in {delay:.1f}s "
                    f"(attempt {retries + 1}/{self.config.max_retries})"
                )
                await asyncio.sleep(delay)
                return await self._make_request(endpoint, payload, retries + 1)
            raise Exception("Request timeout after retries")
    
    async def generate_content(
        self,
        contents: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
        generation_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate content using Ollama Cloud.
        
        Accepts messages in either:
          - Gemini style: {"role": "user", "parts": [{"text": "..."}]}
          - Plain style:  {"role": "user", "content": "..."}
        """
        generation_config = generation_config or {}
        
        # Build messages array
        messages = []
        
        if system_instruction:
            messages.append({
                "role": "system",
                "content": system_instruction
            })
        
        for content in contents:
            role = content.get("role", "user")
            # Support both Gemini-style parts and plain content strings
            if "parts" in content:
                text_content = " ".join(p.get("text", "") for p in content["parts"])
            else:
                text_content = content.get("content", "")
            messages.append({
                "role": role,
                "content": text_content
            })
        
        # Ollama API format: model params go inside "options"
        options = {
            "temperature": generation_config.get("temperature", self.config.temperature),
            "top_p": generation_config.get("top_p", self.config.top_p),
            "num_predict": generation_config.get("max_tokens", self.config.max_tokens),
        }
        if "top_k" in generation_config:
            options["top_k"] = generation_config["top_k"]
        
        payload = {
            "model": self.config.model.value,
            "messages": messages,
            "options": options,
            "stream": False
        }
        
        # Ollama Cloud uses /api/chat (not OpenAI-style /chat/completions)
        result = await self._make_request("api/chat", payload)
        
        # Parse response - handle multiple response formats
        return self._parse_response(result)
    
    def _parse_response(self, result: Dict[str, Any]) -> str:
        """Parse response from various formats"""
        
        # Standard OpenAI-compatible format
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if "message" in choice:
                return choice["message"].get("content", "")
            if "text" in choice:
                return choice["text"]
        
        # Ollama format
        if "message" in result:
            return result["message"].get("content", "")
        
        # Response with content field
        if "content" in result:
            return result["content"]
        
        # Response with text field
        if "text" in result:
            return result["text"]
        
        # Log unexpected format
        logger.warning(f"Unexpected response format: {result}")
        return ""
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate content with simple prompt"""
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        return await self.generate_content(
            messages,
            generation_config=kwargs
        )
    
    async def health_check(self, force: bool = False) -> bool:
        """Check if service is healthy"""
        return await self.health_checker.check_health(force)
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            "circuit_breaker": self.circuit_breaker.stats,
            "rate_limiter": self.rate_limiter.stats,
            "health_checker": self.health_checker.stats,
            "recent_requests": len(self._request_log)
        }


# ============================================================================
# Intent and Sentiment Analysis Prompts
# ============================================================================

INTENT_ANALYSIS_PROMPT = """You are an intent analysis assistant. Analyze the following user message and identify:
1. The primary intent (greeting, farewell, question, request, complaint, praise, confusion, clarification, information, unknown)
2. Any specific topics mentioned
3. Entities mentioned (person names, locations, numbers, dates)

Respond ONLY with valid JSON in this exact format:
{{"intent": "intent_name", "confidence": 0.0-1.0, "topics": ["topic1", "topic2"], "entities": {{"type": "value"}}}}

User message: {message}"""

SENTIMENT_ANALYSIS_PROMPT = """Analyze the sentiment of the following text.
Respond ONLY with valid JSON in this exact format:
{{"sentiment": "very_negative|negative|neutral|positive|very_positive", "score": -1.0 to 1.0, "emotions": ["emotion1", "emotion2"]}}

Text: {text}"""

TRANSLATION_PROMPT = """Translate the following text from {source_lang} to {target_lang}.
Respond ONLY with the translation, no explanations or additional text.

Text: {text}"""

KNOWLEDGE_QUERY_PROMPT = """Based on the following knowledge base entries, answer the user's question.
If the knowledge base doesn't contain relevant information, say so.

Knowledge Base:
{knowledge}

User Question: {question}

Provide a helpful answer based on the knowledge base."""


# ============================================================================
# OllamaCloud Provider Implementation
# ============================================================================

class OllamaCloudProvider:
    """
    OllamaCloud provider for the AI Dialogue System.
    
    Provides NLU, sentiment analysis, translation, and response generation
    using OllamaCloud's API with free tier models.
    
    Features:
    - Circuit breaker for fault tolerance
    - Automatic retry with exponential backoff
    - Connection pooling
    - Health checks
    - Rate limiting
    - Comprehensive error handling with fallbacks
    """
    
    def __init__(self, config: Optional[OllamaCloudConfig] = None):
        self.config = config or OllamaCloudConfig()
        self.client: Optional[OllamaCloudClient] = None
        self._initialized = False
        self._fallback_provider = None
        
        # Default system instruction
        self.system_instruction = """You are an AI assistant for the Fallout Dialogue Creator application.
You help users create dialogue for Fallout 1/2 games.
Be helpful, friendly, and knowledgeable about game mechanics.
Respond in a conversational manner."""
        
        logger.info("OllamaCloudProvider created")
    
    @property
    def is_available(self) -> bool:
        """Check if provider is available"""
        if not self._initialized or self.client is None:
            return False
        return self.client.circuit_breaker.is_available
    
    @property
    def is_healthy(self) -> bool:
        """Check if provider is healthy"""
        if not self.client:
            return False
        return self.client.circuit_breaker.state == CircuitState.CLOSED
    
    async def initialize(self):
        """Initialize the provider"""
        if self._initialized:
            logger.warning("OllamaCloudProvider already initialized")
            return
        
        if not self.config.api_key:
            logger.warning(
                "No OllamaCloud API key provided. "
                "Set OLLAMA_API_KEY environment variable or provide in config. "
                "Provider will run in fallback mode."
            )
            self._initialized = False
            return
        
        try:
            self.client = OllamaCloudClient(self.config)
            
            # First, get list of available models
            try:
                async with aiohttp.ClientSession() as session:
                    headers = self.client._get_headers()
                    async with session.get(
                        "https://ollama.com/api/tags",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            all_models = data.get("models", [])
                            
                            if all_models:
                                # Use first available model
                                # First try to find a cloud model, otherwise use first available
                                cloud_model = next(
                                    (m.get("name", "") for m in all_models
                                     if str(m.get("name", "")).endswith("-cloud")),
                                    None
                                )
                                if cloud_model:
                                    self.config.model = OllamaCloudModel(cloud_model)
                                    logger.info(f"Using cloud model: {self.config.model.value}")
                                else:
                                    # Use any available model
                                    first_model = all_models[0].get("name", "")
                                    if first_model:
                                        # Try to match to enum or create a string-based model
                                        try:
                                            self.config.model = OllamaCloudModel(first_model)
                                        except ValueError:
                                            # Manually set the model value
                                            self.config.model = OllamaCloudModel.GPT_OSS_32B
                                            self.config.model._value_ = first_model
                                        logger.info(f"Using available model: {first_model}")
                            else:
                                logger.warning("No models available")
                                self._initialized = False
                                return
                        else:
                            logger.warning(f"Model list request failed: {resp.status}")
            except Exception as e:
                logger.warning(f"Could not get model list: {e}")
            
            # Try to generate with the configured model
            await self.client.generate("Hi", max_tokens=5)
            self._initialized = True
            logger.info("OllamaCloud provider initialized successfully")
            logger.info(f"Using model: {self.config.model.value}")
                
        except Exception as e:
            logger.error(f"Failed to initialize OllamaCloud provider: {e}")
            self._initialized = False
            # Don't throw - allow fallback mode
    
    async def shutdown(self):
        """Shutdown the provider"""
        if self.client:
            await self.client.close()
        self._initialized = False
        logger.info("OllamaCloudProvider shutdown complete")
    
    def set_fallback_provider(self, provider):
        """Set fallback provider for when OllamaCloud is unavailable"""
        self._fallback_provider = provider
        logger.info(f"Fallback provider set: {type(provider).__name__}")
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from response text with multiple fallback strategies"""
        
        # Strategy 1: Try to extract JSON from markdown code blocks
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        
        # Strategy 2: Try to extract JSON from markdown code blocks (no language)
        json_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        
        # Strategy 3: Try to find JSON object anywhere in text
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Strategy 4: Try to parse entire text as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Strategy 5: Try to find key-value patterns
        result = {}
        
        # Extract intent
        intent_match = re.search(r'"intent"\s*:\s*"([^"]+)"', text, re.IGNORECASE)
        if intent_match:
            result["intent"] = intent_match.group(1)
        
        # Extract confidence
        conf_match = re.search(r'"confidence"\s*:\s*([0-9.]+)', text, re.IGNORECASE)
        if conf_match:
            try:
                result["confidence"] = float(conf_match.group(1))
            except ValueError:
                pass
        
        # Extract sentiment
        sent_match = re.search(r'"sentiment"\s*:\s*"([^"]+)"', text, re.IGNORECASE)
        if sent_match:
            result["sentiment"] = sent_match.group(1)
        
        # Extract score
        score_match = re.search(r'"score"\s*:\s*([-0-9.]+)', text, re.IGNORECASE)
        if score_match:
            try:
                result["score"] = float(score_match.group(1))
            except ValueError:
                pass
        
        # Extract topics array
        topics_match = re.search(r'"topics"\s*:\s*\[(.*?)\]', text, re.DOTALL)
        if topics_match:
            topics_text = topics_match.group(1)
            topics = re.findall(r'"([^"]+)"', topics_text)
            result["topics"] = topics
        
        # Extract entities object
        entities_match = re.search(r'"entities"\s*:\s*\{(.*?)\}', text, re.DOTALL)
        if entities_match:
            entities_text = entities_match.group(1)
            entities = {}
            entity_pairs = re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', entities_text)
            for key, value in entity_pairs:
                entities[key] = value
            result["entities"] = entities
        
        # Extract emotions array
        emotions_match = re.search(r'"emotions"\s*:\s*\[(.*?)\]', text, re.DOTALL)
        if emotions_match:
            emotions_text = emotions_match.group(1)
            emotions = re.findall(r'"([^"]+)"', emotions_text)
            result["emotions"] = emotions
        
        if result:
            logger.debug(f"Parsed JSON using fallback strategies: {result}")
        
        return result
    
    # ========================================================================
    # NLU Methods
    # ========================================================================
    
    async def recognize_intent(
        self,
        text: str,
        context: Optional[Any] = None
    ) -> Tuple[str, float, Dict[str, Any], List[str]]:
        """
        Recognize user intent using OllamaCloud.
        
        Returns:
            Tuple of (intent_type, confidence, entities, topics)
        """
        if not self.is_available:
            logger.warning("OllamaCloud unavailable, using fallback provider")
            if self._fallback_provider:
                return await self._fallback_provider.recognize_intent(text, context)
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
            
            logger.debug(f"Intent recognized: {intent} (confidence: {confidence:.2f})")
            
            return (intent, confidence, entities, topics)
            
        except Exception as e:
            logger.error(f"Intent recognition error: {e}")
            if self._fallback_provider:
                return await self._fallback_provider.recognize_intent(text, context)
            return ("unknown", 0.0, {}, [])
    
    async def analyze_sentiment(
        self,
        text: str
    ) -> Tuple[str, float]:
        """
        Analyze sentiment using OllamaCloud.
        
        Returns:
            Tuple of (sentiment_type, score)
        """
        if not self.is_available:
            logger.warning("OllamaCloud unavailable, using fallback provider")
            if self._fallback_provider:
                return await self._fallback_provider.analyze_sentiment(text)
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
            
            logger.debug(f"Sentiment analyzed: {sentiment} (score: {score:.2f})")
            
            return (sentiment, score)
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            if self._fallback_provider:
                return await self._fallback_provider.analyze_sentiment(text)
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
        """Translate text using OllamaCloud"""
        if not self.is_available:
            logger.warning("OllamaCloud unavailable, using fallback provider")
            if self._fallback_provider:
                result = await self._fallback_provider.translate(text, source_lang, target_lang)
                return result.translated_text if hasattr(result, 'translated_text') else result
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
                result = await self._fallback_provider.translate(text, source_lang, target_lang)
                return result.translated_text if hasattr(result, 'translated_text') else result
            return text
    
    async def detect_language(self, text: str) -> str:
        """Detect language of text"""
        if not self.is_available:
            logger.warning("OllamaCloud unavailable, using fallback provider")
            if self._fallback_provider:
                return await self._fallback_provider.detect_language(text)
            return "en"
        
        # Simple language detection via prompt
        prompt = f"What language is this text? Respond with just the 2-letter language code.\n\nText: {text[:200]}"
        
        try:
            response = await self.client.generate_content(
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
                system_instruction="You are a language detection assistant."
            )
            
            lang_code = response.strip().lower()
            # Validate it's a 2-letter code
            if len(lang_code) == 2 and lang_code.isalpha():
                return lang_code
            
            # Try to extract from response
            match = re.search(r'\b([a-z]{2})\b', lang_code)
            if match:
                return match.group(1)
            
            return "en"
            
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            if self._fallback_provider:
                return await self._fallback_provider.detect_language(text)
            return "en"
    
    # ========================================================================
    # Response Generation
    # ========================================================================
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
        persona: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using OllamaCloud.
        
        Args:
            prompt: The user's prompt
            context: Conversation context
            config: Response configuration
            persona: Persona configuration
            
        Returns:
            Dictionary with generated response
        """
        if not self.is_available:
            logger.warning("OllamaCloud unavailable, using fallback provider")
            if self._fallback_provider:
                return await self._fallback_provider.generate_response(
                    prompt, context, config, persona
                )
            return {"text": "Service unavailable", "error": "OllamaCloud unavailable"}
        
        try:
            # Build system instruction with persona
            system = self.system_instruction
            if persona:
                name = persona.get("name", "Assistant")
                traits = ", ".join(persona.get("traits", []))
                style = persona.get("speaking_style", "neutral")
                
                system = f"""You are {name}. 
                {persona.get('description', '')}
                Your traits: {traits}
                Speaking style: {style}
                {persona.get('backstory', '')}
                
                {self.system_instruction}"""
            
            # Build generation config
            generation_config = {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "max_tokens": self.config.max_tokens
            }
            
            if config:
                generation_config.update(config)
            
            # Build context from conversation history
            contents = []
            
            if context and hasattr(context, 'history'):
                # Add conversation history
                for msg in context.history[-5:]:  # Last 5 messages
                    contents.append({
                        "role": msg.get("role", "user"),
                        "parts": [{"text": msg.get("content", "")}]
                    })
            
            # Add current prompt
            contents.append({
                "role": "user",
                "parts": [{"text": prompt}]
            })
            
            response = await self.client.generate_content(
                contents=contents,
                system_instruction=system,
                generation_config=generation_config
            )
            
            return {
                "text": response,
                "model": self.config.model.value,
                "provider": "ollama_cloud"
            }
            
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            if self._fallback_provider:
                return await self._fallback_provider.generate_response(
                    prompt, context, config, persona
                )
            return {"text": "Error generating response", "error": str(e)}
    
    # ========================================================================
    # Health and Status
    # ========================================================================
    
    async def check_health(self, force: bool = False) -> bool:
        """Check if the service is healthy"""
        if not self.client:
            return False
        return await self.client.health_check(force)
    
    @property
    def status(self) -> Dict[str, Any]:
        """Get provider status"""
        return {
            "initialized": self._initialized,
            "available": self.is_available,
            "healthy": self.is_healthy,
            "model": self.config.model.value if self._initialized else None,
            "circuit_breaker": self.client.circuit_breaker.stats if self.client else None,
            "rate_limiter": self.client.rate_limiter.stats if self.client else None
        }
    
    async def reset_circuit(self):
        """Manually reset the circuit breaker"""
        if self.client:
            await self.client.circuit_breaker.reset()
            logger.info("Circuit breaker manually reset")


# ============================================================================
# Factory Functions
# ============================================================================

def create_ollama_provider(
    api_key: Optional[str] = None,
    model: OllamaCloudModel = OllamaCloudModel.GPT_OSS_32B,
    **kwargs
) -> OllamaCloudProvider:
    """
    Create an OllamaCloud provider with configuration.
    
    Args:
        api_key: OllamaCloud API key (optional, can use env var)
        model: Model to use
        **kwargs: Additional configuration options
        
    Returns:
        Configured OllamaCloudProvider
    """
    config = OllamaCloudConfig(
        api_key=api_key or os.environ.get("OLLAMA_API_KEY", ""),
        model=model,
        **kwargs
    )
    return OllamaCloudProvider(config)


async def create_initialized_ollama_provider(
    api_key: Optional[str] = None,
    model: OllamaCloudModel = OllamaCloudModel.GPT_OSS_32B,
    **kwargs
) -> OllamaCloudProvider:
    """
    Create and initialize an OllamaCloud provider.
    
    Args:
        api_key: OllamaCloud API key (optional, can use env var)
        model: Model to use
        **kwargs: Additional configuration options
        
    Returns:
        Initialized OllamaCloudProvider
    """
    provider = create_ollama_provider(api_key, model, **kwargs)
    await provider.initialize()
    return provider


# Alias for compatibility with tests
create_ollama_provider_async = create_initialized_ollama_provider


# ============================================================================
# Provider Registry
# ============================================================================

class ProviderRegistry:
    """
    Registry for managing multiple AI providers with fallback.
    """
    
    def __init__(self):
        self._providers: Dict[str, Any] = {}
        self._primary_provider: Optional[str] = None
        self._lock = asyncio.Lock()
    
    def register(self, name: str, provider: Any, set_primary: bool = False):
        """Register a provider"""
        self._providers[name] = provider
        if set_primary or not self._primary_provider:
            self._primary_provider = name
        logger.info(f"Registered provider: {name}")
    
    def get(self, name: str) -> Optional[Any]:
        """Get a provider by name"""
        return self._providers.get(name)
    
    @property
    def primary(self) -> Optional[Any]:
        """Get the primary provider"""
        if self._primary_provider:
            return self._providers.get(self._primary_provider)
        return None
    
    async def get_available_provider(self) -> Optional[Any]:
        """Get first available provider with fallback chain"""
        # Try primary first
        if self.primary and self.primary.is_available:
            return self.primary
        
        # Try other providers
        for name, provider in self._providers.items():
            if provider.is_available:
                logger.info(f"Using fallback provider: {name}")
                return provider
        
        return None
    
    @property
    def status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        return {
            name: provider.status if hasattr(provider, 'status') else {"available": provider.is_available}
            for name, provider in self._providers.items()
        }


# Create default registry instance
_default_registry = ProviderRegistry()


def get_default_registry() -> ProviderRegistry:
    """Get the default provider registry"""
    return _default_registry
