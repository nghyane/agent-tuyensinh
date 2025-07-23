"""
University Formatters for Agno Framework
Response formatting classes for university data
"""

from typing import Any, Dict, List, Optional

from shared.utils.text_processing import VietnameseTextProcessor


class BaseFormatter:
    """Base formatter with common utilities"""

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
            return f"📚 {empty_message}"

        result = f"📚 **{title}**\n\n"

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


class DepartmentFormatter(BaseFormatter):
    """Formatter for department data"""

    def format_department(self, dept: Dict[str, Any]) -> str:
        """Format single department"""
        name = dept.get("name", "N/A")
        name_en = dept.get("name_en", "")
        code = dept.get("code", "N/A")
        dept_id = dept.get("id", "N/A")
        description = dept.get("description", "")

        result = f"🏛️ **{name}**\n"
        if name_en:
            result += f"   📝 English: {name_en}\n"
        result += f"   🔖 Code: {code}\n"
        result += f"   🆔 ID: {dept_id}\n"
        if description:
            clean_desc = self.text_processor.clean_query(description)
            result += f"   📄 Mô tả: {clean_desc}\n"
        result += "\n"
        return result

    def format_departments_list(
        self, departments: List[Dict[str, Any]], meta: Dict[str, Any]
    ) -> str:
        """Format departments list"""
        return self._format_list_response(
            departments,
            meta,
            "DANH SÁCH KHOA/PHÒNG BAN FPT UNIVERSITY",
            self.format_department,
            "Không tìm thấy thông tin khoa/phòng ban nào.",
        )


class ProgramFormatter(BaseFormatter):
    """Formatter for program data"""

    def format_program(self, program: Dict[str, Any]) -> str:
        """Format single program"""
        name = program.get("name", "N/A")
        name_en = program.get("name_en", "")
        code = program.get("code", "N/A")
        program_id = program.get("id", "N/A")
        duration = program.get("duration_years", "N/A")
        department = program.get("department", {})

        if isinstance(department, dict):
            dept_name = department.get("name", "N/A")
        else:
            dept_name = "N/A"

        result = f"🎯 **{name}**\n"
        if name_en:
            result += f"   📝 English: {name_en}\n"
        result += f"   🔖 Code: {code}\n"
        result += f"   🆔 ID: {program_id}\n"
        result += f"   ⏱️ Thời gian: {duration} năm\n"
        result += f"   🏛️ Khoa: {dept_name}\n\n"
        return result

    def format_programs_list(
        self,
        programs: List[Dict[str, Any]],
        meta: Dict[str, Any],
        department_code: Optional[str] = None,
    ) -> str:
        """Format programs list"""
        filter_text = f" (khoa: {department_code})" if department_code else ""
        empty_msg = f"Không tìm thấy chương trình học nào{filter_text}."

        return self._format_list_response(
            programs,
            meta,
            "DANH SÁCH CHƯƠNG TRÌNH HỌC FPT UNIVERSITY",
            self.format_program,
            empty_msg,
        )

    def format_program_details(self, program: Dict[str, Any]) -> str:
        """Format program details"""
        if not isinstance(program, dict):
            return "❌ Không tìm thấy thông tin chương trình học."

        name = program.get("name", "N/A")
        name_en = program.get("name_en", "")
        code = program.get("code", "N/A")
        program_id = program.get("id", "N/A")
        duration = program.get("duration_years", "N/A")
        department = program.get("department", {})

        if isinstance(department, dict):
            dept_name = department.get("name", "N/A")
            dept_code = department.get("code", "N/A")
            dept_name_en = department.get("name_en", "")
        else:
            dept_name = "N/A"
            dept_code = "N/A"
            dept_name_en = ""

        result = "🎯 **CHI TIẾT CHƯƠNG TRÌNH HỌC**\n\n"
        result += f"📚 **Tên chương trình**: {name}\n"
        if name_en:
            result += f"📝 **English**: {name_en}\n"
        result += f"🔖 **Mã chương trình**: {code}\n"
        result += f"🆔 **ID chương trình**: {program_id}\n"
        result += f"⏱️ **Thời gian đào tạo**: {duration} năm\n\n"

        result += "🏛️ **THÔNG TIN KHOA**\n"
        result += f"   📚 Tên khoa: {dept_name}\n"
        if dept_name_en:
            result += f"   📝 English: {dept_name_en}\n"
        result += f"   🔖 Mã khoa: {dept_code}\n"

        return result


class CampusFormatter(BaseFormatter):
    """Formatter for campus data"""

    def format_campus(self, campus: Dict[str, Any]) -> str:
        """Format single campus"""
        name = campus.get("name", "N/A")
        code = campus.get("code", "N/A")
        campus_id = campus.get("id", "N/A")
        city = campus.get("city", "N/A")
        address = campus.get("address", "")
        phone = campus.get("phone", "")
        email = campus.get("email", "")
        discount = campus.get("discount_percentage", 0)

        prep_fees = campus.get("preparation_fees", {})
        orientation = (
            prep_fees.get("orientation", {}) if isinstance(prep_fees, dict) else {}
        )
        english_prep = (
            prep_fees.get("english_prep", {}) if isinstance(prep_fees, dict) else {}
        )

        available_programs = campus.get("available_programs", {})
        program_count = (
            available_programs.get("count", 0)
            if isinstance(available_programs, dict)
            else 0
        )

        result = f"🏛️ **{name}**\n"
        result += f"   🔖 Code: {code}\n"
        result += f"   🆔 ID: {campus_id}\n"
        result += f"   📍 Thành phố: {city}\n"

        if address:
            clean_address = self.text_processor.clean_query(address)
            result += f"   🏠 Địa chỉ: {clean_address}\n"
        if phone:
            result += f"   📞 Điện thoại: {phone}\n"
        if email:
            result += f"   📧 Email: {email}\n"

        if discount > 0:
            result += f"   💰 Giảm giá: {discount}%\n"

        result += f"   🎓 Số chương trình: {program_count}\n"

        # Foundation fees with proper formatting
        if isinstance(orientation, dict) and orientation.get("fee"):
            fee = orientation.get("fee", 0)
            if isinstance(fee, (int, float)):
                result += f"   📚 Phí định hướng: {fee:,} VND\n"
        if isinstance(english_prep, dict) and english_prep.get("fee"):
            fee = english_prep.get("fee", 0)
            if isinstance(fee, (int, float)):
                result += f"   🇬🇧 Phí tiếng Anh: {fee:,} VND\n"

        result += "\n"
        return result

    def format_campuses_list(
        self, campuses: List[Dict[str, Any]], meta: Dict[str, Any], year: int = 2025
    ) -> str:
        """Format campuses list"""
        return self._format_list_response(
            campuses,
            meta,
            f"DANH SÁCH CAMPUS FPT UNIVERSITY ({year})",
            self.format_campus,
            "Không tìm thấy thông tin campus nào.",
        )

    def format_basic_campus_info(self, campus: Dict[str, Any]) -> str:
        """Format basic campus information"""
        name = campus.get("name", "N/A")
        code = campus.get("code", "N/A")
        campus_id = campus.get("id", "N/A")
        city = campus.get("city", "N/A")
        address = campus.get("address", "")

        result = "🏛️ **CHI TIẾT CAMPUS FPT UNIVERSITY**\n\n"
        result += f"🏫 **Tên campus**: {name}\n"
        result += f"🔖 **Mã campus**: {code}\n"
        result += f"🆔 **ID campus**: {campus_id}\n"
        result += f"📍 **Thành phố**: {city}\n"

        if address:
            clean_address = self.text_processor.clean_query(address)
            result += f"🏠 **Địa chỉ**: {clean_address}\n"

        return result

    def format_contact_info(self, campus: Dict[str, Any]) -> str:
        """Format contact information"""
        phone = campus.get("phone", "")
        email = campus.get("email", "")

        result = "\n📞 **THÔNG TIN LIÊN HỆ**\n"
        if phone:
            result += f"   📞 Điện thoại: {phone}\n"
        if email:
            result += f"   📧 Email: {email}\n"

        return result

    def format_discount_info(self, campus: Dict[str, Any]) -> str:
        """Format discount information"""
        discount = campus.get("discount_percentage", 0)

        if discount > 0:
            return f"\n💰 **ƯU ĐÃI**\n   🎯 Giảm giá: {discount}%\n"
        return ""

    def format_programs_info(self, campus: Dict[str, Any]) -> str:
        """Format programs information"""
        available_programs = campus.get("available_programs", {})
        if isinstance(available_programs, dict):
            program_count = available_programs.get("count", 0)
            program_codes = available_programs.get("codes", [])
        else:
            program_count = 0
            program_codes = []

        result = "\n🎓 **CHƯƠNG TRÌNH HỌC**\n"
        result += f"   📊 Tổng số chương trình: {program_count}\n"

        if program_codes and len(program_codes) > 0:
            result += f"   📚 Mã chương trình: {', '.join(program_codes[:10])}"
            if len(program_codes) > 10:
                result += f" (và {len(program_codes) - 10} chương trình khác)"
            result += "\n"

        return result

    def _format_foundation_fee(
        self, fee_info: Dict[str, Any], fee_type: str, emoji: str
    ) -> str:
        """Format foundation fee information"""
        if not isinstance(fee_info, dict) or not fee_info.get("fee"):
            return ""

        fee = fee_info.get("fee", 0)
        is_mandatory = fee_info.get("is_mandatory", False)
        max_periods = fee_info.get("max_periods", 0)
        description = fee_info.get("description", "")

        if not isinstance(fee, (int, float)):
            return ""

        result = f"   {emoji} **{fee_type}**: {fee:,} VND\n"
        result += f"      {'🔴 Bắt buộc' if is_mandatory else '🟡 Tùy chọn'}\n"
        result += f"      ⏱️ Thời gian tối đa: {max_periods} kỳ\n"

        if description:
            clean_desc = self.text_processor.clean_query(description)
            result += f"      📝 {clean_desc}\n"

        return result

    def format_foundation_fees(self, campus: Dict[str, Any], year: int) -> str:
        """Format foundation fees information"""
        prep_fees = campus.get("preparation_fees", {})
        orientation = (
            prep_fees.get("orientation", {}) if isinstance(prep_fees, dict) else {}
        )
        english_prep = (
            prep_fees.get("english_prep", {}) if isinstance(prep_fees, dict) else {}
        )

        result = f"\n💳 **PHÍ FOUNDATION ({year})**\n"
        result += self._format_foundation_fee(orientation, "Phí định hướng", "📚")
        result += self._format_foundation_fee(english_prep, "Phí tiếng Anh", "🇬🇧")

        return result

    def format_campus_details(self, campus: Dict[str, Any], year: int = 2025) -> str:
        """Format campus details"""
        if not isinstance(campus, dict):
            return "❌ Không tìm thấy thông tin campus."

        result = self.format_basic_campus_info(campus)
        result += self.format_contact_info(campus)
        result += self.format_discount_info(campus)
        result += self.format_programs_info(campus)
        result += self.format_foundation_fees(campus, year)

        return result
