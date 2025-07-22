"""
University API Client for Agno Framework
Pure API client logic without formatting concerns
"""

import asyncio
import weakref
from typing import Dict, Any, Optional, Union
import aiohttp
from shared.types import Result, UniversityApiEndpoint, UniversityApiResponse


class UniversityApiClient:
    """
    Pure university API client without formatting logic
    Handles HTTP requests and response parsing
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize UniversityApiClient

        Args:
            timeout: Request timeout in seconds
        """
        self.base_url = UniversityApiEndpoint.BASE_URL.value
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

        # Register cleanup on object deletion
        self._finalizer = weakref.finalize(self, self._cleanup_session, self._session)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "University-Agent/1.0"
            }

            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout,
                connector=connector
            )

            # Update finalizer with new session
            self._finalizer.detach()
            self._finalizer = weakref.finalize(self, self._cleanup_session, self._session)

        return self._session

    @staticmethod
    def _cleanup_session(session: Optional[aiohttp.ClientSession]):
        """Static method to cleanup session - called by finalizer"""
        if session and not session.closed:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            loop.create_task(session.close())

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> UniversityApiResponse:
        """
        Make HTTP request to API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data

        Returns:
            UniversityApiResponse object
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}{endpoint}"

            async with session.request(
                method=method,
                url=url,
                params=params,
                json=data if data else None
            ) as response:

                status_code = response.status

                try:
                    response_data = await response.json()
                except:
                    response_data = {"message": await response.text()}

                if 200 <= status_code < 300:
                    # Ensure data and meta are dictionaries or None
                    response_data_dict = None
                    meta_dict = None

                    if isinstance(response_data, dict):
                        raw_data = response_data.get("data")
                        raw_meta = response_data.get("meta")

                        response_data_dict = raw_data if isinstance(raw_data, dict) else None
                        meta_dict = raw_meta if isinstance(raw_meta, dict) else None

                    return UniversityApiResponse(
                        success=True,
                        data=response_data_dict,
                        meta=meta_dict,
                        status_code=status_code
                    )
                else:
                    error_msg = response_data.get("message", f"HTTP {status_code}") if isinstance(response_data, dict) else f"HTTP {status_code}"
                    return UniversityApiResponse(
                        success=False,
                        error_message=error_msg,
                        status_code=status_code
                    )

        except asyncio.TimeoutError:
            return UniversityApiResponse(
                success=False,
                error_message="Request timeout - API không phản hồi trong thời gian cho phép",
                status_code=408
            )
        except aiohttp.ClientError as e:
            return UniversityApiResponse(
                success=False,
                error_message=f"Connection error: {str(e)}",
                status_code=500
            )
        except Exception as e:
            return UniversityApiResponse(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                status_code=500
            )

    async def get_departments(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Result[Dict[str, Any]]:
        """Get departments list"""
        params: Dict[str, Union[int, str]] = {
            "limit": min(max(limit, 1), 100),
            "offset": max(offset, 0)
        }

        response = await self._make_request("GET", UniversityApiEndpoint.DEPARTMENTS.value, params=params)
        
        if response.success:
            return Result.ok({
                "departments": response.data or [],
                "meta": response.meta or {}
            })
        else:
            return Result.error(response.error_message or "Unknown error")

    async def get_programs(
        self,
        department_code: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Result[Dict[str, Any]]:
        """Get programs list"""
        params: Dict[str, Union[int, str]] = {
            "limit": min(max(limit, 1), 100),
            "offset": max(offset, 0)
        }

        if department_code:
            params["department_code"] = department_code

        response = await self._make_request("GET", UniversityApiEndpoint.PROGRAMS.value, params=params)
        
        if response.success:
            return Result.ok({
                "programs": response.data or [],
                "meta": response.meta or {}
            })
        else:
            return Result.error(response.error_message or "Unknown error")

    async def get_program_details(self, program_id: str) -> Result[Dict[str, Any]]:
        """Get specific program details"""
        response = await self._make_request("GET", f"{UniversityApiEndpoint.PROGRAMS.value}/{program_id}")
        
        if response.success:
            return Result.ok(response.data or {})
        else:
            return Result.error(response.error_message or "Unknown error")

    async def get_campuses(
        self,
        year: int = 2025,
        limit: int = 100,
        offset: int = 0
    ) -> Result[Dict[str, Any]]:
        """Get campuses list"""
        params: Dict[str, Union[int, str]] = {
            "year": max(min(year, 2030), 2020),
            "limit": min(max(limit, 1), 100),
            "offset": max(offset, 0)
        }

        response = await self._make_request("GET", UniversityApiEndpoint.CAMPUSES.value, params=params)
        
        if response.success:
            return Result.ok({
                "campuses": response.data or [],
                "meta": response.meta or {}
            })
        else:
            return Result.error(response.error_message or "Unknown error")

    async def get_campus_details(self, campus_id: str, year: int = 2025) -> Result[Dict[str, Any]]:
        """Get specific campus details"""
        params: Dict[str, Union[int, str]] = {
            "year": max(min(year, 2030), 2020)
        }

        response = await self._make_request("GET", f"{UniversityApiEndpoint.CAMPUSES.value}/{campus_id}", params=params)
        
        if response.success:
            return Result.ok(response.data or {})
        else:
            return Result.error(response.error_message or "Unknown error")

    async def close(self):
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

        # Detach finalizer since we manually closed
        if hasattr(self, '_finalizer'):
            self._finalizer.detach()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - auto cleanup"""
        await self.close() 