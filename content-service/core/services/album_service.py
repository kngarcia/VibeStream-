from datetime import date
from pathlib import Path
from infrastructure.db.models import Album, Song
from core.repositories.album_repository import AlbumRepository
from events.producer import publish_album_created_event, publish_album_updated_event
from core.services.artist_lookup import ArtistLookupService
import os
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
from infrastructure.storage.s3_client import upload_bytes_to_s3


class AlbumService:
    def __init__(self, repo: AlbumRepository):
        self.repo = repo

    def _save_cover_image(
        self,
        artist_id: int,
        album_id: int,
        image_data: bytes,
        filename: str | None = None,
    ) -> str:
        ext = ".png"
        if filename:
            _, ext_candidate = os.path.splitext(filename)
            if ext_candidate.lower() in [".png", ".jpg", ".jpeg"]:
                ext = ext_candidate.lower()

        filename = f"cover{ext}"

        # 🔹 Si se usa S3
        if settings.use_s3 and settings.aws_s3_bucket:
            key = f"{artist_id}/{album_id}/{filename}"
            content_type = "image/png" if ext == ".png" else "image/jpeg"
            upload_bytes_to_s3(settings.aws_s3_bucket, key, image_data, content_type)
            cover_url = f"{settings.content_base_path}/{key}"
            print(f"[✓] Imagen subida a S3: {cover_url}")
            return cover_url

        # 🔹 Fallback local
        storage_path = settings.storage_path
        album_folder = storage_path / str(artist_id) / str(album_id)
        album_folder.mkdir(parents=True, exist_ok=True)
        file_path = album_folder / filename

        with open(file_path, "wb") as f:
            f.write(image_data)

        cover_url = f"{settings.content_base_path}/{artist_id}/{album_id}/{filename}"
        print(f"[✓] Imagen guardada localmente: {file_path}")
        return cover_url

    async def create_album(
        self,
        title: str,
        user_id: int,
        db: AsyncSession,  # ⬅️ ACEPTA LA SESIÓN
        release_date: date | None = None,
        cover_image: bytes | None = None,
        cover_filename: str | None = None,
    ) -> Album:
        # 🔹 Ahora, se pasa la sesión a ArtistLookupService
        artist_id = await ArtistLookupService.get_artist_id_by_user(user_id, db=db)
        if not artist_id:
            raise ValueError(f"No existe artista para el user_id {user_id}")

        # Fecha por defecto
        release_date = release_date or date.today()

        # 1. Crear el álbum sin portada
        album = Album(
            title=title,
            artist_id=artist_id,
            release_date=release_date,
        )
        album = await self.repo.create(album)

        # 2. Guardar la portada (si se envía), ahora que ya existe album.id
        if cover_image:
            cover_url = self._save_cover_image(
                artist_id, album.id, cover_image, cover_filename
            )
            album.cover_url = cover_url
            album = await self.repo.update(album)

        # 3. Publicar evento
        await publish_album_created_event(
            {
                "id": album.id,
                "title": album.title,
                "artist_id": album.artist_id,
                "release_date": album.release_date.isoformat()
                if album.release_date
                else None,
                "cover_url": album.cover_url,
            }
        )

        return album

    async def get_album(self, album_id: int) -> Album | None:
        return await self.repo.get_by_id(album_id)

    async def list_albums_by_user(self, user_id: int, db: AsyncSession) -> list[Album]:
        artist_id = await ArtistLookupService.get_artist_id_by_user(user_id, db=db)
        if not artist_id:
            return []
        return list(await self.repo.list_by_artist(artist_id))

    async def update_album(
        self,
        album: Album,
        title: str | None = None,
        release_date: date | None = None,
        cover_image: bytes | None = None,
        cover_filename: str | None = None,
    ) -> Album:
        if title:
            album.title = title
        if release_date:
            album.release_date = release_date

        if cover_image:
            cover_url = self._save_cover_image(
                album.artist_id, album.id, cover_image, cover_filename
            )
            album.cover_url = cover_url

        album = await self.repo.update(album)

        await publish_album_updated_event(
            {
                "id": album.id,
                "title": album.title,
                "artist_id": album.artist_id,
                "release_date": album.release_date.isoformat()
                if album.release_date
                else None,
                "cover_url": album.cover_url,
            }
        )

        return album

    async def delete_album(self, album: Album) -> None:
        await self.repo.delete(album)

    async def list_songs_by_album(self, album_id: int) -> list[Song]:
        return list(await self.repo.list_songs_by_album(album_id))

    async def get_artist_albums_with_info(self, artist_id: int) -> list[dict]:
        """Obtiene todos los álbumes de un artista con información completa"""
        albums = await self.repo.get_albums_with_artist_info(artist_id)

        # Agregar información adicional
        for album in albums:
            # Contar canciones del álbum
            songs = await self.repo.list_songs_by_album(album["id"])
            album["total_songs"] = len(songs)

            # Formatear fechas si es necesario
            if album["release_date"]:
                album["release_date"] = album["release_date"].isoformat()
            if album["created_at"]:
                album["created_at"] = album["created_at"].isoformat()
            if album["updated_at"]:
                album["updated_at"] = album["updated_at"].isoformat()

        return albums
