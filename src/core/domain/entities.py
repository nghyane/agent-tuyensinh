"""
Core domain entities for intent detection system
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Pattern

from shared.types import (
    QueryText, IntentId, Confidence, Score, Metadata,
    DetectionMethod, ConfidenceLevel, IntentCategory
)


@dataclass(frozen=True)
class IntentResult:
    """Core entity representing the result of intent detection"""
    id: IntentId
    confidence: Confidence
    method: DetectionMethod
    category: Optional[IntentCategory] = None
    metadata: Metadata = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Get confidence level category"""
        if self.confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif self.confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif self.confidence >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def is_high_confidence(self) -> bool:
        """Check if result has high confidence (>= 0.7)"""
        return self.confidence >= 0.7

    def with_metadata(self, **kwargs) -> 'IntentResult':
        """Create new result with additional metadata"""
        new_metadata = {**self.metadata, **kwargs}
        return IntentResult(
            id=self.id,
            confidence=self.confidence,
            method=self.method,
            category=self.category,
            metadata=new_metadata,
            timestamp=self.timestamp
        )


@dataclass(frozen=True)
class DetectionContext:
    """Context information for intent detection"""
    query: QueryText
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    language: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Metadata = field(default_factory=dict)


@dataclass
class IntentRule:
    """Rule-based intent detection rule"""
    intent_id: IntentId
    keywords: List[str]
    patterns: List[str]
    weight: float = 1.0
    description: str = ""
    negative_keywords: List[str] = field(default_factory=list)
    priority: str = "medium"
    enabled: bool = True
    metadata: Metadata = field(default_factory=dict)

    _compiled_patterns: Optional[List[Pattern]] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        """Validate rule after initialization"""
        if not self.intent_id:
            raise ValueError("intent_id cannot be empty")
        if not self.keywords and not self.patterns:
            raise ValueError("Rule must have at least keywords or patterns")
        if not (0.1 <= self.weight <= 2.0):
            raise ValueError("Weight must be between 0.1 and 2.0")
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for better performance"""
        compiled = []
        for pattern in self.patterns:
            try:
                compiled.append(re.compile(pattern, re.IGNORECASE | re.UNICODE))
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{pattern}': {e}")
        object.__setattr__(self, '_compiled_patterns', compiled)

    @property
    def compiled_patterns(self) -> List[Pattern]:
        """Get compiled regex patterns"""
        if self._compiled_patterns is None:
            self._compile_patterns()
        return self._compiled_patterns or []

    @property
    def priority_weight(self) -> float:
        """Get priority weight multiplier"""
        priority_weights = {"high": 1.2, "medium": 1.0, "low": 0.8}
        return priority_weights.get(self.priority, 1.0)

    def matches_keywords(self, text: str) -> List[str]:
        """Check which keywords match in the text"""
        text_lower = text.lower()
        matched = []

        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                matched.append(keyword)

        return matched

    def matches_patterns(self, text: str) -> List[str]:
        """Check which patterns match in the text"""
        matched = []

        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(text):
                matched.append(self.patterns[i])

        return matched

    def has_negative_keywords(self, text: str) -> bool:
        """Check if text contains negative keywords"""
        text_lower = text.lower()

        for neg_keyword in self.negative_keywords:
            if neg_keyword.lower() in text_lower:
                return True

        return False


@dataclass(frozen=True)
class RuleMatch:
    """Result of rule-based matching"""
    intent_id: IntentId
    score: Score
    matched_keywords: List[str]
    matched_patterns: List[str]
    weight: float
    position: int = 0
    rule_metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True)
class SearchCandidate:
    """Candidate result from vector search"""
    text: str
    intent_id: IntentId
    score: Score
    metadata: Metadata = field(default_factory=dict)
    source: str = "unknown"
