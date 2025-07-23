"""
API settings for FPT University Agent
"""

from typing import List, Union

from pydantic import Field, field_validator
from pydantic_core.core_schema import FieldValidationInfo
from pydantic_settings import BaseSettings


class ApiSettings(BaseSettings):
    """API settings that are set using environment variables."""

    title: str = "FPT University Agent API"
    version: str = "1.0.0"
    description: str = (
        "API for FPT University Agent with Intent Detection and Agno Integration"
    )

    # Set to False to disable docs at /docs and /redoc
    docs_enabled: bool = True

    # Server settings
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    reload: bool = False

    # CORS origins (comma-separated string)
    cors_origin_list: str = Field(default="", description="Comma-separated list of allowed origins")

    # Intent detection settings
    intent_detection_timeout: float = Field(default=10.0, ge=0.1, le=300.0)
    max_query_length: int = Field(default=1000, ge=1, le=10000)

    # Agent settings
    default_model: str = "gpt-4o"

    @field_validator("cors_origin_list", mode="before")
    @classmethod
    def validate_cors_origins(cls, value):
        """Validate CORS origins string"""
        if not isinstance(value, str):
            return ""
        return value.strip()

    @field_validator("port", mode="before")
    @classmethod
    def validate_port(cls, port_value):
        """Validate and handle empty port value"""
        if isinstance(port_value, str) and not port_value.strip():
            return 8000
        return port_value

    @field_validator("intent_detection_timeout", mode="before")
    @classmethod
    def validate_timeout(cls, timeout_value):
        """Validate and handle empty timeout value"""
        if isinstance(timeout_value, str) and not timeout_value.strip():
            return 10.0
        return timeout_value

    @field_validator("max_query_length", mode="before")
    @classmethod
    def validate_max_query_length(cls, length_value):
        """Validate and handle empty max query length value"""
        if isinstance(length_value, str) and not length_value.strip():
            return 1000
        return length_value

    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins as a list of strings."""
        # Parse comma-separated string
        origins = [
            origin.strip() 
            for origin in self.cors_origin_list.split(",") 
            if origin.strip()
        ]
        
        # Handle wildcard
        if "*" in origins:
            return ["*"]
        
        # Add default origins for development
        default_origins = [
            "http://localhost:3000",
            "http://localhost:8000", 
            "https://app.agno.com",
            "https://playground.agno.com",
            "https://swd-chatbot.vercel.app"
        ]
        
        # Merge and remove duplicates
        all_origins = list(set(origins + default_origins))
        return all_origins

    model_config = {
        "env_file": ".env",
        "env_prefix": "FPT_AGENT_",
        "extra": "ignore",
    }


# Create ApiSettings object
api_settings = ApiSettings()
