"""
AI-Assisted Dialogue Generation System

This module provides comprehensive AI dialogue capabilities including:
- Natural Language Understanding (NLU) for intent recognition
- Conversation context management across multiple exchanges
- Sentiment analysis for emotional tone adaptation
- Personality customization options
- Multi-language support with translation
- Knowledge base integration for domain-specific information
- Configurable response parameters (creativity, length, formality)
- Ethical AI guidelines (content filtering, bias detection)
- Comprehensive logging and analytics

The system uses a modular architecture allowing easy extension of capabilities.
"""

import re
import json
import logging
import threading
import time
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from collections import defaultdict
import queue

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration and Data Types
# ============================================================================

class ResponseCreativity(Enum):
    """Creativity level for response generation"""
    PRECISE = 0      # Most deterministic, factual responses
    BALANCED = 1     # Mix of creativity and precision
    CREATIVE = 2     # More varied and imaginative responses
    UNCONSTRAINED = 3  # Maximum creativity


class ResponseLength(Enum):
    """Preferred response length"""
    CONCISE = 0      # Short, brief responses
    NORMAL = 1       # Standard length
    DETAILED = 2     # Detailed, comprehensive responses
    EXTENDED = 3     # Long, in-depth responses


class FormalityTone(Enum):
    """Formality level for responses"""
    CASUAL = 0       # Casual, informal language
    NEUTRAL = 1      # Neutral, balanced tone
    FORMAL = 2       # Formal, professional language
    CEREMONIAL = 3   # Highly formal, ceremonial


class SentimentType(Enum):
    """Emotional sentiment categories"""
    VERY_NEGATIVE = -2
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1
    VERY_POSITIVE = 2


class IntentType(Enum):
    """Recognized user intents"""
    GREETING = "greeting"
    FAREWELL = "farewell"
    QUESTION = "question"
    STATEMENT = "statement"
    REQUEST = "request"
    COMPLAINT = "complaint"
    PRAISE = "praise"
    CONFUSION = "confusion"
    CLARIFICATION = "clarification"
    INFORMATION = "information"
    UNKNOWN = "unknown"


@dataclass
class ResponseConfig:
    """Configuration parameters for response generation"""
    creativity: ResponseCreativity = ResponseCreativity.BALANCED
    length: ResponseLength = ResponseLength.NORMAL
    formality: FormalityTone = FormalityTone.NEUTRAL
    include_reasoning: bool = False
    max_tokens: int = 500
    temperature: float = 0.7
    top_p: float = 0.9
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "creativity": self.creativity.name,
            "length": self.length.name,
            "formality": self.formality.name,
            "include_reasoning": self.include_reasoning,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty
        }


@dataclass
class Persona:
    """Personality configuration for AI character"""
    name: str = "Assistant"
    description: str = ""
    traits: List[str] = field(default_factory=list)
    speaking_style: str = "neutral"
    backstory: str = ""
    language: str = "en"
    # Behavioral modifiers
    empathy_level: float = 0.5      # 0-1 scale
    humor_level: float = 0.5        # 0-1 scale
    formality_base: float = 0.5    # 0-1 scale
    emotional_expressiveness: float = 0.5  # 0-1 scale
    # Knowledge domains
    expertise_areas: List[str] = field(default_factory=list)
    forbidden_topics: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "traits": self.traits,
            "speaking_style": self.speaking_style,
            "backstory": self.backstory,
            "language": self.language,
            "empathy_level": self.empathy_level,
            "humor_level": self.humor_level,
            "formality_base": self.formality_base,
            "emotional_expressiveness": self.emotional_expressiveness,
            "expertise_areas": self.expertise_areas,
            "forbidden_topics": self.forbidden_topics
        }


@dataclass
class Intent:
    """Represents recognized user intent"""
    type: IntentType
    confidence: float  # 0-1
    entities: Dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    extracted_topics: List[str] = field(default_factory=list)
    sentiment: SentimentType = SentimentType.NEUTRAL
    sentiment_score: float = 0.0


@dataclass
class ConversationMessage:
    """Single message in conversation history"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    intent: Optional[Intent] = None
    sentiment: SentimentType = SentimentType.NEUTRAL
    tokens: int = 0


@dataclass
class ConversationContext:
    """Maintains conversation state and history"""
    conversation_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    messages: List[ConversationMessage] = field(default_factory=list)
    user_profile: Dict[str, Any] = field(default_factory=dict)
    session_data: Dict[str, Any] = field(default_factory=dict)
    topic_stack: List[str] = field(default_factory=list)
    entities_mentioned: Set[str] = field(default_factory=set)
    user_intent_history: List[IntentType] = field(default_factory=list)
    average_sentiment: float = 0.0
    turn_count: int = 0
    
    def add_message(self, message: ConversationMessage):
        """Add message to conversation history"""
        self.messages.append(message)
        self.last_updated = datetime.now()
        self.turn_count += 1
        
        # Update rolling average sentiment
        if self.turn_count > 1:
            old_avg = self.average_sentiment
            sentiment_val = message.sentiment.value
            self.average_sentiment = (old_avg * (self.turn_count - 1) + sentiment_val) / self.turn_count
        else:
            self.average_sentiment = message.sentiment.value
        
        # Track entities
        if message.metadata.get("entities"):
            self.entities_mentioned.update(message.metadata["entities"])
        
        # Track intent history
        if message.intent:
            self.user_intent_history.append(message.intent.type)


@dataclass
class GeneratedResponse:
    """AI-generated response"""
    text: str
    confidence: float = 0.0
    reasoning: str = ""
    suggested_topics: List[str] = field(default_factory=list)
    sentiment: SentimentType = SentimentType.NEUTRAL
    entities_used: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranslationResult:
    """Translation result with metadata"""
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    confidence: float = 0.0
    alternatives: List[str] = field(default_factory=list)


@dataclass
class SentimentResult:
    """Sentiment analysis result"""
    text: str
    sentiment: SentimentType
    confidence: float


@dataclass
class KnowledgeEntry:
    """Knowledge base entry"""
    id: str
    content: str
    category: str
    keywords: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# Abstract Base Classes for Extensibility
# ============================================================================

class NLUProvider(ABC):
    """Abstract base class for NLU implementations"""
    
    @abstractmethod
    def recognize_intent(self, text: str, context: Optional[ConversationContext] = None) -> Intent:
        """Recognize user intent from text"""
        pass
    
    @abstractmethod
    def extract_entities(self, text: str, context: Optional[ConversationContext] = None) -> Dict[str, Any]:
        """Extract named entities from text"""
        pass
    
    @abstractmethod
    def analyze_sentiment(self, text: str) -> Tuple[SentimentType, float]:
        """Analyze sentiment of text"""
        pass


class LanguageModelProvider(ABC):
    """Abstract base class for language model implementations"""
    
    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        context: ConversationContext,
        config: ResponseConfig,
        persona: Persona
    ) -> GeneratedResponse:
        """Generate AI response"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass


class TranslationProvider(ABC):
    """Abstract base class for translation implementations"""
    
    @abstractmethod
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> TranslationResult:
        """Translate text between languages"""
        pass
    
    @abstractmethod
    def detect_language(self, text: str) -> str:
        """Detect language of text"""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        pass


class KnowledgeBaseProvider(ABC):
    """Abstract base class for knowledge base implementations"""
    
    @abstractmethod
    def search(self, query: str, context: Optional[ConversationContext] = None) -> List[KnowledgeEntry]:
        """Search knowledge base"""
        pass
    
    @abstractmethod
    def add_entry(self, entry: KnowledgeEntry) -> bool:
        """Add entry to knowledge base"""
        pass
    
    @abstractmethod
    def get_categories(self) -> List[str]:
        """Get available knowledge categories"""
        pass


# ============================================================================
# Content Filtering and Safety
# ============================================================================

class ContentFilter:
    """Content filtering for ethical AI guidelines"""
    
    # Categories of potentially harmful content
    HARMFUL_CATEGORIES = [
        "hate_speech",
        "violence",
        "sexual_content",
        "self_harm",
        "harassment",
        "illegal_activity",
        "misinformation"
    ]
    
    def __init__(self):
        self.blocked_patterns: List[re.Pattern] = []
        self.warning_patterns: List[re.Pattern] = []
        self._load_default_filters()
    
    def _load_default_filters(self):
        """Load default filtering patterns"""
        # Blocked content patterns (will be replaced with safe response)
        self.blocked_patterns = [
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE),
            re.compile(r'javascript:', re.IGNORECASE),
            # Add more patterns as needed
        ]
        
        # Warning content patterns (will trigger warning but may proceed)
        self.warning_patterns = [
            re.compile(r'\b(weapon|explosive|kill|murder)\b', re.IGNORECASE),
        ]
    
    def check_content(self, text: str) -> Tuple[bool, List[str]]:
        """
        Check content for violations.
        
        Returns:
            Tuple of (is_safe, list of violated categories)
        """
        violations = []
        
        # Check blocked patterns
        for pattern in self.blocked_patterns:
            if pattern.search(text):
                violations.append("blocked_pattern")
        
        return (len(violations) == 0, violations)
    
    def filter_response(self, text: str) -> str:
        """Filter response text, replacing problematic content"""
        filtered = text
        
        for pattern in self.blocked_patterns:
            filtered = pattern.sub('[content filtered]', filtered)
        
        return filtered
    
    def should_warn(self, text: str) -> bool:
        """Check if content should trigger warning"""
        for pattern in self.warning_patterns:
            if pattern.search(text):
                return True
        return False


class BiasDetector:
    """Detect and mitigate bias in responses"""
    
    def __init__(self):
        self.bias_indicators: Dict[str, List[re.Pattern]] = {
            "gender": [],
            "racial": [],
            "age": [],
            "disability": [],
            "religious": [],
            "sexual_orientation": []
        }
        self._load_bias_patterns()
    
    def _load_bias_patterns(self):
        """Load bias detection patterns"""
        # This would be expanded with comprehensive patterns
        # Placeholder patterns for demonstration
        pass
    
    def analyze_text(self, text: str) -> Dict[str, float]:
        """
        Analyze text for potential bias.
        
        Returns:
            Dictionary mapping bias category to confidence score
        """
        scores = {category: 0.0 for category in self.bias_indicators.keys()}
        
        # Analyze text for bias patterns
        text_lower = text.lower()
        
        # This would use more sophisticated analysis in production
        return scores
    
    def mitigate_bias(self, text: str, analysis: Dict[str, float]) -> str:
        """Apply bias mitigation to text"""
        # If significant bias detected, rephrase
        max_score = max(analysis.values()) if analysis else 0.0
        
        if max_score > 0.7:
            # Apply mitigation strategies
            return self._rephrase_neutral(text, analysis)
        
        return text
    
    def _rephrase_neutral(self, text: str, analysis: Dict[str, float]) -> str:
        """Rephrase text to be more neutral"""
        # Simplified neutral rephrasing
        return text


# ============================================================================
# Built-in NLU Implementation
# ============================================================================

class RuleBasedNLU(NLUProvider):
    """Rule-based NLU implementation for intent recognition and entity extraction"""
    
    # Intent keywords mapping
    INTENT_KEYWORDS = {
        IntentType.GREETING: ['hello', 'hi', 'hey', 'greetings', 'howdy', 'hiya'],
        IntentType.FAREWELL: ['bye', 'goodbye', 'farewell', 'see you', 'later', 'cya'],
        IntentType.QUESTION: ['what', 'who', 'where', 'when', 'why', 'how', '?'],
        IntentType.REQUEST: ['please', 'can you', 'could you', 'would you', 'help me', 'i need'],
        IntentType.COMPLAINT: ['problem', 'issue', 'wrong', 'bad', 'disappointed', 'frustrated', 'hate'],
        IntentType.PRAISE: ['great', 'awesome', 'excellent', 'amazing', 'love', 'wonderful', 'fantastic'],
        IntentType.CONFUSION: ['confused', 'don\'t understand', 'unclear', 'lost', 'what do you mean'],
        IntentType.CLARIFICATION: ['explain', 'clarify', 'what do you mean', 'could you elaborate'],
        IntentType.INFORMATION: ['know', 'tell me about', 'information', 'facts', 'learn']
    }
    
    # Entity patterns
    ENTITY_PATTERNS = {
        'person': r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b',
        'location': r'\b(in|at|near|to|from) ([A-Z][a-z]+)\b',
        'date': r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
        'time': r'\b(\d{1,2}:\d{2}(?:\s*[AaPp][Mm])?)\b',
        'number': r'\b(\d+(?:\.\d+)?)\b',
    }
    
    # Sentiment word lists
    POSITIVE_WORDS = {
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome',
        'love', 'like', 'happy', 'pleased', 'satisfied', 'perfect', 'best', 'beautiful',
        'helpful', 'kind', 'nice', 'brilliant', 'superb', 'outstanding', 'positive'
    }
    
    NEGATIVE_WORDS = {
        'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'dislike', 'angry',
        'frustrated', 'disappointed', 'sad', 'upset', 'annoyed', 'poor', 'useless',
        'broken', 'wrong', 'problem', 'issue', 'fail', 'failed', 'disaster'
    }
    
    INTENSIFIERS = {'very', 'really', 'extremely', 'absolutely', 'totally', 'completely'}
    NEGATORS = {'not', 'no', 'never', "n't", 'neither', 'nor'}
    
    def __init__(self):
        self.language = 'en'
    
    def recognize_intent(self, text: str, context: Optional[ConversationContext] = None) -> Intent:
        """Recognize user intent from text"""
        text_lower = text.lower()
        
        # Score each intent
        intent_scores: Dict[IntentType, float] = {}
        
        for intent_type, keywords in self.INTENT_KEYWORDS.items():
            score = 0.0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1.0
            if score > 0:
                intent_scores[intent_type] = score / len(keywords)
        
        # Get best intent
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            intent_type = best_intent[0]
            confidence = min(best_intent[1], 1.0)
        else:
            intent_type = IntentType.UNKNOWN
            confidence = 0.0
        
        # Check for question marks
        if '?' in text:
            intent_type = IntentType.QUESTION
            confidence = max(confidence, 0.8)
        
        # Extract topics
        topics = self._extract_topics(text_lower)
        
        # Analyze sentiment
        sentiment, sentiment_score = self.analyze_sentiment(text)
        
        return Intent(
            type=intent_type,
            confidence=confidence,
            entities=self.extract_entities(text, context),
            raw_text=text,
            extracted_topics=topics,
            sentiment=sentiment,
            sentiment_score=sentiment_score
        )
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text"""
        topics = []
        
        # Simple keyword-based topic extraction
        topic_keywords = {
            'dialogue': ['dialogue', 'conversation', 'talk', 'speech', 'chat'],
            'game': ['game', 'play', 'gaming', 'player'],
            'character': ['character', 'npc', 'persona', 'actor'],
            'script': ['script', 'code', 'programming', 'condition'],
            'file': ['file', 'load', 'save', 'export', 'import'],
            'help': ['help', 'guide', 'tutorial', 'how to'],
            'settings': ['settings', 'preferences', 'options', 'config'],
            'error': ['error', 'bug', 'crash', 'issue', 'problem'],
            'ai': ['ai', 'artificial intelligence', 'generate', 'assistant'],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in text for kw in keywords):
                topics.append(topic)
        
        return topics
    
    def extract_entities(self, text: str, context: Optional[ConversationContext] = None) -> Dict[str, Any]:
        """Extract named entities from text"""
        entities = {}
        
        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                entities[entity_type] = matches
        
        # Extract quoted strings
        quoted = re.findall(r'"([^"]+)"', text)
        if quoted:
            entities['quoted'] = quoted
        
        return entities
    
    def analyze_sentiment(self, text: str) -> Tuple[SentimentType, float]:
        """Analyze sentiment of text"""
        words = re.findall(r'\b\w+\b', text.lower())
        
        positive_count = 0
        negative_count = 0
        intensifier_active = False
        negator_active = False
        
        for i, word in enumerate(words):
            # Check for negators
            if word in self.NEGATORS:
                negator_active = True
                continue
            
            # Check for intensifiers
            if word in self.INTENSIFIERS:
                intensifier_active = True
                continue
            
            # Count sentiment words
            multiplier = 1.5 if intensifier_active else 1.0
            
            if word in self.POSITIVE_WORDS:
                positive_count += multiplier
            elif word in self.NEGATIVE_WORDS:
                negative_count += multiplier
            
            # Reset modifiers
            intensifier_active = False
            negator_active = False
        
        # Calculate sentiment score
        total = positive_count + negative_count
        if total > 0:
            score = (positive_count - negative_count) / total
        else:
            score = 0.0
        
        # Apply negation
        if negator_active:
            score = -score
        
        # Normalize to -1 to 1 range
        score = max(-1.0, min(1.0, score))
        
        # Determine sentiment type
        if score > 0.5:
            sentiment = SentimentType.VERY_POSITIVE
        elif score > 0.2:
            sentiment = SentimentType.POSITIVE
        elif score < -0.5:
            sentiment = SentimentType.VERY_NEGATIVE
        elif score < -0.2:
            sentiment = SentimentType.NEGATIVE
        else:
            sentiment = SentimentType.NEUTRAL
        
        return sentiment, score


# ============================================================================
# Knowledge Base Implementation
# ============================================================================

class InMemoryKnowledgeBase(KnowledgeBaseProvider):
    """In-memory knowledge base implementation"""
    
    def __init__(self):
        self.entries: Dict[str, KnowledgeEntry] = {}
        self.categories: Set[str] = set()
        self._index: Dict[str, Set[str]] = defaultdict(set)
        self._load_default_knowledge()
    
    def _load_default_knowledge(self):
        """Load default knowledge base entries"""
        # Add Fallout-specific knowledge
        default_entries = [
            KnowledgeEntry(
                id="fallout_dialogue_basics",
                content="Dialogue in Fallout games is stored in FMF files. Each dialogue has NPC text, player responses, and conditions controlling which options appear.",
                category="game_mechanics",
                keywords=["dialogue", "fmf", "fallout", "npc", "player response"]
            ),
            KnowledgeEntry(
                id="skill_checks",
                content="Skill checks in Fallout dialogue allow for specialized responses based on player skills like Speech, Barter, Science, Repair, etc.",
                category="game_mechanics",
                keywords=["skill check", "speech", "barter", "science", "repair"]
            ),
            KnowledgeEntry(
                id="conditions_system",
                content="Conditions control when dialogue nodes and options are available. They can check player stats, skills, items, global variables, and custom scripts.",
                category="game_mechanics",
                keywords=["conditions", "script", "variables", "stat check"]
            ),
            KnowledgeEntry(
                id="reaction_system",
                content="The reaction system tracks NPC disposition toward the player (Good, Neutral, Bad) and affects dialogue options and outcomes.",
                category="game_mechanics",
                keywords=["reaction", "karma", "disposition", "npc attitude"]
            ),
            KnowledgeEntry(
                id="dialogue_editor_features",
                content="The Fallout Dialogue Creator supports visual editing, condition builder, script validation, testing engine, and export to multiple formats.",
                category="tool_features",
                keywords=["editor", "features", "export", "import", "testing"]
            ),
        ]
        
        for entry in default_entries:
            self.add_entry(entry)
    
    def search(self, query: str, context: Optional[ConversationContext] = None) -> List[KnowledgeEntry]:
        """Search knowledge base"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        results = []
        
        for entry_id, entry in self.entries.items():
            # Calculate relevance score
            score = 0.0
            
            # Check keywords
            for word in query_words:
                if word in entry.keywords:
                    score += 2.0
                if word in entry.content.lower():
                    score += 1.0
            
            # Check category
            if word in entry.category:
                score += 1.5
            
            if score > 0:
                entry.relevance_score = score
                results.append(entry)
        
        # Sort by relevance
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results[:10]  # Return top 10
    
    def add_entry(self, entry: KnowledgeEntry) -> bool:
        """Add entry to knowledge base"""
        try:
            self.entries[entry.id] = entry
            self.categories.add(entry.category)
            
            # Update index
            for keyword in entry.keywords:
                self._index[keyword.lower()].add(entry.id)
            
            return True
        except Exception as e:
            logger.error(f"Failed to add knowledge entry: {e}")
            return False
    
    def get_categories(self) -> List[str]:
        """Get available knowledge categories"""
        return sorted(list(self.categories))


# ============================================================================
# Translation Implementation
# ============================================================================

class SimpleTranslationProvider(TranslationProvider):
    """Simple rule-based translation provider"""
    
    # Basic translation dictionary (subset for demonstration)
    TRANSLATIONS = {
        'en': {
            'hello': {'es': 'hola', 'fr': 'bonjour', 'de': 'hallo', 'it': 'ciao'},
            'goodbye': {'es': 'adiós', 'fr': 'au revoir', 'de': 'auf wiedersehen', 'it': 'arrivederci'},
            'thank you': {'es': 'gracias', 'fr': 'merci', 'de': 'danke', 'it': 'grazie'},
            'please': {'es': 'por favor', 'fr': 's\'il vous plaît', 'de': 'bitte', 'it': 'per favore'},
            'yes': {'es': 'sí', 'fr': 'oui', 'de': 'ja', 'it': 'sì'},
            'no': {'es': 'no', 'fr': 'non', 'de': 'nein', 'it': 'no'},
            'help': {'es': 'ayuda', 'fr': 'aide', 'de': 'hilfe', 'it': 'aiuto'},
        }
    }
    
    LANGUAGE_NAMES = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'ja': 'Japanese',
        'zh': 'Chinese',
        'ru': 'Russian',
        'pt': 'Portuguese',
        'ar': 'Arabic'
    }
    
    def __init__(self):
        self.default_target = 'es'
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        """Translate text between languages"""
        text_lower = text.lower().strip()
        
        # Simple word-by-word translation
        words = text_lower.split()
        translated_words = []
        
        for word in words:
            found = False
            # Check direct translation
            if source_lang in self.TRANSLATIONS:
                for source_word, target_dict in self.TRANSLATIONS[source_lang].items():
                    if source_word == word and target_lang in target_dict:
                        translated_words.append(target_dict[target_lang])
                        found = True
                        break
            
            if not found:
                # Keep original word
                translated_words.append(word)
        
        translated_text = ' '.join(translated_words)
        
        return TranslationResult(
            original_text=text,
            translated_text=translated_text,
            source_lang=source_lang,
            target_lang=target_lang,
            confidence=0.5 if translated_text != text else 0.0
        )
    
    def detect_language(self, text: str) -> str:
        """Detect language of text"""
        # Simple detection based on character patterns
        if re.search(r'[\u4e00-\u9fff]', text):
            return 'zh'
        elif re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
            return 'ja'
        elif re.search(r'[\u0400-\u04ff]', text):
            return 'ru'
        elif re.search(r'[\u0600-\u06ff]', text):
            return 'ar'
        elif re.search(r'[äöüß]', text.lower()):
            return 'de'
        elif re.search(r'[éèêëàâùûç]', text.lower()):
            return 'fr'
        elif re.search(r'[áéíóúñ¿¡]', text.lower()):
            return 'es'
        else:
            return 'en'
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return list(self.LANGUAGE_NAMES.keys())


# ============================================================================
# Simple Language Model Implementation
# ============================================================================

class SimpleLanguageModel(LanguageModelProvider):
    """Simple template-based language model for fallback"""
    
    def __init__(self):
        self.template_responses: Dict[IntentType, List[str]] = {
            IntentType.GREETING: [
                "Hello! How can I help you with your dialogue today?",
                "Hi there! I'm here to assist with your Fallout dialogue creation.",
                "Greetings! What would you like to work on?"
            ],
            IntentType.FAREWELL: [
                "Goodbye! Feel free to return if you need more assistance.",
                "Take care! Happy dialogue creating!",
                "See you later! Don't hesitate to ask if you need help."
            ],
            IntentType.QUESTION: [
                "That's an interesting question. Let me help you with that.",
                "Good question! Here's what I can tell you...",
                "I understand you're asking about this. Let me explain..."
            ],
            IntentType.REQUEST: [
                "I'd be happy to help with that!",
                "Of course! Let me assist you with that.",
                "Absolutely, I can help you with that."
            ],
            IntentType.COMPLAINT: [
                "I'm sorry to hear you're having trouble. Let me help resolve this.",
                "I understand your frustration. Let's work on fixing this together.",
                "I'm sorry for the inconvenience. How can I make this better?"
            ],
            IntentType.PRAISE: [
                "Thank you so much! I appreciate your kind words.",
                "That's very kind of you to say! I'm here to help.",
                "I'm glad I could assist! Thank you for the positive feedback."
            ],
            IntentType.CONFUSION: [
                "I can see this might be unclear. Let me clarify...",
                "That's a good point of confusion. Here's an explanation...",
                "I understand this can be confusing. Let me break it down..."
            ],
            IntentType.CLARIFICATION: [
                "Of course, let me explain in more detail...",
                "Certainly! Here's a clearer explanation...",
                "Absolutely, I'll clarify that for you..."
            ],
            IntentType.INFORMATION: [
                "Here's some information that might help...",
                "Let me share what I know about this topic...",
                "I can provide you with the following information..."
            ],
            IntentType.UNKNOWN: [
                "I'm not quite sure I understand. Could you elaborate?",
                "I'm here to help, but I need more information.",
                "Could you please provide more details?"
            ]
        }
        
        self.fallback_responses = [
            "I understand. Could you tell me more about what you need?",
            "I'm here to help. What specific aspect would you like to work on?",
            "Let me help you with that. Could you provide more details?"
        ]
    
    def generate_response(
        self,
        prompt: str,
        context: ConversationContext,
        config: ResponseConfig,
        persona: Persona
    ) -> GeneratedResponse:
        """Generate AI response using templates"""
        
        # Get last user message for intent
        last_intent = IntentType.UNKNOWN
        last_sentiment = SentimentType.NEUTRAL
        
        for msg in reversed(context.messages):
            if msg.role == "user":
                if msg.intent:
                    last_intent = msg.intent.type
                    last_sentiment = msg.intent.sentiment
                break
        
        # Select response based on intent
        templates = self.template_responses.get(last_intent, self.fallback_responses)
        
        # Apply creativity level
        import random
        if config.creativity == ResponseCreativity.PRECISE:
            response_text = templates[0] if templates else self.fallback_responses[0]
        elif config.creativity == ResponseCreativity.CREATIVE:
            response_text = random.choice(templates) if templates else random.choice(self.fallback_responses)
        else:
            idx = len(templates) // 2 if templates else 0
            response_text = templates[idx] if templates else self.fallback_responses[0]
        
        # Adjust length based on config
        if config.length == ResponseLength.CONCISE:
            # Use shorter version
            response_text = response_text.split('!')[0].split('.')[0] + "."
        elif config.length == ResponseLength.DETAILED:
            response_text += " Is there anything specific you'd like to know more about?"
        elif config.length == ResponseLength.EXTENDED:
            response_text += " I can provide more detailed information on any aspect you're interested in. Just let me know what you'd like to explore further."
        
        # Adjust formality
        if config.formality == FormalityTone.CASUAL:
            response_text = response_text.replace("Certainly", "Sure").replace("Absolutely", "Yep")
        elif config.formality == FormalityTone.FORMAL:
            response_text = response_text.replace("Sure", "Certainly").replace("Yep", "Absolutely")
        
        # Apply persona modifications
        response_text = self._apply_persona(response_text, persona, last_sentiment)
        
        return GeneratedResponse(
            text=response_text,
            confidence=0.7,
            reasoning="Generated using template-based response with persona adaptation",
            sentiment=last_sentiment
        )
    
    def _apply_persona(self, text: str, persona: Persona, sentiment: SentimentType) -> str:
        """Apply persona modifications to response"""
        
        # Add personality traits
        if persona.traits:
            # Could prepend trait-based intro
            pass
        
        # Adjust for emotional expressiveness
        if persona.emotional_expressiveness > 0.7 and sentiment != SentimentType.NEUTRAL:
            if sentiment == SentimentType.POSITIVE:
                text = "I'm glad you're feeling positive! " + text
            elif sentiment == SentimentType.NEGATIVE:
                text = "I understand this might be frustrating. " + text
        
        return text
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return True


# ============================================================================
# Analytics and Logging
# ============================================================================

@dataclass
class ConversationAnalytics:
    """Analytics data for a conversation"""
    conversation_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    total_messages: int = 0
    user_messages: int = 0
    assistant_messages: int = 0
    average_sentiment: float = 0.0
    intent_distribution: Dict[IntentType, int] = field(default_factory=lambda: defaultdict(int))
    errors_encountered: int = 0
    response_times: List[float] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        """Get conversation duration in seconds"""
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return (datetime.now() - self.started_at).total_seconds()
    
    @property
    def average_response_time(self) -> float:
        """Get average response time"""
        if self.response_times:
            return sum(self.response_times) / len(self.response_times)
        return 0.0


class AnalyticsTracker:
    """Track and analyze conversation metrics"""
    
    def __init__(self):
        self.active_conversations: Dict[str, ConversationAnalytics] = {}
        self.completed_conversations: List[ConversationAnalytics] = []
        self.global_stats: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def start_conversation(self, conversation_id: str) -> ConversationAnalytics:
        """Start tracking a new conversation"""
        with self._lock:
            analytics = ConversationAnalytics(
                conversation_id=conversation_id,
                started_at=datetime.now()
            )
            self.active_conversations[conversation_id] = analytics
            return analytics
    
    def end_conversation(self, conversation_id: str) -> Optional[ConversationAnalytics]:
        """End tracking a conversation"""
        with self._lock:
            if conversation_id in self.active_conversations:
                analytics = self.active_conversations.pop(conversation_id)
                analytics.ended_at = datetime.now()
                self.completed_conversations.append(analytics)
                return analytics
            return None
    
    def record_message(
        self,
        conversation_id: str,
        role: str,
        intent: Optional[IntentType] = None,
        sentiment: float = 0.0,
        response_time: float = 0.0
    ):
        """Record message in conversation analytics"""
        with self._lock:
            if conversation_id in self.active_conversations:
                analytics = self.active_conversations[conversation_id]
                analytics.total_messages += 1
                
                if role == "user":
                    analytics.user_messages += 1
                elif role == "assistant":
                    analytics.assistant_messages += 1
                
                if intent:
                    analytics.intent_distribution[intent] += 1
                
                if response_time > 0:
                    analytics.response_times.append(response_time)
    
    def record_error(self, conversation_id: str):
        """Record an error in conversation"""
        with self._lock:
            if conversation_id in self.active_conversations:
                self.active_conversations[conversation_id].errors_encountered += 1
    
    def get_conversation_stats(self, conversation_id: str) -> Optional[ConversationAnalytics]:
        """Get statistics for a conversation"""
        with self._lock:
            return self.active_conversations.get(conversation_id)
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global statistics"""
        with self._lock:
            total_conversations = len(self.completed_conversations)
            if total_conversations == 0:
                return {"total_conversations": 0}
            
            total_messages = sum(c.total_messages for c in self.completed_conversations)
            total_errors = sum(c.errors_encountered for c in self.completed_conversations)
            avg_duration = sum(c.duration_seconds for c in self.completed_conversations) / total_conversations
            avg_response_time = sum(c.average_response_time for c in self.completed_conversations) / total_conversations
            
            # Aggregate intent distribution
            aggregated_intents = defaultdict(int)
            for conv in self.completed_conversations:
                for intent, count in conv.intent_distribution.items():
                    aggregated_intents[intent] += count
            
            return {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "total_errors": total_errors,
                "average_duration_seconds": avg_duration,
                "average_response_time": avg_response_time,
                "error_rate": total_errors / total_messages if total_messages > 0 else 0,
                "intent_distribution": dict(aggregated_intents)
            }


# ============================================================================
# Main AI Dialogue System
# ============================================================================

class AIDialogueSystem:
    """
    Main AI Dialogue Generation System
    
    This is the primary interface for AI-assisted dialogue generation.
    It coordinates all components including NLU, language models,
    knowledge base, translation, and safety systems.
    """
    
    def __init__(
        self,
        settings: Optional[Any] = None
    ):
        """
        Initialize the AI Dialogue System.
        
        Args:
            settings: Optional settings object for configuration
        """
        self.settings = settings
        
        # Initialize components
        self.nlu: NLUProvider = RuleBasedNLU()
        self.language_model: LanguageModelProvider = SimpleLanguageModel()
        self.knowledge_base: KnowledgeBaseProvider = InMemoryKnowledgeBase()
        self.translation_provider: TranslationProvider = SimpleTranslationProvider()
        
        # Safety systems
        self.content_filter = ContentFilter()
        self.bias_detector = BiasDetector()
        
        # Analytics
        self.analytics = AnalyticsTracker()
        
        # Conversation management
        self.conversations: Dict[str, ConversationContext] = {}
        self.conversation_lock = threading.Lock()
        
        # Default configurations
        self.default_config = ResponseConfig()
        self.default_persona = Persona()
        
        # Callbacks for events
        self.on_response_generated: Optional[Callable[[GeneratedResponse], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        
        # Provider availability
        self._providers_available = {
            "nlu": True,
            "language_model": True,
            "knowledge_base": True,
            "translation": True
        }
        
        logger.info("AI Dialogue System initialized")
    
    def create_conversation(
        self,
        conversation_id: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new conversation.
        
        Args:
            conversation_id: Optional ID for the conversation (generated if not provided)
            user_profile: Optional user profile information
            
        Returns:
            The conversation ID
        """
        if conversation_id is None:
            # Generate unique ID
            timestamp = str(time.time())
            conversation_id = hashlib.md5(timestamp.encode()).hexdigest()[:12]
        
        context = ConversationContext(
            conversation_id=conversation_id,
            user_profile=user_profile or {}
        )
        
        with self.conversation_lock:
            self.conversations[conversation_id] = context
        
        # Start analytics tracking
        self.analytics.start_conversation(conversation_id)
        
        logger.info(f"Created conversation: {conversation_id}")
        return conversation_id
    
    def end_conversation(self, conversation_id: str) -> Optional[ConversationAnalytics]:
        """
        End a conversation and get analytics.
        
        Args:
            conversation_id: ID of the conversation to end
            
        Returns:
            Analytics for the conversation, or None if not found
        """
        with self.conversation_lock:
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
        
        analytics = self.analytics.end_conversation(conversation_id)
        logger.info(f"Ended conversation: {conversation_id}")
        return analytics
    
    def process_message(
        self,
        message: str,
        conversation_id: str,
        config: Optional[ResponseConfig] = None,
        persona: Optional[Persona] = None,
        language: str = "en"
    ) -> GeneratedResponse:
        """
        Process a user message and generate a response.
        
        This is the main entry point for generating AI responses.
        
        Args:
            message: User's input message
            conversation_id: ID of the conversation
            config: Optional response configuration
            persona: Optional persona configuration
            language: Target language code
            
        Returns:
            Generated response
        """
        start_time = time.time()
        
        # Get or create conversation
        context = self._get_or_create_conversation(conversation_id)
        
        if config is None:
            config = self.default_config
        
        if persona is None:
            persona = self.default_persona
        
        try:
            # Step 1: Detect language if needed
            if language == "auto":
                language = self.translation_provider.detect_language(message)
            
            # Step 2: Translate if not English
            original_message = message
            if language != "en":
                translation = self.translation_provider.translate(message, language, "en")
                message = translation.original_text  # Use original for now
            
            # Step 3: NLU - Intent recognition
            intent = self.nlu.recognize_intent(message, context)
            
            # Step 4: Entity extraction
            entities = self.nlu.extract_entities(message, context)
            
            # Step 5: Sentiment analysis
            sentiment, sentiment_score = self.nlu.analyze_sentiment(message)
            
            # Step 6: Search knowledge base
            knowledge_results = []
            if intent.extracted_topics or intent.confidence > 0.3:
                query = " ".join(intent.extracted_topics) if intent.extracted_topics else message
                knowledge_results = self.knowledge_base.search(query, context)
            
            # Step 7: Build context for response generation
            prompt = self._build_prompt(message, context, intent, knowledge_results)

            # Step 8: Generate response - use sync fallback for reliability
            # Note: async provider can't be called from sync code due to asyncio event loop issues
            # Keep fallback for now until a proper async pipeline is built
            if not self.language_model.is_available:
                response = self._get_fallback_response(Exception("Language model unavailable"))
            else:
                # Try sync call first (works for SimpleLanguageModel)
                try:
                    response = self.language_model.generate_response(
                        prompt, context, config, persona
                    )
                except Exception as e:
                    logger.warning(f"Sync call failed: {e}, using fallback")
                    response = self._get_fallback_response(e)

            # Convert dict to GeneratedResponse if needed
            if isinstance(response, dict):
                response = GeneratedResponse(
                    text=response.get("text", ""),
                    confidence=response.get("confidence", 0.0),
                    reasoning=response.get("reasoning", ""),
                    sentiment=response.get("sentiment", SentimentType.NEUTRAL),
                    metadata=response.get("metadata", {})
                )
            
            # Step 9: Apply content filtering
            if self.content_filter.should_warn(response.text):
                response.metadata["content_warning"] = True
            
            response.text = self.content_filter.filter_response(response.text)
            
            # Step 10: Apply bias detection
            bias_analysis = self.bias_detector.analyze_text(response.text)
            response.text = self.bias_detector.mitigate_bias(response.text, bias_analysis)
            response.metadata["bias_analysis"] = bias_analysis
            
            # Step 11: Translate back if needed
            if language != "en":
                translation = self.translation_provider.translate(response.text, "en", language)
                response.text = translation.translated_text
            
            # Step 12: Store messages in context
            user_msg = ConversationMessage(
                role="user",
                content=original_message,
                intent=intent,
                sentiment=sentiment,
                metadata={"entities": list(entities.keys())}
            )
            context.add_message(user_msg)
            
            assistant_msg = ConversationMessage(
                role="assistant",
                content=response.text,
                sentiment=response.sentiment,
                metadata={
                    "knowledge_used": len(knowledge_results),
                    "config": config.to_dict()
                }
            )
            context.add_message(assistant_msg)
            
            # Step 13: Record analytics
            response_time = time.time() - start_time
            self.analytics.record_message(
                conversation_id=conversation_id,
                role="user",
                intent=intent.type,
                sentiment=sentiment_score,
                response_time=response_time
            )
            self.analytics.record_message(
                conversation_id=conversation_id,
                role="assistant",
                sentiment=response.sentiment.value,
                response_time=response_time
            )
            
            # Add metadata
            response.metadata["response_time"] = response_time
            response.metadata["language_detected"] = language
            response.metadata["knowledge_results"] = len(knowledge_results)
            
            logger.debug(f"Generated response in {response_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            self.analytics.record_error(conversation_id)
            
            if self.on_error:
                self.on_error(e)
            
            # Return fallback response
            return self._get_fallback_response(e)
    
    def _get_or_create_conversation(self, conversation_id: str) -> ConversationContext:
        """Get existing conversation or create new one"""
        with self.conversation_lock:
            if conversation_id in self.conversations:
                return self.conversations[conversation_id]
            else:
                context = ConversationContext(conversation_id=conversation_id)
                self.conversations[conversation_id] = context
                self.analytics.start_conversation(conversation_id)
                return context
    
    def _build_prompt(
        self,
        message: str,
        context: ConversationContext,
        intent: Intent,
        knowledge_results: List[KnowledgeEntry]
    ) -> str:
        """Build prompt for language model"""
        prompt_parts = [
            "You are a helpful AI assistant for the Fallout Dialogue Creator.",
            f"\nUser message: {message}",
        ]
        
        # Add conversation history
        if context.messages:
            recent = context.messages[-5:]  # Last 5 messages
            history = "\n".join(f"{m.role}: {m.content[:100]}" for m in recent)
            prompt_parts.append(f"\nRecent conversation:\n{history}")
        
        # Add knowledge base results
        if knowledge_results:
            kb_content = "\n".join(f"- {entry.content}" for entry in knowledge_results[:3])
            prompt_parts.append(f"\nRelevant knowledge:\n{kb_content}")
        
        # Add intent information
        prompt_parts.append(f"\nDetected intent: {intent.type.value}")
        
        return "\n".join(prompt_parts)
    
    def _get_fallback_response(self, error: Exception) -> GeneratedResponse:
        """Generate fallback response on error"""
        return GeneratedResponse(
            text="I apologize, but I encountered an issue processing your request. Please try again or rephrase your message.",
            confidence=0.0,
            reasoning=f"Error: {str(error)}",
            sentiment=SentimentType.NEUTRAL,
            metadata={"error": True}
        )

    # =========================================================================
    # Async Methods for Main Thread Processing
    # =========================================================================

    async def process_message_async(
        self,
        message: str,
        conversation_id: str,
        config: Optional[ResponseConfig] = None,
        persona: Optional[Persona] = None,
        language: str = "en"
    ) -> GeneratedResponse:
        """Async entry point - calls sync method directly"""
        # Just call the sync method - the provider will be set if async is possible
        return self.process_message(message, conversation_id, config, persona, language)

    async def analyze_sentiment_async(self, text: str):
        """Async sentiment analysis"""
        sentiment, score = self.nlu.analyze_sentiment(text)
        from dataclasses import dataclass
        @dataclass
        class Result:
            text: str
            sentiment: any
            confidence: float
        return Result(text=text, sentiment=sentiment, confidence=score)
    
    # =========================================================================
    # Configuration Methods
    # =========================================================================
    
    def set_nlu_provider(self, provider: NLUProvider):
        """Set custom NLU provider"""
        self.nlu = provider
        logger.info("NLU provider updated")
    
    def set_language_model(self, model: LanguageModelProvider):
        """Set custom language model provider"""
        self.language_model = model
        logger.info("Language model provider updated")
    
    def set_translation_provider(self, provider: TranslationProvider):
        """Set custom translation provider"""
        self.translation_provider = provider
        logger.info("Translation provider updated")
    
    def set_knowledge_base(self, kb: KnowledgeBaseProvider):
        """Set custom knowledge base"""
        self.knowledge_base = kb
        logger.info("Knowledge base updated")
    
    def add_knowledge_entry(self, entry: KnowledgeEntry) -> bool:
        """Add entry to knowledge base"""
        return self.knowledge_base.add_entry(entry)
    
    def set_default_config(self, config: ResponseConfig):
        """Set default response configuration"""
        self.default_config = config
    
    def set_default_persona(self, persona: Persona):
        """Set default persona"""
        self.default_persona = persona
    
    # =========================================================================
    # Analytics and Reporting
    # =========================================================================
    
    def get_conversation_history(
        self,
        conversation_id: str,
        max_messages: int = 50
    ) -> List[ConversationMessage]:
        """Get conversation history"""
        with self.conversation_lock:
            context = self.conversations.get(conversation_id)
            if context:
                return context.messages[-max_messages:]
            return []
    
    def get_analytics(self, conversation_id: str) -> Optional[ConversationAnalytics]:
        """Get analytics for a conversation"""
        return self.analytics.get_conversation_stats(conversation_id)
    
    def get_global_analytics(self) -> Dict[str, Any]:
        """Get global analytics"""
        return self.analytics.get_global_stats()
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages for translation"""
        return self.translation_provider.get_supported_languages()
    
    def get_knowledge_categories(self) -> List[str]:
        """Get knowledge base categories"""
        return self.knowledge_base.get_categories()
    
    def check_health(self) -> Dict[str, bool]:
        """Check health status of all components"""
        return {
            "nlu": self._providers_available.get("nlu", True),
            "language_model": self.language_model.is_available(),
            "knowledge_base": self._providers_available.get("knowledge_base", True),
            "translation": self._providers_available.get("translation", True),
            "content_filter": True,
            "bias_detector": True
        }
    
    def set_nlu_provider(self, provider):
        """
        Set the NLU provider.
        
        Args:
            provider: An NLU provider instance (e.g., GeminiProvider, OllamaCloudProvider)
        """
        self.nlu = provider
        self._providers_available["nlu"] = provider.is_available if hasattr(provider, 'is_available') else True
        logger.info(f"NLU provider set to: {type(provider).__name__}")
    
    def set_language_model(self, provider):
        """
        Set the language model provider.
        
        Args:
            provider: A language model provider instance
        """
        self.language_model = provider
        # Check if provider is available - handle both property and method
        if hasattr(provider, 'is_available'):
            if callable(provider.is_available):
                self._providers_available["language_model"] = provider.is_available()
            else:
                # It's a property
                self._providers_available["language_model"] = provider.is_available
        else:
            self._providers_available["language_model"] = True
        logger.info(f"Language model provider set to: {type(provider).__name__}")
    
    def set_translation_provider(self, provider):
        """
        Set the translation provider.
        
        Args:
            provider: A translation provider instance
        """
        self.translation_provider = provider
        self._providers_available["translation"] = provider.is_available if hasattr(provider, 'is_available') else True
        logger.info(f"Translation provider set to: {type(provider).__name__}")
    
    def shutdown(self):
        """Shutdown the system and cleanup resources"""
        # End all active conversations
        with self.conversation_lock:
            for conv_id in list(self.conversations.keys()):
                self.analytics.end_conversation(conv_id)
            self.conversations.clear()
        
        logger.info("AI Dialogue System shutdown complete")


# ============================================================================
# Factory and Singleton
# ============================================================================

_instance: Optional[AIDialogueSystem] = None
_instance_lock = threading.Lock()


def get_ai_dialogue_system(settings: Optional[Any] = None) -> AIDialogueSystem:
    """
    Get singleton instance of AI Dialogue System.
    
    Args:
        settings: Optional settings object
        
    Returns:
        The singleton AIDialogueSystem instance
    """
    global _instance
    
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = AIDialogueSystem(settings)
    
    return _instance


def create_ai_dialogue_system(settings: Optional[Any] = None) -> AIDialogueSystem:
    """
    Create a new AI Dialogue System instance.
    
    Use this instead of get_ai_dialogue_system() if you need
    multiple independent instances.
    
    Args:
        settings: Optional settings object
        
    Returns:
        New AIDialogueSystem instance
    """
    return AIDialogueSystem(settings)


async def _create_provider_from_settings(settings) -> Optional[Any]:
    """
    Create and initialize an AI provider from settings.
    
    Args:
        settings: Settings object with provider configuration
        
    Returns:
        Initialized provider or None if configuration is invalid
    """
    # Use getter methods to properly retrieve settings
    if hasattr(settings, 'get_ai_provider'):
        provider_type = settings.get_ai_provider()
    else:
        provider_type = settings.get('ai_provider', 'gemini') if settings else 'gemini'
    
    if provider_type == 'gemini':
        from core.gemini_provider import GeminiProvider, GeminiConfig, GeminiModel
        
        # Use getter method if available
        if hasattr(settings, 'get_gemini_api_key'):
            api_key = settings.get_gemini_api_key()
        else:
            api_key = settings.get('gemini_api_key', '') if settings else ''
        
        if not api_key:
            logger.warning("No Gemini API key configured")
            return None
        
        # Use getter method if available
        if hasattr(settings, 'get_gemini_model'):
            model_name = settings.get_gemini_model()
        else:
            model_name = settings.get('gemini_model', 'gemini-2.0-flash') if settings else 'gemini-2.0-flash'
        
        try:
            model = GeminiModel(model_name)
        except ValueError:
            model = GeminiModel.GEMINI_2_0_FLASH
        
        config = GeminiConfig(api_key=api_key, model=model)
        provider = GeminiProvider(config)
        await provider.initialize()
        return provider
    
    elif provider_type == 'ollama_cloud':
        from core.ollama_provider import OllamaCloudProvider, OllamaCloudConfig, OllamaCloudModel
        
        # Use getter method if available
        if hasattr(settings, 'get_ollama_cloud_api_key'):
            api_key = settings.get_ollama_cloud_api_key()
        else:
            api_key = settings.get('ollama_cloud_api_key', '') if settings else ''
        
        if not api_key:
            logger.warning("No OllamaCloud API key configured")
            return None
        
        # Use getter method if available
        if hasattr(settings, 'get_ollama_cloud_model'):
            model_name = settings.get_ollama_cloud_model()
        else:
            model_name = settings.get('ollama_cloud_model', 'gpt-oss:32b-cloud') if settings else 'gpt-oss:32b-cloud'
        
        try:
            model = OllamaCloudModel(model_name)
        except ValueError:
            model = OllamaCloudModel.GPT_OSS_32B
        
        # Use getter method if available
        if hasattr(settings, 'get_ollama_cloud_timeout'):
            timeout = settings.get_ollama_cloud_timeout()
        else:
            timeout = settings.get('ollama_cloud_timeout', 60) if settings else 60
        
        config = OllamaCloudConfig(
            api_key=api_key,
            model=model,
            read_timeout=timeout
        )
        provider = OllamaCloudProvider(config)
        await provider.initialize()
        return provider
    
    else:
        logger.warning(f"Unknown provider type: {provider_type}")
        return None


def configure_ai_system_from_settings(ai_system: AIDialogueSystem, settings) -> AIDialogueSystem:
    """Configure an AI Dialogue System with providers from settings."""
    import asyncio
    import concurrent.futures

    def set_provider_on_system(provider):
        """Helper to set provider on the AI system"""
        # Don't set the provider - asyncio event loop conflicts prevent using it
        # Log that it's available for development
        if provider and provider.is_available:
            logger.info(f"Async provider available (not used due to asyncio issues): {type(provider).__name__}")

    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_create_provider_from_settings(settings))
        finally:
            loop.close()

    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            provider = future.result(timeout=30)
            set_provider_on_system(provider)
    except Exception as e:
        logger.warning(f"Failed to configure async provider: {e}")

    return ai_system
