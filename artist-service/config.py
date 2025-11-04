# artist-service/config.py
from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List, Optional
import boto3
import json


class Settings(BaseSettings):
    db_url: str = Field(alias="db_url_py")
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(alias="JWT_ALGORITHM", default="HS256")
    port: int = Field(alias="PORT", default=8003)
    rabbitmq_url: str = Field(alias="RABBITMQ_URL")

    # CORS
    frontend_origins_raw: str = Field(
        alias="FRONTEND_ORIGINS", default="http://localhost:5173"
    )

    # === STORAGE CONFIG ===
    content_base_path: str = Field(default="storage")
    max_file_size: int = Field(default=5 * 1024 * 1024)
    allowed_image_types: list = Field(
        default=["image/jpeg", "image/png", "image/jpg", "image/gif"]
    )

    # === AWS CONFIG (opcional) ===
    use_s3: bool = Field(default=False, alias="USE_S3")
    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(
        default=None, alias="AWS_SECRET_ACCESS_KEY"
    )
    aws_region: Optional[str] = Field(default=None, alias="AWS_REGION")
    aws_s3_bucket: Optional[str] = Field(default=None, alias="AWS_S3_BUCKET")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def frontend_origins(self) -> List[str]:
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
        return Path(self.content_base_path)

    def get_s3_client(self):
        """Devuelve un cliente boto3 configurado si USE_S3=True"""
        if not self.use_s3:
            return None
        return boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region,
        )


settings = Settings()  # type: ignore

print(f"🔧 Config loaded:")
print(f"   JWT Secret: {settings.jwt_secret}")
print(f"   Storage Path: {settings.storage_path}")
print(f"   USE_S3: {settings.use_s3}")
if settings.use_s3:
    print(f"   AWS Bucket: {settings.aws_s3_bucket}")
