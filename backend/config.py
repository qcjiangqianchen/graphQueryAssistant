"""
Configuration management for the application
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"  # Default to cost-effective model
    openai_temperature: float = 0.7
    openai_max_tokens: int = 1000

    # Neo4j Graph Database Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # Application Configuration
    app_name: str = "BNP AI Chatbot"
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


# Initialize settings
settings = Settings()
