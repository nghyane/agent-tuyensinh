"""
Vietnamese text processing utilities
"""

import re
import unicodedata
from typing import List

try:
    from unidecode import unidecode
    UNIDECODE_AVAILABLE = True
except ImportError:
    UNIDECODE_AVAILABLE = False


class VietnameseTextProcessor:
    """
    Vietnamese text processing and normalization
    """
    
    def __init__(self):
        # Vietnamese stop words
        self.stop_words = {
            'và', 'của', 'có', 'là', 'được', 'một', 'này', 'đó', 'cho', 'với',
            'từ', 'tại', 'về', 'như', 'khi', 'nếu', 'để', 'sẽ', 'đã', 'đang',
            'các', 'những', 'nhiều', 'ít', 'rất', 'quá', 'cũng', 'chỉ', 'còn',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        
        # Irrelevant query patterns
        self.irrelevant_patterns = [
            r'thời tiết|weather|mưa|nắng|lạnh|nóng',
            r'nấu ăn|cooking|món ăn|recipe|phở|bún|cơm',
            r'phim|movie|film|xem phim',
            r'âm nhạc|music|bài hát|song',
            r'thể thao|sports|bóng đá|football',
            r'chính trị|politics|bầu cử|election',
            r'tin tức|news|báo|newspaper',
            r'mua sắm|shopping|mua|buy|bán|sell',
            r'du lịch|travel|trip|vacation|nghỉ mát'
        ]
        
        self.compiled_irrelevant = [
            re.compile(pattern, re.IGNORECASE | re.UNICODE) 
            for pattern in self.irrelevant_patterns
        ]
    
    def normalize_vietnamese(self, text: str) -> str:
        """
        Normalize Vietnamese text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Normalize unicode
        text = unicodedata.normalize('NFC', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Expand common abbreviations
        abbreviations = {
            'fpt': 'fpt university',
            'cntt': 'công nghệ thông tin',
            'it': 'information technology',
            'ai': 'artificial intelligence',
            'ql': 'quản lý',
            'kt': 'kinh tế',
            'nn': 'ngoại ngữ'
        }
        
        for abbr, full in abbreviations.items():
            text = re.sub(r'\b' + re.escape(abbr) + r'\b', full, text)
        
        return text
    
    def extract_keywords(self, text: str, min_length: int = 2, max_keywords: int = 20) -> List[str]:
        """
        Extract keywords from text
        """
        if not text:
            return []
        
        # Normalize text
        normalized = self.normalize_vietnamese(text)
        
        # Remove punctuation and split
        words = re.findall(r'\b\w+\b', normalized)
        
        # Filter keywords
        keywords = []
        for word in words:
            if (len(word) >= min_length and 
                word.lower() not in self.stop_words and
                not word.isdigit()):
                keywords.append(word.lower())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:max_keywords]
    
    def detect_language(self, text: str) -> str:
        """
        Detect if text is Vietnamese or English
        """
        if not text:
            return "unknown"
        
        # Count Vietnamese characters
        vietnamese_chars = 0
        total_chars = 0
        
        for char in text:
            if char.isalpha():
                total_chars += 1
                # Check for Vietnamese diacritics
                if ord(char) > 127:  # Non-ASCII characters
                    vietnamese_chars += 1
        
        if total_chars == 0:
            return "unknown"
        
        vietnamese_ratio = vietnamese_chars / total_chars
        
        # If more than 10% Vietnamese characters, consider it Vietnamese
        if vietnamese_ratio > 0.1:
            return "vi"
        else:
            return "en"
    
    def is_irrelevant_query(self, text: str) -> bool:
        """
        Check if query is irrelevant to FPT University domain
        """
        if not text:
            return True
        
        # Check against irrelevant patterns
        for pattern in self.compiled_irrelevant:
            if pattern.search(text):
                return True
        
        return False
    
    def clean_query(self, text: str) -> str:
        """
        Clean and prepare query for processing
        """
        if not text:
            return ""
        
        # Remove special characters but keep Vietnamese
        text = re.sub(r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF]', ' ', text)
        
        # Normalize
        text = self.normalize_vietnamese(text)
        
        return text
    
    def get_text_statistics(self, text: str) -> dict:
        """
        Get statistics about the text
        """
        if not text:
            return {
                "length": 0,
                "word_count": 0,
                "language": "unknown",
                "contains_vietnamese": False,
                "keywords": []
            }
        
        keywords = self.extract_keywords(text)
        language = self.detect_language(text)
        
        return {
            "length": len(text),
            "word_count": len(text.split()),
            "language": language,
            "contains_vietnamese": language == "vi",
            "keywords": keywords,
            "is_irrelevant": self.is_irrelevant_query(text)
        }
