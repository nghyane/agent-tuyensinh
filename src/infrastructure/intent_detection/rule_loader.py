"""
Production rule loader for FPT University Agent
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.domain.entities import IntentRule


class ProductionRuleLoader:
    """
    Loader for production intent rules from JSON configuration
    """
    
    def __init__(self, rules_file_path: Optional[str] = None):
        """
        Initialize rule loader
        
        Args:
            rules_file_path: Path to rules JSON file. If None, uses default production rules.
        """
        if rules_file_path is None:
            # Default to production rules in data directory
            current_dir = Path(__file__).parent.parent.parent.parent
            self.rules_file_path = current_dir / "data" / "production_rules.json"
        else:
            self.rules_file_path = Path(rules_file_path)
        
        self.rules_data: Optional[Dict[str, Any]] = None
        self.loaded_rules: List[IntentRule] = []
        
        print(f"📋 Rule loader initialized: {self.rules_file_path}")
        print(f"📁 File exists: {self.rules_file_path.exists()}")
    
    def load_rules(self) -> List[IntentRule]:
        """
        Load production rules from JSON file
        
        Returns:
            List of IntentRule objects
        """
        try:
            if not self.rules_file_path.exists():
                print(f"⚠️ Rules file not found: {self.rules_file_path}")
                print("🔄 Using default demo rules...")
                return get_default_demo_rules()
            
            # Load JSON data
            with open(self.rules_file_path, 'r', encoding='utf-8') as f:
                self.rules_data = json.load(f)
            
            # Validate structure
            self._validate_rules_structure()
            
            # Convert to IntentRule objects
            self.loaded_rules = self._convert_to_intent_rules()
            
            print(f"✅ Production rules loaded: {len(self.loaded_rules)} rules")
            print(f"📊 Version: {self.rules_data.get('version', 'unknown')}")
            
            return self.loaded_rules
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in rules file: {e}")
            return get_default_demo_rules()
            
        except Exception as e:
            print(f"❌ Failed to load production rules: {e}")
            return get_default_demo_rules()
    
    def _validate_rules_structure(self) -> None:
        """Validate the structure of loaded rules data"""
        if not isinstance(self.rules_data, dict):
            raise ValueError("Rules data must be a JSON object")
        
        if "rules" not in self.rules_data:
            raise ValueError("Rules data must contain 'rules' array")
        
        if not isinstance(self.rules_data["rules"], list):
            raise ValueError("'rules' must be an array")
        
        if len(self.rules_data["rules"]) == 0:
            raise ValueError("Rules array cannot be empty")
    
    def _convert_to_intent_rules(self) -> List[IntentRule]:
        """Convert JSON rule data to IntentRule objects"""
        intent_rules = []
        
        for rule_data in self.rules_data["rules"]:
            try:
                # Create IntentRule object
                intent_rule = IntentRule(
                    intent_id=rule_data["intent_id"],
                    keywords=rule_data["keywords"],
                    patterns=rule_data["patterns"],
                    weight=float(rule_data["weight"]),
                    description=rule_data.get("description", ""),
                    negative_keywords=rule_data.get("negative_keywords", []),
                    priority=rule_data.get("priority", "medium"),
                    enabled=rule_data.get("enabled", True),
                    metadata=rule_data.get("metadata", {})
                )
                
                intent_rules.append(intent_rule)
                
                print(f"  ✅ {intent_rule.intent_id}: {len(intent_rule.keywords)} keywords, {len(intent_rule.patterns)} patterns")
                
            except Exception as e:
                print(f"  ❌ Failed to convert rule {rule_data.get('intent_id', 'unknown')}: {e}")
                continue
        
        return intent_rules
    
    def get_rules_metadata(self) -> Dict[str, Any]:
        """Get metadata about loaded rules"""
        if not self.rules_data:
            return {}
        
        metadata = self.rules_data.get("metadata", {})
        
        # Add computed metadata
        if self.loaded_rules:
            metadata.update({
                "loaded_rule_count": len(self.loaded_rules),
                "intent_ids": [rule.intent_id for rule in self.loaded_rules],
                "total_keywords": sum(len(rule.keywords) for rule in self.loaded_rules),
                "total_patterns": sum(len(rule.patterns) for rule in self.loaded_rules)
            })
        
        return metadata


def get_default_demo_rules() -> List[IntentRule]:
    """
    Get default demo rules for testing when production rules are not available
    
    Returns:
        List of basic IntentRule objects for demo
    """
    print("📋 Loading default demo rules...")
    
    return [
        IntentRule(
            intent_id="tuition_inquiry",
            keywords=['học phí', 'tuition', 'phí', 'tiền', 'cost', 'chi phí'],
            patterns=[r"học phí.*(?:bao nhiêu|giá)", r"tuition.*(?:fee|cost)"],
            weight=1.4,
            description="Basic tuition inquiry rule"
        ),
        IntentRule(
            intent_id="campus_info", 
            keywords=['campus', 'cơ sở', 'thư viện', 'library', 'ký túc xá'],
            patterns=[r"(?:campus|cơ sở).*(?:ở đâu|where)", r"thư viện.*(?:giờ|hours)"],
            weight=1.2,
            description="Basic campus information rule"
        ),
        IntentRule(
            intent_id="program_information",
            keywords=['ngành', 'program', 'major', 'cntt', 'it', 'ai'],
            patterns=[r"ngành.*(?:nào|gì)", r"(?:program|major).*(?:available|có)"],
            weight=1.1,
            description="Basic program information rule"
        ),
        IntentRule(
            intent_id="admission_requirements",
            keywords=['điểm chuẩn', 'admission', 'requirements', 'yêu cầu', 'đầu vào'],
            patterns=[r"điểm chuẩn.*(?:bao nhiêu|2024|2025)", r"(?:yêu cầu|requirements).*(?:đầu vào|admission)"],
            weight=1.3,
            description="Basic admission requirements rule"
        )
    ]
