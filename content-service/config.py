# config.py
from pydantic_settings import BaseSettings
from pathlib import Path
from pydantic import Field
from typing import List
import json


class Settings(BaseSettings):
    # Database
    db_url: str = Field(alias="db_url_py")

    # JWT Configuration
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(alias="JWT_ALGORITHM", default="HS256")

    # Service Configuration
    port: int = Field(alias="PORT", default=8001)

    # Storage Configuration
    content_base_path: str = Field(alias="CONTENT_BASE_PATH", default="storage")
    use_s3: bool = Field(alias="USE_S3", default=False)
    aws_s3_bucket: str | None = Field(alias="AWS_S3_BUCKET", default=None)
    aws_region: str | None = Field(alias="AWS_REGION", default=None)
    aws_access_key_id: str | None = Field(alias="AWS_ACCESS_KEY_ID", default=None)
    aws_secret_access_key: str | None = Field(
        alias="AWS_SECRET_ACCESS_KEY", default=None
    )

    # RabbitMQ
    rabbitmq_url: str = Field(
        alias="RABBITMQ_URL", default="amqp://guest:guest@localhost:5672/"
    )

    # CORS
    frontend_origins_raw: str = Field(
        alias="FRONTEND_ORIGINS", default="http://localhost:5173"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def frontend_origins(self) -> List[str]:
        """Devuelve la lista de orígenes para CORS."""
        raw = self.frontend_origins_raw
        if not raw:
            return []
        s = raw.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if x]
            except Exception:
                pass
        return [p.strip() for p in s.split(",") if p.strip()]

    @property
    def storage_path(self) -> Path:
        """Ruta base de almacenamiento (solo usada si no hay S3)."""
        return Path(self.content_base_path)


settings = Settings()

# Log de configuración cargada
print(f"🔧 Content Service Config loaded:")
print(f"   Database URL: {settings.db_url[:30]}...")
print(f"   JWT Algorithm: {settings.jwt_algorithm}")
print(f"   Port: {settings.port}")
print(f"   Storage Path: {settings.storage_path}")
print(f"   S3 Enabled: {settings.use_s3}")
print(f"   RabbitMQ URL: {settings.rabbitmq_url}")
print(f"   Frontend Origins: {settings.frontend_origins}")
