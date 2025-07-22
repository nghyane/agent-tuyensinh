"""
Intent Detection Tool for Agno Framework
Wrapper cho existing intent detection service để sử dụng như một tool trong Agno
Tối ưu hóa với TemplateManager để quản lý text resources
"""

import asyncio
from typing import Dict, Any, Optional

from agno.tools.toolkit import Toolkit
from core.domain.entities import DetectionContext, IntentResult
from core.application.services.hybrid_intent_service import HybridIntentDetectionService
from shared.types import DetectionMethod
from shared.utils.template_manager import template_manager, TemplateContext


class IntentDetectionTool(Toolkit):
    """
    Tool để phát hiện ý định của người dùng sử dụng existing FPT intent detection service
    Tối ưu hóa cho Agno framework với async support và better error handling
    """

    def __init__(self, intent_service: HybridIntentDetectionService):
        """
        Initialize IntentDetectionTool

        Args:
            intent_service: Instance của HybridIntentDetectionService
        """
        self.intent_service = intent_service

        super().__init__(name="intent_detection")

        # Register the detect function
        self.register(self.detect_intent)

    async def detect_intent(self, query: str, user_id: str = "agno_user", language: Optional[str] = None) -> str:
        """
        Phát hiện ý định của người dùng trong tiếng Việt và tiếng Anh.

        Sử dụng hybrid approach (rule-based + vector search) để xác định intent.

        Args:
            query: Câu hỏi hoặc yêu cầu của người dùng cần phát hiện intent
            user_id: ID của người dùng (mặc định: 'agno_user')
            language: Ngôn ngữ ('vi' hoặc 'en'), auto-detect nếu None

        Returns:
            Kết quả intent detection với confidence và suggestions
        """
        try:
            # Auto-detect language nếu không được chỉ định
            if language is None:
                language = self._detect_language(query)

            # Tạo detection context
            context = DetectionContext(
                query=query,
                user_id=user_id,
                language=language
            )

            # Chạy intent detection với timeout
            result = await asyncio.wait_for(
                self.intent_service.detect_intent(context),
                timeout=10.0  # 10 second timeout
            )

            # Format kết quả
            return self._format_result(result, query)

        except asyncio.TimeoutError:
            return self._handle_timeout_error(query, language or "vi")
        except Exception as e:
            return self._handle_general_error(query, language or "vi", str(e))

    def _detect_language(self, query: str) -> str:
        """
        Tự động phát hiện ngôn ngữ của query

        Args:
            query: Câu hỏi cần phát hiện ngôn ngữ

        Returns:
            Mã ngôn ngữ ('vi' hoặc 'en')
        """
        # Sử dụng VietnameseTextProcessor nếu có sẵn
        if hasattr(self.intent_service, 'text_processor'):
            return self.intent_service.text_processor.detect_language(query)

        # Fallback đơn giản
        return "vi" if any(ord(c) > 127 for c in query) else "en"

    def _format_result(self, result: IntentResult, original_query: str) -> str:
        """Format intent detection result using TemplateManager"""
        language = self._detect_language(original_query)

        # Get action suggestions and format metadata
        action_suggestions = template_manager.get_action_suggestions(result.id, language)
        metadata_info = template_manager.format_metadata(result.metadata, language)

        # Create template context
        context = TemplateContext(
            query=original_query,
            intent_id=result.id,
            confidence=result.confidence,
            method=result.method.value,
            timestamp=result.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            metadata_info=metadata_info,
            action_suggestions=action_suggestions
        )

        return template_manager.render_result_template(context, language)

    def _handle_timeout_error(self, query: str, language: str) -> str:
        """
        Xử lý timeout error một cách gọn gàng và đẹp

        Args:
            query: Câu hỏi gốc
            language: Ngôn ngữ hiện tại

        Returns:
            Kết quả fallback được format đẹp
        """
        error_template = template_manager.get_error_template("timeout", language)

        # Tạo fallback result
        fallback_result = IntentResult(
            id=error_template.get('fallback_intent', 'unknown'),
            confidence=float(error_template.get('fallback_confidence', '0.1')),
            method=DetectionMethod.FALLBACK,
            metadata={
                'timeout_duration': '10s',
                'original_query': query,
                'error_type': 'timeout'
            }
        )

        # Format như kết quả bình thường nhưng với thông tin timeout
        return self._format_result(fallback_result, query)

    def _handle_general_error(self, query: str, language: str, error_message: str) -> str:
        """
        Xử lý general error một cách gọn gàng và đẹp

        Args:
            query: Câu hỏi gốc
            language: Ngôn ngữ hiện tại
            error_message: Thông báo lỗi

        Returns:
            Kết quả fallback được format đẹp
        """
        error_template = template_manager.get_error_template("general", language)

        # Tạo fallback result
        fallback_result = IntentResult(
            id=error_template.get('fallback_intent', 'unknown'),
            confidence=float(error_template.get('fallback_confidence', '0.1')),
            method=DetectionMethod.FALLBACK,
            metadata={
                'error_message': error_message,
                'original_query': query,
                'error_type': 'general'
            }
        )

        # Format như kết quả bình thường nhưng với thông tin lỗi
        return self._format_result(fallback_result, query)


    def get_tool_info(self) -> Dict[str, Any]:
        """
        Lấy thông tin về tool (dành cho debugging và monitoring)

        Returns:
            Dictionary chứa thông tin tool
        """
        return {
            "name": self.name,
            "functions": list(self.functions.keys()),
            "intent_service_available": self.intent_service is not None,
            "version": "1.0.0"
        }


def create_intent_detection_tool(intent_service: HybridIntentDetectionService) -> Toolkit:
    """
    Factory function để tạo IntentDetectionTool

    Args:
        intent_service: Instance của HybridIntentDetectionService

    Returns:
        Toolkit instance (IntentDetectionTool)
    """
    return IntentDetectionTool(intent_service)
