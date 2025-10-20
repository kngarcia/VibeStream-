# artist-service/config.py
from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List
import json

class Settings(BaseSettings):
    db_url: str = Field(alias="db_url_py")
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(alias="JWT_ALGORITHM", default="HS256")
    port: int = Field(alias="PORT", default=8003)
    rabbitmq_url: str = Field(alias="RABBITMQ_URL")
    
    # CORS configuration
    frontend_origins_raw: str = Field(alias="FRONTEND_ORIGINS", default="http://localhost:5173")

    # ✅ AÑADIR CONFIGURACIÓN DE ALMACENAMIENTO (igual que content-service)
    content_base_path: str = Field(default="storage")
    max_file_size: int = Field(default=5 * 1024 * 1024)  # 5MB
    allowed_image_types: list = Field(default=["image/jpeg", "image/png", "image/jpg", "image/gif"])

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

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

    # ✅ AÑADIR PROPIEDAD storage_path (igual que content-service)
    @property
    def storage_path(self) -> Path:
        return Path(self.content_base_path)

settings = Settings()  # type: ignore

# Al final de config.py, agrega:
print(f"🔧 Config loaded:")
print(f"   JWT Secret: {settings.jwt_secret}")
print(f"   JWT Algorithm: {settings.jwt_algorithm}")
print(f"   Port: {settings.port}")
print(f"   Storage Path: {settings.storage_path}")  # ✅ Añadir esto