
"""
Formatter for admission method data
"""

from typing import Any, Dict, List, Optional


class AdmissionMethodFormatter:
    """Formats admission method data into human-readable strings"""

    def format_admission_methods_list(
        self,
        methods: List[Dict[str, Any]],
        meta: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Formats a list of admission methods into a string"""
        if not methods:
            return "Hiện tại không có thông tin phương thức tuyển sinh nào phù hợp."

        year = filters.get("year") if filters else None
        title = f"📝 **Các phương thức xét tuyển năm {year}**\n" if year else "📝 **Các phương thức xét tuyển**\n"
        
        lines = [title]
        for idx, m in enumerate(methods):
            lines.append(
                f"{idx + 1}. **{m.get('name', 'N/A')}** (`{m.get('method_code', 'N/A')}`)"
            )
        
        lines.append("\n👉 Để xem chi tiết yêu cầu của từng phương thức, bạn vui lòng hỏi cụ thể hơn nhé.")
        
        if meta.get("has_next"):
            lines.append(
                "💡 Gợi ý: Vẫn còn các phương thức khác, hãy thử tìm kiếm với bộ lọc chi tiết hơn."
            )

        return "\n".join(lines)

    def format_admission_method_details(self, method: Dict[str, Any]) -> str:
        """Formats a single admission method's details into a string"""
        if not method:
            return "Không tìm thấy thông tin chi tiết cho phương thức tuyển sinh này."

        name = method.get("name", "N/A")
        code = method.get("method_code", "N/A")

        lines = [
            f"📄 **Chi Tiết Phương Thức Tuyển Sinh: {name}** (`{code}`)\n",
            f"**- Yêu cầu:**\n{self._format_multiline(method.get('requirements') or '')}",
            f"**- Ghi chú:**\n{self._format_multiline(method.get('notes') or '')}",
            f"**- Áp dụng cho năm:** {method.get('year', 'N/A')}",
            f"**- Trạng thái:** {'Đang áp dụng' if method.get('is_active') else 'Không áp dụng'}",
        ]

        return "\n".join(lines)

    def _format_multiline(self, text: str) -> str:
        """Helper to format multiline text with indentation"""
        if not text:
            return "  - Chưa có thông tin"
        return "\n".join([f"  - {line.strip()}" for line in text.split('\n') if line.strip()]) 