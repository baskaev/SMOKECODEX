import os
from pydantic import BaseModel


class Settings(BaseModel):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    frontend_url: str = "http://localhost:3000"


settings = Settings(
    database_url=os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://smokecodex:smokecodex@db:5432/smokecodex",
    ),
    jwt_secret=os.getenv("JWT_SECRET", "change-me"),
    jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
    access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE", "1440")),
    app_host=os.getenv("APP_HOST", "0.0.0.0"),
    app_port=int(os.getenv("APP_PORT", "8000")),
    frontend_url=os.getenv("FRONTEND_URL", "http://localhost:3000"),
)
