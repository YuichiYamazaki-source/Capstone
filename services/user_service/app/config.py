from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """User service configuration loaded from environment variables."""

    host: str = "0.0.0.0"
    port: int = 8002
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "course_finder"
    jwt_secret_key: str = "changeme-use-a-long-random-string-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24


settings = Settings()
