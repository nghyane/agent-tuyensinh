"""
Common type definitions for the intent detection system
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

# Basic type aliases
QueryText = str
IntentId = str
Confidence = float
Score = float
Metadata = Dict[str, Any]
CacheKey = str

# Generic types
T = TypeVar("T")


class DetectionMethod(Enum):
    """Methods used for intent detection"""

    RULE = "rule"
    VECTOR = "vector"
    RERANK = "rerank"
    HYBRID = "hybrid"
    FALLBACK = "fallback"


class ConfidenceLevel(Enum):
    """Confidence level categories"""

    VERY_HIGH = "very_high"  # >= 0.9
    HIGH = "high"  # >= 0.7
    MEDIUM = "medium"  # >= 0.5
    LOW = "low"  # >= 0.3
    VERY_LOW = "very_low"  # < 0.3


class IntentCategory(Enum):
    """Categories of intents for FPT University"""

    TUITION_INQUIRY = "tuition_inquiry"
    ADMISSION_REQUIREMENTS = "admission_requirements"
    PROGRAM_INFORMATION = "program_information"
    CAMPUS_FACILITIES = "campus_facilities"
    SCHEDULE_ACADEMIC = "schedule_academic"
    STUDENT_SERVICES = "student_services"
    CONTACT_INFORMATION = "contact_information"
    GENERAL_INFORMATION = "general_information"
    TECHNICAL_SUPPORT = "technical_support"
    GRADUATION_CAREER = "graduation_career"
    OUT_OF_SCOPE = "out_of_scope"


class LogLevel(Enum):
    """Logging levels"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(Enum):
    """Application environments"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class Result(Generic[T]):
    """Generic result type for operations that can fail"""

    success: bool
    data: Optional[T] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    @classmethod
    def ok(cls, data: T) -> "Result[T]":
        """Create successful result"""
        return cls(success=True, data=data)

    @classmethod
    def error(cls, error: str, error_code: Optional[str] = None) -> "Result[T]":
        """Create error result"""
        return cls(success=False, error_message=error, error_code=error_code)

    def is_ok(self) -> bool:
        """Check if result is successful"""
        return self.success

    def is_error(self) -> bool:
        """Check if result is error"""
        return not self.success


@dataclass
class PaginationParams:
    """Pagination parameters"""

    page: int = 1
    page_size: int = 20
    offset: int = 0

    def __post_init__(self):
        if self.offset == 0:
            self.offset = (self.page - 1) * self.page_size


@dataclass
class PaginatedResult(Generic[T]):
    """Paginated result container"""

    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool

    @property
    def total_pages(self) -> int:
        """Calculate total pages"""
        return (self.total + self.page_size - 1) // self.page_size


# University API types
class UniversityApiEndpoint(Enum):
    """University API endpoints"""

    BASE_URL = "https://core-tuyensinh-production.up.railway.app"
    HEALTH = "/health"
    DEPARTMENTS = "/api/v1/departments"
    PROGRAMS = "/api/v1/programs"
    CAMPUSES = "/api/v1/campuses"
    CAMPUSES_SUMMARY = "/api/v1/campuses/summary"
    TUITION = "/api/v1/tuition"
    TUITION_CAMPUS = "/api/v1/tuition/campus"


@dataclass
class UniversityApiResponse:
    """University API response"""

    success: bool
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    error_message: Optional[str] = None
    status_code: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None
