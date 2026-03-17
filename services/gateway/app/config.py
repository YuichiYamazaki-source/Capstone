from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Gateway service configuration loaded from environment variables."""

    host: str = "0.0.0.0"
    port: int = 8000
    course_service_url: str = "http://localhost:8001"
    user_service_url: str = "http://localhost:8002"
    ai_service_url: str = "http://localhost:8003"
    jwt_secret_key: str = "changeme-use-a-long-random-string-in-production"
    jwt_algorithm: str = "HS256"
    frontend_origin: str = "http://localhost:5173"


settings = Settings()
