"""
Template Manager for managing text templates and resources
Clean and simple implementation
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TemplateContext:
    """Context data for template rendering"""

    query: str = ""
    intent_id: str = ""
    confidence: float = 0.0
    method: str = ""
    timestamp: str = ""
    metadata_info: str = ""
    action_suggestions: List[str] = field(default_factory=list)


@dataclass
class TemplateConfig:
    """Template configuration"""

    templates_dir: str = "data"
    default_language: str = "vi"
    fallback_language: str = "en"


@dataclass
class ResultTemplateData:
    """Template data for result rendering"""

    header: str = "🎯 INTENT DETECTION RESULT"
    separator: str = "========================="
    query_label: str = "📝 Query"
    intent_label: str = "Intent"
    confidence_label: str = "📊 Confidence"
    method_label: str = "Method"
    timestamp_label: str = "🕐 Timestamp"
    metadata_header: str = "📊 METADATA:"
    action_suggestions_header: str = "💡 ACTION SUGGESTIONS:"
    next_steps_header: str = "📋 NEXT STEPS:"
    next_steps_items: List[str] = field(default_factory=list)


class TemplateManager:
    """Clean template manager for intent detection results"""

    def __init__(self, config: Optional[TemplateConfig] = None):
        self.config = config or TemplateConfig()
        self.templates_dir = Path(self.config.templates_dir)
        self._templates: Dict[str, Any] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load templates from JSON file"""
        templates_file = self.templates_dir / "templates.json"

        if templates_file.exists():
            with open(templates_file, "r", encoding="utf-8") as f:
                self._templates = json.load(f)
        else:
            print(f"⚠️ Templates file not found: {templates_file}")

    def _get_section_data(self, section: str) -> Dict[str, Any]:
        """Get section data from templates"""
        return self._templates.get("intent_detection", {}).get(section, {})

    def _get_language_data(self, data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Get language-specific data with fallback"""
        return data.get(language, data.get(self.config.fallback_language, {}))

    def _get_result_template_data(self, language: str) -> ResultTemplateData:
        """Get result template data with defaults"""
        section_data = self._get_section_data("result_template")
        template_data = self._get_language_data(section_data, language)

        return ResultTemplateData(
            header=template_data.get("header", "🎯 INTENT DETECTION RESULT"),
            separator=template_data.get("separator", "========================="),
            query_label=template_data.get("query_label", "📝 Query"),
            intent_label=template_data.get("intent_label", "Intent"),
            confidence_label=template_data.get("confidence_label", "📊 Confidence"),
            method_label=template_data.get("method_label", "Method"),
            timestamp_label=template_data.get("timestamp_label", "🕐 Timestamp"),
            metadata_header=template_data.get("metadata_header", "📊 METADATA:"),
            action_suggestions_header=template_data.get(
                "action_suggestions_header", "💡 ACTION SUGGESTIONS:"
            ),
            next_steps_header=template_data.get("next_steps_header", "📋 NEXT STEPS:"),
            next_steps_items=template_data.get("next_steps_items", []),
        )

    def get_action_suggestions(self, intent_id: str, language: str = "vi") -> List[str]:
        """Get action suggestions for intent"""
        section_data = self._get_section_data("action_suggestions")
        intent_data = section_data.get(intent_id, {})

        suggestions = self._get_language_data(intent_data, language)
        if not suggestions:
            default_data = section_data.get("default", {})
            suggestions = self._get_language_data(default_data, language)

        # Ensure suggestions is a list
        if isinstance(suggestions, list):
            return suggestions
        return []

    def get_error_template(
        self, error_type: str, language: str = "vi"
    ) -> Dict[str, str]:
        """Get error template data"""
        section_data = self._get_section_data("error_templates")
        error_data = section_data.get(error_type, {})

        result = self._get_language_data(error_data, language)
        if not result:
            general_data = section_data.get("general", {})
            result = self._get_language_data(general_data, language)

        return result or {}

    def get_metadata_labels(self, language: str = "vi") -> Dict[str, str]:
        """Get metadata labels"""
        section_data = self._get_section_data("metadata_labels")
        return self._get_language_data(section_data, language)

    def render_result_template(
        self, context: TemplateContext, language: str = "vi"
    ) -> str:
        """Render result template with clean formatting"""
        template_data = self._get_result_template_data(language)

        # Build result sections
        sections = [
            self._render_header(template_data),
            self._render_basic_info(context, template_data),
            self._render_metadata(context.metadata_info, template_data),
            self._render_suggestions(context.action_suggestions, template_data),
            self._render_next_steps(template_data),
        ]

        return "\n".join(filter(None, sections))

    def _render_header(self, template: ResultTemplateData) -> str:
        """Render template header"""
        return f"{template.header}\n{template.separator}"

    def _render_basic_info(
        self, context: TemplateContext, template: ResultTemplateData
    ) -> str:
        """Render basic information section"""
        confidence_emoji = self._get_confidence_emoji(context.confidence)
        method_emoji = self._get_method_emoji(context.method)

        lines = [
            f'{template.query_label}: "{context.query}"',
            f"{confidence_emoji} {template.intent_label}: {context.intent_id}",
            f"{template.confidence_label}: {context.confidence}",
            f"{method_emoji} {template.method_label}: {context.method}",
            f"{template.timestamp_label}: {context.timestamp}",
        ]

        return "\n".join(lines)

    def _render_metadata(self, metadata_info: str, template: ResultTemplateData) -> str:
        """Render metadata section"""
        if not metadata_info:
            return ""
        return f"\n{template.metadata_header}\n{metadata_info}"

    def _render_suggestions(
        self, suggestions: List[str], template: ResultTemplateData
    ) -> str:
        """Render action suggestions section"""
        if not suggestions:
            return ""

        items = "\n".join(f"• {suggestion}" for suggestion in suggestions)
        return f"\n{template.action_suggestions_header}\n{items}"

    def _render_next_steps(self, template: ResultTemplateData) -> str:
        """Render next steps section"""
        if not template.next_steps_items:
            return ""

        items = "\n".join(f"- {step}" for step in template.next_steps_items)
        return f"\n{template.next_steps_header}\n{items}"

    def format_metadata(self, metadata: Dict[str, Any], language: str = "vi") -> str:
        """Format metadata with clean structure"""
        if not metadata:
            return ""

        labels = self.get_metadata_labels(language)

        # Define metadata formatters
        formatters = {
            "matched_keywords": lambda v: f"{labels.get('keywords', '🔑 Keywords')}: {', '.join(v[:5])}",
            "matched_patterns": lambda v: f"{labels.get('patterns', '📝 Patterns')}: {v}",
            "confidence_adjusted": lambda _: labels.get(
                "confidence_adjusted", "🎯 Confidence adjusted"
            ),
            "vector_similarity": lambda v: f"{labels.get('vector_similarity', '🔍 Vector similarity')}: {v:.3f}",
            "from_cache": lambda _: labels.get("from_cache", "💾 From cache"),
            "processing_time_ms": lambda v: f"{labels.get('processing_time', '⚡ Processing time')}: {v:.1f}ms",
        }

        # Apply formatters and collect parts
        parts = [
            formatter(metadata[key])
            for key, formatter in formatters.items()
            if key in metadata and metadata[key]
        ]

        if not parts:
            return ""

        template_data = self._get_result_template_data(language)
        return f"{template_data.metadata_header}\n" + "\n".join(
            f"   {part}" for part in parts
        )

    def _get_confidence_emoji(self, confidence: float) -> str:
        """Get confidence emoji based on score"""
        if confidence >= 0.9:
            return "🟢"
        if confidence >= 0.7:
            return "🟡"
        if confidence >= 0.5:
            return "🟠"
        if confidence >= 0.3:
            return "🔴"
        return "⚫"

    def _get_method_emoji(self, method: str) -> str:
        """Get method emoji"""
        emojis = {
            "rule": "📏",
            "vector": "🔍",
            "hybrid": "🔀",
            "fallback": "🔄",
            "cache": "💾",
        }
        return emojis.get(method, "❓")


# Global template manager instance
template_manager = TemplateManager()
