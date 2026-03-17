from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Course service configuration loaded from environment variables."""

    host: str = "0.0.0.0"
    port: int = 8001
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "course_finder"


settings = Settings()
