"""
Application configuration using Pydantic Settings.

Manages environment variables and application constants with type safety.
Loads configuration from .env files in development and environment variables in production.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    """
    Application settings and environment variables.
    
    Uses pydantic-settings for automatic validation and type conversion.
    Configuration can be overridden via environment variables or .env file.
    """
    
    # ============================================================================
    # API Configuration
    # ============================================================================
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "TenzorX Healthcare Navigator"
    PROJECT_DESCRIPTION: str = (
        "AI-Powered Healthcare Navigator and Cost Estimator - "
        "Kayak for Healthcare in India"
    )
    VERSION: str = "1.0.0"
    
    # ============================================================================
    # Neo4j Database Configuration
    # ============================================================================
    NEO4J_URI: str = "bolt://localhost:7687"
    """
    Neo4j database connection URI.
    Format: bolt://hostname:port
    Default: local Neo4j instance on port 7687
    """
    
    NEO4J_USER: str = "neo4j"
    """Neo4j database username for authentication."""
    
    NEO4J_PASSWORD: str = "password"
    """Neo4j database password for authentication."""
    
    NEO4J_DATABASE: str = "neo4j"
    """Neo4j database name to connect to."""
    
    # ============================================================================
    # CORS Configuration
    # ============================================================================
    BACKEND_CORS_ORIGINS: list[str] = [
    "https://tenzor-x.vercel.app", 
    "http://localhost:8000", 
    "http://localhost:3000"
]
    """
    List of allowed CORS origins for frontend communication.
    Production: https://tenzor-x.vercel.app/
    Development: http://localhost:3000, http://localhost:8000
    """
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v
    
    # ============================================================================
    # Security Configuration
    # ============================================================================
    SECRET_KEY: str = "your-secret-key-change-in-production"
    """
    Secret key for JWT token signing.
    MUST be changed in production via environment variable.
    """
    
    ALGORITHM: str = "HS256"
    """JWT token signing algorithm."""
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    """Access token expiration time in minutes."""
    
    # ============================================================================
    # Logging Configuration
    # ============================================================================
    LOG_LEVEL: str = "INFO"
    """Application logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
    
    # ============================================================================
    # Feature Flags
    # ============================================================================
    DEBUG: bool = False
    """Enable debug mode (FastAPI debug, verbose logging)."""
    
    ENABLE_SWAGGER_UI: bool = True
    """Enable Swagger UI documentation endpoint."""
    
    ENABLE_REDOC: bool = True
    """Enable ReDoc documentation endpoint."""
    
    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env


# Create a singleton instance of settings
settings = Settings()
