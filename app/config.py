"""
Configuration module for Contract Intelligence Parser
Loads and manages all application settings from environment variables
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # MongoDB Configuration
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "contract_intelligence"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # File Upload Configuration
    upload_dir: str = "./uploads"
    max_file_size: int = 52428800  # 50MB in bytes
    
    # LLM Configuration (OpenRouter only)
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-3.5-sonnet"
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Application Settings
    log_level: str = "INFO"
    environment: str = "development"
    
    # API Metadata
    app_name: str = "Contract Intelligence API"
    app_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False
        extra = "ignore"
        validate_default = False
        env_ignore_empty = True

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Returns singleton settings object
    """
    return Settings()


# Global settings instance
settings = get_settings()