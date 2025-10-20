# config.py content
from pydantic_settings import BaseSettings
from pathlib import Path
from pydantic import Field
from typing import List, Optional
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

    # RabbitMQ
    rabbitmq_url: str = Field(alias="RABBITMQ_URL", default="amqp://guest:guest@localhost:5672/")

    # CORS - usar el mismo formato que artist-service
    frontend_origins_raw: str = Field(alias="FRONTEND_ORIGINS", default="http://localhost:5173")

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
        # si parece JSON array, parsear
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if x]
            except Exception:
                pass
        # coma-separado por defecto
        return [p.strip() for p in s.split(",") if p.strip()]

    @property
    def storage_path(self) -> Path:
        return Path(self.content_base_path)

# crear la instancia global
settings = Settings()

# Log de configuración cargada
print(f"🔧 Content Service Config loaded:")
print(f"   Database URL: {settings.db_url[:30]}...")  # Mostrar solo parte por seguridad
print(f"   JWT Algorithm: {settings.jwt_algorithm}")
print(f"   Port: {settings.port}")
print(f"   Storage Path: {settings.storage_path}")
print(f"   RabbitMQ URL: {settings.rabbitmq_url}")
print(f"   Frontend Origins: {settings.frontend_origins}")