"""
University API Tool for Agno Framework
Main tool class that orchestrates between API client and formatters
"""

from typing import Dict, Any, Optional, Union
from agno.tools.toolkit import Toolkit

from infrastructure.api.university_client import UniversityApiClient
from shared.utils.university_formatters import DepartmentFormatter, ProgramFormatter, CampusFormatter


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

        # Register all methods as tools
        super().__init__(
            name="university_api",
            tools=[
                self.get_departments,
                self.get_programs,
                self.get_program_details,
                self.get_campuses,
                self.get_campus_details
            ]
        )

    async def get_departments(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> str:
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
            return f"❌ **Lỗi khi lấy thông tin khoa/phòng ban**\n\n{result.error_message}"

    async def get_programs(
        self,
        department_code: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
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
            department_code=department_code,
            limit=limit,
            offset=offset
        )
        
        if result.is_ok():
            data = result.data or {}
            programs = data.get("programs", [])
            meta = data.get("meta", {})
            
            return self.program_formatter.format_programs_list(
                programs, meta, department_code
            )
        else:
            return f"❌ **Lỗi khi lấy thông tin chương trình học**\n\n{result.error_message}"

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
            return f"❌ **Lỗi khi lấy chi tiết chương trình học**\n\n{result.error_message}"

    async def get_campuses(
        self,
        year: int = 2025,
        limit: int = 100,
        offset: int = 0
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
            return f"❌ **Lỗi khi lấy thông tin campus**\n\n{result.error_message}"

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
            return f"❌ **Lỗi khi lấy chi tiết campus**\n\n{result.error_message}"

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