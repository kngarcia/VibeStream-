from pydantic_settings import (
    BaseSettings,
)  # o from pydantic import BaseSettings si usas v1
from pydantic import Field


class Settings(BaseSettings):
    db_url: str = Field(alias="db_url_py")
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    port: int = 8006

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore
