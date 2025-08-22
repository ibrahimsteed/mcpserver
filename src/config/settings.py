# src/config/settings.py
from pydantic_settings import BaseSettings
from pydantic import Field, HttpUrl
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Server Configuration
    server_name: str = Field(default="dify-external-api-server")
    server_version: str = Field(default="1.0.0")
    server_port: int = Field(default=6018)
    log_level: str = Field(default="INFO")
    
    # External API Configuration
    external_api_base_url: Optional[HttpUrl] = Field(default=None)
    external_api_key: Optional[str] = Field(default=None)
    external_api_timeout: int = Field(default=30)
    external_api_rate_limit: int = Field(default=100)
    
    # Optional Database
    database_url: Optional[str] = Field(default=None)
    
    # Optional Email
    smtp_host: Optional[str] = Field(default=None)
    smtp_port: Optional[int] = Field(default=587)
    smtp_user: Optional[str] = Field(default=None)
    smtp_password: Optional[str] = Field(default=None)
    
    # Security
    jwt_secret: str = Field(default="default-secret")
    cors_origins: List[str] = Field(default=["*"])
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()