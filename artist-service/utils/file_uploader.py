# artist-service/utils/file_uploader.py
import os
from pathlib import Path
from fastapi import UploadFile, HTTPException
from config import settings
from typing import Union, Any
import aiofiles


class FileUploader:
    """Helper para manejar subida de archivos (local o S3)"""

    @staticmethod
    async def upload_profile_picture(
        file: UploadFile,
        artist_id: Union[int, Any],
    ) -> str:
        # Validaciones básicas
        if file.content_type not in settings.allowed_image_types:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no permitido: {file.content_type}",
            )

        # Tamaño máximo
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        if file_size > settings.max_file_size:
            raise HTTPException(
                status_code=400, detail="Archivo demasiado grande (máx. 5MB)"
            )

        # Nombre del archivo
        artist_id_str = str(artist_id)
        _, ext = os.path.splitext(file.filename or "file.jpg")
        if not ext:
            ext = ".jpg"
        filename = f"profile_picture{ext}"

        # === Si usamos S3 ===
        if settings.use_s3:
            s3_client = settings.get_s3_client()
            if not s3_client or not settings.aws_s3_bucket:
                raise HTTPException(status_code=500, detail="Configuración S3 inválida")

            key = f"{artist_id_str}/utils/{filename}"

            try:
                file_bytes = await file.read()
                s3_client.put_object(
                    Bucket=settings.aws_s3_bucket,
                    Key=key,
                    Body=file_bytes,
                    ContentType=file.content_type,
                )
                print(f"✅ Imagen subida a S3: s3://{settings.aws_s3_bucket}/{key}")
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Error subiendo a S3: {str(e)}"
                )

            # Retorna la ruta lógica (no pública)
            return f"s3://{settings.aws_s3_bucket}/{key}"

        # === Si usamos almacenamiento local ===
        storage_path = settings.storage_path
        storage_path.mkdir(parents=True, exist_ok=True)

        artist_utils_folder = storage_path / artist_id_str / "utils"
        artist_utils_folder.mkdir(parents=True, exist_ok=True)

        file_location = artist_utils_folder / filename

        try:
            async with aiofiles.open(file_location, "wb") as buffer:
                await buffer.write(await file.read())

            print(f"✅ Imagen guardada localmente en: {file_location}")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error al guardar localmente: {str(e)}"
            )

        return f"/{artist_id_str}/utils/{filename}"
