"""
Tuition Formatter for Agno Framework
Response formatting for tuition data
"""

from typing import Any, Dict, List, Optional

from shared.utils.text_processing import VietnameseTextProcessor


class TuitionFormatter:
    """Formatter for tuition data"""

    def __init__(self):
        self.text_processor = VietnameseTextProcessor()

    def _format_list_response(
        self,
        items: List[Dict[str, Any]],
        meta: Dict[str, Any],
        title: str,
        format_item_func,
        empty_message: str,
    ) -> str:
        """Helper method to format list responses consistently"""
        if not items:
            return f"💰 {empty_message}"

        result = f"💰 **{title}**\n\n"

        for item in items:
            if isinstance(item, dict):
                result += format_item_func(item)

        # Add pagination info
        total = meta.get("total", len(items))
        has_next = meta.get("has_next", False)

        result += f"\n📊 **Thống kê**: Hiển thị {len(items)}/{total} kết quả"
        if has_next:
            result += f" (có thêm {total - len(items)} kết quả khác)"

        return result

    def format_tuition_record(self, tuition: Dict[str, Any]) -> str:
        """Format single tuition record"""
        program_name = tuition.get("program_name", "N/A")
        program_code = tuition.get("program_code", "N/A")
        campus_name = tuition.get("campus_name", "N/A")
        campus_code = tuition.get("campus_code", "N/A")
        campus_city = tuition.get("campus_city", "N/A")
        department_name = tuition.get("department_name", "N/A")
        year = tuition.get("year", "N/A")
        
        semester_1_3 = tuition.get("semester_group_1_3_fee", 0)
        semester_4_6 = tuition.get("semester_group_4_6_fee", 0)
        semester_7_9 = tuition.get("semester_group_7_9_fee", 0)
        total_fee = tuition.get("total_program_fee", 0)
        min_semester = tuition.get("min_semester_fee", 0)
        max_semester = tuition.get("max_semester_fee", 0)
        campus_discount = tuition.get("campus_discount", 0)

        result = f"💰 **{program_name}** ({program_code})\n"
        result += f"   🏛️ Khoa: {department_name}\n"
        result += f"   🏫 Campus: {campus_name} ({campus_code}) - {campus_city}\n"
        result += f"   📅 Năm: {year}\n"
        
        if campus_discount > 0:
            result += f"   🎯 Giảm giá: {campus_discount}%\n"
        
        result += f"   💳 Học phí theo kỳ:\n"
        result += f"      📚 Kỳ 1-3: {semester_1_3:,} VND\n"
        result += f"      📚 Kỳ 4-6: {semester_4_6:,} VND\n"
        result += f"      📚 Kỳ 7-9: {semester_7_9:,} VND\n"
        result += f"   💰 Tổng học phí: {total_fee:,} VND\n"
        result += f"   📊 Phạm vi: {min_semester:,} - {max_semester:,} VND/kỳ\n\n"
        
        return result

    def format_tuition_list(
        self,
        tuition_records: List[Dict[str, Any]],
        meta: Dict[str, Any],
        filters: Optional[Dict[str, str]] = None,
    ) -> str:
        """Format tuition list"""
        filter_text = ""
        if filters:
            filter_parts = []
            if filters.get("program_code"):
                filter_parts.append(f"ngành: {filters['program_code']}")
            if filters.get("campus_code"):
                filter_parts.append(f"campus: {filters['campus_code']}")
            if filters.get("department_code"):
                filter_parts.append(f"khoa: {filters['department_code']}")
            if filters.get("year"):
                filter_parts.append(f"năm: {filters['year']}")
            
            if filter_parts:
                filter_text = f" ({', '.join(filter_parts)})"

        empty_msg = f"Không tìm thấy thông tin học phí nào{filter_text}."

        return self._format_list_response(
            tuition_records,
            meta,
            "DANH SÁCH HỌC PHÍ FPT UNIVERSITY",
            self.format_tuition_record,
            empty_msg,
        )

    def format_tuition_details(self, tuition: Dict[str, Any]) -> str:
        """Format tuition details"""
        if not isinstance(tuition, dict):
            return "❌ Không tìm thấy thông tin học phí."

        program_name = tuition.get("program_name", "N/A")
        program_name_en = tuition.get("program_name_en", "")
        program_code = tuition.get("program_code", "N/A")
        program_id = tuition.get("program_id", "N/A")
        
        campus_name = tuition.get("campus_name", "N/A")
        campus_code = tuition.get("campus_code", "N/A")
        campus_city = tuition.get("campus_city", "N/A")
        campus_id = tuition.get("campus_id", "N/A")
        campus_discount = tuition.get("campus_discount", 0)
        
        department_name = tuition.get("department_name", "N/A")
        department_name_en = tuition.get("department_name_en", "")
        department_code = tuition.get("department_code", "N/A")
        department_id = tuition.get("department_id", "N/A")
        
        year = tuition.get("year", "N/A")
        tuition_id = tuition.get("id", "N/A")
        
        semester_1_3 = tuition.get("semester_group_1_3_fee", 0)
        semester_4_6 = tuition.get("semester_group_4_6_fee", 0)
        semester_7_9 = tuition.get("semester_group_7_9_fee", 0)
        total_fee = tuition.get("total_program_fee", 0)
        min_semester = tuition.get("min_semester_fee", 0)
        max_semester = tuition.get("max_semester_fee", 0)

        result = "💰 **CHI TIẾT HỌC PHÍ FPT UNIVERSITY**\n\n"
        
        result += "🎯 **THÔNG TIN CHƯƠNG TRÌNH**\n"
        result += f"   📚 Tên chương trình: {program_name}\n"
        if program_name_en:
            result += f"   📝 English: {program_name_en}\n"
        result += f"   🔖 Mã chương trình: {program_code}\n"
        result += f"   🆔 ID chương trình: {program_id}\n\n"
        
        result += "🏛️ **THÔNG TIN KHOA**\n"
        result += f"   📚 Tên khoa: {department_name}\n"
        if department_name_en:
            result += f"   📝 English: {department_name_en}\n"
        result += f"   🔖 Mã khoa: {department_code}\n"
        result += f"   🆔 ID khoa: {department_id}\n\n"
        
        result += "🏫 **THÔNG TIN CAMPUS**\n"
        result += f"   🏫 Tên campus: {campus_name}\n"
        result += f"   🔖 Mã campus: {campus_code}\n"
        result += f"   📍 Thành phố: {campus_city}\n"
        result += f"   🆔 ID campus: {campus_id}\n"
        if campus_discount > 0:
            result += f"   🎯 Giảm giá: {campus_discount}%\n"
        result += "\n"
        
        result += f"📅 **NĂM HỌC**: {year}\n"
        result += f"🆔 **ID học phí**: {tuition_id}\n\n"
        
        result += "💳 **CHI TIẾT HỌC PHÍ**\n"
        result += f"   📚 Kỳ 1-3: {semester_1_3:,} VND\n"
        result += f"   📚 Kỳ 4-6: {semester_4_6:,} VND\n"
        result += f"   📚 Kỳ 7-9: {semester_7_9:,} VND\n"
        result += f"   💰 Tổng học phí: {total_fee:,} VND\n"
        result += f"   📊 Phạm vi: {min_semester:,} - {max_semester:,} VND/kỳ\n"

        return result

    def format_campus_tuition_summary(self, campus_data: Dict[str, Any], year: int) -> str:
        """Format campus tuition summary"""
        if not isinstance(campus_data, dict):
            return "❌ Không tìm thấy thông tin tổng hợp học phí campus."

        campus_name = campus_data.get("campus_name", "N/A")
        campus_code = campus_data.get("campus_code", "N/A")
        campus_city = campus_data.get("campus_city", "N/A")
        campus_id = campus_data.get("campus_id", "N/A")
        discount_percentage = campus_data.get("discount_percentage", 0)
        
        total_programs = campus_data.get("total_programs", 0)
        total_departments = campus_data.get("total_departments", 0)
        
        min_semester_fee = campus_data.get("min_semester_fee", 0)
        max_semester_fee = campus_data.get("max_semester_fee", 0)
        avg_semester_1_3_fee = campus_data.get("avg_semester_1_3_fee", 0)
        avg_semester_4_6_fee = campus_data.get("avg_semester_4_6_fee", 0)
        avg_semester_7_9_fee = campus_data.get("avg_semester_7_9_fee", 0)
        
        programs = campus_data.get("programs", [])

        result = f"💰 **TỔNG HỢP HỌC PHÍ CAMPUS {year}**\n\n"
        
        result += "🏫 **THÔNG TIN CAMPUS**\n"
        result += f"   🏫 Tên campus: {campus_name}\n"
        result += f"   🔖 Mã campus: {campus_code}\n"
        result += f"   📍 Thành phố: {campus_city}\n"
        result += f"   🆔 ID campus: {campus_id}\n"
        if discount_percentage > 0:
            result += f"   🎯 Giảm giá: {discount_percentage}%\n"
        result += "\n"
        
        result += "📊 **THỐNG KÊ TỔNG QUAN**\n"
        result += f"   🎓 Tổng số chương trình: {total_programs}\n"
        result += f"   🏛️ Tổng số khoa: {total_departments}\n"
        result += f"   💰 Phạm vi học phí: {min_semester_fee:,} - {max_semester_fee:,} VND/kỳ\n"
        result += "\n"
        
        result += "📈 **HỌC PHÍ TRUNG BÌNH**\n"
        result += f"   📚 Kỳ 1-3: {avg_semester_1_3_fee:,} VND\n"
        result += f"   📚 Kỳ 4-6: {avg_semester_4_6_fee:,} VND\n"
        result += f"   📚 Kỳ 7-9: {avg_semester_7_9_fee:,} VND\n\n"
        
        if programs:
            result += "📚 **DANH SÁCH CHƯƠNG TRÌNH**\n"
            for program in programs[:10]:  # Limit to first 10
                program_name = program.get("program_name", "N/A")
                program_code = program.get("program_code", "N/A")
                department_name = program.get("department_name", "N/A")
                semester_1_3 = program.get("semester_1_3_fee", 0)
                semester_4_6 = program.get("semester_4_6_fee", 0)
                semester_7_9 = program.get("semester_7_9_fee", 0)
                
                result += f"   🎯 **{program_name}** ({program_code})\n"
                result += f"      🏛️ Khoa: {department_name}\n"
                result += f"      💰 Học phí: {semester_1_3:,} - {semester_4_6:,} - {semester_7_9:,} VND\n"
            
            if len(programs) > 10:
                result += f"   ... và {len(programs) - 10} chương trình khác\n"

        return result 