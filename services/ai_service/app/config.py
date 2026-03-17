from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """AI service configuration loaded from environment variables."""

    host: str = "0.0.0.0"
    port: int = 8003
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "course_finder"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # Circuit breaker
    circuit_breaker_failure_threshold: int = 3
    circuit_breaker_recovery_timeout: float = 30.0


settings = Settings()
