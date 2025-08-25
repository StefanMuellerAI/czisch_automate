from pydantic_settings import BaseSettings
from typing import Optional
import logging


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # API Configuration
    app_name: str = "N8N ETL API"
    app_description: str = "Eine dockerisierte OpenAPI für n8n-kompatible ETL-Operationen mit Playwright-Unterstützung"
    app_version: str = "1.0.0"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Playwright Configuration
    playwright_headless: bool = True
    playwright_timeout: int = 30000  # milliseconds
    
    # Logging Configuration
    log_level: str = "INFO"
    
    # API Configuration
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    
    # CORS Configuration
    cors_origins: list = ["*"]
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)
