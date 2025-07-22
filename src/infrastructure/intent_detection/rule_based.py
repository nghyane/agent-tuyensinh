"""
Rule-based intent detection implementation
"""

import time
from typing import List, Optional, Dict, Any

from core.domain.entities import RuleMatch, IntentRule
from shared.types import QueryText, IntentId
from shared.utils.text_processing import VietnameseTextProcessor


class RuleBasedDetectorImpl:
    """
    Optimized rule-based intent detector with early exit
    """
    
    def __init__(
        self,
        rules: List[IntentRule],
        text_processor: VietnameseTextProcessor,
        early_exit_threshold: float = 0.9
    ):
        self.rules = rules
        self.text_processor = text_processor
        self.early_exit_threshold = early_exit_threshold
        
        # Sort rules by priority and weight for better performance
        self.rules.sort(key=lambda r: (r.priority_weight, r.weight), reverse=True)
        
        print(f"✅ Rule-based detector initialized with {len(self.rules)} rules")
    
    async def detect(self, query: QueryText) -> Optional[RuleMatch]:
        """
        Detect intent using rule-based matching with early exit
        
        Args:
            query: Input query text
            
        Returns:
            RuleMatch if found, None otherwise
        """
        start_time = time.time()
        
        try:
            # Clean and normalize query
            cleaned_query = self.text_processor.clean_query(query)
            normalized_query = self.text_processor.normalize_vietnamese(cleaned_query)
            
            best_match = None
            best_score = 0.0
            
            # Check each rule
            for rule in self.rules:
                if not rule.enabled:
                    continue
                
                match = self._match_rule(rule, normalized_query, query)
                
                if match and match.score > best_score:
                    best_match = match
                    best_score = match.score
                    
                    # Early exit for high confidence matches
                    if best_score >= self.early_exit_threshold:
                        break
            
            processing_time = (time.time() - start_time) * 1000
            
            if best_match:
                print(f"🎯 Rule match: {best_match.intent_id} (score: {best_match.score:.3f}, time: {processing_time:.1f}ms)")
            
            return best_match
            
        except Exception as e:
            print(f"❌ Rule detection failed: {e}")
            return None
    
    def _match_rule(self, rule: IntentRule, normalized_query: str, original_query: str) -> Optional[RuleMatch]:
        """
        Match a single rule against the query
        
        Args:
            rule: Intent rule to match
            normalized_query: Normalized query text
            original_query: Original query text
            
        Returns:
            RuleMatch if rule matches, None otherwise
        """
        try:
            # Check for negative keywords first (quick rejection)
            if rule.has_negative_keywords(normalized_query):
                return None
            
            # Match keywords
            matched_keywords = rule.matches_keywords(normalized_query)
            
            # Match patterns
            matched_patterns = rule.matches_patterns(normalized_query)
            
            # Calculate score if we have any matches
            if matched_keywords or matched_patterns:
                score = self._calculate_score(
                    rule, matched_keywords, matched_patterns, normalized_query
                )
                
                # Find position of first match
                position = self._find_first_match_position(
                    normalized_query, matched_keywords, matched_patterns
                )
                
                return RuleMatch(
                    intent_id=rule.intent_id,
                    score=score,
                    matched_keywords=matched_keywords,
                    matched_patterns=matched_patterns,
                    weight=rule.weight,
                    position=position,
                    rule_metadata={
                        "rule_priority": rule.priority,
                        "rule_description": rule.description
                    }
                )
            
            return None
            
        except Exception as e:
            print(f"❌ Rule matching failed for {rule.intent_id}: {e}")
            return None
    
    def _calculate_score(
        self,
        rule: IntentRule,
        matched_keywords: List[str],
        matched_patterns: List[str],
        query: str
    ) -> float:
        """
        Calculate match score for a rule - Simplified logic similar to old system

        Args:
            rule: The intent rule
            matched_keywords: List of matched keywords
            matched_patterns: List of matched patterns
            query: The query text

        Returns:
            Calculated score (0.0 to 1.0+)
        """
        # Use old system logic for better scores
        score = 0.0

        # Keyword scoring: 0.4 * weight per keyword (like old system)
        if matched_keywords:
            score += len(matched_keywords) * 0.4 * rule.weight

        # Pattern scoring: 0.6 * weight per pattern (like old system)
        if matched_patterns:
            score += len(matched_patterns) * 0.6 * rule.weight

        # Apply priority weight
        score *= rule.priority_weight

        # Bonus for multiple matches (simplified)
        total_matches = len(matched_keywords) + len(matched_patterns)
        if total_matches > 1:
            score *= (1 + (total_matches - 1) * 0.1)  # 10% bonus per additional match

        # Bonus for exact keyword matches
        query_words = set(query.lower().split())
        exact_matches = sum(1 for kw in matched_keywords if kw.lower() in query_words)
        if exact_matches > 0:
            score *= (1 + exact_matches * 0.05)  # 5% bonus per exact match

        # Cap at 1.0 like old system for consistency
        return min(score, 1.0)
    
    def _find_first_match_position(
        self, 
        query: str, 
        matched_keywords: List[str], 
        matched_patterns: List[str]
    ) -> int:
        """Find position of first match in query"""
        positions = []
        
        # Find keyword positions
        for keyword in matched_keywords:
            pos = query.lower().find(keyword.lower())
            if pos >= 0:
                positions.append(pos)
        
        # Find pattern positions (simplified)
        for pattern in matched_patterns:
            # This is a simplified approach - in practice you'd use the compiled regex
            pos = query.lower().find(pattern.lower()[:10])  # Use first 10 chars as approximation
            if pos >= 0:
                positions.append(pos)
        
        return min(positions) if positions else 0
    
    async def get_rules(self) -> List[IntentRule]:
        """Get all rules"""
        return self.rules.copy()
    
    def add_rule(self, rule: IntentRule) -> None:
        """Add a new rule"""
        self.rules.append(rule)
        # Re-sort rules
        self.rules.sort(key=lambda r: (r.priority_weight, r.weight), reverse=True)
        
        print(f"✅ Rule added: {rule.intent_id}")
    
    def remove_rule(self, intent_id: IntentId) -> bool:
        """Remove a rule by intent ID"""
        original_count = len(self.rules)
        self.rules = [r for r in self.rules if r.intent_id != intent_id]
        
        removed = len(self.rules) < original_count
        if removed:
            print(f"✅ Rule removed: {intent_id}")
        
        return removed
    
    def get_rule_stats(self) -> Dict[str, Any]:
        """Get statistics about rules"""
        if not self.rules:
            return {}
        
        return {
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules if r.enabled),
            "disabled_rules": sum(1 for r in self.rules if not r.enabled),
            "total_keywords": sum(len(r.keywords) for r in self.rules),
            "total_patterns": sum(len(r.patterns) for r in self.rules),
            "priority_distribution": {
                "high": sum(1 for r in self.rules if r.priority == "high"),
                "medium": sum(1 for r in self.rules if r.priority == "medium"),
                "low": sum(1 for r in self.rules if r.priority == "low")
            },
            "weight_stats": {
                "min": min(r.weight for r in self.rules),
                "max": max(r.weight for r in self.rules),
                "avg": sum(r.weight for r in self.rules) / len(self.rules)
            }
        }
