
"""
Formatter for scholarship data
"""

from typing import Any, Dict, List, Optional


class ScholarshipFormatter:
    """Formats scholarship data into human-readable strings"""

    def format_scholarships_list(
        self,
        scholarships: List[Dict[str, Any]],
        meta: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Formats a list of scholarships into a string"""
        if not scholarships:
            return "Hiện tại không có thông tin học bổng nào phù hợp với yêu cầu của bạn."

        year = filters.get("year") if filters else None
        title = f"📚 **Danh sách học bổng năm {year}**\n\n" if year else "📚 **Danh sách học bổng**\n\n"

        lines = [title]
        for idx, s in enumerate(scholarships):
            lines.append(
                f"{idx + 1}. **{s.get('name', 'N/A')}** (`{s.get('code', 'N/A')}`)"
            )
            lines.append(f"   - **Giá trị:** {self._format_percentage(s.get('percentage'))}")
            lines.append(f"   - **Loại:** {s.get('type', 'N/A').replace('_', ' ').title()}")
            lines.append("")

        if meta.get("has_next"):
            lines.append(
                "💡 Gợi ý: Còn nhiều học bổng khác, hãy thử tìm kiếm với các bộ lọc chi tiết hơn hoặc xem trang tiếp theo."
            )

        return "\n".join(lines)

    def format_scholarship_details(self, scholarship: Dict[str, Any]) -> str:
        """Formats a single scholarship's details into a string"""
        if not scholarship:
            return "Không tìm thấy thông tin chi tiết cho học bổng này."

        name = scholarship.get("name", "N/A")
        code = scholarship.get('code', "N/A")

        lines = [
            f"🎓 **Thông Tin Chi Tiết Học Bổng: {name}** (`{code}`)\n",
            f"**- Loại học bổng:** {scholarship.get('type', 'N/A').replace('_', ' ').title()}",
            f"**- Giá trị:** {self._format_percentage(scholarship.get('percentage'))}",
            f"**- Điều kiện:**\n{self._format_multiline(scholarship.get('requirements', 'Chưa có thông tin'))}",
            f"**- Ghi chú:**\n{self._format_multiline(scholarship.get('notes', 'Không có'))}",
            f"**- Trạng thái:** {'Còn hiệu lực' if scholarship.get('is_active') else 'Hết hiệu lực'}",
            f"**- Áp dụng cho năm:** {scholarship.get('year', 'N/A')}",
        ]

        return "\n".join(lines)

    def _format_percentage(self, percentage: Optional[int]) -> str:
        if percentage is None:
            return "Chưa có thông tin"
        if percentage == 100:
            return "Toàn phần"
        return f"{percentage}% học phí"

    def _format_multiline(self, text: str) -> str:
        """Helper to format multiline text with indentation"""
        if not text:
            return "  - Chưa có thông tin"
        return "\n".join([f"  - {line.strip()}" for line in text.split('\n') if line.strip()]) 