"""
API settings for FPT University Agent
"""

from typing import List

from pydantic import Field, field_validator
from pydantic_core.core_schema import FieldValidationInfo
from pydantic_settings import BaseSettings


class ApiSettings(BaseSettings):
    """API settings that are set using environment variables."""

    title: str = "FPT University Agent API"
    version: str = "1.0.0"
    description: str = "API for FPT University Agent with Intent Detection and Agno Integration"

    # Set to False to disable docs at /docs and /redoc
    docs_enabled: bool = True

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # CORS origin list to allow requests from
    cors_origin_list: List[str] = Field(default_factory=list, validate_default=True)

    # Intent detection settings
    intent_detection_timeout: float = 10.0
    max_query_length: int = 1000

    # Agent settings
    default_model: str = "gpt-4o"

    @field_validator("cors_origin_list", mode="before")
    @classmethod
    def set_cors_origin_list(cls, cors_origin_list, info: FieldValidationInfo):
        # Handle comma-separated string from environment variable
        if isinstance(cors_origin_list, str):
            valid_cors = [origin.strip() for origin in cors_origin_list.split(",") if origin.strip()]
        else:
            valid_cors = cors_origin_list or []

        # Add localhost to cors to allow requests from the local environment
        valid_cors.extend([
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:8080",
            "http://127.0.0.1",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:8080",
            "https://app.agno.com",
            "https://playground.agno.com"
        ])

        return valid_cors

    model_config = {
        "env_file": ".env",
        "env_prefix": "FPT_AGENT_",
        "extra": "ignore"
    }


# Create ApiSettings object
api_settings = ApiSettings()
