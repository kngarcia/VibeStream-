# config.py - VERIFICAR QUE LAS URLS ESTÉN CORRECTAS
from pydantic_settings import BaseSettings
from pydantic import Field
import json
from typing import List

class Settings(BaseSettings):
    db_url: str = Field(alias="db_url_py")
    jwt_secret: str = Field(alias="JWT_SECRET", default="HolaMundoo")
    jwt_algorithm: str = Field(alias="JWT_ALGORITHM", default="HS256")
    port: int = Field(alias="PLAYLIST_PORT", default=8004)
    frontend_origins_raw: str = Field(alias="FRONTEND_ORIGINS", default="http://localhost:3000,http://localhost:5173")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def frontend_origins(self) -> List[str]:
        """Devuelve la lista de orígenes para CORS."""
        raw = self.frontend_origins_raw
        if not raw:
            return ["http://localhost:3000"]  # fallback
            
        s = raw.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if x]
            except Exception:
                pass
        
        # ✅ ASEGURAR PROTOCOLO HTTP/HTTPS
        origins = []
        for origin in s.split(","):
            origin = origin.strip()
            if origin:
                if not origin.startswith(('http://', 'https://')):
                    origin = f"http://{origin}"
                origins.append(origin)
        
        return origins

settings = Settings()

print(f"🔧 Config loaded:"
      f"\n   JWT Secret: {settings.jwt_secret}"
      f"\n   JWT Algorithm: {settings.jwt_algorithm}"
      f"\n   Port: {settings.port}"
      f"\n   Frontend Origins: {settings.frontend_origins}"
)