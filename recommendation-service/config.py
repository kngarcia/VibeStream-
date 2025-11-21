from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    db_url: str = Field(alias="db_url_py")
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    port: int = 8009
    frontend_origins_raw: str = Field(alias="FRONTEND_ORIGINS", default="http://localhost:5173")

    class Config:
        env_file = ".env"

    @property
    def frontend_origins(self) -> List[str]:
        origins = []
        for origin in self.frontend_origins_raw.split(","):
            origin = origin.strip()
            if origin and not origin.startswith(('http://', 'https://')):
                origin = f"http://{origin}"
            if origin:
                origins.append(origin)
        return origins


settings = Settings()  # type: ignore
