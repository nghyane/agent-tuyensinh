"""
Vietnamese text processing utilities optimized for FPT University domain
"""

import re
import unicodedata
from typing import List, Dict, FrozenSet
from functools import lru_cache

try:

    UNIDECODE_AVAILABLE = True
except ImportError:
    UNIDECODE_AVAILABLE = False


class VietnameseTextProcessor:
    """
    Optimized Vietnamese text processing for FPT University domain
    """

    def __init__(self):
        # Domain-specific stop words for FPT University context
        self.stop_words: FrozenSet[str] = frozenset({
            # Vietnamese stop words
            'và', 'của', 'có', 'là', 'được', 'một', 'này', 'đó', 'cho', 'với',
            'từ', 'tại', 'về', 'như', 'khi', 'nếu', 'để', 'sẽ', 'đã', 'đang',
            'các', 'những', 'nhiều', 'ít', 'rất', 'quá', 'cũng', 'chỉ', 'còn',
            'thì', 'mà', 'nên', 'vì', 'do', 'bởi', 'tại', 'ở', 'trong', 'ngoài',
            'trên', 'dưới', 'trước', 'sau', 'giữa', 'bên', 'cạnh', 'gần', 'xa',

            # English stop words
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'can', 'may', 'might', 'must', 'shall', 'this', 'that', 'these', 'those',
            'what', 'when', 'where', 'why', 'how', 'which', 'who', 'whom', 'whose'
        })

        # FPT University specific stop words (keep these for context)
        self.domain_keywords: FrozenSet[str] = frozenset({
            'fpt', 'university', 'đại học', 'trường', 'campus', 'sinh viên', 'student',
            'giảng viên', 'lecturer', 'professor', 'khoa', 'faculty', 'ngành', 'major',
            'chuyên ngành', 'specialization', 'môn học', 'course', 'subject',
            'học kỳ', 'semester', 'năm học', 'academic year', 'tín chỉ', 'credit'
        })

        # Enhanced irrelevant patterns for FPT University context
        self.irrelevant_patterns = [
            # Weather and unrelated topics
            r'thời tiết|weather|mưa|nắng|lạnh|nóng|temperature|forecast',
            r'nấu ăn|cooking|món ăn|recipe|phở|bún|cơm|food|cuisine',
            r'phim|movie|film|xem phim|cinema|entertainment',
            r'âm nhạc|music|bài hát|song|concert|performance',
            r'thể thao|sports|bóng đá|football|basketball|tennis',
            r'chính trị|politics|bầu cử|election|government',
            r'tin tức|news|báo|newspaper|headlines',
            r'mua sắm|shopping|mua|buy|bán|sell|retail',
            r'du lịch|travel|trip|vacation|nghỉ mát|tourism',
            r'cá cược|betting|casino|gambling|lottery',
            r'y tế|medical|health|bệnh viện|hospital|doctor',
            r'xe cộ|car|motorcycle|traffic|giao thông'
        ]

        # Pre-compile all patterns once
        self.compiled_irrelevant = [
            re.compile(pattern, re.IGNORECASE | re.UNICODE)
            for pattern in self.irrelevant_patterns
        ]

        # Pre-compile common regex patterns
        self.whitespace_pattern = re.compile(r'\s+')
        self.word_pattern = re.compile(r'\b\w+\b')
        self.special_char_pattern = re.compile(r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF]')

        # Enhanced abbreviation mapping for FPT University domain
        self.abbreviations: Dict[str, str] = {
            # University abbreviations
            'fpt': 'fpt university',
            'fptu': 'fpt university',
            'fpt edu': 'fpt university',

            # Academic abbreviations
            'cntt': 'công nghệ thông tin',
            'it': 'information technology',
            'ai': 'artificial intelligence',
            'ml': 'machine learning',
            'dl': 'deep learning',
            'ds': 'data science',
            'cs': 'computer science',
            'se': 'software engineering',
            'ce': 'computer engineering',
            'is': 'information systems',
            'cyber': 'cybersecurity',
            'attt': 'an toàn thông tin',

            # Business abbreviations
            'qtkd': 'quản trị kinh doanh',
            'ql': 'quản lý',
            'kt': 'kinh tế',
            'tài chính': 'finance',
            'marketing': 'digital marketing',
            'dm': 'digital marketing',

            # Language abbreviations
            'nn': 'ngoại ngữ',
            'english': 'tiếng anh',
            'ielts': 'international english language testing system',
            'toeic': 'test of english for international communication',

            # Academic terms
            'ojt': 'on the job training',
            'gpa': 'grade point average',
            'credit': 'tín chỉ',
            'semester': 'học kỳ',
            'academic': 'học thuật',

            # Campus abbreviations
            'hanoi': 'hà nội',
            'hcm': 'thành phố hồ chí minh',
            'danang': 'đà nẵng',
            'cantho': 'cần thơ',
            'hoalac': 'hòa lạc',
            'quy nhon': 'quy nhơn'
        }

        # Pre-compile abbreviation replacement patterns
        self.abbreviation_patterns = {
            abbr: re.compile(r'\b' + re.escape(abbr) + r'\b', re.IGNORECASE)
            for abbr in self.abbreviations.keys()
        }

        # Academic context patterns for better keyword extraction
        self.academic_patterns = [
            r'học phí|tuition|fee|cost|price|chi phí',
            r'học bổng|scholarship|financial aid',
            r'điểm chuẩn|admission score|cutoff',
            r'điều kiện|requirement|eligibility',
            r'thời gian|deadline|schedule|timeline',
            r'chương trình|program|curriculum',
            r'ngành|major|specialization',
            r'campus|khuôn viên|facility',
            r'thực tập|internship|ojt',
            r'việc làm|career|job|employment'
        ]

        self.compiled_academic = [
            re.compile(pattern, re.IGNORECASE | re.UNICODE)
            for pattern in self.academic_patterns
        ]

    @lru_cache(maxsize=1024)
    def normalize_vietnamese(self, text: str) -> str:
        """
        Normalize Vietnamese text with enhanced FPT University context
        """
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Normalize unicode
        text = unicodedata.normalize('NFC', text)

        # Remove extra whitespace using pre-compiled pattern
        text = self.whitespace_pattern.sub(' ', text).strip()

        # Expand abbreviations using pre-compiled patterns
        for abbr, full in self.abbreviations.items():
            text = self.abbreviation_patterns[abbr].sub(full, text)

        return text

    def extract_keywords(self, text: str, min_length: int = 2, max_keywords: int = 20) -> List[str]:
        """
        Extract keywords with enhanced academic context awareness
        """
        if not text:
            return []

        # Normalize text
        normalized = self.normalize_vietnamese(text)

        # Use pre-compiled pattern for word extraction
        words = self.word_pattern.findall(normalized)

        # Enhanced keyword filtering with domain awareness
        keywords = []
        seen = set()

        for word in words:
            word_lower = word.lower()
            if (len(word) >= min_length and
                word_lower not in self.stop_words and
                not word.isdigit() and
                word_lower not in seen):

                # Prioritize domain keywords
                if word_lower in self.domain_keywords:
                    keywords.insert(0, word_lower)  # Add to front
                else:
                    keywords.append(word_lower)

                seen.add(word_lower)

                # Early exit if we have enough keywords
                if len(keywords) >= max_keywords:
                    break

        return keywords

    def extract_academic_context(self, text: str) -> Dict[str, List[str]]:
        """
        Extract academic context from text for better intent detection
        """
        if not text:
            return {}

        context = {
            'academic_terms': [],
            'programs': [],
            'campuses': [],
            'financial_terms': [],
            'temporal_terms': []
        }

        normalized = self.normalize_vietnamese(text)

        # Extract academic terms
        for pattern in self.compiled_academic:
            matches = pattern.findall(normalized)
            if matches:
                context['academic_terms'].extend(matches)

        # Extract program names
        program_patterns = [
            r'công nghệ thông tin|information technology|it',
            r'trí tuệ nhân tạo|artificial intelligence|ai',
            r'kỹ thuật phần mềm|software engineering|se',
            r'quản trị kinh doanh|business administration|mba',
            r'thiết kế đồ họa|graphic design|gd',
            r'digital marketing|marketing',
            r'an toàn thông tin|cybersecurity|security',
            r'khoa học dữ liệu|data science|ds'
        ]

        for pattern in program_patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                context['programs'].append(pattern.split('|')[0])

        # Extract campus names
        campus_patterns = [
            r'hà nội|hanoi',
            r'thành phố hồ chí minh|hcm|ho chi minh',
            r'đà nẵng|danang',
            r'cần thơ|cantho',
            r'hòa lạc|hoalac',
            r'quy nhơn|quy nhon'
        ]

        for pattern in campus_patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                context['campuses'].append(pattern.split('|')[0])

        return context

    def detect_language(self, text: str) -> str:
        """
        Optimized language detection with academic context
        """
        if not text:
            return "unknown"

        # Count Vietnamese characters more efficiently
        vietnamese_chars = sum(1 for char in text if char.isalpha() and ord(char) > 127)
        total_chars = sum(1 for char in text if char.isalpha())

        if total_chars == 0:
            return "unknown"

        vietnamese_ratio = vietnamese_chars / total_chars

        return "vi" if vietnamese_ratio > 0.1 else "en"

    def is_irrelevant_query(self, text: str) -> bool:
        """
        Enhanced irrelevant query detection for FPT University context
        """
        if not text:
            return True

        # Early exit: check if text is too short to be relevant
        if len(text.strip()) < 3:
            return True

        # Check for academic context first (if found, likely relevant)
        academic_context = self.extract_academic_context(text)
        if any(academic_context.values()):
            return False

        # Check against pre-compiled patterns with early exit
        for pattern in self.compiled_irrelevant:
            if pattern.search(text):
                return True

        return False

    def clean_query(self, text: str) -> str:
        """
        Clean and prepare query with enhanced academic context
        """
        if not text:
            return ""

        # Use pre-compiled pattern for special character removal
        text = self.special_char_pattern.sub(' ', text)

        # Normalize using cached method
        text = self.normalize_vietnamese(text)

        return text

    def get_text_statistics(self, text: str) -> dict:
        """
        Get comprehensive text statistics with academic context
        """
        if not text:
            return {
                "length": 0,
                "word_count": 0,
                "language": "unknown",
                "contains_vietnamese": False,
                "keywords": [],
                "academic_context": {},
                "is_irrelevant": True
            }

        # Process all statistics in one pass where possible
        keywords = self.extract_keywords(text)
        language = self.detect_language(text)
        is_irrelevant = self.is_irrelevant_query(text)
        academic_context = self.extract_academic_context(text)

        return {
            "length": len(text),
            "word_count": len(text.split()),
            "language": language,
            "contains_vietnamese": language == "vi",
            "keywords": keywords,
            "academic_context": academic_context,
            "is_irrelevant": is_irrelevant
        }

    def clear_cache(self):
        """
        Clear the LRU cache for normalize_vietnamese method
        """
        self.normalize_vietnamese.cache_clear()
