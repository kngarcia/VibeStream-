import os
from pathlib import Path
from fastapi import UploadFile, HTTPException
from config import settings
from typing import Union, Any


class FileUploader:
    """Helper para manejar la subida de archivos usando configuración centralizada"""

    @staticmethod
    async def upload_profile_picture(
        file: UploadFile,
        artist_id: Union[int, Any],  # 🔹 Acepta tanto int como objetos SQLAlchemy
    ) -> str:
        """
        Sube la foto de perfil del artista a {CONTENT_BASE_PATH}/{artist_id}/utils/
        """
        # ✅ VERIFICAR QUE LA CONFIGURACIÓN EXISTA
        if not hasattr(settings, 'storage_path'):
            raise HTTPException(
                status_code=500,
                detail="Configuración de almacenamiento no encontrada. Verifica CONTENT_BASE_PATH en .env"
            )

        # Usar path centralizado desde config
        storage_path = settings.storage_path

        # ✅ CREAR DIRECTORIO BASE SI NO EXISTE
        storage_path.mkdir(parents=True, exist_ok=True)

        # 🔹 Convertir artist_id a string (funciona con int y Column)
        artist_id_str = str(artist_id)

        # Carpeta utils del artista
        artist_utils_folder = storage_path / artist_id_str / "utils"
        artist_utils_folder.mkdir(parents=True, exist_ok=True)

        # ✅ VALIDAR TIPO DE ARCHIVO
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/gif"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no permitido. Tipos permitidos: {', '.join(allowed_types)}"
            )

        # ✅ VALIDAR TAMAÑO (5MB máximo)
        max_size = 5 * 1024 * 1024  # 5MB
        file.file.seek(0, 2)  # Ir al final del archivo
        file_size = file.file.tell()
        file.file.seek(0)  # Volver al inicio
        
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail="Archivo demasiado grande. Tamaño máximo: 5MB"
            )

        # Asegurar que filename nunca sea None
        original_filename = file.filename or "file.jpg"

        # Obtener la extensión original
        _, ext = os.path.splitext(original_filename)
        if not ext:
            ext = ".jpg"  # fallback si no tiene extensión

        # Nombre fijo del archivo
        filename = f"profile_picture{ext}"
        file_location = artist_utils_folder / filename

        try:
            # Guardar (sobre-escribe si ya existía)
            with open(file_location, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
                
            print(f"✅ Imagen guardada en: {file_location}")
            print(f"✅ Ruta relativa: /{artist_id_str}/utils/{filename}")
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al guardar el archivo: {str(e)}"
            )

        # Retornar la URL relativa usando el path base de config
        return f"/{artist_id_str}/utils/{filename}"