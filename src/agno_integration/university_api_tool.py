"""
University API Tool for Agno Framework
Main tool class that orchestrates between API client and formatters
"""

from typing import Optional

from agno.tools.toolkit import Toolkit

from infrastructure.api.university_client import UniversityApiClient
from shared.utils.admission_method_formatter import AdmissionMethodFormatter
from shared.utils.scholarship_formatter import ScholarshipFormatter
from shared.utils.tuition_formatter import TuitionFormatter
from shared.utils.university_formatters import (
    CampusFormatter,
    DepartmentFormatter,
    ProgramFormatter,
)


class UniversityApiTool(Toolkit):
    """
    University API tool for Agno framework
    Orchestrates between API client and formatters
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize UniversityApiTool

        Args:
            timeout: Request timeout in seconds
        """
        self.client = UniversityApiClient(timeout=timeout)
        self.department_formatter = DepartmentFormatter()
        self.program_formatter = ProgramFormatter()
        self.campus_formatter = CampusFormatter()
        self.tuition_formatter = TuitionFormatter()
        self.scholarship_formatter = ScholarshipFormatter()
        self.admission_method_formatter = AdmissionMethodFormatter()

        # Register all methods as tools
        super().__init__(
            name="university_api",
            tools=[
                self.get_departments,
                self.get_programs,
                self.get_program_details,
                self.get_campuses,
                self.get_campus_details,
                self.get_tuition_list,
                self.get_tuition_details,
                self.get_campus_tuition_summary,
                self.get_scholarships,
                self.get_scholarship_details,
                self.get_admission_methods,
                self.get_admission_method_details,
            ],
        )

    async def get_departments(self, limit: int = 100, offset: int = 0) -> str:
        """
        Lấy danh sách các khoa/phòng ban của FPT University

        Args:
            limit: Số lượng kết quả tối đa (1-100)
            offset: Vị trí bắt đầu lấy dữ liệu

        Returns:
            Danh sách khoa/phòng ban được format đẹp
        """
        result = await self.client.get_departments(limit=limit, offset=offset)

        if result.is_ok():
            data = result.data or {}
            departments = data.get("departments", [])
            meta = data.get("meta", {})

            return self.department_formatter.format_departments_list(departments, meta)
        else:
            return (
                f"❌ **Lỗi khi lấy thông tin khoa/phòng ban**\n\n"
                f"{result.error_message}"
            )

    async def get_programs(
        self,
        department_code: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> str:
        """
        Lấy danh sách chương trình học/ngành của FPT University

        Args:
            department_code: Mã khoa để lọc (optional)
            limit: Số lượng kết quả tối đa (1-100)
            offset: Vị trí bắt đầu lấy dữ liệu

        Returns:
            Danh sách chương trình học được format đẹp
        """
        result = await self.client.get_programs(
            department_code=department_code, limit=limit, offset=offset
        )

        if result.is_ok():
            data = result.data or {}
            programs = data.get("programs", [])
            meta = data.get("meta", {})

            return self.program_formatter.format_programs_list(
                programs, meta, department_code
            )
        else:
            return (
                f"❌ **Lỗi khi lấy thông tin chương trình học**\n\n"
                f"{result.error_message}"
            )

    async def get_program_details(self, program_id: str) -> str:
        """
        Lấy chi tiết một chương trình học cụ thể theo ID

        Args:
            program_id: UUID của chương trình học

        Returns:
            Chi tiết chương trình học được format đẹp
        """
        result = await self.client.get_program_details(program_id)

        if result.is_ok():
            program = result.data or {}
            return self.program_formatter.format_program_details(program)
        else:
            return (
                f"❌ **Lỗi khi lấy chi tiết chương trình học**\n\n"
                f"{result.error_message}"
            )

    async def get_campuses(
        self, year: int = 2025, limit: int = 100, offset: int = 0
    ) -> str:
        """
        Lấy danh sách campus của FPT University với thông tin phí foundation

        Args:
            year: Năm để lấy thông tin phí (2020-2030)
            limit: Số lượng kết quả tối đa (1-100)
            offset: Vị trí bắt đầu lấy dữ liệu

        Returns:
            Danh sách campus được format đẹp
        """
        result = await self.client.get_campuses(year=year, limit=limit, offset=offset)

        if result.is_ok():
            data = result.data or {}
            campuses = data.get("campuses", [])
            meta = data.get("meta", {})

            return self.campus_formatter.format_campuses_list(campuses, meta, year)
        else:
            return f"❌ **Lỗi khi lấy thông tin campus**\n\n" f"{result.error_message}"

    async def get_campus_details(self, campus_id: str, year: int = 2025) -> str:
        """
        Lấy chi tiết một campus cụ thể theo ID

        Args:
            campus_id: UUID của campus
            year: Năm để lấy thông tin phí (2020-2030)

        Returns:
            Chi tiết campus được format đẹp
        """
        result = await self.client.get_campus_details(campus_id, year)

        if result.is_ok():
            campus = result.data or {}
            return self.campus_formatter.format_campus_details(campus, year)
        else:
            return f"❌ **Lỗi khi lấy chi tiết campus**\n\n" f"{result.error_message}"

    async def get_tuition_list(
        self,
        program_code: Optional[str] = None,
        campus_code: Optional[str] = None,
        department_code: Optional[str] = None,
        year: int = 2025,
        limit: int = 100,
        offset: int = 0,
    ) -> str:
        """
        Lấy danh sách học phí của FPT University với các bộ lọc tùy chọn

        Args:
            program_code: Mã chương trình để lọc (optional)
            campus_code: Mã campus để lọc (optional)
            department_code: Mã khoa để lọc (optional)
            year: Năm để lấy thông tin học phí (2020-2030)
            limit: Số lượng kết quả tối đa (1-100)
            offset: Vị trí bắt đầu lấy dữ liệu

        Returns:
            Danh sách học phí được format đẹp
        """
        result = await self.client.get_tuition_list(
            program_code=program_code,
            campus_code=campus_code,
            department_code=department_code,
            year=year,
            limit=limit,
            offset=offset,
        )

        if result.is_ok():
            data = result.data or {}
            tuition_records = data.get("tuition_records", [])
            meta = data.get("meta", {})

            filters = {}
            if program_code:
                filters["program_code"] = program_code
            if campus_code:
                filters["campus_code"] = campus_code
            if department_code:
                filters["department_code"] = department_code
            if year:
                filters["year"] = str(year)

            return self.tuition_formatter.format_tuition_list(
                tuition_records, meta, filters
            )
        else:
            return f"❌ **Lỗi khi lấy thông tin học phí**\n\n" f"{result.error_message}"

    async def get_tuition_details(self, tuition_id: str) -> str:
        """
        Lấy chi tiết một bản ghi học phí cụ thể theo ID

        Args:
            tuition_id: UUID của bản ghi học phí

        Returns:
            Chi tiết học phí được format đẹp
        """
        result = await self.client.get_tuition_details(tuition_id)

        if result.is_ok():
            tuition = result.data or {}
            return self.tuition_formatter.format_tuition_details(tuition)
        else:
            return f"❌ **Lỗi khi lấy chi tiết học phí**\n\n" f"{result.error_message}"

    async def get_campus_tuition_summary(self, campus_id: str, year: int = 2025) -> str:
        """
        Lấy tổng hợp học phí của một campus cụ thể theo ID

        Args:
            campus_id: UUID của campus
            year: Năm để lấy thông tin học phí (2020-2030)

        Returns:
            Tổng hợp học phí campus được format đẹp
        """
        result = await self.client.get_campus_tuition_summary(campus_id, year)

        if result.is_ok():
            campus_data = result.data or {}
            return self.tuition_formatter.format_campus_tuition_summary(
                campus_data, year
            )
        else:
            return (
                f"❌ **Lỗi khi lấy tổng hợp học phí campus**\n\n"
                f"{result.error_message}"
            )

    async def get_scholarships(
        self,
        year: int = 2025,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> str:
        """
        Lấy danh sách học bổng của FPT University

        Args:
            year: Năm để lọc (2020-2030)
            is_active: Lọc học bổng còn hiệu lực (true/false)
            limit: Số lượng kết quả tối đa (1-100)
            offset: Vị trí bắt đầu

        Returns:
            Danh sách học bổng được format đẹp
        """
        result = await self.client.get_scholarships(
            year=year, is_active=is_active, limit=limit, offset=offset
        )

        if result.is_ok():
            data = result.data or {}
            scholarships = data.get("scholarships", [])
            meta = data.get("meta", {})
            filters = {"year": year}
            if is_active is not None:
                filters["is_active"] = is_active
            return self.scholarship_formatter.format_scholarships_list(
                scholarships, meta, filters
            )
        else:
            return f"❌ **Lỗi khi lấy thông tin học bổng**\n\n{result.error_message}"

    async def get_scholarship_details(self, scholarship_id: str) -> str:
        """
        Lấy chi tiết một học bổng cụ thể theo ID

        Args:
            scholarship_id: UUID của học bổng

        Returns:
            Chi tiết học bổng được format đẹp
        """
        result = await self.client.get_scholarship_details(scholarship_id)

        if result.is_ok():
            scholarship = result.data or {}
            return self.scholarship_formatter.format_scholarship_details(scholarship)
        else:
            return f"❌ **Lỗi khi lấy chi tiết học bổng**\n\n{result.error_message}"

    async def get_admission_methods(
        self, year: int = 2025, limit: int = 100, offset: int = 0
    ) -> str:
        """
        Lấy danh sách các phương thức tuyển sinh của FPT University

        Args:
            year: Năm để lọc (2020-2030)
            limit: Số lượng kết quả tối đa (1-100)
            offset: Vị trí bắt đầu

        Returns:
            Danh sách phương thức tuyển sinh được format đẹp
        """
        result = await self.client.get_admission_methods(
            year=year, limit=limit, offset=offset
        )

        if result.is_ok():
            data = result.data or {}
            methods = data.get("admission_methods", [])
            meta = data.get("meta", {})
            filters = {"year": year}
            return self.admission_method_formatter.format_admission_methods_list(
                methods, meta, filters
            )
        else:
            return (
                f"❌ **Lỗi khi lấy thông tin phương thức tuyển sinh**\n\n"
                f"{result.error_message}"
            )

    async def get_admission_method_details(self, method_id: str) -> str:
        """
        Lấy chi tiết một phương thức tuyển sinh cụ thể theo ID

        Args:
            method_id: UUID của phương thức tuyển sinh

        Returns:
            Chi tiết phương thức tuyển sinh được format đẹp
        """
        result = await self.client.get_admission_method_details(method_id)

        if result.is_ok():
            method = result.data or {}
            return self.admission_method_formatter.format_admission_method_details(
                method
            )
        else:
            return (
                f"❌ **Lỗi khi lấy chi tiết phương thức tuyển sinh**\n\n"
                f"{result.error_message}"
            )

    async def close(self):
        """Close API client session"""
        await self.client.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - auto cleanup"""
        await self.close()


def create_university_api_tool(timeout: int = 30) -> Toolkit:
    """
    Factory function để tạo UniversityApiTool cho public access

    Args:
        timeout: Request timeout in seconds

    Returns:
        Toolkit instance (UniversityApiTool)
    """
    return UniversityApiTool(timeout=timeout)
