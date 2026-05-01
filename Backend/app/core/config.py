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
    # NVIDIA API Configuration
    # ============================================================================
    NVIDIA_API_KEY: str = ""
    """
    NVIDIA API key for Mistral Large 3 LLM integration.
    Required for AI-powered medical guidance.
    Get from: https://integrate.api.nvidia.com/
    """
    
    OPENAI_API_KEY: str = ""
    """
    OpenAI API key for embeddings in vector fallback.
    Optional, used for FAISS vector database fallback.
    """
    
    # ============================================================================
    # Geo-Spatial Configuration
    # ============================================================================
    GOOGLE_MAPS_API_KEY: str = ""
    """Google Maps API key for geocoding and map services."""
    
    NOMINATIM_USER_AGENT: str = "healthnav-india"
    """User agent for Nominatim geocoding service (OpenStreetMap)."""
    
    # ============================================================================
    # Neo4j Database Configuration
    # ============================================================================
    NEO4J_URI: str = ""
    """
    Neo4j database connection URI.
    Format: bolt://hostname:port or neo4j://hostname:port
    Loaded from environment variable NEO4J_URI
    """
    
    NEO4J_USER: str = ""
    """Neo4j database username for authentication. Loaded from NEO4J_USER env var."""
    
    NEO4J_PASSWORD: str = ""
    """Neo4j database password for authentication. Loaded from NEO4J_PASSWORD env var."""
    
    NEO4J_DATABASE: str = "neo4j"
    """Neo4j database name to connect to. Loaded from NEO4J_DATABASE env var."""
    
    # ============================================================================
    # CORS Configuration
    # ============================================================================
    BACKEND_CORS_ORIGINS: list[str] = [
        "https://tenzor-x.vercel.app",
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1",
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
    # Session & Memory Configuration
    # ============================================================================
    REDIS_URL: str = ""
    """Redis connection URL for session storage. Format: redis://hostname:port."""
    
    OFFLINE_FALLBACK_ENABLED: bool = True
    """Enable offline fallback mode when LLM services are unavailable."""
    
    CONFIDENCE_THRESHOLD_WARN: int = 60
    """Confidence score threshold for showing warning banner."""
    
    CONFIDENCE_THRESHOLD_BLOCK: int = 40
    """Confidence score threshold for blocking results."""
    
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
